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
import { getItems, getBaseItems, ensureJingles } from './data'
import { logger } from './services/logger'
import { validateCharEquipment, validatePassivePoints, checkGoalZone } from './validation'

// Mutable live state
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
      const gameOpts = ev.slotData?.game_options ?? ev.slotData ?? {}
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
      // Classify from local data
      const apItem = getItems().find(i => i.name === item.name)
      item.classification = apItem?.classification ?? 'Filler'
      item.category = apItem?.category ?? []

      state.items = [...state.items, item]
      patch({ items: state.items })

      if (state.whisperUpdates) {
        pushChat({
          t:    timestamp(),
          kind: 'item',
          body: `${item.name} from ${item.from}`,
        })
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
      // Reload filter on zone change
      regenFilter()
      // Check goal
      if (state.goal && !state.goal.complete) {
        if (checkGoalZone(state.goal.type, ev.zone)) {
          const newGoal = { ...state.goal, complete: true }
          patch({ goal: newGoal })
          apSocket.sendChat(`!goal complete`)
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
        const ctx = { receivedItems: state.items, gucciMode: 0 }
        const errs = [
          ...validateCharEquipment(gggChar, ctx),
          ...validatePassivePoints(gggChar, ctx),
        ]
        patch({ errors: errs })
        regenFilter()
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
      settingsService.set('deathlink', action.enabled)
      return null
    }

    case 'setWhisperUpdates': {
      patch({ whisperUpdates: action.enabled })
      settingsService.set('whisperUpdates', action.enabled)
      return null
    }

    case 'saveSetting': {
      settingsService.set(action.key, action.value as never)
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
      settingsService.set('lastCharName', action.charName)
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
      const s2 = settingsService.get()
      const watchOk = s2.clientTxtPath ? clientTxtWatcher.start(s2.clientTxtPath) : false
      patch({ clientTxtOk: watchOk })
      regenFilter()
      pushChat({ t: timestamp(), kind: 'sys', body: 'Switch to Path of Exile — will send /itemfilter __ap when focused' })
      queueChatSend('/itemfilter __ap')
      const charName = state.char?.name ?? settingsService.get().lastCharName
      if (charName) {
        clearCharCache()
        const gggChar = await getCachedCharacter(charName, true)
        if (gggChar) {
          const ctx = { receivedItems: state.items, gucciMode: 0 }
          const errs = [
            ...validateCharEquipment(gggChar, ctx),
            ...validatePassivePoints(gggChar, ctx),
          ]
          patch({ errors: errs })
        }
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
      return { clientTxt: findClientTxt(), docPath: findDocPath() }
    }

    case 'checkPath': {
      return fs.existsSync(action.path)
    }

    case 'getCharacterList': {
      return await fetchCharacterList()
    }

    case 'getSettings': {
      return settingsService.get()
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
  for (const base of [
    path.join(home, 'Documents'),
    path.join(home, 'OneDrive', 'Documents'),
  ]) {
    const p = path.join(base, 'My Games', 'Path of Exile')
    if (fs.existsSync(p)) return p
  }
  return ''
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
  const s = settingsService.get()
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

function itemsByCategory(category: string): number {
  const idx = new Map(getItems().map(i => [i.name, i]))
  return state.items.filter(i => idx.get(i.name)?.category?.includes(category)).length
}

const COMMAND_HANDLERS: Record<string, () => string> = {
  '!gear':            () => `gear check — ${itemsByCategory('Armour')} armor items received`,
  '!gems':            () => `${itemsByCategory('Gem')} gems received`,
  '!goal':            () => state.goal ? `Goal: ${state.goal.type} · ${state.goal.complete ? 'complete' : 'in progress'}` : 'No goal set',
  '!passives':        () => `${(state.char?.passives as any)?.hashes?.length ?? '?'} passives allocated`,
  '!deathlink':       () => `DeathLink: ${state.deathlink ? 'on' : 'off'}`,
  '!help':            () => 'Commands: !gear !gems !goal !passives !deathlink !whisper !ap char !help',
  '!whisper updates': () => `Whisper updates: ${state.whisperUpdates ? 'on' : 'off'}`,
}

async function handleChatCommand(who: string, msg: string): Promise<void> {
  const cmd = msg.trim().toLowerCase()

  // Only respond to messages from our own character (from game chat, @From self)
  if (who !== state.slotName && who !== state.char?.name) return

  // !ap char — handshake
  if (cmd === '!ap char') {
    pushChat({ t: timestamp(), kind: 'sys', body: 'Character handshake — check game for prompt' })
    return
  }

  const handler = COMMAND_HANDLERS[cmd]
  if (handler) {
    const resp = handler()
    pushChat({ t: timestamp(), kind: 'self', body: resp })
    await openChatAndSend(`@${state.slotName} ${resp}`)
  }
}

export function getFullState(): AppState {
  return state
}
