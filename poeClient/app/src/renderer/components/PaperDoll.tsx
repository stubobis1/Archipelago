import React from 'react'
import type { ReceivedItem } from '@shared/types'

export const TIER_LABELS       = ['Normal', 'Magic', 'Rare', 'Unique'] as const
export const TIER_CLS          = ['eq-rarity-normal', 'eq-rarity-magic', 'eq-rarity-rare', 'eq-rarity-unique']
export const FLASK_TIER_LABELS = ['Normal', 'Magic', 'Unique'] as const
export const FLASK_TIER_CLS    = ['eq-rarity-normal', 'eq-rarity-magic', 'eq-rarity-unique']

export const WEAPON_SUBS  = ['Axe','Bow','Claw','Dagger','Mace','Sceptre','Staff','Sword','Wand']
export const OFFHAND_SUBS = ['Shield', 'Quiver']

export const imgUrl = (name: string) =>
  `ap-assets:///images/${name.toLowerCase().replace(/['\s]/g, '')}.png`

export function buildCounts(items: ReceivedItem[]): Record<string, number> {
  return items.reduce<Record<string, number>>((acc, i) => {
    acc[i.name] = (acc[i.name] || 0) + 1
    return acc
  }, {})
}

export function slotTiers(counts: Record<string, number>, base: string): boolean[] {
  const prog = counts[`Progressive ${base}`] || 0
  return TIER_LABELS.map((t, i) => !!(counts[`${t} ${base}`] || prog >= i + 1))
}

const CountsCtx = React.createContext<Record<string, number>>({})
const useCounts = () => React.useContext(CountsCtx)

function TierRow({ tiers, labels, css }: { tiers: boolean[]; labels: readonly string[]; css: string[] }) {
  return (
    <div className="eq-rarity-row">
      {labels.map((t, i) => (
        <React.Fragment key={t}>
          {i > 0 && <span className="eq-rarity-sep">·</span>}
          <span className={tiers[i] ? css[i] : 'eq-rarity-off'}>{t}</span>
        </React.Fragment>
      ))}
    </div>
  )
}

function TierStack({ tiers, labels, css }: { tiers: boolean[]; labels: readonly string[]; css: string[] }) {
  return (
    <div className="eq-rarity-stack">
      {labels.map((t, i) => <span key={t} className={tiers[i] ? css[i] : 'eq-rarity-off'}>{t}</span>)}
    </div>
  )
}

function Tier2col({ tiers }: { tiers: boolean[] }) {
  const c = (i: number) => <span className={tiers[i] ? TIER_CLS[i] : 'eq-rarity-off'}>{TIER_LABELS[i]}</span>
  return (
    <div className="eq-rarity-2col">
      {c(0)}<span className="eq-rarity-sep">·</span>{c(1)}
      {c(2)}<span className="eq-rarity-sep">·</span>{c(3)}
    </div>
  )
}

function LinkDots({ linkName, unlocked }: { linkName: string; unlocked: boolean }) {
  const counts = useCounts()
  const MAX: Record<string, number> = { Helm: 4, Gloves: 4, Boots: 4, BodyArmour: 6, Weapon: 6, Offhand: 3 }
  const max = MAX[linkName]
  if (!max) return null
  const prog = counts[`Progressive max links - ${linkName}`] || 0
  if (prog === 0 && !unlocked) return null
  const cur   = prog + 1
  const label = `${cur} link${cur !== 1 ? 's' : ''}`
  return (
    <div className="eq-links">
      <div className="eq-links-label">{label}</div>
      <div className="eq-link-row">
        {Array.from({ length: max }).map((_, i) => (
          <React.Fragment key={i}>
            {i > 0 && <span className={`eq-link-conn${i < cur ? ' lit' : ''}`} />}
            <span className={`eq-link-dot${i < cur ? ' lit' : ''}`} />
          </React.Fragment>
        ))}
      </div>
    </div>
  )
}

function EqSlot({ area, title, base, imgFile, linkName, variant = 'row', slotClass = '' }: {
  area: string; title: string; base: string; imgFile: string
  linkName?: string; variant?: 'row' | 'stack' | '2col'; slotClass?: string
}) {
  const counts   = useCounts()
  const tiers    = slotTiers(counts, base)
  const unlocked = tiers.some(Boolean)
  return (
    <div className={`eq-slot${unlocked ? '' : ' eq-slot-empty'}${slotClass ? ` ${slotClass}` : ''}`} style={{ gridArea: area }}>
      <div className="eq-slot-title">{title}</div>
      <img className="eq-slot-img" src={imgUrl(imgFile)} alt={title}
        onError={e => { (e.target as HTMLImageElement).style.display = 'none' }} />
      {variant === 'stack' && <TierStack tiers={tiers} labels={TIER_LABELS} css={TIER_CLS} />}
      {variant === '2col'  && <Tier2col tiers={tiers} />}
      {variant === 'row'   && <TierRow  tiers={tiers} labels={TIER_LABELS} css={TIER_CLS} />}
      {linkName && <LinkDots linkName={linkName} unlocked={unlocked} />}
    </div>
  )
}

