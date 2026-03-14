"""
CascadeRx — Drug Name Resolver v1
Converts brand/common/trade drug names → active ingredient(s) via LLM.

Uses Featherless (Llama 3.1 70B) if key is set, otherwise falls back to a
curated offline dictionary of ~200 common brand names.

Pipeline:
  resolve_drug_names(["Crocin", "Brufen", "Loprin"])
  → [
      ResolvedDrug(brand="Crocin",   generic="paracetamol", ingredients=["paracetamol"]),
      ResolvedDrug(brand="Brufen",   generic="ibuprofen",   ingredients=["ibuprofen"]),
      ResolvedDrug(brand="Loprin",   generic="aspirin",     ingredients=["aspirin"]),
    ]
"""

import json
import os
import re
from dataclasses import dataclass, field
from typing import Optional

# ─────────────────────────────────────────────────────────────────
# DATA MODEL
# ─────────────────────────────────────────────────────────────────

@dataclass
class ResolvedDrug:
    brand: str                       # original name user entered
    generic: str                     # primary active ingredient (lowercase)
    ingredients: list[str] = field(default_factory=list)  # all active ingredients
    drugbank_id: Optional[str] = None
    drug_class: Optional[str] = None
    resolution_source: str = "offline"  # "llm" | "offline" | "passthrough"
    confidence: str = "high"         # "high" | "medium" | "low"
    note: Optional[str] = None       # e.g. "combination product"

    def __post_init__(self):
        self.generic = self.generic.strip().lower()
        self.ingredients = [i.strip().lower() for i in self.ingredients]
        if not self.ingredients:
            self.ingredients = [self.generic]

# ─────────────────────────────────────────────────────────────────
# OFFLINE DICTIONARY  (~200 common brand → generic mappings)
# Organised by therapeutic class for easy maintenance.
# ─────────────────────────────────────────────────────────────────

