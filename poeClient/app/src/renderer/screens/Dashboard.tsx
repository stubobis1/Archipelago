import React, { useState, useRef, useEffect } from 'react'
import { useStore } from '../store'
import type { ChatMessage } from '@shared/types'


const SLOT_LABELS: Record<string, string> = {
  BodyArmour: 'Body Armour', Helmet: 'Helmet', Gloves: 'Gloves', Boots: 'Boots',
  Belt: 'Belt', Amulet: 'Amulet', Ring: 'Ring (left)', Ring2: 'Ring (right)',
  Weapon: 'Weapon', Offhand: 'Off-hand', Flask: 'Flask',
  Passives: 'Passive Points', Class: 'Class', GucciHobo: 'Gucci Hobo Mode',
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div style={{ padding: '7px 10px', background: 'var(--bg-3)', borderRadius: 5, border: '1px solid var(--rule)' }}>
      <div className="mono muted" style={{ fontSize: 9.5, textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 2 }}>{label}</div>
      <div style={{ fontFamily: 'var(--display)', fontSize: 16, lineHeight: 1 }}>{value}</div>
      {sub && <div className="mono muted" style={{ fontSize: 9.5, marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="mono" style={{ fontSize: 10.5, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--ink-3)', marginBottom: 6 }}>
      {children}
    </div>
  )
}

function ChatLine({ msg }: { msg: ChatMessage }) {
  return (
    <div className="chat-line">
      <span className="chat-t mono">{msg.t}</span>
      {msg.who && <span className="chat-who" style={{ color: msg.whoColor }}>{msg.who}</span>}
      <span className={`chat-body ${msg.kind}`}>{msg.body}</span>
    </div>
  )
}

function StatusRow({ ok, neutral, warn, label, cta }: { ok: boolean; neutral?: boolean; warn?: boolean; label: string; cta?: React.ReactNode }) {
  const dotColor = ok ? 'var(--ok)' : warn ? '#c8a020' : neutral ? 'var(--ink-4)' : 'var(--err)'
  const glow = ok ? '0 0 6px var(--ok)' : warn ? '0 0 4px #c8a020' : neutral ? 'none' : '0 0 4px var(--err)'
  const textColor = ok ? 'var(--ink-2)' : warn ? 'var(--ink-2)' : neutral ? 'var(--ink-4)' : 'var(--ink-3)'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'space-between', minHeight: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ width: 9, height: 9, borderRadius: '50%', flexShrink: 0, display: 'inline-block',
          background: dotColor, boxShadow: glow }} />
        <span className="mono" style={{ fontSize: 12, color: textColor }}>{label}</span>
      </div>
      {cta && <div>{cta}</div>}
    </div>
  )
}

function StatusCard({ onNavigate }: { onNavigate: (screen: string, section?: string) => void }) {
  const { connection, serverAddr, char, charName, clientTxtPathOk, docPathOk, filterOk, clientTxtOk, oauthStatus, oauthDaysLeft } = useStore()
  const action = useStore(s => s.action)
  const connected = connection === 'connected'

  const handleConnectAP = async () => {
    const s = await action({ type: 'getSettings' }) as any
    if (s?.serverAddress && s?.slotName) {
      action({ type: 'connect', addr: s.serverAddress, slot: s.slotName, password: s.password || '' })
    } else {
      onNavigate('settings', 'ap')
    }
  }

  const charLabel = char
    ? `Character · ${char.name}`
    : charName
    ? `Character · ${charName}`
    : 'Character'
  const apLabel = connected ? `AP Server · ${serverAddr}` : 'Disconnected from AP server'
  const gggLabel = oauthStatus === 'valid' && oauthDaysLeft ? `GGG API · ${oauthDaysLeft}` : 'GGG API'

  return (
    <div>
      <SectionLabel>Status</SectionLabel>
      <div style={{ background: 'var(--bg-3)', border: '1px solid var(--rule)', borderRadius: 6, padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 9 }}>
        <StatusRow
          ok={clientTxtPathOk && docPathOk}
          label="Paths"
          cta={!(clientTxtPathOk && docPathOk)
            ? <button className="btn sm" style={{ fontSize: 10, padding: '2px 8px' }} onClick={() => onNavigate('settings', 'paths')}>Set paths</button>
            : undefined}
        />
        <StatusRow
          ok={filterOk}
          neutral={!filterOk}
          label="Filter"
          cta={!filterOk
            ? <button className="btn sm" style={{ fontSize: 10, padding: '2px 8px' }} onClick={() => onNavigate('settings', 'filter')}>Set filter</button>
            : undefined}
        />
        <StatusRow
          ok={oauthStatus === 'valid'}
          label={gggLabel}
          cta={oauthStatus !== 'valid'
            ? <button className="btn sm" style={{ fontSize: 10, padding: '2px 8px' }} onClick={() => action({ type: 'oauth:start' })}>Connect GGG</button>
            : undefined}
        />
        <StatusRow
          ok={!!char}
          warn={!char && !!charName}
          label={charLabel}
          cta={!char && (!charName || oauthStatus === 'valid')
            ? <button className="btn sm" style={{ fontSize: 10, padding: '2px 8px' }} onClick={() => onNavigate('settings', 'character')}>Set character</button>
            : undefined}
        />
        
        <StatusRow
          ok={connected}
          label={apLabel}
          cta={!connected
            ? <button className="btn sm" style={{ fontSize: 10, padding: '2px 8px' }} onClick={handleConnectAP}>Connect to AP</button>
            : undefined}
        />
        <StatusRow ok={clientTxtOk} label={clientTxtOk ? 'Monitoring' : 'Not monitoring'} />
      </div>
    </div>
  )
}

