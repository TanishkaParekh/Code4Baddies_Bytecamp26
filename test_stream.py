"""
CascadeRx — End-to-End Streaming Test
Tests the full pipeline: engine + SSE streaming + LLM narrative.

Usage:
    python test_stream.py              # full test (mock LLM if no API key)
    python test_stream.py --verbose    # show full LLM report
    python test_stream.py --engine     # engine checks only, skip LLM keywords

Requires server running:
    python main.py
"""

import json
import sys
import time
import requests

BASE_URL = "http://127.0.0.1:8000"
VERBOSE  = "--verbose" in sys.argv
ENGINE   = "--engine"  in sys.argv

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

passed = 0
failed = 0

def ok(msg):
    global passed
    passed += 1
    print(f"  {GREEN}✅{RESET}  {msg}")

def fail(msg, detail=None):
    global failed
    failed += 1
    print(f"  {RED}❌{RESET}  {msg}")
    if detail:
        print(f"      {DIM}{detail}{RESET}")

def warn(msg):
    print(f"  {YELLOW}⚠{RESET}   {msg}")

def section(title):
    print(f"\n{BOLD}{CYAN}{'─'*58}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*58}{RESET}")

# ─────────────────────────────────────────────────────────────────
# STEP 1 — SERVER HEALTH
# ─────────────────────────────────────────────────────────────────

section("step 1 — server health check")

try:
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    r.raise_for_status()
    h = r.json()
    ok(f"Server reachable at {BASE_URL}")
    ok(f"CYP_TABLE: {h['drugs_in_cyp_table']} drugs loaded")
    ok(f"DDI pairs: {h.get('ddi_pairs_loaded', '?')} pairs loaded")
    llm_mode = h.get("llm_mode", "unknown")
    if llm_mode == "featherless":
        ok(f"LLM mode: Featherless (Llama 3.1 70B) — real API")
    else:
        warn(f"LLM mode: mock — set FEATHERLESS_API_KEY in .env for real LLM")
except requests.exceptions.ConnectionError:
    print(f"\n{RED}{BOLD}  ✕ Server not running at {BASE_URL}{RESET}")
    print(f"  Start it with:  python main.py\n")
    sys.exit(1)
except Exception as e:
    fail(f"Health check failed: {e}")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────
# STEP 2 — SYNC ENGINE ENDPOINT (/analyze)
# ─────────────────────────────────────────────────────────────────

section("step 2 — engine endpoint (/analyze)")

ENGINE_CASES = [
    {
        "name": "CYP2D6 — fluoxetine + metoprolol",
        "payload": {"drugs": [{"name": "fluoxetine", "dose": "20mg"},
                               {"name": "metoprolol",  "dose": "50mg"}],
                    "age": 68, "egfr": 55},
        "expect_risk":    ["HIGH", "CRITICAL"],
        "expect_enzyme":  "CYP2D6",
        "expect_inhibitor": "fluoxetine",
        "expect_substrate": "metoprolol",
    },
    {
        "name": "CYP3A4 — clarithromycin + simvastatin",
        "payload": {"drugs": [{"name": "clarithromycin", "dose": "500mg"},
                               {"name": "simvastatin",    "dose": "40mg"}],
                    "age": 72, "egfr": 45},
        "expect_risk":    ["HIGH", "CRITICAL"],
        "expect_enzyme":  "CYP3A4",
        "expect_inhibitor": "clarithromycin",
        "expect_substrate": "simvastatin",
    },
    {
        "name": "CYP2C9 induction — rifampin + warfarin",
        "payload": {"drugs": [{"name": "rifampin", "dose": "600mg"},
                               {"name": "warfarin", "dose": "5mg"}],
                    "age": 60, "egfr": 70},
        "expect_risk":    ["MODERATE", "HIGH", "CRITICAL"],
        "expect_enzyme":  "CYP2C9",
        "expect_inhibitor": None,
        "expect_substrate": "warfarin",
    },
    {
        "name": "patient age 75 bump to CRITICAL",
        "payload": {"drugs": [{"name": "fluoxetine"}, {"name": "metoprolol"}],
                    "age": 75, "egfr": 50},
        "expect_risk":    ["CRITICAL"],
        "expect_enzyme":  "CYP2D6",
        "expect_inhibitor": "fluoxetine",
        "expect_substrate": "metoprolol",
    },
    {
        "name": "error — single drug rejected",
        "payload": {"drugs": [{"name": "fluoxetine"}]},
        "expect_error": True,
    },
]

