// IPC bridge: handles renderer → main actions and broadcasts state patches
import { ipcMain } from 'electron'
import * as fs from 'fs'
import * as path from 'path'
import type { IpcAction } from '@shared/types'
import { settingsService } from './services/settings'
import { getValidToken, tokenTimeLeft } from './services/oauth'
import { getCachedCharacter } from './services/gggApi'
import { clientTxtWatcher } from './services/clientTxtWatcher'
import { queueChatSend } from './services/gameInput'
import { apSocket } from './services/apSocket'
import { getItems, getBosses, getBaseItems, getLevelLocations } from './data'
import { logger } from './services/logger'
import { checkGoalZone, checkBossDrops } from './validation'
import { state, patch, pushChat, timestamp, sc, setSettingsContext, setGameOpts, setPendingGoalToken } from './ipc-state'
import { regenFilter, handleZoneEntry, clearFilters } from './ipc-filter'
import { handleChatCommand } from './ipc-chat'
import { handleAction } from './ipc-actions'

export { state, getFullState } from './ipc-state'
export { clearFilters } from './ipc-filter'

import poeVersion from '../../poe-version.json'
const CLIENT_VERSION = poeVersion.clientVersion
const BACKWARDS_COMPATIBLE_VERSIONS = new Set(poeVersion.backwardsCompatibleVersions)

// Highest item index whispered so far — prevents re-whispering on reconnect replay
let _highWaterIndex = -1

// Batch item whispers — AP sends itemsReceived as a burst; flush on next tick
let _pendingWhisperNames: string[] = []
let _pendingWhisperTimer: ReturnType<typeof setTimeout> | null = null

function flushItemWhisper(charName: string): void {
  if (_pendingWhisperNames.length === 0) return
  const raw = _pendingWhisperNames.splice(0)
  // Collapse duplicates: ["Foo", "Foo", "Bar"] → ["Foo x2", "Bar"]
  const counts: Record<string, number> = {}
  for (const n of raw) counts[n] = (counts[n] ?? 0) + 1
  const names = Object.entries(counts).map(([n, c]) => c > 1 ? `${n} x${c}` : n)
  const prefix = `@${charName} `
  const maxBody = 500 - prefix.length
  const full = 'You received: ' + names.join(', ')
  for (let i = 0; i < full.length; i += maxBody) {
    queueChatSend(prefix + full.slice(i, i + maxBody))
  }
}

/**
 * Register all IPC handlers and wire up AP socket / client-txt watcher callbacks.
 * Must be called once after the Electron app is ready and a BrowserWindow exists.
 */
