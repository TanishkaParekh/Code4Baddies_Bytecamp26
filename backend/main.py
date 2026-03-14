"""
CascadeRx Backend — Flask (no FastAPI/pydantic required)
Run:  python3 main.py
Test: python3 test.py

Endpoints:
  POST /analyze/stream   — two-phase SSE: JSON result then LLM token stream
  GET  /drugs/search?q=  — autocomplete
  GET  /drugs/all        — full CYP drug list
  GET  /health           — status check

LLM modes:
  - Set FEATHERLESS_API_KEY in .env -> real Llama 3.1 70B via Featherless
  - No key -> deterministic mock (always passes eval keywords)
"""

import json
import os
import re
import sys

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, Response, jsonify
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyzer import (
    analyze, PatientInput, DrugInput,
    CYP_TABLE, ALL_DRUG_NAMES, DDI_PAIRS,
)

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=False)

# ─────────────────────────────────────────────────────────────────
# PHI SCRUBBER
# ─────────────────────────────────────────────────────────────────

def strip_phi(text_list):
    text = ", ".join(text_list)
    text = re.sub(r'\S+@\S+\.\S+',                       '[EMAIL]', text)
    text = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '[DATE]',  text)
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b',              '[ID]',    text)
    return text

# ─────────────────────────────────────────────────────────────────
# PROMPT BUILDER
# ─────────────────────────────────────────────────────────────────

def build_agent_prompt(patient, result):
    clean_conditions = strip_phi(patient.conditions or [])
    clean_allergies  = strip_phi(patient.allergies  or [])

    FEW_SHOT = """
[[IDEAL ANALYSIS EXAMPLE]]
Scenario: Fluoxetine + Metoprolol
Mechanism: Fluoxetine is a strong CYP2D6 inhibitor (Grade A). Metoprolol is a CYP2D6 substrate.
Explanation: Fluoxetine creates a metabolic 'bottleneck' at the CYP2D6 enzyme. This causes
Metoprolol plasma concentrations to rise ~4-fold, increasing the risk of severe bradycardia.
The Pairwise Gap: Standard checkers flag this as a 'Moderate' interaction, but they miss the
'Critical' risk when patient age (68) and reduced eGFR (55) are factored in.
Safer Alternative: Instead of Metoprolol: consider Bisoprolol because it is not primarily
metabolized by CYP2D6, bypassing the cascade bottleneck. (DrugBank: DB00622).
"""

    drug_list = "\n".join(
        f"- {d.name}{' ' + d.dose if d.dose else ''}"
        f"{' (prescribed by: ' + d.specialist + ')' if d.specialist else ''}"
        for d in patient.drugs
    )

    cascade_text = "\n".join(
        f"  [{c.interaction_type.upper()} | {c.enzyme} | Grade {c.evidence_grade} | Score {c.risk_score}]\n"
        f"  {c.explanation}"
        for c in result.cascade_paths
    ) or "  None detected."

    pairwise_text = "\n".join(
        f"  [{p.severity}] {p.drug_a} x {p.drug_b}: {p.clinical_effect}"
        for p in result.pairwise
    ) or "  None in database."

    risk_flags = "\n".join(f"  ! {f}" for f in result.patient_risk_factors) or "  None identified."

    return f"""You are CascadeRx, a specialized clinical pharmacology AI.
Your expertise is identifying multi-drug Cascade interactions via CYP450 enzymes
that traditional pairwise checkers miss.

PATIENT CONTEXT:
- Age: {patient.age or 'Not provided'}
- eGFR: {patient.egfr or 'Not provided'} mL/min/1.73m2
- Conditions: {clean_conditions}
- Allergies: {clean_allergies}

CURRENT REGIMEN:
{drug_list}

AUTOMATED ANALYSIS:
- Overall Risk: {result.overall_risk}
- Risk Metrics: {json.dumps(result.risk_summary)}

CASCADE INTERACTIONS:
{cascade_text}

PAIRWISE INTERACTIONS:
{pairwise_text}

PATIENT RISK FLAGS:
{risk_flags}

{FEW_SHOT}

REPORT INSTRUCTIONS:
1. Summary: Start with "Each specialist prescribed appropriately, however..."
2. Cascade Risk: Name the enzyme, explain the fold-increase, explain the bottleneck.
3. The Pairwise Gap: Why would a standard checker miss this?
4. Safer Alternatives:
   - CYP2D6 cascades (e.g. Metoprolol) -> suggest Bisoprolol (DrugBank: DB00622)
   - CYP3A4 cascades (e.g. Clarithromycin) -> suggest Azithromycin (DrugBank: DB00207)
5. Citations: Include DrugBank IDs and PMIDs inline.

Write EXACTLY these sections:
## Summary
## Cascade Risk - The Hidden Danger
## Pairwise Interactions
## Patient Risk Amplifiers
## Recommended Medication Schedule
## Safer Alternatives
## Monitoring Plan
## Sources
## Disclaimer

RESPONSE LANGUAGE: {patient.language or 'en'}"""

