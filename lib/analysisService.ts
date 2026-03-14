/**
 * analysisService.ts
 * ──────────────────
 * Single source of truth for all backend calls.
 * Matches the EXACT response shape from analyzer.py + main.py.
 *
 * KEY FACT: Your backend /analyze/stream is a two-phase SSE:
 *   Phase 1 → { type: "result", data: AnalysisResult }   (structured JSON, instant)
 *   Phase 2 → { type: "token", text: "..." }              (AI report, streamed)
 *   End     → { type: "done" }
 *
 * ONE CALL does everything. Do NOT call /analyze separately (it's commented out in main.py).
 */

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─────────────────────────────────────────────────────────────────
// TYPES — mirrors analyzer.py Pydantic models exactly
// ─────────────────────────────────────────────────────────────────

export interface DrugInput {
    name: string;
    dose?: string;
    specialist?: string;
}

export interface PatientPayload {
    drugs: DrugInput[];
    age?: number | null;
    egfr?: number | null;
    conditions?: string[];
    allergies?: string[];
    language?: string;
}

/** Mirrors analyzer.py CascadePath — includes inducers, evidence_grade, interaction_type */
export interface CascadePath {
    enzyme: string;
    inhibitors: string[];
    substrates: string[];
    inducers: string[];
    risk_score: number;
    evidence_grade: string;     // "A" | "B" | "C"
    interaction_type: string;   // "inhibition" | "induction" | "competition"
    explanation: string;
}

/** Mirrors analyzer.py PairwiseInteraction — includes from_dataset */
export interface PairwiseInteraction {
    drug_a: string;
    drug_b: string;
    severity: "MAJOR" | "MODERATE" | "MINOR";
    mechanism: string;
    clinical_effect: string;
    management: string;
    safer_alternative: string;
    source: string;
    from_dataset: string;       // "DDI_2_0" | "DDInter" | "manual"
}

/** Mirrors analyzer.py AnalysisResult — includes risk_summary + patient_risk_factors */
export interface AnalysisResult {
    cascade_paths: CascadePath[];
    pairwise: PairwiseInteraction[];
    overall_risk: "CRITICAL" | "HIGH" | "MODERATE" | "LOW";
    graph_json: {
        nodes: { id: string; group: string; label: string }[];
        links: {
            source: string;
            target: string;
            type: string;       // "inhibits" | "induces" | "substrate" | "direct"
            severity: string;
            evidence: string;
            cascade: boolean;
        }[];
    };
    risk_summary: {
        major_pairwise: number;
        moderate_pairwise: number;
        minor_pairwise: number;
        cascade_inhibition: number;
        cascade_induction: number;
        cascade_competition: number;
        total_cascade_risk: number;
    };
    patient_risk_factors: string[];
}

// ─────────────────────────────────────────────────────────────────
// MAIN FUNCTION — one SSE call that does everything
// ─────────────────────────────────────────────────────────────────

/**
 * Calls POST /analyze/stream.
 * Handles both phases of the SSE response.
 *
 * Usage in page.tsx:
 *   await analyzeStream(
 *     payload,
 *     (data)  => { setResult(data); setLoading(false); },
 *     (token) => { setAiReport(prev => prev + token); },
 *     ()      => { setStreamDone(true); }
 *   );
 */
