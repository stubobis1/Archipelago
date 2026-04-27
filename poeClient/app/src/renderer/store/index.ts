import { create } from 'zustand'
import type { AppState, IpcAction } from '@shared/types'

interface Store extends AppState {
  patch:  (delta: Partial<AppState>) => void
  action: (a: IpcAction) => Promise<unknown>
}

const INITIAL: AppState = {
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
  filterOk:        false,
  items:           [],
  chat:            [],
  goal:            null,
  errors:          [],
  deathlink:       false,
  whisperUpdates:  true,
  onboardingStep:  1,
  onboardingDone:  false,
}

export const useStore = create<Store>((set) => ({
  ...INITIAL,

  patch:  (delta) => set(s => ({ ...s, ...delta })),
  action: (a: IpcAction) => window.electronAPI.action(a),
}))

// Wire up IPC listeners once
export function initStoreListeners(): void {
  const { patch, action } = useStore.getState()

  window.electronAPI.onStateFull(s  => patch(s))
  window.electronAPI.onStatePatch(d => patch(d))

  window.electronAPI.onHotkeyRevalidate(() => {
    action({ type: 'revalidate' })
  })

  // Pull full state now that listeners are registered — avoids race with did-finish-load push
  action({ type: 'requestFullState' })
}
