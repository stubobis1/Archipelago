import { clipboard } from 'electron'
import { execFile } from 'child_process'
import { promisify } from 'util'
import { settingsService } from './settings'
import { logger } from './logger'
import { clientTxtWatcher } from './clientTxtWatcher'

const execFileAsync = promisify(execFile)

export const DEBOUNCE_MS = 150  // kept for external callers; runtime uses inputDebounceWhisper setting
let lastSendMs = 0

// ── Focus check (via Client.txt [WINDOW] events) ─────────────────────────────
// Old approach used OS APIs (PowerShell GetForegroundWindow / xprop) to poll
// the active window title. Replaced with log-based detection — works on both
// Windows and Linux without spawning subprocesses on every send.
//
// // function xDisplay(): string {
// //   if (process.env.DISPLAY) return process.env.DISPLAY
// //   try {
// //     const sockets = fs.readdirSync('/tmp/.X11-unix').filter(f => /^X\d+$/.test(f))
// //     if (sockets.length > 0) return `:${sockets[0].slice(1)}`
// //   } catch {}
// //   return ':1'
// // }
// //
// // async function getForegroundTitle(): Promise<string> {
// //   if (process.platform === 'win32') {
// //     const script = [
// //       'Add-Type -TypeDefinition \'using System;using System.Runtime.InteropServices;',
// //       'public class W{[DllImport("user32")]public static extern IntPtr GetForegroundWindow();',
// //       '[DllImport("user32")]public static extern int GetWindowText(IntPtr h,System.Text.StringBuilder s,int n);}\';',
// //       '$h=[W]::GetForegroundWindow();$b=New-Object System.Text.StringBuilder(256);',
// //       '[W]::GetWindowText($h,$b,256)|Out-Null;$b.ToString()',
// //     ].join('')
// //     const { stdout } = await execFileAsync('powershell', ['-NoProfile', '-NonInteractive', '-Command', script], { timeout: 4000 })
// //     return stdout.trim()
// //   }
// //   // Linux: xprop on XWayland display (PoE/Proton runs in XWayland)
// //   const display = xDisplay()
// //   const env = { ...process.env, DISPLAY: display }
// //   const { stdout: rootOut } = await execFileAsync('xprop', ['-display', display, '-root', '_NET_ACTIVE_WINDOW'], { timeout: 2000, env })
// //   const winId = rootOut.match(/0x[0-9a-f]+/i)?.[0]
// //   if (!winId) return ''
// //   const { stdout: nameOut } = await execFileAsync('xprop', ['-display', display, '-id', winId, 'WM_NAME', '_NET_WM_NAME'], { timeout: 2000, env })
// //   return nameOut.match(/"(.+)"/)?.[1] ?? ''
// // }

// Tracks PoE window focus state from Client.txt "[WINDOW] Gained/Lost focus" lines.
// Defaults to false; seenFocusEvent tracks whether PoE has ever emitted these lines.
// Some PoE versions/configs don't log [WINDOW] events — if none are ever seen we
// assume focused so queued commands still fire.
let poeWindowFocused = false
let seenFocusEvent   = false

clientTxtWatcher.on(ev => {
  if (ev.type === 'focus') {
    seenFocusEvent   = true
    poeWindowFocused = ev.gained
    logger.debug(`[gameInput] PoE window focus: ${ev.gained ? 'gained' : 'lost'}`)
  }
})

/** Returns `true` if Path of Exile is the foreground window (or focus check is bypassed). */
export async function isPoeFocused(): Promise<boolean> {
  const s = settingsService.get()
  if (s.bypassFocusCheck) return true
  // If PoE never emits [WINDOW] focus events, assume focused rather than blocking all sends.
  if (!seenFocusEvent) return true
  return poeWindowFocused
}

// ── Low-level key send ───────────────────────────────────────────────────────

