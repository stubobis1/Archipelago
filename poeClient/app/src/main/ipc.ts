// IPC bridge: handles renderer → main actions and broadcasts state patches
import { ipcMain, BrowserWindow, dialog, shell, app } from 'electron'
import * as fs from 'fs'
import * as os from 'os'
import * as path from 'path'
import { execSync } from 'child_process'
import archiver from 'archiver'
import type { IpcAction, AppState, ChatMessage } from '@shared/types'
import { settingsService } from './services/settings'
import { startOAuthFlow, clearToken, getValidToken, tokenTimeLeft } from './services/oauth'
import { getCachedCharacter, clearCharCache, fetchCharacterList } from './services/gggApi'
import { clientTxtWatcher } from './services/clientTxtWatcher'
import { writeFilters } from './services/filterWriter'
import { openChatAndSend, queueChatSend } from './services/gameInput'
import { apSocket } from './services/apSocket'
import { getItems, getBaseItems, getBosses, ensureJingles } from './data'
import { logger } from './services/logger'
import { validateCharEquipment, validatePassivePoints, checkGoalZone, checkBossDrops, toEquipArray } from './validation'

// Per-world settings context — set on AP connect, reset on disconnect
let _settingsSeed = ''
let _settingsUuid = ''
let _settingsSlot = ''
const sc = (): [string, string, string] => [_settingsSeed, _settingsUuid, _settingsSlot]

// Game options from slot data — set on AP connect
let _gameOpts: Record<string, any> = {}

// Highest item index whispered so far — prevents re-whispering on reconnect replay
let _highWaterIndex = -1

// Token pending from !ap char self-whisper identification flow
let _pendingCharToken: string | null = null

// AP world version compatibility
import poeVersion from '../../poe-version.json'
const CLIENT_VERSION = poeVersion.clientVersion
const BACKWARDS_COMPATIBLE_VERSIONS = new Set(poeVersion.backwardsCompatibleVersions)

/** Mutable live state snapshot — updated by `patch()` and sent to the renderer on every change. */
export let state: AppState = {
  connection:      'disconnected',
  serverAddr:      '',
  slotName:        '',
  oauthStatus:     'none',
  oauthAccount:    null,
  oauthDaysLeft:   null,
  char:            null,
  zone:            '',
  clientTxtOk:     false,
  clientTxtPathOk: false,
  filterOk:        false,
  items:           [],
  chat:            [],
  goal:            null,
  errors:          [],
  deathlink:       false,
  whisperUpdates:  true,
  hints:           [],
  onboardingStep:  1,
  onboardingDone:  false,
}

function patch(delta: Partial<AppState>): void {
  Object.assign(state, delta)
  const wins = BrowserWindow.getAllWindows()
  for (const w of wins) {
    if (!w.isDestroyed()) w.webContents.send('state:patch', delta)
  }
}

function pushChat(msg: ChatMessage): void {
  state.chat = [...state.chat.slice(-499), msg]
  patch({ chat: state.chat })
}

function timestamp(): string {
  const d = new Date()
  return `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`
}

/**
 * Register all IPC handlers and wire up AP socket / client-txt watcher callbacks.
 * Must be called once after the Electron app is ready and a BrowserWindow exists.
 */