engine_ok = True
for case in ENGINE_CASES:
    print(f"\n  {DIM}{case['name']}{RESET}")
    try:
        r = requests.post(f"{BASE_URL}/analyze", json=case["payload"], timeout=10)

        if case.get("expect_error"):
            if r.status_code == 400:
                ok("single drug correctly rejected (400)")
            else:
                fail("single drug should return 400", detail=f"got {r.status_code}")
                engine_ok = False
            continue

        r.raise_for_status()
        data = r.json()

        risk = data["overall_risk"]
        if risk in case["expect_risk"]:
            ok(f"overall_risk = {risk}")
        else:
            fail(f"overall_risk = {risk}", detail=f"expected one of {case['expect_risk']}")
            engine_ok = False

        enzymes = [c["enzyme"] for c in data["cascade_paths"]]
        if case["expect_enzyme"] in enzymes:
            ok(f"cascade enzyme = {case['expect_enzyme']}")
        else:
            fail(f"expected enzyme {case['expect_enzyme']}", detail=f"got {enzymes}")
            engine_ok = False

        if case["expect_inhibitor"]:
            inhibitors = [i for c in data["cascade_paths"] for i in c["inhibitors"]]
            if case["expect_inhibitor"] in inhibitors:
                ok(f"inhibitor = {case['expect_inhibitor']}")
            else:
                fail(f"inhibitor not found", detail=f"expected {case['expect_inhibitor']}, got {inhibitors}")
                engine_ok = False

        substrates = [s for c in data["cascade_paths"] for s in c["substrates"]]
        if case["expect_substrate"] in substrates:
            ok(f"substrate = {case['expect_substrate']}")
        else:
            fail(f"substrate not found", detail=f"expected {case['expect_substrate']}, got {substrates}")
            engine_ok = False

        # graph structure
        node_ids = [n["id"] for n in data["graph_json"]["nodes"]]
        if case["expect_enzyme"] in node_ids:
            ok(f"graph has enzyme node {case['expect_enzyme']}")
        else:
            fail(f"graph missing enzyme node", detail=f"nodes: {node_ids}")
            engine_ok = False

    except Exception as e:
        fail(f"request failed: {e}")
        engine_ok = False

if ENGINE:
    section("engine-only mode — skipping LLM tests")
    total = passed + failed
    print(f"\n{BOLD}{'═'*58}{RESET}")
    print(f"{BOLD}  {GREEN}{passed} passed{RESET}{BOLD} / {RED}{failed} failed{RESET}{BOLD} / {total} total{RESET}")
    sys.exit(0 if failed == 0 else 1)

# ─────────────────────────────────────────────────────────────────
# STEP 3 — SSE STREAMING PROTOCOL
# ─────────────────────────────────────────────────────────────────

section("step 3 — SSE streaming protocol")

STREAM_PAYLOAD = {
    "drugs": [{"name": "fluoxetine", "dose": "20mg"},
              {"name": "metoprolol",  "dose": "50mg"}],
    "age": 68, "egfr": 55, "language": "en",
}

print(f"\n  {DIM}sending POST /analyze/stream ...{RESET}")
t0 = time.time()

try:
    resp = requests.post(
        f"{BASE_URL}/analyze/stream",
        json=STREAM_PAYLOAD,
        stream=True,
        timeout=90,
    )
    resp.raise_for_status()

    events       = []
    result_data  = None
    report_chars = 0
    phase1_time  = None
    done_time    = None
    token_count  = 0

    for raw_line in resp.iter_lines():
        if not raw_line:
            continue
        line = raw_line.decode("utf-8")
        if not line.startswith("data: "):
            continue
        payload = line[6:]
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            continue

        events.append(event["type"])

        if event["type"] == "result":
            result_data = event["data"]
            phase1_time = time.time() - t0
        elif event["type"] == "token":
            report_chars += len(event.get("text", ""))
            token_count  += 1
        elif event["type"] == "error":
            fail(f"server sent error event: {event.get('message')}")
            break
        elif event["type"] == "done":
            done_time = time.time() - t0

    # Protocol checks
    if "result" in events:
        ok(f"phase 1 — result event received in {phase1_time:.2f}s")
    else:
        fail("phase 1 — no 'result' event received")

    if result_data:
        ok(f"phase 1 — overall_risk = {result_data['overall_risk']}")
        cascade_enzymes = [c["enzyme"] for c in result_data["cascade_paths"]]
        if cascade_enzymes:
            ok(f"phase 1 — cascade_paths contains: {cascade_enzymes}")
        else:
            fail("phase 1 — cascade_paths is empty")
        graph_nodes = [n["id"] for n in result_data["graph_json"]["nodes"]]
        if "CYP2D6" in graph_nodes:
            ok(f"phase 1 — graph_json has enzyme node CYP2D6")
        else:
            fail("phase 1 — graph_json missing enzyme node")
    else:
        fail("phase 1 — result_data was None")

    if token_count > 0:
        ok(f"phase 2 — {token_count} tokens streamed, {report_chars} total chars")
    else:
        fail("phase 2 — no tokens received")

    if "done" in events:
        ok(f"phase 2 — 'done' event received at {done_time:.2f}s")
    else:
        fail("phase 2 — stream never sent 'done' event")

    # Event order check
    if events and events[0] == "result":
        ok("event order — 'result' arrives before tokens (correct)")
    else:
        fail("event order — first event should be 'result'", detail=f"got: {events[:3]}")