BRAND_TO_GENERIC: dict[str, dict] = {
    # ── Analgesics / Antipyretics ─────────────────────────────────
    "tylenol":      {"generic": "paracetamol", "class": "analgesic",     "db": "DB00316"},
    "panadol":      {"generic": "paracetamol", "class": "analgesic",     "db": "DB00316"},
    "crocin":       {"generic": "paracetamol", "class": "analgesic",     "db": "DB00316"},
    "calpol":       {"generic": "paracetamol", "class": "analgesic",     "db": "DB00316"},
    "dolo":         {"generic": "paracetamol", "class": "analgesic",     "db": "DB00316"},
    "fevadol":      {"generic": "paracetamol", "class": "analgesic",     "db": "DB00316"},
    "advil":        {"generic": "ibuprofen",   "class": "nsaid",         "db": "DB01050"},
    "brufen":       {"generic": "ibuprofen",   "class": "nsaid",         "db": "DB01050"},
    "nurofen":      {"generic": "ibuprofen",   "class": "nsaid",         "db": "DB01050"},
    "combiflam":    {"generic": "ibuprofen+paracetamol", "class": "nsaid+analgesic", "db": None,
                     "ingredients": ["ibuprofen", "paracetamol"], "note": "combination product"},
    "voltaren":     {"generic": "diclofenac",  "class": "nsaid",         "db": "DB00586"},
    "voveran":      {"generic": "diclofenac",  "class": "nsaid",         "db": "DB00586"},
    "celebrex":     {"generic": "celecoxib",   "class": "nsaid",         "db": "DB00482"},
    "aspirin":      {"generic": "aspirin",     "class": "nsaid",         "db": "DB00945"},
    "loprin":       {"generic": "aspirin",     "class": "nsaid",         "db": "DB00945"},
    "ecosprin":     {"generic": "aspirin",     "class": "nsaid",         "db": "DB00945"},
    "disprin":      {"generic": "aspirin",     "class": "nsaid",         "db": "DB00945"},
    "ultracet":     {"generic": "tramadol+paracetamol", "class": "opioid+analgesic", "db": None,
                     "ingredients": ["tramadol", "paracetamol"], "note": "combination product"},
    "tramadol":     {"generic": "tramadol",    "class": "opioid",        "db": "DB00193"},

    # ── Cardiovascular ────────────────────────────────────────────
    "lopressor":    {"generic": "metoprolol",  "class": "beta-blocker",  "db": "DB00264"},
    "betaloc":      {"generic": "metoprolol",  "class": "beta-blocker",  "db": "DB00264"},
    "metolar":      {"generic": "metoprolol",  "class": "beta-blocker",  "db": "DB00264"},
    "coreg":        {"generic": "carvedilol",  "class": "beta-blocker",  "db": "DB00388"},
    "tenormin":     {"generic": "atenolol",    "class": "beta-blocker",  "db": "DB00335"},
    "bisocor":      {"generic": "bisoprolol",  "class": "beta-blocker",  "db": "DB00612"},
    "concor":       {"generic": "bisoprolol",  "class": "beta-blocker",  "db": "DB00612"},
    "norvasc":      {"generic": "amlodipine",  "class": "ccb",           "db": "DB00381"},
    "stamlo":       {"generic": "amlodipine",  "class": "ccb",           "db": "DB00381"},
    "isoptin":      {"generic": "verapamil",   "class": "ccb",           "db": "DB00661"},
    "cardizem":     {"generic": "diltiazem",   "class": "ccb",           "db": "DB00343"},
    "zestril":      {"generic": "lisinopril",  "class": "ace-inhibitor", "db": "DB00722"},
    "prinivil":     {"generic": "lisinopril",  "class": "ace-inhibitor", "db": "DB00722"},
    "vasotec":      {"generic": "enalapril",   "class": "ace-inhibitor", "db": "DB00584"},
    "tritace":      {"generic": "ramipril",    "class": "ace-inhibitor", "db": "DB00178"},
    "cozaar":       {"generic": "losartan",    "class": "arb",           "db": "DB00678"},
    "diovan":       {"generic": "valsartan",   "class": "arb",           "db": "DB00177"},
    "atacand":      {"generic": "candesartan", "class": "arb",           "db": "DB00796"},
    "lasix":        {"generic": "furosemide",  "class": "diuretic",      "db": "DB00695"},
    "frusemide":    {"generic": "furosemide",  "class": "diuretic",      "db": "DB00695"},
    "aldactone":    {"generic": "spironolactone", "class": "diuretic",   "db": "DB00421"},
    "lanoxin":      {"generic": "digoxin",     "class": "cardiac glycoside", "db": "DB00390"},
    "coumadin":     {"generic": "warfarin",    "class": "anticoagulant", "db": "DB00682"},
    "warf":         {"generic": "warfarin",    "class": "anticoagulant", "db": "DB00682"},
    "acitrom":      {"generic": "acenocoumarol", "class": "anticoagulant", "db": "DB01418"},
    "xarelto":      {"generic": "rivaroxaban", "class": "anticoagulant", "db": "DB06228"},
    "eliquis":      {"generic": "apixaban",    "class": "anticoagulant", "db": "DB07828"},
    "plavix":       {"generic": "clopidogrel", "class": "antiplatelet",  "db": "DB00758"},
    "clopivas":     {"generic": "clopidogrel", "class": "antiplatelet",  "db": "DB00758"},

    # ── Lipid-Lowering ────────────────────────────────────────────
    "lipitor":      {"generic": "atorvastatin", "class": "statin",       "db": "DB01076"},
    "atorva":       {"generic": "atorvastatin", "class": "statin",       "db": "DB01076"},
    "zocor":        {"generic": "simvastatin",  "class": "statin",       "db": "DB00641"},
    "simvas":       {"generic": "simvastatin",  "class": "statin",       "db": "DB00641"},
    "crestor":      {"generic": "rosuvastatin", "class": "statin",       "db": "DB01098"},
    "rosuvas":      {"generic": "rosuvastatin", "class": "statin",       "db": "DB01098"},
    "pravachol":    {"generic": "pravastatin",  "class": "statin",       "db": "DB00175"},

    # ── Diabetes ──────────────────────────────────────────────────
    "glucophage":   {"generic": "metformin",   "class": "biguanide",     "db": "DB00331"},
    "glycomet":     {"generic": "metformin",   "class": "biguanide",     "db": "DB00331"},
    "amaryl":       {"generic": "glimepiride", "class": "sulfonylurea",  "db": "DB00222"},
    "glimy":        {"generic": "glimepiride", "class": "sulfonylurea",  "db": "DB00222"},
    "diamicron":    {"generic": "gliclazide",  "class": "sulfonylurea",  "db": "DB01120"},
    "januvia":      {"generic": "sitagliptin", "class": "dpp4-inhibitor","db": "DB01261"},
    "jardiance":    {"generic": "empagliflozin","class": "sglt2-inhibitor","db": "DB09038"},
    "forxiga":      {"generic": "dapagliflozin","class": "sglt2-inhibitor","db": "DB06292"},
    "victoza":      {"generic": "liraglutide", "class": "glp1-agonist",  "db": "DB06655"},
    "ozempic":      {"generic": "semaglutide", "class": "glp1-agonist",  "db": "DB13928"},
    "lantus":       {"generic": "insulin glargine", "class": "insulin",  "db": "DB00047"},
    "novorapid":    {"generic": "insulin aspart", "class": "insulin",    "db": "DB01306"},
    "mixtard":      {"generic": "insulin (biphasic)", "class": "insulin", "db": None},

    # ── Antibiotics ───────────────────────────────────────────────
    "augmentin":    {"generic": "amoxicillin+clavulanate", "class": "penicillin",
                     "ingredients": ["amoxicillin", "clavulanic acid"], "note": "combination product",
                     "db": "DB01060"},
    "zithromax":    {"generic": "azithromycin", "class": "macrolide",    "db": "DB00207"},
    "azithral":     {"generic": "azithromycin", "class": "macrolide",    "db": "DB00207"},
    "biaxin":       {"generic": "clarithromycin","class": "macrolide",   "db": "DB01211"},
    "klacid":       {"generic": "clarithromycin","class": "macrolide",   "db": "DB01211"},
    "ciprobay":     {"generic": "ciprofloxacin","class": "fluoroquinolone","db": "DB00537"},
    "cifran":       {"generic": "ciprofloxacin","class": "fluoroquinolone","db": "DB00537"},
    "levaquin":     {"generic": "levofloxacin", "class": "fluoroquinolone","db": "DB01137"},
    "flagyl":       {"generic": "metronidazole","class": "nitroimidazole","db": "DB00916"},
    "metrogyl":     {"generic": "metronidazole","class": "nitroimidazole","db": "DB00916"},
    "doxycycline":  {"generic": "doxycycline",  "class": "tetracycline", "db": "DB00254"},

    # ── Antifungals / Antivirals ──────────────────────────────────
    "diflucan":     {"generic": "fluconazole",  "class": "antifungal",   "db": "DB00196"},
    "zovirax":      {"generic": "acyclovir",    "class": "antiviral",    "db": "DB00787"},
    "valtrex":      {"generic": "valacyclovir", "class": "antiviral",    "db": "DB00577"},

    # ── Psychiatric / Neurological ────────────────────────────────
    "prozac":       {"generic": "fluoxetine",  "class": "ssri",          "db": "DB00472"},
    "flunil":       {"generic": "fluoxetine",  "class": "ssri",          "db": "DB00472"},
    "zoloft":       {"generic": "sertraline",  "class": "ssri",          "db": "DB01104"},
    "serlift":      {"generic": "sertraline",  "class": "ssri",          "db": "DB01104"},
    "lexapro":      {"generic": "escitalopram","class": "ssri",          "db": "DB01175"},
    "nexito":       {"generic": "escitalopram","class": "ssri",          "db": "DB01175"},
    "paxil":        {"generic": "paroxetine",  "class": "ssri",          "db": "DB00715"},
    "cymbalta":     {"generic": "duloxetine",  "class": "snri",          "db": "DB01010"},
    "effexor":      {"generic": "venlafaxine", "class": "snri",          "db": "DB00285"},
    "veniz":        {"generic": "venlafaxine", "class": "snri",          "db": "DB00285"},
    "remeron":      {"generic": "mirtazapine", "class": "nassa",         "db": "DB00688"},
    "elavil":       {"generic": "amitriptyline","class": "tca",          "db": "DB00321"},
    "tryptomer":    {"generic": "amitriptyline","class": "tca",          "db": "DB00321"},
    "risperdal":    {"generic": "risperidone", "class": "antipsychotic", "db": "DB00734"},
    "sizodon":      {"generic": "risperidone", "class": "antipsychotic", "db": "DB00734"},
    "zyprexa":      {"generic": "olanzapine",  "class": "antipsychotic", "db": "DB00334"},
    "seroquel":     {"generic": "quetiapine",  "class": "antipsychotic", "db": "DB01224"},
    "xanax":        {"generic": "alprazolam",  "class": "benzodiazepine","db": "DB00404"},
    "valium":       {"generic": "diazepam",    "class": "benzodiazepine","db": "DB00829"},
    "ativan":       {"generic": "lorazepam",   "class": "benzodiazepine","db": "DB00186"},
    "topamax":      {"generic": "topiramate",  "class": "anticonvulsant","db": "DB00273"},
    "lamictal":     {"generic": "lamotrigine", "class": "anticonvulsant","db": "DB00555"},
    "tegretol":     {"generic": "carbamazepine","class": "anticonvulsant","db": "DB00564"},
    "depakote":     {"generic": "valproate",   "class": "anticonvulsant","db": "DB00313"},
    "neurontin":    {"generic": "gabapentin",  "class": "anticonvulsant","db": "DB00996"},
    "aricept":      {"generic": "donepezil",   "class": "cholinesterase-inhibitor","db": "DB00843"},

    # ── Respiratory ───────────────────────────────────────────────
    "ventolin":     {"generic": "salbutamol",  "class": "beta-agonist",  "db": "DB01001"},
    "asthalin":     {"generic": "salbutamol",  "class": "beta-agonist",  "db": "DB01001"},
    "symbicort":    {"generic": "budesonide+formoterol", "class": "ics+laba",
                     "ingredients": ["budesonide", "formoterol"], "note": "combination product",
                     "db": "DB01407"},
    "seretide":     {"generic": "fluticasone+salmeterol", "class": "ics+laba",
                     "ingredients": ["fluticasone", "salmeterol"], "note": "combination product",
                     "db": "DB00588"},
    "allegra":      {"generic": "fexofenadine","class": "antihistamine", "db": "DB00950"},
    "cetirizine":   {"generic": "cetirizine",  "class": "antihistamine", "db": "DB00341"},
    "zyrtec":       {"generic": "cetirizine",  "class": "antihistamine", "db": "DB00341"},
    "montek":       {"generic": "montelukast", "class": "leukotriene-inhibitor","db": "DB00471"},
    "singulair":    {"generic": "montelukast", "class": "leukotriene-inhibitor","db": "DB00471"},

    # ── GI / Proton-pump inhibitors ───────────────────────────────
    "nexium":       {"generic": "esomeprazole","class": "ppi",           "db": "DB00736"},
    "prilosec":     {"generic": "omeprazole",  "class": "ppi",           "db": "DB00338"},
    "omez":         {"generic": "omeprazole",  "class": "ppi",           "db": "DB00338"},
    "prevacid":     {"generic": "lansoprazole","class": "ppi",           "db": "DB00448"},
    "pantocid":     {"generic": "pantoprazole","class": "ppi",           "db": "DB00213"},
    "razo":         {"generic": "rabeprazole", "class": "ppi",           "db": "DB01129"},
    "zantac":       {"generic": "ranitidine",  "class": "h2-blocker",    "db": "DB00863"},

    # ── Thyroid ───────────────────────────────────────────────────
    "synthroid":    {"generic": "levothyroxine","class": "thyroid",      "db": "DB00451"},
    "eltroxin":     {"generic": "levothyroxine","class": "thyroid",      "db": "DB00451"},
    "thyronorm":    {"generic": "levothyroxine","class": "thyroid",      "db": "DB00451"},

    # ── Corticosteroids ───────────────────────────────────────────
    "medrol":       {"generic": "methylprednisolone","class": "corticosteroid","db": "DB00959"},
    "wysolone":     {"generic": "prednisolone", "class": "corticosteroid","db": "DB00860"},
    "omnacortil":   {"generic": "prednisolone", "class": "corticosteroid","db": "DB00860"},
    "dexamethasone":{"generic": "dexamethasone","class": "corticosteroid","db": "DB01234"},
    "decadron":     {"generic": "dexamethasone","class": "corticosteroid","db": "DB01234"},

    # ── Miscellaneous ─────────────────────────────────────────────
    "viagra":       {"generic": "sildenafil",  "class": "pde5-inhibitor","db": "DB00203"},
    "cialis":       {"generic": "tadalafil",   "class": "pde5-inhibitor","db": "DB00820"},
    "cyclosporine": {"generic": "cyclosporine","class": "immunosuppressant","db": "DB00091"},
    "neoral":       {"generic": "cyclosporine","class": "immunosuppressant","db": "DB00091"},
    "prograf":      {"generic": "tacrolimus",  "class": "immunosuppressant","db": "DB00864"},
    "allopurinol":  {"generic": "allopurinol", "class": "xanthine-oxidase-inhibitor","db": "DB00437"},
    "zyloprim":     {"generic": "allopurinol", "class": "xanthine-oxidase-inhibitor","db": "DB00437"},
    "colchicine":   {"generic": "colchicine",  "class": "anti-gout",    "db": "DB01394"},
}

