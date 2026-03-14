"""
CYP_TABLE — 237 drugs with evidence grades
Source: FDA Drug Development and Drug Interactions Table
Format: drug → {inhibits: [(enzyme, grade)], induces: [(enzyme, grade)], substrate_of: [enzyme]}
Grades: A = strong/moderate inhibitor (FDA classification)
        B = weak inhibitor (FDA classification)
        C = theoretical (not used — all data here is FDA-sourced)

Drop-in replacement for the hardcoded CYP_TABLE in analyzer.py
"""

CYP_TABLE: dict[str, dict] = {

    # ── A ──────────────────────────────────────────────────────
    "abiraterone": {"inhibits": [("CYP2D6","A")], "induces": [], "substrate_of": []},
    "acyclovir": {"inhibits": [("CYP1A2","B")], "induces": [], "substrate_of": []},
    "adagrasib": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "adefovir": {"inhibits": [], "induces": [], "substrate_of": []},
    "alfentanil": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "allopurinol": {"inhibits": [("CYP1A2","B")], "induces": [], "substrate_of": []},
    "alosetron": {"inhibits": [], "induces": [], "substrate_of": ["CYP1A2"]},
    "alprazolam": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "amiodarone": {"inhibits": [("CYP2C9","A"), ("CYP3A4","B"), ("CYP2D6","B")], "induces": [], "substrate_of": []},
    "apalutamide": {"inhibits": [], "induces": [("CYP3A4","A"), ("CYP2C19","A"), ("CYP2C9","B")], "substrate_of": []},
    "aprepitant": {"inhibits": [("CYP3A4","A")], "induces": [("CYP2C9","B")], "substrate_of": ["CYP3A4"]},
    "armodafinil": {"inhibits": [], "induces": [("CYP3A4","B")], "substrate_of": []},
    "atazanavir and ritonavir": {"inhibits": [], "induces": [], "substrate_of": []},
    "atomoxetine": {"inhibits": [], "induces": [], "substrate_of": ["CYP2D6"]},
    "atorvastatin": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "avanafil": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},

    # ── B ──────────────────────────────────────────────────────
    "baricitinib": {"inhibits": [], "induces": [], "substrate_of": []},
    "bosentan": {"inhibits": [], "induces": [("CYP3A4","A")], "substrate_of": []},
    "brigatinib": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "budesonide": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "bumetanide": {"inhibits": [], "induces": [], "substrate_of": []},
    "bupropion": {"inhibits": [("CYP2D6","A")], "induces": [], "substrate_of": ["CYP2B6"]},
    "buspirone": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},

    # ── C ──────────────────────────────────────────────────────
    "caffeine": {"inhibits": [], "induces": [], "substrate_of": ["CYP1A2"]},
    "capmatinib": {"inhibits": [("CYP1A2","A")], "induces": [], "substrate_of": []},
    "carbamazepine": {"inhibits": [], "induces": [("CYP3A4","A"), ("CYP2B6","A"), ("CYP2C9","B")], "substrate_of": []},
    "cefaclor": {"inhibits": [], "induces": [], "substrate_of": []},
    "ceftizoxime": {"inhibits": [], "induces": [], "substrate_of": []},
    "celecoxib": {"inhibits": [("CYP2D6","B")], "induces": [], "substrate_of": ["CYP2C9"]},
    "cenobamate": {"inhibits": [("CYP2C19","A")], "induces": [], "substrate_of": []},
    "ceritinib": {"inhibits": [("CYP3A4","A"), ("CYP2C9","B")], "induces": [], "substrate_of": []},
    "chlorzoxazone": {"inhibits": [("CYP3A4","B")], "induces": [], "substrate_of": []},
    "cilostazol": {"inhibits": [("CYP3A4","B")], "induces": [], "substrate_of": []},
    "cimetidine": {"inhibits": [("CYP3A4","B"), ("CYP2D6","B"), ("CYP1A2","B")], "induces": [], "substrate_of": []},
    "cinacalcet": {"inhibits": [("CYP2D6","A")], "induces": [], "substrate_of": []},
    "ciprofloxacin": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "clarithromycin": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "clobazam": {"inhibits": [("CYP2D6","B")], "induces": [], "substrate_of": []},
    "clopidogrel": {"inhibits": [("CYP2C8","A"), ("CYP2B6","B")], "induces": [], "substrate_of": []},
    "clotrimazole": {"inhibits": [("CYP3A4","B")], "induces": [], "substrate_of": []},
    "clozapine": {"inhibits": [], "induces": [], "substrate_of": ["CYP1A2"]},
    "cobicistat": {"inhibits": [("CYP3A4","A"), ("CYP2D6","B")], "induces": [], "substrate_of": []},
    "colchicine": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "conivaptan": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": ["CYP3A4"]},
    "crizotinib": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "curcumin": {"inhibits": [], "induces": [], "substrate_of": []},
    "cyclosporine": {"inhibits": [("CYP3A4","B")], "induces": [], "substrate_of": []},

    # ── D ──────────────────────────────────────────────────────
    "dabigatran etexilate": {"inhibits": [], "induces": [], "substrate_of": []},
    "dabrafenib": {"inhibits": [], "induces": [("CYP3A4","A"), ("CYP2C9","B")], "substrate_of": []},
    "darifenacin": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "darolutamide": {"inhibits": [], "induces": [], "substrate_of": []},
    "darunavir": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "dasatinib": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "deferasirox": {"inhibits": [("CYP2C8","A")], "induces": [], "substrate_of": []},
    "desipramine": {"inhibits": [], "induces": [], "substrate_of": ["CYP2D6"]},
    "desloratadine": {"inhibits": [], "induces": [], "substrate_of": ["CYP2C8"]},
    "dextromethorphan": {"inhibits": [], "induces": [], "substrate_of": ["CYP2D6"]},
    "diazepam": {"inhibits": [], "induces": [], "substrate_of": ["CYP2C19"]},
    "digoxin": {"inhibits": [], "induces": [], "substrate_of": []},
    "diltiazem": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "diosmin": {"inhibits": [("CYP2C9","B")], "induces": [], "substrate_of": []},
    "disulfiram": {"inhibits": [("CYP2C9","B")], "induces": [], "substrate_of": []},
    "docetaxel": {"inhibits": [], "induces": [], "substrate_of": []},
    "dolutegravir": {"inhibits": [], "induces": [], "substrate_of": []},
    "dronedarone": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": ["CYP3A4"]},
    "duloxetine": {"inhibits": [("CYP2D6","A")], "induces": [], "substrate_of": ["CYP1A2"]},

    # ── E ──────────────────────────────────────────────────────
    "edoxaban": {"inhibits": [], "induces": [], "substrate_of": []},
    "efavirenz": {"inhibits": [], "induces": [("CYP3A4","A"), ("CYP2C19","A"), ("CYP2B6","A")], "substrate_of": ["CYP2B6"]},
    "elagolix": {"inhibits": [], "induces": [("CYP3A4","B")], "substrate_of": []},
    "eletriptan": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "eliglustat": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4", "CYP2D6"]},
    "eltrombopag": {"inhibits": [], "induces": [], "substrate_of": []},
    "elvitegravir and ritonavir": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "entrectinib": {"inhibits": [("CYP3A4","B")], "induces": [], "substrate_of": ["CYP3A4"]},
    "enzalutamide": {"inhibits": [], "induces": [("CYP3A4","A"), ("CYP2C19","A"), ("CYP2C9","A")], "substrate_of": []},
    "eplerenone": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "erythromycin": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "escitalopram": {"inhibits": [("CYP2D6","B")], "induces": [], "substrate_of": []},
    "etravirine": {"inhibits": [], "induces": [("CYP3A4","A")], "substrate_of": []},
    "everolimus": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},

    # ── F ──────────────────────────────────────────────────────
    "famotidine": {"inhibits": [], "induces": [], "substrate_of": []},
    "febuxostat": {"inhibits": [], "induces": [], "substrate_of": []},
    "felbamate": {"inhibits": [("CYP2C19","A")], "induces": [], "substrate_of": []},
    "felodipine": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "fexofenadine": {"inhibits": [], "induces": [], "substrate_of": []},
    "fluconazole": {"inhibits": [("CYP2C19","A"), ("CYP3A4","A"), ("CYP2C9","A")], "induces": [], "substrate_of": []},
    "fluoxetine": {"inhibits": [("CYP2C19","A"), ("CYP2D6","A")], "induces": [], "substrate_of": []},
    "fluvastatin": {"inhibits": [("CYP2C9","B")], "induces": [], "substrate_of": []},
    "fluvoxamine": {"inhibits": [("CYP2C19","A"), ("CYP1A2","A"), ("CYP3A4","B"), ("CYP2D6","B"), ("CYP2C9","B")], "induces": [], "substrate_of": []},
    "fosaprepitant": {"inhibits": [("CYP3A4","B")], "induces": [], "substrate_of": []},
    "fostamatinib": {"inhibits": [], "induces": [], "substrate_of": []},
    "furosemide": {"inhibits": [], "induces": [], "substrate_of": []},

    # ── G ──────────────────────────────────────────────────────
    "gemfibrozil": {"inhibits": [("CYP2C8","A")], "induces": [], "substrate_of": []},
    "glimepiride": {"inhibits": [], "induces": [], "substrate_of": ["CYP2C9"]},
    "glyburide": {"inhibits": [], "induces": [], "substrate_of": []},
    "grapefruit juice": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},

    # ── I ──────────────────────────────────────────────────────
    "ibrutinib": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "idelalisib": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "imatinib": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "imipramine": {"inhibits": [], "induces": [], "substrate_of": ["CYP2D6"]},
    "indinavir": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "indinavir and ritonavir": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "isavuconazole": {"inhibits": [("CYP3A4","A")], "induces": [("CYP2B6","B")], "substrate_of": ["CYP3A4"]},
    "istradefylline": {"inhibits": [("CYP3A4","B")], "induces": [], "substrate_of": []},
    "itraconazole": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "ivabradine": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "ivacaftor": {"inhibits": [("CYP3A4","B")], "induces": [], "substrate_of": []},
    "ivosidenib": {"inhibits": [], "induces": [("CYP3A4","A")], "substrate_of": []},

    # ── K ──────────────────────────────────────────────────────
    "ketoconazole": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},

    # ── L ──────────────────────────────────────────────────────
    "labetalol": {"inhibits": [("CYP2D6","B")], "induces": [], "substrate_of": []},
    "lansoprazole": {"inhibits": [], "induces": [], "substrate_of": ["CYP2C19"]},
    "lapatinib": {"inhibits": [], "induces": [], "substrate_of": []},
    "larotrectinib": {"inhibits": [("CYP3A4","B")], "induces": [], "substrate_of": ["CYP3A4"]},
    "lazertinib": {"inhibits": [("CYP3A4","B")], "induces": [], "substrate_of": []},
    "lemborexant": {"inhibits": [], "induces": [("CYP2B6","B")], "substrate_of": ["CYP3A4"]},
    "lomitapide": {"inhibits": [("CYP3A4","B")], "induces": [], "substrate_of": ["CYP3A4"]},
    "loperamide": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4", "CYP2C8"]},
    "lopinavir and ritonavir": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "lorcaserin": {"inhibits": [("CYP2D6","A")], "induces": [], "substrate_of": []},
    "lorlatinib": {"inhibits": [], "induces": [("CYP3A4","A"), ("CYP2B6","B"), ("CYP2C9","B")], "substrate_of": []},
    "lovastatin": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "lumacaftor and ivacaftor": {"inhibits": [], "induces": [("CYP3A4","A")], "substrate_of": []},
    "lurasidone": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},

    # ── M ──────────────────────────────────────────────────────
    "maraviroc": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "melatonin": {"inhibits": [], "induces": [], "substrate_of": ["CYP1A2"]},
    "metformin": {"inhibits": [], "induces": [], "substrate_of": []},
    "methotrexate": {"inhibits": [], "induces": [], "substrate_of": []},
    "methoxsalen": {"inhibits": [("CYP1A2","A")], "induces": [], "substrate_of": []},
    "metoprolol": {"inhibits": [], "induces": [], "substrate_of": ["CYP2D6"]},
    "mexiletine": {"inhibits": [("CYP1A2","A")], "induces": [], "substrate_of": []},
    "miconazole": {"inhibits": [("CYP2C9","A")], "induces": [], "substrate_of": []},
    "midazolam": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "mirabegron": {"inhibits": [("CYP2D6","A")], "induces": [], "substrate_of": []},
    "mitotane": {"inhibits": [], "induces": [("CYP3A4","A")], "substrate_of": []},
    "mobocertinib": {"inhibits": [], "induces": [("CYP3A4","B")], "substrate_of": ["CYP3A4"]},
    "modafinil": {"inhibits": [], "induces": [("CYP3A4","B")], "substrate_of": []},
    "montelukast": {"inhibits": [], "induces": [], "substrate_of": ["CYP2C8"]},

    # ── N ──────────────────────────────────────────────────────
    "naloxegol": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "nebivolol": {"inhibits": [], "induces": [], "substrate_of": ["CYP2D6"]},
    "nefazodone": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "nelfinavir": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "nevirapine": {"inhibits": [], "induces": [("CYP2B6","B")], "substrate_of": []},
    "nisoldipine": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "nortriptyline": {"inhibits": [], "induces": [], "substrate_of": ["CYP2D6"]},

    # ── O ──────────────────────────────────────────────────────
    "omeprazole": {"inhibits": [("CYP2C19","B")], "induces": [], "substrate_of": ["CYP2C19"]},
    "oral contraceptives": {"inhibits": [("CYP1A2","A")], "induces": [], "substrate_of": []},
    "oseltamivir carboxylate": {"inhibits": [], "induces": [], "substrate_of": []},

    # ── P ──────────────────────────────────────────────────────
    "paclitaxel": {"inhibits": [], "induces": [], "substrate_of": []},
    "paritaprevir and ritonavir and (ombitasvir and/or dasabuvir)": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "paroxetine": {"inhibits": [("CYP2D6","A")], "induces": [], "substrate_of": []},
    "peginterferon alpha-2a": {"inhibits": [("CYP1A2","B")], "induces": [], "substrate_of": []},
    "penicillin g": {"inhibits": [], "induces": [], "substrate_of": []},
    "perphenazine": {"inhibits": [], "induces": [], "substrate_of": ["CYP2D6"]},
    "pexidartinib": {"inhibits": [], "induces": [("CYP3A4","A")], "substrate_of": []},
    "phenobarbital": {"inhibits": [], "induces": [("CYP3A4","A")], "substrate_of": []},
    "phenytoin": {"inhibits": [], "induces": [("CYP3A4","A"), ("CYP2C19","A"), ("CYP1A2","A")], "substrate_of": ["CYP2C9"]},
    "pimozide": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4", "CYP2D6"]},
    "pioglitazone": {"inhibits": [], "induces": [], "substrate_of": ["CYP2C8"]},
    "piperine": {"inhibits": [("CYP2C9","A"), ("CYP1A2","B")], "induces": [], "substrate_of": []},
    "pirfenidone": {"inhibits": [], "induces": [], "substrate_of": ["CYP1A2"]},
    "pirtobrutinib": {"inhibits": [("CYP2C8","A"), ("CYP3A4","B"), ("CYP2C19","B")], "induces": [], "substrate_of": []},
    "pitavastatin": {"inhibits": [], "induces": [], "substrate_of": []},
    "posaconazole": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "pralsetinib": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "pravastatin": {"inhibits": [], "induces": [], "substrate_of": []},
    "primidone": {"inhibits": [], "induces": [("CYP3A4","A")], "substrate_of": []},
    "probenecid": {"inhibits": [], "induces": [], "substrate_of": []},
    "propafenone": {"inhibits": [], "induces": [], "substrate_of": ["CYP2D6"]},
    "propranolol": {"inhibits": [], "induces": [], "substrate_of": ["CYP2D6"]},
    "pyrimethamine": {"inhibits": [], "induces": [], "substrate_of": []},

    # ── Q ──────────────────────────────────────────────────────
    "quetiapine": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "quinidine": {"inhibits": [("CYP2D6","A")], "induces": [], "substrate_of": []},

    # ── R ──────────────────────────────────────────────────────
    "r-venlafaxine": {"inhibits": [], "induces": [], "substrate_of": ["CYP2D6"]},
    "rabeprazole": {"inhibits": [], "induces": [], "substrate_of": ["CYP2C19"]},
    "ramelteon": {"inhibits": [], "induces": [], "substrate_of": ["CYP1A2"]},
    "ranitidine": {"inhibits": [("CYP3A4","B")], "induces": [], "substrate_of": []},
    "ranolazine": {"inhibits": [("CYP3A4","B")], "induces": [], "substrate_of": []},
    "repaglinide": {"inhibits": [], "induces": [], "substrate_of": ["CYP2C8"]},
    "repotrectinib": {"inhibits": [], "induces": [("CYP3A4","A")], "substrate_of": ["CYP3A4"]},
    "resmetirom": {"inhibits": [("CYP2C8","B")], "induces": [], "substrate_of": ["CYP2C8"]},
    "rifampin": {"inhibits": [], "induces": [("CYP3A4","A"), ("CYP2C19","A"), ("CYP2C8","A"), ("CYP2B6","A"), ("CYP2C9","A"), ("CYP1A2","A")], "substrate_of": []},
    "rilpivirine": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "ritonavir 14, 15,": {"inhibits": [("CYP3A4","A")], "induces": [("CYP2C19","B"), ("CYP2B6","B"), ("CYP2C9","B")], "substrate_of": []},
    "rivaroxaban": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "rolapitant": {"inhibits": [("CYP2D6","A")], "induces": [], "substrate_of": []},
    "rosiglitazone": {"inhibits": [], "induces": [], "substrate_of": ["CYP2C8"]},
    "rosuvastatin": {"inhibits": [], "induces": [], "substrate_of": []},
    "rufinamide": {"inhibits": [], "induces": [("CYP3A4","B")], "substrate_of": []},

    # ── S ──────────────────────────────────────────────────────
    "s-mephenytoin": {"inhibits": [], "induces": [], "substrate_of": ["CYP2C19"]},
    "s-venlafaxine": {"inhibits": [], "induces": [], "substrate_of": ["CYP2D6"]},
    "saquinavir": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "saquinavir and ritonavir": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "selexipag": {"inhibits": [], "induces": [], "substrate_of": ["CYP2C8"]},
    "selpercatinib": {"inhibits": [("CYP2C8","A"), ("CYP3A4","B")], "induces": [], "substrate_of": ["CYP3A4"]},
    "sertraline": {"inhibits": [("CYP2D6","B")], "induces": [], "substrate_of": []},
    "sevabertinib": {"inhibits": [("CYP3A4","B")], "induces": [], "substrate_of": ["CYP3A4"]},
    "sildenafil": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "simvastatin": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "sirolimus": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "sofosbuvir and velpatasvir and voxilaprevir": {"inhibits": [], "induces": [], "substrate_of": []},
    "sotorasib": {"inhibits": [], "induces": [("CYP3A4","A")], "substrate_of": []},
    "st. john’s wort": {"inhibits": [], "induces": [("CYP3A4","A")], "substrate_of": []},
    "sulfasalazine": {"inhibits": [], "induces": [], "substrate_of": []},

    # ── T ──────────────────────────────────────────────────────
    "tacrolimus": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "tadalafil": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "taletrectinib": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "tasimelteon": {"inhibits": [], "induces": [], "substrate_of": ["CYP1A2"]},
    "tazemetostat": {"inhibits": [("CYP2C8","B")], "induces": [("CYP3A4","B")], "substrate_of": ["CYP3A4"]},
    "telithromycin": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "tenofovir": {"inhibits": [("CYP2B6","B")], "induces": [], "substrate_of": []},
    "terbinafine": {"inhibits": [("CYP2D6","A")], "induces": [], "substrate_of": []},
    "teriflunomide": {"inhibits": [("CYP2C8","A")], "induces": [("CYP1A2","A")], "substrate_of": []},
    "theophylline": {"inhibits": [], "induces": [], "substrate_of": ["CYP1A2"]},
    "ticagrelor": {"inhibits": [("CYP3A4","B")], "induces": [], "substrate_of": ["CYP3A4"]},
    "ticlopidine": {"inhibits": [("CYP2C19","A"), ("CYP2B6","B")], "induces": [], "substrate_of": []},
    "tipranavir": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "tipranavir and ritonavir": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "tizanidine": {"inhibits": [], "induces": [], "substrate_of": ["CYP1A2"]},
    "tobacco (smoking)": {"inhibits": [], "induces": [("CYP1A2","A")], "substrate_of": []},
    "tolbutamide": {"inhibits": [], "induces": [], "substrate_of": ["CYP2C9"]},
    "tolterodine": {"inhibits": [], "induces": [], "substrate_of": ["CYP2D6"]},
    "tolvaptan": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "tramadol": {"inhibits": [], "induces": [], "substrate_of": ["CYP2D6"]},
    "triazolam": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "trimethoprim": {"inhibits": [("CYP2C8","B")], "induces": [], "substrate_of": []},
    "trimipramine": {"inhibits": [], "induces": [], "substrate_of": ["CYP2D6"]},
    "tucatinib": {"inhibits": [("CYP3A4","A"), ("CYP2C8","B")], "induces": [], "substrate_of": ["CYP2C8"]},

    # ── V ──────────────────────────────────────────────────────
    "vandetanib": {"inhibits": [], "induces": [], "substrate_of": []},
    "vardenafil": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "vemurafenib": {"inhibits": [("CYP1A2","A"), ("CYP2D6","B")], "induces": [("CYP3A4","B")], "substrate_of": []},
    "venetoclax": {"inhibits": [], "induces": [], "substrate_of": ["CYP3A4"]},
    "verapamil": {"inhibits": [("CYP3A4","A")], "induces": [], "substrate_of": []},
    "voriconazole": {"inhibits": [("CYP3A4","A"), ("CYP2C19","A"), ("CYP2B6","B"), ("CYP2C9","B")], "induces": [], "substrate_of": ["CYP2C19"]},

    # ── W ──────────────────────────────────────────────────────
    "warfarin": {"inhibits": [], "induces": [], "substrate_of": ["CYP2C9"]},

    # ── Z ──────────────────────────────────────────────────────
    "zanubrutinib": {"inhibits": [], "induces": [("CYP3A4","B")], "substrate_of": []},
    "zileuton": {"inhibits": [("CYP1A2","B")], "induces": [], "substrate_of": []},
    "zongertinib": {"inhibits": [], "induces": [], "substrate_of": []},
}

if __name__ == "__main__":
    from analyzer import _enzyme_list
    total = len(CYP_TABLE)
    inh = [d for d,v in CYP_TABLE.items() if v["inhibits"]]
    ind = [d for d,v in CYP_TABLE.items() if v["induces"]]
    sub = [d for d,v in CYP_TABLE.items() if v["substrate_of"]]
    print(f"Total: {total} | Inhibitors: {len(inh)} | Inducers: {len(ind)} | Substrates: {len(sub)}")
    # Verify demo drugs
    for d in ["fluoxetine","metoprolol","celecoxib","clarithromycin","simvastatin","warfarin","fluconazole"]:
        print(f"  {d}: {CYP_TABLE.get(d,'MISSING')}")