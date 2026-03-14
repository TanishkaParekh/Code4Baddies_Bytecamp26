"""
CascadeRx — Analyzer Engine v3
Loads real DDI datasets at startup:
  - DDI_2_0.json        → primary pairwise (10+ entries, full clinical detail)
  - ddinter_downloads_code_A.csv → fallback severity (optional, 56k pairs)
  - db_drug_interactions_csv.zip → DrugBank name autocomplete (optional)

CYP450 table imported from cyp_table.py
"""

import csv
import json
import os
import zipfile
from itertools import combinations
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from cyp_table import CYP_TABLE

# ─────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────

DATA_DIR     = Path(os.environ.get("CASCADERX_DATA_DIR", "./data"))
DDI2_PATH    = DATA_DIR / "DDI_2_0.json"
DDINTER_PATH = DATA_DIR / "ddinter_downloads_code_A.csv"
DRUGBANK_ZIP = DATA_DIR / "db_drug_interactions_csv.zip"

# ─────────────────────────────────────────────────────────────────
# DATASET LOADERS
# ─────────────────────────────────────────────────────────────────

_SEV_MAP = {
    "Major": "MAJOR", "Moderate": "MODERATE", "Minor": "MINOR",
    "major": "MAJOR", "moderate": "MODERATE", "minor": "MINOR",
}


def _load_ddi2(path: Path) -> dict:
    if not path.exists():
        print(f"[CascadeRx] WARNING: {path} not found — using empty DDI2 pairs")
        return {}
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)["ddi_database"]
    pairs = {}
    for e in raw:
        a = e["drug_a"].strip().lower()
        b = e["drug_b"].strip().lower()
        pairs[frozenset([a, b])] = {
            "severity":          _SEV_MAP.get(e["severity"], "MODERATE"),
            "mechanism":         e["mechanism"],
            "clinical_effect":   e["clinical_effect"],
            "safer_alternative": e["safer_alternative"],
            "management":        e["clinical_management"],
            "source":            e["reference"][:200],
            "_from_dataset":     "DDI_2_0",
        }
    print(f"[CascadeRx] Loaded {len(pairs)} pairs from DDI_2_0.json")
    return pairs


def _load_ddinter(path: Path) -> dict:
    if not path.exists():
        print(f"[CascadeRx] INFO: {path} not found — DDInter fallback disabled (optional)")
        return {}
    pairs = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sev_raw = row.get("Level", "").strip()
            sev = _SEV_MAP.get(sev_raw)
            if not sev or sev_raw == "Unknown":
                continue
            a = row["Drug_A"].strip().lower()
            b = row["Drug_B"].strip().lower()
            if not a or not b:
                continue
            key = frozenset([a, b])
            if key not in pairs:
                pairs[key] = {
                    "severity":          sev,
                    "mechanism":         "See DDInter database for interaction mechanism details.",
                    "clinical_effect":   f"{sev.title()} interaction reported.",
                    "safer_alternative": "Consult prescriber for alternatives.",
                    "management":        "Review with prescriber. Refer to DDInter for guidance.",
                    "source":            "DDInter Database (ddinter.scbdd.com)",
                    "_from_dataset":     "DDInter",
                }
    print(f"[CascadeRx] Loaded {len(pairs)} fallback pairs from DDInter")
    return pairs


def _load_drugbank_names(zip_path: Path) -> set:
    names: set = set()
    if not zip_path.exists():
        print(f"[CascadeRx] INFO: {zip_path} not found — DrugBank autocomplete disabled (optional)")
        return names
    try:
        with zipfile.ZipFile(zip_path) as z:
            csv_name = z.namelist()[0]
            with z.open(csv_name) as f:
                reader = csv.reader(line.decode("utf-8", errors="replace") for line in f)
                next(reader)
                for row in reader:
                    if len(row) >= 2:
                        names.add(row[0].strip().lower())
                        names.add(row[1].strip().lower())
    except Exception as exc:
        print(f"[CascadeRx] WARNING: Could not load DrugBank zip: {exc}")
    print(f"[CascadeRx] Loaded {len(names)} drug names from DrugBank")
    return names


def build_ddi_pairs() -> dict:
    ddinter = _load_ddinter(DDINTER_PATH)
    ddi2    = _load_ddi2(DDI2_PATH)
    merged  = {**ddinter, **ddi2}   # DDI2 overwrites DDInter on overlap
    print(f"[CascadeRx] Total merged DDI pairs: {len(merged)}")
    return merged


