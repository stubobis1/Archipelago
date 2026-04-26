// Shared types between main and renderer processes

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error'
export type OAuthStatus = 'none' | 'pending' | 'valid' | 'expired'
export type FilterDisplay = 0 | 1 | 2 | 3  // show / hide / randomize / uniform
export type FilterSound  = 0 | 1 | 2  // none / tts / jingle

export interface Settings {
  // Paths
  clientTxtPath:  string
  poeDocPath:     string
  baseItemFilter: string
  // AP connection
  serverAddress:  string
  slotName:       string
  password:       string
  // Preferences
  whisperUpdates:   boolean
  bypassFocusCheck: boolean
  inputDelayEnter:  number
  inputDelayPaste:  number
  deathlink:       boolean
  filterDisplay:   FilterDisplay
  filterSound:     FilterSound
  ttsEnabled:      boolean
  ttsSpeed:        number
  // OAuth token cache
  oauthToken:      string | null
  oauthExpires:    number | null  // unix ms
  poeUuid:         string | null
  lastCharName:    string | null
  // Onboarding
  onboardingDone:  boolean
}

export interface CharacterData {
  name:       string
  class:      string
  level:      number
  league:     string
  equipment:  Record<string, EquipmentSlot>
  inventory:  InventoryItem[]
  passives:   PassivesData
}

export interface EquipmentSlot {
  typeLine:    string
  frameType:   number  // 0=normal 1=magic 2=rare 3=unique
  socketedItems?: GemItem[]
  sockets?:    Socket[]
  properties?: Property[]
  requirements?: Requirement[]
  inventoryId: string
}

export interface GemItem {
  typeLine:    string
  support?:    boolean
  properties?: Property[]
}

export interface Socket {
  group: number
  attr:  string  // R G B W
}

export interface Property {
  name:   string
  values: [string, number][]
}

export interface Requirement {
  name:  string
  values: [string, number][]
}

export interface InventoryItem {
  typeLine: string
  frameType: number
  inventoryId: string
  w?: number
  h?: number
}

export interface PassivesData {
  hashes:       number[]
  items:        InventoryItem[]
  totalUsed?:   number
  totalAlloc?:  number
}

export interface APItem {
  id:          number
  name:        string
  classification: string
  category:    string[]
  reqLevel?:   number
  reqToUse?:   number
}

export interface APBaseItem {
  name:     string
  baseItem: string
  act:      number
  dropLevel: number
  placeInAct?: number
}

export interface APBoss {
  name:       string
  id:         number
  difficulty: number
  drops:      { name: string }[]
}

export interface AlternateGem {
  name:    string
  baseGem: string
  type:    string
}

export interface ReceivedItem {
  id:    number
  name:  string
  classification: string
  category: string[]
  from:  string
  index: number
}

export interface ChatMessage {
  t:       string   // HH:MM timestamp
  kind:    'sys' | 'item' | 'hint' | 'chat' | 'self' | 'out' | 'chat-self'
  who?:    string
  whoColor?: string
  body:    string
}

export interface GoalState {
  type:    number   // from Options.Goal
  bosses?: string[] // for defeat_bosses goal
  defeated: string[]
  actZoneReached?: number
  complete: boolean
}

export interface ValidationError {
  slot: string
  msg:  string
}

export interface APHint {
  item:      string
  location:  string
  entrance?: string
  finder:    string
  receiver:  string
  found:     boolean
}

// IPC state snapshot pushed from main → renderer
export interface AppState {
  connection:  ConnectionStatus
  serverAddr:  string
  slotName:    string
  oauthStatus: OAuthStatus
  oauthAccount: string | null
  oauthDaysLeft: string | null
  char:        CharacterData | null
  zone:        string
  clientTxtOk:       boolean
  clientTxtPathOk:   boolean
  filterOk:    boolean
  items:       ReceivedItem[]
  chat:        ChatMessage[]
  goal:        GoalState | null
  errors:      ValidationError[]
  deathlink:   boolean
  whisperUpdates: boolean
  hints:       APHint[]
  // onboarding
  onboardingStep: number
  onboardingDone: boolean
}

export type IpcAction =
  | { type: 'connect'; addr: string; slot: string; password: string }
  | { type: 'disconnect' }
  | { type: 'oauth:start' }
  | { type: 'oauth:clear' }
  | { type: 'revalidate' }
  | { type: 'regenerateFilter' }
  | { type: 'sendCommand'; cmd: string }
  | { type: 'setDeathlink'; enabled: boolean }
  | { type: 'setWhisperUpdates'; enabled: boolean }
  | { type: 'saveSetting'; key: keyof Settings; value: unknown }
  | { type: 'handshakeChar'; charName: string }
  | { type: 'onboardingNext' }
  | { type: 'window:minimize' }
  | { type: 'window:close' }
  | { type: 'getDefaultPaths' }
  | { type: 'browsePath'; mode: 'file' | 'folder'; title: string; defaultPath?: string }
  | { type: 'checkPath'; path: string }
  | { type: 'getCharacterList' }
  | { type: 'getSettings' }
  | { type: 'startMonitoring' }
  | { type: 'stopMonitoring' }
  | { type: 'onboardingComplete' }
  | { type: 'hintItem'; itemName: string }
  | { type: 'openConfigDir' }
  | { type: 'exportConfigZip' }
  | { type: 'deleteConfigData' }
  | { type: 'requestFullState' }