export function initIpc(): void {
  clearFilters()

  // Init oauth state from persisted token
  const token = getValidToken()
  if (token) {
    patch({
      oauthStatus:   'valid',
      oauthDaysLeft: tokenTimeLeft(),
    })
  }

  // Init from settings
  const s = settingsService.get()
  patch({
    slotName:        s.slotName,
    serverAddr:      s.serverAddress,
    whisperUpdates:  s.whisperUpdates,
    deathlink:       s.deathlink ?? false,
    clientTxtOk:     false,
    clientTxtPathOk: !!(s.clientTxtPath && fs.existsSync(s.clientTxtPath)),
    docPathOk:       !!(s.poeDocPath && fs.existsSync(s.poeDocPath)),
    filterOk:        !!(s.poeDocPath && fs.existsSync(path.join(s.poeDocPath, '__ap.filter'))),
    onboardingDone:  s.onboardingDone ?? false,
    charName:        s.lastCharName ?? null,
  })

  // Reload last character if token is valid
  if (getValidToken() && s.lastCharName) {
    getCachedCharacter(s.lastCharName, false).then(gggChar => {
      if (gggChar) patch({ char: gggChar as any, charName: gggChar.name })
    }).catch(e => logger.warn('[init] char reload failed:', e?.message))
  }

  // AP socket events
  apSocket.on(ev => {
    if (ev.type === 'connected') {
      logger.info('AP connected as', ev.slot)
      // H-2: prefer server-side poe-uuid over OAuth UUID
      setSettingsContext(ev.seedName, ev.slotData?.['poe-uuid'] ?? settingsService.get().poeUuid ?? '', ev.slot)
      const ws = settingsService.get(...sc())
      patch({ deathlink: ws.deathlink, whisperUpdates: ws.whisperUpdates })
      _highWaterIndex = Math.max(_highWaterIndex, ws.chatHighWaterIndex ?? -1)

      const gameOpts = ev.slotData?.game_options ?? ev.slotData ?? {}
      setGameOpts(gameOpts)
      const goalType: number = gameOpts.goal ?? 0
      const bossesForGoal: string[] = gameOpts.bosses_for_goal ?? []
      const goalState = {
        type:     goalType,
        bosses:   bossesForGoal.length > 0 ? bossesForGoal : undefined,
        defeated: state.goal?.defeated ?? [],
        eligible: state.goal?.eligible ?? false,
        complete: state.goal?.complete ?? false,
      }
      patch({ connection: 'connected', slotName: ev.slot, goal: goalState })

      // Defer one tick so archipelago.js finishes populating room.checkedLocations/missingLocations
      setTimeout(() => {
        const nameToAct: Record<string, number | string> = {}
        for (const b of getBaseItems()) nameToAct[b.name] = b.act
        for (const boss of Object.values(getBosses())) nameToAct[boss.name] = '0_boss'
        for (const lvl of getLevelLocations()) nameToAct[lvl.name] = 'level'
        const rawLocs = apSocket.getAllLocationsWithNames()
        const locations = rawLocs.map(l => ({ ...l, act: nameToAct[l.name] ?? 'Other' }))
        patch({ locations })
      }, 0)
      pushChat({ t: timestamp(), kind: 'sys', body: `Connected as "${ev.slot}" · Path of Exile` })

      // H-3: version check
      const generatedVersion: string = ev.slotData?.generated_version ?? ''
      if (generatedVersion && generatedVersion !== CLIENT_VERSION) {
        if (BACKWARDS_COMPATIBLE_VERSIONS.has(generatedVersion)) {
          pushChat({ t: timestamp(), kind: 'sys', body: `Version mismatch (compatible): server=${generatedVersion} client=${CLIENT_VERSION}` })
        } else {
          pushChat({ t: timestamp(), kind: 'sys', body: `⚠ Version mismatch (INCOMPATIBLE): server=${generatedVersion} client=${CLIENT_VERSION} — this may cause issues!` })
        }
      }

      // H-4: starting character hint from slot data
      const startingChar: string = gameOpts.starting_character ?? ''
      if (startingChar) pushChat({ t: timestamp(), kind: 'sys', body: `Starting character: ${startingChar}` })

      regenFilter()
    }
    if (ev.type === 'locationsChecked') {
      const checkedSet = new Set(ev.ids)
      state.locations = state.locations.map(l => checkedSet.has(l.id) ? { ...l, checked: true } : l)
      patch({ locations: state.locations })
      regenFilter()
    }
    if (ev.type === 'disconnected') {
      logger.info('AP disconnected')
      patch({ connection: 'disconnected', locations: [] })
      pushChat({ t: timestamp(), kind: 'sys', body: 'Disconnected from server' })
    }
    if (ev.type === 'item') {
      const item = ev.item
      const apItem = getItems().find(i => i.name === item.name)
      item.classification = apItem?.classification ?? 'Filler'
      item.category = apItem?.category ?? []

      // Dedup: archipelago.js replays all items from index 0 on reconnect.
      // Only whisper items with an index strictly above the high-water mark.
      const isNew = item.index > _highWaterIndex
      if (isNew) {
        _highWaterIndex = item.index
        settingsService.set('chatHighWaterIndex', _highWaterIndex, ...sc())
      }

      const alreadyHave = state.items.some(i => i.index === item.index)
      if (!alreadyHave) {
        state.items = [...state.items, item]
        patch({ items: state.items })
      }

      // Boss defeat: match received AP item ID against boss IDs (mirrors Python approach)
      if (state.goal?.type === 10) {
        const allBosses = getBosses()
        const bossEntry = Object.entries(allBosses).find(([, b]) => b.id === item.id)
        if (bossEntry) {
          const [bossKey] = bossEntry
          const goal = state.goal
          if (goal.bosses?.includes(bossKey) && !goal.defeated.includes(bossKey)) {
            const newDefeated = [...goal.defeated, bossKey]
            const allDone = goal.bosses.every(b => newDefeated.includes(b))
            patch({ goal: { ...goal, defeated: newDefeated, eligible: allDone } })
            pushChat({ t: timestamp(), kind: 'sys', body: `Boss defeated: ${bossKey}` })
            if (allDone) {
              pushChat({ t: timestamp(), kind: 'sys', body: 'All bosses defeated — click Send Goal to complete!' })
            }
          }
        }
      }

      if (isNew) {
        pushChat({ t: timestamp(), kind: 'item', body: `${item.name} from ${item.from}` })
        if (state.whisperUpdates) {
          const ws = settingsService.get(...sc())
          const whispered = new Set(ws.whisperedIndices ?? [])
          if (!whispered.has(item.index)) {
            whispered.add(item.index)
            settingsService.set('whisperedIndices', [...whispered], ...sc())
            const charName = state.charName ?? state.char?.name
            if (charName) {
              _pendingWhisperNames.push(item.name)
              if (_pendingWhisperTimer) clearTimeout(_pendingWhisperTimer)
              _pendingWhisperTimer = setTimeout(() => {
                _pendingWhisperTimer = null
                flushItemWhisper(charName)
              }, 2000)
            }
          }
        }
      }
    }
    if (ev.type === 'chat') {
      pushChat({ t: timestamp(), kind: 'chat', body: ev.msg })
    }
    if (ev.type === 'hint') {
      const existing = state.hints.findIndex(
        h => h.item === ev.item && h.location === ev.location && h.finder === ev.finder
      )
      const hint = { item: ev.item, location: ev.location, finder: ev.finder, receiver: ev.receiver ?? '', found: false }
      if (existing >= 0) {
        state.hints = state.hints.map((h, i) => i === existing ? hint : h)
      } else {
        state.hints = [...state.hints, hint]
      }
      patch({ hints: state.hints })
    }
    if (ev.type === 'deathlink') {
      if (state.deathlink) {
        pushChat({ t: timestamp(), kind: 'sys', body: `DeathLink received from ${ev.source} — sending /exit` })
        queueChatSend('/exit')
      }
    }
    if (ev.type === 'error') {
      logger.error('AP error:', ev.msg)
      pushChat({ t: timestamp(), kind: 'sys', body: `Error: ${ev.msg}` })
    }
  })

  // Client.txt watcher events
  clientTxtWatcher.on(ev => {
    if (ev.type === 'zone') {
      patch({ zone: ev.zone })
      pushChat({ t: timestamp(), kind: 'sys', body: `You have entered ${ev.zone}` })
      if (apSocket.connected && state.connection === 'connected') {
        handleZoneEntry(ev.zone).catch(e => {
          logger.error('[zone] validation error:', e?.message)
          regenFilter()
        })
      } else {
        regenFilter()
      }

      if (state.goal && !state.goal.complete) {
        // Zone-based goals: send token to char to verify in-game identity, then enable Send Goal
        if (checkGoalZone(state.goal.type, ev.zone) && state.char && !state.goal.eligible) {
          const token = Math.random().toString(36).slice(2, 8)
          setPendingGoalToken(token)
          queueChatSend(`@${state.char.name} ${token}`)
          pushChat({ t: timestamp(), kind: 'sys', body: 'Goal zone reached — verifying character in-game...' })
        }
        // Boss defeat goal — detect drops in inventory → check AP location
        // Goal state is updated when the AP server sends back the "defeat X" item
        if (state.goal.type === 10) {
          const charName = state.char?.name ?? settingsService.get().lastCharName
          if (charName) {
            getCachedCharacter(charName, false).then(gggChar => {
              if (!gggChar) return
              const allBosses = getBosses()
              for (const bossKey of checkBossDrops(gggChar, allBosses)) {
                const boss = allBosses[bossKey]
                if (boss?.id) apSocket.locationChecked(boss.id)
              }
            }).catch(() => {})
          }
        }
      }
    }
    if (ev.type === 'death') {
      if (state.deathlink && ev.who === state.slotName) {
        apSocket.sendDeathlink(ev.who)
        pushChat({ t: timestamp(), kind: 'sys', body: `DeathLink sent (${ev.who} died)` })
      }
    }
    if (ev.type === 'chat') {
      handleChatCommand(ev.who, ev.msg)
    }
  })

  // IPC actions from renderer
  ipcMain.handle('action', async (evt, action: IpcAction) => {
    if (action.type === 'requestFullState') {
      evt.sender.send('state:full', state)
      return null
    }
    return handleAction(action)
  })
}