# ── Build at import time ─────────────────────────────────────────
DDI_PAIRS:      dict = build_ddi_pairs()
DRUGBANK_NAMES: set  = _load_drugbank_names(DRUGBANK_ZIP)
ALL_DRUG_NAMES: set  = set(CYP_TABLE.keys()) | DRUGBANK_NAMES

# ─────────────────────────────────────────────────────────────────
# PYDANTIC MODELS
# ─────────────────────────────────────────────────────────────────

class DrugInput(BaseModel):
    name: str
    dose: Optional[str] = None
    specialist: Optional[str] = None

    def model_post_init(self, __context):
        self.name = self.name.strip().lower()


class PatientInput(BaseModel):
    drugs: list[DrugInput]
    age: Optional[int] = None
    conditions: Optional[list[str]] = []
    allergies: Optional[list[str]] = []
    egfr: Optional[float] = None
    language: Optional[str] = "en"


class CascadePath(BaseModel):
    enzyme: str
    inhibitors: list[str]
    substrates: list[str]
    inducers: list[str]
    risk_score: float
    evidence_grade: str
    interaction_type: str
    explanation: str


class PairwiseInteraction(BaseModel):
    drug_a: str
    drug_b: str
    severity: str
    mechanism: str
    clinical_effect: str
    management: str
    safer_alternative: str
    source: str
    from_dataset: str


class AnalysisResult(BaseModel):
    cascade_paths: list[CascadePath]
    pairwise: list[PairwiseInteraction]
    overall_risk: str
    graph_json: dict
    risk_summary: dict
    patient_risk_factors: list[str]


# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────

def _enzyme_list(entries: list) -> list[str]:
    return [e[0] if isinstance(e, tuple) else e for e in entries]


def _best_grade(drug: str, enzyme: str, relation: str) -> str:
    entries = CYP_TABLE.get(drug, {}).get(relation, [])
    for e in entries:
        if isinstance(e, tuple) and e[0] == enzyme:
            return e[1]
    return "C"


# ─────────────────────────────────────────────────────────────────
# CASCADE ENGINE
# ─────────────────────────────────────────────────────────────────

ENZYME_WEIGHTS = {
    "CYP2D6": 2.5, "CYP2C9": 2.5, "CYP3A4": 2.0,
    "CYP2C19": 2.0, "CYP1A2": 1.5, "CYP2C8": 1.2,
}
EVIDENCE_SCORE = {"A": 1.0, "B": 0.7, "C": 0.4}


def _patient_multiplier(patient: PatientInput) -> float:
    mult = 1.0
    if patient.age and patient.age >= 65:
        mult += 0.3
    if patient.egfr:
        if patient.egfr < 30:
            mult += 0.7
        elif patient.egfr <= 45:   # fix: include eGFR=45 (CKD stage 3b boundary)
            mult += 0.4
    conditions_lower = [c.lower() for c in (patient.conditions or [])]
    if any(c in conditions_lower for c in ["heart failure", "liver disease", "cirrhosis"]):
        mult += 0.4
    return round(mult, 2)


