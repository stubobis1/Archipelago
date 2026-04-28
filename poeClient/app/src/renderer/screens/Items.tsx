import React, { useState, useRef, useEffect } from 'react'
import { useStore } from '../store'
import type { ReceivedItem, APHint } from '@shared/types'
import { initGemTooltips, preloadGems, showGemTooltip, hideGemTooltip, moveGemTooltip } from '../services/gemTooltip'
import { PaperDoll } from '../components/PaperDoll'

const CLASS_TREE = [
  { base: 'Marauder', asc: ['Berserker', 'Chieftain', 'Juggernaut'] },
  { base: 'Duelist',  asc: ['Champion', 'Gladiator', 'Slayer'] },
  { base: 'Scion',    asc: ['Ascendant', 'Reliquarian'] },
  { base: 'Ranger',   asc: ['Deadeye', 'Pathfinder', 'Warden'] },
  { base: 'Shadow',   asc: ['Assassin', 'Saboteur', 'Trickster'] },
  { base: 'Witch',    asc: ['Elementalist', 'Necromancer', 'Occultist'] },
  { base: 'Templar',  asc: ['Guardian', 'Hierophant', 'Inquisitor'] },
]

const CAT_ORDER = ['Skill Gems', 'Support Gems', 'Utility Gems', 'Flasks', 'Weapons', 'Armour', 'Progression', 'Other']
const CAT_CSS: Record<string, string> = {
  'Skill Gems':   'gem',
  'Support Gems': 'support',
  'Utility Gems': 'util',
  'Flasks':       'flask',
  'Weapons':      'weapon',
  'Armour':       'armour',
  'Progression':  'prog',
}

function imgUrl(name: string) {
  return `ap-assets:///images/${name.toLowerCase().replace(/['\s]/g, '')}.png`
}

function categorizeItem(item: ReceivedItem): string {
  const cats = item.category ?? []
  if (cats.includes('Level') || cats.includes('max links')) return 'Progression'
  if (cats[0] === 'Flask') return 'Flasks'
  if (cats.includes('Base Class')) return 'Classes'
  if (cats.includes('Ascendancy')) return 'Ascendancies'
  if (cats[0] === 'MainSkillGem') return 'Skill Gems'
  if (cats[0] === 'SupportGem') return 'Support Gems'
  if (cats[0] === 'UtilSkillGem') return 'Utility Gems'
  if (cats.includes('Weapon') || cats.includes('Fishing Rod')) return 'Weapons'
  if (cats.includes('Armour')) return 'Armour'
  if (item.name.endsWith(' Support')) return 'Support Gems'
  if (/flask/i.test(item.name)) return 'Flasks'
  return 'Other'
}

function ItemTag({ name, count, css, isGem }: { name: string; count: number; css: string; isGem?: boolean }) {
  const handlers = isGem ? {
    onMouseEnter: (e: React.MouseEvent) => showGemTooltip(e.nativeEvent, name),
    onMouseLeave: () => hideGemTooltip(),
    onMouseMove:  (e: React.MouseEvent) => moveGemTooltip(e.nativeEvent),
  } : {}
  return (
    <span className={`item-tag ${css}`} style={isGem ? { cursor: 'default' } : undefined} {...handlers}>
      <img className="item-img" src={imgUrl(name)} alt=""
        onError={e => { (e.target as HTMLImageElement).style.display = 'none' }} />
      {name}
      {count > 1 && <span className="item-count">×{count}</span>}
    </span>
  )
}

const GEM_CATS = new Set(['Skill Gems', 'Support Gems', 'Utility Gems'])

