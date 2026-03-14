/**
 * translations.ts  — pure data + hooks only, NO JSX
 * For the dropdown component, import LanguageSelector from ./LanguageSelector.tsx
 */
"use client";
import { useState, useCallback } from "react";

export type Lang = "en" | "hi" | "mr";

export const LANGUAGE_OPTIONS: { code: Lang; label: string; nativeLabel: string }[] = [
    { code: "en", label: "English", nativeLabel: "English" },
    { code: "hi", label: "Hindi", nativeLabel: "हिंदी" },
    { code: "mr", label: "Marathi", nativeLabel: "मराठी" },
];

// All string keys used in the UI
type Key =
    | "appName" | "tagline" | "disclaimer"
    | "patientMedications" | "loadDemo" | "drugsEntered" | "cascadeActive" | "addMore"
    | "drugNamePlaceholder" | "dosePlaceholder" | "selectSpecialist" | "addAnotherDrug"
    | "patientContext" | "age" | "agePlaceholder" | "egfr" | "egfrPlaceholder"
    | "allergies" | "allergiesPlaceholder"
    | "analyze" | "analyzing" | "copyReport" | "copied" | "exportPDF"
    | "overallRisk" | "cascadePaths" | "pairwiseInteractions"
    | "cascadeFingerprint" | "enzymeNetwork" | "cascadeDrug" | "safeDrug"
    | "cascadePath" | "particleNote" | "cascadeDetected"
    | "riskScore" | "inhibitors" | "affected" | "inducers"
    | "evidenceGrade" | "interactionType"
    | "pairwiseTitle" | "mechanism" | "effect" | "management" | "alternative" | "fullReport"
    | "patientRiskFactors" | "riskSummary"
    | "emptyTitle" | "emptySubtitle"
    | "cardiologist" | "endocrinologist" | "rheumatologist" | "psychiatrist"
    | "neurologist" | "pulmonologist" | "gastroenterologist" | "gp" | "other"
    | "uploadPrescription" | "readingPrescription" | "drugsFound" | "uploadError";

const en: Record<Key, string> = {
    appName: "CascadeRx", tagline: "Multi-drug cascade interaction checker",
    disclaimer: "Clinical decision support only — not a substitute for pharmacist review",
    patientMedications: "Patient medications", loadDemo: "Load demo ↗",
    drugsEntered: "drug(s) entered", cascadeActive: "✓ cascade detection active",
    addMore: "— add 3+ for cascade analysis",
    drugNamePlaceholder: "Drug name (e.g. metoprolol)", dosePlaceholder: "Dose",
    selectSpecialist: "Select prescribing specialist", addAnotherDrug: "+ Add another drug",
    patientContext: "Patient context", age: "Age", agePlaceholder: "e.g. 68",
    egfr: "eGFR (renal fn)", egfrPlaceholder: "e.g. 55",
    allergies: "Known allergies (comma-separated)", allergiesPlaceholder: "e.g. penicillin, sulfa",
    analyze: "Analyze interaction cascade", analyzing: "Analyzing cascade risks...",
    copyReport: "Copy report", copied: "Copied ✓", exportPDF: "Export PDF",
    overallRisk: "Overall risk level",
    cascadePaths: "cascade path(s)", pairwiseInteractions: "pairwise interaction(s)",
    cascadeFingerprint: "Cascade Fingerprint™", enzymeNetwork: "enzyme interaction network",
    cascadeDrug: "Cascade drug", safeDrug: "Safe drug",
    cascadePath: "Cascade path", particleNote: "particles = risk flowing through enzyme",
    cascadeDetected: "⚠ Cascade interactions detected — invisible to pairwise checkers",
    riskScore: "risk score", inhibitors: "Inhibitors", affected: "Affected", inducers: "Inducers",
    evidenceGrade: "Evidence grade", interactionType: "Type",
    pairwiseTitle: "Pairwise interactions", mechanism: "Mechanism", effect: "Effect",
    management: "Management", alternative: "Alternative", fullReport: "Full clinical report",
    patientRiskFactors: "Patient risk factors", riskSummary: "Risk summary",
    emptyTitle: "Enter a patient's full medication list to reveal hidden cascade interaction risks.",
    emptySubtitle: "Click \"Load demo ↗\" for a pre-filled example showing a CRITICAL cascade.",
    cardiologist: "Cardiologist", endocrinologist: "Endocrinologist",
    rheumatologist: "Rheumatologist", psychiatrist: "Psychiatrist",
    neurologist: "Neurologist", pulmonologist: "Pulmonologist",
    gastroenterologist: "Gastroenterologist", gp: "General Practitioner", other: "Other",
    uploadPrescription: "Upload prescription photo",
    readingPrescription: "Reading prescription...",
    drugsFound: "drug(s) found in prescription",
    uploadError: "Could not read prescription. Please enter drugs manually.",
};

