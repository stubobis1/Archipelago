import { describe, it, expect, vi, beforeEach } from 'vitest'

const MOCK_ITEMS = [
  { name: 'Fireball',  classification: 'Filler', category: ['MainSkillGem'] },
  { name: 'Iron Ring', classification: 'Useful', category: ['Armour'] },
]
const MOCK_BASE_ITEMS = [
  { name: 'Rusty Sword Drop', baseItem: 'Rusty Sword', act: 1, dropLevel: 1 },
]
const MOCK_BOSSES = {
  Hillock: { name: 'Hillock', id: 1, difficulty: 0, drops: [] },
}

vi.mock('fs', () => ({
  readFileSync:  vi.fn((p: string) => {
    if (p.includes('BaseItems.json')) return JSON.stringify(MOCK_BASE_ITEMS)
    if (p.includes('Items.json'))     return JSON.stringify(MOCK_ITEMS)
    if (p.includes('Bosses.json'))    return JSON.stringify(MOCK_BOSSES)
    throw new Error(`Unexpected readFileSync: ${p}`)
  }),
  existsSync:    vi.fn(() => true),
  mkdirSync:     vi.fn(),
  copyFileSync:  vi.fn(),
  writeFileSync: vi.fn(),
}))

// Reset module registry before each test so lazy caches are cleared
beforeEach(async () => {
  vi.resetModules()
  vi.clearAllMocks()
  // Re-import the mocked fs after module reset to get the fresh spy instance
  const { existsSync } = await import('fs')
  vi.mocked(existsSync).mockReturnValue(true)
})

describe('getItems', () => {
  it('returns parsed items array', async () => {
    const { getItems } = await import('../main/data')
    expect(getItems()).toEqual(MOCK_ITEMS)
  })

  it('returns same reference on second call (lazy cache)', async () => {
    const { getItems } = await import('../main/data')
    expect(getItems()).toBe(getItems())
  })
})

describe('getItemByName', () => {
  it('finds item by exact name', async () => {
    const { getItemByName } = await import('../main/data')
    expect(getItemByName('Fireball')).toMatchObject({ name: 'Fireball' })
  })

  it('returns undefined for unknown name', async () => {
    const { getItemByName } = await import('../main/data')
    expect(getItemByName('Nonexistent')).toBeUndefined()
  })
})

describe('getBaseItems', () => {
  it('returns parsed base items array', async () => {
    const { getBaseItems } = await import('../main/data')
    expect(getBaseItems()).toEqual(MOCK_BASE_ITEMS)
  })
})

describe('getBosses', () => {
  it('returns parsed bosses record', async () => {
    const { getBosses } = await import('../main/data')
    expect(getBosses()).toMatchObject({ Hillock: { name: 'Hillock' } })
  })
})

describe('ensureJingles', () => {
  it('creates destination dir and copies missing files', async () => {
    const fs = await import('fs')
    // src files exist, dest files do not
    vi.mocked(fs.existsSync).mockImplementation((p: any) =>
      !String(p).includes('_ap_jingle')
    )
    const { ensureJingles } = await import('../main/data')
    const dest = ensureJingles('/poe/docs')
    expect(dest).toContain('_ap_jingle')
    expect(fs.mkdirSync).toHaveBeenCalledWith(dest, { recursive: true })
    expect(fs.copyFileSync).toHaveBeenCalledTimes(5)
  })

  it('skips copy when dest files already exist', async () => {
    const fs = await import('fs')
    vi.mocked(fs.existsSync).mockReturnValue(true)
    const { ensureJingles } = await import('../main/data')
    ensureJingles('/poe/docs')
    expect(fs.copyFileSync).not.toHaveBeenCalled()
  })
})
