// Dashboard — split symmetry layout
// Left: commands as primary action surface, each with persisted "last response" tile
// Right: multiworld chat (outgoing + incoming + text input)
// Top strip: compact char/connection/goal status
// Bottom: condensed items + client.txt (secondary, small)

const StatusStrip = () => (
  <div style={{
    display:"grid",
    gridTemplateColumns:"auto 1fr auto auto auto",
    gap: 18,
    alignItems:"center",
    padding:"12px 22px",
    background:"var(--bg-2)",
    borderBottom:"1px solid var(--rule)",
  }}>
    <span className="pill ok" style={{padding:"3px 10px"}}><span className="dot"/>connected · archipelago.gg:38281</span>
    <div style={{display:"flex", alignItems:"baseline", gap:10}}>
      <span style={{fontFamily:"var(--display)", fontSize:20, lineHeight:1, letterSpacing:"-.005em"}}>Kyra</span>
      <span className="mono muted" style={{fontSize:11}}>Witch · lv 34 · Act 6 · The Crypt</span>
    </div>
    <div style={{display:"flex", gap:18, alignItems:"center"}}>
      <div style={{display:"flex", flexDirection:"column", alignItems:"flex-end"}}>
        <span className="mono" style={{fontSize:10.5, color:"var(--ink-3)", letterSpacing:".08em", textTransform:"uppercase"}}>Goal</span>
        <span style={{fontFamily:"var(--display)", fontSize:14, marginTop:1}}>Defeat 3 bosses · 1/3</span>
      </div>
      <div style={{display:"flex", flexDirection:"column", alignItems:"flex-end"}}>
        <span className="mono" style={{fontSize:10.5, color:"var(--ink-3)", letterSpacing:".08em", textTransform:"uppercase"}}>Passives</span>
        <span style={{fontFamily:"var(--display)", fontSize:14, marginTop:1}}><span style={{color:"var(--accent)"}}>42</span> <span className="muted">/ 64 used</span></span>
      </div>
    </div>
    <div style={{width:1, height:28, background:"var(--rule)"}}/>
    <div style={{display:"flex", gap:6}}>
      <button className="btn sm">F12 revalidate</button>
      <button className="btn sm">regenerate filter</button>
    </div>
  </div>
);

// One command button with persistent last-response tile
const CmdTile = ({cmd, label, resp, accent, warn}) => (
  <button className={`cmd-tile ${warn ? "warn" : ""}`}>
    <div style={{display:"flex", alignItems:"baseline", justifyContent:"space-between", gap:8}}>
      <span className="mono cmd-name" style={{color: warn ? "var(--err)" : accent || "var(--accent)"}}>{cmd}</span>
      <span className="cmd-label">{label}</span>
    </div>
    {resp && <div className="cmd-resp">{resp}</div>}
  </button>
);

const CmdGroup = ({title, note, children}) => (
  <div>
    <div style={{display:"flex", alignItems:"baseline", justifyContent:"space-between", marginBottom:8}}>
      <div className="mono" style={{fontSize:10.5, letterSpacing:".1em", textTransform:"uppercase", color:"var(--ink-3)"}}>{title}</div>
      {note && <div className="mono muted" style={{fontSize:10}}>{note}</div>}
    </div>
    <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:6}}>{children}</div>
  </div>
);

// Chat line — one row in the multiworld feed
const ChatLine = ({t, who, whoColor, kind, children}) => (
  <div className="chat-line">
    <span className="chat-t mono">{t}</span>
    {who && <span className="chat-who" style={{color: whoColor}}>{who}</span>}
    <span className={`chat-body ${kind||""}`}>{children}</span>
  </div>
);