export async function analyzeStream(
    payload: PatientPayload,
    onResult: (data: AnalysisResult) => void,
    onToken: (text: string) => void,
    onDone: () => void,
): Promise<void> {
    const res = await fetch(`${API}/analyze/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (!res.ok) {
        const text = await res.text();
        throw new Error(`Backend error ${res.status}: ${text}`);
    }
    if (!res.body) throw new Error("No response body");

    const reader = res.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });

        for (const line of chunk.split("\n")) {
            if (!line.startsWith("data: ")) continue;
            const raw = line.slice(6).trim();
            if (!raw) continue;

            try {
                const parsed = JSON.parse(raw);
                if (parsed.type === "result") {
                    onResult(parsed.data as AnalysisResult);
                } else if (parsed.type === "token" && parsed.text) {
                    onToken(parsed.text);
                } else if (parsed.type === "done") {
                    onDone();
                    return;
                }
            } catch {
                // skip malformed chunk
            }
        }
    }

    onDone(); // stream closed without explicit done event
}

// ─────────────────────────────────────────────────────────────────
// DRUG AUTOCOMPLETE
// ─────────────────────────────────────────────────────────────────

/** GET /drugs/search?q=<query> — returns [] silently if backend unreachable */
export async function searchDrugs(query: string): Promise<string[]> {
    if (query.trim().length < 2) return [];
    try {
        const res = await fetch(`${API}/drugs/search?q=${encodeURIComponent(query.trim())}`);
        if (!res.ok) return [];
        const data = await res.json();
        return data.results ?? [];
    } catch {
        return [];
    }
}

// ─────────────────────────────────────────────────────────────────
// MOCK DATA — full offline fallback so demo works without backend
// ─────────────────────────────────────────────────────────────────

export function getMockResult(drugNames: string[]): AnalysisResult {
    const lower = drugNames.map((d) => d.toLowerCase());
    const knownInhibitors = ["fluoxetine", "paroxetine", "celecoxib", "amiodarone"];
    const knownSubstrates = ["metoprolol", "carvedilol", "codeine", "tramadol"];
    const inhibitors = lower.filter((d) => knownInhibitors.includes(d));
    const substrates = lower.filter((d) => knownSubstrates.includes(d));
    const hasCascade = inhibitors.length > 0 && substrates.length > 0;

    return {
        cascade_paths: hasCascade
            ? [{
                enzyme: "CYP2D6",
                inhibitors,
                substrates,
                inducers: [],
                risk_score: 9.2,
                evidence_grade: "A",
                interaction_type: "inhibition",
                explanation:
                    "Fluoxetine and Celecoxib both inhibit CYP2D6, blocking clearance of Metoprolol. " +
                    "Metoprolol plasma levels RISE 3–5×. Severe bradycardia and AV block risk. " +
                    "Neither drug pair alone triggers a major pairwise alert — this is a pure cascade.",
            }]
            : [],
        pairwise: [{
            drug_a: lower[0] ?? "fluoxetine",
            drug_b: lower[1] ?? "metoprolol",
            severity: "MAJOR",
            mechanism: "CYP2D6 inhibition — reduced metoprolol clearance",
            clinical_effect: "Metoprolol accumulates; bradycardia, hypotension, AV block",
            management: "Reduce metoprolol dose 50% or switch to bisoprolol. Monitor HR and BP.",
            safer_alternative: "Bisoprolol 5mg (renally cleared, no CYP2D6 involvement)",
            source: "FDA DDI Table; DrugBank DB00318; PubMed PMID 18923352",
            from_dataset: "DDI_2_0",
        }],
        overall_risk: hasCascade ? "CRITICAL" : "MODERATE",
        graph_json: {
            nodes: lower.map((id) => ({ id, group: "drug", label: id })),
            links: lower.length >= 2
                ? [
                    { source: lower[0], target: lower[1], type: "direct", severity: "MAJOR", evidence: "A", cascade: hasCascade },
                    ...(lower[2] ? [{ source: lower[0], target: lower[2], type: "direct", severity: "MODERATE", evidence: "B", cascade: false }] : []),
                ]
                : [],
        },
        risk_summary: {
            major_pairwise: 1, moderate_pairwise: 0, minor_pairwise: 0,
            cascade_inhibition: hasCascade ? 1 : 0,
            cascade_induction: 0, cascade_competition: 0,
            total_cascade_risk: hasCascade ? 9.2 : 0,
        },
        patient_risk_factors: [
            "Age 68: reduced hepatic reserve, polypharmacy sensitivity",
            "eGFR 55: moderate renal impairment — monitor drug levels",
        ],
    };
}

export const MOCK_REPORT = `## Summary

Each specialist prescribed appropriately for their domain. However, together these medications create a hidden CYP2D6 enzyme cascade — a risk that no pairwise checker can detect.

## Cascade Risk — The Hidden Danger

Fluoxetine and Celecoxib are both CYP2D6 inhibitors. Metoprolol is a CYP2D6 substrate. With the enzyme doubly blocked, Metoprolol cannot be cleared — blood levels rise 3–5× above therapeutic range.

**Why pairwise checkers miss this:** Fluoxetine ↔ Metoprolol alone = "Moderate" alert. Celecoxib ↔ Metoprolol alone = no alert. The CRITICAL risk only emerges from the three-drug combination — which pairwise tools are structurally unable to see.

## Recommended Schedule

- **Morning:** Metformin 500mg with breakfast
- **Midday:** Celecoxib 200mg with food
- **Evening:** Metoprolol (dose-adjusted to 25mg) — or switch to Bisoprolol
- **Note:** Fluoxetine should be taken at maximum interval from Metoprolol

## Safer Alternatives

- Replace Metoprolol → **Bisoprolol 5mg** (renally cleared, no CYP2D6 involvement)
- If Metoprolol kept: reduce to 25mg with daily HR and BP monitoring

## Sources

- FDA Drug Interaction Table (CYP2D6)
- DrugBank DB00318 (Fluoxetine)
- PubMed PMID 18923352
- DrugBank DB00264 (Metoprolol)

---
*Clinical decision support only. Verify all recommendations with a licensed pharmacist.*`;