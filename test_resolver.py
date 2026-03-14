"""
CascadeRx — Resolver Tests
Tests the brand-name resolution pipeline in isolation (no server needed).

Run: python3 test_resolver.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from drug_resolver import (
    resolve_drug_names,
    build_ingredient_map,
    get_all_ingredients,
    BRAND_TO_GENERIC,
)

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"

def test(name, condition):
    status = PASS if condition else FAIL
    print(f"  {status} {name}")
    return condition

def section(title):
    print(f"\n── {title} {'─' * (50 - len(title))}")

# ─────────────────────────────────────────────────────────────────
# 1. Basic offline resolution
# ─────────────────────────────────────────────────────────────────
section("1. Offline dictionary resolution")

r = resolve_drug_names(["Crocin", "Brufen", "Loprin"])
test("resolves 3 drugs", len(r) == 3)
test("Crocin → paracetamol",   r[0].generic == "paracetamol")
test("Brufen → ibuprofen",     r[1].generic == "ibuprofen")
test("Loprin → aspirin",       r[2].generic == "aspirin")
test("all from offline source",all(x.resolution_source == "offline" for x in r))
test("all high confidence",    all(x.confidence == "high" for x in r))
test("preserves brand names",  r[0].brand == "Crocin")

# ─────────────────────────────────────────────────────────────────
# 2. Case insensitivity
# ─────────────────────────────────────────────────────────────────
section("2. Case insensitivity")

r2 = resolve_drug_names(["CROCIN", "brufen", "LoPrIn"])
test("CROCIN → paracetamol",  r2[0].generic == "paracetamol")
test("brufen → ibuprofen",    r2[1].generic == "ibuprofen")
test("LoPrIn → aspirin",      r2[2].generic == "aspirin")

# ─────────────────────────────────────────────────────────────────
# 3. Combination products
# ─────────────────────────────────────────────────────────────────
section("3. Combination products")

r3 = resolve_drug_names(["Combiflam", "Augmentin"])
test("Combiflam has 2 ingredients",    len(r3[0].ingredients) == 2)
test("Combiflam has ibuprofen",        "ibuprofen" in r3[0].ingredients)
test("Combiflam has paracetamol",      "paracetamol" in r3[0].ingredients)
test("Combiflam has combination note", r3[0].note and "combination" in r3[0].note)
test("Augmentin has amoxicillin",      "amoxicillin" in r3[1].ingredients)
test("Augmentin has clavulanic acid",  "clavulanic acid" in r3[1].ingredients)

# ─────────────────────────────────────────────────────────────────
# 4. get_all_ingredients flattening
# ─────────────────────────────────────────────────────────────────
section("4. Ingredient flattening")

r4 = resolve_drug_names(["Combiflam", "Loprin"])
ingredients = get_all_ingredients(r4)
test("has ibuprofen",    "ibuprofen" in ingredients)
test("has paracetamol",  "paracetamol" in ingredients)
test("has aspirin",      "aspirin" in ingredients)
test("no duplicates",    len(ingredients) == len(set(ingredients)))
test("3 total ingredients", len(ingredients) == 3)

# ─────────────────────────────────────────────────────────────────
# 5. Passthrough for unknown names
# ─────────────────────────────────────────────────────────────────
section("5. Unknown name passthrough")

r5 = resolve_drug_names(["fluoxetine", "metoprolol", "UnknownDrug99"])
test("fluoxetine passes through as generic",  r5[0].generic == "fluoxetine")
test("metoprolol passes through as generic",  r5[1].generic == "metoprolol")
test("unknown passes through",               r5[2].generic == "unknowndrug99")
test("unknown has low confidence",           r5[2].confidence == "low")
test("unknown resolution_source",           r5[2].resolution_source in ("passthrough", "llm"))

# ─────────────────────────────────────────────────────────────────
# 6. DrugBank IDs preserved
# ─────────────────────────────────────────────────────────────────
section("6. DrugBank ID preservation")

r6 = resolve_drug_names(["Lipitor", "Coumadin", "Prozac"])
test("Lipitor DB ID",   r6[0].drugbank_id == "DB01076")
test("Coumadin DB ID",  r6[1].drugbank_id == "DB00682")
test("Prozac DB ID",    r6[2].drugbank_id == "DB00472")

# ─────────────────────────────────────────────────────────────────
# 7. Ingredient → brand mapping
# ─────────────────────────────────────────────────────────────────
section("7. Ingredient → brand reverse mapping")

r7 = resolve_drug_names(["Crocin", "Prozac"])
ing_map = build_ingredient_map(r7)
test("paracetamol → Crocin",   ing_map.get("paracetamol") == "Crocin")
test("fluoxetine → Prozac",    ing_map.get("fluoxetine")  == "Prozac")

# ─────────────────────────────────────────────────────────────────
# 8. Indian brand names
# ─────────────────────────────────────────────────────────────────
section("8. Indian brand names")

indian_brands = ["Dolo", "Voveran", "Montek", "Concor", "Glycomet", "Wysolone"]
r8 = resolve_drug_names(indian_brands)
test("Dolo → paracetamol",     r8[0].generic == "paracetamol")
test("Voveran → diclofenac",   r8[1].generic == "diclofenac")
test("Montek → montelukast",   r8[2].generic == "montelukast")
test("Concor → bisoprolol",    r8[3].generic == "bisoprolol")
test("Glycomet → metformin",   r8[4].generic == "metformin")
test("Wysolone → prednisolone",r8[5].generic == "prednisolone")

# ─────────────────────────────────────────────────────────────────
# 9. Mixed brand + generic input
# ─────────────────────────────────────────────────────────────────
section("9. Mixed brand + generic input")

r9 = resolve_drug_names(["Prozac", "metoprolol", "Crocin", "warfarin"])
test("4 results",              len(r9) == 4)
test("Prozac resolved",        r9[0].generic == "fluoxetine")
test("metoprolol passed through", r9[1].generic == "metoprolol")
test("Crocin resolved",        r9[2].generic == "paracetamol")
test("warfarin passed through",r9[3].generic == "warfarin")

# ─────────────────────────────────────────────────────────────────
# 10. Drug class is preserved
# ─────────────────────────────────────────────────────────────────
section("10. Drug class metadata")

r10 = resolve_drug_names(["Lipitor", "Zestril", "Ventolin"])
test("Lipitor class = statin",        r10[0].drug_class == "statin")
test("Zestril class = ace-inhibitor", r10[1].drug_class == "ace-inhibitor")
test("Ventolin class = beta-agonist", r10[2].drug_class == "beta-agonist")

# ─────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────
print(f"\n{'─' * 54}")
print(f"  Drug resolver test complete.")
print(f"  Total brands in offline dictionary: {len(BRAND_TO_GENERIC)}")
print()
