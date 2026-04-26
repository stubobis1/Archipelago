// Screen: Onboarding wizard — first-run setup flow
// Steps: paths -> OAuth -> AP connect -> character handshake -> ready

const OnboardingScreen = () => {
  const steps = [
    { n: 1, label: "Paths",     state: "done" },
    { n: 2, label: "GGG OAuth", state: "done" },
    { n: 3, label: "Connect",   state: "active" },
    { n: 4, label: "Character", state: "idle" },
    { n: 5, label: "Ready",     state: "idle" },
  ];

  return (
    <div className="app">
      <TitleBar status="warn" charName={null} />
      <div style={{flex:1, display:"flex", overflow:"hidden"}}>
        {/* Left: stepper */}
        <aside style={{width: 260, background:"var(--bg-2)", borderRight:"1px solid var(--rule)", padding:"32px 28px", display:"flex", flexDirection:"column"}}>
          <div style={{fontFamily:"var(--display)", fontSize:24, lineHeight:1, marginBottom:4}}>First run</div>
          <div className="mono muted" style={{fontSize:10.5, letterSpacing:".08em", textTransform:"uppercase", marginBottom:32}}>setup · 3 of 5</div>
          <div style={{display:"flex", flexDirection:"column", gap:2}}>
            {steps.map((s, i) => (
              <div key={s.n} style={{display:"flex", alignItems:"center", gap:12, padding:"10px 0", position:"relative"}}>
                <div style={{
                  width:22, height:22, borderRadius:"50%",
                  border: `1px solid ${s.state==="done" ? "var(--accent)" : s.state==="active" ? "var(--accent)" : "var(--rule-2)"}`,
                  background: s.state==="done" ? "var(--accent)" : s.state==="active" ? "transparent" : "transparent",
                  color: s.state==="done" ? "#1a1208" : s.state==="active" ? "var(--accent)" : "var(--ink-3)",
                  display:"flex", alignItems:"center", justifyContent:"center",
                  fontFamily:"var(--mono)", fontSize:10, fontWeight:600
                }}>
                  {s.state === "done" ? Ico.check() : s.n}
                </div>
                <span style={{
                  fontSize: 13,
                  color: s.state==="active" ? "var(--ink)" : s.state==="done" ? "var(--ink-2)" : "var(--ink-3)",
                  fontWeight: s.state==="active" ? 500 : 400
                }}>{s.label}</span>
                {i < steps.length-1 && <div style={{position:"absolute", left:10, top:32, width:1, height:14, background: s.state==="done" ? "var(--accent)" : "var(--rule-2)"}}/>}
              </div>
            ))}
          </div>
          <div className="spacer"/>
          <div className="mono muted" style={{fontSize:10, lineHeight:1.7}}>
            You can change any of this later from Settings.
          </div>
        </aside>

        {/* Right: current step content */}
        <div style={{flex:1, overflow:"auto", padding:"48px 56px"}}>
          <div className="mono" style={{fontSize:10.5, letterSpacing:".1em", color:"var(--accent)", textTransform:"uppercase", marginBottom:10}}>Step 3</div>
          <h1 style={{fontFamily:"var(--display)", fontWeight:400, fontSize:40, lineHeight:1, letterSpacing:"-.01em", margin:"0 0 14px"}}>Connect to your Archipelago server.</h1>
          <p style={{color:"var(--ink-2)", fontSize:14, maxWidth:560, marginBottom:36, lineHeight:1.55}}>
            Paste the server address from your host. If you generated locally, that's usually <span className="mono" style={{background:"var(--bg-3)", padding:"1px 6px", borderRadius:3, fontSize:12}}>archipelago.gg:&lt;port&gt;</span>. Your slot name is what you entered in your YAML.
          </p>

          <div style={{maxWidth: 640, display:"grid", gap:20}}>
            <div>
              <label className="label">Server address</label>
              <input className="input mono" defaultValue="archipelago.gg:38281"/>
            </div>
            <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:16}}>
              <div>
                <label className="label">Slot name</label>
                <input className="input" defaultValue="Kyra"/>
              </div>
              <div>
                <label className="label">Password <span className="muted mono" style={{fontSize:10, textTransform:"none", letterSpacing:0}}>optional</span></label>
                <input className="input" type="password" defaultValue="•••••••"/>
              </div>
            </div>

            <div style={{background:"var(--panel)", border:"1px solid var(--rule)", borderRadius:5, padding:"14px 18px", display:"flex", alignItems:"center", gap:12}}>
              <span className="pill ok"><span className="dot"/>checking slot…</span>
              <span className="muted mono" style={{fontSize:11.5}}>reachable · protocol v0.5.1</span>
            </div>

            <div style={{display:"flex", gap:10, marginTop:10}}>
              <button className="btn ghost">← back</button>
              <div className="spacer"/>
              <button className="btn">skip</button>
              <button className="btn primary">Connect</button>
            </div>
          </div>

          {/* Prior step summary */}
          <div style={{marginTop:56, paddingTop:28, borderTop:"1px solid var(--rule)"}}>
            <div className="label" style={{marginBottom:14}}>Detected in earlier steps</div>
            <div className="grid-2" style={{maxWidth:640}}>
              <div className="card" style={{padding:"12px 14px"}}>
                <div className="muted mono" style={{fontSize:10.5, marginBottom:4}}>Client.txt</div>
                <div className="mono" style={{fontSize:11}}>C:\Games\Path of Exile\logs\</div>
                <div style={{display:"flex", gap:6, marginTop:6}}>
                  <span className="pill ok"><span className="dot"/>tailing</span>
                </div>
              </div>
              <div className="card" style={{padding:"12px 14px"}}>
                <div className="muted mono" style={{fontSize:10.5, marginBottom:4}}>PoE documents</div>
                <div className="mono" style={{fontSize:11}}>C:\Users\kyra\Documents\My Games\Path of Exile\</div>
                <div style={{display:"flex", gap:6, marginTop:6}}>
                  <span className="pill ok"><span className="dot"/>writable</span>
                </div>
              </div>
              <div className="card" style={{padding:"12px 14px"}}>
                <div className="muted mono" style={{fontSize:10.5, marginBottom:4}}>GGG OAuth</div>
                <div style={{fontSize:12.5}}>Kyra_exile</div>
                <div style={{display:"flex", gap:6, marginTop:6}}>
                  <span className="pill ok"><span className="dot"/>token valid · 47d</span>
                </div>
              </div>
              <div className="card" style={{padding:"12px 14px"}}>
                <div className="muted mono" style={{fontSize:10.5, marginBottom:4}}>PoE window</div>
                <div style={{fontSize:12.5}}>Running · foreground OK</div>
                <div style={{display:"flex", gap:6, marginTop:6}}>
                  <span className="pill ok"><span className="dot"/>input test passed</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

window.OnboardingScreen = OnboardingScreen;
