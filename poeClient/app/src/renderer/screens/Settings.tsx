import React, { useState, useEffect } from 'react'
import { useStore } from '../store'
import type { Settings } from '@shared/types'

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 36 }}>
      <div className="mono" style={{ fontSize: 10.5, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--ink-3)', marginBottom: 14 }}>{title}</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {children}
      </div>
    </div>
  )
}

function Row({ label, note, children }: { label: string; note?: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, alignItems: 'start', paddingBottom: 14, borderBottom: '1px solid var(--rule)' }}>
      <div>
        <div style={{ fontSize: 13, fontWeight: 500 }}>{label}</div>
        {note && <div className="muted" style={{ fontSize: 11.5, marginTop: 3, lineHeight: 1.5 }}>{note}</div>}
      </div>
      <div>{children}</div>
    </div>
  )
}

function Toggle({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className={`toggle ${on ? 'on' : ''}`} onClick={() => onChange(!on)}>
      <div className="knob" />
      <span style={{ fontSize: 12, color: on ? 'var(--ink)' : 'var(--ink-3)' }}>{on ? 'on' : 'off'}</span>
    </div>
  )
}

function PathStatus({ valid }: { valid: boolean | null }) {
  if (valid === null) return null
  return valid
    ? <span style={{ color: 'var(--ok)', fontSize: 16, lineHeight: 1, flexShrink: 0 }}>✓</span>
    : <span style={{ color: 'var(--err)', fontSize: 16, lineHeight: 1, flexShrink: 0 }}>✗</span>
}

function usePathValid(p: string): boolean | null {
  const action = useStore(s => s.action)
  const [valid, setValid] = useState<boolean | null>(null)
  useEffect(() => {
    if (!p) { setValid(null); return }
    const t = setTimeout(() => {
      action({ type: 'checkPath', path: p }).then(r => setValid(r as boolean))
    }, 300)
    return () => clearTimeout(t)
  }, [p])
  return valid
}

