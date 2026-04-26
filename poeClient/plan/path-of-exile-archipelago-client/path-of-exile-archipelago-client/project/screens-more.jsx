// Gear page — paper-doll layout matching stubobis1/pathofexile_ap grid
// Plus: Items page (gems/support/util etc), Goal, Chat full, Settings, Tray, Onboarding already in own file.

// ============ ICON SILHOUETTES for equipment slots ============
// Minimal inline SVG silhouettes — placeholder art, one per slot type.
const Silh = {
  helmet: (s=38) => <svg width={s} height={s} viewBox="0 0 40 40" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"><path d="M8 26c0-8 5-14 12-14s12 6 12 14v4H8z"/><path d="M14 30v4M20 30v4M26 30v4"/></svg>,
  body:   (s=80) => <svg width={s} height={s*1.55} viewBox="0 0 40 60" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"><path d="M10 8 L20 4 L30 8 L33 22 L28 24 L28 52 L12 52 L12 24 L7 22 Z"/><path d="M20 4 V24"/></svg>,
  gloves: (s=36) => <svg width={s} height={s} viewBox="0 0 40 40" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"><path d="M8 14 Q8 10 12 10 L24 10 Q32 10 32 18 L32 28 Q32 34 26 34 L14 34 Q8 34 8 28 Z"/><path d="M14 10v-4M20 10v-4M26 10v-3"/></svg>,
  boots:  (s=36) => <svg width={s} height={s} viewBox="0 0 40 40" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"><path d="M14 6 L14 22 L10 30 L10 34 L30 34 L30 26 L22 22 L22 6 Z"/></svg>,
  belt:   (s=36) => <svg width={s*1.3} height={s*0.5} viewBox="0 0 52 20" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"><rect x="4" y="6" width="44" height="8" rx="1"/><rect x="22" y="3" width="8" height="14" rx="1"/><circle cx="26" cy="10" r="1.5"/></svg>,
  amulet: (s=36) => <svg width={s} height={s} viewBox="0 0 40 40" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"><path d="M8 8 Q20 20 32 8"/><path d="M20 22 L16 30 L20 34 L24 30 Z"/></svg>,
  ring:   (s=30) => <svg width={s} height={s} viewBox="0 0 40 40" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"><ellipse cx="20" cy="24" rx="9" ry="7"/><path d="M16 18 L14 10 L26 10 L24 18"/><path d="M20 14 L20 10"/></svg>,
  weapon: (s=80) => <svg width={s*0.6} height={s*1.55} viewBox="0 0 24 60" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"><path d="M12 2 L16 10 L16 44 L12 50 L8 44 L8 10 Z"/><path d="M8 44 L4 48 L4 52 L20 52 L20 48 L16 44"/><path d="M12 52 V58"/></svg>,
  offhand:(s=80) => <svg width={s*0.65} height={s*1.55} viewBox="0 0 26 60" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"><path d="M13 3 L22 8 L22 30 Q22 46 13 56 Q4 46 4 30 L4 8 Z"/><path d="M13 12 V48"/><path d="M6 22 H20"/></svg>,
  flask:  (s=28) => <svg width={s} height={s*1.3} viewBox="0 0 24 32" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"><path d="M9 3 L15 3 L15 10 L18 14 Q20 18 20 22 Q20 28 12 28 Q4 28 4 22 Q4 18 6 14 L9 10 Z"/><path d="M8 3 H16"/></svg>,
};

// ============ EQUIPMENT SLOT ============
// state: 'empty' | 'filled' (any tier unlocked)
// tiers = {normal,magic,rare,unique} booleans. 'invalid' triggers flash.
const RarityRow = ({tiers, style="2col", showUnique=true}) => {
  const items = [
    ["Normal", "eq-r-normal", tiers.normal],
    ["Magic",  "eq-r-magic",  tiers.magic],
    ["Rare",   "eq-r-rare",   tiers.rare],
  ];
  if (showUnique) items.push(["Unique","eq-r-unique", tiers.unique]);

  if (style === "2col") {
    return (
      <div className="eq-rarity-2col">
        {items.slice(0,2).map(([l, c, on], i) => (
          <React.Fragment key={i}>
            {i>0 && <span className="eq-r-sep">·</span>}
            <span className={on ? c : "eq-r-off"}>{l}</span>
          </React.Fragment>
        ))}
        {items.length > 2 && <span style={{gridColumn:"1 / -1", height:1}}/>}
        {items.slice(2).map(([l, c, on], i) => (
          <React.Fragment key={"b"+i}>
            {i>0 && <span className="eq-r-sep">·</span>}
            <span className={on ? c : "eq-r-off"}>{l}</span>
          </React.Fragment>
        ))}
      </div>
    );
  }
  return (
    <div className="eq-rarity-stack">
      {items.map(([l, c, on], i) => (
        <span key={i} className={on ? c : "eq-r-off"}>{l}</span>
      ))}
    </div>
  );
};

