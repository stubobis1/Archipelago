// Port of worlds/poe/poeClient/validationLogic.py
import type { GGGCharacter } from './services/gggApi'
import type { APBoss, ReceivedItem, ValidationError } from '@shared/types'
import { getAlternateGems } from './data'

const RARITY_NAMES = ['Normal', 'Magic', 'Rare', 'Unique'] as const

const enum GucciHoboMode {
  Disabled         = 0,
  OneSlotAnyRarity = 1,
  OneSlotNormal    = 2,
  NoNonUnique      = 3,
}

const SIMPLE_SLOTS   = ['BodyArmour', 'Amulet', 'Belt', 'Boots', 'Gloves', 'Helmet']
const WEAPON_TYPES   = ['Axe', 'Bow', 'Claw', 'Dagger', 'Mace', 'Sceptre', 'Staff', 'Sword', 'Wand', 'Shield', 'Quiver']
const IGNORE_INV_IDS = new Set(['BrequelGrafts', 'BrequelGrafts2'])

export interface ValidationCtx {
  receivedItems: ReceivedItem[]
  gucciMode?:    number
  goal?:         number
  seedName?:     string
}

function rarityName(frameType: number): string {
  return RARITY_NAMES[frameType] ?? 'Normal'
}

function countNamed(names: string[], target: string): number {
  let n = 0
  for (const x of names) if (x === target) n++
  return n
}

// Port of Python rarity_check(): validate slot rarity against progressive/specific received items
function rarityCheck(receivedNames: string[], frameType: number, slot: string): string | null {
  const rarity = rarityName(frameType)
  const prog   = countNamed(receivedNames, `Progressive ${slot}`)
  let valid: boolean
  if      (rarity === 'Unique') valid = receivedNames.includes(`Unique ${slot}`) || prog >= 4
  else if (rarity === 'Rare')   valid = receivedNames.includes(`Rare ${slot}`)   || prog >= 3
  else if (rarity === 'Magic')  valid = receivedNames.includes(`Magic ${slot}`)  || prog >= 2
  else                          valid = receivedNames.includes(`Normal ${slot}`)  || prog >= 1
  return valid ? null : slot
}

// GGG API v2 returns equipment as an array; normalize to array regardless
export function toEquipArray(char: GGGCharacter): any[] {
  if (!char.equipment) return []
  return Array.isArray(char.equipment) ? char.equipment as any[] : Object.values(char.equipment)
}

