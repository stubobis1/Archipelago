import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mutable state lets us change mock behavior without post-reset identity issues
let execFileStdout = ''
let execFileError: Error | null = null

// child_process must be mocked before module import.
// execFile can be called as (cmd, args, cb) or (cmd, args, opts, cb) — handle both.
vi.mock('child_process', () => ({
  execFile: vi.fn((_cmd: string, _args: string[], _optsOrCb: any, _cb?: any) => {
    const cb = typeof _cb === 'function' ? _cb : _optsOrCb
    cb(execFileError, execFileStdout, '')
    return {} as any
  }),
}))

// Settings mock — reads from mutable variable so module resets pick up current value
let mockSettings: any = { bypassFocusCheck: false, inputDelayEnter: 0, inputDelayPaste: 0 }
vi.mock('../main/services/settings', () => ({
  settingsService: { get: vi.fn(() => mockSettings) },
}))

beforeEach(() => {
  execFileStdout = ''
  execFileError  = null
  mockSettings   = { bypassFocusCheck: false, inputDelayEnter: 0, inputDelayPaste: 0 }
})

afterEach(() => {
  vi.useRealTimers()
})

// Reset modules + return fresh spy + fresh module.
// Import child_process BEFORE gameInput so both share the same fresh mock instance.
async function freshGameInput() {
  vi.resetModules()
  const cp  = await import('child_process') as any
  const mod = await import('../main/services/gameInput')
  return { mod, execFile: cp.execFile as ReturnType<typeof vi.fn> }
}

// ── isPoeFocused ──────────────────────────────────────────────────────────────

describe('isPoeFocused', () => {
  it('returns true immediately when bypassFocusCheck=true (no PowerShell)', async () => {
    mockSettings = { bypassFocusCheck: true }
    const { mod, execFile } = await freshGameInput()
    expect(await mod.isPoeFocused()).toBe(true)
    expect(execFile).not.toHaveBeenCalled()
  })

  it('returns false when foreground window is not PoE', async () => {
    execFileStdout = 'Discord\n'
    const { mod } = await freshGameInput()
    expect(await mod.isPoeFocused()).toBe(false)
  })

  it('returns true when foreground window is Path of Exile', async () => {
    execFileStdout = 'Path of Exile\n'
    const { mod } = await freshGameInput()
    expect(await mod.isPoeFocused()).toBe(true)
  })

  it('returns false on PowerShell error', async () => {
    execFileError = new Error('timeout')
    const { mod } = await freshGameInput()
    expect(await mod.isPoeFocused()).toBe(false)
  })
})

// ── DEBOUNCE_MS ───────────────────────────────────────────────────────────────

describe('DEBOUNCE_MS', () => {
  it('is exported as a positive number', async () => {
    const { mod } = await freshGameInput()
    expect(typeof mod.DEBOUNCE_MS).toBe('number')
    expect(mod.DEBOUNCE_MS).toBeGreaterThan(0)
  })
})

// ── openChatAndSend ───────────────────────────────────────────────────────────

describe('openChatAndSend', () => {
  it('returns false when PoE not focused', async () => {
    execFileStdout = 'Discord\n'
    const { mod } = await freshGameInput()
    expect(await mod.openChatAndSend('/tp someplace')).toBe(false)
  })

  it('sends command and returns true when bypass=true', async () => {
    mockSettings = { bypassFocusCheck: true, inputDelayEnter: 0, inputDelayPaste: 0 }
    const { mod } = await freshGameInput()
    expect(await mod.openChatAndSend('/itemfilter __ap')).toBe(true)
  })
})

// ── queueChatSend ─────────────────────────────────────────────────────────────

describe('queueChatSend', () => {
  it('resolves true when bypass=true and send succeeds', async () => {
    mockSettings = { bypassFocusCheck: true, inputDelayEnter: 0, inputDelayPaste: 0 }
    vi.useFakeTimers()
    const { mod } = await freshGameInput()
    const promise = mod.queueChatSend('/itemfilter __ap', 1)
    // Fake timers start at system time → Date.now() >> 1000 → debounce passes on first tick
    await vi.advanceTimersByTimeAsync(600)
    vi.useRealTimers()
    expect(await promise).toBe(true)
  }, 15_000)
})
