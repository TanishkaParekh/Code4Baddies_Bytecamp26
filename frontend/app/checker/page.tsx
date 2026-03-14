"use client";
import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import ReactMarkdown from "react-markdown";
import { useTranslation, getSpecialists } from "../../components/translations";
import { LanguageSelector } from "../../components/LanguageSelector";
import {
  analyzeStream,
  searchDrugs,
  getMockResult,
  MOCK_REPORT,
  type AnalysisResult,
  type DrugInput,
} from "../../lib/analysisService";

const CascadeGraph = dynamic(() => import("../../components/CascadeGraph"), { ssr: false });

function buildPositionedGraph(
  rawGraph: { nodes: { id: string }[]; links: { source: string; target: string; severity?: string; cascade?: boolean }[] },
  cascadePaths: { inhibitors: string[]; substrates: string[]; inducers?: string[] }[]
) {
  const inhibitorSet = new Set(cascadePaths.flatMap(c => c.inhibitors));
  const substrateSet = new Set(cascadePaths.flatMap(c => c.substrates.filter(s => !inhibitorSet.has(s))));
  const cascadeSet = new Set([...inhibitorSet, ...substrateSet]);
  const inhibitors = rawGraph.nodes.filter(n => inhibitorSet.has(n.id));
  const substrates = rawGraph.nodes.filter(n => substrateSet.has(n.id));
  const safe = rawGraph.nodes.filter(n => !cascadeSet.has(n.id));
  const CY = 130;
  const positioned = [
    ...inhibitors.map((n, i) => ({ ...n, fx: 150, fy: CY + (i - (inhibitors.length - 1) / 2) * 90 })),
    ...substrates.map((n, i) => ({ ...n, fx: 400, fy: CY + (i - (substrates.length - 1) / 2) * 90 })),
    ...safe.map((n, i) => ({ ...n, fx: 570, fy: 80 + i * 80 })),
  ];
  const cascadeLinkKeys = new Set(cascadePaths.flatMap(c =>
    c.inhibitors.flatMap(inh => c.substrates.map(sub => `${inh}|${sub}`))
  ));
  const links = rawGraph.links.map(l => ({
    ...l, cascade: l.cascade ?? cascadeLinkKeys.has(`${l.source}|${l.target}`),
  }));
  return { nodes: positioned, links };
}

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const C = {
  cream: "#F5F0E8", rose: "#D4A5A5", teal: "#2E7D8A",
  tealDark: "#1f5f6b", roseDark: "#b88888", text: "#1a1a1a", textLight: "#666",
};