except requests.exceptions.Timeout:
    fail("streaming timed out after 90s — check Featherless API key or server logs")
    sys.exit(1)
except Exception as e:
    fail(f"streaming request failed: {e}")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────
# STEP 4 — LLM KEYWORD VALIDATION
# ─────────────────────────────────────────────────────────────────

section("step 4 — LLM narrative keyword validation")

LLM_SCENARIOS = [
    {
        "name": "CYP2D6 — fluoxetine + metoprolol",
        "payload": {
            "drugs": [{"name": "fluoxetine", "dose": "20mg"},
                      {"name": "metoprolol",  "dose": "50mg"}],
            "age": 68, "egfr": 55, "language": "en",
        },
        "keywords": [
            ("CYP2D6",      "enzyme named correctly"),
            ("Bisoprolol",  "safer alternative named"),
            ("bottleneck",  "mechanism described (few-shot keyword)"),
            ("DB00622",     "DrugBank ID cited for bisoprolol"),
        ],
    },
    {
        "name": "CYP3A4 — clarithromycin + simvastatin",
        "payload": {
            "drugs": [{"name": "clarithromycin", "dose": "500mg"},
                      {"name": "simvastatin",    "dose": "40mg"}],
            "age": 72, "egfr": 45, "language": "en",
        },
        "keywords": [
            ("CYP3A4",      "enzyme named correctly"),
            ("Azithromycin","safer alternative named"),
            ("fold-increase","fold-increase quantified"),
            ("DB00121",     "DrugBank ID cited for azithromycin"),
        ],
    },
]

llm_ok = True
for scenario in LLM_SCENARIOS:
    print(f"\n  {DIM}{scenario['name']}{RESET}")
    try:
        resp = requests.post(
            f"{BASE_URL}/analyze/stream",
            json=scenario["payload"],
            stream=True,
            timeout=90,
        )
        resp.raise_for_status()

        full_report = ""
        risk_level  = None

        for raw_line in resp.iter_lines():
            if not raw_line:
                continue
            line = raw_line.decode("utf-8")
            if not line.startswith("data: "):
                continue
            try:
                event = json.loads(line[6:])
                if event["type"] == "result":
                    risk_level = event["data"]["overall_risk"]
                elif event["type"] == "token":
                    full_report += event.get("text", "")
            except json.JSONDecodeError:
                continue

        ok(f"stream complete — {len(full_report)} chars — risk: {risk_level}")

        if VERBOSE:
            print(f"\n{DIM}{'─'*58}")
            print(full_report[:2000])
            if len(full_report) > 2000:
                print(f"... [{len(full_report)-2000} more chars]")
            print(f"{'─'*58}{RESET}\n")

        for keyword, reason in scenario["keywords"]:
            if keyword.lower() in full_report.lower():
                ok(f"'{keyword}' — {reason}")
            else:
                fail(f"'{keyword}' missing — {reason}")
                llm_ok = False

    except requests.exceptions.Timeout:
        fail("timed out — Featherless may be slow, try again")
        llm_ok = False
    except Exception as e:
        fail(f"failed: {e}")
        llm_ok = False

# ─────────────────────────────────────────────────────────────────
# STEP 5 — DRUG SEARCH AUTOCOMPLETE
# ─────────────────────────────────────────────────────────────────

section("step 5 — drug search autocomplete")

search_tests = [("flu", ["fluoxetine", "fluconazole"]),
                ("met", ["metoprolol", "metformin"]),
                ("war", ["warfarin"])]

for query, expected_hits in search_tests:
    r = requests.get(f"{BASE_URL}/drugs/search?q={query}", timeout=5)
    results = r.json().get("results", [])
    hits = [e for e in expected_hits if e in results]
    if hits:
        ok(f"search '{query}' → found {hits}")
    else:
        fail(f"search '{query}' returned no expected drugs", detail=f"got: {results[:5]}")

# ─────────────────────────────────────────────────────────────────
# FINAL SUMMARY
# ─────────────────────────────────────────────────────────────────

total = passed + failed
print(f"\n{BOLD}{'═'*58}{RESET}")
print(f"{BOLD}  RESULTS: {GREEN}{passed} passed{RESET}{BOLD} / {RED}{failed} failed{RESET}{BOLD} / {total} total{RESET}")
print(f"{BOLD}{'═'*58}{RESET}")

if failed == 0:
    print(f"\n{GREEN}{BOLD}  ✨ ALL TESTS PASSED — pipeline is ready{RESET}\n")
elif engine_ok and not llm_ok:
    print(f"\n{YELLOW}{BOLD}  ⚠  Engine OK — LLM keywords failed{RESET}")
    print(f"  If using mock mode: keywords are hardcoded and should pass.")
    print(f"  If using Featherless: tune build_agent_prompt() in main.py")
    print(f"  Tip: run with --verbose to see the full LLM report\n")
    sys.exit(1)
else:
    print(f"\n{RED}{BOLD}  ✕  Tests failed — see above{RESET}\n")
    sys.exit(1)