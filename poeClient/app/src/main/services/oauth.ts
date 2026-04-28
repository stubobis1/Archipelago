import { BrowserWindow } from 'electron'
import * as crypto from 'crypto'
import * as https from 'https'
import { settingsService } from './settings'

const CLIENT_ID    = 'archipelagopoe'
const REDIRECT_URI = 'http://127.0.0.1:8234/oauth-callback'
const SCOPES       = 'account:profile account:characters account:stashes account:leagues'
const AUTH_URL     = 'https://www.pathofexile.com/oauth/authorize'
const TOKEN_URL    = 'https://www.pathofexile.com/oauth/token'

function base64url(buf: Buffer): string {
  return buf.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')
}

function generatePKCE(): { verifier: string; challenge: string } {
  const verifier  = base64url(crypto.randomBytes(32))
  const challenge = base64url(crypto.createHash('sha256').update(verifier).digest())
  return { verifier, challenge }
}

function httpsPost(url: string, body: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const u = new URL(url)
    const req = https.request({
      hostname: u.hostname,
      path:     u.pathname,
      method:   'POST',
      headers: {
        'Content-Type':   'application/x-www-form-urlencoded',
        'Content-Length': Buffer.byteLength(body),
        'User-Agent':     'archipelago-poe-client/0.1',
      }
    }, res => {
      let data = ''
      res.on('data', chunk => (data += chunk))
      res.on('end', () => resolve(data))
    })
    req.on('error', reject)
    req.write(body)
    req.end()
  })
}

let activeWin: BrowserWindow | null = null

/**
 * Open a GGG OAuth2 login window using PKCE.
 * Blocks until the user completes (or closes) the popup, then persists the
 * access token and expiry into settings.
 */
export async function startOAuthFlow(): Promise<void> {
  const { verifier, challenge } = generatePKCE()
  const state = base64url(crypto.randomBytes(16))

  const params = new URLSearchParams({
    client_id:             CLIENT_ID,
    response_type:         'code',
    redirect_uri:          REDIRECT_URI,
    scope:                 SCOPES,
    state,
    code_challenge:        challenge,
    code_challenge_method: 'S256',
  })

  const authUrl = `${AUTH_URL}?${params}`

  activeWin = new BrowserWindow({
    width: 900, height: 700,
    title: 'GGG Login',
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  })

  activeWin.loadURL(authUrl)

  await new Promise<void>((resolve, reject) => {
    const win = activeWin!
    win.webContents.on('will-redirect', async (_ev, url) => {
      if (!url.startsWith(REDIRECT_URI)) return
      const u    = new URL(url)
      const code = u.searchParams.get('code')
      if (!code) { reject(new Error('No code in redirect')); win.close(); return }

      try {
        const tokenBody = new URLSearchParams({
          client_id:     CLIENT_ID,
          grant_type:    'authorization_code',
          code,
          redirect_uri:  REDIRECT_URI,
          code_verifier: verifier,
        }).toString()

        const raw  = await httpsPost(TOKEN_URL, tokenBody)
        const json = JSON.parse(raw)
        if (json.error) throw new Error(json.error_description ?? json.error)

        const expires = Date.now() + json.expires_in * 1000
        settingsService.setMany({
          oauthToken:   json.access_token,
          oauthExpires: expires,
        })

        win.close()
        resolve()
      } catch (e) {
        win.close()
        reject(e)
      }
    })

    win.on('closed', () => {
      activeWin = null
      resolve()
    })
  })
}

/** Returns the stored OAuth token if it exists and has not expired, otherwise `null`. */
export function getValidToken(): string | null {
  const s = settingsService.get()
  if (!s.oauthToken || !s.oauthExpires) return null
  if (Date.now() >= s.oauthExpires) return null
  return s.oauthToken
}

/** Wipe the stored OAuth token, expiry, and linked poeUuid from settings. */
export function clearToken(): void {
  settingsService.setMany({ oauthToken: null, oauthExpires: null, poeUuid: null })
}

/** Returns a human-readable time remaining string (`"4h"`, `"2d"`) or `null` if expired/absent. */
export function tokenTimeLeft(): string | null {
  const s = settingsService.get()
  if (!s.oauthToken || !s.oauthExpires) return null
  const ms = s.oauthExpires - Date.now()
  if (ms <= 0) return null
  const hours = Math.floor(ms / 3_600_000)
  if (hours < 1) return `${Math.ceil(ms / 60_000)}m`
  return hours < 24 ? `${hours}h` : `${Math.floor(hours / 24)}d`
}
