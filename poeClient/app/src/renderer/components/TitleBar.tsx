import React from 'react'
import { useStore } from '../store'

export function TitleBar() {
  const { connection, char, slotName, clientTxtOk, filterOk, action } = useStore()

  const allGood = connection === 'connected' && clientTxtOk && filterOk && !!char
  const someGood = connection === 'connected' && !allGood

  const dotClass =
    allGood                     ? ''     :
    someGood                    ? 'warn' :
    connection === 'connecting' ? 'warn' : 'off'

  const charLabel = char
    ? `${char.name} · ${char.class} ${char.level}`
    : slotName || null

  return (
    <div className="titlebar">
      <div className={`status-dot ${dotClass}`} />
      <span className="title">PoE Archipelago</span>
      {charLabel && <span className="muted mono" style={{ fontSize: 10 }}>{charLabel}</span>}
      <span className="spacer" />
      <span className="mono muted" style={{ fontSize: 10 }}>
        {connection === 'connected'  ? 'connected'  :
         connection === 'connecting' ? 'connecting…' : 'offline'}
      </span>
      <div className="wincontrols">
        <div className="wc" title="minimize" onClick={() => action({ type: 'window:minimize' })} />
        <div className="wc" title="close" onClick={() => action({ type: 'window:close' })} style={{ background: 'var(--err)' }} />
      </div>
    </div>
  )
}
