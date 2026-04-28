import * as fs from 'fs'
import chokidar from 'chokidar'
import { logger } from './logger'

const ZONE_RE  = /\] : You have entered (.+)\./
const DEATH_RE = /\] (.+) has been slain\./
const CHAT_RE  = /\]\s?(?:<.*?>)?\s?(?:@To|@From)?\s?(.+): (?:\x00)?(.*)/
const FOCUS_RE = /\[WINDOW\] (Gained|Lost) focus/

export type ClientTxtEvent =
  | { type: 'zone';  zone: string }
  | { type: 'death'; who:  string }
  | { type: 'chat';  who:  string; msg: string }
  | { type: 'focus'; gained: boolean }
  | { type: 'raw';   line: string }

type Listener = (ev: ClientTxtEvent) => void

/** Parse one trimmed Client.txt line into a typed event. Exported for testing. */
export function parseLine(line: string): ClientTxtEvent {
  const focusM = FOCUS_RE.exec(line)
  if (focusM) return { type: 'focus', gained: focusM[1] === 'Gained' }

  const zoneM = ZONE_RE.exec(line)
  if (zoneM) return { type: 'zone', zone: zoneM[1] }

  const deathM = DEATH_RE.exec(line)
  if (deathM) return { type: 'death', who: deathM[1] }

  const chatM = CHAT_RE.exec(line)
  if (chatM) return { type: 'chat', who: chatM[1], msg: chatM[2] }

  return { type: 'raw', line }
}

function createClientTxtWatcher() {
  let watcher:   ReturnType<typeof chokidar.watch> | null = null
  let listeners: Listener[] = []
  let offset     = 0
  let filePath   = ''

  const emit = (ev: ClientTxtEvent) => listeners.forEach(l => l(ev))

  function readNew(): void {
    try {
      const stat = fs.statSync(filePath)
      if (stat.size < offset) offset = 0  // file rotated
      if (stat.size === offset) return

      const buf = Buffer.alloc(stat.size - offset)
      const fd  = fs.openSync(filePath, 'r')
      fs.readSync(fd, buf, 0, buf.length, offset)
      fs.closeSync(fd)
      offset = stat.size

      buf.toString('utf8')
        .split('\n')
        .map(l => l.trim())
        .filter(Boolean)
        .map(parseLine)
        .forEach(emit)
    } catch {}
  }

  return {
    /** Register an event listener. */
    on(fn: Listener):  void { listeners = [...listeners, fn] },
    /** Unregister an event listener. */
    off(fn: Listener): void { listeners = listeners.filter(l => l !== fn) },

    get isRunning(): boolean { return watcher !== null },

    /**
     * Start tailing the given Client.txt path.
     * Returns `false` if the file does not exist.
     */
    start(clientTxtPath: string): boolean {
      if (watcher) this.stop()
      filePath = clientTxtPath
      if (!fs.existsSync(clientTxtPath)) {
        logger.warn('[clientTxt] path not found:', clientTxtPath)
        return false
      }
      offset  = fs.statSync(clientTxtPath).size
      watcher = chokidar.watch(clientTxtPath, {
        usePolling:       process.platform === 'win32',
        interval:         500,
        awaitWriteFinish: false,
      })
      watcher.on('change', readNew)
      logger.info('[clientTxt] watching', clientTxtPath, `(polling=${process.platform === 'win32'})`)
      return true
    },

    /** Stop tailing and reset state. */
    stop(): void {
      watcher?.close()
      watcher = null
      offset  = 0
    },
  }
}

export const clientTxtWatcher = createClientTxtWatcher()
