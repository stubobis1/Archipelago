import { describe, it, expect, vi, beforeEach } from 'vitest'
import { classificationFromFlags, writeFilters, filterStats } from '../main/services/filterWriter'

// ── classificationFromFlags ───────────────────────────────────────────────────

describe('classificationFromFlags', () => {
  it('classifies 0 as Filler', () => {
    expect(classificationFromFlags(0b000)).toBe('Filler')
  })

  it('classifies 0b001 as Progression', () => {
    expect(classificationFromFlags(0b001)).toBe('Progression')
  })

  it('classifies 0b010 as Useful', () => {
    expect(classificationFromFlags(0b010)).toBe('Useful')
  })

  it('classifies 0b100 as Trap', () => {
    expect(classificationFromFlags(0b100)).toBe('Trap')
  })

  it('classifies 0b011 as ProgUseful (skip-balancing)', () => {
    expect(classificationFromFlags(0b011)).toBe('ProgUseful')
  })

  it('Progression takes priority over Trap when both set', () => {
    // 0b101 = progression + trap — progression wins via ProgUseful check first, then Progression
    expect(classificationFromFlags(0b101)).toBe('Progression')
  })
})

// ── writeFilters ──────────────────────────────────────────────────────────────

// Mock fs so tests don't write to disk
vi.mock('fs', async () => {
  const written: Record<string, string> = {}
  return {
    writeFileSync: vi.fn((p: string, content: string) => { written[p] = content }),
    readFileSync:  vi.fn((p: string) => written[p] ?? ''),
    existsSync:    vi.fn(() => true),
    _written:      written,
  }
})

import * as fs from 'fs'

beforeEach(() => {
  vi.mocked(fs.writeFileSync).mockClear()
})

describe('writeFilters', () => {
  const baseOpts = {
    docDir:             '/poe/docs',
    uncheckedBaseItems: [] as { baseItem: string; flags: number }[],
    baseFilter:         '',
    display:            0 as const,
    sound:              0 as const,
  }

  it('writes two files (ap + invalid)', () => {
    writeFilters(baseOpts)
    expect(fs.writeFileSync).toHaveBeenCalledTimes(2)
    const paths = vi.mocked(fs.writeFileSync).mock.calls.map(c => c[0])
    expect(paths.some((p: unknown) => String(p).includes('__ap.filter'))).toBe(true)
    expect(paths.some((p: unknown) => String(p).includes('__invalid.filter'))).toBe(true)
  })

  it('produces one Show block per unchecked item (display=show)', () => {
    const opts = {
      ...baseOpts,
      uncheckedBaseItems: [
        { baseItem: 'Siege Axe',  flags: 0b001 },
        { baseItem: 'Iron Ring',  flags: 0b010 },
        { baseItem: 'Life Flask', flags: 0 },
      ],
    }
    const { blocks } = writeFilters(opts)
    expect(blocks).toBe(3)
  })

  it('produces zero Show blocks when display=hide', () => {
    const opts = {
      ...baseOpts,
      display: 1 as const,
      uncheckedBaseItems: [
        { baseItem: 'Siege Axe', flags: 0b001 },
      ],
    }
    const { blocks } = writeFilters(opts)
    expect(blocks).toBe(0)
  })

  it('appends Import directive when baseFilter provided', () => {
    const opts = { ...baseOpts, baseFilter: 'Neversink' }
    writeFilters(opts)
    const apCall = vi.mocked(fs.writeFileSync).mock.calls.find(c => String(c[0]).includes('__ap.filter'))
    expect(apCall?.[1]).toContain('Import "Neversink"')
  })

  it('includes CustomAlertSoundOptional when sound=jingles and soundDir set', () => {
    const opts = {
      ...baseOpts,
      sound:              2 as const,
      soundDir:           '/poe/docs/_ap_jingle',
      uncheckedBaseItems: [{ baseItem: 'Iron Ring', flags: 0b001 }],
    }
    writeFilters(opts)
    const apCall = vi.mocked(fs.writeFileSync).mock.calls.find(c => String(c[0]).includes('__ap.filter'))
    expect(apCall?.[1]).toContain('CustomAlertSoundOptional')
    expect(apCall?.[1]).toContain('Progression.wav')
  })

  it('display=2 (randomize): still produces one block per item', () => {
    const opts = {
      ...baseOpts,
      display:            2 as const,
      uncheckedBaseItems: [{ baseItem: 'Siege Axe', flags: 0b001 }],
    }
    const { blocks } = writeFilters(opts)
    expect(blocks).toBe(1)
  })

  it('display=3 (uniform): all items get Progression style', () => {
    const opts = {
      ...baseOpts,
      display:            3 as const,
      uncheckedBaseItems: [
        { baseItem: 'Siege Axe', flags: 0b010 },  // would be Useful in display=0
        { baseItem: 'Iron Ring', flags: 0b100 },  // would be Trap in display=0
      ],
    }
    writeFilters(opts)
    const apCall = vi.mocked(fs.writeFileSync).mock.calls.find(c => String(c[0]).includes('__ap.filter'))
    const content = apCall?.[1] as string
    // Both items should have Progression font size (45), not Trap or Useful sizes
    expect(content.match(/SetFontSize 45/g)?.length).toBe(2)
  })

  it('invalid filter block contains Show with red styling', () => {
    writeFilters(baseOpts)
    const invalidCall = vi.mocked(fs.writeFileSync).mock.calls.find(c => String(c[0]).includes('__invalid.filter'))
    expect(invalidCall?.[1]).toContain('Show')
    expect(invalidCall?.[1]).toContain('255 0 0')
  })
})

// ── filterStats ───────────────────────────────────────────────────────────────

describe('filterStats', () => {
  it('counts Show blocks and reports size', () => {
    vi.mocked(fs.readFileSync).mockReturnValueOnce('Show\nBaseType == "x"\n\nShow\nBaseType == "y"\n')
    const { blocks } = filterStats('/any/path/__ap.filter')
    expect(blocks).toBe(2)
  })

  it('returns zeros when file unreadable', () => {
    vi.mocked(fs.readFileSync).mockImplementationOnce(() => { throw new Error('ENOENT') })
    expect(filterStats('/missing.filter')).toEqual({ blocks: 0, sizeKB: 0 })
  })
})
