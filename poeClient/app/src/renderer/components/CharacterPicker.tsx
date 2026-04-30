import { useState, useEffect } from 'react'
import { useStore } from '../store'

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

export function CharacterPicker() {
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
    <div style={{ display: 'grid', gap: 20 }}>
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
    </div>
  )
}
