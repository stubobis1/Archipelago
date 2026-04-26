import { describe, it, expect, vi } from 'vitest'
import { checkGoalZone, validatePassivePoints, validateCharEquipment } from '../main/validation'
import type { ValidationCtx } from '../main/validation'

// Mock data module — tests shouldn't read from disk
vi.mock('../main/data', () => ({
  getItems: vi.fn(() => [
    { name: 'Normal Helmet', classification: 'Filler', category: ['Helmet'] },
    { name: 'Magic Helmet',  classification: 'Useful', category: ['Helmet'] },
    { name: 'Fireball',      classification: 'Filler', category: ['MainSkillGem'] },
  ]),
}))

// ── checkGoalZone ─────────────────────────────────────────────────────────────

describe('checkGoalZone', () => {
  it('returns true for the correct completion zone', () => {
    expect(checkGoalZone(1, 'Southern Forest')).toBe(true)
    expect(checkGoalZone(0, 'Karui Shores')).toBe(true)
    expect(checkGoalZone(9, 'Oriath Docks')).toBe(true)
  })

  it('returns false for wrong zone', () => {
    expect(checkGoalZone(1, 'The Mud Flats')).toBe(false)
    expect(checkGoalZone(0, 'Southern Forest')).toBe(false)
  })

  it('returns false for unknown goal type', () => {
    expect(checkGoalZone(99, 'Karui Shores')).toBe(false)
  })
})

// ── validatePassivePoints ─────────────────────────────────────────────────────

function makeChar(allocatedPassives: number): any {
  return { passives: { hashes: Array(allocatedPassives).fill(0) }, equipment: {} }
}

function makeCtx(receivedPassives: number): ValidationCtx {
  return {
    receivedItems: Array(receivedPassives).fill({ name: 'Progressive passive point', classification: 'PassiveSkillPoint', category: [], id: 0, from: '', index: 0 }),
  }
}

describe('validatePassivePoints', () => {
  it('returns no errors when within budget', () => {
    // baseline: 0 received → max = 24
    expect(validatePassivePoints(makeChar(20), makeCtx(0))).toHaveLength(0)
  })

  it('returns error when over-allocated', () => {
    // 0 received → max = 24; 30 allocated = over
    const errs = validatePassivePoints(makeChar(30), makeCtx(0))
    expect(errs).toHaveLength(1)
    expect(errs[0].slot).toBe('Passives')
    expect(errs[0].msg).toMatch(/30 passives allocated/)
  })

  it('scales max with received items', () => {
    // 10 received → max = 44; 44 allocated should be fine
    expect(validatePassivePoints(makeChar(44), makeCtx(10))).toHaveLength(0)
    // 45 allocated = over
    expect(validatePassivePoints(makeChar(45), makeCtx(10))).toHaveLength(1)
  })
})

// ── rarityCheck via validateCharEquipment (GucciHoboMode) ────────────────────

describe('GucciHoboMode rarity checks', () => {
  const baseChar = (frameType: number) => ({
    equipment: { Helmet: { frameType, socketedItems: [] } },
    passives: { hashes: [] },
  } as any)

  it('mode 0 (disabled): any rarity allowed', () => {
    expect(validateCharEquipment(baseChar(0), { receivedItems: [], gucciMode: 0 })).toHaveLength(0)
    expect(validateCharEquipment(baseChar(1), { receivedItems: [], gucciMode: 0 })).toHaveLength(0)
  })

  it('mode 3 (NoNonUnique): non-unique returns error', () => {
    const errs = validateCharEquipment(baseChar(0), { receivedItems: [], gucciMode: 3 })
    expect(errs.some(e => e.msg.includes('only unique items allowed'))).toBe(true)
  })

  it('mode 3 (NoNonUnique): unique (frameType 3) is fine', () => {
    expect(validateCharEquipment(baseChar(3), { receivedItems: [], gucciMode: 3 })).toHaveLength(0)
  })

  it('mode 2 (OneSlotNormal): magic rarity returns error', () => {
    const errs = validateCharEquipment(baseChar(1), { receivedItems: [], gucciMode: 2 })
    expect(errs.some(e => e.msg.includes('only Normal rarity'))).toBe(true)
  })

  it('mode 2 (OneSlotNormal): normal rarity is fine', () => {
    expect(validateCharEquipment(baseChar(0), { receivedItems: [], gucciMode: 2 })).toHaveLength(0)
  })
})

// ── validateCharEquipment ─────────────────────────────────────────────────────

describe('validateCharEquipment', () => {
  it('returns no errors when no equipment', () => {
    const char = { equipment: {}, passives: { hashes: [] } } as any
    const ctx: ValidationCtx = { receivedItems: [], gucciMode: 0 }
    expect(validateCharEquipment(char, ctx)).toHaveLength(0)
  })

  it('reports unsocketed gem not received', () => {
    const char = {
      equipment: {
        Helmet: {
          frameType: 0,
          socketedItems: [{ typeLine: 'Firestorm', support: false }],
        },
      },
      passives: { hashes: [] },
    } as any
    const ctx: ValidationCtx = { receivedItems: [], gucciMode: 0 }
    const errs = validateCharEquipment(char, ctx)
    expect(errs.some(e => e.msg.includes('Firestorm'))).toBe(true)
  })

  it('does not report gem as missing when received', () => {
    const char = {
      equipment: {
        Helmet: {
          frameType: 0,
          socketedItems: [{ typeLine: 'Fireball', support: false }],
        },
      },
      passives: { hashes: [] },
    } as any
    const ctx: ValidationCtx = {
      receivedItems: [{ name: 'Fireball', classification: 'Filler', category: ['MainSkillGem'], id: 0, from: '', index: 0 }],
      gucciMode: 0,
    }
    expect(validateCharEquipment(char, ctx)).toHaveLength(0)
  })

  it('does not report support gems as errors', () => {
    const char = {
      equipment: {
        Helmet: {
          frameType: 0,
          socketedItems: [{ typeLine: 'Faster Attacks Support', support: true }],
        },
      },
      passives: { hashes: [] },
    } as any
    const ctx: ValidationCtx = { receivedItems: [], gucciMode: 0 }
    expect(validateCharEquipment(char, ctx)).toHaveLength(0)
  })
})
