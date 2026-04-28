// Port of gem-tooltip.js — wiki data cache, fixed tooltip overlay.
// Data: L1 in-memory map, L2 localStorage (2-week TTL).
// Sprite images served locally via ap-assets:// protocol.

const WIKI_API = 'https://www.poewiki.net/api.php'
const CORS_PROXIES = [
  'https://corsproxy.io/?',
  'https://api.allorigins.win/raw?url=',
  'https://corsproxy.io/?',
]
const BATCH_SIZE  = 10
const BATCH_DELAY = 600

const HEADER_IMG_URL = 'ap-assets:///Item-ui-header-single.png'
const SEP_IMG_URL    = 'ap-assets:///Item-ui-separators.png'

const LS_PREFIX = 'gem_wiki_'
const TTL_MS    = 14 * 24 * 60 * 60 * 1000

type GemData = { fields: Record<string, string> } | { notFound: true } | { error: true }

const memCache   = new Map<string, GemData>()
const inflight   = new Map<string, Promise<GemData>>()
const preloading = new Set<string>()

let tipEl:      HTMLElement | null = null
let activeName: string | null      = null

// ── localStorage helpers ──────────────────────────────────────────────────────
function lsGet(name: string): GemData | null {
  try {
    const raw = localStorage.getItem(LS_PREFIX + name)
    if (!raw) return null
    const { data, ts } = JSON.parse(raw) as { data: GemData; ts: number }
    if (Date.now() - ts > TTL_MS) { localStorage.removeItem(LS_PREFIX + name); return null }
    return data
  } catch { return null }
}

function lsSet(name: string, data: GemData) {
  try {
    localStorage.setItem(LS_PREFIX + name, JSON.stringify({ data, ts: Date.now() }))
  } catch { /* quota exceeded — in-memory cache still works */ }
}

// Local files served via ap-assets — use directly in CSS, no fetch needed.
const headerImgCss = `url("${HEADER_IMG_URL}")`
const sepImgCss    = `url("${SEP_IMG_URL}")`

// ── CSS ───────────────────────────────────────────────────────────────────────
function buildCss() {
  return `
#gem-tip {
  position: fixed;
  z-index: 99999;
  pointer-events: none;
  display: none;
}
#gem-tip .item-box {
  display: inline-block;
  box-sizing: border-box;
  border-width: 1px;
  border-style: solid;
  padding: 2px;
  min-width: 220px;
  max-width: 420px;
  text-align: center;
  font-family: 'Fontin SmallCaps','Fontin',FontinSmallCaps,Verdana,Arial,Helvetica,sans-serif;
  font-size: 15px;
  line-height: 1.265;
  font-weight: normal;
  font-style: normal;
  font-variant-ligatures: none;
  color: rgb(127,127,127);
  background-color: #000;
  box-shadow: 0 6px 28px rgba(0,0,0,.92);
}
#gem-tip .item-box.-gem { border-color: rgb(27,162,155); }
#gem-tip .item-box > .header {
  display: block;
  overflow: hidden;
  position: relative;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 20px;
  background-repeat: no-repeat, no-repeat, repeat-x;
}
#gem-tip .item-box.-gem > .header { color: rgb(27,162,155); }
#gem-tip .item-box > .header.-single {
  background-image: ${headerImgCss},${headerImgCss},${headerImgCss};
  padding: 3px 32px;
  height: 28px;
  line-height: 25px;
}
#gem-tip .item-box.-gem > .header.-single {
  background-position: left -306px, right -374px, center -340px;
}
#gem-tip .item-box > .header > .symbol {
  content: "";
  display: block;
  position: absolute;
  top: 0;
  background-position: center;
  background-repeat: no-repeat;
}
#gem-tip .item-box > .header > .symbol:first-child { left: 0; }
#gem-tip .item-box > .header > .symbol:last-child  { right: 0; }
#gem-tip .item-box > .header.-single > .symbol { width: 32px; height: 34px; }
#gem-tip .item-stats { display: block; padding: 7px 12px; margin: 0 auto; }
#gem-tip .item-stats > .group { display: block; margin: 0 auto; }
#gem-tip .item-stats > .group:nth-last-child(n+2)::after {
  display: block;
  margin: 5px auto;
  width: auto;
  height: 3px;
  background-image: ${sepImgCss};
  background-position: center -15px;
  background-repeat: no-repeat;
  content: "";
}
#gem-tip .tc      { font-style: normal; }
#gem-tip em.tc    { font-style: normal; }
#gem-tip em.tc.-i { font-style: italic; }
#gem-tip .tc.-value { color: rgb(255,255,255); }
#gem-tip .tc.-mod {
  font-family: 'Fontin SmallCaps','Fontin',FontinSmallCaps,Verdana,Arial,Helvetica,sans-serif;
  font-variant-ligatures: none;
  color: rgb(136,136,255);
}
#gem-tip .tc.-gemdesc  { color: rgb(27,162,155); }
#gem-tip .tc.-help     { font-style: italic; color: rgb(127,127,127); }
#gem-tip .tc.-corrupted{ color: rgb(210,0,0); }
#gem-tip .gt-spin,
#gem-tip .gt-err {
  min-width: 220px;
  padding: 14px 16px;
  text-align: center;
  font-family: 'Fontin SmallCaps','Fontin',Verdana,Arial,sans-serif;
  font-size: 13px;
  background: #000;
  border: 1px solid rgb(27,162,155);
  box-shadow: 0 6px 28px rgba(0,0,0,.92);
}
#gem-tip .gt-spin { color: rgb(127,127,127); font-style: italic; }
#gem-tip .gt-err  { color: rgb(200,80,80); }
`
}

