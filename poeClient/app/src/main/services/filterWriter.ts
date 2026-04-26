import * as fs from 'fs'
import * as path from 'path'
import type { FilterDisplay, FilterSound } from '@shared/types'

const AP_FILTER      = '__ap'
const INVALID_FILTER = '__invalid'

// Mirrored from worlds/poe/poeClient/itemFilter.py
const STYLE: Record<string, string[]> = {
  Progression: [
    'SetFontSize 45',
    'SetTextColor 201 117 130 255',
    'SetBorderColor 117 194 116 255',
    'SetBackgroundColor 238 227 147 255',
    'MinimapIcon 0 Green UpsideDownHouse',
    'PlayEffect Cyan',
  ],
  Useful: [
    'SetFontSize 38',
    'SetTextColor 201 117 130 255',
    'SetBorderColor 117 194 116 255',
    'SetBackgroundColor 238 227 147 225',
    'MinimapIcon 1 Green UpsideDownHouse',
    'PlayEffect Cyan Temp',
  ],
  Filler: [
    'SetFontSize 31',
    'SetTextColor 201 117 130 255',
    'SetBorderColor 117 194 116 255',
    'SetBackgroundColor 238 227 147 200',
    'MinimapIcon 2 Green UpsideDownHouse',
  ],
  Trap: [
    'SetFontSize 45',
    'SetBackgroundColor 201 117 130 255',
    'SetBorderColor 117 194 116 255',
    'SetTextColor 238 227 147 255',
    'MinimapIcon 2 Red Cross',
    'PlayEffect Red Temp',
  ],
}

const MINIMAP_COLORS = ['Red','Green','Blue','Brown','White','Yellow','Cyan','Grey','Orange','Pink','Purple']
const MINIMAP_SHAPES = ['Circle','Diamond','Hexagon','Square','Star','Triangle','Cross','Moon','Raindrop','Kite','Pentagon','UpsideDownHouse']
const RAND_SOUND_CLASSES = ['Progression','ProgUseful','Useful','Filler','Trap']

const ri = (lo: number, hi: number) => Math.floor(Math.random() * (hi - lo + 1)) + lo
const rp = <T>(a: T[]): T => a[Math.floor(Math.random() * a.length)]

function randomStyleLines(): string[] {
  return [
    `SetFontSize ${ri(28, 45)}`,
    `SetTextColor ${ri(0,255)} ${ri(0,255)} ${ri(0,255)} ${ri(180,255)}`,
    `SetBorderColor ${ri(0,255)} ${ri(0,255)} ${ri(0,255)} ${ri(0,255)}`,
    `SetBackgroundColor ${ri(0,255)} ${ri(0,255)} ${ri(0,255)} ${ri(100,255)}`,
    `MinimapIcon ${ri(0,2)} ${rp(MINIMAP_COLORS)} ${rp(MINIMAP_SHAPES)}`,
    `PlayEffect ${rp(MINIMAP_COLORS)}`,
  ]
}

/**
 * Map Archipelago item flags bitmask to a classification string.
 * Flags: 0b001=progression, 0b010=useful, 0b100=trap, 0b011=skip_balancing(ProgUseful)
 * Exported for testing.
 */
export function classificationFromFlags(flags: number): string {
  if ((flags & 0b011) === 0b011) return 'ProgUseful'
  if (flags & 0b001) return 'Progression'
  if (flags & 0b100) return 'Trap'
  if (flags & 0b010) return 'Useful'
  return 'Filler'
}

const filterPath = (docDir: string, name: string) => path.join(docDir, `${name}.filter`)

/** Filter block shown when the AP filter is not yet loaded — solid red to signal the error state. */
function invalidBlock(): string {
  return [
    'Show',
    'SetTextColor 255 0 0 0',
    'SetBorderColor 255 0 0 255',
    'SetBackgroundColor 255 0 0 255',
    '',
  ].join('\n')
}

export interface FilterWriteOptions {
  docDir:             string
  /** Unchecked AP location base item names + item flags. Empty = not connected. */
  uncheckedBaseItems: { baseItem: string; flags: number }[]
  baseFilter:         string
  display:            FilterDisplay
  sound:              FilterSound
  soundDir?:          string
}

/**
 * Write `__ap.filter` and `__invalid.filter` to `docDir`.
 * Returns the paths and block/size stats for the AP filter.
 */
export function writeFilters(opts: FilterWriteOptions): { apPath: string; invalidPath: string; blocks: number; sizeKB: number } {
  const { docDir, uncheckedBaseItems, baseFilter, display, sound, soundDir = '' } = opts

  const apBlocks = uncheckedBaseItems.flatMap(({ baseItem, flags }) => {
    if (display === 1) return []  // hide mode — emit nothing

    const [styleLines, soundClass] = (() => {
      if (display === 2) return [randomStyleLines(), rp(RAND_SOUND_CLASSES)]
      if (display === 3) return [STYLE['Progression'], 'Progression']
      const cls = classificationFromFlags(flags)
      return [STYLE[cls === 'ProgUseful' ? 'Useful' : cls] ?? STYLE['Progression'], cls]
    })()

    const lines = ['Show', `BaseType == "${baseItem}"`, ...styleLines]
    if (sound === 2 && soundDir) {
      lines.push(`CustomAlertSoundOptional "${path.join(soundDir, `${soundClass}.wav`).replace(/\\/g, '/')}" 300`)
    }
    lines.push('')
    return [lines.join('\n')]
  })

  if (baseFilter) apBlocks.push(`Import "${baseFilter}"`)

  const apContent = apBlocks.join('\n')
  const apPath    = filterPath(docDir, AP_FILTER)
  fs.writeFileSync(apPath, apContent, 'utf8')

  const blocks = (apContent.match(/^Show$/gm) ?? []).length
  const sizeKB = parseFloat((Buffer.byteLength(apContent, 'utf8') / 1024).toFixed(1))

  const invalidPath = filterPath(docDir, INVALID_FILTER)
  fs.writeFileSync(invalidPath, invalidBlock(), 'utf8')

  return { apPath, invalidPath, blocks, sizeKB }
}

/** Read block count and file size for an existing filter file. */
export function filterStats(apPath: string): { blocks: number; sizeKB: number } {
  try {
    const text   = fs.readFileSync(apPath, 'utf8')
    const blocks = (text.match(/^Show$/gm) ?? []).length
    const sizeKB = parseFloat((Buffer.byteLength(text, 'utf8') / 1024).toFixed(1))
    return { blocks, sizeKB }
  } catch {
    return { blocks: 0, sizeKB: 0 }
  }
}