export function initIpc(): void {
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
    slotName:       s.slotName,
    serverAddr:     s.serverAddress,
    whisperUpdates: s.whisperUpdates,
    deathlink:      s.deathlink ?? false,
    clientTxtOk:    false,
    clientTxtPathOk: !!(s.clientTxtPath && fs.existsSync(s.clientTxtPath)),
    filterOk:       !!(s.poeDocPath && fs.existsSync(path.join(s.poeDocPath, '__ap.filter'))),
    onboardingDone: s.onboardingDone ?? false,
  })

  // Reload last character if token is valid
  if (getValidToken() && s.lastCharName) {
    getCachedCharacter(s.lastCharName, false).then(gggChar => {
      if (gggChar) patch({ char: gggChar as any })
    }).catch(e => logger.warn('[init] char reload failed:', e?.message))
  }

  // AP socket events
  apSocket.on(ev => {
    if (ev.type === 'connected') {
      logger.info('AP connected as', ev.slot)
      // Establish per-world settings context (H-2: prefer server-side poe-uuid over OAuth UUID)
      _settingsSeed = ev.seedName
      _settingsSlot = ev.slot
      _settingsUuid = ev.slotData?.['poe-uuid'] ?? settingsService.get().poeUuid ?? ''
      // Load world-specific settings overrides
      const ws = settingsService.get(...sc())
      patch({ deathlink: ws.deathlink, whisperUpdates: ws.whisperUpdates })

      const gameOpts = ev.slotData?.game_options ?? ev.slotData ?? {}
      _gameOpts = gameOpts
      const goalType: number = gameOpts.goal ?? 0
      const bossesForGoal: string[] = gameOpts.bosses_for_goal ?? []
      const goalState = {
        type:     goalType,
        bosses:   bossesForGoal.length > 0 ? bossesForGoal : undefined,
        defeated: state.goal?.defeated ?? [],
        complete: state.goal?.complete ?? false,
      }
      patch({ connection: 'connected', slotName: ev.slot, goal: goalState })
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
      regenFilter()
    }
    if (ev.type === 'disconnected') {
      logger.info('AP disconnected')
      patch({ connection: 'disconnected' })
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
      if (isNew) _highWaterIndex = item.index

      const alreadyHave = state.items.some(i => i.index === item.index)
      if (!alreadyHave) {
        state.items = [...state.items, item]
        patch({ items: state.items })
      }

      if (isNew && state.whisperUpdates) {
        pushChat({ t: timestamp(), kind: 'item', body: `${item.name} from ${item.from}` })
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
        // Zone-based goals
        if (checkGoalZone(state.goal.type, ev.zone)) {
          const newGoal = { ...state.goal, complete: true }
          patch({ goal: newGoal })
          apSocket.sendGoalComplete()
          queueChatSend('Congratulations! You have won!')
        }
        // Boss defeat goal — scan inventory for drops each zone change
        if (state.goal.type === 10) {
          const charName = state.char?.name ?? settingsService.get().lastCharName
          if (charName) {
            getCachedCharacter(charName, false).then(gggChar => {
              if (!gggChar || !state.goal) return
              const newly   = checkBossDrops(gggChar, getBosses())
              const allDone = [...new Set([...state.goal.defeated, ...newly])]
              if (allDone.length === state.goal.defeated.length) return  // no change
              const required = state.goal.bosses ?? []
              const complete  = required.length > 0 && required.every(b => allDone.includes(b))
              patch({ goal: { ...state.goal, defeated: allDone, complete } })
              for (const b of newly) {
                pushChat({ t: timestamp(), kind: 'sys', body: `Boss defeated: ${b}` })
                // Check the location with AP server
                const boss = getBosses()[b]
                if (boss?.id) apSocket.locationChecked(boss.id)
              }
              if (complete) {
                apSocket.sendGoalComplete()
                queueChatSend('Congratulations! All bosses defeated!')
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

async function handleAction(action: IpcAction): Promise<unknown> {
  switch (action.type) {

    case 'connect': {
      patch({ connection: 'connecting', serverAddr: action.addr, slotName: action.slot })
      settingsService.setMany({ serverAddress: action.addr, slotName: action.slot, password: action.password })
      settingsService.setMany({ serverAddress: action.addr, slotName: action.slot, password: action.password }, ...sc())
      try {
        await apSocket.connect(action.addr, action.slot, action.password)
      } catch (e: any) {
        logger.error('Connect failed:', e?.message)
        patch({ connection: 'error' })
        pushChat({ t: timestamp(), kind: 'sys', body: `Connect failed: ${e?.message}` })
      }
      return null
    }

    case 'disconnect': {
      await apSocket.disconnect()
      return null
    }

    case 'oauth:start': {
      try {
        await startOAuthFlow()
        patch({
          oauthStatus:   'valid',
          oauthDaysLeft: tokenTimeLeft(),
        })
        pushChat({ t: timestamp(), kind: 'sys', body: 'GGG OAuth complete' })
      } catch (e: any) {
        pushChat({ t: timestamp(), kind: 'sys', body: `OAuth error: ${e?.message}` })
      }
      return null
    }

    case 'oauth:clear': {
      clearToken()
      patch({ oauthStatus: 'none', oauthAccount: null, oauthDaysLeft: null, char: null })
      return null
    }

    case 'revalidate': {
      const charName = state.char?.name ?? settingsService.get().lastCharName
      if (!charName) return null
      clearCharCache()
      const gggChar = await getCachedCharacter(charName, true)
      if (gggChar) {
        const ctx = {
          receivedItems:        state.items,
          gucciMode:            _gameOpts.gucciHobo            ?? 0,
          passivePointsAsItems: _gameOpts.passivePointsAsItems !== false,
        }
        const errs = [
          ...validateCharEquipment(gggChar, ctx),
          ...validatePassivePoints(gggChar, ctx),
        ]
        patch({ errors: errs })
        if (errs.length > 0) {
          queueChatSend('/itemfilter __invalid')
        } else {
          regenFilter()
          queueChatSend('/itemfilter __ap')
        }
      }
      return null
    }

    case 'regenerateFilter': {
      regenFilter()
      queueChatSend('/itemfilter __ap')
      return null
    }

    case 'sendCommand': {
      const cmd = action.cmd.startsWith('/') || action.cmd.startsWith('!')
        ? action.cmd
        : `/${action.cmd}`
      // Echo to AP chat and game
      apSocket.sendChat(action.cmd)
      await openChatAndSend(cmd)
      pushChat({ t: timestamp(), kind: 'out', body: `→ you ${action.cmd}` })
      return null
    }

    case 'setDeathlink': {
      patch({ deathlink: action.enabled })
      settingsService.set('deathlink', action.enabled, ...sc())
      return null
    }

    case 'setWhisperUpdates': {
      patch({ whisperUpdates: action.enabled })
      settingsService.set('whisperUpdates', action.enabled, ...sc())
      return null
    }

    case 'saveSetting': {
      settingsService.set(action.key, action.value as never, ...sc())
      // Infra keys are global — also write to default so per-world stores stay in sync
      const GLOBAL_KEYS = new Set(['clientTxtPath', 'poeDocPath', 'baseItemFilter'])
      if (GLOBAL_KEYS.has(action.key)) settingsService.set(action.key, action.value as never)
      if (action.key === 'clientTxtPath') {
        const p      = action.value as string
        const pathOk = !!(p && fs.existsSync(p))
        patch({ clientTxtPathOk: pathOk })
      }
      if (action.key === 'filterSound' || action.key === 'filterDisplay' || action.key === 'baseItemFilter') {
        regenFilter()
        queueChatSend('/itemfilter __ap')
      }
      return null
    }

    case 'handshakeChar': {
      settingsService.set('lastCharName', action.charName, ...sc())
      const gggChar = await getCachedCharacter(action.charName, true)
      if (gggChar) {
        patch({ char: gggChar as any })
      }
      return null
    }

    case 'onboardingNext': {
      const next = Math.min(state.onboardingStep + 1, 5)
      patch({ onboardingStep: next })
      return null
    }

    case 'startMonitoring': {
      const s2 = settingsService.get(...sc())
      const watchOk = s2.clientTxtPath ? clientTxtWatcher.start(s2.clientTxtPath) : false
      patch({ clientTxtOk: watchOk })
      regenFilter()  // always write the AP filter file first
      pushChat({ t: timestamp(), kind: 'sys', body: 'Switch to Path of Exile — validating character before loading filter' })
      const charName = state.char?.name ?? settingsService.get().lastCharName
      if (charName) {
        clearCharCache()
        const gggChar = await getCachedCharacter(charName, true)
        if (gggChar) {
          patch({ char: gggChar as any })
          const ctx = {
            receivedItems:        state.items,
            gucciMode:            _gameOpts.gucciHobo            ?? 0,
            passivePointsAsItems: _gameOpts.passivePointsAsItems !== false,
          }
          const errs = [
            ...validateCharEquipment(gggChar, ctx),
            ...validatePassivePoints(gggChar, ctx),
          ]
          patch({ errors: errs })
          if (errs.length > 0) {
            pushChat({ t: timestamp(), kind: 'sys', body: `Out of logic: ${errs.map(e => e.msg).join(', ')}` })
            queueChatSend('/itemfilter __invalid')
          } else {
            queueChatSend('/itemfilter __ap')
          }
        } else {
          queueChatSend('/itemfilter __ap')
        }
      } else {
        queueChatSend('/itemfilter __ap')
      }
      pushChat({ t: timestamp(), kind: 'sys', body: 'Monitoring started — filter loaded, gear validated' })
      return null
    }

    case 'stopMonitoring': {
      clientTxtWatcher.stop()
      patch({ clientTxtOk: false })
      pushChat({ t: timestamp(), kind: 'sys', body: 'Monitoring stopped' })
      return null
    }

    case 'onboardingComplete': {
      settingsService.set('onboardingDone', true)
      patch({ onboardingDone: true })
      return null
    }

    case 'window:minimize': {
      BrowserWindow.getFocusedWindow()?.minimize()
      return null
    }

    case 'window:close': {
      BrowserWindow.getFocusedWindow()?.close()
      return null
    }

    case 'getDefaultPaths': {
      const saved = settingsService.get()
      return {
        clientTxt:      saved.clientTxtPath  || findClientTxt(),
        docPath:        saved.poeDocPath     || findDocPath(),
        baseItemFilter: saved.baseItemFilter || '',
      }
    }

    case 'checkPath': {
      return fs.existsSync(action.path)
    }

    case 'getCharacterList': {
      return await fetchCharacterList()
    }

    case 'getSettings': {
      return settingsService.get(...sc())
    }

    case 'hintItem': {
      apSocket.hintItem(action.itemName)
      return null
    }

    case 'openConfigDir': {
      await shell.openPath(app.getPath('userData'))
      return null
    }

    case 'exportConfigZip': {
      const userData = app.getPath('userData')
      const dest = path.join(app.getPath('downloads'), `poeap-config-${Date.now()}.zip`)
      // Only include settings json files and logs dir — skip all Electron runtime dirs
      const INCLUDE_EXTS = new Set(['.json', '.log'])
      try {
        await new Promise<void>((resolve, reject) => {
          const output = fs.createWriteStream(dest)
          const arc = archiver('zip', { zlib: { level: 6 } })
          output.on('close', resolve)
          arc.on('error', reject)
          arc.pipe(output)
          // Add logs dir
          const logsDir = path.join(userData, 'logs')
          if (fs.existsSync(logsDir)) arc.directory(logsDir, 'logs')
          // Add top-level json files (settings stores)
          for (const f of fs.readdirSync(userData)) {
            if (INCLUDE_EXTS.has(path.extname(f))) {
              arc.file(path.join(userData, f), { name: f })
            }
          }
          arc.finalize()
        })
        await shell.openPath(path.dirname(dest))
      } catch (e: any) {
        logger.error('Export zip failed:', e?.message)
      }
      return null
    }

    case 'deleteConfigData': {
      const userData = app.getPath('userData')
      try {
        for (const f of fs.readdirSync(userData)) {
          const fp = path.join(userData, f)
          fs.rmSync(fp, { recursive: true, force: true })
        }
        settingsService.setMany({
          clientTxtPath: '', poeDocPath: '', baseItemFilter: '',
          serverAddress: '', slotName: '', oauthToken: null, oauthExpires: null,
          onboardingDone: false,
        })
        patch({ onboardingDone: false, onboardingStep: 1 })
      } catch (e: any) {
        logger.error('Delete config failed:', e?.message)
      }
      return null
    }

    case 'browsePath': {
      const win = BrowserWindow.getFocusedWindow()
      if (!win) return null
      const result = await dialog.showOpenDialog(win, {
        title:       action.title,
        defaultPath: action.defaultPath,
        properties:  action.mode === 'file' ? ['openFile'] : ['openDirectory'],
      })
      return result.canceled ? null : result.filePaths[0]
    }
  }
}

function registryGet(key: string, value: string): string | null {
  try {
    const out = execSync(`reg query "${key}" /v "${value}"`, { encoding: 'utf8' })
    const m = out.match(/REG_SZ\s+(.+)/)
    return m ? m[1].trim() : null
  } catch { return null }
}

function findClientTxt(): string {
  const home = os.homedir()

  if (process.platform === 'linux') {
    const p = path.join(home, '.local/share/Steam/steamapps/common/Path of Exile/logs/Client.txt')
    if (fs.existsSync(p)) return p
    return ''
  }

  const regPath = registryGet('HKCU\\Software\\GrindingGearGames\\Path of Exile', 'InstallLocation')
  if (regPath) {
    const p = path.join(regPath, 'logs', 'Client.txt')
    if (fs.existsSync(p)) return p
  }

  const intermediates = ['', 'games', 'Program Files (x86)', 'Program Files',
    'Program Files (x86)\\Steam', 'Program Files\\Steam', 'Steam', 'SteamLibrary',
    'games\\SteamLibrary', 'steamlibraryd']
  const suffixes = ['steamapps\\common\\Path of Exile', 'Path of Exile', 'poe']

  for (const drive of ['D', 'C', 'E', 'F', 'G']) {
    for (const mid of intermediates) {
      for (const suf of suffixes) {
        const p = path.join(`${drive}:\\`, mid, suf, 'logs', 'Client.txt')
        if (fs.existsSync(p)) return p
      }
    }
  }
  return ''
}

function findDocPath(): string {
  const home = os.homedir()

  if (process.platform === 'linux') {
    const p = path.join(home, '.local/share/Steam/steamapps/compatdata/238960/pfx/drive_c/users/steamuser/Documents/My Games/Path of Exile')
    if (fs.existsSync(p)) return p
    return ''
  }

  for (const base of [
    path.join(home, 'Documents'),
    path.join(home, 'OneDrive', 'Documents'),
  ]) {
    const p = path.join(base, 'My Games', 'Path of Exile')
    if (fs.existsSync(p)) return p
  }
  return ''
}

/**
 * Full zone-entry validation loop — mirrors Python validationLogic.when_enter_new_zone.
 * Fetches char from GGG API, validates equipment + passives, checks base-item and
 * level-up locations, then switches the active filter based on validation result.
 */
async function handleZoneEntry(_zone: string): Promise<void> {
  const charName = state.char?.name ?? settingsService.get(...sc()).lastCharName ?? settingsService.get().lastCharName
  if (!charName) {
    pushChat({ t: timestamp(), kind: 'sys', body: 'Zone entered — no character set. Type !ap char in game to identify.' })
    regenFilter()
    return
  }

  let gggChar: any
  try {
    clearCharCache()
    gggChar = await getCachedCharacter(charName, true)
  } catch (e: any) {
    logger.error('[zone] GGG API fetch failed:', e?.message)
    pushChat({ t: timestamp(), kind: 'sys', body: `Zone validation: API fetch failed — ${e?.message}` })
    regenFilter()
    return
  }
  if (!gggChar) { regenFilter(); return }

  patch({ char: gggChar as any })

  const ctx = {
    receivedItems:       state.items,
    gucciMode:           _gameOpts.gucciHobo           ?? 0,
    passivePointsAsItems: _gameOpts.passivePointsAsItems !== false,
  }

  const errs = [
    ...validateCharEquipment(gggChar, ctx),
    ...validatePassivePoints(gggChar, ctx),
  ]
  patch({ errors: errs })

  // Build location check set
  const missingWithNames = apSocket.getMissingLocationsWithNames()
  const missingSet       = new Set(missingWithNames.map(l => l.id))
  const locNameToBase    = locationNameToBase()

  // location name → location ID for base-item locations
  const baseItemToLocId = new Map<string, number>()
  for (const { id, name } of missingWithNames) {
    const baseItem = locNameToBase[name]
    if (baseItem) baseItemToLocId.set(baseItem, id)
  }

  const toCheck = new Set<number>()

  // Scan char inventory + equipment for held base items that match AP locations
  const charInv: any[]   = Array.isArray((gggChar as any).inventory) ? (gggChar as any).inventory : []
  const charEquip: any[] = toEquipArray(gggChar)
  for (const item of [...charInv, ...charEquip]) {
    const baseType: string = item.baseType ?? ''
    const locId = baseItemToLocId.get(baseType)
    if (locId !== undefined && missingSet.has(locId)) toCheck.add(locId)
  }

  // Level-up locations: "Reach Level N" for every level up to char.level
  if (_gameOpts.add_leveling_up_to_location_pool !== false && gggChar.level) {
    for (let level = 2; level <= gggChar.level; level++) {
      const loc = missingWithNames.find(l => l.name === `Reach Level ${level}`)
      if (loc) toCheck.add(loc.id)
    }
  }

  if (errs.length > 0) {
    const errorText = errs.map((e: any) => e.msg).join(', ')
    pushChat({ t: timestamp(), kind: 'sys', body: `Out of logic: ${errorText}` })
    queueChatSend('/itemfilter __invalid')
  } else {
    if (toCheck.size > 0) {
      apSocket.checkLocations([...toCheck])
      pushChat({ t: timestamp(), kind: 'sys', body: `Checked ${toCheck.size} new location(s)` })
    }
    regenFilter()
    queueChatSend('/itemfilter __ap')
  }
}

let _locationNameToBase: Record<string, string> | null = null
function locationNameToBase(): Record<string, string> {
  if (!_locationNameToBase) {
    _locationNameToBase = {}
    for (const b of getBaseItems()) {
      if (b.name && b.baseItem) _locationNameToBase[b.name] = b.baseItem
    }
  }
  return _locationNameToBase
}

function regenFilter(): void {
  const s = settingsService.get(...sc())
  if (!s.poeDocPath) {
    pushChat({ t: timestamp(), kind: 'sys', body: 'Filter write failed: PoE documents path not set' })
    return
  }
  try {
    const uncheckedBaseItems = apSocket.getUncheckedBaseItems(locationNameToBase())
    const soundDir = s.filterSound === 2 ? ensureJingles(s.poeDocPath) : ''
    const { blocks, sizeKB } = writeFilters({
      docDir:             s.poeDocPath,
      uncheckedBaseItems,
      baseFilter:         s.baseItemFilter,
      display:            s.filterDisplay,
      sound:              s.filterSound,
      soundDir,
    })
    patch({ filterOk: true })
    pushChat({ t: timestamp(), kind: 'sys', body: `Filter regenerated (${blocks} blocks · ${sizeKB} KB)` })
  } catch (e: any) {
    patch({ filterOk: false })
    pushChat({ t: timestamp(), kind: 'sys', body: `Filter write failed: ${e?.message}` })
  }
}

// ── Chat command helpers ─────────────────────────────────────────────────────

function receivedIds(): Set<number> {
  return new Set(state.items.map(i => i.id))
}

function receivedOfCategory(cat: string) {
  const ids = receivedIds()
  return getItems().filter(i => i.category?.includes(cat) && ids.has(i.id))
}

function gemsOfCategory(cat: string, maxLevel?: number) {
  return receivedOfCategory(cat)
    .filter(i => maxLevel == null || (i.reqLevel ?? 0) <= maxLevel)
    .sort((a, b) => (a.reqLevel ?? 0) - (b.reqLevel ?? 0))
}

function rarityFromProgCount(n: number): string {
  if (n >= 4) return 'Any'
  if (n === 3) return 'up to Rare'
  if (n === 2) return 'up to Magic'
  return 'Normal'
}

function gearMessage(filterCat: string): string {
  const ids  = receivedIds()
  const pool = getItems().filter(i => i.category?.includes(filterCat))
  const recv = pool.filter(i => ids.has(i.id))

  // Progressive items → "up to Rare Helmet" etc.
  const progCounts: Record<string, number> = {}
  for (const item of recv) {
    if (item.category?.includes('Progressive')) {
      const base = item.name.replace('Progressive ', '')
      progCounts[base] = (progCounts[base] ?? 0) + 1
    }
  }
  const progParts = Object.entries(progCounts).map(([k, v]) => `${rarityFromProgCount(v)} ${k}`)

  // Non-progressive specific items (e.g. "Unique Helmet")
  const RARITIES = ['Normal', 'Magic', 'Rare', 'Unique']
  const singles  = recv.filter(i => !i.category?.includes('Progressive') && RARITIES.some(r => i.category?.includes(r)))
  const singleParts = singles.map(i => i.name)

  const parts = [...progParts, ...singleParts]
  return parts.length ? parts.join(', ') : 'none'
}

function goalMessage(): string {
  const g = state.goal
  if (!g) return 'No goal set'
  const GOAL_NAMES: Record<number, string> = {
    0: 'Complete the campaign (reach Karui Shores)',
    1: 'Complete Act 1 (reach The Southern Forest)',
    2: 'Complete Act 2 (reach The City of Sarn)',
    3: 'Complete Act 3 (reach The Aqueduct)',
    4: 'Complete Act 4 (reach The Slave Pens)',
    5: 'Reach Karui Fortress (Act 5/6)',
    6: 'Complete Act 6 (reach The Bridge Encampment)',
    7: 'Complete Act 7 (reach The Sarn Ramparts)',
    8: 'Complete Act 8 (reach The Blood Aqueduct)',
    9: 'Complete Act 9 (reach Oriath Docks)',
    10: 'Defeat bosses',
  }
  const name = GOAL_NAMES[g.type] ?? `Goal type ${g.type}`
  if (g.type === 10 && g.bosses?.length) {
    const parts = g.bosses.map(b => (g.defeated.includes(b) ? `✓${b}` : `✗${b}`))
    return `${name}: ${parts.join(' ')}${g.complete ? ' — ALL DONE!' : ''}`
  }
  return `${name} — ${g.complete ? 'complete!' : 'in progress'}`
}

async function sendGameChat(resp: string): Promise<void> {
  const prefix = `@${state.char?.name ?? state.slotName} `
  const MAX    = 500 - prefix.length
  for (let i = 0; i < resp.length; i += MAX) {
    await openChatAndSend(prefix + resp.slice(i, i + MAX))
  }
}

async function handleChatCommand(who: string, msg: string): Promise<void> {
  const trimmed = msg.trim()

  // Token response from self-whisper char identification — check before owner filter
  if (_pendingCharToken && trimmed === `char_${_pendingCharToken}`) {
    _pendingCharToken = null
    await handleAction({ type: 'handshakeChar', charName: who })
    pushChat({ t: timestamp(), kind: 'sys', body: `Character identified: ${who}` })
    return
  }

  // Only respond to our own character's messages.
  // When knownChar is null (pre-identification) reject everything — the token
  // flow above is the only valid path and it already returned.
  const knownChar = state.char?.name ?? null
  if (!knownChar || (who !== knownChar && who !== state.slotName)) return

  const cmd = trimmed.toLowerCase()
  const charLevel = state.char?.level

  let resp: string | null = null

  if (['!ap char', '!ap character', '!apchar'].includes(cmd)) {
    const token = Math.random().toString(36).slice(2, 10)
    _pendingCharToken = token
    queueChatSend(`char_${token}`)
    pushChat({ t: timestamp(), kind: 'sys', body: `Identifying character — sent char_${token}` })
    return
  }

  if (['!help', '!commands', '!cmds'].includes(cmd)) {
    resp = '!gear !weapons !armor !links !flasks !gems !main gems !support gems !utility gems !usable gems !ascendancy !passives !deathlink !whisper updates !goal !help'
  } else if (cmd === '!gear') {
    resp = `Gear: ${gearMessage('Gear')}`
  } else if (cmd === '!weapons') {
    resp = `Weapons: ${gearMessage('Weapon')}`
  } else if (['!armor', '!armour'].includes(cmd)) {
    resp = `Armour: ${gearMessage('Armour')}`
  } else if (cmd === '!links') {
    const links = receivedOfCategory('max links')
    const counts: Record<string, number> = {}
    for (const i of links) counts[i.name] = (counts[i.name] ?? 0) + 1
    resp = Object.keys(counts).length
      ? Object.entries(counts).map(([k, v]) => `${k}: ${v}`).join(', ')
      : 'No link items'
  } else if (['!flasks', '!flask'].includes(cmd)) {
    const flasks = receivedOfCategory('Flask')
    const counts: Record<string, number> = {}
    for (const i of flasks) counts[i.name] = (counts[i.name] ?? 0) + 1
    resp = Object.keys(counts).length
      ? Object.entries(counts).map(([k, v]) => `${k}: ${v}`).join(', ')
      : 'No flask items'
  } else if (['!gems', '!all gems'].includes(cmd)) {
    const gems = [
      ...gemsOfCategory('MainSkillGem'),
      ...gemsOfCategory('SupportGem'),
      ...gemsOfCategory('UtilSkillGem'),
      ...receivedOfCategory('GemModifier'),
    ]
    resp = gems.length ? gems.map(g => g.name).join(', ') : 'No gems'
  } else if (cmd === '!main gems') {
    const gems = gemsOfCategory('MainSkillGem')
    resp = gems.length ? gems.map(g => g.name).join(', ') : 'No skill gems'
  } else if (cmd === '!support gems') {
    const gems = gemsOfCategory('SupportGem')
    resp = gems.length ? gems.map(g => g.name).join(', ') : 'No support gems'
  } else if (cmd === '!utility gems') {
    const gems = gemsOfCategory('UtilSkillGem')
    resp = gems.length ? gems.map(g => g.name).join(', ') : 'No utility gems'
  } else if (cmd === '!usable gems') {
    const gems = [
      ...gemsOfCategory('MainSkillGem', charLevel),
      ...gemsOfCategory('SupportGem',   charLevel),
      ...gemsOfCategory('UtilSkillGem', charLevel),
    ].sort((a, b) => (b.reqLevel ?? 0) - (a.reqLevel ?? 0))
    resp = gems.length ? gems.map(g => `${g.name}(${g.reqLevel ?? 0})`).join(', ') : 'No usable gems'
  } else if (cmd === '!usable skill gems') {
    const gems = gemsOfCategory('MainSkillGem', charLevel).reverse()
    resp = gems.length ? gems.map(g => `${g.name}(${g.reqLevel ?? 0})`).join(', ') : 'No usable skill gems'
  } else if (cmd === '!usable support gems') {
    const gems = gemsOfCategory('SupportGem', charLevel).reverse()
    resp = gems.length ? gems.map(g => `${g.name}(${g.reqLevel ?? 0})`).join(', ') : 'No usable support gems'
  } else if (cmd === '!usable utility gems') {
    const gems = gemsOfCategory('UtilSkillGem', charLevel).reverse()
    resp = gems.length ? gems.map(g => `${g.name}(${g.reqLevel ?? 0})`).join(', ') : 'No usable utility gems'
  } else if (['!ascendancy', '!ascendancies', '!classes', '!class'].includes(cmd)) {
    const items = receivedOfCategory('Ascendancy')
    resp = items.length ? items.map(i => i.name).join(', ') : 'No ascendancy items'
  } else if (['!p', '!passive', '!passives'].includes(cmd)) {
    const received  = state.items.filter(i => i.name === 'Progressive passive point').length
    const allocated = (state.char?.passives as any)?.hashes?.length ?? 0
    resp = `${received - allocated} passive points available (${allocated}/${received} used for ${state.char?.name ?? '?'})`
  } else if (cmd === '!deathlink') {
    const newVal = !state.deathlink
    patch({ deathlink: newVal })
    settingsService.set('deathlink', newVal, ...sc())
    resp = `DeathLink ${newVal ? 'enabled' : 'disabled'}`
  } else if (['!whisper updates', '!whisper update', '!updates', '!update'].includes(cmd)) {
    const newVal = !state.whisperUpdates
    patch({ whisperUpdates: newVal })
    settingsService.set('whisperUpdates', newVal, ...sc())
    resp = `Whisper updates ${newVal ? 'enabled' : 'disabled'}`
  } else if (cmd === '!goal') {
    resp = goalMessage()
  }

  if (resp) {
    pushChat({ t: timestamp(), kind: 'self', body: resp })
    await sendGameChat(resp)
  }
}

export function getFullState(): AppState {
  return state
}