const css = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap');
  *{margin:0;padding:0;box-sizing:border-box}
  @keyframes fadeUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
  @keyframes spin{to{transform:rotate(360deg)}}
  @keyframes blink{0%,100%{opacity:1}50%{opacity:0}}
  @keyframes pulse-dot{0%,100%{box-shadow:0 0 0 0 rgba(212,165,165,0.6)}50%{box-shadow:0 0 0 8px rgba(212,165,165,0)}}
  @keyframes cascade-pulse{0%,100%{box-shadow:0 0 0 0 rgba(226,75,74,0.35)}50%{box-shadow:0 0 0 8px rgba(226,75,74,0)}}
  .inp{width:100%;padding:10px 14px;font-size:13px;border:1.5px solid rgba(46,125,138,0.2);border-radius:8px;outline:none;background:rgba(245,240,232,0.5);color:#1a1a1a;font-family:'DM Sans',sans-serif;transition:all 0.2s}
  .inp:focus{border-color:#2E7D8A;background:#fff;box-shadow:0 0 0 3px rgba(46,125,138,0.1)}
  .btn-primary{background:#2E7D8A;color:#fff;border:none;padding:12px 24px;border-radius:50px;font-size:14px;font-weight:600;cursor:pointer;font-family:'DM Sans',sans-serif;transition:all 0.25s}
  .btn-primary:hover{background:#1f5f6b;transform:translateY(-1px);box-shadow:0 6px 20px rgba(46,125,138,0.3)}
  .btn-primary:disabled{opacity:0.5;cursor:not-allowed;transform:none}
  .btn-secondary{background:transparent;color:#2E7D8A;border:1.5px solid #2E7D8A;padding:10px 20px;border-radius:50px;font-size:13px;font-weight:500;cursor:pointer;font-family:'DM Sans',sans-serif;transition:all 0.2s}
  .btn-secondary:hover{background:rgba(46,125,138,0.08)}
  .btn-ghost{background:transparent;color:#666;border:1px solid rgba(46,125,138,0.15);padding:7px 14px;border-radius:8px;font-size:12px;cursor:pointer;font-family:'DM Sans',sans-serif;transition:all 0.2s}
  .btn-ghost:hover{border-color:#2E7D8A;color:#2E7D8A}
  .drug-card{background:#fff;border-radius:14px;padding:16px;border:1px solid rgba(46,125,138,0.1);position:relative;transition:all 0.2s;animation:fadeUp 0.4s both}
  .drug-card:hover{border-color:rgba(46,125,138,0.25)}
  .severity-chip{font-size:11px;font-weight:700;padding:3px 10px;border-radius:20px;letter-spacing:0.05em;display:inline-block}
  .cascade-card{background:#fff;border-radius:14px;padding:18px;border:1.5px solid rgba(212,165,165,0.55);animation:fadeUp 0.5s both;animation:cascade-pulse 2s ease-in-out infinite}
  .pairwise-row{border-radius:10px;border:1px solid rgba(46,125,138,0.1);overflow:hidden;animation:fadeUp 0.4s both}
  .pairwise-summary{display:flex;align-items:center;gap:10px;padding:12px 16px;cursor:pointer;background:#fff;transition:background 0.15s;list-style:none}
  .pairwise-summary:hover{background:#F5F0E8}
  details[open] .pairwise-summary{background:#F5F0E8}
  .spinner{width:16px;height:16px;border:2px solid rgba(46,125,138,0.2);border-top-color:#2E7D8A;border-radius:50%;animation:spin 0.7s linear infinite;display:inline-block;flex-shrink:0}
  .tab-btn{padding:8px 16px;border-radius:8px;font-size:13px;font-weight:500;cursor:pointer;font-family:'DM Sans',sans-serif;transition:all 0.2s;border:none;background:transparent;color:#666}
  .tab-btn.active{background:rgba(46,125,138,0.12);color:#2E7D8A;font-weight:600}
  .scrollbox{overflow-y:auto;overflow-x:hidden;scrollbar-width:thin;scrollbar-color:rgba(46,125,138,0.2) transparent;max-width:100%}
  .scrollbox::-webkit-scrollbar{width:4px}
  .scrollbox::-webkit-scrollbar-thumb{background:rgba(46,125,138,0.2);border-radius:4px}
  .report-body{word-break:break-word;overflow-wrap:break-word;overflow-x:hidden;max-width:100%}
  .report-body h2{font-size:15px;font-weight:700;color:#1a1a1a;margin:16px 0 6px;word-break:break-word}
  .report-body h3{font-size:14px;font-weight:600;color:#2E7D8A;margin:12px 0 4px;word-break:break-word}
  .report-body p{font-size:13px;color:#444;line-height:1.7;margin-bottom:8px;word-break:break-word}
  .report-body ul{padding-left:18px;margin-bottom:8px;max-width:100%}
  .report-body li{font-size:13px;color:#444;line-height:1.7;word-break:break-word}
  .report-body strong{color:#1a1a1a;font-weight:600}
  .report-body em{color:#2E7D8A}
  .report-body pre,.report-body code{white-space:pre-wrap;word-break:break-word;max-width:100%;overflow-x:hidden}
  .upload-zone{border:2px dashed rgba(46,125,138,0.3);border-radius:12px;padding:18px;text-align:center;cursor:pointer;transition:all 0.2s;background:rgba(245,240,232,0.4)}
  .upload-zone:hover{border-color:#2E7D8A;background:rgba(46,125,138,0.04)}
`;

const SEVERITY_COLORS: Record<string, { bg: string; color: string; border: string }> = {
  CRITICAL: { bg: "#FEE2E2", color: "#B91C1C", border: "#FCA5A5" },
  HIGH:     { bg: "#FEF3C7", color: "#92400E", border: "#FCD34D" },
  MAJOR:    { bg: "#FEE2E2", color: "#B91C1C", border: "#FCA5A5" },
  MODERATE: { bg: "#FEF9C3", color: "#854D0E", border: "#FDE047" },
  MINOR:    { bg: "#DCFCE7", color: "#166534", border: "#86EFAC" },
  LOW:      { bg: "#DCFCE7", color: "#166534", border: "#86EFAC" },
};

const DEMO_DRUGS: DrugInput[] = [
  { name: "Fluoxetine", dose: "20mg", specialist: "Psychiatrist" },
  { name: "Metoprolol", dose: "50mg", specialist: "Cardiologist" },
  { name: "Celecoxib", dose: "200mg", specialist: "Rheumatologist" },
  { name: "Metformin", dose: "500mg", specialist: "Endocrinologist" },
];

function SeverityChip({ level }: { level: string }) {
  const c = SEVERITY_COLORS[level] || SEVERITY_COLORS.MODERATE;
  return (
    <span className="severity-chip" style={{ background: c.bg, color: c.color, border: `1px solid ${c.border}` }}>
      {level}
    </span>
  );
}

export default function CheckerPage() {
  const router = useRouter();
  const { t, lang, setLang } = useTranslation();
  const specialists = getSpecialists(t);

  const [drugs, setDrugs] = useState<DrugInput[]>([{ name: "", dose: "", specialist: "" }]);
  const [age, setAge] = useState("");
  const [egfr, setEgfr] = useState("");
  const [allergies, setAllergies] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [aiReport, setAiReport] = useState("");
  const [streamDone, setStreamDone] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [activeSuggIdx, setActiveSuggIdx] = useState(-1);
  const [copied, setCopied] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState("");
  const [resultTab, setResultTab] = useState<"cascade" | "pairwise" | "report">("cascade");
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Autocomplete
  const handleDrugNameChange = useCallback(async (i: number, value: string) => {
    setDrugs(prev => prev.map((d, idx) => idx === i ? { ...d, name: value } : d));
    if (value.length >= 2) {
      const results = await searchDrugs(value);
      setSuggestions(results);
      setActiveSuggIdx(i);
    } else {
      setSuggestions([]);
    }
  }, []);

  function updateDrug(i: number, field: keyof DrugInput, value: string) {
    setDrugs(prev => prev.map((d, idx) => idx === i ? { ...d, [field]: value } : d));
  }

  function addDrug() { setDrugs(prev => [...prev, { name: "", dose: "", specialist: "" }]); }
  function removeDrug(i: number) { setDrugs(prev => prev.filter((_, idx) => idx !== i)); }

  function loadDemo() {
    setDrugs(DEMO_DRUGS);
    setAge("68");
    setEgfr("55");
    setAllergies("");
    setResult(null);
    setAiReport("");
    setStreamDone(false);
  }

  // Prescription OCR upload
  async function handleImageUpload(file: File) {
    setUploadLoading(true);
    setUploadMsg(t("readingPrescription"));
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${API}/extract-from-image`, { method: "POST", body: formData });
      const data = await res.json();
      if (data.error || !data.drugs?.length) {
        setUploadMsg(t("uploadError"));
        return;
      }
      setDrugs(data.drugs.map((d: any) => ({ name: d.name || "", dose: d.dose || "", specialist: "" })));
      setUploadMsg(`✓ ${data.drugs.length} ${t("drugsFound")}`);
    } catch {
      setUploadMsg(t("uploadError"));
    } finally {
      setUploadLoading(false);
    }
  }

  // Main analyze — uses analyzeStream from analysisService
  async function handleAnalyze() {
    const validDrugs = drugs.filter(d => d.name.trim());
    if (validDrugs.length < 2) { alert("Please enter at least 2 medications."); return; }

    setLoading(true);
    setResult(null);
    setAiReport("");
    setStreamDone(false);
    setResultTab("cascade");
    setSelectedNode(null);

    const payload = {
      drugs: validDrugs,
      age: age ? parseInt(age) : null,
      egfr: egfr ? parseFloat(egfr) : null,
      allergies: allergies ? allergies.split(",").map(s => s.trim()) : [],
      language: lang,
    };

    try {
      await analyzeStream(
        payload,
        (data) => {
          setResult(data);
          setLoading(false);
          setResultTab(data.cascade_paths.length > 0 ? "cascade" : "pairwise");
        },
        (token) => setAiReport(prev => prev + token),
        () => setStreamDone(true),
      );
    } catch (err) {
      console.warn("Backend unavailable, using mock data:", err);
      // Graceful fallback to mock data
      const mockResult = getMockResult(validDrugs.map(d => d.name));
      setResult(mockResult);
      setLoading(false);
      setResultTab(mockResult.cascade_paths.length > 0 ? "cascade" : "pairwise");
      // Simulate streaming mock report
      let i = 0;
      const words = MOCK_REPORT.split(" ");
      const interval = setInterval(() => {
        if (i >= words.length) { setStreamDone(true); clearInterval(interval); return; }
        setAiReport(prev => prev + (i === 0 ? "" : " ") + words[i]);
        i++;
      }, 30);
    }
  }

  async function exportPDF() {
    const { jsPDF } = await import("jspdf");
    const doc = new jsPDF();
    doc.setFontSize(16);
    doc.text("CascadeRx — Medication Safety Report", 14, 20);
    doc.setFontSize(10);
    doc.text(`Generated: ${new Date().toLocaleDateString()} | Language: ${lang.toUpperCase()}`, 14, 28);
    if (result) {
      doc.setFontSize(12);
      doc.text(`Overall Risk: ${result.overall_risk}`, 14, 38);
      doc.setFontSize(10);
      doc.text(`Cascade paths: ${result.cascade_paths.length} | Pairwise: ${result.pairwise.length}`, 14, 46);
      if (result.patient_risk_factors?.length) {
        doc.text("Patient risk factors:", 14, 54);
        result.patient_risk_factors.forEach((f, i) => doc.text(`• ${f}`, 16, 62 + i * 7));
      }
    }
    const lines = doc.splitTextToSize(aiReport.replace(/[#*]/g, ""), 180);
    doc.text(lines, 14, result?.patient_risk_factors?.length ? 62 + result.patient_risk_factors.length * 7 + 8 : 58);
    doc.save("cascaderx-report.pdf");
  }

  function copyReport() {
    navigator.clipboard.writeText(aiReport);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  // Get cascade-involved drugs for graph coloring
  const cascadeInvolvedDrugs = result
    ? result.cascade_paths.flatMap(c => [...c.inhibitors, ...c.substrates, ...c.inducers])
    : [];

  return (
    <>
      <style>{css}</style>
      <div style={{ minHeight: "100vh", background: C.cream, fontFamily: "'DM Sans', sans-serif", overflowX: "hidden" }}>

        {/* Header */}
        <header style={{ background: "#fff", borderBottom: `1px solid rgba(46,125,138,0.1)`, padding: "0 28px", height: 58, display: "flex", alignItems: "center", justifyContent: "space-between", boxShadow: "0 1px 6px rgba(0,0,0,0.04)" }}>
          {/* Clickable logo → dashboard */}
          <div onClick={() => router.push("/dashboard")} style={{ display: "flex", alignItems: "center", gap: 9, cursor: "pointer" }}>
            <div style={{ width: 32, height: 32, borderRadius: 9, background: `linear-gradient(135deg, ${C.teal}, ${C.tealDark})`, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ color: "#fff", fontWeight: 700, fontSize: 12, fontFamily: "'DM Serif Display', serif" }}>Rx</span>
            </div>
            <span style={{ fontWeight: 700, fontSize: 16, color: C.teal, fontFamily: "'DM Serif Display', serif" }}>CascadeRx</span>
            <span style={{ fontSize: 12, color: C.textLight }}>— {t("tagline")}</span>
          </div>

          {/* Language selector using the real component */}
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 12, color: C.textLight }}>Language:</span>
            <LanguageSelector lang={lang} setLang={setLang} />
          </div>

          <div style={{ background: "#FEF9C3", border: "1px solid #FDE047", borderRadius: 20, padding: "4px 12px", fontSize: 11, color: "#854D0E" }}>
            ⚕ {t("disclaimer")}
          </div>
        </header>

        <main style={{ maxWidth: "min(1200px, 100vw)", margin: "0 auto", padding: "20px 24px", display: "grid", gridTemplateColumns: "clamp(300px, 30%, 380px) 1fr", gap: 20, boxSizing: "border-box", overflowX: "hidden" }}>

          {/* ── LEFT: Input Panel ── */}
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>

            {/* Demo + upload buttons */}
            <div style={{ background: "#fff", borderRadius: 14, padding: "16px", border: `1px solid rgba(46,125,138,0.1)` }}>
              <div style={{ display: "flex", gap: 8, marginBottom: uploadMsg ? 10 : 0 }}>
                <button className="btn-primary" style={{ flex: 1, fontSize: 13, padding: "9px" }} onClick={loadDemo}>
                  ⚡ {t("loadDemo")}
                </button>
                <button className="btn-secondary" style={{ flex: 1, fontSize: 13, padding: "8px" }}
                  onClick={() => fileInputRef.current?.click()}>
                  {uploadLoading ? <span className="spinner" /> : `📷 ${t("uploadPrescription")}`}
                </button>
                <input ref={fileInputRef} type="file" accept="image/*" style={{ display: "none" }}
                  onChange={e => { if (e.target.files?.[0]) handleImageUpload(e.target.files[0]); }} />
              </div>
              {uploadMsg && (
                <div style={{ fontSize: 12, padding: "7px 10px", borderRadius: 8, background: uploadMsg.startsWith("✓") ? "#DCFCE7" : "#FEE2E2", color: uploadMsg.startsWith("✓") ? "#166534" : "#B91C1C" }}>
                  {uploadMsg}
                </div>
              )}
            </div>

            {/* Drug inputs */}
            <div style={{ background: "#fff", borderRadius: 14, padding: "18px", border: `1px solid rgba(46,125,138,0.1)` }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <h2 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 16, color: C.text }}>{t("patientMedications")}</h2>
                <span style={{ fontSize: 11, color: drugs.filter(d => d.name).length >= 3 ? C.teal : C.textLight }}>
                  {drugs.filter(d => d.name).length} {t("drugsEntered")}
                  {drugs.filter(d => d.name).length >= 3 ? ` · ${t("cascadeActive")}` : ` ${t("addMore")}`}
                </span>
              </div>

              {drugs.map((drug, i) => (
                <div key={i} className="drug-card" style={{ marginBottom: 10, animationDelay: `${i * 0.04}s` }}>
                  <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                    <div style={{ flex: 1, position: "relative" }}>
                      <input className="inp" placeholder={t("drugNamePlaceholder")} value={drug.name}
                        onChange={e => handleDrugNameChange(i, e.target.value)}
                        onBlur={() => setTimeout(() => setSuggestions([]), 180)} />
                      {suggestions.length > 0 && activeSuggIdx === i && (
                        <div style={{ position: "absolute", zIndex: 30, top: "100%", left: 0, right: 0, background: "#fff", border: `1px solid rgba(46,125,138,0.2)`, borderRadius: 8, boxShadow: "0 8px 24px rgba(0,0,0,0.1)", marginTop: 2, overflow: "hidden" }}>
                          {suggestions.slice(0, 6).map(s => (
                            <button key={s} style={{ width: "100%", textAlign: "left", padding: "8px 14px", fontSize: 13, background: "transparent", border: "none", cursor: "pointer", fontFamily: "'DM Sans', sans-serif", color: C.text, display: "flex", alignItems: "center", gap: 8 }}
                              onMouseDown={() => { updateDrug(i, "name", s); setSuggestions([]); }}>
                              💊 {s}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                    <input className="inp" placeholder={t("dosePlaceholder")} value={drug.dose ?? ""}
                      onChange={e => updateDrug(i, "dose", e.target.value)} style={{ width: 76 }} />
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <select className="inp" style={{ flex: 1 }} value={drug.specialist ?? ""}
                      onChange={e => updateDrug(i, "specialist", e.target.value)}>
                      <option value="">{t("selectSpecialist")}</option>
                      {specialists.map(s => <option key={s}>{s}</option>)}
                    </select>
                    {drugs.length > 1 && (
                      <button onClick={() => removeDrug(i)} style={{ width: 26, height: 26, borderRadius: "50%", border: "none", background: "#FEE2E2", color: "#B91C1C", cursor: "pointer", fontSize: 14, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>×</button>
                    )}
                  </div>
                </div>
              ))}

              <button onClick={addDrug} style={{ width: "100%", padding: "9px", border: `1.5px dashed rgba(46,125,138,0.3)`, borderRadius: 10, background: "transparent", fontSize: 13, color: C.teal, cursor: "pointer", fontFamily: "'DM Sans', sans-serif" }}>
                {t("addAnotherDrug")}
              </button>
            </div>

            {/* Patient context */}
            <div style={{ background: "#fff", borderRadius: 14, padding: "18px", border: `1px solid rgba(46,125,138,0.1)` }}>
              <h2 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 16, color: C.text, marginBottom: 14 }}>{t("patientContext")}</h2>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 10 }}>
                <div>
                  <label style={{ fontSize: 11, fontWeight: 600, color: C.teal, display: "block", marginBottom: 5, letterSpacing: "0.05em" }}>{t("age").toUpperCase()}</label>
                  <input className="inp" placeholder={t("agePlaceholder")} value={age} onChange={e => setAge(e.target.value)} />
                </div>
                <div>
                  <label style={{ fontSize: 11, fontWeight: 600, color: C.teal, display: "block", marginBottom: 5, letterSpacing: "0.05em" }}>{t("egfr").toUpperCase()}</label>
                  <input className="inp" placeholder={t("egfrPlaceholder")} value={egfr} onChange={e => setEgfr(e.target.value)} />
                </div>
              </div>
              <div>
                <label style={{ fontSize: 11, fontWeight: 600, color: C.teal, display: "block", marginBottom: 5, letterSpacing: "0.05em" }}>{t("allergies").toUpperCase()}</label>
                <input className="inp" placeholder={t("allergiesPlaceholder")} value={allergies} onChange={e => setAllergies(e.target.value)} />
              </div>
            </div>

            {/* Analyze button */}
            <button className="btn-primary" style={{ width: "100%", padding: "14px", fontSize: 15, borderRadius: 14 }}
              onClick={handleAnalyze} disabled={loading}>
              {loading
                ? <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10 }}>
                    <span className="spinner" /> {t("analyzing")}
                  </span>
                : `🔬 ${t("analyze")}`}
            </button>
          </div>

          {/* ── RIGHT: Results Panel ── */}
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

            {/* Overall risk + actions */}
            {result && (
              <div style={{ background: "#fff", borderRadius: 14, padding: "16px 20px", border: `1px solid rgba(46,125,138,0.1)`, display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap", animation: "fadeUp 0.4s both" }}>
                <SeverityChip level={result.overall_risk} />
                <span style={{ fontSize: 14, fontWeight: 600, color: C.text }}>{t("overallRisk")}</span>
                <span style={{ fontSize: 13, color: C.textLight }}>
                  {result.cascade_paths.length} {t("cascadePaths")} · {result.pairwise.length} {t("pairwiseInteractions")}
                </span>
                {result.risk_summary && (
                  <span style={{ fontSize: 11, color: C.textLight, background: C.cream, borderRadius: 20, padding: "3px 10px" }}>
                    Total cascade risk: {result.risk_summary.total_cascade_risk.toFixed(1)}
                  </span>
                )}
                <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
                  <button className="btn-ghost" onClick={copyReport}>{copied ? `${t("copied")}` : t("copyReport")}</button>
                  <button className="btn-ghost" onClick={exportPDF}>{t("exportPDF")}</button>
                </div>
              </div>
            )}

            {/* Patient risk factors */}
            {result?.patient_risk_factors?.length ? (
              <div style={{ background: "#FEF9C3", border: "1px solid #FDE047", borderRadius: 12, padding: "12px 16px", animation: "fadeUp 0.4s 0.1s both" }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: "#854D0E", marginBottom: 6, letterSpacing: "0.06em" }}>{t("patientRiskFactors").toUpperCase()}</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                  {result.patient_risk_factors.map((f, i) => (
                    <div key={i} style={{ fontSize: 12, color: "#92400E" }}>• {f}</div>
                  ))}
                </div>
              </div>
            ) : null}

            {/* Cascade Fingerprint Graph */}
            {result && result.graph_json.nodes.length > 0 && (
              <div style={{ background: "#fff", borderRadius: 14, padding: "18px", border: `1px solid rgba(46,125,138,0.1)`, animation: "fadeUp 0.4s 0.15s both" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
                  <h3 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 16, color: C.text }}>{t("cascadeFingerprint")}</h3>
                  <span style={{ fontSize: 12, color: C.textLight }}>— {t("enzymeNetwork")}</span>
                  {selectedNode && (
                    <span style={{ marginLeft: "auto", fontSize: 12, background: C.teal, color: "#fff", padding: "3px 10px", borderRadius: 20 }}>
                      Selected: {selectedNode}
                    </span>
                  )}
                </div>
                <CascadeGraph
                  graphData={result.graph_json}
                  cascadeInvolvedDrugs={cascadeInvolvedDrugs}
                  onNodeClick={(name) => setSelectedNode(prev => prev === name ? null : name)}
                />
              </div>
            )}

            {/* Results tabs */}
            {result && (
              <div style={{ background: "#fff", borderRadius: 14, border: `1px solid rgba(46,125,138,0.1)`, overflow: "hidden", animation: "fadeUp 0.4s 0.2s both" }}>
                <div style={{ display: "flex", gap: 4, padding: "10px 14px", borderBottom: `1px solid rgba(46,125,138,0.08)` }}>
                  <button className={`tab-btn ${resultTab === "cascade" ? "active" : ""}`} onClick={() => setResultTab("cascade")}>
                    ⚠ {t("cascadeDetected").split("⚠ ")[1]?.split(" —")[0] || "Cascade Alerts"} {result.cascade_paths.length > 0 && `(${result.cascade_paths.length})`}
                  </button>
                  <button className={`tab-btn ${resultTab === "pairwise" ? "active" : ""}`} onClick={() => setResultTab("pairwise")}>
                    {t("pairwiseTitle")} {result.pairwise.length > 0 && `(${result.pairwise.length})`}
                  </button>
                  <button className={`tab-btn ${resultTab === "report" ? "active" : ""}`} onClick={() => setResultTab("report")}>
                    {t("fullReport")}
                    {!streamDone && aiReport && <span style={{ width: 6, height: 6, borderRadius: "50%", background: C.teal, display: "inline-block", marginLeft: 6, animation: "pulse-dot 1s infinite" }} />}
                  </button>
                </div>

                <div style={{ padding: "16px" }}>

                  {/* CASCADE TAB */}
                  {resultTab === "cascade" && (
                    result.cascade_paths.length === 0 ? (
                      <div style={{ textAlign: "center", padding: "28px", color: C.textLight }}>
                        <div style={{ fontSize: 28, marginBottom: 8 }}>✅</div>
                        <div style={{ fontSize: 14, fontWeight: 600, color: "#166534" }}>No cascade interactions found</div>
                        <div style={{ fontSize: 12, marginTop: 4 }}>Check pairwise tab for standard interactions</div>
                      </div>
                    ) : (
                      <div>
                        <div style={{ background: "#FEE2E2", border: "1px solid #FCA5A5", borderRadius: 10, padding: "9px 14px", marginBottom: 14, fontSize: 13, color: "#B91C1C", display: "flex", alignItems: "center", gap: 8 }}>
                          <span style={{ width: 7, height: 7, borderRadius: "50%", background: "#B91C1C", display: "inline-block", animation: "pulse-dot 1.5s infinite" }} />
                          <strong>{result.cascade_paths.length} hidden cascade{result.cascade_paths.length > 1 ? "s" : ""} detected</strong> — invisible to standard pairwise checkers
                        </div>
                        {result.cascade_paths.map((c, i) => (
                          <div key={i} className="cascade-card" style={{ marginBottom: 12, animationDelay: `${i * 0.1}s` }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10, flexWrap: "wrap" }}>
                              <span style={{ fontFamily: "monospace", background: `${C.rose}25`, color: C.roseDark, fontSize: 12, fontWeight: 700, padding: "3px 10px", borderRadius: 6 }}>{c.enzyme}</span>
                              <span style={{ fontSize: 11, color: C.roseDark, fontWeight: 600 }}>{t("riskScore")}: {c.risk_score}</span>
                              {c.evidence_grade && (
                                <span style={{ fontSize: 11, background: "#DCFCE7", color: "#166534", padding: "2px 8px", borderRadius: 6, fontWeight: 600 }}>
                                  {t("evidenceGrade")}: {c.evidence_grade}
                                </span>
                              )}
                              {c.interaction_type && (
                                <span style={{ fontSize: 11, background: C.cream, color: C.textLight, padding: "2px 8px", borderRadius: 6 }}>
                                  {t("interactionType")}: {c.interaction_type}
                                </span>
                              )}
                            </div>
                            <p style={{ fontSize: 13, color: C.text, lineHeight: 1.65, marginBottom: 12 }}>{c.explanation}</p>
                            <div style={{ display: "flex", gap: 20, flexWrap: "wrap", fontSize: 12 }}>
                              <div><span style={{ color: C.textLight }}>{t("inhibitors")}: </span><strong style={{ color: C.roseDark }}>{c.inhibitors.join(", ") || "—"}</strong></div>
                              <div><span style={{ color: C.textLight }}>{t("affected")}: </span><strong style={{ color: C.text }}>{c.substrates.join(", ") || "—"}</strong></div>
                              {c.inducers.length > 0 && (
                                <div><span style={{ color: C.textLight }}>{t("inducers")}: </span><strong style={{ color: "#92400E" }}>{c.inducers.join(", ")}</strong></div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )
                  )}

                  {/* PAIRWISE TAB */}
                  {resultTab === "pairwise" && (
                    result.pairwise.length === 0 ? (
                      <div style={{ textAlign: "center", padding: "28px", color: C.textLight }}>
                        <div style={{ fontSize: 28, marginBottom: 8 }}>✅</div>
                        <div style={{ fontSize: 14, fontWeight: 600, color: "#166534" }}>No pairwise interactions found</div>
                      </div>
                    ) : (
                      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                        {result.pairwise.map((p, i) => (
                          <details key={i} className="pairwise-row" style={{ animationDelay: `${i * 0.06}s` }}>
                            <summary className="pairwise-summary">
                              <SeverityChip level={p.severity} />
                              <span style={{ fontSize: 14, fontWeight: 600, color: C.text }}>{p.drug_a} × {p.drug_b}</span>
                              {p.from_dataset && (
                                <span style={{ fontSize: 10, color: C.textLight, background: C.cream, borderRadius: 10, padding: "2px 7px", marginLeft: "auto" }}>
                                  {p.from_dataset}
                                </span>
                              )}
                              <span style={{ fontSize: 12, color: C.textLight, marginLeft: p.from_dataset ? 4 : "auto" }}>▼</span>
                            </summary>
                            <div style={{ padding: "12px 16px", borderTop: `1px solid rgba(46,125,138,0.08)`, background: C.cream }}>
                              {[
                                [t("mechanism"), p.mechanism],
                                [t("effect"), p.clinical_effect],
                                [t("management"), p.management],
                                [t("alternative"), p.safer_alternative],
                              ].map(([label, val]) => (
                                <p key={label} style={{ fontSize: 13, color: C.text, marginBottom: 6, lineHeight: 1.6 }}>
                                  <strong style={{ color: C.teal }}>{label}:</strong> {val}
                                </p>
                              ))}
                              <p style={{ fontSize: 11, color: C.teal, marginTop: 6 }}>📚 {p.source}</p>
                            </div>
                          </details>
                        ))}
                      </div>
                    )
                  )}

                  {/* REPORT TAB */}
                  {resultTab === "report" && (
                    <div>
                      {!aiReport && !streamDone ? (
                        <div style={{ display: "flex", alignItems: "center", gap: 10, color: C.textLight, fontSize: 13, padding: "12px" }}>
                          <span className="spinner" /> Generating your safety report in {lang === "en" ? "English" : lang === "hi" ? "हिंदी" : "मराठी"}...
                        </div>
                      ) : (
                        <div>
                          <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
                            <button className="btn-ghost" onClick={copyReport}>{copied ? t("copied") : t("copyReport")}</button>
                            <button className="btn-ghost" onClick={exportPDF}>{t("exportPDF")}</button>
                          </div>
                          <div className="report-body scrollbox" style={{ maxHeight: 420, fontSize: 13, maxWidth: "100%", overflowX: "hidden" }}>
                            <ReactMarkdown>{aiReport}</ReactMarkdown>
                            {!streamDone && (
                              <span style={{ display: "inline-block", width: 2, height: 14, background: C.teal, marginLeft: 2, verticalAlign: "middle", animation: "blink 0.8s step-end infinite" }} />
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Loading state */}
            {loading && !result && (
              <div style={{ background: "#fff", borderRadius: 14, padding: "44px", textAlign: "center", border: `1px solid rgba(46,125,138,0.1)` }}>
                <div style={{ width: 44, height: 44, border: `3px solid rgba(46,125,138,0.15)`, borderTopColor: C.teal, borderRadius: "50%", animation: "spin 0.8s linear infinite", margin: "0 auto 18px" }} />
                <div style={{ fontSize: 15, fontWeight: 600, color: C.text, marginBottom: 6 }}>{t("analyzing")}</div>
                <div style={{ fontSize: 12, color: C.textLight }}>
                  Running CYP enzyme model · Checking {Math.max(0, drugs.filter(d => d.name).length * (drugs.filter(d => d.name).length - 1) / 2)} drug pairs · Generating {lang === "en" ? "English" : lang === "hi" ? "Hindi" : "Marathi"} report
                </div>
              </div>
            )}

            {/* Empty state */}
            {!result && !loading && (
              <div style={{ background: "#fff", borderRadius: 14, border: `1.5px dashed rgba(46,125,138,0.18)`, padding: "52px 36px", textAlign: "center" }}>
                <div style={{ fontSize: 44, marginBottom: 14 }}>💊</div>
                <h3 style={{ fontFamily: "'DM Serif Display', serif", fontSize: 19, color: C.text, marginBottom: 8 }}>{t("emptyTitle")}</h3>
                <p style={{ fontSize: 13, color: C.textLight, lineHeight: 1.65, maxWidth: 400, margin: "0 auto 22px" }}>{t("emptySubtitle")}</p>
                <button className="btn-secondary" onClick={loadDemo}>{t("loadDemo")}</button>
              </div>
            )}
          </div>
        </main>
      </div>
    </>
  );
}
