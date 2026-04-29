import { useState, useEffect } from 'react'
import { useStore } from '../store'
import type { Settings } from '@shared/types'
import { PathInput, FilterPathInput } from '../components/PathInput'

const STEPS = [
  { n: 1, label: 'Paths'     },
  { n: 2, label: 'GGG OAuth' },
  { n: 3, label: 'Connect'   },
  { n: 4, label: 'Character' },
  { n: 5, label: 'Ready'     },
]

function Step1Paths({ onNext }: { onNext: () => void }) {
  const action = useStore(s => s.action)
  const [clientTxt, setClientTxt] = useState('')
  const [docPath, setDocPath]     = useState('')
  const [filter, setFilter]       = useState('')

  useEffect(() => {
    action({ type: 'getDefaultPaths' }).then((res: any) => {
      if (res?.clientTxt)       setClientTxt(res.clientTxt)
      if (res?.docPath)         setDocPath(res.docPath)
      if (res?.baseItemFilter)  setFilter(res.baseItemFilter)
    })
  }, [])

  function savePath(key: keyof Settings, value: string) {
    if (value) action({ type: 'saveSetting', key, value })
  }

  function saveAll() {
    savePath('clientTxtPath', clientTxt)
    savePath('poeDocPath', docPath)
    savePath('baseItemFilter', filter)
    onNext()
  }

  return (
    <div style={{ maxWidth: 640, display: 'grid', gap: 20 }}>
      <PathInput
        label="Client.txt path"
        value={clientTxt} onChange={setClientTxt}
        onBlur={v => savePath('clientTxtPath', v)}
        placeholder="C:\Games\Path of Exile\logs\Client.txt"
        mode="file" browseTitle="Select Client.txt"
        browseDefaultPath={clientTxt || undefined}
      />
      <PathInput
        label="PoE documents folder"
        value={docPath} onChange={setDocPath}
        onBlur={v => savePath('poeDocPath', v)}
        placeholder="C:\Users\you\Documents\My Games\Path of Exile\"
        mode="folder" browseTitle="Select PoE documents folder"
        browseDefaultPath={docPath || undefined}
      />
      <FilterPathInput
        label={<>Base item filter <span className="muted mono" style={{ fontSize: 10, textTransform: 'none' }}>optional</span></>}
        value={filter} docPath={docPath}
        onChange={setFilter}
        onBlur={v => savePath('baseItemFilter', v)}
        note="Path to an existing filter file. The AP filter will chain-import it."
      />
      <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
        <div className="spacer" />
        <button className="btn primary" onClick={saveAll}>Next →</button>
      </div>
    </div>
  )
}

