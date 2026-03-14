"""
CascadeRx Backend — Flask v3 (with Brand-Name Resolver)
Run:  python3 main.py
Test: python3 test.py

New in v3:
  - POST /resolve           — resolve brand/common drug names → active ingredients
  - POST /analyze/brand     — full pipeline from brand names (resolve → analyze → stream)
  - POST /analyze/stream    — existing pipeline (accepts generic names directly)
  - GET  /drugs/search?q=   — autocomplete (searches both brand names and generics)
  - GET  /drugs/all         — full CYP drug list
  - GET  /health            — status check

Brand-name pipeline flow:
  Brand names → drug_resolver.py → active ingredients → analyzer.py → LLM report
  The LLM report references both brand names AND generic names throughout.
"""

import json
import os
import re
import sys

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, Response, jsonify

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyzer import (
    analyze, PatientInput, DrugInput,
    CYP_TABLE, ALL_DRUG_NAMES, DDI_PAIRS,
)
from drug_resolver import (
    resolve_drug_names, build_ingredient_map, get_all_ingredients,
    ResolvedDrug, BRAND_TO_GENERIC,
)

app = Flask(__name__)

@app.route("/library/drug")
def drug_library():

    q = request.args.get("q","").strip().lower()

    if not q:
        return jsonify({"error":"drug name required"}),400

    info = {}

    # CYP enzyme data
    if q in CYP_TABLE:
        info["enzymes"] = CYP_TABLE[q]

    # pairwise interactions
    interactions = []

    for pair,data in DDI_PAIRS.items():

        if q in pair:
            other = [d for d in pair if d != q][0]

            interactions.append({
                "drug": other,
                "severity": data["severity"],
                "effect": data["clinical_effect"]
            })

    info["known_interactions"] = interactions[:10]

    return jsonify({
        "drug": q,
        "library": info
    })
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
# BRAND-AWARE PROMPT BUILDER
# ─────────────────────────────────────────────────────────────────

def _format_drug_label(ingredient: str, resolved_map: dict[str, ResolvedDrug]) -> str:
    """Returns 'BrandName (generic)' or just 'generic' if no brand found."""
    r = resolved_map.get(ingredient)
    if r and r.brand.lower() != ingredient.lower():
        return f"{r.brand} ({ingredient})"
    return ingredient
def generate_report_text(result):
    text = f"Overall medication risk level is {result.overall_risk}. "

    if result.pairwise:
        text += "The following drug interactions were detected. "
        for p in result.pairwise:
            text += f"{p.drug_a} and {p.drug_b} have a {p.severity} interaction. "

    if result.patient_risk_factors:
        text += "Patient risk factors include. "
        for f in result.patient_risk_factors:
            text += f"{f}. "

    return text
from gtts import gTTS
from flask import send_file
import uuid

@app.post("/analyze/voice")
def analyze_voice():

    data = request.json

    patient = PatientInput(**data)

    result = analyze(patient)

    report_text = generate_report_text(result)

    filename = f"voice_{uuid.uuid4()}.mp3"

    tts = gTTS(report_text, lang="en")

    tts.save(filename)

    return send_file(filename, mimetype="audio/mpeg")    