const hi: Record<Key, string> = {
    appName: "CascadeRx", tagline: "बहु-दवा कैस्केड इंटरेक्शन चेकर",
    disclaimer: "केवल नैदानिक निर्णय समर्थन — फार्मासिस्ट की सलाह का विकल्प नहीं",
    patientMedications: "रोगी की दवाएं", loadDemo: "डेमो लोड करें ↗",
    drugsEntered: "दवा/दवाएं दर्ज की गईं", cascadeActive: "✓ कैस्केड डिटेक्शन सक्रिय",
    addMore: "— कैस्केड विश्लेषण के लिए 3+ दवाएं जोड़ें",
    drugNamePlaceholder: "दवा का नाम (जैसे मेटोप्रोलोल)", dosePlaceholder: "खुराक",
    selectSpecialist: "विशेषज्ञ चुनें", addAnotherDrug: "+ एक और दवा जोड़ें",
    patientContext: "रोगी की जानकारी", age: "आयु", agePlaceholder: "जैसे 68",
    egfr: "eGFR (गुर्दे की कार्यक्षमता)", egfrPlaceholder: "जैसे 55",
    allergies: "ज्ञात एलर्जी (अल्पविराम से अलग करें)", allergiesPlaceholder: "जैसे पेनिसिलिन, सल्फा",
    analyze: "इंटरेक्शन कैस्केड विश्लेषण करें", analyzing: "कैस्केड जोखिम का विश्लेषण हो रहा है...",
    copyReport: "रिपोर्ट कॉपी करें", copied: "कॉपी हो गई ✓", exportPDF: "PDF निर्यात करें",
    overallRisk: "कुल जोखिम स्तर",
    cascadePaths: "कैस्केड पथ", pairwiseInteractions: "जोड़ीवार इंटरेक्शन",
    cascadeFingerprint: "कैस्केड फिंगरप्रिंट™", enzymeNetwork: "एंजाइम इंटरेक्शन नेटवर्क",
    cascadeDrug: "कैस्केड दवा", safeDrug: "सुरक्षित दवा",
    cascadePath: "कैस्केड पथ", particleNote: "चलते बिंदु = एंजाइम के माध्यम से जोखिम प्रवाह",
    cascadeDetected: "⚠ कैस्केड इंटरेक्शन मिली — जोड़ी-जांच में नहीं दिखती",
    riskScore: "जोखिम स्कोर", inhibitors: "अवरोधक", affected: "प्रभावित", inducers: "प्रेरक",
    evidenceGrade: "साक्ष्य स्तर", interactionType: "प्रकार",
    pairwiseTitle: "जोड़ीवार इंटरेक्शन", mechanism: "तंत्र", effect: "प्रभाव",
    management: "प्रबंधन", alternative: "विकल्प", fullReport: "पूर्ण नैदानिक रिपोर्ट",
    patientRiskFactors: "रोगी जोखिम कारक", riskSummary: "जोखिम सारांश",
    emptyTitle: "छिपे हुए कैस्केड जोखिमों को उजागर करने के लिए रोगी की पूरी दवा सूची दर्ज करें।",
    emptySubtitle: "CRITICAL कैस्केड दिखाने वाले उदाहरण के लिए \"डेमो लोड करें\" पर क्लिक करें।",
    cardiologist: "हृदय रोग विशेषज्ञ", endocrinologist: "अंतःस्रावी विशेषज्ञ",
    rheumatologist: "संधि रोग विशेषज्ञ", psychiatrist: "मनोचिकित्सक",
    neurologist: "तंत्रिका विशेषज्ञ", pulmonologist: "फेफड़े विशेषज्ञ",
    gastroenterologist: "पाचन तंत्र विशेषज्ञ", gp: "सामान्य चिकित्सक", other: "अन्य",
    uploadPrescription: "प्रिस्क्रिप्शन फोटो अपलोड करें",
    readingPrescription: "प्रिस्क्रिप्शन पढ़ी जा रही है...",
    drugsFound: "दवा/दवाएं प्रिस्क्रिप्शन में मिलीं",
    uploadError: "प्रिस्क्रिप्शन पढ़ नहीं सकी। कृपया दवाएं मैन्युअल रूप से दर्ज करें।",
};

