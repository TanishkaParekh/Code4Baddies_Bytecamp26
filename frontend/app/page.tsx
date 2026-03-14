"use client";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

const C = {
  cream: "#F5F0E8",
  rose: "#D4A5A5",
  teal: "#2E7D8A",
  tealDark: "#1f5f6b",
  roseDark: "#b88888",
  text: "#1a1a1a",
  textLight: "#666",
};

const css = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap');
  * { margin:0; padding:0; box-sizing:border-box; }
  @keyframes fadeUp { from{opacity:0;transform:translateY(28px)} to{opacity:1;transform:translateY(0)} }
  @keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
  @keyframes drift { 0%{transform:translate(0,0) rotate(0deg)} 50%{transform:translate(25px,-18px) rotate(180deg)} 100%{transform:translate(0,0) rotate(360deg)} }
  @keyframes pulse-dot { 0%,100%{box-shadow:0 0 0 0 rgba(212,165,165,0.5)} 50%{box-shadow:0 0 0 10px rgba(212,165,165,0)} }
  @keyframes edgePulse { 0%,100%{opacity:0.3} 50%{opacity:1} }
  @keyframes nodePulse { 0%,100%{box-shadow:0 0 0 0 rgba(212,165,165,0.4)} 50%{box-shadow:0 0 0 10px rgba(212,165,165,0)} }
  .a1{animation:fadeUp 0.8s cubic-bezier(.16,1,.3,1) both}
  .a2{animation:fadeUp 0.8s 0.12s cubic-bezier(.16,1,.3,1) both}
  .a3{animation:fadeUp 0.8s 0.24s cubic-bezier(.16,1,.3,1) both}
  .a4{animation:fadeUp 0.8s 0.36s cubic-bezier(.16,1,.3,1) both}
  .a5{animation:fadeUp 0.8s 0.48s cubic-bezier(.16,1,.3,1) both}
  .float{animation:float 4s ease-in-out infinite}
  .float2{animation:float 5s 1.2s ease-in-out infinite}
  .drift1{animation:drift 20s linear infinite}
  .drift2{animation:drift 28s 5s linear infinite}
  .sf{opacity:0;transform:translateY(20px);transition:all 0.7s cubic-bezier(.16,1,.3,1)}
  .sf.vis{opacity:1;transform:translateY(0)}
  .btn-p{background:${C.teal};color:#fff;border:none;padding:13px 28px;border-radius:50px;font-size:14px;font-weight:600;cursor:pointer;font-family:'DM Sans',sans-serif;transition:all 0.25s}
  .btn-p:hover{background:${C.tealDark};transform:translateY(-2px);box-shadow:0 8px 24px rgba(46,125,138,0.35)}
  .btn-s{background:transparent;color:${C.teal};border:1.5px solid ${C.teal};padding:12px 24px;border-radius:50px;font-size:14px;font-weight:500;cursor:pointer;font-family:'DM Sans',sans-serif;transition:all 0.25s}
  .btn-s:hover{background:${C.teal}15;transform:translateY(-2px)}
  .fcard{background:#fff;border-radius:18px;padding:26px 22px;border:1px solid rgba(46,125,138,0.1);transition:all 0.3s;cursor:default}
  .fcard:hover{transform:translateY(-6px);box-shadow:0 20px 48px rgba(46,125,138,0.12);border-color:${C.rose}}
  .badge{display:flex;align-items:center;gap:6px;background:#fff;border:1px solid rgba(46,125,138,0.15);border-radius:50px;padding:7px 16px;font-size:12px;font-family:'DM Sans',sans-serif;color:${C.teal};font-weight:500;transition:all 0.2s}
  .badge:hover{background:${C.teal};color:#fff}
  .nl{transition:color 0.2s;cursor:pointer}
  .nl:hover{color:${C.teal} !important}
`;

export default function LandingPage() {
  const router = useRouter();
  const [scrolled, setScrolled] = useState(false);
  const [activeDrug, setActiveDrug] = useState(0);

  const drugs = [
    { name: "Metoprolol 50mg", spec: "Cardiologist", risk: true },
    { name: "Fluoxetine 20mg", spec: "Psychiatrist", risk: true },
    { name: "Celecoxib 200mg", spec: "Rheumatologist", risk: true },
    { name: "Metformin 500mg", spec: "Endocrinologist", risk: false },
  ];

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll);
    const interval = setInterval(() => setActiveDrug(p => (p + 1) % drugs.length), 1600);
    const observer = new IntersectionObserver(
      entries => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add("vis"); }),
      { threshold: 0.12 }
    );
    document.querySelectorAll(".sf").forEach(el => observer.observe(el));
    return () => { window.removeEventListener("scroll", onScroll); clearInterval(interval); observer.disconnect(); };
  }, []);

  return (
    <>
      <style>{css}</style>
      <div style={{ fontFamily: "'DM Sans', sans-serif", background: C.cream, color: C.text, overflowX: "hidden" }}>

        {/* BG blobs */}
        <div style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0, overflow: "hidden" }}>
          <div className="drift1" style={{ position: "absolute", top: "8%", right: "4%", width: 420, height: 420, borderRadius: "50%", background: `radial-gradient(circle, ${C.rose}20 0%, transparent 70%)` }} />
          <div className="drift2" style={{ position: "absolute", bottom: "15%", left: "2%", width: 360, height: 360, borderRadius: "50%", background: `radial-gradient(circle, ${C.teal}12 0%, transparent 70%)` }} />
        </div>

        {/* Navbar */}
        <nav style={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 100, padding: "0 48px", height: 66, display: "flex", alignItems: "center", justifyContent: "space-between", background: scrolled ? "rgba(245,240,232,0.93)" : "transparent", backdropFilter: scrolled ? "blur(16px)" : "none", borderBottom: scrolled ? "1px solid rgba(46,125,138,0.1)" : "none", transition: "all 0.35s" }}>
          <div onClick={() => router.push("/")} style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer" }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: `linear-gradient(135deg, ${C.teal}, ${C.tealDark})`, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: `0 4px 12px ${C.teal}44` }}>
              <span style={{ color: "#fff", fontWeight: 700, fontSize: 13, fontFamily: "'DM Serif Display', serif" }}>Rx</span>
            </div>
            <span style={{ fontWeight: 600, fontSize: 18, color: C.teal, fontFamily: "'DM Serif Display', serif" }}>CascadeRx</span>
          </div>
          <div style={{ display: "flex", gap: 28 }}>
            {["How it Works", "Features", "About"].map(l => <span key={l} className="nl" style={{ fontSize: 14, color: C.textLight, fontWeight: 500 }}>{l}</span>)}
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            <button className="btn-s" style={{ padding: "8px 20px", fontSize: 13 }} onClick={() => router.push("/login")}>Sign in</button>
            <button className="btn-p" style={{ padding: "8px 20px", fontSize: 13 }} onClick={() => router.push("/signup")}>Get started free</button>
          </div>
        </nav>

        {/* Hero */}
        <section style={{ maxWidth: 1160, margin: "0 auto", padding: "130px 48px 80px", display: "grid", gridTemplateColumns: "1.1fr 0.9fr", gap: 60, alignItems: "center", position: "relative", zIndex: 1 }}>
          <div>
            <div className="a1" style={{ display: "inline-flex", alignItems: "center", gap: 8, background: `${C.rose}22`, border: `1px solid ${C.rose}55`, borderRadius: 50, padding: "5px 16px", marginBottom: 26 }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: C.rose, display: "inline-block", animation: "pulse-dot 2s infinite" }} />
              <span style={{ fontSize: 11, color: C.roseDark, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase" }}>Medication Safety for Everyone</span>
            </div>
            <h1 className="a2" style={{ fontFamily: "'DM Serif Display', serif", fontSize: "clamp(38px, 5vw, 62px)", lineHeight: 1.1, letterSpacing: "-0.02em", marginBottom: 20, color: C.text }}>
              Check if your<br />
              <span style={{ color: C.teal, fontStyle: "italic" }}>medications</span><br />
              are safe together.
            </h1>
            <p className="a3" style={{ fontSize: 16, color: C.textLight, lineHeight: 1.75, marginBottom: 32, maxWidth: 470, fontWeight: 300 }}>
              When different doctors prescribe medications, hidden drug cascades can occur. CascadeRx analyzes your full list to detect risks <em>before they affect you.</em>
            </p>
            <div className="a4" style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 36 }}>
              <button className="btn-p" style={{ fontSize: 15, padding: "14px 30px" }} onClick={() => router.push("/signup")}>Start Medication Check →</button>
              <button className="btn-s" onClick={() => router.push("/checker")}>See How It Works</button>
            </div>
            <div className="a5" style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {["🔬 FDA Verified", "⚗️ CYP Enzyme Model", "🛡️ Private & Secure", "⚡ Results in Seconds"].map(b => (
                <div key={b} className="badge">{b}</div>
              ))}
            </div>
          </div>

          {/* Hero card */}
          <div style={{ position: "relative" }}>
            <div className="a4" style={{ background: "#fff", borderRadius: 24, padding: 28, boxShadow: `0 24px 60px rgba(46,125,138,0.14)`, border: `1px solid ${C.teal}15` }}>
              <div style={{ fontSize: 11, color: C.textLight, fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#4CAF50", display: "inline-block" }} />
                Your medications
              </div>
              {drugs.map((d, i) => (
                <div key={d.name} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", borderRadius: 10, marginBottom: 8, background: i === activeDrug ? `${C.teal}10` : C.cream, border: `1px solid ${i === activeDrug ? C.teal + "44" : "transparent"}`, transition: "all 0.35s", fontFamily: "'DM Sans', sans-serif" }}>
                  <span style={{ fontSize: 16 }}>💊</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, color: C.text, fontSize: 13 }}>{d.name}</div>
                    <div style={{ fontSize: 11, color: C.textLight }}>{d.spec}</div>
                  </div>
                  <span style={{ fontSize: 11, fontWeight: 700, padding: "2px 8px", borderRadius: 20, background: d.risk ? `${C.rose}25` : "#4CAF5018", color: d.risk ? C.roseDark : "#4CAF50" }}>{d.risk ? "⚠ Risk" : "✓ Safe"}</span>
                </div>
              ))}
              <button className="btn-p" style={{ width: "100%", marginTop: 10, fontSize: 14 }} onClick={() => router.push("/checker")}>Analyze Medication Interactions</button>
            </div>
            {/* Alert float */}
            <div className="float" style={{ position: "absolute", bottom: -20, right: -20, background: C.teal, borderRadius: 16, padding: "12px 16px", boxShadow: `0 10px 30px ${C.teal}44`, maxWidth: 230 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 5 }}>
                <span style={{ width: 7, height: 7, borderRadius: "50%", background: C.rose, display: "inline-block", animation: "pulse-dot 1.5s infinite" }} />
                <span style={{ fontSize: 10, color: "rgba(255,255,255,0.9)", fontWeight: 700, letterSpacing: "0.07em" }}>CASCADE DETECTED</span>
              </div>
              <p style={{ fontSize: 11, color: "rgba(255,255,255,0.82)", lineHeight: 1.5 }}>Fluoxetine is blocking the enzyme that clears Metoprolol from your body</p>
            </div>
            {/* Score float */}
            <div className="float2" style={{ position: "absolute", top: -16, left: -16, background: "#fff", borderRadius: 14, padding: "10px 14px", boxShadow: "0 8px 24px rgba(0,0,0,0.1)", display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 20 }}>🛡️</span>
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: C.text }}>Risk Score</div>
                <div style={{ fontSize: 12, color: C.roseDark, fontWeight: 600 }}>9.2 / 10 — Critical</div>
              </div>
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="sf" style={{ maxWidth: 880, margin: "0 auto", padding: "0 48px 72px", display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 18, position: "relative", zIndex: 1 }}>
          {[
            { num: "73%", label: "of cascade risks missed by standard checkers" },
            { num: "< 30s", label: "to get your complete medication safety report" },
            { num: "FDA", label: "verified data powering every interaction check" },
          ].map(s => (
            <div key={s.num} style={{ background: "#fff", borderRadius: 16, padding: "22px", textAlign: "center", border: `1px solid rgba(46,125,138,0.08)` }}>
              <div style={{ fontFamily: "'DM Serif Display', serif", fontSize: 34, color: C.teal }}>{s.num}</div>
              <div style={{ fontSize: 12, color: C.textLight, marginTop: 6, lineHeight: 1.5 }}>{s.label}</div>
            </div>
          ))}
        </section>

        {/* How it works */}
        <section className="sf" style={{ background: C.teal, padding: "72px 48px", position: "relative", zIndex: 1 }}>
          <div style={{ maxWidth: 1100, margin: "0 auto" }}>
            <div style={{ textAlign: "center", marginBottom: 48 }}>
              <div style={{ fontSize: 11, color: `${C.cream}88`, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 10 }}>How it works</div>
              <h2 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 38, color: C.cream }}>Three steps to peace of mind.</h2>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 18 }}>
              {[
                { num: "01", title: "Enter all your medications", desc: "Add every medication from every doctor — dose and specialist info makes the analysis more precise.", icon: "💊" },
                { num: "02", title: "Our engine analyzes cascades", desc: "We model CYP enzyme pathways to find hidden risks that only appear when 3+ drugs interact together.", icon: "🔬" },
                { num: "03", title: "Get your safety report", desc: "Plain English explanation, what to tell your pharmacist, and safer alternatives where available.", icon: "📋" },
              ].map((item, i) => (
                <div key={item.num} style={{ background: i === 1 ? C.cream : "rgba(255,255,255,0.1)", borderRadius: 18, padding: "28px 24px", border: i !== 1 ? "1px solid rgba(255,255,255,0.15)" : "none", transition: "transform 0.3s" }}>
                  <div style={{ fontSize: 11, color: i === 1 ? C.teal : `${C.cream}77`, letterSpacing: "0.1em", marginBottom: 14 }}>{item.num}</div>
                  <div style={{ fontSize: 28, marginBottom: 12 }}>{item.icon}</div>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: i === 1 ? C.teal : C.cream, marginBottom: 8, fontFamily: "'DM Serif Display', serif" }}>{item.title}</h3>
                  <p style={{ fontSize: 13, color: i === 1 ? C.textLight : `${C.cream}cc`, lineHeight: 1.7 }}>{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Real example */}
        <section className="sf" style={{ maxWidth: 1100, margin: "0 auto", padding: "72px 48px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 56, alignItems: "center", position: "relative", zIndex: 1 }}>
          <div>
            <div style={{ fontSize: 11, color: C.rose, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 14, fontWeight: 600 }}>Real Example</div>
            <h2 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 34, color: C.text, marginBottom: 18, lineHeight: 1.2 }}>What standard checkers <em style={{ color: C.rose }}>miss.</em></h2>
            <p style={{ fontSize: 15, color: C.textLight, lineHeight: 1.75, marginBottom: 20 }}>A patient seeing 4 different specialists. Each doctor prescribed correctly for their area. But <strong style={{ color: C.text }}>Fluoxetine was silently blocking the enzyme</strong> that clears Metoprolol — causing it to build up to 3–5× normal levels.</p>
            <p style={{ fontSize: 14, color: C.textLight, lineHeight: 1.7, marginBottom: 28 }}>No standard pairwise checker would have found this. CascadeRx caught it instantly.</p>
            <button className="btn-p" onClick={() => router.push("/checker")}>See it live →</button>
          </div>
          <div style={{ background: "#fff", borderRadius: 22, padding: 28, boxShadow: "0 10px 40px rgba(0,0,0,0.07)", border: `1px solid ${C.rose}22` }}>
            <div style={{ fontSize: 11, color: C.textLight, fontWeight: 600, marginBottom: 18, letterSpacing: "0.07em", textTransform: "uppercase" }}>Cascade Fingerprint™</div>
            <div style={{ position: "relative", height: 190 }}>
              <svg style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
                <line x1="22%" y1="22%" x2="45%" y2="50%" stroke={C.rose} strokeWidth="2.5" strokeDasharray="6,3" style={{ animation: "edgePulse 1.5s infinite" }} />
                <line x1="45%" y1="56%" x2="22%" y2="82%" stroke={C.rose} strokeWidth="2.5" strokeDasharray="6,3" style={{ animation: "edgePulse 1.5s 0.4s infinite" }} />
                <line x1="48%" y1="55%" x2="72%" y2="72%" stroke="#ccc" strokeWidth="1.5" />
              </svg>
              {[
                { label: "Fluoxetine", x: 22, y: 18, bg: C.rose, color: "#fff" },
                { label: "CYP2D6", x: 45, y: 50, bg: C.teal, color: "#fff", round: true },
                { label: "Metoprolol", x: 22, y: 82, bg: C.rose, color: "#fff" },
                { label: "Metformin", x: 72, y: 72, bg: "#7BAE8A", color: "#fff" },
              ].map(n => (
                <div key={n.label} style={{ position: "absolute", left: `${n.x}%`, top: `${n.y}%`, transform: "translate(-50%,-50%)" }}>
                  <div style={{ background: n.bg, color: n.color, borderRadius: n.round ? "50%" : 8, padding: n.round ? "14px 10px" : "7px 12px", fontSize: 11, fontWeight: 700, textAlign: "center", minWidth: n.round ? 60 : 80, minHeight: n.round ? 60 : 32, display: "flex", alignItems: "center", justifyContent: "center", animation: n.bg === C.rose ? "nodePulse 2s infinite" : "none" }}>{n.label}</div>
                </div>
              ))}
            </div>
            <div style={{ background: `${C.rose}15`, border: `1px solid ${C.rose}44`, borderRadius: 10, padding: "11px 14px", marginTop: 10 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: C.roseDark, marginBottom: 3 }}>⚠ CASCADE ALERT — CRITICAL</div>
              <div style={{ fontSize: 12, color: C.textLight, lineHeight: 1.5 }}>Fluoxetine blocks CYP2D6 → Metoprolol builds up 3–5× → Bradycardia risk</div>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="sf" style={{ background: `${C.rose}12`, padding: "72px 48px", position: "relative", zIndex: 1 }}>
          <div style={{ maxWidth: 1100, margin: "0 auto" }}>
            <div style={{ textAlign: "center", marginBottom: 48 }}>
              <div style={{ fontSize: 11, color: C.rose, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 12, fontWeight: 600 }}>What you get</div>
              <h2 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 38, color: C.text }}>Everything you need to stay safe.</h2>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16 }}>
              {[
                { icon: "🕸️", title: "Cascade Fingerprint™", desc: "Interactive graph that lights up red when it finds a hidden multi-drug enzyme bottleneck." },
                { icon: "⚗️", title: "CYP Enzyme Modelling", desc: "Models the exact liver enzymes responsible for clearing most common medications." },
                { icon: "📜", title: "FDA Verified Sources", desc: "Every flag cites FDA tables, DrugBank, and PubMed — you can verify every claim." },
                { icon: "🤖", title: "AI Safety Report", desc: "Plain English explanation of what's happening and exactly what to tell your pharmacist." },
                { icon: "📄", title: "PDF Export", desc: "Download your full report to bring to your next doctor or pharmacy appointment." },
                { icon: "👤", title: "Save Your Profile", desc: "Save your medication list and check again whenever a new drug is prescribed." },
              ].map(f => (
                <div key={f.title} className="fcard">
                  <div style={{ fontSize: 26, marginBottom: 12 }}>{f.icon}</div>
                  <h3 style={{ fontSize: 15, fontWeight: 700, color: C.text, marginBottom: 7, fontFamily: "'DM Serif Display', serif" }}>{f.title}</h3>
                  <p style={{ fontSize: 13, color: C.textLight, lineHeight: 1.7 }}>{f.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="sf" style={{ maxWidth: 680, margin: "0 auto", padding: "90px 48px", textAlign: "center", position: "relative", zIndex: 1 }}>
          <h2 style={{ fontFamily: "'DM Serif Display', serif", fontSize: "clamp(30px, 4vw, 50px)", color: C.text, marginBottom: 16, lineHeight: 1.2 }}>Check your medications<br /><span style={{ color: C.teal, fontStyle: "italic" }}>in under 30 seconds.</span></h2>
          <p style={{ fontSize: 15, color: C.textLight, marginBottom: 32, lineHeight: 1.7 }}>Free to use. No credit card. No medical jargon.</p>
          <div style={{ display: "flex", gap: 14, justifyContent: "center", flexWrap: "wrap" }}>
            <button className="btn-p" style={{ fontSize: 15, padding: "15px 34px" }} onClick={() => router.push("/signup")}>Start Medication Check →</button>
            <button className="btn-s" onClick={() => router.push("/checker")}>Try demo first</button>
          </div>
        </section>

        {/* Footer */}
        <footer style={{ background: C.text, padding: "32px 48px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16, position: "relative", zIndex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 30, height: 30, borderRadius: 8, background: C.teal, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ color: "#fff", fontWeight: 700, fontSize: 11, fontFamily: "'DM Serif Display', serif" }}>Rx</span>
            </div>
            <span style={{ fontWeight: 600, fontSize: 15, color: C.cream, fontFamily: "'DM Serif Display', serif" }}>CascadeRx</span>
          </div>
          <p style={{ fontSize: 12, color: "#777" }}>For medication safety guidance only — always confirm with your pharmacist. © 2026</p>
          <div style={{ display: "flex", gap: 20 }}>
            {["Privacy", "Terms", "Contact"].map(l => <span key={l} style={{ fontSize: 13, color: "#777", cursor: "pointer" }}>{l}</span>)}
          </div>
        </footer>
      </div>
    </>
  );
}
