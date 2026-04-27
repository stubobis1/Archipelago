import React from 'react'
import { useStore } from '../store'

const GOAL_NAMES: Record<number, string> = {
  0:  'Complete the Campaign',
  1:  'Complete Act 1',
  2:  'Complete Act 2',
  3:  'Complete Act 3',
  4:  'Complete Act 4',
  5:  'Complete Act 5',
  6:  'Complete Act 6',
  7:  'Complete Act 7',
  8:  'Complete Act 8',
  9:  'Complete Act 9',
  10: 'Defeat Bosses',
}

export function GoalScreen() {
  const { goal, action } = useStore()

  if (!goal) {
    return (
      <div style={{ flex: 1, overflow: 'auto' }}>
        <div className="page-header">
          <h1>Goal</h1>
          <div className="sub">Connect to a server to see your goal.</div>
        </div>
        <div style={{ padding: '60px 28px', textAlign: 'center', color: 'var(--ink-3)' }}>
          No active goal. Connect to an Archipelago server.
        </div>
      </div>
    )
  }

  const goalName    = GOAL_NAMES[goal.type] ?? `Goal ${goal.type}`
  const totalBosses = goal.bosses?.length ?? 0
  const defeated    = goal.defeated.length
  const canSend     = goal.eligible && !goal.complete

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <div className="page-header">
        <h1>Goal</h1>
        <div className="sub" style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <span>{goalName}</span>
          {goal.complete && <span className="pill ok"><span className="dot" />complete</span>}
          {goal.eligible && !goal.complete && <span className="pill" style={{ background: 'var(--accent-soft)', color: 'var(--accent)' }}><span className="dot" style={{ background: 'var(--accent)' }} />ready</span>}
        </div>
      </div>

      <div style={{ padding: '28px 28px' }}>

        {/* Boss defeat goal */}
        {goal.type === 10 && (
          <>
            <div className="label" style={{ marginBottom: 16 }}>Bosses · {defeated}/{totalBosses}</div>

            {goal.bosses && goal.bosses.length > 0 ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 10, maxWidth: 800 }}>
                {goal.bosses.map(boss => {
                  const done = goal.defeated.includes(boss)
                  return (
                    <div key={boss} className="card" style={{
                      padding: '12px 16px',
                      opacity: done ? 1 : 0.6,
                      borderColor: done ? 'color-mix(in oklch, var(--ok) 50%, var(--rule))' : undefined,
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        {done
                          ? <span style={{ color: 'var(--ok)', fontSize: 14 }}>✓</span>
                          : <span style={{ color: 'var(--ink-4)', fontSize: 14 }}>✗</span>
                        }
                        <span style={{ fontSize: 13, color: done ? 'var(--ink)' : 'var(--ink-2)' }}>{boss}</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="muted mono" style={{ fontSize: 12, marginBottom: 16 }}>No bosses configured for this goal.</div>
            )}

            {totalBosses > 0 && (
              <div style={{ marginTop: 28, maxWidth: 400 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span className="mono muted" style={{ fontSize: 11 }}>Progress</span>
                  <span className="mono" style={{ fontSize: 11 }}>{defeated}/{totalBosses}</span>
                </div>
                <div style={{ height: 6, background: 'var(--rule)', borderRadius: 99, overflow: 'hidden' }}>
                  <div style={{
                    width: `${totalBosses > 0 ? (defeated / totalBosses) * 100 : 0}%`,
                    height: '100%',
                    background: goal.complete ? 'var(--ok)' : 'var(--accent)',
                    borderRadius: 99,
                    transition: 'width .4s',
                  }} />
                </div>
              </div>
            )}
          </>
        )}

        {/* Zone-based goals */}
        {goal.type < 10 && (
          <div className="card" style={{ maxWidth: 400, padding: '20px 22px' }}>
            <div style={{ fontFamily: 'var(--display)', fontSize: 22, marginBottom: 8 }}>{goalName}</div>
            {goal.complete
              ? <span className="pill ok" style={{ fontSize: 12 }}><span className="dot" />Complete!</span>
              : goal.eligible
                ? <span className="muted mono" style={{ fontSize: 12, color: 'var(--accent)' }}>Character verified — ready to send goal.</span>
                : <span className="muted mono" style={{ fontSize: 12 }}>Enter the goal zone in-game to complete.</span>
            }
          </div>
        )}

        {/* Send Goal button */}
        {!goal.complete && (
          <div style={{ marginTop: 32 }}>
            <button
              className="btn"
              style={{
                padding: '10px 28px',
                fontSize: 14,
                fontWeight: 600,
                background: canSend ? 'var(--ok)' : undefined,
                color: canSend ? '#fff' : undefined,
                cursor: canSend ? 'pointer' : 'not-allowed',
                opacity: canSend ? 1 : 0.4,
              }}
              disabled={!canSend}
              onClick={() => action({ type: 'sendGoal' })}
            >
              Send Goal
            </button>
            {!goal.eligible && (
              <div className="muted mono" style={{ fontSize: 11, marginTop: 8 }}>
                {goal.type === 10
                  ? 'Defeat all required bosses to unlock.'
                  : 'Enter the goal zone in-game to unlock.'}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
