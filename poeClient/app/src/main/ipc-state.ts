import { BrowserWindow } from 'electron'
import type { AppState, ChatMessage } from '@shared/types'

export let state: AppState = {
  connection:      'disconnected',
  serverAddr:      '',
  slotName:        '',
  oauthStatus:     'none',
  oauthAccount:    null,
  oauthDaysLeft:   null,
  char:            null,
  charName:        null,
  zone:            '',
  clientTxtOk:     false,
  clientTxtPathOk: false,
  docPathOk:       false,
  filterOk:        false,
  items:           [],
  chat:            [],
  goal:            null,
  errors:          [],
  deathlink:       false,
  whisperUpdates:  true,
  hints:           [],
  locations:       [],
  onboardingStep:  1,
  onboardingDone:  false,
}

export function patch(delta: Partial<AppState>): void {
  Object.assign(state, delta)
  const wins = BrowserWindow.getAllWindows()
  for (const w of wins) {
    if (!w.isDestroyed()) w.webContents.send('state:patch', delta)
  }
}

export function pushChat(msg: ChatMessage): void {
  state.chat = [...state.chat.slice(-499), msg]
  patch({ chat: state.chat })
}

export function timestamp(): string {
  const d = new Date()
  return `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`
}

export function getFullState(): AppState {
  return state
}

// Per-world settings context — set on AP connect
let _settingsSeed = ''
let _settingsUuid = ''
let _settingsSlot = ''

export function sc(): [string, string, string] {
  return [_settingsSeed, _settingsUuid, _settingsSlot]
}

export function setSettingsContext(seed: string, uuid: string, slot: string): void {
  _settingsSeed = seed
  _settingsUuid = uuid
  _settingsSlot = slot
}

// Game options from slot data — set on AP connect
let _gameOpts: Record<string, any> = {}

export function getGameOpts(): Record<string, any> { return _gameOpts }
export function setGameOpts(opts: Record<string, any>): void { _gameOpts = opts }

// Pending goal verification token (zone goals) — send token to char, wait for whisper back
let _pendingGoalToken: string | null = null

export function getPendingGoalToken(): string | null { return _pendingGoalToken }
export function setPendingGoalToken(t: string | null): void { _pendingGoalToken = t }
