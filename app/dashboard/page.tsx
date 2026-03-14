"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { onAuthStateChanged, signOut } from "firebase/auth";
import { auth } from "../../lib/firebase";

const C = { cream: "#F5F0E8", rose: "#D4A5A5", teal: "#2E7D8A", tealDark: "#1f5f6b", roseDark: "#b88888", text: "#1a1a1a", textLight: "#666" };

const css = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap');
  *{margin:0;padding:0;box-sizing:border-box}
  @keyframes fadeUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
  @keyframes pulse-dot{0%,100%{box-shadow:0 0 0 0 rgba(212,165,165,0.5)}50%{box-shadow:0 0 0 8px rgba(212,165,165,0)}}
  .a1{animation:fadeUp 0.5s cubic-bezier(.16,1,.3,1) both}
  .a2{animation:fadeUp 0.5s 0.08s cubic-bezier(.16,1,.3,1) both}
  .a3{animation:fadeUp 0.5s 0.16s cubic-bezier(.16,1,.3,1) both}
  .a4{animation:fadeUp 0.5s 0.24s cubic-bezier(.16,1,.3,1) both}
  .nav-item{padding:10px 14px;border-radius:10px;border:none;background:transparent;cursor:pointer;font-family:'DM Sans',sans-serif;font-size:13px;display:flex;align-items:center;gap:9px;width:100%;text-align:left;transition:all 0.15s;color:#666}
  .nav-item:hover{background:rgba(46,125,138,0.08);color:${C.teal}}
  .nav-item.active{background:${C.teal}18;color:${C.teal};font-weight:600}
  .med-row{display:flex;align-items:center;gap:10px;padding:12px 14px;border-radius:10px;border:1px solid rgba(46,125,138,0.08);background:rgba(245,240,232,0.4);transition:all 0.2s}
  .med-row:hover{background:#fff;border-color:rgba(46,125,138,0.2)}
  .history-row{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-radius:10px;background:rgba(245,240,232,0.4);border:1px solid rgba(46,125,138,0.08);transition:all 0.2s}
  .history-row:hover{background:#fff;border-color:rgba(46,125,138,0.2)}
  .history-row-clickable{cursor:pointer}
  .history-row-clickable:hover{transform:translateX(3px)}
  .btn-main{background:${C.teal};color:#fff;border:none;padding:13px 24px;border-radius:50px;font-size:14px;font-weight:600;cursor:pointer;font-family:'DM Sans',sans-serif;transition:all 0.25s;display:inline-flex;align-items:center;gap:8px}
  .btn-main:hover{background:${C.tealDark};transform:translateY(-2px);box-shadow:0 8px 24px rgba(46,125,138,0.3)}
  .scrollbox{overflow-y:auto;scrollbar-width:thin;scrollbar-color:rgba(46,125,138,0.2) transparent}
  .scrollbox::-webkit-scrollbar{width:4px}
  .scrollbox::-webkit-scrollbar-track{background:transparent}
  .scrollbox::-webkit-scrollbar-thumb{background:rgba(46,125,138,0.2);border-radius:4px}
  
  /* GLASS ALERT HOVER */
  .safety-card{transition: all 0.3s ease;}
  .safety-card:hover{transform: translateY(-3px); box-shadow: 0 15px 35px rgba(46, 125, 138, 0.3), inset 0 0 0 1px rgba(255, 255, 255, 0.2) !important;}
`;

const ALL_MEDS_LOG = [
  { name: "Metoprolol 50mg", doctor: "Dr. Shah — Cardiologist", date: "14 Mar 2026", risk: true },
  { name: "Fluoxetine 20mg", doctor: "Dr. Patel — Psychiatrist", date: "14 Mar 2026", risk: true },
  { name: "Celecoxib 200mg", doctor: "Dr. Kumar — Rheumatologist", date: "14 Mar 2026", risk: true },
  { name: "Metformin 500mg", doctor: "Dr. Rao — Endocrinologist", date: "14 Mar 2026", risk: false },
  { name: "Aspirin 75mg", doctor: "Dr. Shah — Cardiologist", date: "28 Feb 2026", risk: false },
  { name: "Omeprazole 20mg", doctor: "Dr. Mehta — Gastroenterologist", date: "28 Feb 2026", risk: false },
  { name: "Amlodipine 5mg", doctor: "Dr. Shah — Cardiologist", date: "10 Jan 2026", risk: false },
];

const PAST_CHECKS = [
  { id: 1, date: "14 Mar 2026", drugs: "4 medications", risk: "CRITICAL", icon: "⚠", meds: ["Fluoxetine", "Metoprolol", "Celecoxib", "Metformin"] },
  { id: 2, date: "28 Feb 2026", drugs: "3 medications", risk: "SAFE", icon: "✓", meds: ["Aspirin", "Omeprazole", "Amlodipine"] },
  { id: 3, date: "10 Jan 2026", drugs: "2 medications", risk: "MODERATE", icon: "⚠", meds: ["Amlodipine", "Metformin"] },
];

const RISK_COLOR: Record<string, { bg: string; color: string; border: string }> = {
  CRITICAL: { bg: "#FEE2E2", color: "#B91C1C", border: "#FCA5A5" },
  HIGH:     { bg: "#FEF3C7", color: "#92400E", border: "#FCD34D" },
  MODERATE: { bg: "#FEF9C3", color: "#854D0E", border: "#FDE047" },
  SAFE:     { bg: "#DCFCE7", color: "#166534", border: "#86EFAC" },
};

function RiskBadge({ risk }: { risk: string }) {
  const c = RISK_COLOR[risk] || RISK_COLOR.MODERATE;
  return (
    <span style={{ fontSize: 11, fontWeight: 700, padding: "3px 10px", borderRadius: 20, background: c.bg, color: c.color, border: `1px solid ${c.border}`, letterSpacing: "0.05em" }}>{risk}</span>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("dashboard");

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, u => {
      if (!u) router.push("/login");
      else { setUser(u); setLoading(false); }
    });
    return () => unsub();
  }, [router]);

  if (loading) return (
    <div style={{ minHeight: "100vh", background: C.cream, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'DM Sans', sans-serif" }}>
      <div style={{ textAlign: "center" }}>
        <div style={{ width: 40, height: 40, borderRadius: 10, background: C.teal, display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 12px" }}>
          <span style={{ color: "#fff", fontWeight: 700, fontFamily: "'DM Serif Display', serif" }}>Rx</span>
        </div>
        <div style={{ fontSize: 14, color: C.textLight }}>Loading...</div>
      </div>
    </div>
  );

  const firstName = user?.displayName?.split(" ")[0] || "there";

  const navItems = [
    { id: "dashboard", label: "My Dashboard", icon: "🏠" },
    { id: "check", label: "Check Medications", icon: "🔬" },
    { id: "past", label: "Past Checks", icon: "📋" },
    { id: "profile", label: "My Profile", icon: "👤" },
  ];

  return (
    <>
      <style>{css}</style>
      <div style={{ minHeight: "100vh", background: C.cream, fontFamily: "'DM Sans', sans-serif", display: "flex", flexDirection: "column" }}>

        <nav style={{ background: "#fff", borderBottom: `1px solid rgba(46,125,138,0.1)`, padding: "0 32px", height: 62, display: "flex", alignItems: "center", justifyContent: "space-between", boxShadow: "0 1px 8px rgba(0,0,0,0.04)" }}>
          <div onClick={() => setTab("dashboard")} style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer" }}>
            <div style={{ width: 34, height: 34, borderRadius: 10, background: `linear-gradient(135deg, ${C.teal}, ${C.tealDark})`, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ color: "#fff", fontWeight: 700, fontSize: 12, fontFamily: "'DM Serif Display', serif" }}>Rx</span>
            </div>
            <span style={{ fontWeight: 600, fontSize: 17, color: C.teal, fontFamily: "'DM Serif Display', serif" }}>CascadeRx</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, background: C.cream, borderRadius: 50, padding: "6px 14px 6px 8px" }}>
              <div style={{ width: 28, height: 28, borderRadius: "50%", background: `linear-gradient(135deg, ${C.rose}, ${C.roseDark})`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ color: "#fff", fontSize: 12, fontWeight: 700 }}>{firstName[0]?.toUpperCase()}</span>
              </div>
              <span style={{ fontSize: 13, fontWeight: 500, color: C.text }}>{user?.displayName || user?.email}</span>
            </div>
            <button onClick={async () => { await signOut(auth); router.push("/"); }} style={{ padding: "7px 16px", fontSize: 12, background: "transparent", border: `1px solid rgba(46,125,138,0.2)`, borderRadius: 50, color: C.textLight, cursor: "pointer", fontFamily: "'DM Sans', sans-serif" }}>Sign out</button>
          </div>
        </nav>

        <div style={{ display: "flex", flex: 1 }}>
          <aside style={{ width: 210, background: "#fff", borderRight: `1px solid rgba(46,125,138,0.08)`, padding: "20px 14px", display: "flex", flexDirection: "column", gap: 3, flexShrink: 0 }}>
            {navItems.map(item => (
              <button key={item.id} className={`nav-item ${tab === item.id ? "active" : ""}`} onClick={() => item.id === "check" ? router.push("/checker") : setTab(item.id)}>
                <span>{item.icon}</span>{item.label}
              </button>
            ))}
          </aside>

          <main style={{ flex: 1, padding: "32px 36px", overflowY: "auto" }}>
            {tab === "dashboard" && (
              <div>
                <div className="a1" style={{ marginBottom: 24 }}>
                  <h1 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 30, color: C.text, letterSpacing: "-0.02em", marginBottom: 4 }}>
                    Welcome back, {firstName} 👋
                  </h1>
                  <p style={{ fontSize: 14, color: C.textLight }}>Let's check if your medications are working safely together.</p>
                </div>

                <div className="a2" style={{ background: `linear-gradient(135deg, ${C.teal}, ${C.tealDark})`, borderRadius: 18, padding: "24px 32px", marginBottom: 24, display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 16 }}>
                  <div>
                    <h2 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 20, color: "#fff", marginBottom: 5 }}>Check your medications now</h2>
                    <p style={{ fontSize: 13, color: "rgba(255,255,255,0.75)", lineHeight: 1.5 }}>Get a full safety report in under 30 seconds.</p>
                  </div>
                  <button className="btn-main" style={{ background: "#fff", color: C.teal }} onClick={() => router.push("/checker")}>🔬 Analyze My Medications</button>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1.3fr 0.7fr", gap: 20, alignItems: "stretch" }}>
                  <div className="a3" style={{ background: "#fff", borderRadius: 18, padding: "24px", boxShadow: "0 2px 12px rgba(0,0,0,0.05)", border: `1px solid rgba(46,125,138,0.07)` }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                      <h3 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 18, color: C.text }}>Your Medications</h3>
                      <span style={{ fontSize: 12, color: C.textLight, background: C.cream, borderRadius: 20, padding: "3px 10px" }}>{ALL_MEDS_LOG.length} total</span>
                    </div>
                    <div className="scrollbox" style={{ maxHeight: 280, display: "flex", flexDirection: "column", gap: 8 }}>
                      {ALL_MEDS_LOG.map((m, i) => (
                        <div key={i} className="med-row">
                          <span style={{ fontSize: 18 }}>💊</span>
                          <div style={{ flex: 1 }}>
                            <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{m.name}</div>
                            <div style={{ fontSize: 11, color: C.textLight }}>{m.doctor}</div>
                          </div>
                          <RiskBadge risk={m.risk ? "CRITICAL" : "SAFE"} />
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="a4" style={{ display: "flex", flexDirection: "column" }}>
                    {/* UPGRADED SAFETY ALERT BOX */}
                    <div className="safety-card" style={{ 
                      background: `linear-gradient(135deg, rgba(46, 125, 138, 0.95), rgba(31, 95, 107, 0.9))`, 
                      backdropFilter: "blur(10px)", borderRadius: 24, padding: "32px", 
                      boxShadow: `0 12px 30px rgba(46, 125, 138, 0.25), inset 0 0 0 1px rgba(255, 255, 255, 0.15)`, 
                      flex: 1, display: "flex", flexDirection: "column", position: "relative", overflow: "hidden" 
                    }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 28 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <span style={{ width: 8, height: 8, borderRadius: "50%", background: C.rose, display: "inline-block", animation: "pulse-dot 1.5s infinite" }} />
                          <span style={{ fontSize: 25, color: "rgba(237, 171, 171, 0.8)", fontWeight: 900, letterSpacing: "0.1em" }}>SAFETY ALERT!</span>
                        </div>
                        <div style={{ width: 48, height: 48, borderRadius: 14, background: "rgba(255,255,255,0.12)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 24, backdropFilter: "blur(5px)", border: "1px solid rgba(255,255,255,0.2)" }}>🧬</div>
                      </div>

                      <h2 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 24, color: "#fff", marginBottom: 20, lineHeight: 1.2 }}>
                        Medication Interaction Detected
                      </h2>

                      <p style={{ fontSize: 14, color: "rgba(255,255,255,0.95)", lineHeight: 1.7, marginBottom: 18 }}>
                        <strong style={{ color: "#fff", fontWeight: 700 }}>2 of your medications</strong> are currently blocking the enzyme that clears Metoprolol — raising its levels dangerously.
                      </p>

                      <p style={{ fontSize: 12, color: "rgba(255,255,255,0.6)", lineHeight: 1.6, marginBottom: 24, fontStyle: "italic" }}>
                        This interaction was cross-referenced from your current medication list and previous safety checks.
                      </p>

                      <div style={{ marginTop: "auto" }}>
                        <button onClick={() => router.push("/checker")} style={{ width: "100%", padding: "14px", fontSize: 13, fontWeight: 700, background: "#fff", color: C.teal, border: "none", borderRadius: 14, cursor: "pointer", boxShadow: "0 4px 12px rgba(0,0,0,0.1)" }}>
                          Resolve Interaction →
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="a4" style={{ background: "#fff", borderRadius: 18, padding: "24px", boxShadow: "0 2px 12px rgba(0,0,0,0.05)", border: `1px solid rgba(46,125,138,0.07)`, marginTop: 20 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                    <h3 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 18, color: C.text }}>Past Medication Checks</h3>
                    <button onClick={() => setTab("past")} style={{ fontSize: 12, color: C.teal, background: "transparent", border: "none", cursor: "pointer", fontWeight: 500 }}>See all →</button>
                  </div>
                  <div className="scrollbox" style={{ maxHeight: 220, display: "flex", flexDirection: "column", gap: 8 }}>
                    {PAST_CHECKS.map(h => (
                      <div key={h.id} className="history-row">
                        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                          <div style={{ width: 34, height: 34, borderRadius: 10, background: h.risk === "SAFE" ? "#4CAF5015" : `${C.rose}20`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15 }}>{h.icon}</div>
                          <div>
                            <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{h.drugs}</div>
                            <div style={{ fontSize: 11, color: C.textLight }}>{h.date}</div>
                          </div>
                        </div>
                        <RiskBadge risk={h.risk} />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
            {tab === "past" && <div><h1 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 28, color: C.text }}>Past Checks</h1></div>}
            {tab === "profile" && <div><h1 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 28, color: C.text }}>My Profile</h1></div>}
          </main>
        </div>
      </div>
    </>
  );
}