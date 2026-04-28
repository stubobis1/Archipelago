import { settingsService } from './services/settings'
import { getCachedCharacter } from './services/gggApi'
import { openChatAndSend, queueChatSend } from './services/gameInput'
import { getItems } from './data'
import { state, patch, pushChat, timestamp, sc, getPendingGoalToken, setPendingGoalToken } from './ipc-state'

let _pendingCharToken: string | null = null

function receivedIds(): Set<number> {
  return new Set(state.items.map(i => i.id))
}

function receivedOfCategory(cat: string) {
  const ids = receivedIds()
  return getItems().filter(i => i.category?.includes(cat) && ids.has(i.id))
}

function gemsOfCategory(cat: string, maxLevel?: number) {
  return receivedOfCategory(cat)
    .filter(i => maxLevel == null || (i.reqLevel ?? 0) <= maxLevel)
    .sort((a, b) => (a.reqLevel ?? 0) - (b.reqLevel ?? 0))
}

function rarityFromProgCount(n: number): string {
  if (n >= 4) return 'Any'
  if (n === 3) return 'up to Rare'
  if (n === 2) return 'up to Magic'
  return 'Normal'
}

function gearMessage(filterCat: string): string {
  const ids  = receivedIds()
  const pool = getItems().filter(i => i.category?.includes(filterCat))
  const recv = pool.filter(i => ids.has(i.id))

  const progCounts: Record<string, number> = {}
  for (const item of recv) {
    if (item.category?.includes('Progressive')) {
      const base = item.name.replace('Progressive ', '')
      progCounts[base] = (progCounts[base] ?? 0) + 1
    }
  }
  const progParts = Object.entries(progCounts).map(([k, v]) => `${rarityFromProgCount(v)} ${k}`)

  const RARITIES = ['Normal', 'Magic', 'Rare', 'Unique']
  const singles  = recv.filter(i => !i.category?.includes('Progressive') && RARITIES.some(r => i.category?.includes(r)))
  const singleParts = singles.map(i => i.name)

  const parts = [...progParts, ...singleParts]
  return parts.length ? parts.join(', ') : 'none'
}

function goalMessage(): string {
  const g = state.goal
  if (!g) return 'No goal set'
  const GOAL_NAMES: Record<number, string> = {
    0: 'Complete the campaign (reach Karui Shores)',
    1: 'Complete Act 1 (reach The Southern Forest)',
    2: 'Complete Act 2 (reach The City of Sarn)',
    3: 'Complete Act 3 (reach The Aqueduct)',
    4: 'Complete Act 4 (reach The Slave Pens)',
    5: 'Reach Karui Fortress (Act 5/6)',
    6: 'Complete Act 6 (reach The Bridge Encampment)',
    7: 'Complete Act 7 (reach The Sarn Ramparts)',
    8: 'Complete Act 8 (reach The Blood Aqueduct)',
    9: 'Complete Act 9 (reach Oriath Docks)',
    10: 'Defeat bosses',
  }
  const name = GOAL_NAMES[g.type] ?? `Goal type ${g.type}`
  if (g.type === 10 && g.bosses?.length) {
    const parts = g.bosses.map(b => (g.defeated.includes(b) ? `✓${b}` : `✗${b}`))
    return `${name}: ${parts.join(' ')}${g.complete ? ' — ALL DONE!' : ''}`
  }
  return `${name} — ${g.complete ? 'complete!' : 'in progress'}`
}

async function sendGameChat(resp: string): Promise<void> {
  const prefix = `@${state.char?.name ?? state.slotName} `
  const MAX    = 500 - prefix.length
  for (let i = 0; i < resp.length; i += MAX) {
    await openChatAndSend(prefix + resp.slice(i, i + MAX))
  }
}

