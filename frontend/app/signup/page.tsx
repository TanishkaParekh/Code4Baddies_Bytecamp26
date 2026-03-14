"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { createUserWithEmailAndPassword, updateProfile } from "firebase/auth";
import { auth } from "../../lib/firebase";

const C = { cream: "#F5F0E8", rose: "#D4A5A5", teal: "#2E7D8A", tealDark: "#1f5f6b", roseDark: "#b88888", text: "#1a1a1a", textLight: "#666" };

const css = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap');
  *{margin:0;padding:0;box-sizing:border-box}
  @keyframes fadeUp{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:translateY(0)}}
  @keyframes drift{0%{transform:translate(0,0) rotate(0deg)}50%{transform:translate(20px,-15px) rotate(180deg)}100%{transform:translate(0,0) rotate(360deg)}}
  .card{animation:fadeUp 0.7s cubic-bezier(.16,1,.3,1) both}
  .drift1{animation:drift 18s linear infinite}
  .drift2{animation:drift 25s 4s linear infinite}
  .inp{width:100%;padding:12px 16px;font-size:14px;border:1.5px solid rgba(46,125,138,0.2);border-radius:10px;outline:none;background:rgba(245,240,232,0.6);color:${C.text};font-family:'DM Sans',sans-serif;transition:all 0.2s;box-sizing:border-box}
  .inp:focus{border-color:${C.teal};background:#fff;box-shadow:0 0 0 3px rgba(46,125,138,0.1)}
  .btn{width:100%;padding:13px;font-size:15px;font-weight:600;background:${C.teal};color:#fff;border:none;border-radius:50px;cursor:pointer;font-family:'DM Sans',sans-serif;transition:all 0.25s;margin-top:8px}
  .btn:hover{background:${C.tealDark};transform:translateY(-2px);box-shadow:0 8px 24px rgba(46,125,138,0.3)}
  .btn:disabled{opacity:0.6;cursor:not-allowed;transform:none}
`;

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [agreed, setAgreed] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSignup() {
    setError("");
    if (!name || !email || !password || !confirm) { setError("Please fill in all fields."); return; }
    if (password !== confirm) { setError("Passwords do not match."); return; }
    if (password.length < 6) { setError("Password must be at least 6 characters."); return; }
    if (!agreed) { setError("Please agree to the disclaimer to continue."); return; }
    setLoading(true);
    try {
      const cred = await createUserWithEmailAndPassword(auth, email, password);
      await updateProfile(cred.user, { displayName: name });
      router.push("/dashboard");
    } catch (err: any) {
      if (err.code === "auth/email-already-in-use") setError("An account with this email already exists.");
      else setError("Something went wrong. Please try again.");
    } finally { setLoading(false); }
  }

  return (
    <>
      <style>{css}</style>
      <div style={{ minHeight: "100vh", background: C.cream, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'DM Sans', sans-serif", padding: 24, position: "relative", overflow: "hidden" }}>

        <div style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0 }}>
          <div className="drift1" style={{ position: "absolute", top: "5%", right: "8%", width: 380, height: 380, borderRadius: "50%", background: `radial-gradient(circle, ${C.rose}22 0%, transparent 70%)` }} />
          <div className="drift2" style={{ position: "absolute", bottom: "10%", left: "5%", width: 300, height: 300, borderRadius: "50%", background: `radial-gradient(circle, ${C.teal}14 0%, transparent 70%)` }} />
        </div>

        <div style={{ width: "100%", maxWidth: 440, position: "relative", zIndex: 1 }}>
          <div style={{ textAlign: "center", marginBottom: 28, animation: "fadeUp 0.6s cubic-bezier(.16,1,.3,1) both" }}>
            <div onClick={() => router.push("/")} style={{ width: 50, height: 50, borderRadius: 14, background: `linear-gradient(135deg, ${C.teal}, ${C.tealDark})`, display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 12px", boxShadow: `0 8px 20px ${C.teal}44`, cursor: "pointer" }}>
              <span style={{ color: "#fff", fontWeight: 700, fontSize: 18, fontFamily: "'DM Serif Display', serif" }}>Rx</span>
            </div>
            <h1 onClick={() => router.push("/")} style={{ fontFamily: "'DM Serif Display', serif", fontSize: 22, color: C.teal, margin: 0, cursor: "pointer" }}>CascadeRx</h1>
            <p style={{ fontSize: 13, color: C.textLight, marginTop: 4 }}>Free medication safety checker</p>
          </div>

          <div className="card" style={{ background: "#fff", borderRadius: 24, padding: 36, boxShadow: `0 20px 60px rgba(46,125,138,0.12), 0 4px 20px rgba(0,0,0,0.05)`, border: `1px solid rgba(46,125,138,0.08)` }}>
            <h2 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 26, color: C.text, marginBottom: 6 }}>Create your account</h2>
            <p style={{ fontSize: 13, color: C.textLight, marginBottom: 28 }}>Start checking your medications for free</p>

            {error && (
              <div style={{ background: "#FEE2E2", border: "1px solid #FCA5A5", borderRadius: 10, padding: "10px 14px", marginBottom: 20, fontSize: 13, color: "#B91C1C", display: "flex", alignItems: "center", gap: 8 }}>
                <span>⚠</span> {error}
              </div>
            )}

            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {[
                { label: "FULL NAME", type: "text", placeholder: "Jane Smith", value: name, set: setName },
                { label: "EMAIL ADDRESS", type: "email", placeholder: "you@example.com", value: email, set: setEmail },
                { label: "PASSWORD", type: "password", placeholder: "At least 6 characters", value: password, set: setPassword },
                { label: "CONFIRM PASSWORD", type: "password", placeholder: "••••••••", value: confirm, set: setConfirm },
              ].map(f => (
                <div key={f.label}>
                  <label style={{ fontSize: 12, fontWeight: 600, color: C.teal, display: "block", marginBottom: 6, letterSpacing: "0.05em" }}>{f.label}</label>
                  <input className="inp" type={f.type} placeholder={f.placeholder} value={f.value} onChange={e => f.set(e.target.value)} />
                </div>
              ))}
            </div>

            <div style={{ display: "flex", alignItems: "flex-start", gap: 10, margin: "20px 0 24px" }}>
              <input type="checkbox" checked={agreed} onChange={e => setAgreed(e.target.checked)} style={{ marginTop: 3, accentColor: C.teal, width: 14, height: 14, cursor: "pointer", flexShrink: 0 }} />
              <label style={{ fontSize: 12, color: C.textLight, lineHeight: 1.6, cursor: "pointer" }} onClick={() => setAgreed(!agreed)}>
                I understand CascadeRx provides medication safety guidance and is not a substitute for professional medical or pharmacist advice.
              </label>
            </div>

            <button className="btn" onClick={handleSignup} disabled={loading}>
              {loading ? "Creating account..." : "Create free account →"}
            </button>

            <p style={{ textAlign: "center", fontSize: 14, color: C.textLight, marginTop: 20 }}>
              Already have an account?{" "}
              <span onClick={() => router.push("/login")} style={{ color: C.teal, fontWeight: 600, cursor: "pointer" }}>Sign in</span>
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