export function validateCharEquipment(char: GGGCharacter, ctx: ValidationCtx): ValidationError[] {
  const receivedNames = ctx.receivedItems.map(i => i.name)
  const errors: ValidationError[] = []
  const altGems = getAlternateGems()

  // Class ownership
  const charClass: string = (char as any).class ?? ''
  if (charClass && !receivedNames.includes(charClass)) {
    errors.push({ slot: 'Class', msg: `Class ${charClass} not received` })
  }

  const items = toEquipArray(char)
  const gucciTally: Record<string, number> = {}
  let normalFlasks = 0, magicFlasks = 0, uniqueFlasks = 0

  for (const item of items) {
    const inv: string = item.inventoryId ?? ''
    const ft: number  = item.frameType   ?? 0
    const rarity      = rarityName(ft)

    if (IGNORE_INV_IDS.has(inv)) continue

    // Simple armour/accessory slots
    if (SIMPLE_SLOTS.includes(inv)) {
      const e = rarityCheck(receivedNames, ft, inv)
      if (e) errors.push({ slot: inv, msg: e })
    }

    // Rings
    if (inv === 'Ring')  { const e = rarityCheck(receivedNames, ft, 'Ring (left)');  if (e) errors.push({ slot: inv, msg: e }) }
    if (inv === 'Ring2') { const e = rarityCheck(receivedNames, ft, 'Ring (right)'); if (e) errors.push({ slot: inv, msg: e }) }

    // Weapon/offhand — detect type from item properties
    if (inv === 'Weapon' || inv === 'Offhand') {
      for (const prop of (item.properties ?? []) as { name: string }[]) {
        for (const wt of WEAPON_TYPES) {
          if (prop.name?.toLowerCase().endsWith(wt.toLowerCase())) {
            const e = rarityCheck(receivedNames, ft, wt)
            if (e) errors.push({ slot: inv, msg: e })
          }
        }
      }
    }

    // Flask slots (Flask1–Flask5)
    if (/^Flask\d*$/.test(inv)) {
      if      (rarity === 'Normal') normalFlasks++
      else if (rarity === 'Magic')  magicFlasks++
      else if (rarity === 'Unique') uniqueFlasks++
      continue  // skip rarity/gem checks for flasks
    }

    // Socketed gems
    let supportCount = 0
    for (const gem of (item.socketedItems ?? []) as any[]) {
      if (gem.support) supportCount++
      const bt: string = gem.baseType ?? gem.typeLine ?? ''
      if (!bt || bt.toLowerCase().includes('eye jewel')) continue

      if (bt.startsWith('Vaal ')) {
        if (!receivedNames.includes('Vaal Gems'))
          errors.push({ slot: `${inv}:gem`, msg: `Vaal gem ${bt} requires "Vaal Gems"` })
        continue
      }
      const alt = altGems[bt]
      if (alt) {
        if (!receivedNames.includes(alt.baseGem))
          errors.push({ slot: `${inv}:gem`, msg: `Alt gem ${bt} requires ${alt.baseGem}` })
        continue
      }
      if (!receivedNames.includes(bt))
        errors.push({ slot: `${inv}:gem`, msg: `${bt} not received` })
    }

    // Link count: support gems linked > received progressive link items
    const linksHeld = countNamed(receivedNames, `Progressive max links - ${inv}`)
    if (supportCount > linksHeld)
      errors.push({ slot: inv, msg: `Too many supports in ${item.typeLine ?? inv} (${supportCount} linked, ${linksHeld} received)` })

    // Track non-flask rarity for Gucci mode
    gucciTally[rarity] = (gucciTally[rarity] ?? 0) + 1
  }

  // Flask rarity caps (max 5 of each type)
  let fp = countNamed(receivedNames, 'Progressive Flask Unlock')
  const normalAllowed = Math.min(5, Math.max(countNamed(receivedNames, 'Progressive Normal Flask Unlock'), fp))
  fp -= 5
  const magicAllowed  = Math.min(5, Math.max(countNamed(receivedNames, 'Progressive Magic Flask Unlock'),  Math.max(0, fp)))
  fp -= 5
  const uniqueAllowed = Math.min(5, Math.max(countNamed(receivedNames, 'Progressive Unique Flask Unlock'), Math.max(0, fp)))
  if (normalFlasks > normalAllowed) errors.push({ slot: 'Flask', msg: `Too many Normal flasks (${normalFlasks}/${normalAllowed} allowed)` })
  if (magicFlasks  > magicAllowed)  errors.push({ slot: 'Flask', msg: `Too many Magic flasks (${magicFlasks}/${magicAllowed} allowed)` })
  if (uniqueFlasks > uniqueAllowed) errors.push({ slot: 'Flask', msg: `Too many Unique flasks (${uniqueFlasks}/${uniqueAllowed} allowed)` })

  // Gucci Hobo mode
  const gm = ctx.gucciMode ?? GucciHoboMode.Disabled
  if (gm !== GucciHoboMode.Disabled) {
    const n = gucciTally['Normal'] ?? 0, mg = gucciTally['Magic'] ?? 0, r = gucciTally['Rare'] ?? 0
    if (gm === GucciHoboMode.OneSlotAnyRarity && n + mg + r > 1)
      errors.push({ slot: 'GucciHobo', msg: 'Max 1 non-unique item (mode 1)' })
    if (gm === GucciHoboMode.OneSlotNormal && (n > 1 || mg + r > 0))
      errors.push({ slot: 'GucciHobo', msg: 'Max 1 Normal item, no Magic/Rare (mode 2)' })
    if (gm === GucciHoboMode.NoNonUnique && n + mg + r > 0)
      errors.push({ slot: 'GucciHobo', msg: 'No non-unique items allowed (mode 3)' })
  }

  return errors
}

export function validatePassivePoints(char: GGGCharacter, ctx: ValidationCtx): ValidationError[] {
  // Count received "Progressive passive point" items (1:1 ratio, no multiplier)
  const passiveItems = ctx.receivedItems.filter(i => i.name === 'Progressive passive point').length
  const allocated    = (char.passives as any)?.hashes?.length ?? 0
  if (allocated > passiveItems) {
    return [{ slot: 'Passives', msg: `${allocated - passiveItems} over-allocated (${allocated} used, ${passiveItems} received)` }]
  }
  return []
}

// Goal zone names keyed by Options.Goal values
export const GOAL_ZONES: Record<number, string> = {
  0: 'Karui Shores',
  1: 'The Southern Forest',
  2: 'The City of Sarn',
  3: 'The Aqueduct',
  4: 'The Slave Pens',
  5: 'The Karui Fortress',
  6: 'The Bridge Encampment',
  7: 'The Sarn Ramparts',
  8: 'The Blood Aqueduct',
  9: 'Oriath Docks',
}

/** Returns true when the player has entered the goal completion zone. */
export function checkGoalZone(goalType: number, zone: string): boolean {
  const target = GOAL_ZONES[goalType]
  return !!target && zone === target
}

/** Scan character inventory for boss drops. Returns defeated boss keys (e.g. "defeat hydra"). */
export function checkBossDrops(char: GGGCharacter, bosses: Record<string, APBoss>): string[] {
  const inv: any[]  = Array.isArray((char as any).inventory) ? (char as any).inventory : []
  const heldNames   = new Set(inv.map((i: any) => i.name || i.typeLine || '').filter(Boolean))
  return Object.entries(bosses)
    .filter(([, boss]) => boss.drops.some(d => heldNames.has(d.name)))
    .map(([key]) => key)
}