export async function handleChatCommand(who: string, msg: string): Promise<void> {
  const trimmed = msg.trim()

  // Goal zone verification token — char whispers back the token to confirm in-game identity
  const goalToken = getPendingGoalToken()
  if (goalToken && trimmed.includes(goalToken) && who === (state.char?.name ?? state.slotName)) {
    setPendingGoalToken(null)
    if (state.goal && !state.goal.eligible) {
      patch({ goal: { ...state.goal, eligible: true } })
      pushChat({ t: timestamp(), kind: 'sys', body: 'Character verified — click Send Goal to complete!' })
    }
    return
  }

  // Token response from self-whisper char identification — check before owner filter
  if (_pendingCharToken && trimmed === `char_${_pendingCharToken}`) {
    _pendingCharToken = null
    settingsService.set('lastCharName', who, ...sc())
    settingsService.set('lastCharName', who)
    patch({ charName: who })
    const gggChar = await getCachedCharacter(who, true)
    if (gggChar) patch({ char: gggChar as any, charName: gggChar.name })
    pushChat({ t: timestamp(), kind: 'sys', body: `Character identified: ${who}` })
    return
  }

  // !ap char — must be before the owner guard so it works before character is identified
  const cmd0 = trimmed.toLowerCase()
  if (['!ap char', '!ap character', '!apchar', '!ap setchar', '!ap setcharacter', '!ap_char'].includes(cmd0)) {
    const token = Math.random().toString(36).slice(2, 10)
    _pendingCharToken = token
    queueChatSend(`char_${token}`)
    pushChat({ t: timestamp(), kind: 'sys', body: `Identifying character — sent char_${token}` })
    return
  }

  // Only respond to our own character's messages.
  // Fall back to charName when char object is absent (no OAuth / API offline).
  const knownChar = state.char?.name ?? state.charName ?? null
  if (!knownChar || (who !== knownChar && who !== state.slotName)) return

  const cmd = trimmed.toLowerCase()
  const charLevel = state.char?.level

  let resp: string | null = null

  if (['!help', '!commands', '!cmds'].includes(cmd)) {
    resp = '!gear !weapons !armor !links !flasks !gems !main gems !support gems !utility gems !usable gems !ascendancy !passives !deathlink !whisper updates !goal !help'
  } else if (cmd === '!gear') {
    resp = `Gear: ${gearMessage('Gear')}`
  } else if (cmd === '!weapons') {
    resp = `Weapons: ${gearMessage('Weapon')}`
  } else if (['!armor', '!armour'].includes(cmd)) {
    resp = `Armour: ${gearMessage('Armour')}`
  } else if (cmd === '!links') {
    const links = receivedOfCategory('max links')
    const counts: Record<string, number> = {}
    for (const i of links) counts[i.name] = (counts[i.name] ?? 0) + 1
    resp = Object.keys(counts).length
      ? Object.entries(counts).map(([k, v]) => `${k}: ${v}`).join(', ')
      : 'No link items'
  } else if (['!flasks', '!flask'].includes(cmd)) {
    const flasks = receivedOfCategory('Flask')
    const counts: Record<string, number> = {}
    for (const i of flasks) counts[i.name] = (counts[i.name] ?? 0) + 1
    resp = Object.keys(counts).length
      ? Object.entries(counts).map(([k, v]) => `${k}: ${v}`).join(', ')
      : 'No flask items'
  } else if (['!gems', '!all gems'].includes(cmd)) {
    const gems = [
      ...gemsOfCategory('MainSkillGem'),
      ...gemsOfCategory('SupportGem'),
      ...gemsOfCategory('UtilSkillGem'),
      ...receivedOfCategory('GemModifier'),
    ]
    resp = gems.length ? gems.map(g => g.name).join(', ') : 'No gems'
  } else if (cmd === '!main gems') {
    const gems = gemsOfCategory('MainSkillGem')
    resp = gems.length ? gems.map(g => g.name).join(', ') : 'No skill gems'
  } else if (cmd === '!support gems') {
    const gems = gemsOfCategory('SupportGem')
    resp = gems.length ? gems.map(g => g.name).join(', ') : 'No support gems'
  } else if (cmd === '!utility gems') {
    const gems = gemsOfCategory('UtilSkillGem')
    resp = gems.length ? gems.map(g => g.name).join(', ') : 'No utility gems'
  } else if (cmd === '!usable gems') {
    const gems = [
      ...gemsOfCategory('MainSkillGem', charLevel),
      ...gemsOfCategory('SupportGem',   charLevel),
      ...gemsOfCategory('UtilSkillGem', charLevel),
    ].sort((a, b) => (b.reqLevel ?? 0) - (a.reqLevel ?? 0))
    resp = gems.length ? gems.map(g => `${g.name}(${g.reqLevel ?? 0})`).join(', ') : 'No usable gems'
  } else if (cmd === '!usable skill gems') {
    const gems = gemsOfCategory('MainSkillGem', charLevel).reverse()
    resp = gems.length ? gems.map(g => `${g.name}(${g.reqLevel ?? 0})`).join(', ') : 'No usable skill gems'
  } else if (cmd === '!usable support gems') {
    const gems = gemsOfCategory('SupportGem', charLevel).reverse()
    resp = gems.length ? gems.map(g => `${g.name}(${g.reqLevel ?? 0})`).join(', ') : 'No usable support gems'
  } else if (cmd === '!usable utility gems') {
    const gems = gemsOfCategory('UtilSkillGem', charLevel).reverse()
    resp = gems.length ? gems.map(g => `${g.name}(${g.reqLevel ?? 0})`).join(', ') : 'No usable utility gems'
  } else if (['!ascendancy', '!ascendancies', '!classes', '!class'].includes(cmd)) {
    const items = receivedOfCategory('Ascendancy')
    resp = items.length ? items.map(i => i.name).join(', ') : 'No ascendancy items'
  } else if (['!p', '!passive', '!passives'].includes(cmd)) {
    const received  = state.items.filter(i => i.name === 'Progressive passive point').length
    const allocated = (state.char?.passives as any)?.hashes?.length ?? 0
    resp = `${received - allocated} passive points available (${allocated}/${received} used for ${state.char?.name ?? '?'})`
  } else if (cmd === '!deathlink') {
    const newVal = !state.deathlink
    patch({ deathlink: newVal })
    settingsService.set('deathlink', newVal, ...sc())
    resp = `DeathLink ${newVal ? 'enabled' : 'disabled'}`
  } else if (['!whisper updates', '!whisper update', '!updates', '!update'].includes(cmd)) {
    const newVal = !state.whisperUpdates
    patch({ whisperUpdates: newVal })
    settingsService.set('whisperUpdates', newVal, ...sc())
    resp = `Whisper updates ${newVal ? 'enabled' : 'disabled'}`
  } else if (cmd === '!goal') {
    resp = goalMessage()
  }

  if (resp) {
    pushChat({ t: timestamp(), kind: 'self', body: resp })
    await sendGameChat(resp)
  }
}