function MonitoringCard() {
  const { clientTxtOk } = useStore()
  const action = useStore(s => s.action)

  const handleRefresh = () => {
    action({ type: 'revalidate' })
    action({ type: 'regenerateFilter' })
  }

  return (
    <div>
      <SectionLabel>Monitoring</SectionLabel>
      <div style={{ background: 'var(--bg-3)', border: '1px solid var(--rule)', borderRadius: 6, padding: '14px 16px' }}>
        <div style={{ display: 'flex', gap: 6 }}>
          <button
            className="btn sm"
            style={{ flex: 1, ...(!clientTxtOk
              ? { color: '#0d1a0d', background: 'var(--ok)', borderColor: 'var(--ok)', fontWeight: 600 }
              : { color: 'var(--ink-4)', borderColor: 'var(--rule)', opacity: 0.5, cursor: 'default' }) }}
            disabled={clientTxtOk}
            onClick={() => action({ type: 'startMonitoring' })}
          >▶ Start</button>
          <button
            className="btn sm"
            style={{ flex: 1, ...(clientTxtOk
              ? { color: 'var(--err)', borderColor: 'color-mix(in oklch, var(--err) 40%, var(--rule))' }
              : { color: 'var(--ink-4)', borderColor: 'var(--rule)', opacity: 0.5, cursor: 'default' }) }}
            disabled={!clientTxtOk}
            onClick={() => action({ type: 'stopMonitoring' })}
          >■ Stop</button>
          <button
            className="btn sm"
            style={{ flex: 1, ...(!clientTxtOk
              ? { color: 'var(--ink-4)', borderColor: 'var(--rule)', opacity: 0.5, cursor: 'default' }
              : {}) }}
            disabled={!clientTxtOk}
            onClick={handleRefresh}
          >↺ Refresh</button>
        </div>
      </div>
    </div>
  )
}

