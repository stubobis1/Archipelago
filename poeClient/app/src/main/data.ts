import * as fs from 'fs'
import * as path from 'path'
import type { APItem, APBaseItem, APBoss, AlternateGem } from '@shared/types'

function dataDir(): string {
  return process.env.NODE_ENV === 'development'
    ? path.resolve(__dirname, '../../resources/data')
    : path.join(process.resourcesPath, 'data')
}

function jinglesSourceDir(): string {
  return process.env.NODE_ENV === 'development'
    ? path.resolve(__dirname, '../../resources/sounds/jingles')
    : path.join(process.resourcesPath, 'sounds', 'jingles')
}

function randomSoundsSourceDir(): string {
  return process.env.NODE_ENV === 'development'
    ? path.resolve(__dirname, '../../resources/sounds/random')
    : path.join(process.resourcesPath, 'sounds', 'random')
}

const RANDOM_SOUND_DIR_NAME = '_ap_random'

/**
 * Copy random wav files into `{docDir}/_ap_random/` if not already present.
 * Returns the destination directory path.
 */
export function ensureRandomSounds(docDir: string): string {
  const dest = path.join(docDir, RANDOM_SOUND_DIR_NAME)
  fs.mkdirSync(dest, { recursive: true })
  const src = randomSoundsSourceDir()
  if (fs.existsSync(src)) {
    for (const f of fs.readdirSync(src).filter(n => n.toLowerCase().endsWith('.wav'))) {
      const dstFile = path.join(dest, f)
      if (!fs.existsSync(dstFile)) fs.copyFileSync(path.join(src, f), dstFile)
    }
  }
  return dest
}

const JINGLE_DIR_NAME = '_ap_jingle'
const JINGLE_FILES = ['Progression.wav', 'Useful.wav', 'Filler.wav', 'Trap.wav', 'ProgUseful.wav']

/**
 * Copy jingle wav files into `{docDir}/_ap_jingle/` if not already present.
 * Returns the destination directory path.
 */
export function ensureJingles(docDir: string): string {
  const dest = path.join(docDir, JINGLE_DIR_NAME)
  fs.mkdirSync(dest, { recursive: true })
  const src = jinglesSourceDir()
  for (const f of JINGLE_FILES) {
    const srcFile = path.join(src, f)
    const dstFile = path.join(dest, f)
    if (fs.existsSync(srcFile) && !fs.existsSync(dstFile)) {
      fs.copyFileSync(srcFile, dstFile)
    }
  }
  return dest
}

function readJson<T>(name: string): T {
  return JSON.parse(fs.readFileSync(path.join(dataDir(), name), 'utf8')) as T
}

// Lazy-loaded singletons — parsed once on first access
let _items:     APItem[]                        | null = null
let _baseItems: APBaseItem[]                    | null = null
let _bosses:    Record<string, APBoss>          | null = null
let _altGems:   Record<string, AlternateGem>   | null = null

/** All AP item definitions (lazy-loaded from Items.json). */
export function getItems(): APItem[] {
  return (_items ??= readJson<APItem[]>('Items.json'))
}

/** All AP base item definitions (lazy-loaded from BaseItems.json). */
export function getBaseItems(): APBaseItem[] {
  return (_baseItems ??= readJson<APBaseItem[]>('BaseItems.json'))
}

/** All AP boss definitions keyed by name (lazy-loaded from Bosses.json). */
export function getBosses(): Record<string, APBoss> {
  return (_bosses ??= readJson<Record<string, APBoss>>('Bosses.json'))
}

/** Alternate gem map keyed by alternate gem name (lazy-loaded from AlternateGems.json). */
export function getAlternateGems(): Record<string, AlternateGem> {
  return (_altGems ??= readJson<Record<string, AlternateGem>>('AlternateGems.json'))
}

/** Look up a single AP item by name. */
export function getItemByName(name: string): APItem | undefined {
  return getItems().find(i => i.name === name)
}