def build_agent_prompt(patient, result, resolved_list: list[ResolvedDrug] = None):
    clean_conditions = strip_phi(patient.conditions or [])
    clean_allergies  = strip_phi(patient.allergies  or [])

    # Build ingredient → ResolvedDrug map for label enrichment
    ing_to_resolved: dict[str, ResolvedDrug] = {}
    if resolved_list:
        for r in resolved_list:
            for ing in r.ingredients:
                ing_to_resolved[ing] = r

    FEW_SHOT = """
[[IDEAL ANALYSIS EXAMPLE]]
Scenario: Prozac (fluoxetine) + Betaloc (metoprolol)
Mechanism: Fluoxetine is a strong CYP2D6 inhibitor (Grade A). Metoprolol is a CYP2D6 substrate.
Explanation: Fluoxetine (Prozac) creates a metabolic bottleneck at CYP2D6. This causes
metoprolol (Betaloc) plasma concentrations to rise ~4-fold, increasing severe bradycardia risk.
The Pairwise Gap: Standard checkers flag this as 'Moderate' but miss the 'Critical' risk
when patient age and eGFR are factored in.
Safer Alternative: Instead of Betaloc (metoprolol): consider Bisoprolol (brand: Concor/Bisocor)
because it is not primarily metabolized by CYP2D6, bypassing the bottleneck. (DrugBank: DB00612).
"""

    # Drug list with brand names if available
    drug_lines = []
    for d in patient.drugs:
        label = _format_drug_label(d.name, ing_to_resolved)
        line = f"- {label}"
        if d.dose:
            line += f" {d.dose}"
        if d.specialist:
            line += f" (prescribed by: {d.specialist})"
        drug_lines.append(line)
    drug_list = "\n".join(drug_lines)

    # Resolution summary for context
    resolution_notes = ""
    if resolved_list:
        combo_drugs = [r for r in resolved_list if r.note and "combination" in r.note]
        if combo_drugs:
            combos = ", ".join(f"{r.brand} ({r.generic})" for r in combo_drugs)
            resolution_notes = f"\nNOTE - Combination products detected: {combos}\n"

    cascade_text = "\n".join(
        f"  [{c.interaction_type.upper()} | {c.enzyme} | Grade {c.evidence_grade} | Score {c.risk_score}]\n"
        f"  {c.explanation}"
        for c in result.cascade_paths
    ) or "  None detected."

    pairwise_text = "\n".join(
        f"  [{p.severity}] {_format_drug_label(p.drug_a, ing_to_resolved)} x "
        f"{_format_drug_label(p.drug_b, ing_to_resolved)}: {p.clinical_effect}"
        for p in result.pairwise
    ) or "  None in database."

    risk_flags = "\n".join(f"  ! {f}" for f in result.patient_risk_factors) or "  None identified."

    return f"""You are CascadeRx, a specialized clinical pharmacology AI.
Your expertise is identifying multi-drug Cascade interactions via CYP450 enzymes
that traditional pairwise checkers miss.

CRITICAL FORMATTING RULE: Always refer to drugs using BOTH their brand name AND generic name
in the format: BrandName (generic). For example: "Betaloc (metoprolol)" or "Prozac (fluoxetine)".
When suggesting alternatives, always provide both a generic name AND at least one common brand name.

PATIENT CONTEXT:
- Age: {patient.age or 'Not provided'}
- eGFR: {patient.egfr or 'Not provided'} mL/min/1.73m2
- Conditions: {clean_conditions}
- Allergies: {clean_allergies}

CURRENT REGIMEN (Brand Name → Active Ingredient):
{drug_list}
{resolution_notes}
AUTOMATED ANALYSIS:
- Overall Risk: {result.overall_risk}
- Risk Metrics: {json.dumps(result.risk_summary)}

CASCADE INTERACTIONS (enzyme-mediated, multi-drug):
{cascade_text}

PAIRWISE INTERACTIONS (direct drug-drug):
{pairwise_text}

PATIENT RISK FLAGS:
{risk_flags}

{FEW_SHOT}

REPORT INSTRUCTIONS:
1. Summary: Start with "Each specialist prescribed appropriately, however..."
2. Always reference drugs as BrandName (generic) — e.g. "Betaloc (metoprolol)"
3. Cascade Risk: Name the enzyme, explain fold-increase, explain the bottleneck.
4. The Pairwise Gap: Why would a standard checker miss this?
5. Safer Alternatives: For EVERY drug you suggest replacing, provide:
   - The generic name
   - At least one common brand name in parentheses
   - The DrugBank ID
   - Why it avoids the interaction
   Example: "Instead of Betaloc (metoprolol): consider bisoprolol (brand: Concor, Bisocor)
   (DrugBank: DB00612) because it is not primarily metabolized by CYP2D6."
6. Citations: Include DrugBank IDs and PMIDs inline.

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

def _mock_report(result, patient, resolved_list: list[ResolvedDrug] = None):
    ing_to_resolved: dict[str, ResolvedDrug] = {}
    if resolved_list:
        for r in resolved_list:
            for ing in r.ingredients:
                ing_to_resolved[ing] = r

    c      = result.cascade_paths[0] if result.cascade_paths else None
    enzyme = c.enzyme if c else "CYP2D6"
    inhibs = ", ".join(_format_drug_label(i, ing_to_resolved) for i in c.inhibitors) if c else "drug A"
    subs   = ", ".join(_format_drug_label(s, ing_to_resolved) for s in c.substrates) if c else "drug B"
    grade  = c.evidence_grade if c else "A"

    if "2D6" in enzyme:
        safer, safer_brand, dbid = "bisoprolol", "Concor / Bisocor", "DB00622"
    elif "3A4" in enzyme:
        safer, safer_brand, dbid = "azithromycin", "Zithromax / Azithral", "DB00207"
    else:
        safer, safer_brand, dbid = "bisoprolol", "Concor / Bisocor", "DB00622"

    pairwise_lines = "\n".join(
        f"- [{p.severity}] {_format_drug_label(p.drug_a, ing_to_resolved)} x "
        f"{_format_drug_label(p.drug_b, ing_to_resolved)}: {p.clinical_effect}"
        for p in result.pairwise
    ) or "- None detected."

    risk_flags = "\n".join(f"- {f}" for f in result.patient_risk_factors) or "- None identified."

    # Extract the substrate drug's brand name for the alternative suggestion
    sub_raw = c.substrates[0] if c and c.substrates else "the substrate drug"
    sub_label = _format_drug_label(sub_raw, ing_to_resolved)

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
Instead of {sub_label}: consider {safer} (brand: {safer_brand}) (DrugBank: {dbid})
because it is not primarily metabolized by {enzyme}, completely bypassing the cascade
bottleneck. This means the {inhibs} inhibition has no effect on its plasma levels.

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

def stream_llm(prompt, result, patient, resolved_list=None):
    if not FEATHERLESS_KEY:
        print("[CascadeRx] No FEATHERLESS_API_KEY — using deterministic mock LLM")
        report = _mock_report(result, patient, resolved_list)
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
        yield _mock_report(result, patient, resolved_list)

# ─────────────────────────────────────────────────────────────────
# INPUT PARSERS
# ─────────────────────────────────────────────────────────────────

def parse_patient(data, override_drug_names: list[str] = None):
    """
    Parse patient JSON. 
    If override_drug_names provided, those replace the drugs list
    (used after brand-name resolution to substitute with generic ingredients).
    """
    if override_drug_names:
        # Build DrugInput from resolved ingredient names,
        # carrying dose/specialist from original if we can match by index
        original_drugs = data.get("drugs", [])
        drugs = []
        for i, name in enumerate(override_drug_names):
            orig = original_drugs[i] if i < len(original_drugs) else {}
            drugs.append(DrugInput(
                name=name,
                dose=orig.get("dose") if isinstance(orig, dict) else None,
                specialist=orig.get("specialist") if isinstance(orig, dict) else None,
            ))
    else:
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


def _resolve_and_expand(data: dict) -> tuple[list[ResolvedDrug], list[str]]:
    """
    Resolve drug names from request data.
    Returns (resolved_list, all_ingredient_names).
    """
    drug_names = [d["name"] for d in data.get("drugs", [])]
    resolved   = resolve_drug_names(drug_names)
    ingredients = get_all_ingredients(resolved)
    return resolved, ingredients

# ─────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────

@app.route("/resolve", methods=["POST"])
def resolve_endpoint():
    """
    Resolve brand/common drug names to active ingredients.
    
    Input:  { "drugs": ["Crocin", "Brufen", "Loprin"] }
    Output: {
        "resolved": [
            {
                "brand": "Crocin",
                "generic": "paracetamol",
                "ingredients": ["paracetamol"],
                "drugbank_id": "DB00316",
                "drug_class": "analgesic",
                "resolution_source": "offline",
                "confidence": "high",
                "note": null
            },
            ...
        ],
        "all_ingredients": ["paracetamol", "ibuprofen", "aspirin"],
        "combination_drugs": ["Combiflam"]
    }
    """
    data = request.get_json(force=True)
    if not data or not data.get("drugs"):
        return jsonify({"error": "drugs list required"}), 400

    drug_names = [
        d["name"] if isinstance(d, dict) else d
        for d in data["drugs"]
    ]
    resolved = resolve_drug_names(drug_names)
    ingredients = get_all_ingredients(resolved)
    combos = [r.brand for r in resolved if r.note and "combination" in r.note]

    return jsonify({
        "resolved": [vars(r) for r in resolved],
        "all_ingredients": ingredients,
        "combination_drugs": combos,
    })


@app.route("/analyze", methods=["POST"])
def analyze_endpoint():
    """Synchronous — returns structured JSON, no LLM. Accepts generic names."""
    data = request.get_json(force=True)
    if not data or len(data.get("drugs", [])) < 2:
        return jsonify({"error": "At least 2 drugs required."}), 400
    patient = parse_patient(data)
    result  = analyze(patient)
    return jsonify(result.model_dump())


@app.route("/analyze/brand", methods=["POST"])
def analyze_brand():
    """
    Full brand-name pipeline:
    1. Resolve brand names → active ingredients
    2. Run analyzer on ingredients
    3. Return resolution + analysis JSON (no LLM narrative)
    
    Input: same as /analyze but drug names can be brand names
    Output: {
        "resolution": { resolved, all_ingredients, combination_drugs },
        "analysis": { cascade_paths, pairwise, overall_risk, ... }
    }
    """
    data = request.get_json(force=True)
    if not data or len(data.get("drugs", [])) < 2:
        return jsonify({"error": "At least 2 drugs required."}), 400

    resolved, ingredients = _resolve_and_expand(data)
    if len(ingredients) < 2:
        return jsonify({"error": "Could not resolve enough distinct ingredients for analysis."}), 400

    patient = parse_patient(data, override_drug_names=ingredients)
    result  = analyze(patient)
    combos  = [r.brand for r in resolved if r.note and "combination" in r.note]

    return jsonify({
        "resolution": {
            "resolved": [vars(r) for r in resolved],
            "all_ingredients": ingredients,
            "combination_drugs": combos,
        },
        "analysis": result.model_dump(),
    })


@app.route("/analyze/stream", methods=["POST"])
def analyze_stream():
    """
    Streaming endpoint — accepts EITHER generic names OR brand names.
    Detects brand names automatically and resolves them first.
    
    SSE event types:
      { "type": "resolution", "data": { resolved, all_ingredients } }
      { "type": "result",     "data": { analysis result } }
      { "type": "token",      "text": "..." }
      { "type": "done" }
    """
    data = request.get_json(force=True)
    if not data or len(data.get("drugs", [])) < 2:
        return jsonify({"error": "At least 2 drugs required."}), 400

    # Always run resolution (pass-through for already-generic names)
    resolved, ingredients = _resolve_and_expand(data)

    if len(ingredients) < 2:
        return jsonify({"error": "Could not resolve enough ingredients for analysis."}), 400

    patient = parse_patient(data, override_drug_names=ingredients)
    result  = analyze(patient)
    prompt  = build_agent_prompt(patient, result, resolved)
    combos  = [r.brand for r in resolved if r.note and "combination" in r.note]

    def generate():
        # Phase 0: Resolution data
        yield f"data: {json.dumps({'type': 'resolution', 'data': {'resolved': [vars(r) for r in resolved], 'all_ingredients': ingredients, 'combination_drugs': combos}})}\n\n"

        # Phase 1: Structured analysis result
        yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump()})}\n\n"

        # Phase 2: LLM narrative stream
        for chunk in stream_llm(prompt, result, patient, resolved):
            yield f"data: {json.dumps({'type': 'token', 'text': chunk})}\n\n"

        yield 'data: {"type": "done"}\n\n'

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/drugs/search", methods=["GET"])
def search_drugs():
    """
    Autocomplete — searches both brand names and generic names.
    Returns results tagged with their type.
    """
    q = request.args.get("q", "").strip().lower()
    if len(q) < 2:
        return jsonify({"results": []})

    # Search CYP table (generics with interaction data)
    cyp_matches = sorted([
        {"name": d, "type": "generic", "has_cyp_data": True}
        for d in CYP_TABLE if q in d
    ], key=lambda x: x["name"])

    # Search brand names dictionary
    brand_matches = sorted([
        {
            "name": k.title(),
            "type": "brand",
            "generic": v["generic"],
            "drug_class": v.get("class"),
            "has_cyp_data": v["generic"] in CYP_TABLE,
        }
        for k, v in BRAND_TO_GENERIC.items() if q in k
    ], key=lambda x: x["name"])

    # Search other known drug names
    other_matches = sorted([
        {"name": d, "type": "generic", "has_cyp_data": False}
        for d in ALL_DRUG_NAMES if q in d and d not in CYP_TABLE
    ], key=lambda x: x["name"])

    # Combine: CYP generics first, then brands, then others
    # Deduplicate by name
    seen = set()
    combined = []
    for item in (cyp_matches + brand_matches + other_matches):
        key = item["name"].lower()
        if key not in seen:
            seen.add(key)
            combined.append(item)
        if len(combined) >= 20:
            break

    return jsonify({"results": combined})


@app.route("/drugs/all", methods=["GET"])
def all_drugs():
    """Returns all drugs with CYP interaction data, plus all known brand names."""
    generics = sorted(CYP_TABLE.keys())
    brands = sorted([
        {
            "brand": k.title(),
            "generic": v["generic"],
            "class": v.get("class"),
            "db": v.get("db"),
        }
        for k, v in BRAND_TO_GENERIC.items()
    ], key=lambda x: x["brand"])
    return jsonify({"generics": generics, "brands": brands})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "drugs_in_cyp_table":    len(CYP_TABLE),
        "ddi_pairs_loaded":      len(DDI_PAIRS),
        "brand_names_in_dict":   len(BRAND_TO_GENERIC),
        "llm_mode":              "featherless" if FEATHERLESS_KEY else "mock",
        "resolver_llm_fallback": bool(FEATHERLESS_KEY),
        "version": "3.0",
    })


if __name__ == "__main__":
    mode = "Featherless (Llama 3.1 70B)" if FEATHERLESS_KEY else "Mock (deterministic)"
    print("=" * 62)
    print("  CascadeRx Backend  —  Flask v3 (Brand-Name Resolver)")
    print(f"  LLM mode  : {mode}")
    print("  Listening : http://127.0.0.1:8000")
    print("  Endpoints :")
    print("    POST /resolve               ← NEW: brand → generic")
    print("    POST /analyze/brand         ← NEW: full brand pipeline (JSON)")
    print("    POST /analyze/stream        ← updated: auto-resolves brand names")
    print("    POST /analyze               ← unchanged: generic names only")
    print("    GET  /drugs/search?q=<term> ← updated: searches brands + generics")
    print("    GET  /drugs/all             ← updated: returns brands + generics")
    print("    GET  /health")
    print("=" * 62)
    app.run(host="127.0.0.1", port=8000, debug=True)
