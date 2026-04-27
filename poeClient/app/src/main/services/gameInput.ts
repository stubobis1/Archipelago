import { clipboard } from 'electron'
import { execFile } from 'child_process'
import { promisify } from 'util'
import * as fs from 'fs'
import { settingsService } from './settings'
import { logger } from './logger'

const execFileAsync = promisify(execFile)

export const DEBOUNCE_MS = 1000
let lastSendMs = 0

// ── Focus check ──────────────────────────────────────────────────────────────

function xDisplay(): string {
  if (process.env.DISPLAY) return process.env.DISPLAY
  try {
    const sockets = fs.readdirSync('/tmp/.X11-unix').filter(f => /^X\d+$/.test(f))
    if (sockets.length > 0) return `:${sockets[0].slice(1)}`
  } catch {}
  return ':1'
}

async function getForegroundTitle(): Promise<string> {
  if (process.platform === 'win32') {
    const script = [
      'Add-Type -TypeDefinition \'using System;using System.Runtime.InteropServices;',
      'public class W{[DllImport("user32")]public static extern IntPtr GetForegroundWindow();',
      '[DllImport("user32")]public static extern int GetWindowText(IntPtr h,System.Text.StringBuilder s,int n);}\';',
      '$h=[W]::GetForegroundWindow();$b=New-Object System.Text.StringBuilder(256);',
      '[W]::GetWindowText($h,$b,256)|Out-Null;$b.ToString()',
    ].join('')
    const { stdout } = await execFileAsync('powershell', ['-NoProfile', '-NonInteractive', '-Command', script], { timeout: 4000 })
    return stdout.trim()
  }
  // Linux: xprop on XWayland display (PoE/Proton runs in XWayland)
  const display = xDisplay()
  const env = { ...process.env, DISPLAY: display }
  const { stdout: rootOut } = await execFileAsync('xprop', ['-display', display, '-root', '_NET_ACTIVE_WINDOW'], { timeout: 2000, env })
  const winId = rootOut.match(/0x[0-9a-f]+/i)?.[0]
  if (!winId) return ''
  const { stdout: nameOut } = await execFileAsync('xprop', ['-display', display, '-id', winId, 'WM_NAME', '_NET_WM_NAME'], { timeout: 2000, env })
  return nameOut.match(/"(.+)"/)?.[1] ?? ''
}

/** Returns `true` if Path of Exile is the foreground window (or focus check is bypassed). */
export async function isPoeFocused(): Promise<boolean> {
  const s = settingsService.get()
  if (s.bypassFocusCheck) return true
  try {
    const title = await getForegroundTitle()
    return title.toLowerCase().includes('path of exile')
  } catch {
    logger.warn('[gameInput] isPoeFocused error — assuming not focused')
    return false
  }
}

// ── Low-level key send ───────────────────────────────────────────────────────

/** Open chat → paste → send in a single PowerShell invocation to avoid startup-gap timing issues. */
async function sendSequenceWin(command: string): Promise<void> {
  const s = settingsService.get()
  const delayEnter = s.inputDelayEnter ?? 0
  const delayPaste = s.inputDelayPaste ?? 0
  const escaped = command.replace(/'/g, "''")
  const script = [
    `$sh = New-Object -ComObject WScript.Shell`,
    `$sh.SendKeys('{ENTER}')`,
    `Start-Sleep -Milliseconds ${delayEnter}`,
    `Set-Clipboard -Value '${escaped}'`,
    `$sh.SendKeys('^v')`,
    `Start-Sleep -Milliseconds ${delayPaste}`,
    `$sh.SendKeys('{ENTER}')`,
  ].join('; ')
  await execFileAsync('powershell', ['-NoProfile', '-NonInteractive', '-Command', script], { timeout: 8000 })
}

async function sendSequenceLinux(command: string): Promise<void> {
  const s       = settingsService.get()
  const display = xDisplay()
  const env     = { ...process.env, DISPLAY: display }
  const delay   = (ms: number) => new Promise(r => setTimeout(r, Math.max(ms, 50)))
  clipboard.writeText(command)
  // Enter opens chat, ctrl+v pastes, Enter submits
  await execFileAsync('xdotool', ['key', '--clearmodifiers', 'Return'],   { timeout: 3000, env })
  await delay(s.inputDelayPaste ?? 0)
  await execFileAsync('xdotool', ['key', '--clearmodifiers', 'ctrl+v'],   { timeout: 3000, env })
  await delay(s.inputDelayEnter ?? 0)
  await execFileAsync('xdotool', ['key', '--clearmodifiers', 'Return'],   { timeout: 3000, env })
}

/** Send one command, assuming PoE is already focused. Debounced to prevent double-sends. */
async function sendImmediate(command: string): Promise<boolean> {
  const now = Date.now()
  if (now - lastSendMs < DEBOUNCE_MS) return false
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
    logger.error('[gameInput] sendImmediate error:', e?.message)
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

function startRetryLoop(): void {
  if (retryTimer) return
  retryTimer = setInterval(async () => {
    if (retryRunning) return
    if (queue.length === 0) {
      clearInterval(retryTimer!)
      retryTimer = null
      return
    }
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
    }
  }, 500)
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
    queue.push({ command, maxTries, tries: 0, resolve })
    startRetryLoop()
  })
}

/** @deprecated Use `openChatAndSend` directly. */
export async function sendPoeText(command: string): Promise<boolean> {
  return openChatAndSend(command)
}
