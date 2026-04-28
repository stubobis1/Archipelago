import React, { useState } from 'react'
import { useStore } from '../store'
import type { APLocation } from '@shared/types'

function actLabel(act: number | string): string {
  if (act === 'level') return 'Level Milestones'
  if (act === '0_boss') return 'Endgame Bosses'
  if (typeof act === 'string' && act.endsWith('_boss')) return `Act ${act.replace('_boss', '')} Bosses`
  if (act === 0 || act === 0.2) return 'Twilight Strand'
  if (act >= 1 && act <= 10) return `Act ${act}`
  if (act === 11) return 'Maps / Endgame'
  return 'Other'
}

function actSortKey(act: number | string): number {
  if (act === 0 || act === 0.2) return -1
  if (act === 'level') return 99
  if (act === '0_boss') return 12
  if (typeof act === 'string' && act.endsWith('_boss')) return parseFloat(act) + 0.5
  return Number(act)
}

function locDisplayName(name: string): string {
  return name.replace(/\s*-\s*(early\s+)?act\s+\d+$/i, '')
}

function ActSection({ label, locs }: { label: string; locs: APLocation[] }) {
  const [collapsed, setCollapsed] = useState(true)
  const total   = locs.length
  const doneN   = locs.filter(l => l.checked).length
  const pct     = total > 0 && doneN > 0 ? Math.round(doneN / total * 100) : 0
  const complete = doneN === total && total > 0

  const sorted = [...locs].sort((a, b) =>
    locDisplayName(a.name).localeCompare(locDisplayName(b.name), undefined, { numeric: true })
  )

  return (
    <div className="act-section">
      <div className={`act-header ${collapsed ? 'collapsed' : ''}`} onClick={() => setCollapsed(v => !v)}>
        <span className="act-toggle">{collapsed ? '▸' : '▾'}</span>
        <h3>{label}</h3>
        <div className="act-bar-wrap">
          <div className={`act-bar${complete ? ' complete' : ''}`} style={{ width: `${pct}%` }} />
        </div>
        <span className="act-progress">{doneN} / {total}</span>
      </div>
      {!collapsed && (
        <div className="act-locations">
          {sorted.map(l => (
            <span key={l.id} className={`loc-tag ${l.checked ? 'checked' : 'unchecked'}`}>
              {locDisplayName(l.name)}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export function LocationsScreen() {
  const { locations, connection } = useStore()

  const byAct: Record<string, APLocation[]> = {}
  for (const loc of locations) {
    const key = String(loc.act)
    if (!byAct[key]) byAct[key] = []
    byAct[key].push(loc)
  }

  const acts = Object.keys(byAct).sort((a, b) => actSortKey(a) - actSortKey(b))
  const total   = locations.length
  const checked = locations.filter(l => l.checked).length

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <div className="page-header">
        <h1>Locations</h1>
        <div className="sub">{connection === 'connected' ? `${checked} / ${total} checked` : 'not connected'}</div>
      </div>
      <div style={{ padding: '24px 28px', maxWidth: 900 }}>
        {locations.length === 0 && (
          <div style={{ color: 'var(--ink-3)', fontSize: 13, textAlign: 'center', padding: '60px 0' }}>
            {connection === 'connected'
              ? 'Loading locations…'
              : 'Connect to an Archipelago server to view location progress.'}
          </div>
        )}
        {acts.map(act => (
          <ActSection key={act} label={actLabel(act)} locs={byAct[act]} />
        ))}
      </div>
    </div>
  )
}
