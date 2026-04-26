import Store from 'electron-store'
import type { Settings } from '@shared/types'

const DEFAULTS: Settings = {
  clientTxtPath:    '',
  poeDocPath:       '',
  baseItemFilter:   '',
  serverAddress:    'archipelago.gg:38281',
  slotName:         '',
  password:         '',
  whisperUpdates:   true,
  bypassFocusCheck: false,
  inputDelayEnter:  0,
  inputDelayPaste:  0,
  deathlink:        false,
  filterDisplay:    0,
  filterSound:      2,
  ttsEnabled:       false,
  ttsSpeed:         175,
  oauthToken:       null,
  oauthExpires:     null,
  poeUuid:          null,
  lastCharName:     null,
  onboardingDone:   false,
}

/** Derive a store key from connection context; falls back to "default". */
function storeKey(seed?: string, uuid?: string, slot?: string): string {
  return seed && uuid && slot ? `${seed}__${uuid}__${slot}` : 'default'
}

function createSettingsService() {
  const stores = new Map<string, Store<Settings>>()

  function getStore(key: string): Store<Settings> {
    const existing = stores.get(key)
    if (existing) return existing
    const store = new Store<Settings>({ name: `settings-${key}`, defaults: DEFAULTS })
    stores.set(key, store)
    return store
  }

  return {
    /** Read all settings for the given context (defaults to "default" store). */
    get(seed?: string, uuid?: string, slot?: string): Settings {
      return getStore(storeKey(seed, uuid, slot)).store
    },

    /** Write a single setting key. */
    set<K extends keyof Settings>(k: K, v: Settings[K], seed?: string, uuid?: string, slot?: string): void {
      getStore(storeKey(seed, uuid, slot)).set(k, v)
    },

    /** Write multiple settings at once. */
    setMany(patch: Partial<Settings>, seed?: string, uuid?: string, slot?: string): void {
      const store = getStore(storeKey(seed, uuid, slot))
      for (const [k, v] of Object.entries(patch)) {
        store.set(k as keyof Settings, v as never)
      }
    },
  }
}

export const settingsService = createSettingsService()
