import React from 'react'
import { useStore } from '../store'
import logoUrl from '@resources/poeAP.png'

const { clientVersion, backwardsCompatibleVersions } = window.electronAPI.poeVersion

export function TitleBar() {
  const { connection, char, slotName, clientTxtOk, filterOk, oauthStatus, action } = useStore()

  const gggOk = oauthStatus === 'valid'
  const allGood = connection === 'connected' && clientTxtOk && filterOk && !!char && gggOk
  const someGood = connection === 'connected' && !allGood

  const dotClass =
    !gggOk                      ? 'off'  :
    allGood                     ? ''     :
    someGood                    ? 'warn' :
    connection === 'connecting' ? 'warn' : 'off'

  const charLabel = char
    ? `${char.name} · ${char.class} ${char.level}`
    : slotName || null

  return (
    <div className="titlebar">
      <img src={logoUrl} className="titlebar-logo" alt="" />
      <span className="title">Archi<em>PoE</em>lago</span>
      <span
        className="mono muted"
        style={{ fontSize: 10, cursor: 'default' }}
        title={`Compatible: ${backwardsCompatibleVersions.join(', ')}`}
      >
        v{clientVersion}
      </span>
      <div className={`status-dot ${dotClass}`} />
      {charLabel && <span className="muted mono" style={{ fontSize: 10 }}>{charLabel}</span>}
      <span className="spacer" />
      <span className="mono muted" style={{ fontSize: 10 }}>
        {!gggOk                          ? 'no GGG connection' :
         connection === 'connected'      ? 'connected'         :
         connection === 'connecting'     ? 'connecting…'       : 'offline'}
      </span>
      <div className="wincontrols">
        <div className="wc" title="minimize" onClick={() => action({ type: 'window:minimize' })} />
        <div className="wc" title="close" onClick={() => action({ type: 'window:close' })} style={{ background: 'var(--err)' }} />
      </div>
    </div>
  )
}
