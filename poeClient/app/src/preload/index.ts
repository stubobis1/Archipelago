import { contextBridge, ipcRenderer } from 'electron'
import type { IpcAction, AppState } from '@shared/types'

contextBridge.exposeInMainWorld('electronAPI', {
  action: (a: IpcAction) => ipcRenderer.invoke('action', a),

  onStateFull:  (fn: (s: AppState) => void) => {
    ipcRenderer.on('state:full', (_e, s) => fn(s))
  },
  onStatePatch: (fn: (delta: Partial<AppState>) => void) => {
    ipcRenderer.on('state:patch', (_e, d) => fn(d))
  },
  onHotkeyRevalidate: (fn: () => void) => {
    ipcRenderer.on('hotkey:revalidate', fn)
  },

  removeAllListeners: (channel: string) => {
    ipcRenderer.removeAllListeners(channel)
  },
})

declare global {
  interface Window {
    electronAPI: {
      action: (a: IpcAction) => Promise<unknown>
      onStateFull:  (fn: (s: AppState) => void) => void
      onStatePatch: (fn: (delta: Partial<AppState>) => void) => void
      onHotkeyRevalidate: (fn: () => void) => void
      removeAllListeners: (channel: string) => void
    }
  }
}
