import { contextBridge, ipcRenderer } from 'electron'
import type { IpcAction, AppState } from '@shared/types'
import poeVersion from '../../poe-version.json'

contextBridge.exposeInMainWorld('electronAPI', {
  poeVersion: { clientVersion: poeVersion.clientVersion, backwardsCompatibleVersions: poeVersion.backwardsCompatibleVersions },
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

