import { app, BrowserWindow, protocol, net, globalShortcut } from 'electron'
import * as path from 'path'
import * as url from 'url'

import { initIpc, getFullState } from './ipc'
import { clientTxtWatcher } from './services/clientTxtWatcher'
import { settingsService } from './services/settings'
import { initLogger, logger } from './services/logger'

// Custom protocol to serve pathofexile_ap images
function registerApAssetsProtocol(): void {
  protocol.handle('ap-assets', (request) => {
    const reqUrl  = new URL(request.url)
    const relPath = decodeURIComponent(reqUrl.pathname)
    const imgRoot = path.resolve(__dirname, '../../../../pathofexile_ap/images')
    const fullPath = path.join(imgRoot, relPath)
    return net.fetch(url.pathToFileURL(fullPath).toString())
  })
}

let mainWindow: BrowserWindow | null = null

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width:  1280,
    height: 800,
    minWidth:  900,
    minHeight: 600,
    frame:   false,   // custom titlebar
    backgroundColor: '#1a1713',
    title: 'PoE Archipelago',
    icon: path.join(app.getAppPath(), 'resources', 'poeAP.png'),
    webPreferences: {
      preload:          path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration:  false,
      sandbox:          false,
    },
  })

  // Send full state on page load
  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow?.webContents.send('state:full', getFullState())
  })

  if (process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
    mainWindow.webContents.openDevTools({ mode: 'detach' })
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(async () => {
  initLogger()
  registerApAssetsProtocol()
  initIpc()
  createWindow()
  logger.info('Window created')

  // Start client.txt watcher if path is configured
  const s = settingsService.get()
  if (s.clientTxtPath) {
    clientTxtWatcher.start(s.clientTxtPath)
  }

  // F12 global hotkey for revalidate
  globalShortcut.register('F12', () => {
    mainWindow?.webContents.send('hotkey:revalidate')
  })

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  clientTxtWatcher.stop()
  if (process.platform !== 'darwin') app.quit()
})
