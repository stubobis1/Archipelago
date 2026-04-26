import { vi } from 'vitest'

// Mock Electron — not available outside the Electron runtime
vi.mock('electron', () => ({
  clipboard: { readText: vi.fn(() => ''), writeText: vi.fn() },
  app:       { getPath: vi.fn(() => '/tmp/poeap') },
  shell:     { openPath: vi.fn() },
  ipcMain:   { handle: vi.fn() },
  BrowserWindow: { getAllWindows: vi.fn(() => []), getFocusedWindow: vi.fn(() => null) },
  dialog:    { showOpenDialog: vi.fn() },
}))

// Mock electron-store — relies on Electron paths
vi.mock('electron-store', () => {
  return {
    default: vi.fn().mockImplementation(() => ({
      store: {},
      get:   vi.fn((k: string, d: unknown) => d),
      set:   vi.fn(),
    })),
  }
})

// Mock electron-log — must include transports.file so logger.ts initialises without throwing
vi.mock('electron-log', () => ({
  default: {
    info:  vi.fn(),
    warn:  vi.fn(),
    error: vi.fn(),
    debug: vi.fn(),
    transports: {
      file: { resolvePathFn: undefined, level: 'debug' },
      console: { level: 'debug' },
    },
  },
}))