export function SettingsScreen() {
  const action = useStore(s => s.action)
  const { oauthStatus, oauthDaysLeft, oauthAccount, connection, serverAddr, deathlink } = useStore()

  const save = (key: keyof Settings) => (value: unknown) => {
    action({ type: 'saveSetting', key, value })
  }

  const [paths, setPaths]           = useState({ clientTxt: '', docPath: '', baseFilter: '' })
  const [whisper, setWhisper]       = useState(true)
  const [bypass,  setBypass]        = useState(false)
  const [filterDisplay, setFilterDisplay] = useState(0)
  const [filterSound,   setFilterSound]   = useState(2)
  const [delayEnter, setDelayEnter] = useState(0)
  const [delayPaste, setDelayPaste] = useState(0)

  // Load persisted paths on mount
  useEffect(() => {
    action({ type: 'getSettings' }).then((s: any) => {
      if (!s) return
      setPaths({
        clientTxt:  s.clientTxtPath   ?? '',
        docPath:    s.poeDocPath      ?? '',
        baseFilter: s.baseItemFilter  ?? '',
      })
      setWhisper(s.whisperUpdates  ?? true)
      setBypass(s.bypassFocusCheck ?? false)
      setFilterDisplay(s.filterDisplay ?? 0)
      setFilterSound(s.filterSound   ?? 2)
      setDelayEnter(s.inputDelayEnter ?? 0)
      setDelayPaste(s.inputDelayPaste ?? 0)
    })
  }, [])

  const clientOk    = usePathValid(paths.clientTxt)
  const docOk       = usePathValid(paths.docPath)
  const baseFilterOk = usePathValid(
    paths.baseFilter && paths.docPath ? `${paths.docPath}\\${paths.baseFilter}.filter` : ''
  )

  async function browse(mode: 'file' | 'folder', title: string, current: string, set: (v: string) => void, saveKey: keyof Settings) {
    const res = await action({ type: 'browsePath', mode, title, defaultPath: current || undefined }) as string | null
    if (res) {
      set(res)
      action({ type: 'saveSetting', key: saveKey, value: res })
    }
  }

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <div className="page-header">
        <h1>Settings</h1>
        <div className="sub">App configuration · persisted per seed/character</div>
      </div>

      <div style={{ padding: '28px 28px', maxWidth: 860 }}>

        <Section title="Paths">
          <Row label="Client.txt" note="PoE log file; tailed for zone changes, deaths, and chat commands.">
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input className="input mono" style={{ flex: 1 }} value={paths.clientTxt}
                onChange={e => setPaths(p => ({ ...p, clientTxt: e.target.value }))}
                onBlur={() => save('clientTxtPath')(paths.clientTxt)}
                placeholder="C:\Games\Path of Exile\logs\Client.txt" />
              <PathStatus valid={clientOk} />
              <button className="btn" onClick={() => browse('file', 'Select Client.txt', paths.clientTxt, v => setPaths(p => ({ ...p, clientTxt: v })), 'clientTxtPath')}>Browse</button>
            </div>
          </Row>
          <Row label="PoE Documents folder" note="Where __ap.filter will be written.">
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input className="input mono" style={{ flex: 1 }} value={paths.docPath}
                onChange={e => setPaths(p => ({ ...p, docPath: e.target.value }))}
                onBlur={() => save('poeDocPath')(paths.docPath)}
                placeholder="C:\Users\you\Documents\My Games\Path of Exile\" />
              <PathStatus valid={docOk} />
              <button className="btn" onClick={() => browse('folder', 'Select PoE documents folder', paths.docPath, v => setPaths(p => ({ ...p, docPath: v })), 'poeDocPath')}>Browse</button>
            </div>
          </Row>
          <Row label="Base item filter" note="Filter name to chain imports from (optional). The AP filter wraps it.">
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input className="input" style={{ flex: 1 }} value={paths.baseFilter}
                onChange={e => setPaths(p => ({ ...p, baseFilter: e.target.value }))}
                onBlur={() => save('baseItemFilter')(paths.baseFilter)}
                placeholder="Neversink" />
              <PathStatus valid={baseFilterOk} />
              <button className="btn" onClick={async () => {
                const startDir = paths.docPath || undefined
                const res = await action({ type: 'browsePath', mode: 'file', title: 'Select base filter', defaultPath: startDir }) as string | null
                if (res) {
                  // Store just the name without extension
                  const name = res.replace(/\.filter$/i, '').split(/[\\/]/).pop() ?? res
                  setPaths(p => ({ ...p, baseFilter: name }))
                  action({ type: 'saveSetting', key: 'baseItemFilter', value: name })
                }
              }}>Browse</button>
            </div>
          </Row>
        </Section>

        <Section title="GGG Account">
          <Row label="OAuth status" note="Read-only access to character data.">
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <span className={`pill ${oauthStatus === 'valid' ? 'ok' : ''}`}>
                <span className="dot" />
                {oauthStatus === 'valid' ? `valid · ${oauthDaysLeft}` : oauthStatus}
              </span>
              {oauthAccount && <span style={{ fontSize: 12, color: 'var(--ink-2)' }}>{oauthAccount}</span>}
            </div>
          </Row>
          <Row label="Re-authenticate" note="Opens the GGG login page in a browser window.">
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn" onClick={() => action({ type: 'oauth:start' })}>Login with GGG</button>
              {oauthStatus === 'valid' && (
                <button className="btn ghost" onClick={() => action({ type: 'oauth:clear' })}>Clear token</button>
              )}
            </div>
          </Row>
        </Section>

        <Section title="Archipelago Connection">
          <Row label="Connection" note="Current server connection status.">
            <span className={`pill ${connection === 'connected' ? 'ok' : ''}`}>
              <span className="dot" />{connection} {serverAddr && `· ${serverAddr}`}
            </span>
          </Row>
          <Row label={connection === 'connected' ? 'Disconnect' : 'Connect'} note={connection === 'connected' ? 'Drop current server connection.' : 'Connect to an Archipelago server from the Dashboard.'}>
            {connection === 'connected'
              ? <button className="btn" onClick={() => action({ type: 'disconnect' })}>Disconnect</button>
              : <span className="muted mono" style={{ fontSize: 12 }}>Use the Dashboard to connect.</span>
            }
          </Row>
        </Section>

        <Section title="Game Input">
          <Row label="Bypass focus check" note="Always send commands even if PoE isn't in the foreground.">
            <Toggle on={bypass} onChange={v => { setBypass(v); save('bypassFocusCheck')(v) }} />
          </Row>
          <Row label="Item whispers" note="Show a whisper in-game when you receive a new item.">
            <Toggle on={whisper} onChange={v => { setWhisper(v); action({ type: 'setWhisperUpdates', enabled: v }) }} />
          </Row>
          <Row label="Enter delay (ms)" note="Wait after pressing Enter to open chat before pasting.">
            <input className="input mono" type="number" min={0} max={2000} style={{ width: 80 }}
              value={delayEnter}
              onChange={e => setDelayEnter(+e.target.value)}
              onBlur={() => save('inputDelayEnter')(delayEnter)} />
          </Row>
          <Row label="Paste delay (ms)" note="Wait after pasting before pressing Enter to send.">
            <input className="input mono" type="number" min={0} max={2000} style={{ width: 80 }}
              value={delayPaste}
              onChange={e => setDelayPaste(+e.target.value)}
              onBlur={() => save('inputDelayPaste')(delayPaste)} />
          </Row>
        </Section>

        <Section title="Item Filter">
          <Row label="Display mode" note="How to display AP items in the loot filter.">
            <div className="seg" style={{ fontSize: 11.5 }}>
              {([['Show',0],['Hide Classification',3],['Randomize',2],['Hide',1]] as [string,number][]).map(([lbl,v]) => (
                <div key={v} className={`opt${filterDisplay===v?' active':''}`} onClick={() => { setFilterDisplay(v); save('filterDisplay')(v) }}>{lbl}</div>
              ))}
            </div>
          </Row>
          <Row label="Sound mode" note="Alert sounds for AP items.">
            <div className="seg" style={{ fontSize: 11.5 }}>
              {([['None',0],['Jingles',2]] as [string,number][]).map(([lbl,v]) => (
                <div key={v} className={`opt${filterSound===v?' active':''}`} onClick={() => { setFilterSound(v); save('filterSound')(v) }}>{lbl}</div>
              ))}
            </div>
          </Row>
          <Row label="Regenerate now" note="Force-write the filter immediately.">
            <button className="btn" onClick={() => action({ type: 'regenerateFilter' })}>Regenerate filter</button>
          </Row>
        </Section>

        <Section title="DeathLink">
          <Row label="DeathLink" note="Send your death to the multiworld, and receive deaths from it.">
            <Toggle on={deathlink} onChange={v => action({ type: 'setDeathlink', enabled: v })} />
          </Row>
        </Section>

        <Section title="Data">
          <Row label="Config directory" note="Open the folder where settings and logs are stored.">
            <button className="btn" onClick={() => action({ type: 'openConfigDir' })}>Open folder</button>
          </Row>
          <Row label="Export logs" note="Zip config and logs to send to the developer.">
            <button className="btn" onClick={() => action({ type: 'exportConfigZip' })}>Export zip</button>
          </Row>
          <Row label="Reset all data" note="Delete all configuration, logs, and stored settings.">
            <button className="btn ghost" style={{ color: 'var(--err)' }}
              onClick={() => {
                if (window.confirm('Delete all configuration and logs? This cannot be undone.')) {
                  action({ type: 'deleteConfigData' })
                }
              }}>
              Delete all data
            </button>
          </Row>
        </Section>

      </div>
    </div>
  )
}