function CatSection({ cat, entries }: { cat: string; entries: [string, number][] }) {
  const [collapsed, setCollapsed] = useState(false)
  const css   = CAT_CSS[cat] ?? ''
  const isGem = GEM_CATS.has(cat)
  const total = entries.reduce((s, [, c]) => s + c, 0)
  return (
    <div className="cat-section">
      <div className={`cat-header ${collapsed ? 'collapsed' : ''}`} onClick={() => setCollapsed(v => !v)}>
        <span className="collapse-icon">{collapsed ? '▸' : '▾'}</span>
        <h3>{cat}</h3>
        <span className="cat-count">{entries.length} types · {total} total</span>
      </div>
      {!collapsed && (
        <div className="cat-body">
          {entries.map(([name, count]) => (
            <ItemTag key={name} name={name} count={count} css={css} isGem={isGem} />
          ))}
        </div>
      )}
    </div>
  )
}

function ClassSection({ receivedNames }: { receivedNames: Set<string> }) {
  const [collapsed, setCollapsed] = useState(false)
  const allAsc = CLASS_TREE.flatMap(r => r.asc)
  const got    = CLASS_TREE.filter(r => receivedNames.has(r.base)).length + allAsc.filter(a => receivedNames.has(a)).length
  const total  = CLASS_TREE.length + allAsc.length
  return (
    <div className="cat-section">
      <div className={`class-section-header ${collapsed ? 'collapsed' : ''}`} onClick={() => setCollapsed(v => !v)}>
        <span className="collapse-icon">{collapsed ? '▸' : '▾'}</span>
        <h3>Classes &amp; Ascendancies</h3>
        <span className="cat-count">{got} / {total}</span>
      </div>
      {!collapsed && (
        <div className="class-rows">
          {[CLASS_TREE.slice(0, 3), CLASS_TREE.slice(3, 5), CLASS_TREE.slice(5)].map((group, gi) => (
            <div className="class-col" key={gi}>
              {group.map(({ base, asc }) => (
                <div className="class-row" key={base}>
                  <div className={`class-card base ${receivedNames.has(base) ? 'received' : ''}`}>
                    <img src={imgUrl(base)} alt="" onError={e => { (e.target as HTMLImageElement).style.display = 'none' }} />
                    <span>{base}</span>
                  </div>
                  {asc.map(a => (
                    <div key={a} className={`class-card asc ${receivedNames.has(a) ? 'received' : ''}`}>
                      <img src={imgUrl(a)} alt="" onError={e => { (e.target as HTMLImageElement).style.display = 'none' }} />
                      <span>{a}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function HintComboBox({ value, onChange, items: names }: { value: string; onChange: (v: string) => void; items: string[] }) {
  const [open, setOpen] = useState(false)
  const [activeIdx, setActiveIdx] = useState(-1)
  const wrapRef = useRef<HTMLDivElement>(null)
  const listRef = useRef<HTMLUListElement>(null)

  const filtered = value.trim()
    ? names.filter(n => n.toLowerCase().includes(value.toLowerCase()))
    : names

  useEffect(() => {
    setActiveIdx(-1)
  }, [value])

  useEffect(() => {
    if (!open) return
    function onDown(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [open])

  function select(name: string) {
    onChange(name)
    setOpen(false)
  }

  function onKey(e: React.KeyboardEvent) {
    if (!open && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) { setOpen(true); return }
    if (!open) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      const next = Math.min(activeIdx + 1, filtered.length - 1)
      setActiveIdx(next)
      listRef.current?.children[next]?.scrollIntoView({ block: 'nearest' })
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      const prev = Math.max(activeIdx - 1, 0)
      setActiveIdx(prev)
      listRef.current?.children[prev]?.scrollIntoView({ block: 'nearest' })
    } else if (e.key === 'Enter') {
      if (activeIdx >= 0 && filtered[activeIdx]) select(filtered[activeIdx])
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <div ref={wrapRef} style={{ position: 'relative', flex: 1 }}>
      <input
        className="input mono" style={{ width: '100%', fontSize: 12, boxSizing: 'border-box' }}
        placeholder="Item name to hint…"
        value={value}
        onChange={e => { onChange(e.target.value); setOpen(true) }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKey}
      />
      {open && filtered.length > 0 && (
        <ul ref={listRef} style={{
          position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 100,
          margin: 0, padding: '4px 0', listStyle: 'none',
          background: 'var(--bg-3)', border: '1px solid var(--rule-2)',
          borderRadius: 5, maxHeight: 280, overflowY: 'auto',
          boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
        }}>
          {filtered.map((n, i) => (
            <li key={n}
              onMouseDown={() => select(n)}
              onMouseEnter={() => setActiveIdx(i)}
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '5px 10px', cursor: 'default', fontSize: 12,
                background: i === activeIdx ? 'var(--accent-soft)' : 'transparent',
                color: i === activeIdx ? 'var(--ink)' : 'var(--ink-2)',
              }}>
              <img src={imgUrl(n)} alt="" style={{ width: 22, height: 22, objectFit: 'contain', flexShrink: 0 }}
                onError={e => { (e.target as HTMLImageElement).style.display = 'none' }} />
              <span className="mono">{n}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function HintsSection({ hints }: { hints: APHint[] }) {
  const action = useStore(s => s.action)
  const { items } = useStore()
  const [hintInput, setHintInput] = useState('')
  const itemNames = [...new Set(items.map(i => i.name))].sort()

  function sendHint() {
    const v = hintInput.trim()
    if (!v) return
    action({ type: 'hintItem', itemName: v })
    setHintInput('')
  }

  return (
    <div style={{ marginTop: 40 }}>
      <div className="mono" style={{ fontSize: 10.5, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--ink-3)', marginBottom: 14 }}>Hints</div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        <HintComboBox value={hintInput} onChange={setHintInput} items={itemNames} />
        <button className="btn" onClick={sendHint} disabled={!hintInput.trim()}>Hint</button>
      </div>

      {hints.length === 0
        ? <div className="muted mono" style={{ fontSize: 12 }}>No hints yet. Use !hint in chat or the input above.</div>
        : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--rule)' }}>
                {['Item', 'Location', 'Finder', 'Receiver', 'Found'].map(h => (
                  <th key={h} className="mono" style={{ textAlign: 'left', padding: '4px 10px 8px', fontSize: 10.5, color: 'var(--ink-3)', textTransform: 'uppercase', letterSpacing: '.06em', fontWeight: 500 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {hints.map((h, i) => (
                <tr key={i} style={{ borderBottom: '1px solid color-mix(in oklch, var(--rule) 50%, transparent)' }}>
                  <td style={{ padding: '6px 10px' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                      <img src={imgUrl(h.item)} alt="" style={{ width: 18, height: 18, objectFit: 'contain' }}
                        onError={e => { (e.target as HTMLImageElement).style.display = 'none' }} />
                      {h.item}
                    </span>
                  </td>
                  <td style={{ padding: '6px 10px', color: 'var(--ink-2)' }}>{h.location}</td>
                  <td style={{ padding: '6px 10px', color: 'var(--ink-2)' }}>{h.finder}</td>
                  <td style={{ padding: '6px 10px', color: 'var(--ink-2)' }}>{h.receiver}</td>
                  <td style={{ padding: '6px 10px' }}>
                    <span style={{ color: h.found ? 'var(--ok)' : 'var(--ink-4)' }}>{h.found ? '✓' : '—'}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )
      }
    </div>
  )
}

export function ItemsScreen() {
  const { items, hints, char } = useStore()

  useEffect(() => { initGemTooltips() }, [])

  useEffect(() => {
    const gemNames = items
      .filter(i => GEM_CATS.has(categorizeItem(i)))
      .map(i => i.name)
      .filter((n, idx, arr) => arr.indexOf(n) === idx)
    if (gemNames.length) preloadGems(gemNames)
  }, [items])

  const passiveItems = items.filter(i => i.name === 'Progressive passive point' || i.name.toLowerCase().includes('passive point'))
  const passiveCount = passiveItems.length
  const allocatedPassives = (char?.passives as any)?.hashes?.length ?? 0
  const availablePassives = passiveCount - allocatedPassives

  const classItems = new Set(CLASS_TREE.flatMap(r => [r.base, ...r.asc]))
  const receivedNames = new Set(items.map(i => i.name))
  const hasClassItems = CLASS_TREE.some(r => receivedNames.has(r.base) || r.asc.some(a => receivedNames.has(a)))

  const grouped: Record<string, Record<string, number>> = {}
  for (const cat of CAT_ORDER) grouped[cat] = {}
  for (const item of items) {
    if (classItems.has(item.name)) continue
    const cat = categorizeItem(item)
    if (!grouped[cat]) grouped[cat] = {}
    grouped[cat][item.name] = (grouped[cat][item.name] || 0) + 1
  }

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <div className="page-header">
        <h1>Items</h1>
        <div className="sub">{items.length} received</div>
      </div>
      <style>{`@keyframes passive-flash { from { opacity: 1 } to { opacity: 0.25 } }`}</style>

      <div className="items-page-outer">
      <div className="items-page-content">
        {items.length === 0 && (
          <div style={{ color: 'var(--ink-3)', fontSize: 13, textAlign: 'center', padding: '60px 0' }}>
            No items received yet. Connect to an Archipelago server to start.
          </div>
        )}

        {/* Passive bar */}
        {passiveCount > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 24, padding: '10px 14px', background: 'var(--bg-3)', borderRadius: 6, border: '1px solid var(--rule)' }}>
            <img src={imgUrl('Progressive passive point')} alt=""
              style={{ width: 28, height: 28, objectFit: 'contain', flexShrink: 0 }}
              onError={e => { (e.target as HTMLImageElement).style.display = 'none' }} />
            <span style={{ fontSize: 13, fontWeight: 500 }}>Passive Points</span>
            <span style={{
              fontSize: 13, fontWeight: 600,
              color: availablePassives > 0 ? 'var(--ok)' : availablePassives < 0 ? 'var(--err)' : 'var(--ink-3)',
              animation: availablePassives < 0 ? 'passive-flash 0.8s ease-in-out infinite alternate' : undefined,
            }}>
              {availablePassives > 0 ? '+' : ''}{availablePassives} available
            </span>
            <span className="mono" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', lineHeight: 1.3, marginLeft: 'auto' }}>
              <span style={{ fontSize: 12, color: 'var(--accent)' }}>{allocatedPassives} <span style={{ fontSize: 10, color: 'var(--ink-3)' }}>allocated</span></span>
              <span style={{ fontSize: 10, color: 'var(--ink-4)' }}>────────</span>
              <span style={{ fontSize: 12, color: 'var(--accent)' }}>{passiveCount} <span style={{ fontSize: 10, color: 'var(--ink-3)' }}>unlocked</span></span>
            </span>
          </div>
        )}

        {/* Classes & Ascendancies */}
        {hasClassItems && <ClassSection receivedNames={receivedNames} />}

        {/* Item categories */}
        {CAT_ORDER.map(cat => {
          const entries = Object.entries(grouped[cat] ?? {}).sort((a, b) => a[0].localeCompare(b[0]))
          if (entries.length === 0) return null
          return <CatSection key={cat} cat={cat} entries={entries} />
        })}

        {/* Hints */}
        <HintsSection hints={hints} />

        {/* Paper doll — visible below 1650px, hidden at wide breakpoint where it moves to sidebar */}
        <div className="items-paperdoll-bottom">
          <div className="mono" style={{ fontSize: 10.5, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--ink-3)', marginBottom: 14, marginTop: 40 }}>Equipment</div>
          <PaperDoll items={items} mobile />
        </div>
      </div>

      {/* Paper doll sidebar — only visible at wide breakpoint */}
      <div className="items-paperdoll-sidebar">
        <div className="mono" style={{ fontSize: 10.5, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--ink-3)', marginBottom: 14 }}>Equipment</div>
        <PaperDoll items={items} mobile />
      </div>
      </div>
    </div>
  )
}
