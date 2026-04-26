import { describe, it, expect, vi, beforeEach } from 'vitest'
import { parseLine } from '../main/services/clientTxtWatcher'

// ── parseLine (pure function, no mocks needed) ────────────────────────────────

describe('parseLine', () => {
  it('parses zone entry', () => {
    const line = '2024/01/01 12:00:00 1 a [INFO Client 1] : You have entered The Mud Flats.'
    expect(parseLine(line)).toEqual({ type: 'zone', zone: 'The Mud Flats' })
  })

  it('parses multi-word zone name', () => {
    const line = '2024/01/01 12:00:00 1 a [INFO Client 1] : You have entered Karui Shores.'
    expect(parseLine(line)).toEqual({ type: 'zone', zone: 'Karui Shores' })
  })

  it('parses player death', () => {
    const line = '2024/01/01 12:00:00 1 a [INFO Client 1] StuBob has been slain.'
    expect(parseLine(line)).toEqual({ type: 'death', who: 'StuBob' })
  })

  it('parses spaced player name death', () => {
    const line = '2024/01/01 12:00:00 1 a [INFO Client 1] Some Player has been slain.'
    expect(parseLine(line)).toEqual({ type: 'death', who: 'Some Player' })
  })

  it('parses local chat message', () => {
    const ev = parseLine('2024/01/01 12:00:00 1 a [INFO Client 1] PlayerName: hello world')
    expect(ev).toMatchObject({ type: 'chat', who: 'PlayerName', msg: 'hello world' })
  })

  it('parses @From whisper', () => {
    const ev = parseLine('2024/01/01 12:00:00 1 a [INFO Client 1] @From SomePlayer: hi')
    expect(ev.type).toBe('chat')
  })

  it('returns raw for unrecognised lines', () => {
    expect(parseLine('random log line')).toEqual({ type: 'raw', line: 'random log line' })
  })
})

// ── watcher lifecycle (chokidar + fs mocked) ──────────────────────────────────

// Capture the change handler registered by the watcher
let onChangeFn: (() => void) | null = null
const fakeWatcher = {
  on:    vi.fn((ev: string, fn: () => void) => { if (ev === 'change') onChangeFn = fn }),
  close: vi.fn(),
}

vi.mock('chokidar', () => ({
  default: { watch: vi.fn(() => fakeWatcher) },
}))

// Simple fs mock — size starts at 0, content can be set per test
let fakeSize    = 0
let fakeContent = ''

vi.mock('fs', () => ({
  existsSync: vi.fn(() => true),
  statSync:   vi.fn(() => ({ size: fakeSize })),
  openSync:   vi.fn(() => 42),
  readSync:   vi.fn((fd: number, buf: Buffer) => {
    buf.write(fakeContent, 0, fakeContent.length, 'utf8')
    return fakeContent.length
  }),
  closeSync:  vi.fn(),
}))

beforeEach(() => {
  onChangeFn  = null
  fakeSize    = 0
  fakeContent = ''
  vi.mocked(fakeWatcher.close).mockClear()
  vi.mocked(fakeWatcher.on).mockClear()
  vi.resetModules()
})

describe('watcher.start / isRunning / stop', () => {
  it('returns false and stays not running when file missing', async () => {
    const { existsSync } = await import('fs')
    vi.mocked(existsSync).mockReturnValueOnce(false)
    const { clientTxtWatcher: w } = await import('../main/services/clientTxtWatcher')
    expect(w.start('/no/file.txt')).toBe(false)
    expect(w.isRunning).toBe(false)
  })

  it('returns true and isRunning when file exists', async () => {
    const { clientTxtWatcher: w } = await import('../main/services/clientTxtWatcher')
    expect(w.start('/poe/logs/Client.txt')).toBe(true)
    expect(w.isRunning).toBe(true)
  })

  it('stops watcher and clears isRunning', async () => {
    const { clientTxtWatcher: w } = await import('../main/services/clientTxtWatcher')
    w.start('/poe/logs/Client.txt')
    w.stop()
    expect(w.isRunning).toBe(false)
    expect(fakeWatcher.close).toHaveBeenCalled()
  })

  it('stops old watcher before starting new one', async () => {
    const { clientTxtWatcher: w } = await import('../main/services/clientTxtWatcher')
    w.start('/poe/logs/Client.txt')
    w.start('/poe/logs/Client.txt')
    expect(fakeWatcher.close).toHaveBeenCalledTimes(1)
  })
})

describe('watcher readNew — file change events', () => {
  it('emits zone event on zone line', async () => {
    const { clientTxtWatcher: w } = await import('../main/services/clientTxtWatcher')
    const events: any[] = []
    w.on(ev => events.push(ev))
    w.start('/poe/logs/Client.txt')

    fakeContent = '2024/01/01 12:00:00 1 a [INFO Client 1] : You have entered The Mud Flats.\n'
    fakeSize    = Buffer.byteLength(fakeContent)
    onChangeFn?.()

    expect(events).toContainEqual({ type: 'zone', zone: 'The Mud Flats' })
  })

  it('emits death event on death line', async () => {
    const { clientTxtWatcher: w } = await import('../main/services/clientTxtWatcher')
    const events: any[] = []
    w.on(ev => events.push(ev))
    w.start('/poe/logs/Client.txt')

    fakeContent = '2024/01/01 12:00:00 1 a [INFO Client 1] StuBob has been slain.\n'
    fakeSize    = Buffer.byteLength(fakeContent)
    onChangeFn?.()

    expect(events).toContainEqual({ type: 'death', who: 'StuBob' })
  })

  it('emits chat event on chat line', async () => {
    const { clientTxtWatcher: w } = await import('../main/services/clientTxtWatcher')
    const events: any[] = []
    w.on(ev => events.push(ev))
    w.start('/poe/logs/Client.txt')

    fakeContent = '2024/01/01 12:00:00 1 a [INFO Client 1] Player: hello\n'
    fakeSize    = Buffer.byteLength(fakeContent)
    onChangeFn?.()

    expect(events.some(e => e.type === 'chat')).toBe(true)
  })

  it('does not emit when file size unchanged', async () => {
    const { clientTxtWatcher: w } = await import('../main/services/clientTxtWatcher')
    const events: any[] = []
    w.on(ev => events.push(ev))
    // Start sets offset = fakeSize (0); no content added
    w.start('/poe/logs/Client.txt')
    onChangeFn?.()
    expect(events).toHaveLength(0)
  })

  it('on/off removes listener', async () => {
    const { clientTxtWatcher: w } = await import('../main/services/clientTxtWatcher')
    const events: any[] = []
    const listener = (ev: any) => events.push(ev)
    w.on(listener)
    w.off(listener)
    w.start('/poe/logs/Client.txt')

    fakeContent = '2024/01/01 12:00:00 1 a [INFO Client 1] : You have entered X.\n'
    fakeSize    = Buffer.byteLength(fakeContent)
    onChangeFn?.()

    expect(events).toHaveLength(0)
  })
})
