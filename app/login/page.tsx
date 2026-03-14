"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { signInWithEmailAndPassword } from "firebase/auth";
import { auth } from "../../lib/firebase";

const C = { cream: "#F5F0E8", rose: "#D4A5A5", teal: "#2E7D8A", tealDark: "#1f5f6b", roseDark: "#b88888", text: "#1a1a1a", textLight: "#666" };

const css = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap');
  *{margin:0;padding:0;box-sizing:border-box}
  @keyframes fadeUp{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:translateY(0)}}
  @keyframes drift{0%{transform:translate(0,0) rotate(0deg)}50%{transform:translate(20px,-15px) rotate(180deg)}100%{transform:translate(0,0) rotate(360deg)}}
  @keyframes shimmer{0%{background-position:-200% center}100%{background-position:200% center}}
  .card{animation:fadeUp 0.7s cubic-bezier(.16,1,.3,1) both}
  .drift1{animation:drift 18s linear infinite}
  .drift2{animation:drift 25s 4s linear infinite}
  .inp{width:100%;padding:12px 16px;font-size:14px;border:1.5px solid rgba(46,125,138,0.2);border-radius:10px;outline:none;background:rgba(245,240,232,0.6);color:${C.text};font-family:'DM Sans',sans-serif;transition:all 0.2s}
  .inp:focus{border-color:${C.teal};background:#fff;box-shadow:0 0 0 3px rgba(46,125,138,0.1)}
  .btn{width:100%;padding:13px;font-size:15px;font-weight:600;background:${C.teal};color:#fff;border:none;border-radius:50px;cursor:pointer;font-family:'DM Sans',sans-serif;transition:all 0.25s;margin-top:8px}
  .btn:hover{background:${C.tealDark};transform:translateY(-2px);box-shadow:0 8px 24px rgba(46,125,138,0.3)}
  .btn:disabled{opacity:0.6;cursor:not-allowed;transform:none}
`;

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin() {
    setError("");
    if (!email || !password) { setError("Please fill in all fields."); return; }
    setLoading(true);
    try {
      await signInWithEmailAndPassword(auth, email, password);
      router.push("/dashboard");
    } catch {
      setError("Invalid email or password. Please try again.");
    } finally { setLoading(false); }
  }

  return (
    <>
      <style>{css}</style>
      <div style={{ minHeight: "100vh", background: C.cream, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'DM Sans', sans-serif", padding: 24, position: "relative", overflow: "hidden" }}>

        {/* BG blobs */}
        <div style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0 }}>
          <div className="drift1" style={{ position: "absolute", top: "5%", right: "8%", width: 380, height: 380, borderRadius: "50%", background: `radial-gradient(circle, ${C.rose}22 0%, transparent 70%)` }} />
          <div className="drift2" style={{ position: "absolute", bottom: "10%", left: "5%", width: 300, height: 300, borderRadius: "50%", background: `radial-gradient(circle, ${C.teal}14 0%, transparent 70%)` }} />
        </div>

        <div style={{ width: "100%", maxWidth: 420, position: "relative", zIndex: 1 }}>
          {/* Logo */}
          <div style={{ textAlign: "center", marginBottom: 28, animation: "fadeUp 0.6s cubic-bezier(.16,1,.3,1) both" }}>
            <div onClick={() => router.push("/")} style={{ width: 50, height: 50, borderRadius: 14, background: `linear-gradient(135deg, ${C.teal}, ${C.tealDark})`, display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 12px", boxShadow: `0 8px 20px ${C.teal}44`, cursor: "pointer" }}>
              <span style={{ color: "#fff", fontWeight: 700, fontSize: 18, fontFamily: "'DM Serif Display', serif" }}>Rx</span>
            </div>
            <h1 onClick={() => router.push("/")} style={{ fontFamily: "'DM Serif Display', serif", fontSize: 22, color: C.teal, margin: 0, cursor: "pointer" }}>CascadeRx</h1>
            <p style={{ fontSize: 13, color: C.textLight, marginTop: 4 }}>Medication safety, powered by AI</p>
          </div>

          {/* Card */}
          <div className="card" style={{ background: "#fff", borderRadius: 24, padding: 36, boxShadow: `0 20px 60px rgba(46,125,138,0.12), 0 4px 20px rgba(0,0,0,0.05)`, border: `1px solid rgba(46,125,138,0.08)` }}>
            <h2 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 26, color: C.text, marginBottom: 6 }}>Welcome back</h2>
            <p style={{ fontSize: 13, color: C.textLight, marginBottom: 28 }}>Sign in to check your medications</p>

            {error && (
              <div style={{ background: "#FEE2E2", border: "1px solid #FCA5A5", borderRadius: 10, padding: "10px 14px", marginBottom: 20, fontSize: 13, color: "#B91C1C", display: "flex", alignItems: "center", gap: 8 }}>
                <span>⚠</span> {error}
              </div>
            )}

            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: C.teal, display: "block", marginBottom: 6, letterSpacing: "0.05em" }}>EMAIL ADDRESS</label>
              <input className="inp" type="email" placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} onKeyDown={e => e.key === "Enter" && handleLogin()} />
            </div>

            <div style={{ marginBottom: 8 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: C.teal, display: "block", marginBottom: 6, letterSpacing: "0.05em" }}>PASSWORD</label>
              <input className="inp" type="password" placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} onKeyDown={e => e.key === "Enter" && handleLogin()} />
            </div>

            <div style={{ textAlign: "right", marginBottom: 22 }}>
              <span style={{ fontSize: 12, color: C.roseDark, cursor: "pointer", fontWeight: 500 }}>Forgot password?</span>
            </div>

            <button className="btn" onClick={handleLogin} disabled={loading}>
              {loading ? "Signing in..." : "Sign in →"}
            </button>

            <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "24px 0" }}>
              <div style={{ flex: 1, height: 1, background: "rgba(46,125,138,0.1)" }} />
              <span style={{ fontSize: 12, color: C.textLight }}>or</span>
              <div style={{ flex: 1, height: 1, background: "rgba(46,125,138,0.1)" }} />
            </div>

            <p style={{ textAlign: "center", fontSize: 14, color: C.textLight }}>
              Don't have an account?{" "}
              <span onClick={() => router.push("/signup")} style={{ color: C.teal, fontWeight: 600, cursor: "pointer" }}>Create one free</span>
            </p>
          </div>

          <p style={{ textAlign: "center", fontSize: 11, color: C.textLight, marginTop: 20, lineHeight: 1.5, opacity: 0.7 }}>
            Medication safety guidance only — not a substitute for professional medical advice.
          </p>
        </div>
      </div>
    </>
  );
}
