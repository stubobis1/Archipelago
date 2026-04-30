import { useStore } from '../store'
import logoUrl from '@resources/poeAP.png'

const { clientVersion, backwardsCompatibleVersions } = window.electronAPI.poeVersion

type Screen = 'dashboard' | 'gear' | 'items' | 'locations' | 'goal' | 'settings' | 'setup'

interface SidebarProps {
  active:    Screen
  onNavigate: (s: Screen) => void
}

const NAV: { id: Screen; label: string; icon: string }[] = [
  { id: 'dashboard', label: 'Dashboard',  icon: '⊞' },
  { id: 'gear',      label: 'Gear',       icon: '⚔' },
  { id: 'items',     label: 'Items',      icon: '◈' },
  { id: 'locations', label: 'Locations',  icon: '◉' },
  { id: 'goal',      label: 'Goal',       icon: '◎' },
  { id: 'settings',  label: 'Settings',   icon: '⚙' },
]

const NAV_BOTTOM: { id: Screen; label: string; icon: string }[] = [
  { id: 'setup', label: 'First-time Setup', icon: '◑' },
]

export function Sidebar({ active, onNavigate }: SidebarProps) {
  const { connection, items, errors, clientTxtOk, filterOk, char, locations, goal, totalGearUnlocks } = useStore()

  const locsChecked  = locations.filter(l => l.checked).length
  const locsTotal    = locations.length
  const itemsPossible = locsTotal

  const gearItems = items.filter(i => {
    const cats = i.category ?? []
    return cats.includes('Weapon') || cats.includes('Armour') || cats.includes('Fishing Rod')
      || /^(Progressive|Normal|Magic|Rare|Unique) /.test(i.name)
  }).length

  const badges: Partial<Record<Screen, string | number>> = {}
  const badgeOk: Partial<Record<Screen, boolean>> = {}

  // Gear: gear items received / total possible gear unlocks from slot data
  if (gearItems > 0 || totalGearUnlocks > 0 || errors.length > 0) {
    const gearTotal = totalGearUnlocks > 0 ? totalGearUnlocks : undefined
    badges.gear  = gearTotal !== undefined ? `${gearItems}/${gearTotal}` : String(gearItems)
    badgeOk.gear = errors.length === 0 && gearTotal !== undefined && gearItems >= gearTotal
  }

  // Items: received / total in pool (pool size = location count)
  if (items.length > 0 || itemsPossible > 0) {
    badges.items  = itemsPossible > 0 ? `${items.length}/${itemsPossible}` : String(items.length)
    badgeOk.items = itemsPossible > 0 && items.length >= itemsPossible
  }

  // Locations: checked / total
  if (locsTotal > 0) {
    badges.locations  = `${locsChecked}/${locsTotal}`
    badgeOk.locations = locsChecked === locsTotal
  }

  // Goal: boss progress or zone completion
  if (goal) {
    if (goal.type === 10) {
      const bosses = goal.bosses?.length ?? 0
      badges.goal  = `${goal.defeated.length}/${bosses}`
    } else {
      badges.goal  = goal.complete ? '1/1' : '0/1'
    }
    badgeOk.goal = goal.complete
  }

  const allGood = connection === 'connected' && clientTxtOk && filterOk && !!char

  return (
    <aside className="sidebar">
      <div className="brand">
        <img src={logoUrl} alt="PoE AP" style={{ width: 50, height: 50, marginBottom: 8, display: 'block', margin: '0 auto 8px' }} />
        <div className="mark" style={{ textAlign: 'center' }}>Archi<em>PoE</em>lago</div>
        <div className="sub" style={{ textTransform: 'none', fontSize: 9 }}>Randomizer for Path of Exile.</div>
        <div className="sub" title={`Compatible: ${backwardsCompatibleVersions.join(', ')}`}>v{clientVersion}</div>
      </div>

      <nav className="nav">
        {NAV.map(({ id, label, icon }) => (
          <div
            key={id}
            className={`item ${active === id ? 'active' : ''}`}
            onClick={() => onNavigate(id)}
          >
            <span className="ico" style={{ fontSize: 13, fontFamily: 'var(--mono)' }}>{icon}</span>
            <span>{label}</span>
            {badges[id] !== undefined && (
              <span className={`badge${badgeOk[id] ? ' ok' : ''}`}>{badges[id]}</span>
            )}
          </div>
        ))}
        <div style={{ flex: 1 }} />
        {NAV_BOTTOM.map(({ id, label, icon }) => (
          <div
            key={id}
            className={`item ${active === id ? 'active' : ''}`}
            onClick={() => onNavigate(id)}
          >
            <span className="ico" style={{ fontSize: 13, fontFamily: 'var(--mono)' }}>{icon}</span>
            <span>{label}</span>
          </div>
        ))}
      </nav>

      <div className="footer">
        {connection === 'connected'
          ? (() => {
              const missing = [
                !clientTxtOk && 'monitor',
                !filterOk    && 'filter',
                !char        && 'char',
              ].filter(Boolean) as string[]
              return (
                <span className={`pill ${allGood ? 'ok' : 'warn'}`} style={{ marginBottom: 4 }}>
                  <span className="dot" />
                  {allGood ? 'live' : `no ${missing.join(', ')}`}
                </span>
              )
            })()
          : <span className="muted">not connected</span>
        }
      </div>
    </aside>
  )
}