function injectStyle() {
  let el = document.getElementById('gem-tip-css') as HTMLStyleElement | null
  if (!el) {
    el = document.createElement('style')
    el.id = 'gem-tip-css'
    document.head.appendChild(el)
  }
  el.textContent = buildCss()
}

// ── Wiki fetch ────────────────────────────────────────────────────────────────
async function proxiedFetch(wikiUrl: string): Promise<Response> {
  for (const proxy of CORS_PROXIES) {
    try {
      const r = await fetch(proxy + encodeURIComponent(wikiUrl))
      if (r.ok) return r
    } catch { /* try next */ }
  }
  throw new Error('All proxies failed')
}

async function fetchWikitextBatch(titles: string[]): Promise<Map<string, string>> {
  const params = new URLSearchParams({
    action: 'query', prop: 'revisions',
    titles: titles.join('|'),
    rvslots: 'main', rvprop: 'content', format: 'json',
    redirects: '1',
  })
  const r = await proxiedFetch(`${WIKI_API}?${params}`)
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  const j = await r.json() as {
    query?: {
      redirects?: { from: string; to: string }[]
      pages?: Record<string, { title: string; missing?: unknown; revisions?: { slots: { main: { '*': string } } }[] }>
    }
  }

  // Build redirect target → original queried title map so lookups survive redirects
  const redirectBack = new Map<string, string>()
  for (const rd of j?.query?.redirects ?? []) redirectBack.set(rd.to, rd.from)

  const out = new Map<string, string>()
  for (const page of Object.values(j?.query?.pages ?? {})) {
    const wt = page?.revisions?.[0]?.slots?.main?.['*'] ?? null
    if (!wt || page.missing !== undefined) continue
    // Use original queried title if this page was a redirect target
    const key = redirectBack.get(page.title) ?? page.title
    out.set(key, wt)
  }
  return out
}

function parseFields(wikitext: string): Record<string, string> {
  const data: Record<string, string> = {}
  for (const line of wikitext.split('\n')) {
    const m = line.match(/^\|\s*([A-Za-z_]\w*)\s*=\s*(.*?)\s*$/)
    if (m && !(m[1] in data)) data[m[1]] = m[2]
  }
  return data
}

function fetchGem(name: string): Promise<GemData> {
  if (memCache.has(name)) return Promise.resolve(memCache.get(name)!)
  if (inflight.has(name)) return inflight.get(name)!

  const p = (async (): Promise<GemData> => {
    const stored = lsGet(name)
    if (stored) { memCache.set(name, stored); return stored }

    for (const title of [name, `${name} (gem)`]) {
      const batch = await fetchWikitextBatch([title]).catch(() => new Map<string, string>())
      const wt = batch.get(title)
      if (wt && wt.includes('{{Item')) {
        const data: GemData = { fields: parseFields(wt) }
        memCache.set(name, data); lsSet(name, data)
        return data
      }
    }
    const data: GemData = { notFound: true }
    memCache.set(name, data); lsSet(name, data)
    return data
  })().catch((): GemData => {
    const data: GemData = { error: true }
    memCache.set(name, data)
    return data
  }).finally(() => inflight.delete(name))

  inflight.set(name, p)
  return p
}