def find_cascade_paths(drugs: list[str], patient: Optional[PatientInput] = None) -> list[CascadePath]:
    pt_mult = _patient_multiplier(patient) if patient else 1.0
    cascades = []

    all_enzymes: set[str] = set()
    for d in drugs:
        info = CYP_TABLE.get(d, {})
        all_enzymes.update(_enzyme_list(info.get("inhibits", [])))
        all_enzymes.update(_enzyme_list(info.get("induces", [])))
        all_enzymes.update(info.get("substrate_of", []))

    for enzyme in all_enzymes:
        inhibitors = [d for d in drugs if enzyme in _enzyme_list(CYP_TABLE.get(d, {}).get("inhibits", []))]
        inducers   = [d for d in drugs if enzyme in _enzyme_list(CYP_TABLE.get(d, {}).get("induces", []))]
        substrates = [d for d in drugs if enzyme in CYP_TABLE.get(d, {}).get("substrate_of", [])]

        real_subs_inh = [s for s in substrates if s not in inhibitors]
        real_subs_ind = [s for s in substrates if s not in inducers]
        weight = ENZYME_WEIGHTS.get(enzyme, 1.0)

        # Inhibition cascade — substrate levels RISE → toxicity
        if inhibitors and real_subs_inh:
            grade = min(
                [_best_grade(d, enzyme, "inhibits") for d in inhibitors],
                key=lambda g: EVIDENCE_SCORE.get(g, 0),
                default="C",
            )
            risk = round(
                len(inhibitors) * len(real_subs_inh) * weight * EVIDENCE_SCORE[grade] * pt_mult, 2
            )
            note = (
                f" Risk amplified by patient eGFR {patient.egfr}."
                if patient and patient.egfr and patient.egfr <= 45
                else ""
            )
            cascades.append(CascadePath(
                enzyme=enzyme,
                inhibitors=inhibitors,
                substrates=real_subs_inh,
                inducers=[],
                risk_score=risk,
                evidence_grade=grade,
                interaction_type="inhibition",
                explanation=(
                    f"{', '.join(inhibitors)} inhibit(s) {enzyme}, blocking clearance of "
                    f"{', '.join(real_subs_inh)}. Plasma levels RISE — accumulation risk. "
                    f"Evidence grade: {grade}.{note}"
                ),
            ))

        # Induction cascade — substrate levels DROP → treatment failure
        if inducers and real_subs_ind:
            grade = min(
                [_best_grade(d, enzyme, "induces") for d in inducers],
                key=lambda g: EVIDENCE_SCORE.get(g, 0),
                default="C",
            )
            risk = round(
                len(inducers) * len(real_subs_ind) * weight * EVIDENCE_SCORE[grade] * pt_mult * 0.8, 2
            )
            cascades.append(CascadePath(
                enzyme=enzyme,
                inhibitors=[],
                inducers=inducers,
                substrates=real_subs_ind,
                risk_score=risk,
                evidence_grade=grade,
                interaction_type="induction",
                explanation=(
                    f"{', '.join(inducers)} induce(s) {enzyme}, accelerating clearance of "
                    f"{', '.join(real_subs_ind)}. Plasma levels DROP — subtherapeutic risk. "
                    f"Evidence grade: {grade}."
                ),
            ))

        # Competition — multiple substrates, no inhibitor
        elif len(real_subs_inh) >= 2 and not inhibitors:
            risk = round(len(real_subs_inh) * weight * 0.6 * pt_mult, 2)
            cascades.append(CascadePath(
                enzyme=enzyme,
                inhibitors=[],
                substrates=real_subs_inh,
                inducers=[],
                risk_score=risk,
                evidence_grade="B",
                interaction_type="competition",
                explanation=(
                    f"Multiple drugs compete for {enzyme}: {', '.join(real_subs_inh)}. "
                    f"Enzyme saturation can slow clearance of all substrates."
                ),
            ))

    return sorted(cascades, key=lambda x: x.risk_score, reverse=True)


# ─────────────────────────────────────────────────────────────────
# PAIRWISE CHECK
# ─────────────────────────────────────────────────────────────────

def check_pairwise(drugs: list[str]) -> list[PairwiseInteraction]:
    results = []
    for a, b in combinations(drugs, 2):
        key = frozenset([a, b])
        if key in DDI_PAIRS:
            d = DDI_PAIRS[key]
            results.append(PairwiseInteraction(
                drug_a=a, drug_b=b,
                severity=d["severity"],
                mechanism=d["mechanism"],
                clinical_effect=d["clinical_effect"],
                management=d["management"],
                safer_alternative=d["safer_alternative"],
                source=d["source"],
                from_dataset=d.get("_from_dataset", "unknown"),
            ))
    order = {"MAJOR": 0, "MODERATE": 1, "MINOR": 2}
    return sorted(results, key=lambda x: order.get(x.severity, 3))


# ─────────────────────────────────────────────────────────────────
# GRAPH BUILDER
# ─────────────────────────────────────────────────────────────────

def build_graph_json(
    drugs: list[str],
    cascades: list[CascadePath],
    pairwise: list[PairwiseInteraction],
) -> dict:
    nodes = [{"id": d, "group": "drug", "label": d.title()} for d in drugs]
    links = []

    enzyme_nodes = {c.enzyme for c in cascades}
    nodes += [{"id": e, "group": "enzyme", "label": e} for e in enzyme_nodes]

    for c in cascades:
        for inh in c.inhibitors:
            links.append({
                "source": inh, "target": c.enzyme, "type": "inhibits",
                "severity": "MAJOR" if c.risk_score >= 3 else "MODERATE",
                "evidence": c.evidence_grade, "cascade": True,
            })
        for ind in c.inducers:
            links.append({
                "source": ind, "target": c.enzyme, "type": "induces",
                "severity": "MODERATE", "evidence": c.evidence_grade, "cascade": True,
            })
        for sub in c.substrates:
            links.append({
                "source": c.enzyme, "target": sub, "type": "substrate",
                "severity": "MAJOR" if c.risk_score >= 3 else "MODERATE",
                "evidence": c.evidence_grade, "cascade": True,
            })

    for p in pairwise:
        links.append({
            "source": p.drug_a, "target": p.drug_b, "type": "direct",
            "severity": p.severity, "evidence": "A", "cascade": False,
        })

    return {"nodes": nodes, "links": links}