function MultiSlot({ area, title, subs, linkName, imgFile, slotClass = '' }: {
  area: string; title: string; subs: string[]; linkName?: string; imgFile?: string; slotClass?: string
}) {
  const counts   = useCounts()
  const unlocked = subs.some(sub => slotTiers(counts, sub).some(Boolean))
  return (
    <div className={`eq-slot${unlocked ? '' : ' eq-slot-empty'}${slotClass ? ` ${slotClass}` : ''}`} style={{ gridArea: area }}>
      <div className="eq-slot-title">{title}</div>
      {imgFile && (
        <img className="eq-slot-img" src={imgUrl(imgFile)} alt={title}
          onError={e => { (e.target as HTMLImageElement).style.display = 'none' }} />
      )}
      <div className="eq-sub-list">
        {subs.map(sub => (
          <div className="eq-sub-row" key={sub}>
            <span className="eq-sub-label">{sub}</span>
            <Tier2col tiers={slotTiers(counts, sub)} />
          </div>
        ))}
      </div>
      {linkName && <LinkDots linkName={linkName} unlocked={unlocked} />}
    </div>
  )
}

function FlaskSlot({ slotNum }: { slotNum: number }) {
  const counts     = useCounts()
  const prog       = counts['Progressive Flask Unlock']        || 0
  const normProg   = counts['Progressive Normal Flask Unlock'] || 0
  const magicProg  = counts['Progressive Magic Flask Unlock']  || 0
  const uniqueProg = counts['Progressive Unique Flask Unlock'] || 0
  const tiers = [
    prog >= slotNum      || normProg  >= slotNum,
    prog >= slotNum + 5  || magicProg >= slotNum,
    prog >= slotNum + 10 || uniqueProg >= slotNum,
  ]
  const unlocked = tiers.some(Boolean)
  return (
    <div className={`eq-slot${unlocked ? '' : ' eq-slot-empty'}`}>
      <div className="eq-slot-title">Flask {slotNum}</div>
      <img className="eq-slot-img" src={imgUrl('Progressive Normal Flask Unlock')} alt={`Flask ${slotNum}`}
        onError={e => { (e.target as HTMLImageElement).style.display = 'none' }} />
      <TierStack tiers={tiers} labels={FLASK_TIER_LABELS} css={FLASK_TIER_CLS} />
    </div>
  )
}

export function PaperDoll({ items, mobile }: { items: ReceivedItem[]; mobile?: boolean }) {
  const counts = buildCounts(items)
  const anyUnlocked = items.some(i =>
    /^(Progressive|Normal|Magic|Rare|Unique) /.test(i.name) ||
    i.name.startsWith('Progressive Flask')
  )

  if (!anyUnlocked) return null

  return (
    <CountsCtx.Provider value={counts}>
      <div className={`eq-grid${mobile ? ' eq-grid-mobile' : ''}`}>
        <EqSlot area="helmet"     title="Helmet"      base="Helmet"     imgFile="normalhelmet"     linkName="Helm"       variant="2col" />
        <MultiSlot area="weapon"  title="Weapon"      subs={WEAPON_SUBS}                           linkName="Weapon" />
        <MultiSlot area="offhand" title="Offhand"     subs={OFFHAND_SUBS}                          linkName="Offhand"   imgFile="normalshield" slotClass="eq-slot-lg" />
        <EqSlot area="body"       title="Body Armour" base="BodyArmour" imgFile="normalbodyarmour" linkName="BodyArmour" variant="2col" slotClass="eq-slot-lg" />
        <EqSlot area="amulet"     title="Amulet"      base="Amulet"     imgFile="normalamulet"                          variant="stack" />
        <EqSlot area="ringleft"   title="Left Ring"   base="Ring (left)"  imgFile="normalring(left)"                    variant="stack" />
        <EqSlot area="ringright"  title="Right Ring"  base="Ring (right)" imgFile="normalring(right)"                   variant="stack" />
        <EqSlot area="gloves"     title="Gloves"      base="Gloves"     imgFile="normalgloves"     linkName="Gloves"    variant="2col" />
        <EqSlot area="belt"       title="Belt"        base="Belt"       imgFile="normalbelt"                            variant="2col" />
        <EqSlot area="boots"      title="Boots"       base="Boots"      imgFile="normalboots"      linkName="Boots"     variant="2col" />
        <div className="eq-flask-row">
          {[1, 2, 3, 4, 5].map(n => <FlaskSlot key={n} slotNum={n} />)}
        </div>
      </div>
    </CountsCtx.Provider>
  )
}
