import React, { useState, useRef, useEffect } from 'react'
import { useStore } from '../store'
import type { ChatMessage } from '@shared/types'


function StatusStrip() {
  const { connection, serverAddr, slotName, char, zone, goal } = useStore()
  const action = useStore(s => s.action)
  const [addr, setAddr] = useState(serverAddr || '')
  const [slot, setSlot] = useState(slotName || '')
  const [pass, setPass] = useState('')

  const connected   = connection === 'connected'
  const connecting  = connection === 'connecting'

  return (
    <div style={{ background: 'var(--bg-2)', borderBottom: '1px solid var(--rule)' }}>
      {/* top row — always visible */}
      <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr auto', gap: 18, alignItems: 'center', padding: '10px 22px' }}>
        {connected
          ? <span className="pill ok"><span className="dot" />connected · {serverAddr}</span>
          : connecting
          ? <span className="pill warn"><span className="dot" />connecting…</span>
          : <span className="pill"><span className="dot" style={{ background: 'var(--ink-4)' }} />offline</span>
        }
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
          {char
            ? <>
                <span style={{ fontFamily: 'var(--display)', fontSize: 20, lineHeight: 1 }}>{char.name}</span>
                <span className="mono muted" style={{ fontSize: 11 }}>{char.class} · lv {char.level}{zone ? ` · ${zone}` : ''}</span>
              </>
            : <span className="muted mono" style={{ fontSize: 11 }}>no character loaded</span>
          }
        </div>
        {goal && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
            <span className="mono" style={{ fontSize: 10.5, color: 'var(--ink-3)', textTransform: 'uppercase' }}>Goal</span>
            <span style={{ fontFamily: 'var(--display)', fontSize: 14, marginTop: 1 }}>
              {goal.complete ? '✓ Complete' : `in progress · ${goal.defeated.length} done`}
            </span>
          </div>
        )}
      </div>

      {/* connect bar — shown when not connected */}
      {!connected && (
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', padding: '0 22px 10px', flexWrap: 'wrap' }}>
          <input
            className="input mono" style={{ flex: '2 1 160px', fontSize: 12 }}
            placeholder="server:port"
            value={addr} onChange={e => setAddr(e.target.value)}
          />
          <input
            className="input" style={{ flex: '1 1 120px', fontSize: 12 }}
            placeholder="slot name"
            value={slot} onChange={e => setSlot(e.target.value)}
          />
          <input
            className="input" style={{ flex: '1 1 100px', fontSize: 12 }}
            placeholder="password"
            type="password"
            value={pass} onChange={e => setPass(e.target.value)}
          />
          <button
            className="btn primary" style={{ flexShrink: 0 }}
            disabled={!addr || !slot || connecting}
            onClick={() => action({ type: 'connect', addr, slot, password: pass })}
          >
            {connecting ? 'Connecting…' : 'Connect'}
          </button>
        </div>
      )}

      {/* disconnect button — shown when connected */}
      {connected && (
        <div style={{ padding: '0 22px 10px' }}>
          <button className="btn ghost" style={{ fontSize: 11 }}
            onClick={() => action({ type: 'disconnect' })}>
            Disconnect
          </button>
        </div>
      )}
    </div>
  )
}


function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div style={{ padding: '10px 14px', background: 'var(--bg-3)', borderRadius: 6, border: '1px solid var(--rule)' }}>
      <div className="mono muted" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 4 }}>{label}</div>
      <div style={{ fontFamily: 'var(--display)', fontSize: 22, lineHeight: 1 }}>{value}</div>
      {sub && <div className="mono muted" style={{ fontSize: 10.5, marginTop: 3 }}>{sub}</div>}
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

function StatusDot({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <span style={{ width: 10, height: 10, borderRadius: '50%', flexShrink: 0, display: 'inline-block',
        background: ok ? 'var(--ok)' : 'var(--err)',
        boxShadow: ok ? '0 0 6px var(--ok)' : '0 0 4px var(--err)' }} />
      <span className="mono" style={{ fontSize: 13, color: ok ? 'var(--ink-2)' : 'var(--ink-3)' }}>{label}</span>
    </div>
  )
}

