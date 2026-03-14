"""
CascadeRx Backend — FastAPI
Run: uvicorn main:app --reload
Requires: ANTHROPIC_API_KEY in environment
"""
import re

def strip_phi(text_list: list[str]) -> str:
    """Combines list to string and scrubs potential PHI."""
    text = ", ".join(text_list)
    # Scrub Emails
    text = re.sub(r'\S+@\S+\.\S+', '[EMAIL]', text)
    # Scrub Dates (DOBs)
    text = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '[DATE]', text)
    # Scrub potential SSNs
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[ID]', text)
    return text

LANGUAGE_INSTRUCTIONS = {
    "en": "Write the report in English.",
    "es": "Escriba el informe en español.",
    "fr": "Rédigez le rapport en français.",
    "hi": "रिपोर्ट हिंदी में लिखें (Hindi).",
    "de": "Schreiben Sie den Bericht auf Deutsch."
}

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
import os
import anthropic

from analyzer import (
    PatientInput, AnalysisResult,
    analyze, CYP_TABLE, ALL_DRUG_NAMES,
)

app = FastAPI(title="CascadeRx API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ─────────────────────────────────────────────────────────────────
# AI PROMPT BUILDER
# ─────────────────────────────────────────────────────────────────
'''
def build_agent_prompt(patient: PatientInput, result: AnalysisResult) -> str:
    drug_list = "\n".join(
        f"  - {d.name}{' ' + d.dose if d.dose else ''}"
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

    return f"""You are CascadeRx, a clinical pharmacology AI specialising in polypharmacy risk. \
You identify complex multi-drug interaction risks that standard pairwise checkers miss.

PATIENT PROFILE:
  Age: {patient.age or 'not provided'}
  eGFR: {patient.egfr or 'not provided'} mL/min/1.73m2
  Conditions: {', '.join(patient.conditions) if patient.conditions else 'not specified'}
  Allergies: {', '.join(patient.allergies) if patient.allergies else 'none reported'}

PRESCRIBED MEDICATIONS (from multiple specialists):
{drug_list}

AUTOMATED ANALYSIS — OVERALL RISK: {result.overall_risk}

PATIENT-SPECIFIC RISK FLAGS:
{risk_flags}

CASCADE INTERACTIONS (enzyme-mediated, multi-drug):
{cascade_text}

PAIRWISE INTERACTIONS (known direct DDI):
{pairwise_text}

RISK COUNTS: {json.dumps(result.risk_summary)}

YOUR TASK: Write a structured clinical report with EXACTLY these sections:

## Summary
One paragraph starting with "Each specialist prescribed appropriately, however..." \
Frame the cascade finding as the hidden systemic risk.

## Cascade Risk — The Hidden Danger
Explain mechanistically how the cascade works. Name the enzyme, the inhibitor/inducer, \
and what drug accumulates or becomes subtherapeutic. Explain why pairwise tools missed it.

## Pairwise Interactions
For each: [MAJOR] or [MODERATE] chip, mechanism in one sentence, clinical effect, what to monitor.

## Patient Risk Amplifiers
Explain how this patient's age/renal function/conditions make the interactions worse.

## Recommended Medication Schedule
A concrete Morning / Afternoon / Evening / Night schedule with specific timing rationale \
(e.g. "take warfarin at 6pm — stable absorption, away from antacids").

## Safer Alternatives
For each MAJOR or cascade interaction: name the specific safer drug with rationale. \
Format: "Instead of [drug]: consider [alternative] because [mechanism reason]."

## Monitoring Plan
Specific tests, frequency, and threshold values. Example: \
"Check INR every 3 days for 2 weeks after starting amiodarone."

## Sources
Cite specific FDA DDI Tables, DrugBank IDs (e.g. DB00318), or PubMed PMIDs for each interaction.

## Disclaimer
This is clinical decision support — not a diagnosis. Verify with a licensed pharmacist or physician.

Be precise. Always explain WHY mechanistically. Do not hedge excessively."""

'''

def build_agent_prompt(patient: PatientInput, result: AnalysisResult) -> str:
    
    # Pre-processing: Strip PHI and prepare lists (H11-H14 integration)
    # Note: Ensure the strip_phi function is defined in main.py or utils.py
    clean_conditions = strip_phi(patient.conditions or [])
    clean_allergies = strip_phi(patient.allergies or [])
    
    # 1. FEW-SHOT EXAMPLE: Teaches Claude the "CascadeRx Tone" and "Pairwise Gap" logic
    FEW_SHOT_EXAMPLE = """
    [[IDEAL ANALYSIS EXAMPLE]]
    Scenario: Fluoxetine + Metoprolol
    Mechanism: Fluoxetine is a strong CYP2D6 inhibitor (Grade A). Metoprolol is a CYP2D6 substrate.
    Explanation: Fluoxetine creates a metabolic 'bottleneck' at the CYP2D6 enzyme. This causes Metoprolol 
    plasma concentrations to rise ~4-fold, increasing the risk of severe bradycardia. 
    The Pairwise Gap: Standard checkers flag this as a 'Moderate' interaction, but they miss the 
    'Critical' risk created when the patient's age (68) and reduced eGFR (55) are factored in.
    Safer Alternative: Instead of Metoprolol: consider Bisoprolol because it is not primarily 
    metabolized by CYP2D6, bypassing the cascade bottleneck. (DrugBank: DB00622).
    """

    # 2. DATA PREPARATION: Format the drug list for the prompt
    drug_list = "\n".join([
        f"- {d.name}{' ' + d.dose if d.dose else ''}"
        f"{' (prescribed by: ' + d.specialist + ')' if d.specialist else ''}"
        for d in patient.drugs
    ])
    
    # 3. CONSTRUCTING THE FINAL PROMPT
    return f"""You are CascadeRx, a specialized clinical pharmacology AI. \
Your expertise is in identifying multi-drug 'Cascade' interactions involving CYP450 enzymes \
that traditional pairwise checkers miss.

PATIENT CONTEXT:
- Age: {patient.age or 'Not provided'}
- eGFR: {patient.egfr or 'Not provided'} mL/min/1.73m2
- Conditions: {clean_conditions}
- Allergies: {clean_allergies}

CURRENT REGIMEN (Multiple Specialists):
{drug_list}

AUTOMATED ANALYSIS DATA:
- Overall Risk: {result.overall_risk}
- Cascade Paths: {result.cascade_paths}
- Pairwise DDIs: {result.pairwise}
- Patient Risk Flags: {result.patient_risk_factors}
- Risk Metrics: {json.dumps(result.risk_summary)}

{FEW_SHOT_EXAMPLE}

REPORT INSTRUCTIONS:
1. **Summary**: Start with: "Each specialist prescribed appropriately, however..." Explain the systemic cascade risk.
2. **Mechanics**: For every cascade, name the enzyme (e.g., CYP2D6) and explain the fold-increase in drug levels.
3. **The Pairwise Gap**: Explicitly state why a standard checker would miss this specific multi-drug interaction.
4. **Safer Alternatives**: 
    - For CYP2D6 cascades (e.g., Metoprolol): Suggest Bisoprolol.
    - For CYP3A4 cascades (e.g., Clarithromycin): Suggest Azithromycin.
5. **Citations**: Cite specific DrugBank IDs (e.g., DB00622) and PMIDs inline for every interaction.

## Summary
## Cascade Risk — The Hidden Danger
## Pairwise Interactions
## Patient Risk Amplifiers
## Recommended Medication Schedule
## Safer Alternatives
## Monitoring Plan
## Sources
## Disclaimer

RESPONSE LANGUAGE: {patient.language or 'en'}
    """

# ─────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_endpoint(patient: PatientInput):
    """Run full cascade + pairwise analysis. Returns structured JSON."""
    if len(patient.drugs) < 2:
        raise HTTPException(status_code=400, detail="At least 2 drugs required.")
    return analyze(patient)


@app.post("/analyze/stream")
async def analyze_stream(patient: PatientInput):
    """
    Two-phase streaming endpoint:
    1. Sends structured JSON result immediately as first SSE event
    2. Streams AI clinical report token by token
    """
    if len(patient.drugs) < 2:
        raise HTTPException(status_code=400, detail="At least 2 drugs required.")

    result = analyze(patient)
    prompt = build_agent_prompt(patient, result)

    async def generate():
        # Phase 1: send structured data immediately so frontend can render graph
        yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump()})}\n\n"

        # Phase 2: stream AI report
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {json.dumps({'type': 'token', 'text': text})}\n\n"

        yield "data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/drugs/search")
async def search_drugs(q: str = ""):
    """Autocomplete — CYP table drugs first, then full DrugBank name set (85k)."""
    q_lower = q.strip().lower()
    if not q_lower or len(q_lower) < 2:
        return {"results": []}
    cyp_matches   = sorted([d for d in CYP_TABLE.keys() if q_lower in d])
    other_matches = sorted([d for d in ALL_DRUG_NAMES if q_lower in d and d not in CYP_TABLE])
    return {"results": (cyp_matches + other_matches)[:15]}


@app.get("/drugs/all")
async def all_drugs():
    """Return full drug list for frontend selector."""
    return {"drugs": sorted(CYP_TABLE.keys())}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "drugs_in_cyp_table": len(CYP_TABLE),
        "version": "2.0",
    }
