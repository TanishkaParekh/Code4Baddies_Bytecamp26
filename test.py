"""
CascadeRx Eval Harness
Tests the full pipeline: deterministic engine + LLM narrative output.

Run:
    python test.py                  # full test with LLM
    python test.py --engine-only    # test deterministic engine only (no LLM needed)
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

# ─────────────────────────────────────────────────────────────────
# ENGINE-ONLY TEST (no LLM required)
# ─────────────────────────────────────────────────────────────────

def test_engine_only():
    """Tests the deterministic analyze endpoint directly."""
    print("\n" + "="*60)
    print("ENGINE-ONLY TESTS (no LLM)")
    print("="*60)

    cases = [
        {
            "name": "CYP2D6 cascade — fluoxetine + metoprolol",
            "data": {
                "drugs": [{"name": "fluoxetine", "dose": "20mg"}, {"name": "metoprolol", "dose": "50mg"}],
                "age": 68, "egfr": 55
            },
            "expect_risk": ["HIGH", "CRITICAL"],
            "expect_cascade_enzyme": "CYP2D6",
            "expect_inhibitor": "fluoxetine",
            "expect_substrate": "metoprolol",
        },
        {
            "name": "CYP3A4 cascade — clarithromycin + simvastatin",
            "data": {
                "drugs": [{"name": "clarithromycin", "dose": "500mg"}, {"name": "simvastatin", "dose": "40mg"}],
                "age": 72, "egfr": 45
            },
            "expect_risk": ["HIGH", "CRITICAL"],
            "expect_cascade_enzyme": "CYP3A4",
            "expect_inhibitor": "clarithromycin",
            "expect_substrate": "simvastatin",
        },
        {
            "name": "CYP2C9 induction — rifampin + warfarin",
            "data": {
                "drugs": [{"name": "rifampin", "dose": "600mg"}, {"name": "warfarin", "dose": "5mg"}],
                "age": 60, "egfr": 70
            },
            "expect_risk": ["HIGH", "CRITICAL", "MODERATE"],
            "expect_cascade_enzyme": "CYP2C9",
            "expect_inhibitor": None,
            "expect_substrate": "warfarin",
        },
        {
            "name": "Patient risk flag — age 75 bump",
            "data": {
                "drugs": [{"name": "fluoxetine"}, {"name": "metoprolol"}],
                "age": 75, "egfr": 50
            },
            "expect_risk": ["CRITICAL"],
            "expect_cascade_enzyme": "CYP2D6",
            "expect_inhibitor": "fluoxetine",
            "expect_substrate": "metoprolol",
        },
    ]

    all_passed = True

    for case in cases:
        print(f"\n  Testing: {case['name']}")
        try:
            resp = requests.post(f"{BASE_URL}/analyze", json=case["data"], timeout=10)
            resp.raise_for_status()
            data = resp.json()

            # Check risk level
            risk = data["overall_risk"]
            if risk in case["expect_risk"]:
                print(f"    ✅ Risk level: {risk}")
            else:
                print(f"    ❌ Risk level: got {risk}, expected one of {case['expect_risk']}")
                all_passed = False

            # Check cascade enzyme detected
            enzymes = [c["enzyme"] for c in data["cascade_paths"]]
            if case["expect_cascade_enzyme"] in enzymes:
                print(f"    ✅ Cascade enzyme detected: {case['expect_cascade_enzyme']}")
            else:
                print(f"    ❌ Cascade enzyme: expected {case['expect_cascade_enzyme']}, got {enzymes}")
                all_passed = False

            # Check inhibitor
            if case["expect_inhibitor"]:
                all_inhibitors = [i for c in data["cascade_paths"] for i in c["inhibitors"]]
                if case["expect_inhibitor"] in all_inhibitors:
                    print(f"    ✅ Inhibitor identified: {case['expect_inhibitor']}")
                else:
                    print(f"    ❌ Inhibitor: expected {case['expect_inhibitor']}, got {all_inhibitors}")
                    all_passed = False

            # Check substrate
            all_substrates = [s for c in data["cascade_paths"] for s in c["substrates"]]
            if case["expect_substrate"] in all_substrates:
                print(f"    ✅ Substrate identified: {case['expect_substrate']}")
            else:
                print(f"    ❌ Substrate: expected {case['expect_substrate']}, got {all_substrates}")
                all_passed = False

            # Show risk summary
            print(f"    ℹ  Risk summary: {data['risk_summary']}")
            if data["patient_risk_factors"]:
                print(f"    ℹ  Patient flags: {data['patient_risk_factors']}")

        except requests.exceptions.ConnectionError:
            print(f"    ❌ Cannot connect to server at {BASE_URL}")
            print(f"       Run: uvicorn main:app --reload")
            return False
        except Exception as e:
            print(f"    ❌ Error: {e}")
            all_passed = False

    return all_passed


# ─────────────────────────────────────────────────────────────────
# FULL STREAMING TEST (LLM required)
# ─────────────────────────────────────────────────────────────────

def run_llm_evaluation(name, patient_data, expected_keywords):
    print(f"\n  Testing LLM output: {name}...")
    try:
        response = requests.post(
            f"{BASE_URL}/analyze/stream",
            json=patient_data,
            stream=True,
            timeout=60,
        )
        response.raise_for_status()

        full_report = ""
        result_data = None

        for line in response.iter_lines():
            if line:
                decoded = line.decode("utf-8").replace("data: ", "")
                try:
                    event = json.loads(decoded)
                    if event["type"] == "result":
                        result_data = event["data"]
                        print(f"    ℹ  Phase 1 received — risk: {result_data['overall_risk']}")
                    elif event["type"] == "token":
                        full_report += event["text"]
                    elif event["type"] == "error":
                        print(f"    ❌ LLM error: {event['message']}")
                        return False
                    elif event["type"] == "done":
                        print(f"    ℹ  LLM report complete ({len(full_report)} chars)")
                except json.JSONDecodeError:
                    continue

        passed = True
        for keyword in expected_keywords:
            if keyword.lower() in full_report.lower():
                print(f"    ✅ Found clinical marker: '{keyword}'")
            else:
                print(f"    ❌ Missing clinical marker: '{keyword}'")
                passed = False

        return passed

    except Exception as e:
        print(f"    ❌ Error: {e}")
        return False


# ─────────────────────────────────────────────────────────────────
# SCENARIOS
# ─────────────────────────────────────────────────────────────────

scenario_1 = {
    "name": "CYP2D6 — fluoxetine + metoprolol",
    "data": {
        "drugs": [{"name": "fluoxetine", "dose": "20mg"}, {"name": "metoprolol", "dose": "50mg"}],
        "age": 68, "egfr": 55, "language": "en",
    },
    "expected": ["CYP2D6", "Bisoprolol", "bottleneck", "DB00622"],
}

scenario_2 = {
    "name": "CYP3A4 — clarithromycin + simvastatin",
    "data": {
        "drugs": [{"name": "clarithromycin", "dose": "500mg"}, {"name": "simvastatin", "dose": "40mg"}],
        "age": 72, "egfr": 45, "language": "en",
    },
    "expected": ["CYP3A4", "Azithromycin", "fold-increase", "DB00121"],
}


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    engine_only = "--engine-only" in sys.argv

    # Always test the health endpoint first
    print("\n" + "="*60)
    print("CASCADERX BACKEND TEST SUITE")
    print("="*60)

    try:
        h = requests.get(f"{BASE_URL}/health", timeout=5)
        h.raise_for_status()
        health = h.json()
        print(f"\n✅ Server healthy — {health['drugs_in_cyp_table']} drugs in CYP table, "
              f"{health.get('ddi_pairs_loaded', '?')} DDI pairs loaded")
    except Exception as e:
        print(f"\n❌ Server not reachable: {e}")
        print(f"   Start it with: uvicorn main:app --reload")
        sys.exit(1)

    # Engine tests
    engine_ok = test_engine_only()

    if engine_only:
        print("\n" + "="*60)
        if engine_ok:
            print("✅ ENGINE TESTS PASSED — deterministic pipeline is correct")
        else:
            print("❌ ENGINE TESTS FAILED — check cascade logic")
            sys.exit(1)
        sys.exit(0)

    # LLM streaming tests
    print("\n" + "="*60)
    print("LLM STREAMING TESTS")
    print("="*60)

    s1 = run_llm_evaluation(scenario_1["name"], scenario_1["data"], scenario_1["expected"])
    s2 = run_llm_evaluation(scenario_2["name"], scenario_2["data"], scenario_2["expected"])

    print("\n" + "="*60)
    if engine_ok and s1 and s2:
        print("✨ ALL TESTS PASSED — CascadeRx is ready")
    elif engine_ok:
        print("⚠️  ENGINE OK but LLM keyword checks failed")
        print("   → Tune build_agent_prompt() in main.py")
        print("   → Check FEATHERLESS_API_KEY is set in .env")
    else:
        print("❌ ENGINE TESTS FAILED — fix analyzer.py first")
        sys.exit(1)