function ItemsPanel() {
  const { items, char, goal, errors, clientTxtOk, clientTxtPathOk, filterOk, connection } = useStore()
  const action = useStore(s => s.action)

  const byCategory = (cat: string) => items.filter(i => i.category?.includes(cat)).length
  const gems         = byCategory('Gem')
  const armour       = byCategory('Armour')
  const weapons      = byCategory('Weapon')
  const flasks       = byCategory('Flask')
  const passivePoints = items.filter(i => i.category?.includes('Passive')).length
  const allocatedPassives = (char?.passives as any)?.hashes?.length ?? null

  return (
    <div style={{ padding: '18px 20px 14px 22px', borderRight: '1px solid var(--rule)', overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 18 }}>
      <h2 style={{ fontFamily: 'var(--display)', fontWeight: 400, fontSize: 22, lineHeight: 1, letterSpacing: '-.005em', margin: 0 }}>Status</h2>

      {/* Monitoring */}
      <div>
        <SectionLabel>Monitoring</SectionLabel>
        <div style={{ background: 'var(--bg-3)', border: '1px solid var(--rule)', borderRadius: 6, padding: '16px 18px', display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <StatusDot ok={clientTxtPathOk}          label="Client.txt" />
            <StatusDot ok={filterOk}               label="Filter" />
            <StatusDot ok={connection === 'connected'} label="AP server" />
            <StatusDot ok={!!char}                 label="Character" />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 0 4px', borderTop: '1px solid var(--rule)' }}>
            <span style={{ width: 12, height: 12, borderRadius: '50%', flexShrink: 0, display: 'inline-block',
              background: clientTxtOk ? 'var(--ok)' : 'var(--ink-4)',
              boxShadow: clientTxtOk ? '0 0 8px var(--ok)' : 'none' }} />
            <span style={{ fontSize: 15, fontWeight: 600, color: clientTxtOk ? 'var(--ok)' : 'var(--ink-3)', fontFamily: 'var(--mono)' }}>
              {clientTxtOk ? 'Monitoring' : 'Not monitoring'}
            </span>
          </div>
          <div style={{ display: 'flex', gap: 6 }}>
            <button className="btn sm" style={{ flex: 1 }} onClick={() => action({ type: 'revalidate' })}>↺ revalidate gear</button>
            <button className="btn sm" style={{ flex: 1 }} onClick={() => action({ type: 'regenerateFilter' })}>↺ filter</button>
            <button className="btn sm" style={{ flex: 1, ...(clientTxtOk ? { color: 'var(--ink-4)', borderColor: 'var(--rule)', opacity: 0.5, cursor: 'default' } : { color: '#0d1a0d', background: 'var(--ok)', borderColor: 'var(--ok)', fontWeight: 600 }) }} disabled={clientTxtOk} onClick={() => action({ type: 'startMonitoring' })}>▶ Start</button>
            <button className="btn sm" style={{ flex: 1, ...(!clientTxtOk ? { color: 'var(--ink-4)', borderColor: 'var(--rule)', opacity: 0.5, cursor: 'default' } : { color: 'var(--err)', borderColor: 'color-mix(in oklch, var(--err) 40%, var(--rule))' }) }} disabled={!clientTxtOk} onClick={() => action({ type: 'stopMonitoring' })}>■ Stop</button>
          </div>
        </div>
      </div>

      {/* Items received */}
      <div>
        <SectionLabel>Items received · {items.length} total</SectionLabel>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
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

      {/* Errors */}
      {errors.length > 0 && (
        <div>
          <SectionLabel>Validation · {errors.length} issue{errors.length !== 1 ? 's' : ''}</SectionLabel>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {errors.map((e, i) => (
              <div key={i} style={{ padding: '8px 12px', background: 'color-mix(in srgb, var(--err) 10%, var(--bg-3))', borderRadius: 5, border: '1px solid color-mix(in srgb, var(--err) 30%, transparent)', fontSize: 12 }}>
                <span style={{ color: 'var(--err)', fontWeight: 600 }}>{e.slot}</span>
                <span className="muted" style={{ marginLeft: 8 }}>{e.msg}</span>
              </div>
            ))}
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
      <div style={{ padding: '14px 20px 10px', borderBottom: '1px solid var(--rule)' }}>
        <h2 style={{ fontFamily: 'var(--display)', fontWeight: 400, fontSize: 22, lineHeight: 1, letterSpacing: '-.005em', margin: 0 }}>Multiworld chat</h2>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '12px 20px', display: 'flex', flexDirection: 'column', gap: 1, fontSize: 12.5 }}>
        {chat.map((m, i) => <ChatLine key={i} msg={m} />)}
        <div ref={chatEndRef} />
      </div>

      <div style={{ padding: '10px 16px 14px', borderTop: '1px solid var(--rule)', background: 'var(--bg-2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'var(--panel-2)', border: '1px solid var(--rule)', borderRadius: 4, padding: '8px 12px' }}>
          <span className="mono" style={{ color: 'var(--accent)', fontSize: 13 }}>›</span>
          <input
            className="chat-input mono"
            placeholder="send to multiworld (e.g. !help)"
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

export function Dashboard() {
  return (
    <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 1fr', minHeight: 0 }}>
      <ItemsPanel />
      <ChatPanel />
    </div>
  )
}

export function DashboardPage() {
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <StatusStrip />
      <Dashboard />
    </div>
  )
}