# ─────────────────────────────────────────────────────────────────
# LLM RESOLVER
# ─────────────────────────────────────────────────────────────────

FEATHERLESS_KEY = os.environ.get("FEATHERLESS_API_KEY", "")
MODEL_ID = "meta-llama/Meta-Llama-3.1-70B-Instruct"

_LLM_RESOLVE_PROMPT = """You are a clinical pharmacology expert.
For each drug name provided, identify the active ingredient(s) and return ONLY a valid JSON array.
No explanations, no markdown, no preamble — only the JSON.

Each element must follow this schema:
{{
  "brand": "<original name>",
  "generic": "<primary active ingredient, lowercase>",
  "ingredients": ["<ingredient1>", "<ingredient2>"],
  "drugbank_id": "<DBxxxxx or null>",
  "drug_class": "<pharmacological class>",
  "confidence": "high|medium|low",
  "note": "<null or 'combination product' etc>"
}}

Drug names to resolve: {drug_names}

Rules:
- For combination products, list ALL ingredients in the 'ingredients' array
- generic = primary/most pharmacologically significant ingredient
- confidence = 'low' if you are unsure
- Return ONLY the JSON array, nothing else
"""


def _resolve_via_llm(drug_names: list[str]) -> list[ResolvedDrug]:
    """Call LLM to resolve unknown brand names."""
    if not FEATHERLESS_KEY:
        return []
    try:
        from openai import OpenAI
        client = OpenAI(base_url="https://api.featherless.ai/v1", api_key=FEATHERLESS_KEY)
        prompt = _LLM_RESOLVE_PROMPT.format(drug_names=", ".join(drug_names))
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            stream=False,
            max_tokens=1000,
            temperature=0.1,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"```\s*$", "", raw, flags=re.MULTILINE)
        parsed = json.loads(raw)
        results = []
        for item in parsed:
            results.append(ResolvedDrug(
                brand=item.get("brand", ""),
                generic=item.get("generic", ""),
                ingredients=item.get("ingredients", [item.get("generic", "")]),
                drugbank_id=item.get("drugbank_id"),
                drug_class=item.get("drug_class"),
                resolution_source="llm",
                confidence=item.get("confidence", "medium"),
                note=item.get("note"),
            ))
        return results
    except Exception as e:
        print(f"[CascadeRx Resolver] LLM resolution failed: {e}")
        return []