function Step2OAuth({ onNext }: { onNext: () => void }) {
  const { oauthStatus, oauthDaysLeft, oauthAccount } = useStore()
  const action = useStore(s => s.action)

  return (
    <div style={{ maxWidth: 640, display: 'grid', gap: 20 }}>
      <p style={{ color: 'var(--ink-2)', fontSize: 14, maxWidth: 560, lineHeight: 1.55, margin: 0 }}>
        Read-only access to your PoE account — used to check your character's equipment, gems, and passive points. No trading or account changes.
      </p>

      {oauthStatus === 'valid' ? (
        <div className="card" style={{ padding: '18px 20px', display: 'grid', gap: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span className="pill ok"><span className="dot" />authenticated</span>
            {oauthDaysLeft && <span className="mono muted" style={{ fontSize: 11 }}>expires in {oauthDaysLeft}</span>}
          </div>

          {oauthAccount && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span className="mono muted" style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '.08em' }}>Account</span>
              <span style={{ fontSize: 13, color: 'var(--ink)' }}>{oauthAccount}</span>
            </div>
          )}

          <div style={{ borderTop: '1px solid var(--rule)', paddingTop: 12, display: 'grid', gap: 6 }}>
            <div className="mono muted" style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 2 }}>Granted scopes</div>
            {['account:profile', 'account:characters', 'account:stashes', 'account:leagues'].map(s => (
              <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ color: 'var(--ok)', fontSize: 12 }}>✓</span>
                <span className="mono" style={{ fontSize: 11.5, color: 'var(--ink-2)' }}>{s}</span>
              </div>
            ))}
          </div>

          <div style={{ borderTop: '1px solid var(--rule)', paddingTop: 12 }}>
            <button className="btn ghost" style={{ fontSize: 11 }}
              onClick={() => action({ type: 'oauth:clear' })}>
              Clear token
            </button>
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: '18px 20px', display: 'grid', gap: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span className="pill"><span className="dot" style={{ background: 'var(--ink-4)' }} />not connected</span>
          </div>
          <p style={{ margin: 0, fontSize: 12.5, color: 'var(--ink-3)', lineHeight: 1.5 }}>
            Opens a GGG login page in your browser. After approving, you'll be redirected back automatically.
          </p>
          <button className="btn primary" style={{ alignSelf: 'flex-start' }}
            onClick={() => action({ type: 'oauth:start' })}>
            Login with GGG
          </button>
        </div>
      )}

      <div style={{ display: 'flex', gap: 10 }}>
        <button className="btn ghost" onClick={onNext}>skip</button>
        <div className="spacer" />
        <button className="btn primary" onClick={onNext} disabled={oauthStatus !== 'valid'}>Next →</button>
      </div>
    </div>
  )
}

function Step3Connect({ onNext }: { onNext: () => void }) {
  const { connection, serverAddr, slotName } = useStore()
  const action = useStore(s => s.action)
  const [addr, setAddr]   = useState(serverAddr || '')
  const [slot, setSlot]   = useState(slotName || '')
  const [pass, setPass]   = useState('')

  function connect() {
    action({ type: 'connect', addr, slot, password: pass })
  }

  return (
    <div style={{ maxWidth: 640, display: 'grid', gap: 20 }}>
      <p style={{ color: 'var(--ink-2)', fontSize: 14, maxWidth: 560, lineHeight: 1.55, margin: 0 }}>
        Paste the server address from your host. Your slot name is what you entered in your YAML.
      </p>
      <div>
        <label className="label">Server address</label>
        <input className="input mono" value={addr} onChange={e => setAddr(e.target.value)} placeholder="archipelago.gg:38281" />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div>
          <label className="label">Slot name</label>
          <input className="input" value={slot} onChange={e => setSlot(e.target.value)} />
        </div>
        <div>
          <label className="label">Password <span className="muted mono" style={{ fontSize: 10, textTransform: 'none' }}>optional</span></label>
          <input className="input" type="password" value={pass} onChange={e => setPass(e.target.value)} />
        </div>
      </div>

      <div style={{ background: 'var(--panel)', border: '1px solid var(--rule)', borderRadius: 5, padding: '14px 18px', display: 'flex', alignItems: 'center', gap: 12 }}>
        {connection === 'connected'
          ? <span className="pill ok"><span className="dot" />connected</span>
          : connection === 'connecting'
          ? <span className="pill warn"><span className="dot" />connecting…</span>
          : <span className="pill"><span className="dot" style={{ background: 'var(--ink-4)' }} />not connected</span>
        }
      </div>

      <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
        <div className="spacer" />
        <button className={`btn${addr && slot && connection !== 'connected' ? ' primary' : ''}`} onClick={connect}>Connect</button>
        <button className="btn ghost" onClick={onNext}>skip</button>
        <button className={`btn${connection === 'connected' ? ' primary' : ''}`} onClick={onNext} disabled={connection !== 'connected'}>Next →</button>
      </div>
    </div>
  )
}

type CharEntry = { name: string; class: string; level: number; league: string }