const LinkDots = ({max, lit, labelOverride}) => {
  const dots = [];
  for (let i=0; i<max; i++) {
    if (i > 0) dots.push(<span key={`c${i}`} className={`eq-link-conn ${i < lit ? "lit" : ""}`}/>);
    dots.push(<span key={`d${i}`} className={`eq-link-dot ${i < lit ? "lit" : ""}`}/>);
  }
  return (
    <div className="eq-links">
      <div className="eq-links-label">{labelOverride || `${lit} of ${max} links`}</div>
      <div className="eq-link-row">{dots}</div>
    </div>
  );
};

const EqSlot = ({area, title, tiers, silh, links, invalid, rarityStyle="2col", showUnique=true, big=false}) => {
  const filled = tiers && Object.values(tiers).some(Boolean);
  return (
    <div className={`eq-slot ${filled ? "filled" : "empty"} ${invalid ? "invalid" : ""}`} style={{gridArea: area}}>
      <div className="eq-slot-title">{title}</div>
      <div className="eq-silhouette">{silh}</div>
      {tiers && <RarityRow tiers={tiers} style={rarityStyle} showUnique={showUnique}/>}
      {links && <LinkDots max={links.max} lit={links.lit}/>}
      {invalid && <div style={{position:"absolute", top:6, right:6}} className="mono" >
        <span style={{fontSize:9, color:"var(--err)", letterSpacing:".08em"}}>⚠ INVALID</span>
      </div>}
    </div>
  );
};

const EqMultiSlot = ({area, title, subtypes, silh, links}) => {
  const anyFilled = subtypes.some(s => Object.values(s.tiers).some(Boolean));
  return (
    <div className={`eq-slot ${anyFilled ? "filled" : "empty"}`} style={{gridArea: area}}>
      <div className="eq-slot-title">{title}</div>
      <div className="eq-silhouette">{silh}</div>
      <div className="eq-sub-list">
        {subtypes.map(s => (
          <div key={s.label} className="eq-sub-row">
            <span className="eq-sub-label">{s.label}</span>
            <RarityRow tiers={s.tiers} style="2col" showUnique={false}/>
          </div>
        ))}
      </div>
      {links && <LinkDots max={links.max} lit={links.lit}/>}
    </div>
  );
};