const mr: Record<Key, string> = {
    appName: "CascadeRx", tagline: "बहु-औषध कॅस्केड इंटरॅक्शन तपासक",
    disclaimer: "केवल क्लिनिकल निर्णय समर्थन — फार्मासिस्टच्या सल्ल्याचा पर्याय नाही",
    patientMedications: "रुग्णाची औषधे", loadDemo: "डेमो लोड करा ↗",
    drugsEntered: "औषध/औषधे नोंदवली", cascadeActive: "✓ कॅस्केड डिटेक्शन सक्रिय",
    addMore: "— कॅस्केड विश्लेषणासाठी 3+ औषधे जोडा",
    drugNamePlaceholder: "औषधाचे नाव (उदा. मेटोप्रोलॉल)", dosePlaceholder: "डोस",
    selectSpecialist: "तज्ञ निवडा", addAnotherDrug: "+ आणखी एक औषध जोडा",
    patientContext: "रुग्णाची माहिती", age: "वय", agePlaceholder: "उदा. 68",
    egfr: "eGFR (मूत्रपिंड कार्य)", egfrPlaceholder: "उदा. 55",
    allergies: "ज्ञात ऍलर्जी (स्वल्पविरामाने वेगळे करा)", allergiesPlaceholder: "उदा. पेनिसिलिन, सल्फा",
    analyze: "इंटरॅक्शन कॅस्केड विश्लेषण करा", analyzing: "कॅस्केड धोक्याचे विश्लेषण होत आहे...",
    copyReport: "अहवाल कॉपी करा", copied: "कॉपी झाले ✓", exportPDF: "PDF निर्यात करा",
    overallRisk: "एकूण धोक्याची पातळी",
    cascadePaths: "कॅस्केड मार्ग", pairwiseInteractions: "जोडी इंटरॅक्शन",
    cascadeFingerprint: "कॅस्केड फिंगरप्रिंट™", enzymeNetwork: "एन्झाइम इंटरॅक्शन नेटवर्क",
    cascadeDrug: "कॅस्केड औषध", safeDrug: "सुरक्षित औषध",
    cascadePath: "कॅस्केड मार्ग", particleNote: "हलणारे ठिपके = एन्झाइमद्वारे धोका प्रवाह",
    cascadeDetected: "⚠ कॅस्केड इंटरॅक्शन आढळल्या — जोडी-तपासणीत दिसत नाहीत",
    riskScore: "धोका स्कोअर", inhibitors: "अवरोधक", affected: "प्रभावित", inducers: "प्रेरक",
    evidenceGrade: "पुरावा स्तर", interactionType: "प्रकार",
    pairwiseTitle: "जोडी इंटरॅक्शन", mechanism: "यंत्रणा", effect: "परिणाम",
    management: "व्यवस्थापन", alternative: "पर्याय", fullReport: "संपूर्ण क्लिनिकल अहवाल",
    patientRiskFactors: "रुग्ण जोखीम घटक", riskSummary: "जोखीम सारांश",
    emptyTitle: "लपलेले कॅस्केड धोके उघड करण्यासाठी रुग्णाची संपूर्ण औषध यादी नोंदवा.",
    emptySubtitle: "CRITICAL कॅस्केड दर्शवणाऱ्या उदाहरणासाठी \"डेमो लोड करा\" वर क्लिक करा.",
    cardiologist: "हृदयरोग तज्ञ", endocrinologist: "अंतःस्रावी तज्ञ",
    rheumatologist: "संधिवात तज्ञ", psychiatrist: "मनोचिकित्सक",
    neurologist: "मज्जातंतू तज्ञ", pulmonologist: "फुफ्फुस तज्ञ",
    gastroenterologist: "पचन तज्ञ", gp: "सामान्य वैद्य", other: "इतर",
    uploadPrescription: "प्रिस्क्रिप्शन फोटो अपलोड करा",
    readingPrescription: "प्रिस्क्रिप्शन वाचत आहे...",
    drugsFound: "औषध/औषधे प्रिस्क्रिप्शनमध्ये सापडली",
    uploadError: "प्रिस्क्रिप्शन वाचता आले नाही. कृपया औषधे स्वहस्ते नोंदवा.",
};

const translations: Record<Lang, Record<Key, string>> = { en, hi, mr };

export function useTranslation() {
    const [lang, setLang] = useState<Lang>("en");
    const t = useCallback(
        (key: Key): string => translations[lang][key] ?? translations["en"][key] ?? key,
        [lang],
    );
    return { t, lang, setLang };
}

export function getSpecialists(t: (key: Key) => string): string[] {
    return [
        t("cardiologist"), t("endocrinologist"), t("rheumatologist"),
        t("psychiatrist"), t("neurologist"), t("pulmonologist"),
        t("gastroenterologist"), t("gp"), t("other"),
    ];
}