# ─────────────────────────────────────────────────────────────────
# MAIN RESOLVER
# ─────────────────────────────────────────────────────────────────

def resolve_drug_names(drug_names: list[str]) -> list[ResolvedDrug]:
    """
    Resolve a list of drug names (brand, generic, common) to their active ingredients.
    
    Strategy:
    1. Exact match in offline dictionary (case-insensitive)
    2. If name already looks like a known generic/INN, pass through
    3. Batch unknown names to LLM resolver
    4. Any still-unknown names pass through as-is with low confidence
    """
    results = []
    unknown = []

    for name in drug_names:
        key = name.strip().lower()
        if key in BRAND_TO_GENERIC:
            entry = BRAND_TO_GENERIC[key]
            ingredients = entry.get("ingredients", [entry["generic"]])
            results.append(ResolvedDrug(
                brand=name,
                generic=entry["generic"],
                ingredients=ingredients,
                drugbank_id=entry.get("db"),
                drug_class=entry.get("class"),
                resolution_source="offline",
                confidence="high",
                note=entry.get("note"),
            ))
        else:
            # Check if it's already a known generic (pass-through)
            # Simple heuristic: if no capital letters and looks like a drug name
            unknown.append(name)

    # Batch resolve unknowns via LLM
    if unknown and FEATHERLESS_KEY:
        print(f"[CascadeRx Resolver] Sending {len(unknown)} unknown names to LLM: {unknown}")
        llm_results = _resolve_via_llm(unknown)
        resolved_brands = {r.brand.strip().lower() for r in llm_results}
        results.extend(llm_results)

        # Anything the LLM also couldn't resolve → passthrough
        for name in unknown:
            if name.strip().lower() not in resolved_brands:
                results.append(ResolvedDrug(
                    brand=name,
                    generic=name.strip().lower(),
                    ingredients=[name.strip().lower()],
                    resolution_source="passthrough",
                    confidence="low",
                    note="Could not resolve — treated as generic name",
                ))
    else:
        # No LLM available — passthrough unknowns
        for name in unknown:
            results.append(ResolvedDrug(
                brand=name,
                generic=name.strip().lower(),
                ingredients=[name.strip().lower()],
                resolution_source="passthrough",
                confidence="low",
                note="Offline dictionary miss — treated as generic name" if not FEATHERLESS_KEY
                     else "Could not resolve",
            ))

    # Preserve original input order
    order = {n.strip().lower(): i for i, n in enumerate(drug_names)}
    results.sort(key=lambda r: order.get(r.brand.strip().lower(), 999))
    return results


def build_ingredient_map(resolved: list[ResolvedDrug]) -> dict[str, str]:
    """
    Returns a mapping from every ingredient → original brand name.
    Used to translate pipeline output back to brand names in the report.
    """
    mapping = {}
    for r in resolved:
        for ingredient in r.ingredients:
            mapping[ingredient] = r.brand
    return mapping


def get_all_ingredients(resolved: list[ResolvedDrug]) -> list[str]:
    """Flattens all ingredients from all resolved drugs (deduplicated, preserving order)."""
    seen = set()
    result = []
    for r in resolved:
        for ing in r.ingredients:
            if ing not in seen:
                seen.add(ing)
                result.append(ing)
    return result
