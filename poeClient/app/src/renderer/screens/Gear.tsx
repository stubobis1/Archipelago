import { useStore } from '../store'
import { PaperDoll } from '../components/PaperDoll'

export function GearScreen() {
  const { items, char, errors } = useStore()

  const anyUnlocked = items.some(i =>
    /^(Progressive|Normal|Magic|Rare|Unique) /.test(i.name) ||
    i.name.startsWith('Progressive Flask')
  )

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      <div className="page-header">
        <h1>Equipment</h1>
        <div className="sub">
          AP unlock tiers · {char ? `${char.name} · ${char.class} lv ${char.level}` : 'no character loaded'}
          {errors.length > 0 && <span className="pill err" style={{ marginLeft: 12 }}>{errors.length} issues</span>}
        </div>
      </div>

      <div style={{ padding: '28px 28px' }}>
        {!anyUnlocked && (
          <div style={{ color: 'var(--ink-3)', fontSize: 13, textAlign: 'center', padding: '60px 0' }}>
            Connect to the multiworld to see equipment.
          </div>
        )}

        {anyUnlocked && <PaperDoll items={items} />}

        {errors.length > 0 && (
          <div style={{ marginTop: 32, maxWidth: 640 }}>
            <div className="label" style={{ marginBottom: 12 }}>Validation errors</div>
            {errors.map((e, i) => (
              <div key={i} style={{ background: 'color-mix(in oklch, var(--err) 8%, var(--panel))', border: '1px solid color-mix(in oklch, var(--err) 40%, var(--rule))', borderRadius: 4, padding: '10px 14px', marginBottom: 6, fontSize: 12.5 }}>
                <span className="mono" style={{ color: 'var(--err)', marginRight: 10 }}>{e.slot}</span>
                <span style={{ color: 'var(--ink-2)' }}>{e.msg}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