function ItemsPanel({ onNavigate }: { onNavigate: (screen: string, section?: string) => void }) {
  const { items, char, goal, errors } = useStore()

  const byCategory = (cat: string) => items.filter(i => i.category?.includes(cat)).length
  const gems         = byCategory('Gem')
  const armour       = byCategory('Armour')
  const weapons      = byCategory('Weapon')
  const flasks       = byCategory('Flask')
  const passivePoints = items.filter(i => i.category?.includes('Passive')).length
  const allocatedPassives = (char?.passives as any)?.hashes?.length ?? null

  return (
    <div style={{ padding: '18px 20px 14px 22px', borderRight: '1px solid var(--rule)', overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 16 }}>

      <StatusCard onNavigate={onNavigate} />

      <MonitoringCard />


      {/* Errors */}
      {errors.length > 0 && (
        <div>
          <style>{`@keyframes err-pulse { 0%,100% { background: color-mix(in srgb, var(--err) 8%, var(--bg-3)); border-color: color-mix(in srgb, var(--err) 25%, transparent); } 50% { background: color-mix(in srgb, var(--err) 22%, var(--bg-3)); border-color: color-mix(in srgb, var(--err) 60%, transparent); } }`}</style>
          <SectionLabel>Validation · {errors.length} issue{errors.length !== 1 ? 's' : ''}</SectionLabel>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {errors.map((e, i) => (
              <div key={i} style={{ padding: '8px 12px', borderRadius: 5, border: '1px solid', fontSize: 12, animation: 'err-pulse 1.6s ease-in-out infinite' }}>
                <span style={{ color: 'var(--err)', fontWeight: 600 }}>{SLOT_LABELS[e.slot] ?? e.slot}</span>
                <span className="muted" style={{ marginLeft: 8 }}>{e.msg}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Items received */}
      <div>
        <SectionLabel>Items received · {items.length}</SectionLabel>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 5 }}>
          <StatCard label="Gems"    value={gems} />
          <StatCard label="Armour"  value={armour} />
          <StatCard label="Weapons" value={weapons} />
          <StatCard label="Flasks"  value={flasks} />
          <StatCard label="Passive pts" value={passivePoints} sub="from multiworld" />
          {allocatedPassives !== null && (
            <StatCard label="Allocated" value={allocatedPassives} sub="on passive tree" />
          )}
        </div>
      </div>

      {/* Goal */}
      {goal && (
        <div>
          <SectionLabel>Goal</SectionLabel>
          <div style={{ padding: '10px 14px', background: goal.complete ? 'color-mix(in srgb, var(--ok) 12%, var(--bg-3))' : 'var(--bg-3)', borderRadius: 6, border: `1px solid ${goal.complete ? 'var(--ok)' : 'var(--rule)'}` }}>
            <div style={{ fontSize: 13, fontWeight: 500 }}>
              {goal.complete ? '✓ Complete' : 'In progress'}
            </div>
            {goal.bosses && goal.bosses.length > 0 && (
              <div className="mono muted" style={{ fontSize: 10.5, marginTop: 4 }}>
                {goal.defeated.length} / {goal.bosses.length} bosses defeated
              </div>
            )}
            {goal.actZoneReached !== undefined && (
              <div className="mono muted" style={{ fontSize: 10.5, marginTop: 4 }}>
                Act zone reached: {goal.actZoneReached}
              </div>
            )}
          </div>
        </div>
      )}

      
    </div>
  )
}

function ChatPanel() {
  const { chat } = useStore()
  const action = useStore(s => s.action)
  const [cmdInput, setCmdInput] = useState('')
  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chat])

  function sendCmd(cmd: string) {
    if (!cmd.trim()) return
    action({ type: 'sendCommand', cmd })
    setCmdInput('')
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0, background: 'var(--bg-2)' }}>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 20px', display: 'flex', flexDirection: 'column', gap: 1, fontSize: 12.5 }}>
        {chat.map((m, i) => <ChatLine key={i} msg={m} />)}
        <div ref={chatEndRef} />
      </div>

      <div style={{ padding: '10px 16px 14px', borderTop: '1px solid var(--rule)', background: 'var(--bg-2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'var(--panel-2)', border: '1px solid var(--rule)', borderRadius: 4, padding: '8px 12px' }}>
          <span className="mono" style={{ color: 'var(--accent)', fontSize: 13 }}>›</span>
          <input
            className="chat-input mono"
            placeholder="send to multiworld (e.g. /help)"
            value={cmdInput}
            onChange={e => setCmdInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') sendCmd(cmdInput) }}
          />
          <span className="mono muted" style={{ fontSize: 10 }}>enter</span>
        </div>
      </div>
    </div>
  )
}

export function Dashboard({ onNavigate }: { onNavigate: (screen: string, section?: string) => void }) {
  return (
    <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 1fr', minHeight: 0 }}>
      <ItemsPanel onNavigate={onNavigate} />
      <ChatPanel />
    </div>
  )
}

export function DashboardPage({ onNavigate }: { onNavigate: (screen: string, section?: string) => void }) {
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <Dashboard onNavigate={onNavigate} />
    </div>
  )
}
