import requests
import json
import sys

# Ensure your FastAPI server is running with the Featherless configuration
BASE_URL = "http://127.0.0.1:8000"

def run_evaluation(name, patient_data, expected_keywords):
    print(f"\n🔍 Testing Featherless AI Integration: {name}...")
    
    try:
        # Standard POST to your streaming endpoint
        response = requests.post(f"{BASE_URL}/analyze/stream", json=patient_data, stream=True)
        response.raise_for_status()
        
        full_report = ""
        result_data = None

        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8').replace('data: ', '')
                try:
                    event = json.loads(decoded_line)
                    if event["type"] == "result":
                        result_data = event["data"]
                    elif event["type"] == "token":
                        # Reassemble tokens to verify Llama's reasoning
                        full_report += event["text"]
                except json.JSONDecodeError:
                    continue

        # Clinical Validation Logic
        passed = True
        print(f"  - Overall Risk Level: {result_data['overall_risk']}")
        
        for keyword in expected_keywords:
            if keyword.lower() in full_report.lower():
                print(f"  ✅ [PASS] Found clinical marker: '{keyword}'")
            else:
                # If Llama misses a keyword, it often requires prompt tuning
                print(f"  ❌ [FAIL] Missing clinical marker: '{keyword}'")
                passed = False
        
        return passed

    except Exception as e:
        print(f"  ❌ System Error during evaluation: {e}")
        return False

# ── SCENARIO 1: CYP2D6 (Metoprolol + Fluoxetine) ──
scenario_1 = {
    "name": "CYP2D6 Cascade Check",
    "data": {
        "drugs": [
            {"name": "fluoxetine", "dose": "20mg"},
            {"name": "metoprolol", "dose": "50mg"}
        ],
        "age": 68, "egfr": 55, "language": "en"
    },
    # Keywords modified to verify Llama follows the Power Prompt
    "expected": ["CYP2D6", "Bisoprolol", "bottleneck", "DB00622"]
}

# ── SCENARIO 2: CYP3A4 (Clarithromycin + Simvastatin) ──
scenario_2 = {
    "name": "CYP3A4 Cascade Check",
    "data": {
        "drugs": [
            {"name": "clarithromycin", "dose": "500mg"},
            {"name": "simvastatin", "dose": "40mg"}
        ],
        "age": 72, "egfr": 45, "language": "en"
    },
    "expected": ["CYP3A4", "Azithromycin", "fold-increase", "DB00121"]
}

if __name__ == "__main__":
    # Sequentially testing to respect the 3-concurrency limit of the $25 tier
    s1 = run_evaluation(scenario_1["name"], scenario_1["data"], scenario_1["expected"])
    s2 = run_evaluation(scenario_2["name"], scenario_2["data"], scenario_2["expected"])
    
    if s1 and s2:
        print("\n✨ FEATHERLESS AI VALIDATED. System is ready for demo.")
    else:
        print("\n⚠️ VALIDATION FAILED. Review Llama's response formatting.")
        sys.exit(1)