const DashboardScreen = () => {
  return (
    <div className="app">
      <TitleBar charName="Kyra · Witch 34" />
      <div className="shell">
        <Sidebar active="dashboard" items={NAV_ITEMS} />
        <div className="content" style={{display:"flex", flexDirection:"column"}}>
          <StatusStrip/>

          {/* SPLIT SYMMETRY: commands | chat */}
          <div style={{flex:1, display:"grid", gridTemplateColumns:"1fr 1fr", minHeight:0}}>
            {/* LEFT: COMMANDS */}
            <div style={{padding:"18px 20px 14px 22px", borderRight:"1px solid var(--rule)", overflow:"auto", display:"flex", flexDirection:"column", gap: 18}}>
              <div style={{display:"flex", alignItems:"baseline", justifyContent:"space-between"}}>
                <h2 style={{fontFamily:"var(--display)", fontWeight:400, fontSize:22, lineHeight:1, letterSpacing:"-.005em"}}>Commands</h2>
                <span className="mono muted" style={{fontSize:11}}>click to run · last response pinned</span>
              </div>

              <CmdGroup title="Loadout" note="all gear/gems queries">
                <CmdTile cmd="!gear" label="gear progress" resp={<><span className="muted">7 of 10 slots · </span>weapon 2/3 · body 3/3</>}/>
                <CmdTile cmd="!gems" label="all gems" resp={<><span className="muted">14 received · </span>6 main · 5 support · 3 util</>}/>
                <CmdTile cmd="!usable gems" label="usable now" resp={<><span style={{color:"var(--ok)"}}>6 usable</span> <span className="muted">at lv 34</span></>}/>
                <CmdTile cmd="!main gems"    label="main skill gems"    resp="Frostbolt, Cold Snap, Arc, +3"/>
                <CmdTile cmd="!support gems" label="support gems"       resp="Added Cold, Elem Prolif, +3"/>
                <CmdTile cmd="!utility gems" label="utility gems"       resp="Flame Dash, Frostblink, +1"/>
                <CmdTile cmd="!weapons" label="weapon slots"            resp="2/3 · Normal, Magic"/>
                <CmdTile cmd="!armor"   label="armor slots"             resp="Body 3/3 · Helm 0/1 · Gloves 2/3"/>
                <CmdTile cmd="!links"   label="max links per slot"      resp="body 4L · helm 3L · weapon 4L"/>
                <CmdTile cmd="!flasks"  label="flask unlocks"           resp="3 received · 2 usable"/>
              </CmdGroup>

              <CmdGroup title="Progress">
                <CmdTile cmd="!ascendancy" label="class / ascendancies" resp={<><span className="muted">Witch unlocked · </span>Occultist</>}/>
                <CmdTile cmd="!passives"   label="passive points"       resp={<><span style={{color:"var(--accent)"}}>42</span><span className="muted"> used / </span><span>22</span><span className="muted"> available</span></>}/>
                <CmdTile cmd="!goal"       label="current goal"         resp="Defeat 3 bosses · 1/3 ✓ Hydra"/>
              </CmdGroup>

              <CmdGroup title="Toggles">
                <CmdTile cmd="!deathlink"        label="death link"            accent="var(--err)" resp={<><span style={{color:"var(--ink-4)"}}>currently </span><span>off</span></>}/>
                <CmdTile cmd="!whisper updates"  label="per-item whispers"     resp={<><span style={{color:"var(--ink-4)"}}>currently </span><span style={{color:"var(--ok)"}}>on</span></>}/>
                <CmdTile cmd="!help"             label="print command list"    resp="23 commands available"/>
                <CmdTile cmd="!ap char"          label="re-handshake char"     warn resp={<span style={{color:"var(--err)"}}>runs the name capture flow</span>}/>
              </CmdGroup>
            </div>

            {/* RIGHT: CHAT */}
            <div style={{display:"flex", flexDirection:"column", minHeight:0, background:"var(--bg-2)"}}>
              <div style={{padding:"14px 20px 10px", display:"flex", alignItems:"baseline", justifyContent:"space-between", borderBottom:"1px solid var(--rule)"}}>
                <h2 style={{fontFamily:"var(--display)", fontWeight:400, fontSize:22, lineHeight:1, letterSpacing:"-.005em"}}>Multiworld chat</h2>
                <div style={{display:"flex", gap:6, alignItems:"center"}}>
                  <span className="mono muted" style={{fontSize:10.5}}>filter</span>
                  <div className="seg" style={{fontSize:10.5}}>
                    <div className="opt active">all</div>
                    <div className="opt">items</div>
                    <div className="opt">hints</div>
                    <div className="opt">chat</div>
                  </div>
                </div>
              </div>

              <div style={{flex:1, overflow:"auto", padding:"12px 20px", display:"flex", flexDirection:"column", gap:1, fontSize:12.5}}>
                <ChatLine t="14:02" kind="sys">Connected as "Kyra" · Path of Exile · 4 of 8</ChatLine>
                <ChatLine t="14:02" kind="sys">Tailing Client.txt · writing __ap.filter</ChatLine>
                <ChatLine t="14:08" who="Nova" whoColor="#c5a4ff" kind="chat">gl out there, big drop coming for you</ChatLine>
                <ChatLine t="14:09" kind="item"><b style={{color:"var(--prog)"}}>Progressive Weapon</b> <span className="muted">from</span> Nova <span className="muted">(Hollow Knight)</span></ChatLine>
                <ChatLine t="14:11" kind="item"><b style={{color:"var(--filler)"}}>Scroll of Wisdom ×20</b> <span className="muted">at</span> Coast of the Deep <span className="muted">(act 6)</span></ChatLine>
                <ChatLine t="14:14" kind="hint"><b style={{color:"var(--useful)"}}>hint:</b> Progressive Body Armour is at <span style={{color:"#ffc58a"}}>Nova</span>'s <span className="muted">Dirtmouth · Bench</span></ChatLine>
                <ChatLine t="14:16" kind="out"><b>→ you</b> !usable gems</ChatLine>
                <ChatLine t="14:16" kind="self"><span className="muted">to you:</span> 6 usable gems · Frostbolt 28, Cold Snap 16, Arc 12, Added Cold 8, Elem Prolif 18, Flame Dash 10</ChatLine>
                <ChatLine t="14:19" kind="item"><b style={{color:"var(--useful)"}}>Added Lightning Damage</b> <span className="muted">from</span> Roose <span className="muted">(Stardew)</span></ChatLine>
                <ChatLine t="14:22" who="Roose" whoColor="#9fd98a" kind="chat">anyone seen the chaos orb ? been grinding maps</ChatLine>
                <ChatLine t="14:23" who="Nova" whoColor="#c5a4ff" kind="chat">check your hints tab</ChatLine>
                <ChatLine t="14:24" kind="out"><b>→ you</b> !goal</ChatLine>
                <ChatLine t="14:24" kind="self"><span className="muted">to you:</span> Defeat 3 bosses · ✓ Hydra · ✗ Minotaur · ✗ Chimera</ChatLine>
                <ChatLine t="14:27" kind="item"><b style={{color:"var(--prog)"}}>Progressive max links · BodyArmour</b> <span className="muted">from</span> Kizz <span className="muted">(Celeste)</span></ChatLine>
                <ChatLine t="14:31" kind="sys">F12 · revalidate — filter regenerated (312 blocks · 18.4 KB)</ChatLine>
                <ChatLine t="14:32" kind="item"><b style={{color:"var(--trap)"}}>Trap · Brittle flasks (60s)</b> <span className="muted">from</span> Nova</ChatLine>
                <ChatLine t="14:34" who="you" whoColor="var(--accent)" kind="chat-self">thanks all, going for Minotaur now</ChatLine>
              </div>

              {/* Composer */}
              <div style={{padding:"10px 16px 14px", borderTop:"1px solid var(--rule)", background:"var(--bg-2)"}}>
                <div style={{display:"flex", gap:6, marginBottom:8, flexWrap:"wrap"}}>
                  <span className="mono muted" style={{fontSize:10, letterSpacing:".08em", marginRight:4, alignSelf:"center"}}>QUICK</span>
                  {["!gear","!usable gems","!goal","!passives","!deathlink"].map(c => (
                    <button key={c} className="chip mono">{c}</button>
                  ))}
                </div>
                <div style={{display:"flex", alignItems:"center", gap:8, background:"var(--panel-2)", border:"1px solid var(--rule)", borderRadius:4, padding:"8px 12px"}}>
                  <span className="mono" style={{color:"var(--accent)", fontSize:13}}>›</span>
                  <input className="chat-input mono" placeholder="send to multiworld or whisper yourself (e.g. !gear)"/>
                  <span className="mono muted" style={{fontSize:10}}>enter</span>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom footer: collapsed items / client.txt tail */}
          <div style={{borderTop:"1px solid var(--rule)", background:"var(--bg)", padding:"8px 22px", display:"flex", alignItems:"center", gap:16, fontSize:11}}>
            <span className="mono" style={{fontSize:10, letterSpacing:".08em", color:"var(--ink-3)"}}>CLIENT.TXT</span>
            <span className="mono muted" style={{whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis", flex:1}}>
              [14:34] @From Kyra: !usable gems · [14:34] You have entered The Crypt Level 2 · [14:34] : Cold Snap (Level 16) has been added to your inventory
            </span>
            <span className="pill ok" style={{padding:"1px 8px", fontSize:10}}><span className="dot"/>tailing</span>
            <span className="mono muted" style={{fontSize:10}}>47 items · 3 hints · 312 locs</span>
          </div>
        </div>
      </div>
    </div>
  );
};

window.DashboardScreen = DashboardScreen;