// ── Preload (batched) ─────────────────────────────────────────────────────────
export async function preloadGems(names: string[]) {
  const toFetch = names.filter(n => {
    if (memCache.has(n) || preloading.has(n)) return false
    const stored = lsGet(n)
    if (stored !== null) { memCache.set(n, stored); return false }
    return true
  })
  if (!toFetch.length) return

  toFetch.forEach(n => preloading.add(n))

  function store(name: string, data: GemData) {
    memCache.set(name, data); preloading.delete(name); lsSet(name, data)
  }

  for (let i = 0; i < toFetch.length; i += BATCH_SIZE) {
    if (i > 0) await new Promise(r => setTimeout(r, BATCH_DELAY))
    const batch = toFetch.slice(i, i + BATCH_SIZE)
    let results: Map<string, string>
    try { results = await fetchWikitextBatch(batch) }
    catch { batch.forEach(n => preloading.delete(n)); continue }

    const needDisambig: string[] = []
    for (const name of batch) {
      const wt = results.get(name)
      if (wt && wt.includes('{{Item')) store(name, { fields: parseFields(wt) })
      else needDisambig.push(name)
    }
    if (!needDisambig.length) continue

    let dis: Map<string, string>
    try { dis = await fetchWikitextBatch(needDisambig.map(n => `${n} (gem)`)) }
    catch { needDisambig.forEach(n => store(n, { notFound: true })); continue }

    for (const name of needDisambig) {
      const wt = dis.get(`${name} (gem)`)
      store(name, wt && wt.includes('{{Item')
        ? { fields: parseFields(wt) }
        : { notFound: true })
    }
  }
}

// ── HTML builder ──────────────────────────────────────────────────────────────
function v(text: string) { return `<em class="tc -value">${text}</em>` }

function reqRange(lo: string | undefined, hi: string | undefined): string | null {
  if (!lo || lo === '0') return null
  return (!hi || hi === lo) ? lo : `(${lo}-${hi})`
}

function buildHTML(name: string, data: GemData): string {
  if ('notFound' in data) return `<div class="gt-err">No wiki page found for "<strong>${name}</strong>".</div>`
  if ('error'    in data) return `<div class="gt-err">Could not reach poewiki.net — check your connection.</div>`

  const f = data.fields
  const tags     = f.gem_tags         || ''
  const desc     = f.gem_description  || ''
  const helpTxt  = f.help_text        || 'Place into an item socket of the right colour to gain this skill. Right click to remove from a socket.'
  const statTxt  = f.stat_text        || ''
  const qualTxt  = f.quality_type1_stat_text || ''
  const isSupport = tags.toLowerCase().includes('support')

  const rawCast = parseFloat(f.cast_time ?? '0')
  const castT   = (!isNaN(rawCast) && rawCast > 0) ? rawCast.toFixed(2) : null
  const crit    = f.static_critical_strike_chance ? parseFloat(f.static_critical_strike_chance).toFixed(2) : null
  const dmgEff  = f.static_damage_effectiveness || null

  const resPct       = f.static_mana_reservation_percent || null
  const resFlat      = f.static_mana_reservation_flat    || null
  const costTypes    = f.static_cost_types || 'Mana'
  const cost1        = f.level1_cost_amounts  || null
  const cost20       = f.level20_cost_amounts || null
  const costStr      = (cost1 && cost20 && cost1 !== cost20) ? `(${cost1}-${cost20})` : (cost1 || cost20 || null)
  const costResMult  = f.static_cost_and_reservation_multiplier || f.static_cost_multiplier || null
  const supportLetter = f.support_gem_letter || null

  const reqLvl1   = f.required_level || f.level1_level_requirement || null
  const reqLvl20  = f.level20_level_requirement || null
  const reqLvlStr = reqRange(reqLvl1 ?? undefined, reqLvl20 ?? undefined)
  const intPct = parseInt(f.intelligence_percent || '0', 10)
  const strPct = parseInt(f.strength_percent     || '0', 10)
  const dexPct = parseInt(f.dexterity_percent    || '0', 10)
  const intStr = intPct ? reqRange(f.level1_intelligence_requirement, f.level20_intelligence_requirement) : null
  const strStr = strPct ? reqRange(f.level1_strength_requirement,     f.level20_strength_requirement)     : null
  const dexStr = dexPct ? reqRange(f.level1_dexterity_requirement,    f.level20_dexterity_requirement)    : null

  const g1Parts = [tags]
  if (isSupport && supportLetter) {
    const cls = intPct > strPct && intPct > dexPct ? 'blue' : strPct > dexPct ? 'red' : 'green'
    g1Parts.push(`Icon: <span class="support-gem-id-${cls}">${supportLetter}</span>`)
  }
  g1Parts.push(`Level: ${v('(1-20)')}`)
  if (resPct)        g1Parts.push(`Reservation: ${v(`${resPct}% ${costTypes}`)}`)
  else if (resFlat)  g1Parts.push(`Reservation: ${v(`${resFlat} ${costTypes}`)}`)
  else if (costResMult) g1Parts.push(`Cost &amp; Reservation Multiplier: ${v(`${costResMult}%`)}`)
  else if (costStr)  g1Parts.push(`Cost: ${v(`${costStr} ${costTypes}`)}`)
  if (castT)  g1Parts.push(`Cast Time: ${v(`${castT} sec`)}`)
  if (crit)   g1Parts.push(`Critical Strike Chance: ${v(`${crit}%`)}`)
  if (dmgEff) g1Parts.push(`Effectiveness of Added Damage: ${v(`${dmgEff}%`)}`)

  const reqParts: string[] = []
  if (reqLvlStr)        reqParts.push(`Level ${v(reqLvlStr)}`)
  if (intStr && intPct) reqParts.push(`Int ${v(intStr)}`)
  if (strStr && strPct) reqParts.push(`Str ${v(strStr)}`)
  if (dexStr && dexPct) reqParts.push(`Dex ${v(dexStr)}`)

  const modParts: string[] = []
  if (statTxt) modParts.push(statTxt.replace(/<br\s*\/?>/gi, '<br>'))
  if (qualTxt) modParts.push(` <br> ${v(`Additional Effects From 1-20% Quality:<br><em class="tc -mod">${qualTxt}</em>`)}`)

  const groups = [
    `<span class="group">${g1Parts.join('<br>')}</span>`,
    ...(reqParts.length ? [`<span class="group">Requires ${reqParts.join(', ')}</span>`] : []),
    ...(desc            ? [`<span class="group tc -gemdesc">${desc}</span>`]             : []),
    ...(modParts.length ? [`<span class="group tc -mod">${modParts.join('')}</span>`]    : []),
    `<span class="group tc -help">${helpTxt}</span>`,
  ]

  return `<span class="item-box -gem">
    <span class="header -single"><span class="symbol"></span>${name}<span class="symbol"></span></span>
    <span class="item-stats">${groups.join('')}</span>
  </span>`
}