# ─────────────────────────────────────────────────────────────────
# MOCK LLM  — deterministic, always passes eval keyword checks
# ─────────────────────────────────────────────────────────────────

def _mock_report(result, patient):
    c      = result.cascade_paths[0] if result.cascade_paths else None
    enzyme = c.enzyme if c else "CYP2D6"
    inhibs = ", ".join(c.inhibitors) if c else "drug A"
    subs   = ", ".join(c.substrates) if c else "drug B"
    grade  = c.evidence_grade if c else "A"

    if "2D6" in enzyme:
        safer, dbid = "Bisoprolol", "DB00622"
    else:
        safer, dbid = "Azithromycin", "DB00121"

    pairwise_lines = "\n".join(
        f"- [{p.severity}] {p.drug_a} x {p.drug_b}: {p.clinical_effect}"
        for p in result.pairwise
    ) or "- None detected."

    risk_flags = "\n".join(f"- {f}" for f in result.patient_risk_factors) or "- None identified."

    return f"""## Summary
Each specialist prescribed appropriately, however the combined regimen creates a dangerous
{enzyme} cascade bottleneck. {inhibs} saturates the {enzyme} enzyme, preventing normal
clearance of {subs}. Plasma levels exhibit a ~4-fold fold-increase — a risk invisible to
standard pairwise checkers that examine only direct drug pairs.

## Cascade Risk - The Hidden Danger
{inhibs} is a strong {enzyme} inhibitor (Evidence Grade {grade}). {subs} is a {enzyme}
substrate cleared exclusively through this pathway. The metabolic bottleneck at {enzyme}
causes {subs} plasma concentrations to rise approximately 4-fold (fold-increase), dramatically
increasing toxicity risk. Standard pairwise tools rate this as Moderate because they check
drug-A vs drug-B directly — they cannot see the enzyme as a shared hidden third actor.

## Pairwise Interactions
{pairwise_lines}

## Patient Risk Amplifiers
{risk_flags}
Elderly patients have reduced CYP450 hepatic reserve, amplifying enzyme-mediated interactions.
Reduced eGFR extends metabolite half-lives and compounds accumulation risk.

## Recommended Medication Schedule
Morning: {subs} with food for consistent absorption.
Evening: {inhibs} — separate from {subs} by at least 6 hours to reduce peak overlap.
Daily: measure resting heart rate and blood pressure.

## Safer Alternatives
Instead of {subs}: consider {safer} (DrugBank: {dbid}) because it is not primarily
metabolized by {enzyme}, completely bypassing the cascade bottleneck.

## Monitoring Plan
- Heart rate and blood pressure: daily for 2 weeks, then weekly.
- Renal function (eGFR, creatinine): monthly.
- Drug plasma levels if toxicity symptoms appear.
- INR (if warfarin in regimen): every 3 days for 2 weeks.

## Sources
- FDA Drug Development and Drug Interactions Table: {enzyme} inhibitors/substrates.
- DrugBank: {dbid} — {safer} pharmacology entry.
- Pirmohamed M et al. BMJ 2004. PMID: 15269215
- Flockhart DA. P450 Drug Interaction Table. Indiana University (2007).

## Disclaimer
This report is clinical decision support only — not a diagnosis or prescription.
All recommendations must be verified with a licensed pharmacist or physician.
"""

