import React, { useState, useRef, useEffect } from 'react'
import { useStore } from '../store'
import type { ChatMessage } from '@shared/types'

type Filter = 'all' | 'items' | 'hints' | 'chat'

export function ChatScreen() {
  const { chat } = useStore()
  const action   = useStore(s => s.action)
  const [filter, setFilter] = useState<Filter>('all')
  const [search, setSearch] = useState('')
  const [input,  setInput]  = useState('')
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chat])

  function send() {
    if (!input.trim()) return
    action({ type: 'sendCommand', cmd: input.trim() })
    setInput('')
  }

  const visible = chat.filter(m => {
    if (filter === 'items' && m.kind !== 'item') return false
    if (filter === 'hints' && m.kind !== 'hint') return false
    if (filter === 'chat'  && !['chat', 'chat-self'].includes(m.kind)) return false
    if (search && !m.body.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <div className="page-header" style={{ paddingBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <h1 style={{ margin: 0 }}>Chat</h1>
          <div className="seg" style={{ fontSize: 10.5 }}>
            {(['all','items','hints','chat'] as Filter[]).map(f => (
              <div key={f} className={`opt ${filter === f ? 'active' : ''}`} onClick={() => setFilter(f)}>
                {f}
              </div>
            ))}
          </div>
          <input className="input" placeholder="search…" value={search} onChange={e => setSearch(e.target.value)}
            style={{ maxWidth: 200, fontSize: 11.5, padding: '4px 8px' }} />
          <span className="muted mono" style={{ fontSize: 10.5, marginLeft: 'auto' }}>{visible.length} lines</span>
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '12px 28px', display: 'flex', flexDirection: 'column', gap: 1, fontSize: 12.5 }}>
        {visible.map((m, i) => (
          <div key={i} className="chat-line">
            <span className="chat-t mono">{m.t}</span>
            {m.who && <span className="chat-who" style={{ color: m.whoColor }}>{m.who}</span>}
            <span className={`chat-body ${m.kind}`}>{m.body}</span>
          </div>
        ))}
        <div ref={endRef} />
        {visible.length === 0 && (
          <div style={{ color: 'var(--ink-4)', textAlign: 'center', padding: '40px 0', fontFamily: 'var(--mono)', fontSize: 11 }}>
            {chat.length === 0 ? 'No messages yet.' : 'No messages match filter.'}
          </div>
        )}
      </div>

      <div style={{ padding: '10px 16px 14px', borderTop: '1px solid var(--rule)', background: 'var(--bg-2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'var(--panel-2)', border: '1px solid var(--rule)', borderRadius: 4, padding: '8px 12px' }}>
          <span className="mono" style={{ color: 'var(--accent)', fontSize: 13 }}>›</span>
          <input className="chat-input mono" placeholder="send to multiworld (e.g. !goal)" value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') send() }} />
          <span className="mono muted" style={{ fontSize: 10 }}>enter</span>
        </div>
      </div>
    </div>
  )
}
