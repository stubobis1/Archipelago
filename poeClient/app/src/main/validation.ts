// Port of worlds/poe/poeClient/validationLogic.py
import type { GGGCharacter } from './services/gggApi'
import type { ReceivedItem, ValidationError } from '@shared/types'
import { getItems } from './data'

// frameType: 0=normal 1=magic 2=rare 3=unique
const RARITY_NAMES = ['Normal', 'Magic', 'Rare', 'Unique']

// GucciHoboMode values from Options.py
const enum GucciHoboMode {
  Disabled         = 0,
  OneSlotAnyRarity = 1,
  OneSlotNormal    = 2,
  NoNonUnique      = 3,
}

const SLOT_NAMES = [
  'BodyArmour', 'Amulet', 'Belt', 'Boots', 'Gloves',
  'Helmet', 'Ring', 'Ring2', 'Weapon', 'Offhand',
]

export interface ValidationCtx {
  receivedItems:  ReceivedItem[]
  gucciMode?:     number
  goal?:          number
  seedName?:      string
}

function rarityCheck(
  receivedNames: Set<string>,
  rarity: number,
  slot: string,
  gucciMode: GucciHoboMode,
): string | null {
  if (gucciMode === GucciHoboMode.Disabled) return null
  if (rarity === 3) return null  // unique always OK

  if (gucciMode === GucciHoboMode.NoNonUnique) {
    return `${slot}: only unique items allowed (GucciHobo mode 3)`
  }
  if (gucciMode === GucciHoboMode.OneSlotNormal) {
    return rarity > 0 ? `${slot}: only Normal rarity items allowed (GucciHobo mode 2)` : null
  }
  return null
}

/**
 * Validate equipped items against received AP items.
 * Returns one error per slot/gem that violates the current GucciHobo mode or is not yet received.
 */
export function validateCharEquipment(char: GGGCharacter, ctx: ValidationCtx): ValidationError[] {
  const receivedNames = new Set(ctx.receivedItems.map(i => i.name))
  const equipment = (char.equipment ?? {}) as Record<string, any>

  return SLOT_NAMES.flatMap(slot => {
    const item = equipment[slot]
    if (!item) return []

    const errors: ValidationError[] = []

    const rarityErr = rarityCheck(receivedNames, item.frameType ?? 0, slot, ctx.gucciMode ?? 0)
    if (rarityErr) errors.push({ slot, msg: rarityErr })

    const gemErrors = (item.socketedItems as any[] ?? [])
      .filter(gem => gem.typeLine && !gem.support)
      .filter(gem => ![...receivedNames].some(n => n.includes(gem.typeLine) || gem.typeLine.includes(n)))
      .map(gem => ({ slot: `${slot}:gem`, msg: `${gem.typeLine} not yet received` }))

    return [...errors, ...gemErrors]
  })
}

/**
 * Validate passive point allocation against received AP passive items.
 * Flags over-allocation (more than received × 2 + 24 baseline).
 */
export function validatePassivePoints(char: GGGCharacter, ctx: ValidationCtx): ValidationError[] {
  const received  = ctx.receivedItems.filter(i =>
    i.classification === 'PassiveSkillPoint' || i.name.includes('Passive')
  ).length
  const allocated = (char.passives as any)?.hashes?.length ?? 0
  const max       = received * 2 + 24

  if (allocated > max) {
    return [{ slot: 'Passives', msg: `${allocated} passives allocated but only ${received} received (max ~${max})` }]
  }
  return []
}

/** Zone name reached at the end of each act (for campaign/act completion goals). */
const GOAL_ZONES: Record<number, string> = {
  0: 'Karui Shores',   // full campaign
  1: 'Southern Forest',
  2: 'City of Sarn',
  3: 'Aqueduct',
  4: 'Slave Pens',
  5: 'Karui Fortress',
  6: 'Bridge Encampment',
  7: 'Sarn Ramparts',
  8: 'Blood Aqueduct',
  9: 'Oriath Docks',
}

/** Returns `true` when the player has entered the completion zone for the given goal type. */
export function checkGoalZone(goalType: number, zone: string): boolean {
  const target = GOAL_ZONES[goalType]
  return !!target && zone === target
}