/** Open chat → paste → send in a single PowerShell invocation to avoid startup-gap timing issues. */
async function sendSequenceWin(command: string): Promise<void> {
  const s = settingsService.get()
  const delayEnter = s.inputDelayEnter ?? 0
  const delayPaste = s.inputDelayPaste ?? 0
  const escaped = command.replace(/'/g, "''")
  const script = [
    `$ErrorActionPreference = 'SilentlyContinue'`,
    `$sh = New-Object -ComObject WScript.Shell`,
    `$prev = Get-Clipboard -Raw`,
    `$sh.SendKeys('{ENTER}')`,
    `Start-Sleep -Milliseconds ${delayEnter}`,
    `Set-Clipboard -Value '${escaped}'`,
    `$sh.SendKeys('^v')`,
    `Start-Sleep -Milliseconds ${delayPaste}`,
    `$sh.SendKeys('{ENTER}')`,
    `try { if ($prev) { Set-Clipboard -Value $prev } } catch {}`,
    `exit 0`,
  ].join('; ')
  const encoded = Buffer.from(script, 'utf16le').toString('base64')
  await execFileAsync('powershell', ['-NoProfile', '-NonInteractive', '-EncodedCommand', encoded], { timeout: 8000 })
}

async function sendSequenceLinux(command: string): Promise<void> {
  const s   = settingsService.get()
  const env = { ...process.env }
  const delay   = (ms: number) => new Promise(r => setTimeout(r, Math.max(ms, 50)))
  const prev = clipboard.readText()
  clipboard.writeText(command)
  // Enter opens chat, ctrl+v pastes, Enter submits
  await execFileAsync('xdotool', ['key', '--clearmodifiers', 'Return'],   { timeout: 3000, env })
  await delay(s.inputDelayPaste ?? 0)
  await execFileAsync('xdotool', ['key', '--clearmodifiers', 'ctrl+v'],   { timeout: 3000, env })
  await delay(s.inputDelayEnter ?? 0)
  await execFileAsync('xdotool', ['key', '--clearmodifiers', 'Return'],   { timeout: 3000, env })
  clipboard.writeText(prev)
}

/** Send one command, assuming PoE is already focused. Debounced to prevent double-sends. */
async function sendImmediate(command: string): Promise<boolean> {
  const now = Date.now()
  const debounce = settingsService.get().inputDebounceWhisper ?? DEBOUNCE_MS
  if (now - lastSendMs < debounce) return false
  lastSendMs = now
  const prev = clipboard.readText()
  try {
    if (process.platform === 'win32') {
      await sendSequenceWin(command)
    } else {
      await sendSequenceLinux(command)
    }
    return true
  } catch (e: any) {
    logger.error('[gameInput] sendImmediate error:', e?.message, '| stderr:', e?.stderr || '(empty)', '| stdout:', e?.stdout || '(empty)')
    return false
  } finally {
    clipboard.writeText(prev)
  }
}

// ── Retry queue ───────────────────────────────────────────────────────────────

interface QueueItem {
  command:  string
  maxTries: number
  tries:    number
  resolve:  (sent: boolean) => void
}

const queue: QueueItem[] = []
let retryTimer:   ReturnType<typeof setInterval> | null = null
let retryRunning  = false

async function tryFlushQueue(): Promise<void> {
  if (retryRunning) return
  if (queue.length === 0) return
  retryRunning = true
  try {
    const focused = await isPoeFocused()
    if (!focused) return
    const item = queue.shift()
    if (!item) return
    const sent = await sendImmediate(item.command)
    if (!sent && item.tries < item.maxTries) {
      queue.unshift({ ...item, tries: item.tries + 1 })
    } else {
      item.resolve(sent)
    }
  } finally {
    retryRunning = false
    if (queue.length === 0 && retryTimer) {
      clearInterval(retryTimer)
      retryTimer = null
    }
  }
}

function startRetryLoop(): void {
  if (retryTimer) return
  retryTimer = setInterval(() => { tryFlushQueue().catch(() => {}) }, 500)
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Send a command immediately if PoE is currently focused.
 * Fire-and-forget; drops silently when PoE is not in the foreground.
 */
export async function openChatAndSend(command: string): Promise<boolean> {
  if (!(await isPoeFocused())) {
    logger.debug('[gameInput] PoE not focused — skipping immediate send')
    return false
  }
  return sendImmediate(command)
}

/**
 * Queue a command to be sent when PoE next becomes focused.
 * Retries up to `maxTries` times (~30 s by default) before giving up.
 */
export function queueChatSend(command: string, maxTries = 60): Promise<boolean> {
  logger.info(`[gameInput] queued: "${command}" (max ${maxTries} retries)`)
  return new Promise(resolve => {
    if (command.startsWith('/itemfilter')) {
      // Drop older /itemfilter entries; only most-recent matters
      const dropped = queue.filter(i => i.command.startsWith('/itemfilter'))
      dropped.forEach(i => i.resolve(false))
      const keep = queue.filter(i => !i.command.startsWith('/itemfilter'))
      queue.length = 0
      queue.push(...keep)
    }
    queue.push({ command, maxTries, tries: 0, resolve })
    startRetryLoop()
    tryFlushQueue().catch(() => {})
  })
}

/** @deprecated Use `openChatAndSend` directly. */
export async function sendPoeText(command: string): Promise<boolean> {
  return openChatAndSend(command)
}