// ── Position / show / hide ────────────────────────────────────────────────────
function pos(x: number, y: number) {
  if (!tipEl) return
  const W  = window.innerWidth
  const H  = window.innerHeight
  const tw = (tipEl.firstElementChild as HTMLElement | null)?.offsetWidth  || 420 + 20
  const th = (tipEl.firstElementChild as HTMLElement | null)?.offsetHeight || 200 + 20
  tipEl.style.left = Math.max(4, x + tw > W - 50 ? x - tw : x + 14) + 'px'
  tipEl.style.top  = Math.max(4, y + th > H ? y - th : y + 14) + 'px'
}

export async function showGemTooltip(e: MouseEvent, name: string) {
  if (!tipEl) return
  activeName = name
  tipEl.innerHTML = `<div class="gt-spin">${name}…</div>`
  tipEl.style.display = 'block'
  pos(e.clientX, e.clientY)
  const data = await fetchGem(name)
  if (activeName !== name) return
  tipEl.innerHTML = buildHTML(name, data)
  tipEl.style.display = 'block'
  pos(e.clientX, e.clientY)
}

export function hideGemTooltip() {
  activeName = null
  if (tipEl) tipEl.style.display = 'none'
}

export function moveGemTooltip(e: MouseEvent) {
  if (tipEl?.style.display !== 'none') pos(e.clientX, e.clientY)
}

// ── Init (call once) ──────────────────────────────────────────────────────────
let initialized = false

export function initGemTooltips() {
  if (initialized) return
  initialized = true
  injectStyle()
  if (!document.getElementById('gem-tip')) {
    tipEl = document.createElement('div')
    tipEl.id = 'gem-tip'
    document.body.appendChild(tipEl)
  } else {
    tipEl = document.getElementById('gem-tip')
  }
  ;(window as any).gemTooltip = { clearCache: clearGemCache }
}

export function clearGemCache() {
  const keys = Object.keys(localStorage).filter(k => k.startsWith(LS_PREFIX))
  keys.forEach(k => localStorage.removeItem(k))
  memCache.clear()
}