// ============ GEAR PAGE ============
const GearScreen = () => {
  // Sample progression state — mirrors the reference data shape
  const t = (n,m,r,u=false) => ({normal:n, magic:m, rare:r, unique:u});
  return (
    <div className="app">
      <TitleBar charName="Kyra · Witch 34" />
      <div className="shell">
        <Sidebar active="gear" items={NAV_ITEMS} />
        <div className="content">
          <div className="page-header" style={{display:"flex", alignItems:"flex-end", justifyContent:"space-between"}}>
            <div>
              <h1>Gear</h1>
              <div className="sub">
                Paper-doll of unlocked rarity tiers per slot.
                <span className="mono muted" style={{marginLeft:10, fontSize:11.5}}>!gear · !weapons · !armor · !flasks · !links</span>
              </div>
            </div>
            <div style={{display:"flex", gap:6, alignItems:"center"}}>
              <span className="pill warn"><span className="dot"/>1 slot flagged</span>
              <div className="seg">
                <div className="opt active">progression</div>
                <div className="opt">requirements</div>
              </div>
            </div>
          </div>

          <div style={{padding:"24px 24px 18px", flex:1, overflow:"auto"}}>
            <div className="eq-grid">
              <EqSlot
                area="helmet"
                title="Helmet"
                silh={Silh.helmet()}
                tiers={t(true, true, false)}
                links={{max:4, lit:2}}
              />
              <EqMultiSlot
                area="weapon"
                title="Weapon"
                silh={Silh.weapon()}
                links={{max:6, lit:4}}
                subtypes={[
                  {label:"Axe",     tiers:t(true,false,false)},
                  {label:"Bow",     tiers:t(false,false,false)},
                  {label:"Claw",    tiers:t(true,true,false)},
                  {label:"Dagger",  tiers:t(true,true,true)},
                  {label:"Mace",    tiers:t(false,false,false)},
                  {label:"Sceptre", tiers:t(true,false,false)},
                  {label:"Staff",   tiers:t(false,false,false)},
                  {label:"Sword",   tiers:t(true,true,false)},
                  {label:"Wand",    tiers:t(true,true,true)},
                ]}
              />
              <EqMultiSlot
                area="offhand"
                title="Offhand"
                silh={Silh.offhand()}
                links={{max:3, lit:2}}
                subtypes={[
                  {label:"Shield", tiers:t(true,true,false)},
                  {label:"Quiver", tiers:t(false,false,false)},
                ]}
              />
              <EqSlot
                area="body"
                title="Body Armour"
                silh={Silh.body()}
                tiers={t(true,true,true,false)}
                links={{max:6, lit:5}}
                rarityStyle="2col"
              />
              <EqSlot
                area="amulet"
                title="Amulet"
                silh={Silh.amulet()}
                tiers={t(false,false,false,false)}
                rarityStyle="stack"
              />
              <EqSlot
                area="ringleft"
                title="Left Ring"
                silh={Silh.ring()}
                tiers={t(true,false,false,false)}
                rarityStyle="stack"
              />
              <EqSlot
                area="ringright"
                title="Right Ring"
                silh={Silh.ring()}
                tiers={t(false,false,false,false)}
                rarityStyle="stack"
                invalid
              />
              <EqSlot
                area="gloves"
                title="Gloves"
                silh={Silh.gloves()}
                tiers={t(true,true,false)}
                links={{max:4, lit:2}}
              />
              <EqSlot
                area="belt"
                title="Belt"
                silh={Silh.belt()}
                tiers={t(true,true,false)}
              />
              <EqSlot
                area="boots"
                title="Boots"
                silh={Silh.boots()}
                tiers={t(true,false,false)}
                links={{max:4, lit:1}}
              />
              {/* Flasks row */}
              <div className="eq-flask-row">
                {[1,2,3,4,5].map(n => (
                  <EqSlot
                    key={n}
                    area=""
                    title={`Flask ${n}`}
                    silh={Silh.flask()}
                    tiers={{
                      normal: n <= 3,
                      magic:  n <= 2,
                      rare:   false,
                      unique: n === 1,
                    }}
                    showUnique={true}
                    rarityStyle="stack"
                  />
                ))}
              </div>
            </div>

            {/* Bottom legend / warnings */}
            <div style={{marginTop: 22, display:"grid", gridTemplateColumns:"1fr 1fr", gap: 14}}>
              <div className="card" style={{padding:"12px 16px"}}>
                <div className="h3-row"><h3>Tier legend</h3></div>
                <div style={{display:"flex", gap:18, flexWrap:"wrap", fontFamily:"var(--mono)", fontSize:11}}>
                  <span className="eq-r-normal">NORMAL</span>
                  <span className="eq-r-magic">MAGIC</span>
                  <span className="eq-r-rare">RARE</span>
                  <span className="eq-r-unique">UNIQUE</span>
                  <span style={{color:"var(--ink-4)"}}>· Dim = locked. Unlock tiers by receiving the corresponding AP items.</span>
                </div>
              </div>
              <div className="card" style={{padding:"12px 16px", borderColor:"color-mix(in oklch, var(--err) 30%, var(--rule))"}}>
                <div className="h3-row"><h3 style={{color:"var(--err)"}}>Invalid · Right Ring</h3></div>
                <div style={{fontSize:12, color:"var(--ink-2)", lineHeight:1.45}}>
                  You equipped an item here but no tier is unlocked for Right Ring.
                  <br/><span className="muted">Either unequip it, or check Client.txt for a parsing error (last scan 2s ago).</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============ ITEMS PAGE (gems / classes / flasks / etc) ============
const ItemsScreen = () => {
  const Section = ({title, count, children}) => (
    <div style={{marginBottom: 18}}>
      <div style={{display:"flex", alignItems:"center", justifyContent:"space-between", padding:"4px 0 4px", borderBottom:"1px solid var(--rule)", marginBottom:10}}>
        <h3 style={{margin:0, fontFamily:"var(--mono)", fontSize:10.5, letterSpacing:".1em", textTransform:"uppercase", color:"var(--accent)"}}>{title}</h3>
        <span className="mono muted" style={{fontSize:10.5}}>{count}</span>
      </div>
      <div style={{display:"flex", flexWrap:"wrap", gap:6}}>{children}</div>
    </div>
  );
  const Tag = ({name, cls="", count, level}) => (
    <span className={`item-tag ${cls}`} style={{
      display:"inline-flex", alignItems:"center", gap:6, padding:"3px 9px 3px 8px",
      border:`1px solid ${cls==="gem"?"#2f5a3a":cls==="support"?"#5a2f3a":cls==="util"?"#2a3f5a":cls==="flask"?"#4a3a18":"var(--rule)"}`,
      borderRadius:3, fontSize:12,
      color: cls==="gem"?"var(--ok)":cls==="support"?"#ef8a96":cls==="util"?"var(--useful)":cls==="flask"?"#e8c870":"var(--ink)",
      background:"var(--bg-2)"
    }}>
      {name}
      {level && <span className="mono" style={{fontSize:9.5, color:"var(--ink-4)", background:"var(--bg)", padding:"0 4px", borderRadius:8}}>L{level}</span>}
      {count > 1 && <span className="mono" style={{fontSize:9.5, color:"var(--accent)", background:"var(--bg)", padding:"0 4px", borderRadius:8}}>×{count}</span>}
    </span>
  );

  return (
    <div className="app">
      <TitleBar charName="Kyra · Witch 34" />
      <div className="shell">
        <Sidebar active="items" items={NAV_ITEMS} />
        <div className="content">
          <div className="page-header" style={{display:"flex", alignItems:"flex-end", justifyContent:"space-between"}}>
            <div>
              <h1>Items received</h1>
              <div className="sub">47 items · grouped by category. <span className="mono muted" style={{marginLeft:6}}>!gems · !main gems · !support gems · !utility gems · !usable gems</span></div>
            </div>
            <div className="seg">
              <div className="opt active">alphabetical</div>
              <div className="opt">by level</div>
            </div>
          </div>

          <div style={{padding:"18px 24px", flex:1, overflow:"auto"}}>
            {/* Passive points bar */}
            <div style={{display:"flex", alignItems:"center", gap:10, padding:"10px 14px", border:"1px solid var(--rule)", borderRadius:4, background:"var(--panel)", marginBottom:18}}>
              <div style={{width:24, height:24, borderRadius:"50%", background:"color-mix(in oklch, var(--accent) 20%, transparent)", color:"var(--accent)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:14, fontFamily:"var(--display)"}}>✦</div>
              <span className="mono" style={{fontSize:10.5, letterSpacing:".1em", textTransform:"uppercase", color:"var(--ink-3)"}}>Passive points</span>
              <span style={{fontFamily:"var(--display)", fontSize:18, color:"var(--accent)"}}>22</span>
              <span className="muted" style={{fontSize:11.5}}>received · 42 used · 20 available</span>
              <div className="spacer"/>
              <span className="mono muted" style={{fontSize:10}}>!passives</span>
            </div>

            <Section title="Skill gems (main)" count="6 received">
              <Tag name="Frostbolt" cls="gem" level={28}/>
              <Tag name="Cold Snap" cls="gem" level={16}/>
              <Tag name="Arc" cls="gem" level={12}/>
              <Tag name="Ice Nova" cls="gem" level={28}/>
              <Tag name="Freezing Pulse" cls="gem" level={1}/>
              <Tag name="Vaal Cold Snap" cls="gem" level={68}/>
            </Section>

            <Section title="Support gems" count="5 received">
              <Tag name="Added Cold Damage" cls="support" level={8}/>
              <Tag name="Elemental Proliferation" cls="support" level={18}/>
              <Tag name="Hypothermia" cls="support" level={38}/>
              <Tag name="Controlled Destruction" cls="support" level={18}/>
              <Tag name="Greater Multiple Projectiles" cls="support" level={38}/>
            </Section>

            <Section title="Utility gems" count="3 received">
              <Tag name="Flame Dash" cls="util" level={10}/>
              <Tag name="Frost Wall" cls="util" level={34}/>
              <Tag name="Frostblink" cls="util" level={10}/>
            </Section>

            <Section title="Classes & ascendancies" count="2 of 30">
              <Tag name="Witch" cls="flask"/>
              <Tag name="Occultist" cls="flask"/>
            </Section>

            <Section title="Flasks" count="3 received">
              <Tag name="Progressive Flask Unlock" count={3}/>
            </Section>

            <Section title="Progression" count="8 items">
              <Tag name="Progressive Weapon" count={2}/>
              <Tag name="Progressive Body Armour" count={3}/>
              <Tag name="Progressive Helmet" count={2}/>
              <Tag name="Progressive Gloves" count={2}/>
              <Tag name="Progressive max links - BodyArmour" count={4}/>
              <Tag name="Progressive max links - Weapon" count={3}/>
            </Section>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============ GOAL PAGE ============
const GoalScreen = () => (
  <div className="app">
    <TitleBar charName="Kyra · Witch 34" />
    <div className="shell">
      <Sidebar active="goal" items={NAV_ITEMS} />
      <div className="content">
        <div className="page-header">
          <h1>Goal · Defeat 3 bosses</h1>
          <div className="sub">Mirror of <span className="mono">!goal</span>. This slot wins when all 3 guardians are defeated.</div>
        </div>
        <div style={{padding:"24px 28px", flex:1, overflow:"auto"}}>
          <div style={{display:"grid", gridTemplateColumns:"repeat(3, 1fr)", gap:16}}>
            {[
              {name:"Hydra", tier:"Guardian", done:true, when:"2h ago"},
              {name:"Minotaur", tier:"Guardian", done:false},
              {name:"Chimera", tier:"Guardian", done:false},
            ].map(b => (
              <div key={b.name} className="card" style={{padding:"20px 22px", display:"flex", flexDirection:"column", gap:10, borderColor: b.done ? "color-mix(in oklch, var(--ok) 40%, var(--rule))" : "var(--rule)", background: b.done ? "color-mix(in oklch, var(--ok) 6%, var(--panel))" : "var(--panel)"}}>
                <div style={{display:"flex", alignItems:"center", gap:10}}>
                  <div style={{width:40, height:40, borderRadius:"50%", border:`1.5px solid ${b.done ? "var(--ok)" : "var(--rule-2)"}`, color: b.done ? "var(--ok)" : "var(--ink-4)", display:"flex", alignItems:"center", justifyContent:"center"}}>
                    {b.done ? Ico.check({width:18, height:18}) : Ico.skull({width:20, height:20})}
                  </div>
                  <div>
                    <div style={{fontFamily:"var(--display)", fontSize:24, lineHeight:1}}>{b.name}</div>
                    <div className="mono muted" style={{fontSize:10.5, letterSpacing:".08em", textTransform:"uppercase", marginTop:4}}>{b.tier}</div>
                  </div>
                </div>
                <div style={{fontSize:12, color: b.done ? "var(--ok)" : "var(--ink-3)"}}>
                  {b.done ? `✓ Defeated · ${b.when}` : "Pending · attempt any time"}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  </div>
);

// ============ CHAT (fullscreen) ============
const ChatScreen = () => (
  <div className="app">
    <TitleBar charName="Kyra · Witch 34" />
    <div className="shell">
      <Sidebar active="chat" items={NAV_ITEMS} />
      <div className="content" style={{display:"flex", flexDirection:"column"}}>
        <div className="page-header" style={{display:"flex", alignItems:"flex-end", justifyContent:"space-between"}}>
          <div>
            <h1>Chat</h1>
            <div className="sub">Full history of the multiworld. Filter by kind, search by sender or item.</div>
          </div>
          <div style={{display:"flex", gap:8, alignItems:"center"}}>
            <input className="input" placeholder="search chat…" style={{width:200}}/>
            <div className="seg">
              <div className="opt active">all</div>
              <div className="opt">items</div>
              <div className="opt">hints</div>
              <div className="opt">chat</div>
              <div className="opt">system</div>
            </div>
          </div>
        </div>
        <div style={{flex:1, overflow:"auto", padding:"12px 28px", fontSize:13}}>
          {/* denser feed with day separators */}
          <div className="mono muted" style={{fontSize:10, textAlign:"center", padding:"10px 0", letterSpacing:".12em"}}>— today · 14:02 connected —</div>
          <ChatLine t="14:02" kind="sys">Connected as "Kyra" · Path of Exile · team 0 · slot 4 of 8</ChatLine>
          <ChatLine t="14:02" kind="sys">Tailing C:\Games\Path of Exile\logs\Client.txt</ChatLine>
          <ChatLine t="14:02" kind="sys">Character "Kyra" validated · filter written (__ap.filter · 312 blocks)</ChatLine>
          <ChatLine t="14:08" who="Nova" whoColor="#c5a4ff" kind="chat">gl out there kyra, big drop coming for you</ChatLine>
          <ChatLine t="14:09" kind="item"><b style={{color:"var(--prog)"}}>Progressive Weapon</b> <span className="muted">from</span> Nova <span className="muted">(Hollow Knight) · Dirtmouth Bench</span></ChatLine>
          <ChatLine t="14:11" kind="item"><b style={{color:"var(--filler)"}}>Scroll of Wisdom ×20</b> <span className="muted">at</span> Coast of the Deep <span className="muted">· act 6</span></ChatLine>
          <ChatLine t="14:14" kind="hint"><b style={{color:"var(--useful)"}}>hint:</b> Progressive Body Armour at <b>Nova</b>'s <span className="muted">Dirtmouth · Bench</span></ChatLine>
          <ChatLine t="14:16" kind="out"><b>→ you</b> !usable gems</ChatLine>
          <ChatLine t="14:16" kind="self"><span className="muted">to you:</span> 6 usable gems · Frostbolt 28, Cold Snap 16, Arc 12, Added Cold 8, Elem Prolif 18, Flame Dash 10</ChatLine>
          <ChatLine t="14:19" kind="item"><b style={{color:"var(--useful)"}}>Added Lightning Damage</b> <span className="muted">from</span> Roose <span className="muted">(Stardew Valley)</span></ChatLine>
          <ChatLine t="14:22" who="Roose" whoColor="#9fd98a" kind="chat">anyone seen a chaos orb ? been grinding yellow maps</ChatLine>
          <ChatLine t="14:23" who="Nova" whoColor="#c5a4ff" kind="chat">check your hints tab roose</ChatLine>
          <ChatLine t="14:24" kind="out"><b>→ you</b> !goal</ChatLine>
          <ChatLine t="14:24" kind="self"><span className="muted">to you:</span> Defeat 3 bosses · ✓ Hydra · ✗ Minotaur · ✗ Chimera</ChatLine>
          <ChatLine t="14:27" kind="item"><b style={{color:"var(--prog)"}}>Progressive max links · BodyArmour</b> <span className="muted">from</span> Kizz <span className="muted">(Celeste)</span></ChatLine>
          <ChatLine t="14:27" who="Kizz" whoColor="#ffb084" kind="chat">linky linky for my favorite witch</ChatLine>
          <ChatLine t="14:29" kind="sys">Death Link received from Roose — ignored (deathlink off)</ChatLine>
          <ChatLine t="14:31" kind="sys">F12 · revalidate — filter regenerated (312 blocks · 18.4 KB)</ChatLine>
          <ChatLine t="14:32" kind="item"><b style={{color:"var(--trap)"}}>Trap · Brittle flasks (60s)</b> <span className="muted">from</span> Nova</ChatLine>
          <ChatLine t="14:34" who="you" whoColor="var(--accent)" kind="chat-self">thanks all — going for Minotaur now</ChatLine>
        </div>
        <div style={{padding:"12px 28px 16px", borderTop:"1px solid var(--rule)", background:"var(--bg-2)"}}>
          <div style={{display:"flex", gap:6, marginBottom:8, flexWrap:"wrap"}}>
            <span className="mono muted" style={{fontSize:10, letterSpacing:".08em", marginRight:4, alignSelf:"center"}}>QUICK</span>
            {["!gear","!gems","!usable gems","!goal","!passives","!links","!flasks","!deathlink"].map(c => (
              <button key={c} className="chip mono">{c}</button>
            ))}
          </div>
          <div style={{display:"flex", alignItems:"center", gap:8, background:"var(--panel-2)", border:"1px solid var(--rule)", borderRadius:4, padding:"9px 14px"}}>
            <span className="mono" style={{color:"var(--accent)", fontSize:13}}>›</span>
            <input className="chat-input mono" placeholder="send to multiworld (plain text) or whisper a command (e.g. !gear)"/>
            <span className="mono muted" style={{fontSize:10}}>enter · ↑ history</span>
          </div>
        </div>
      </div>
    </div>
  </div>
);

// ============ SETTINGS — includes every CLI / slash command ============
const SettingsScreen = () => {
  const Section = ({title, id, children}) => (
    <div className="card" id={id}>
      <h3>{title}</h3>
      <div style={{display:"flex", flexDirection:"column"}}>{children}</div>
    </div>
  );
  const Row = ({label, cmd, hint, children}) => (
    <div style={{display:"grid", gridTemplateColumns:"220px 1fr", gap:18, alignItems:"center", padding:"10px 0", borderBottom:"1px solid var(--rule)"}}>
      <div>
        <div style={{fontSize:12.5}}>{label}</div>
        {cmd && <div className="mono" style={{fontSize:10, color:"var(--ink-4)", marginTop:2, letterSpacing:".02em"}}>{cmd}</div>}
        {hint && <div className="muted" style={{fontSize:11, marginTop:3}}>{hint}</div>}
      </div>
      <div>{children}</div>
    </div>
  );

  return (
    <div className="app">
      <TitleBar charName="Kyra · Witch 34" />
      <div className="shell">
        <Sidebar active="settings" items={NAV_ITEMS} />
        <div className="content">
          <div className="page-header" style={{display:"flex", alignItems:"flex-end", justifyContent:"space-between"}}>
            <div>
              <h1>Settings</h1>
              <div className="sub">Every <span className="mono" style={{color:"var(--accent)"}}>/command</span> from the Python client, as a real control. Per-world settings keyed by seed + username.</div>
            </div>
            <div style={{display:"flex", gap:8}}>
              <button className="btn sm">export config</button>
              <button className="btn sm">reset to defaults</button>
            </div>
          </div>

          <div style={{display:"flex", flex:1, minHeight:0}}>
            {/* anchor nav */}
            <aside style={{width:200, padding:"22px 8px 22px 22px", borderRight:"1px solid var(--rule)", flexShrink:0}}>
              <div className="mono" style={{fontSize:10, letterSpacing:".1em", textTransform:"uppercase", color:"var(--ink-4)", marginBottom:8}}>jump to</div>
              {[
                ["Connection","connection"],
                ["Paths","paths"],
                ["Character","character"],
                ["Loot filter","filter"],
                ["TTS","tts"],
                ["Client behavior","client"],
                ["Hotkeys","hotkeys"],
                ["Advanced CLI","advanced"],
              ].map(([l,id]) => (
                <div key={id} style={{padding:"5px 10px", fontSize:12, color:"var(--ink-2)", borderRadius:3, cursor:"pointer"}}>{l}</div>
              ))}
            </aside>

            <div style={{flex:1, overflow:"auto", padding:"22px 26px", display:"flex", flexDirection:"column", gap:16}}>

              <Section title="Connection" id="connection">
                <Row label="Server" cmd="archipelago URL · host:port">
                  <input className="input mono" defaultValue="archipelago.gg:38281" style={{maxWidth:320}}/>
                </Row>
                <Row label="Slot name">
                  <input className="input" defaultValue="Kyra" style={{maxWidth:200}}/>
                </Row>
                <Row label="Password">
                  <input className="input" type="password" defaultValue="•••••••" style={{maxWidth:200}}/>
                </Row>
                <Row label="Auto-reconnect" hint="Keep trying if the server drops.">
                  <span className="toggle on"><span className="knob"/></span>
                </Row>
              </Section>

              <Section title="Paths" id="paths">
                <Row label="Client.txt" cmd="/client · /set_client_text_path &lt;path&gt;" hint="Directory is also accepted — appends Client.txt.">
                  <div style={{display:"flex", gap:8}}>
                    <input className="input mono" defaultValue="C:\Games\Path of Exile\logs\Client.txt" style={{flex:1}}/>
                    <button className="btn">{Ico.folder()} browse</button>
                  </div>
                </Row>
                <Row label="PoE documents folder" cmd="/poe_documents_directory &lt;path&gt;" hint="Empty arg resets to OS default.">
                  <div style={{display:"flex", gap:8}}>
                    <input className="input mono" defaultValue="C:\Users\kyra\Documents\My Games\Path of Exile\" style={{flex:1}}/>
                    <button className="btn">{Ico.folder()} browse</button>
                  </div>
                </Row>
              </Section>

              <Section title="Character" id="character">
                <Row label="Character name" cmd="/char &lt;name&gt; · /char_name &lt;name&gt;" hint="Skip the in-game !ap char handshake by setting directly.">
                  <div style={{display:"flex", gap:8}}>
                    <input className="input" defaultValue="Kyra" style={{maxWidth:200}}/>
                    <button className="btn sm">run !ap char instead</button>
                  </div>
                </Row>
                <Row label="GGG OAuth" cmd="/poe_auth" hint="Required for character + stash API reads.">
                  <div className="row">
                    <span className="pill ok"><span className="dot"/>Kyra_exile · 47d left</span>
                    <button className="btn sm">re-auth</button>
                    <button className="btn sm">sign out</button>
                  </div>
                </Row>
              </Section>

              <Section title="Loot filter" id="filter">
                <Row label="Display mode" cmd="/loot_filter_display 0|1|2" hint="0 show · 1 hide · 2 randomize">
                  <div className="seg">
                    <div className="opt active">show classification</div>
                    <div className="opt">hide classification</div>
                    <div className="opt">randomize style</div>
                  </div>
                </Row>
                <Row label="Drop sound" cmd="/loot_filter_sounds 0|1|2" hint="0 none · 1 TTS · 2 jingles">
                  <div className="seg">
                    <div className="opt">none</div>
                    <div className="opt">TTS</div>
                    <div className="opt active">jingles</div>
                  </div>
                </Row>
                <Row label="Base filter to chain" cmd="/filter &lt;name.filter&gt; · /base_item_filter" hint="Any .filter in your PoE docs folder. __ap and __invalid are reserved.">
                  <input className="input mono" defaultValue="NeverSink_v9.2.0_Strict.filter" style={{maxWidth:420}}/>
                </Row>
              </Section>

              <Section title="TTS" id="tts">
                <Row label="TTS generation" cmd="/enable_tts [on|off]">
                  <span className="toggle"><span className="knob"/></span>
                </Row>
                <Row label="TTS speed" cmd="/tts_speed &lt;wpm&gt;" hint="Words per minute, default 250.">
                  <div className="row" style={{gap:12}}>
                    <input type="range" min="50" max="500" defaultValue="250" style={{flex:1, maxWidth:300}}/>
                    <span className="mono" style={{fontSize:12}}>250 wpm</span>
                    <button className="btn sm">preview</button>
                  </div>
                </Row>
                <Row label="Pre-generate TTS" cmd="/generate_tts" hint="Force generation for all remaining missing locations.">
                  <button className="btn">run now</button>
                </Row>
              </Section>

              <Section title="Client behavior" id="client">
                <Row label="Start / stop loop" cmd="/start · /start_poe · /stop" hint="Validates character, writes filter, begins tailing.">
                  <div className="row">
                    <button className="btn primary">start</button>
                    <button className="btn">stop</button>
                    <span className="pill ok" style={{marginLeft:6}}><span className="dot"/>running</span>
                  </div>
                </Row>
                <Row label="Per-item whispers" cmd="/whisper_updates [on|off] · !whisper updates">
                  <span className="toggle on"><span className="knob"/></span>
                </Row>
                <Row label="Death Link" cmd="/deathlink · !deathlink" hint="Die here, die everywhere.">
                  <span className="toggle"><span className="knob"/></span>
                </Row>
                <Row label="Minimize to tray on close">
                  <span className="toggle on"><span className="knob"/></span>
                </Row>
                <Row label="Launch at login">
                  <span className="toggle"><span className="knob"/></span>
                </Row>
              </Section>

              <Section title="Hotkeys" id="hotkeys">
                <Row label="Re-validate character" hint="Re-fetches GGG character + regenerates filter.">
                  <span className="mono" style={{background:"var(--bg-3)", padding:"3px 10px", borderRadius:3, fontSize:11.5}}>F12</span>
                </Row>
                <Row label="Toggle dashboard window">
                  <span className="mono" style={{background:"var(--bg-3)", padding:"3px 10px", borderRadius:3, fontSize:11.5}}>Ctrl+Shift+A</span>
                </Row>
              </Section>

              <Section title="Advanced · CLI console" id="advanced">
                <div style={{fontSize:12, color:"var(--ink-2)", marginBottom:10}}>
                  Every <span className="mono" style={{color:"var(--accent)"}}>/command</span> from the Python client is also runnable here — useful for scripts, debugging, or if a setting you're looking for isn't exposed yet.
                </div>
                <div style={{background:"var(--bg)", border:"1px solid var(--rule)", borderRadius:4, padding:"12px 14px", fontFamily:"var(--mono)", fontSize:11.5}}>
                  <div style={{color:"var(--ink-4)"}}>[14:31] &gt; /start</div>
                  <div style={{color:"var(--ok)"}}>[14:31] ✓ client loop started · tailing Client.txt · filter written (312 blocks)</div>
                  <div style={{color:"var(--ink-4)"}}>[14:34] &gt; /tts_speed 275</div>
                  <div style={{color:"var(--ok)"}}>[14:34] ✓ tts speed = 275 wpm</div>
                  <div style={{display:"flex", alignItems:"center", gap:8, marginTop:6}}>
                    <span style={{color:"var(--accent)"}}>›</span>
                    <input className="chat-input" placeholder="/command [args]" style={{flex:1}}/>
                  </div>
                </div>
              </Section>

            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============ TRAY ============
const TrayScreen = () => (
  <div className="app" style={{background:"transparent", boxShadow:"none", border:"none", overflow:"visible"}}>
    <div style={{width:"100%", height:"100%", background:"radial-gradient(circle at 80% 20%, #2a251f 0%, #121017 70%)", position:"relative"}}>
      <div style={{position:"absolute", bottom:0, left:0, right:0, height:32, background:"#0d0b09", borderTop:"1px solid #1c1915", display:"flex", alignItems:"center", padding:"0 12px", gap:14}}>
        <div style={{fontFamily:"var(--mono)", fontSize:10, color:"var(--ink-4)"}}>— system tray —</div>
        <div className="spacer"/>
        <div style={{display:"flex", gap:14, alignItems:"center"}}>
          <div className="dim" style={{fontSize:11}}>◊</div>
          <div className="dim" style={{fontSize:11}}>⌨</div>
          <div className="dim" style={{fontSize:11}}>♪</div>
          <div style={{width:18, height:18, borderRadius:3, background:"var(--accent)", display:"flex", alignItems:"center", justifyContent:"center", color:"#1a1208", fontFamily:"var(--display)", fontSize:12, fontWeight:600, boxShadow:"0 0 8px color-mix(in oklch, var(--accent) 50%, transparent)"}}>A</div>
          <div style={{fontFamily:"var(--mono)", fontSize:11, color:"var(--ink-3)"}}>14:34</div>
        </div>
      </div>
      <div style={{position:"absolute", bottom:44, right:16, width:300, background:"var(--bg-2)", border:"1px solid var(--rule-2)", borderRadius:6, boxShadow:"0 18px 44px rgba(0,0,0,.6)", padding:"8px 0"}}>
        <div style={{padding:"12px 16px 10px", borderBottom:"1px solid var(--rule)"}}>
          <div style={{display:"flex", alignItems:"center", gap:10, marginBottom:8}}>
            <div style={{width:26, height:26, borderRadius:4, background:"var(--accent)", color:"#1a1208", fontFamily:"var(--display)", fontWeight:600, fontSize:15, display:"flex", alignItems:"center", justifyContent:"center"}}>A</div>
            <div>
              <div style={{fontSize:12.5, fontWeight:500}}>Archipelago · PoE</div>
              <div className="muted mono" style={{fontSize:10}}>v0.4.1</div>
            </div>
            <div className="spacer"/>
            <span className="pill ok"><span className="dot"/>live</span>
          </div>
          <div className="kv" style={{gridTemplateColumns:"56px 1fr", fontSize:11.5}}>
            <dt>slot</dt><dd>Kyra · 4/8</dd>
            <dt>zone</dt><dd>The Crypt Lv 2</dd>
            <dt>goal</dt><dd>1 of 3 bosses</dd>
          </div>
        </div>
        {[
          ["dashboard", "Open dashboard", "Ctrl+Shift+A"],
          ["target", "Re-validate character", "F12"],
          ["filter", "Regenerate filter", null],
          ["log",    "Open chat", null],
        ].map(([ic,l,k]) => (
          <div key={l} style={{display:"flex", alignItems:"center", gap:10, padding:"9px 16px", fontSize:12.5, cursor:"pointer"}}>
            <span style={{color:"var(--ink-3)"}}>{Ico[ic] && Ico[ic]()}</span>
            <span>{l}</span>
            <div className="spacer"/>
            {k && <span className="mono muted" style={{fontSize:10}}>{k}</span>}
          </div>
        ))}
        <div style={{height:1, background:"var(--rule)", margin:"4px 0"}}/>
        <div style={{padding:"9px 16px", fontSize:12.5, display:"flex", alignItems:"center", gap:10}}>
          <span style={{color:"var(--ink-3)"}}>{Ico.skull()}</span>Death link <span className="spacer"/><span className="toggle"><span className="knob"/></span>
        </div>
        <div style={{padding:"9px 16px", fontSize:12.5, display:"flex", alignItems:"center", gap:10}}>
          <span style={{color:"var(--ink-3)"}}>{Ico.sound()}</span>Whisper updates <span className="spacer"/><span className="toggle on"><span className="knob"/></span>
        </div>
        <div style={{height:1, background:"var(--rule)", margin:"4px 0"}}/>
        <div style={{padding:"9px 16px", fontSize:12.5, color:"var(--ink-2)", cursor:"pointer"}}>Disconnect</div>
        <div style={{padding:"9px 16px", fontSize:12.5, color:"var(--err)", cursor:"pointer"}}>Quit</div>
      </div>
      <div style={{position:"absolute", bottom:280, right:16, width:300, background:"var(--bg-2)", border:"1px solid var(--rule-2)", borderLeft:"3px solid var(--accent)", borderRadius:5, padding:"12px 16px", boxShadow:"0 8px 24px rgba(0,0,0,.5)"}}>
        <div className="mono" style={{fontSize:10, color:"var(--accent)", letterSpacing:".08em", marginBottom:4, textTransform:"uppercase"}}>Received · Progression</div>
        <div style={{fontSize:13, fontWeight:500, marginBottom:2}}>Progressive Weapon</div>
        <div className="muted mono" style={{fontSize:10.5}}>from Nova · Hollow Knight · 4s ago</div>
      </div>
    </div>
  </div>
);

Object.assign(window, { GearScreen, ItemsScreen, GoalScreen, ChatScreen, SettingsScreen, TrayScreen, ChatLine });