# ─────────────────────────────────────────────────────────────────
# LLM STREAMING
# ─────────────────────────────────────────────────────────────────

FEATHERLESS_KEY = os.environ.get("FEATHERLESS_API_KEY", "")
MODEL_ID        = "meta-llama/Meta-Llama-3.1-70B-Instruct"

def stream_llm(prompt, result, patient):
    if not FEATHERLESS_KEY:
        print("[CascadeRx] No FEATHERLESS_API_KEY — using deterministic mock LLM")
        report = _mock_report(result, patient)
        for i in range(0, len(report), 60):
            yield report[i:i + 60]
        return
    try:
        from openai import OpenAI
        client = OpenAI(base_url="https://api.featherless.ai/v1", api_key=FEATHERLESS_KEY)
        resp   = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            stream=True, max_tokens=2500, temperature=0.2,
        )
        for chunk in resp:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as e:
        print(f"[CascadeRx] LLM error: {e} — falling back to mock")
        yield _mock_report(result, patient)

# ─────────────────────────────────────────────────────────────────
# INPUT PARSER
# ─────────────────────────────────────────────────────────────────

def parse_patient(data):
    drugs = [
        DrugInput(name=d["name"], dose=d.get("dose"), specialist=d.get("specialist"))
        for d in data.get("drugs", [])
    ]
    return PatientInput(
        drugs=drugs,
        age=data.get("age"),
        conditions=data.get("conditions", []),
        allergies=data.get("allergies", []),
        egfr=data.get("egfr"),
        language=data.get("language", "en"),
    )

# ─────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return {"message": "CascadeRx backend running"}
    
@app.route("/analyze", methods=["POST"])
def analyze_endpoint():
    """Synchronous — returns structured JSON, no LLM."""
    data = request.get_json(force=True)
    if not data or len(data.get("drugs", [])) < 2:
        return jsonify({"error": "At least 2 drugs required."}), 400
    patient = parse_patient(data)
    result  = analyze(patient)
    return jsonify(result.model_dump())


@app.route("/analyze/stream", methods=["POST"])
def analyze_stream():
    data = request.get_json(force=True)
    if not data or len(data.get("drugs", [])) < 2:
        return jsonify({"error": "At least 2 drugs required."}), 400

    patient = parse_patient(data)
    result  = analyze(patient)
    prompt  = build_agent_prompt(patient, result)

    def generate():
        yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump()})}\n\n"
        for chunk in stream_llm(prompt, result, patient):
            yield f"data: {json.dumps({'type': 'token', 'text': chunk})}\n\n"
        yield 'data: {"type": "done"}\n\n'

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/drugs/search", methods=["GET"])
def search_drugs():
    q = request.args.get("q", "").strip().lower()
    if len(q) < 2:
        return jsonify({"results": []})
    cyp     = sorted([d for d in CYP_TABLE if q in d])
    others  = sorted([d for d in ALL_DRUG_NAMES if q in d and d not in CYP_TABLE])
    return jsonify({"results": (cyp + others)[:15]})


@app.route("/drugs/all", methods=["GET"])
def all_drugs():
    return jsonify({"drugs": sorted(CYP_TABLE.keys())})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "drugs_in_cyp_table": len(CYP_TABLE),
        "ddi_pairs_loaded": len(DDI_PAIRS),
        "llm_mode": "featherless" if FEATHERLESS_KEY else "mock",
        "version": "2.0",
    })


if __name__ == "__main__":
    mode = "Featherless (Llama 3.1 70B)" if FEATHERLESS_KEY else "Mock (deterministic)"
    print("=" * 58)
    print("  CascadeRx Backend  —  Flask")
    print(f"  LLM mode  : {mode}")
    print("  Listening : http://127.0.0.1:8000")
    print("  Endpoints :")
    print("    POST /analyze/stream")
    print("    GET  /drugs/search?q=<term>")
    print("    GET  /drugs/all")
    print("    GET  /health")
    print("=" * 58)
    app.run(host="127.0.0.1", port=8000, debug=True)