const CLASS_TREE: { base: string; ascendancies: string[] }[] = [
  { base: 'Marauder', ascendancies: ['Berserker', 'Chieftain', 'Juggernaut'] },
  { base: 'Duelist',  ascendancies: ['Champion', 'Gladiator', 'Slayer'] },
  { base: 'Ranger',   ascendancies: ['Deadeye', 'Pathfinder', 'Warden'] },
  { base: 'Shadow',   ascendancies: ['Assassin', 'Saboteur', 'Trickster'] },
  { base: 'Witch',    ascendancies: ['Elementalist', 'Necromancer', 'Occultist'] },
  { base: 'Templar',  ascendancies: ['Guardian', 'Hierophant', 'Inquisitor'] },
  { base: 'Scion',    ascendancies: ['Ascendant', 'Reliquarian'] },
]

function UnlockDot({ unlocked }: { unlocked: boolean }) {
  return (
    <span style={{
      display: 'inline-block', width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
      background: unlocked ? 'var(--ok)' : 'var(--rule-2)',
      boxShadow: unlocked ? '0 0 5px var(--ok)' : 'none',
    }} />
  )
}

function Step4Character({ onNext }: { onNext: () => void }) {
  const { char, oauthStatus, items } = useStore()
  const action = useStore(s => s.action)
  const [name, setName]       = useState(char?.name || '')
  const [chars, setChars]     = useState<CharEntry[]>([])
  const [loading, setLoading] = useState(oauthStatus === 'valid')
  const [fetchErr, setFetchErr] = useState<string | null>(null)

  const unlockedNames = new Set(items.map(i => i.name))

  function fetchChars() {
    setLoading(true)
    setFetchErr(null)
    action({ type: 'getCharacterList' }).then((res: any) => {
      if (Array.isArray(res)) {
        setChars(res)
      } else if (res && typeof res === 'object' && res.error) {
        setFetchErr(String(res.error))
      } else {
        setChars([])
      }
    }).catch((e: any) => setFetchErr(e?.message ?? 'Unknown error')).finally(() => setLoading(false))
  }

  useEffect(() => {
    if (oauthStatus !== 'valid') return
    fetchChars()
  }, [oauthStatus])

  function pick(charName: string) {
    setName(charName)
    action({ type: 'handshakeChar', charName })
  }

  function handshake() {
    if (name) action({ type: 'handshakeChar', charName: name })
  }

  return (
    <div style={{ maxWidth: 680, display: 'grid', gap: 20 }}>
      <p style={{ color: 'var(--ink-2)', fontSize: 14, maxWidth: 560, lineHeight: 1.55, margin: 0 }}>
        Enter your PoE character name so the client can pull your equipment and gems from the GGG API.
      </p>

      <div>
        <label className="label">AP unlocks</label>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 6 }}>
          {CLASS_TREE.map(({ base, ascendancies }) => (
            <div key={base} style={{ background: 'var(--panel)', border: '1px solid var(--rule)', borderRadius: 4, padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: 5 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <UnlockDot unlocked={unlockedNames.has(base)} />
                <span style={{ fontSize: 12, fontWeight: 500, color: unlockedNames.has(base) ? 'var(--ink)' : 'var(--ink-3)' }}>{base}</span>
              </div>
              {ascendancies.map(asc => (
                <div key={asc} style={{ display: 'flex', alignItems: 'center', gap: 6, paddingLeft: 4 }}>
                  <UnlockDot unlocked={unlockedNames.has(asc)} />
                  <span style={{ fontSize: 10.5, color: unlockedNames.has(asc) ? 'var(--ink-2)' : 'var(--ink-4)' }}>{asc}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      {oauthStatus === 'valid' && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <label className="label" style={{ margin: 0 }}>Your characters</label>
            {loading
              ? <span className="muted mono" style={{ fontSize: 10 }}>loading…</span>
              : <button className="btn" style={{ padding: '3px 8px', fontSize: 11 }} onClick={fetchChars}>↻</button>
            }
          </div>
          {fetchErr && (
            <div style={{ fontSize: 11, color: 'var(--err)', marginBottom: 6, fontFamily: 'var(--mono)' }}>
              API error: {fetchErr}
            </div>
          )}
          {!loading && !fetchErr && chars.length === 0 && (
            <div className="muted mono" style={{ fontSize: 11 }}>No characters found.</div>
          )}
          {chars.length > 0 ? (() => {
            const byLeague = chars.reduce<Record<string, CharEntry[]>>((acc, c) => {
              ;(acc[c.league] ??= []).push(c)
              return acc
            }, {})
            return (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxHeight: 240, overflowY: 'auto' }}>
                {Object.entries(byLeague).map(([league, members]) => (
                  <div key={league}>
                    <div className="mono muted" style={{ fontSize: 10, letterSpacing: '.08em', textTransform: 'uppercase', marginBottom: 4 }}>{league}</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                      {members.map(c => (
                        <div key={c.name} onClick={() => pick(c.name)}
                          style={{
                            display: 'flex', alignItems: 'center', gap: 10, padding: '7px 12px',
                            background: name === c.name ? 'color-mix(in oklch, var(--accent) 12%, var(--panel))' : 'var(--panel)',
                            border: `1px solid ${name === c.name ? 'var(--accent)' : 'var(--rule)'}`,
                            borderRadius: 4, cursor: 'pointer',
                          }}>
                          <UnlockDot unlocked={unlockedNames.has(c.class)} />
                          <span style={{ fontSize: 13, color: 'var(--ink)', flex: 1 }}>{c.name}</span>
                          <span className="muted mono" style={{ fontSize: 10.5 }}>{c.class} · lv {c.level}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )
          })() : null}
        </div>
      )}

      <div>
        <label className="label">{oauthStatus === 'valid' ? 'Or enter name manually' : 'Character name'}</label>
        <div style={{ display: 'flex', gap: 8 }}>
          <input className="input" value={name} onChange={e => setName(e.target.value)} placeholder="ExileKyra" />
          <button className="btn" onClick={handshake}>Load</button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
        <button className="btn ghost" onClick={onNext}>skip</button>
        <div className="spacer" />
        <button className="btn primary" onClick={onNext}>Next →</button>
      </div>
    </div>
  )
}

function Step5Ready({ onDone }: { onDone: () => void }) {
  const { connection, oauthStatus, clientTxtOk, clientTxtPathOk, filterOk } = useStore()
  const action = useStore(s => s.action)
  return (
    <div style={{ maxWidth: 640, display: 'grid', gap: 20 }}>
      <p style={{ color: 'var(--ink-2)', fontSize: 14, maxWidth: 560, lineHeight: 1.55, margin: 0 }}>
        Setup complete. The client is watching your game and managing your filter automatically.
      </p>
      <div className="grid-2" style={{ maxWidth: 480 }}>
        <div className="card" style={{ padding: '12px 14px' }}>
          <div className="muted mono" style={{ fontSize: 10.5, marginBottom: 4 }}>AP server</div>
          <span className={`pill ${connection === 'connected' ? 'ok' : ''}`}>
            <span className="dot" />{connection}
          </span>
        </div>
        <div className="card" style={{ padding: '12px 14px' }}>
          <div className="muted mono" style={{ fontSize: 10.5, marginBottom: 4 }}>GGG OAuth</div>
          <span className={`pill ${oauthStatus === 'valid' ? 'ok' : ''}`}>
            <span className="dot" />{oauthStatus}
          </span>
        </div>
        <div className="card" style={{ padding: '12px 14px' }}>
          <div className="muted mono" style={{ fontSize: 10.5, marginBottom: 4 }}>Client.txt</div>
          <span className={`pill ${clientTxtOk || clientTxtPathOk ? 'ok' : ''}`}>
            <span className="dot" />{clientTxtOk ? 'tailing' : clientTxtPathOk ? 'path set' : 'not found'}
          </span>
        </div>
        <div className="card" style={{ padding: '12px 14px' }}>
          <div className="muted mono" style={{ fontSize: 10.5, marginBottom: 4 }}>Item filter</div>
          <span className={`pill ${filterOk ? 'ok' : ''}`}>
            <span className="dot" />{filterOk ? 'written' : 'pending'}
          </span>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
        <div className="spacer" />
        <button className="btn primary" onClick={() => { action({ type: 'onboardingComplete' }); onDone() }}>Open Dashboard →</button>
      </div>
    </div>
  )
}

export function Onboarding({ onDone }: { onDone: () => void }) {
  const [step, setStep] = useState(1)
  const { clientTxtPathOk, oauthStatus, connection, char } = useStore()

  const next = () => setStep(s => Math.min(s + 1, 5))

  const stepValid = (n: number): boolean => {
    switch (n) {
      case 1: return clientTxtPathOk
      case 2: return oauthStatus === 'valid'
      case 3: return connection === 'connected'
      case 4: return char !== null
      default: return false
    }
  }

  const stepState = (n: number) => {
    if (n === step) return 'active'
    if (stepValid(n)) return 'done'
    return 'idle'
  }

  const CHECK = (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
      <polyline points="1.5,5 4,7.5 8.5,2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )

  return (
    <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <aside style={{ width: 260, background: 'var(--bg-2)', borderRight: '1px solid var(--rule)', padding: '32px 28px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ fontFamily: 'var(--display)', fontSize: 24, lineHeight: 1, marginBottom: 4 }}>First run</div>
          <div className="mono muted" style={{ fontSize: 10.5, letterSpacing: '.08em', textTransform: 'uppercase', marginBottom: 32 }}>
            setup · {step} of 5
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {STEPS.map((s, i) => {
              const st = stepState(s.n)
              return (
                <div key={s.n} onClick={() => setStep(s.n)} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0', position: 'relative', cursor: 'pointer' }}>
                  <div style={{
                    width: 22, height: 22, borderRadius: '50%',
                    border: `1px solid ${st !== 'idle' ? 'var(--accent)' : 'var(--rule-2)'}`,
                    background: st === 'done' ? 'var(--accent)' : 'transparent',
                    color: st === 'done' ? '#1a1208' : st === 'active' ? 'var(--accent)' : 'var(--ink-3)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontFamily: 'var(--mono)', fontSize: 10, fontWeight: 600
                  }}>
                    {st === 'done' ? CHECK : s.n}
                  </div>
                  <span style={{
                    fontSize: 13,
                    color: st === 'active' ? 'var(--ink)' : st === 'done' ? 'var(--ink-2)' : 'var(--ink-3)',
                    fontWeight: st === 'active' ? 500 : 400
                  }}>{s.label}</span>
                  {i < STEPS.length - 1 && (
                    <div style={{ position: 'absolute', left: 10, top: 32, width: 1, height: 14, background: st === 'done' ? 'var(--accent)' : 'var(--rule-2)' }} />
                  )}
                </div>
              )
            })}
          </div>

          <div className="spacer" />
          <div className="mono muted" style={{ fontSize: 10, lineHeight: 1.7 }}>
            You can change any of this later from Settings.
          </div>
        </aside>

        <div style={{ flex: 1, overflow: 'auto', padding: '48px 56px' }}>
          <div className="mono" style={{ fontSize: 10.5, letterSpacing: '.1em', color: 'var(--accent)', textTransform: 'uppercase', marginBottom: 10 }}>
            Step {step}
          </div>
          <h1 style={{ fontFamily: 'var(--display)', fontWeight: 400, fontSize: 40, lineHeight: 1, letterSpacing: '-.01em', margin: '0 0 24px' }}>
            {step === 1 && 'Set your paths, Exile.'}
            {step === 2 && 'Login.'}
            {step === 3 && 'Connect to Archipelago server.'}
            {step === 4 && 'Choose your character.'}
            {step === 5 && "You're ready."}
          </h1>

          {step === 1 && <Step1Paths onNext={next} />}
          {step === 2 && <Step2OAuth onNext={next} />}
          {step === 3 && <Step3Connect onNext={next} />}
          {step === 4 && <Step4Character onNext={next} />}
          {step === 5 && <Step5Ready onDone={onDone} />}
        </div>
    </div>
  )
}
