import { useStore } from '../store'
import logoUrl from '@resources/poeAP.png'

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
  { id: 'setup',     label: 'Setup',      icon: '◑' },
]

export function Sidebar({ active, onNavigate }: SidebarProps) {
  const { connection, items, chat, errors, clientTxtOk, filterOk, char } = useStore()

  const badges: Partial<Record<Screen, string | number>> = {}
  if (errors.length > 0)  badges.gear  = errors.length
  if (chat.filter(m => m.kind === 'item').length > 0)
    badges.items = items.length

  const allGood = connection === 'connected' && clientTxtOk && filterOk && !!char

  return (
    <aside className="sidebar">
      <div className="brand">
        <img src={logoUrl} alt="PoE AP" style={{ width: 40, height: 40, marginBottom: 8, display: 'block' }} />
        <div className="mark">Path of <em>Exile</em></div>
        <div className="sub">Archipelago · v0.1</div>
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
              <span className="badge">{badges[id]}</span>
            )}
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