# ─────────────────────────────────────────────────────────────────
# PATIENT RISK FLAGS
# ─────────────────────────────────────────────────────────────────

def get_patient_risk_factors(patient: PatientInput) -> list[str]:
    flags = []
    if patient.age and patient.age >= 65:
        flags.append(f"Age {patient.age}: reduced hepatic reserve, polypharmacy sensitivity")
    if patient.egfr:
        if patient.egfr < 30:
            flags.append(f"eGFR {patient.egfr}: severe renal impairment — metformin contraindicated")
        elif patient.egfr <= 45:
            flags.append(f"eGFR {patient.egfr}: moderate-severe renal impairment — dose reduction required")
        elif patient.egfr < 60:
            flags.append(f"eGFR {patient.egfr}: moderate renal impairment — monitor drug levels")
    conditions_lower = [c.lower() for c in (patient.conditions or [])]
    if "heart failure" in conditions_lower:
        flags.append("Heart failure: NSAIDs contraindicated — worsen fluid retention and cardiac output")
    if any(c in conditions_lower for c in ["liver disease", "cirrhosis"]):
        flags.append("Hepatic impairment: CYP450 activity reduced — all hepatically cleared drugs accumulate")
    if "diabetes" in conditions_lower:
        diab_worseners = {"furosemide", "prednisolone", "dexamethasone", "hydrochlorothiazide"}
        if any(d.name in diab_worseners for d in patient.drugs):
            flags.append("Diabetes + diuretic/corticosteroid: hyperglycaemia risk — monitor glucose")
    return flags


# ─────────────────────────────────────────────────────────────────
# RISK CALCULATOR
# ─────────────────────────────────────────────────────────────────

def calculate_overall_risk(
    cascades: list[CascadePath],
    pairwise: list[PairwiseInteraction],
    patient: Optional[PatientInput] = None,
) -> tuple[str, dict]:
    has_major    = any(p.severity == "MAJOR" for p in pairwise)
    high_cascade = any(c.risk_score >= 3.0 for c in cascades)
    grade_a      = any(c.evidence_grade == "A" for c in cascades)

    counts = {
        "major_pairwise":      sum(1 for p in pairwise if p.severity == "MAJOR"),
        "moderate_pairwise":   sum(1 for p in pairwise if p.severity == "MODERATE"),
        "minor_pairwise":      sum(1 for p in pairwise if p.severity == "MINOR"),
        "cascade_inhibition":  sum(1 for c in cascades if c.interaction_type == "inhibition"),
        "cascade_induction":   sum(1 for c in cascades if c.interaction_type == "induction"),
        "cascade_competition": sum(1 for c in cascades if c.interaction_type == "competition"),
        "total_cascade_risk":  round(sum(c.risk_score for c in cascades), 2),
    }

    if (has_major and high_cascade) or counts["major_pairwise"] >= 2:
        level = "CRITICAL"
    elif has_major or (high_cascade and grade_a):
        level = "HIGH"
    elif cascades or pairwise:
        level = "MODERATE"
    else:
        level = "LOW"

    # Bump for vulnerable patients
    if patient and level in ("MODERATE", "HIGH"):
        if (patient.egfr and patient.egfr <= 45) or (patient.age and patient.age >= 75):
            level = {"MODERATE": "HIGH", "HIGH": "CRITICAL"}.get(level, level)

    return level, counts


# ─────────────────────────────────────────────────────────────────
# MASTER FUNCTION
# ─────────────────────────────────────────────────────────────────

def analyze(patient: PatientInput) -> AnalysisResult:
    drugs         = [d.name for d in patient.drugs]
    cascades      = find_cascade_paths(drugs, patient)
    pairwise      = check_pairwise(drugs)
    level, counts = calculate_overall_risk(cascades, pairwise, patient)
    graph_json    = build_graph_json(drugs, cascades, pairwise)
    risk_factors  = get_patient_risk_factors(patient)

    return AnalysisResult(
        cascade_paths=cascades,
        pairwise=pairwise,
        overall_risk=level,
        graph_json=graph_json,
        risk_summary=counts,
        patient_risk_factors=risk_factors,
    )