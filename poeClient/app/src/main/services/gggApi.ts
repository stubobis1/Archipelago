import * as https from 'https'
import { getValidToken } from './oauth'

// Rate limiter: max 60/min, min 1s between requests
class RateLimiter {
  private queue: Array<() => void> = []
  private lastMs  = 0
  private tokens  = 60
  private readonly maxTokens = 60
  private readonly minGapMs  = 1000

  acquire(): Promise<void> {
    return new Promise(resolve => {
      this.queue.push(resolve)
      this.drain()
    })
  }

  private drain(): void {
    if (this.queue.length === 0) return
    const now  = Date.now()
    const wait = Math.max(0, this.lastMs + this.minGapMs - now)
    setTimeout(() => {
      if (this.tokens <= 0) { setTimeout(() => this.drain(), 500); return }
      const cb = this.queue.shift()
      if (!cb) return
      this.tokens--
      this.lastMs = Date.now()
      setTimeout(() => { this.tokens = Math.min(this.tokens + 1, this.maxTokens) }, 60_000)
      cb()
      this.drain()
    }, wait)
  }
}

const limiter = new RateLimiter()

function httpsGet(path: string, token: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const req = https.request({
      hostname: 'api.pathofexile.com',
      path,
      method:   'GET',
      headers: {
        Authorization: `Bearer ${token}`,
        'User-Agent':  'OAuth archipelago-poe-client/0.1 (contact: mr.stubob@gmail.com)',
        Accept:        'application/json',
      }
    }, res => {
      let data = ''
      res.on('data', c => (data += c))
      res.on('end', () => resolve(data))
    })
    req.on('error', reject)
    req.end()
  })
}

async function apiGet<T>(path: string): Promise<T> {
  const token = getValidToken()
  if (!token) throw new Error('No valid OAuth token')
  await limiter.acquire()
  const raw  = await httpsGet(path, token)
  const json = JSON.parse(raw)
  if (json.error) throw new Error(json.error.message ?? String(json.error))
  return json as T
}

export interface GGGCharacter {
  name:      string
  class:     string
  level:     number
  league:    string
  equipment?: Record<string, unknown>
  inventory?: unknown[]
  jewels?:    unknown[]
  passives?:  unknown
}

export async function fetchCharacter(name: string): Promise<GGGCharacter> {
  const res = await apiGet<{ character: GGGCharacter }>(`/character/${encodeURIComponent(name)}`)
  return res.character
}

export async function fetchCharacterList(): Promise<{ name: string; class: string; level: number; league: string }[]> {
  if (_charListCache && Date.now() - _charListCacheMs < CHAR_LIST_TTL) return _charListCache
  if (_charListInflight) return _charListInflight
  _charListInflight = (async () => {
    const res = await apiGet<{ characters: { name: string; class: string; level: number; league: string }[] }>('/character')
    _charListCache   = res.characters ?? []
    _charListCacheMs = Date.now()
    _charListInflight = null
    return _charListCache
  })()
  return _charListInflight
}

export async function fetchStashTabs(league: string): Promise<{ id: string; name: string; type: string }[]> {
  const res = await apiGet<{ stashes: { id: string; name: string; type: string }[] }>(
    `/stash/${encodeURIComponent(league)}`
  )
  return res.stashes ?? []
}

let _charListCache:    { name: string; class: string; level: number; league: string }[] | null = null
let _charListCacheMs = 0
let _charListInflight: Promise<{ name: string; class: string; level: number; league: string }[]> | null = null
const CHAR_LIST_TTL  = 60_000  // 60s

let _cachedChar: GGGCharacter | null = null
let _cacheTime = 0

export async function getCachedCharacter(name: string, forceRefresh = false): Promise<GGGCharacter | null> {
  if (!forceRefresh && _cachedChar && _cachedChar.name === name && Date.now() - _cacheTime < 30_000) {
    return _cachedChar
  }
  try {
    _cachedChar  = await fetchCharacter(name)
    _cacheTime   = Date.now()
    return _cachedChar
  } catch {
    return _cachedChar
  }
}

export function clearCharCache(): void {
  _cachedChar = null
  _cacheTime  = 0
}
