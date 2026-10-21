"""Deterministic generator for the QUANT synthetic supplementary holdout candidate.

Everything produced here is SYNTHETIC. Labels come from (a) merchant->category templates
and (b) explicitly documented anomaly scenarios. Nothing is human-verified.
Usage: python generate_quant_candidate.py <outdir>
"""
from __future__ import annotations

import csv
import random
import statistics
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SEED = 20261008
IST = timezone(timedelta(hours=5, minutes=30))
START = date(2026, 7, 1)
N_DAYS = 90  # 2026-07-01 .. 2026-09-28
MON = {7: "JUL", 8: "AUG", 9: "SEP"}

FIRST = ["AMIT", "PRIYA", "RAHUL", "ANITA", "SURESH", "MEERA", "VIKRAM", "KAVITA", "ARJUN", "NEHA",
         "MANOJ", "SUNITA", "DEEPAK", "POOJA", "KARAN", "RITU", "NITIN", "SHEETAL", "HARISH", "LATA",
         "IMRAN", "FARAH", "GURPREET", "JASLEEN", "TARUN", "DIVYA", "ASHOK", "REKHA", "SANDEEP", "MAYA"]
INIT = "ABCDEFGHIJKLMNOPRSTV"
COMPANIES = ["NORTHWIND SOFTWARE SERVICES", "BLUEFIELD ANALYTICS", "KESTREL LOGISTICS", "LUMEN HEALTH SYSTEMS",
             "ORCHID RETAIL SOLUTIONS", "SABLE ENGINEERING WORKS", "TERRAVIEW CONSULTING", "HELIX MEDIA NETWORKS",
             "CEDARLINE FINANCIAL SERVICES", "MARIGOLD FOODS", "PINNACLE EDU SERVICES", "VERTEX AUTO COMPONENTS"]

MERCH = {
    "Food & Dining": ["ZOMATO", "SWIGGY", "DOMINOS PIZZA", "STARBUCKS", "MCDONALDS", "BARBEQUE NATION", "CHAAYOS",
                      "BURGER KING", "HALDIRAM", "KFC", "CAFE COFFEE DAY", "BEHROUZ BIRYANI", "FAASOS",
                      "SAGAR RATNA", "THIRD WAVE COFFEE", "PIZZA HUT"],
    "Groceries": ["BIGBASKET", "BLINKIT", "ZEPTO", "DMART", "RELIANCE FRESH", "SPENCERS DAILY", "NATURES BASKET",
                  "MORE SUPERMARKET", "JIOMART", "SHREE GANESH KIRANA STORE", "AMUL PARLOUR", "FRESHTOHOME"],
    "Transport": ["UBER", "OLA CABS", "RAPIDO", "IRCTC", "REDBUS", "DMRC METRO RECHARGE", "FASTAG RECHARGE",
                  "INDIAN OIL PETROL PUMP", "HP PETROL PUMP", "BHARAT PETROLEUM FUEL", "BEST BUS PASS", "NAMMA METRO"],
    "Shopping": ["FLIPKART", "MYNTRA", "AJIO", "DECATHLON", "CROMA", "NYKAA", "LENSKART", "IKEA", "PANTALOONS",
                 "WESTSIDE", "RELIANCE DIGITAL", "MAX FASHION", "SHOPPERS STOP", "TATA CLIQ"],
    "Utilities": ["BESCOM ELECTRICITY", "TATA POWER", "ADANI ELECTRICITY", "AIRTEL PREPAID RECHARGE",
                  "JIO PREPAID RECHARGE", "VI PREPAID RECHARGE", "ACT FIBERNET", "MAHANAGAR GAS", "BWSSB WATER BILL",
                  "BSNL BROADBAND", "TATA PLAY DTH", "INDRAPRASTHA GAS"],
    "Entertainment": ["NETFLIX", "SPOTIFY", "PVR CINEMAS", "BOOKMYSHOW", "AMAZON PRIME VIDEO", "HOTSTAR",
                      "YOUTUBE PREMIUM", "INOX MOVIES", "STEAM GAMES", "SONYLIV", "ZEE5", "TIMEZONE GAMES"],
    "Healthcare": ["APOLLO PHARMACY", "MEDPLUS", "TATA 1MG", "PHARMEASY", "PRACTO CONSULT", "LAL PATHLABS",
                   "DR AGARWALS EYE CLINIC", "SMILE DENTAL CLINIC", "NETMEDS", "THYROCARE", "CITY CARE CLINIC"],
}
MAND = {
    "EMI": ["HDFC BANK HOME LOAN", "SBI CAR LOAN", "BAJAJ FINSERV", "ICICI BANK PERSONAL LOAN", "AXIS BANK LOAN",
            "TATA CAPITAL LOAN", "HOME CREDIT"],
    "Investment": ["SIP HDFC FLEXICAP FUND", "SIP AXIS BLUECHIP FUND", "SIP PARAG PARIKH FLEXI CAP", "NPS CONTRIBUTION",
                   "PPF DEPOSIT", "SIP NIPPON SMALL CAP FUND", "RD INSTALMENT", "SIP MIRAE ASSET FUND"],
}
# (merchant, category, confidence, note) -- genuinely ambiguous templates, flagged for human review
AMBIG = [
    ("HDFC CREDIT CARD BILL PAYMENT", "Other", "medium", "Credit-card bill payment: Other vs Transfer vs EMI"),
    ("LIC PREMIUM", "Other", "medium", "Insurance premium: Other vs Investment"),
    ("AMAZON PAY WALLET TOPUP", "Transfer", "low", "Wallet load: Transfer vs Shopping vs Other"),
    ("CULT FIT MEMBERSHIP", "Entertainment", "medium", "Gym/fitness: Entertainment vs Healthcare"),
    ("RELIANCE SMART BAZAAR", "Groceries", "medium", "Hypermarket: Groceries vs Shopping"),
    ("PAYMENT TO MERCHANT", "Other", "low", "Non-informative narration; true category unknowable from text"),
    ("AMAZON PAY INDIA", "Shopping", "medium", "Marketplace: could be groceries, bills or shopping"),
    ("PAYTM WALLET LOAD", "Transfer", "low", "Wallet load: Transfer vs Other"),
    ("MUNICIPAL PROPERTY TAX", "Other", "medium", "Tax/government fee: Other vs Utilities"),
]
CITY = ["MUMBAI", "BENGALURU", "PUNE", "DELHI", "HYDERABAD", "CHENNAI", "JAIPUR", "NAGPUR", "KOCHI", "LUCKNOW", "INDORE", "AHMEDABAD"]

# acct -> profile. cats = categories present in base history. anom_first = (category, merchant, amount).
# decoy_first = (category, merchant, amount) small first-seen. scale scales discretionary amounts.
P = {
 "q01": dict(kind="salaried", city="MUMBAI", sal=(1, 78000), rent=(5, 24000), emi=(8, 12500), sip=(3, 5000),
             absent=["Entertainment"], anom_first=("Entertainment", "LIVE EVENTS TICKETING", 38000), decoy_first=None, scale=1.2, mand_night=("EMI", 2)),
 "q02": dict(kind="salaried", city="BENGALURU", sal=(1, 95000), rent=(5, 32000), emi=None, sip=(3, 10000),
             absent=["EMI"], anom_first=("Healthcare", "FORTIS HOSPITAL IP DEPOSIT", 78000), decoy_first=None, scale=1.4),
 "q03": dict(kind="salaried", city="PUNE", sal=(30, 62000), rent=(2, 18500), emi=(10, 9800), sip=None,
             absent=["Investment"], anom_first=("Investment", "UPSTOX FUND ADD", 70000), decoy_first=None, scale=1.0),
 "q04": dict(kind="student", city="DELHI", sal=None, rent=None, emi=None, sip=None, absent=["Investment", "Healthcare", "EMI", "Rent"],
             anom_first=("Investment", "ZERODHA FUND ADD", 60000), decoy_first=("Healthcare", "APOLLO PHARMACY", 120), scale=0.45, night=True),
 "q05": dict(kind="student", city="HYDERABAD", sal=None, rent=(3, 7500), emi=None, sip=(10, 500),
             absent=["EMI"], anom_first=("Healthcare", "CARE HOSPITALS ADMISSION", 48000), decoy_first=None, scale=0.5, night=True),
 "q06": dict(kind="family", city="CHENNAI", sal=(1, 105000), rent=None, emi=(6, 28500), sip=(5, 8000),
             absent=["Rent"], anom_first=("Rent", "RENT TRANSFER", 85000), decoy_first=None, scale=1.5, mand_night=("Investment", 3)),
 "q07": dict(kind="retiree", city="JAIPUR", sal=(1, 38000), rent=None, emi=None, sip=(12, 3000),
             absent=["Shopping", "Entertainment", "EMI", "Rent"], anom_first=("Shopping", "TANISHQ JEWELLERS", 110000),
             decoy_first=("Entertainment", "NETFLIX", 199), scale=0.8),
 "q08": dict(kind="retiree", city="NAGPUR", sal=(3, 29500), rent=None, emi=None, sip=(15, 2000),
             absent=["Entertainment", "EMI", "Rent"], anom_first=("Entertainment", "ONLINE GAMING DEPOSIT", 40000), decoy_first=None, scale=0.7),
 "q09": dict(kind="freelancer", city="KOCHI", sal=("irregular", 85000), rent=(1, 21000), emi=(12, 7400), sip=(20, 4000),
             absent=["Healthcare"], anom_first=("Healthcare", "AMRITA HOSPITAL SURGERY ADVANCE", 95000), decoy_first=None, scale=1.0),
 "q10": dict(kind="freelancer", city="LUCKNOW", sal=("irregular", 52000), rent=(4, 14000), emi=(11, 6200), sip=None,
             absent=["Investment", "Healthcare"], anom_first=("Investment", "MF LUMPSUM PURCHASE", 125000),
             decoy_first=("Healthcare", "MEDPLUS", 260), scale=0.9),
 "q11": dict(kind="salaried", city="INDORE", sal=(28, 48000), rent=(3, 11500), emi=(9, 8800), sip=(25, 3000),
             absent=["Entertainment"], anom_first=("Entertainment", "ONLINE GAMING DEPOSIT", 28000), decoy_first=None, scale=0.8),
 "q12": dict(kind="salaried", city="AHMEDABAD", sal=(1, 88000), rent=(6, 27000), emi=(10, 15500), sip=(4, 7500),
             absent=["Healthcare"], anom_first=("Healthcare", "SHALBY HOSPITAL PROCEDURE", 110000), decoy_first=None, scale=1.3),
}
COUNTS = {  # approx rows per category over 90 days for scale=1 (discretionary)
    "Food & Dining": 14, "Groceries": 10, "Transport": 11, "Shopping": 6, "Utilities": 6,
    "Entertainment": 6, "Healthcare": 4, "Transfer": 8, "Other": 5,
}
AMT = {  # (low, high) log-uniform before scale
    "Food & Dining": (110, 1500), "Groceries": (90, 2400), "Transport": (35, 700), "Shopping": (350, 5200),
    "Utilities": (199, 2600), "Entertainment": (129, 1400), "Healthcare": (90, 2800), "Transfer": (200, 6500), "Other": (100, 4500),
}
HOURS = {
    "Food & Dining": [(8, 10, 0.2), (12, 15, 0.4), (18, 22, 0.4)], "Groceries": [(8, 12, 0.4), (16, 21, 0.6)],
    "Transport": [(7, 10, 0.5), (17, 21, 0.5)], "Shopping": [(10, 22, 1.0)], "Utilities": [(9, 20, 1.0)],
    "Entertainment": [(11, 23, 1.0)], "Healthcare": [(9, 20, 1.0)], "Transfer": [(9, 21, 1.0)], "Other": [(10, 18, 1.0)],
}

def pick_name(rng, used=None):
    while True:
        n = f"{rng.choice(FIRST)} {rng.choice(INIT)}"
        if used is None or n not in used:
            return n

class Gen:
    def __init__(self):
        self.rows = []
        self.uid = 0

    def add(self, acct, when, desc, amount, tx_type, cat, merchant="", **meta):
        r = dict(account_id=f"acct_{acct}", when=when, description=desc, amount=round(float(amount), 2), tx_type=tx_type,
                 expected_category=cat, merchant=merchant, is_anomaly="false", anomaly_type="", scenario="base",
                 cat_source="generator_merchant_template", anom_source="generator_scenario_base_normal",
                 conf="high", notes="", review="no")
        r.update(meta)
        self.rows.append(r)
        return r

def ref(rng):
    return rng.randint(100000, 999999999)

def rand_time(rng, cat, day):
    bands = HOURS[cat]
    x, acc = rng.random(), 0
    for lo, hi, w in bands:
        acc += w
        if x <= acc:
            h = rng.randint(lo, hi - 1)
            break
    else:
        h = rng.randint(bands[-1][0], bands[-1][1] - 1)
    return datetime(day.year, day.month, day.day, h, rng.randint(0, 59), rng.randint(0, 59), tzinfo=IST)

def narrate(rng, cat, m, city):
    k = rng.random()
    if cat == "Utilities":
        return rng.choice([f"BBPS-{m}-{ref(rng)}", f"BILLPAY/{m}/{ref(rng)}", f"UPI/P2M/{ref(rng)}/{m}"])
    if k < 0.45:
        return f"UPI/P2M/{ref(rng)}/{m}"
    if k < 0.65:
        return f"UPI-{m}-PAYMENT-{ref(rng)}"
    if k < 0.85:
        return f"POS XX{rng.randint(1000, 9999)} {m} {city}"
    return f"{m} ONLINE {ref(rng)}"

def amount_for(rng, cat, scale):
    lo, hi = AMT[cat]
    a = lo * (hi / lo) ** rng.random() * scale
    return max(20.0, round(a if a < 500 else round(a / 5) * 5, 2))

def build_account(g, acct, p, idx):
    rng = random.Random(SEED + idx)
    city = p["city"]
    absent = set(p["absent"])
    if p.get("anom_first"):
        absent.add(p["anom_first"][0])
    scale = p["scale"]
    day = lambda off: START + timedelta(days=off)
    # ---- recurring income / rent / mandates
    months = [(7, 0), (8, 31), (9, 62)]
    company = rng.choice(COMPANIES)
    payee_family = [pick_name(rng) for _ in range(4)]
    landlord = pick_name(rng)
    if p["sal"]:
        for mi, (mo, base) in enumerate(months):
            if p["sal"][0] == "irregular":
                for _ in range(2):  # two client payments / month
                    d = day(base + rng.randint(1, 26)); amt = round(p["sal"][1] * rng.uniform(0.4, 0.8), -2)
                    cl = rng.choice(COMPANIES)
                    g.add(acct, datetime(d.year, d.month, d.day, rng.randint(10, 17), rng.randint(0, 59), 0, tzinfo=IST),
                          rng.choice([f"IMPS-{ref(rng)}-{cl} INVOICE PAYMENT", f"NEFT-{ref(rng)}-{cl} PROJECT FEE {MON[mo]}"]),
                          amt, "credit", "Salary/Income", cl)
            else:
                dd = min(p["sal"][0], 28)
                d = day(base + dd - 1)
                if p["kind"] == "retiree":
                    desc = f"PENSION CREDIT {MON[mo]} TREASURY {ref(rng)}"
                elif p["kind"] == "student":
                    desc = f"STIPEND {MON[mo]} {ref(rng)}"
                else:
                    desc = rng.choice([f"NEFT-{ref(rng)}-{company} SALARY {MON[mo]}", f"SALARY {MON[mo]} {company}"])
                g.add(acct, datetime(d.year, d.month, d.day, rng.randint(9, 11), rng.randint(0, 59), 0, tzinfo=IST),
                      desc, round(p["sal"][1] * rng.uniform(0.995, 1.0), 2), "credit", "Salary/Income", company)
        d = day(rng.randint(60, 85))
        g.add(acct, datetime(d.year, d.month, d.day, 6, rng.randint(0, 59), 0, tzinfo=IST), f"INT.PD:SAVINGS INTEREST QTR {ref(rng) % 100000}",
              round(rng.uniform(180, 1450), 2), "credit", "Salary/Income", "BANK INTEREST", notes="Interest credit mapped to Salary/Income by taxonomy rule",
              conf="medium", review="yes", cat_source="ai_proposed_taxonomy_rule")
    if p["kind"] == "student":  # allowance from family -> Transfer credit
        for mo, base in months:
            d = day(base + rng.randint(0, 3))
            g.add(acct, datetime(d.year, d.month, d.day, rng.randint(10, 19), rng.randint(0, 59), 0, tzinfo=IST),
                  f"UPI/P2A/{ref(rng)}/{payee_family[0]}/RECEIVED", rng.choice([6000, 8000, 10000, 12000]), "credit", "Transfer", payee_family[0])
    if p["rent"]:
        for mo, base in months:
            d = day(base + p["rent"][0] - 1)
            desc = rng.choice([f"UPI/P2A/{ref(rng)}/{landlord}/RENT {MON[mo]}", f"NEFT-{ref(rng)}-{landlord}-RENT {MON[mo]}", f"IMPS-{ref(rng)}-{landlord} HOUSE RENT"])
            g.add(acct, datetime(d.year, d.month, d.day, rng.randint(9, 20), rng.randint(0, 59), 0, tzinfo=IST), desc, p["rent"][1], "debit", "Rent", landlord)
    night_for = p.get("mand_night")
    for cat, key in (("EMI", "emi"), ("Investment", "sip")):
        if not p[key]:
            continue
        m = rng.choice(MAND[cat])
        for mo, base in months:
            d = day(base + p[key][0] - 1)
            if night_for and night_for[0] == cat:
                when = datetime(d.year, d.month, d.day, night_for[1], rng.randint(0, 40), rng.randint(0, 59), tzinfo=IST)
                extra = dict(scenario="decoy_scheduled_mandate_odd_hour", anom_source="generator_scenario_decoy_normal", conf="medium", review="yes",
                             notes="Scheduled mandate debited 01:00-04:59; labelled normal because it is not a customer-initiated payment (see guidelines). Confirm.")
            else:
                when = datetime(d.year, d.month, d.day, rng.randint(6, 12), rng.randint(0, 59), 0, tzinfo=IST); extra = {}
            desc = rng.choice([f"ACH D- {m}-{ref(rng)}", f"NACH DR {m} {ref(rng)}"]) if cat == "Investment" else rng.choice([f"ACH D- {m} EMI-{ref(rng)}", f"EMI {m} LOAN A/C XX{rng.randint(1000, 9999)}"])
            g.add(acct, when, desc, p[key][1], "debit", cat, m, **extra)
    # ---- utilities subscriptions
    for mo, base in months:
        for m in rng.sample(MERCH["Utilities"], 1 + (1 if p["kind"] != "student" else 0)):
            d = day(base + rng.randint(8, 25))
            g.add(acct, rand_time(rng, "Utilities", d), narrate(rng, "Utilities", m, city), round(amount_for(rng, "Utilities", scale), 2), "debit", "Utilities", m)
    # ---- discretionary
    fam_paid = {}
    for cat, n in COUNTS.items():
        if cat in absent or cat == "Utilities":
            continue
        n = max(2, round(n * rng.uniform(0.8, 1.2) * (0.7 if p["kind"] == "retiree" and cat in ("Food & Dining", "Transport") else 1)))
        merchants = rng.sample(MERCH.get(cat, ["X"]), 4) if cat in MERCH else None
        for _ in range(n):
            d = day(rng.randint(0, N_DAYS - 1))
            if cat == "Transfer":
                if rng.random() < 0.2:
                    nm = payee_family[0]; desc = f"UPI/P2A/{ref(rng)}/{nm}/RECEIVED"
                    g.add(acct, rand_time(rng, cat, d), desc, round(rng.choice([500, 1000, 1500, 2000, 3000]), 2), "credit", "Transfer", nm); continue
                nm = rng.choice(payee_family)
                desc = rng.choice([f"UPI/P2A/{ref(rng)}/{nm}", f"IMPS-{ref(rng)}-{nm}", f"NEFT-{ref(rng)}-{nm}", f"UPI/P2A/{ref(rng)}/SELF SAVINGS"])
                amt = rng.choice([500, 1000, 1500, 2000, 2500, 3000, 5000]) if rng.random() < 0.6 else round(rng.uniform(250, 7500), 0)
                g.add(acct, rand_time(rng, cat, d), desc, amt, "debit", cat, nm); continue
            if cat == "Other":
                k = rng.random()
                if k < 0.35:
                    desc, amt, m = f"ATM WDL XX{rng.randint(1000, 9999)} {city}", rng.choice([1000, 2000, 3000, 5000]), "ATM"
                    g.add(acct, rand_time(rng, cat, d), desc, amt, "debit", cat, m); continue
                if k < 0.5:
                    g.add(acct, rand_time(rng, cat, d), rng.choice(["SMS ALERT CHARGES", "ANNUAL DEBIT CARD FEE", "GST ON BANK CHARGES", "MIN BAL PENALTY CHARGES"]),
                          rng.choice([17.7, 29.5, 118.0, 236.0, 59.0]), "debit", cat, "BANK CHARGES"); continue
            if cat == "Other" or rng.random() < 0.06:
                m_, c_, conf_, note_ = rng.choice(AMBIG)
                if c_ in absent and c_ != cat:
                    m_, c_, conf_, note_ = AMBIG[5]
                g.add(acct, rand_time(rng, cat if cat in HOURS else "Other", d), narrate(rng, c_, m_, city), amount_for(rng, c_ if c_ in AMT else "Other", scale),
                      "debit", c_, m_, conf=conf_, notes=note_, review="yes", cat_source="ai_proposed_ambiguous_template"); continue
            m = rng.choice(merchants)
            when = rand_time(rng, cat, d)
            amt = amount_for(rng, cat, scale)
            extra = {}
            if p.get("night") and cat == "Food & Dining" and rng.random() < 0.3:
                when = datetime(d.year, d.month, d.day, rng.choice([23, 23, 0]), rng.randint(0, 45), rng.randint(0, 59), tzinfo=IST)
            g.add(acct, when, narrate(rng, cat, m, city), amt, "debit", cat, m, **extra)
    # refunds (credits) -- ambiguous by design
    if "Shopping" not in absent and p["kind"] != "retiree":
        d = day(rng.randint(10, 80)); m = rng.choice(MERCH["Shopping"])
        g.add(acct, rand_time(rng, "Shopping", d), f"REFUND {m} ORDER {ref(rng)}", round(rng.uniform(300, 2500), 2), "credit", "Shopping", m,
              conf="medium", review="yes", cat_source="ai_proposed_ambiguous_template",
              notes="Refund credit assigned the original merchant's category (guideline G7); Other/Transfer also defensible")

def inject(g, acct, p, idx, plan):
    rng = random.Random(SEED + 1000 + idx)
    mine = [r for r in g.rows if r["account_id"] == f"acct_{acct}"]
    day = lambda off: START + timedelta(days=off)
    def tm(d, h, mi=None, s=None):
        return datetime(d.year, d.month, d.day, h, rng.randint(0, 59) if mi is None else mi, rng.randint(0, 59) if s is None else s, tzinfo=IST)
    city = p["city"]
    # --- amount_spike
    for _ in range(plan.get("spike", 0)):
        cands = [c for c in ("Food & Dining", "Groceries", "Shopping", "Entertainment") if len([r for r in mine if r["expected_category"] == c and r["tx_type"] == "debit" and r["scenario"] == "base"]) >= 3]
        c = rng.choice(cands)
        base = [r for r in mine if r["expected_category"] == c and r["tx_type"] == "debit" and r["scenario"] == "base"]
        med = statistics.median(r["amount"] for r in base)
        ratio = rng.uniform(9.5, 18)
        amt = round(max(med * ratio, 5200) / 10) * 10
        if amt / med < 9:
            amt = round(med * 9.5 / 10) * 10
        m = rng.choice(base)["merchant"]; d = day(rng.randint(20, 85))
        g.add(acct, g_time(rng, c, d), narrate(rng, c, m, city), amt, "debit", c, m, is_anomaly="true", anomaly_type="amount_spike", scenario="amount_spike",
              anom_source="generator_scenario_injected", conf="high", notes=f"Injected: same-merchant debit at {amt/med:.1f}x the account's base median for {c} (median {med:.0f}); threshold >=9x and >=5,000. Large amount alone is NOT evidence of fraud.", review="yes")
    # decoy: large but within 3-6x
    if plan.get("spike_decoy"):
        c = "Shopping" if "Shopping" not in p["absent"] else "Groceries"
        base = [r for r in mine if r["expected_category"] == c and r["tx_type"] == "debit" and r["scenario"] == "base"]
        med = statistics.median(r["amount"] for r in base)
        amt = round(med * rng.uniform(3.5, 6.0) / 10) * 10; m = rng.choice(base)["merchant"]; d = day(rng.randint(20, 85))
        g.add(acct, g_time(rng, c, d), narrate(rng, c, m, city), amt, "debit", c, m, scenario="decoy_large_but_below_threshold", anom_source="generator_scenario_decoy_normal",
              conf="medium", review="yes", notes=f"Hard negative: {amt/med:.1f}x category median (<9x threshold); labelled normal by definition. Reviewer should judge plausibility.")
    # --- duplicate_transaction
    for _ in range(plan.get("dup", 0)):
        base = [r for r in mine if r["tx_type"] == "debit" and r["scenario"] == "base" and r["expected_category"] in ("Food & Dining", "Groceries", "Shopping", "Transport", "Healthcare", "Entertainment") and r["amount"] >= 150 and not r.get("used")]
        o = rng.choice(base); o["used"] = True
        o["scenario"] = "duplicate_original"; o["anom_source"] = "generator_scenario_pair_original_normal"; o["review"] = "yes"
        o["notes"] = "Original of an injected duplicate pair (label normal; the later copy is the anomaly)."
        g.add(acct, o["when"] + timedelta(seconds=rng.randint(25, 150)), o["description"], o["amount"], "debit", o["expected_category"], o["merchant"], is_anomaly="true", anomaly_type="duplicate_transaction",
              scenario="duplicate_copy", anom_source="generator_scenario_injected", conf="high", review="yes",
              notes="Injected: identical narration (incl. reference), amount and account re-posted 25-150 s after the original. A same-day repeat alone is not proof of a duplicate.")
    # decoy: same merchant & amount, different refs, hours apart
    if plan.get("dup_decoy"):
        c = "Transport"; base = [r for r in mine if r["expected_category"] == c and r["scenario"] == "base" and r["tx_type"] == "debit"]
        o = rng.choice(base); d = o["when"].date()
        g.add(acct, datetime(d.year, d.month, d.day, rng.randint(18, 21), rng.randint(0, 59), 0, tzinfo=IST), narrate(rng, c, o["merchant"], city), o["amount"], "debit", c, o["merchant"],
              scenario="decoy_same_amount_hours_apart", anom_source="generator_scenario_decoy_normal", conf="medium", review="yes",
              notes="Hard negative: same merchant and amount as another debit that day but different reference, several hours apart (e.g. outbound/return trips). Labelled normal.")
        o["when"] = o["when"].replace(hour=rng.randint(7, 10))
        o["scenario"] = "decoy_same_amount_hours_apart_pair"; o["review"] = "yes"; o["notes"] = "Partner of same-amount-hours-apart decoy; labelled normal."
    # --- large_round_transfer
    for _ in range(plan.get("round", 0)):
        used = {r["merchant"] for r in mine}
        nm = pick_name(rng, used)
        amt = rng.choice([50000, 60000, 75000, 80000, 100000, 150000, 200000])
        d = day(rng.randint(25, 86))
        g.add(acct, g_time(rng, "Transfer", d), rng.choice([f"UPI/P2A/{ref(rng)}/{nm}", f"IMPS-{ref(rng)}-{nm}", f"NEFT-{ref(rng)}-{nm}"]), amt, "debit", "Transfer", nm,
              is_anomaly="true", anomaly_type="large_round_transfer", scenario="large_round_transfer", anom_source="generator_scenario_injected", conf="medium", review="yes",
              notes="Injected: round amount (multiple of 5,000, >=50,000) to a payee never seen earlier in this account whose prior transfers are all <=7,500. Could be a legitimate one-off; human must judge.")
    if plan.get("round_decoy"):
        nm = [r for r in mine if r["expected_category"] == "Transfer" and r["tx_type"] == "debit" and r["scenario"] == "base"]
        nm = nm[0]["merchant"]; d = day(rng.randint(50, 86))
        g.add(acct, g_time(rng, "Transfer", d), f"UPI/P2A/{ref(rng)}/{nm}", rng.choice([50000, 60000]), "debit", "Transfer", nm, scenario="decoy_round_to_established_payee",
              anom_source="generator_scenario_decoy_normal", conf="medium", review="yes", notes="Hard negative: large round transfer to a payee with several earlier transfers. Labelled normal by definition; reviewer to confirm.")
    if plan.get("nonround_decoy"):
        nm = pick_name(rng, {r["merchant"] for r in mine}); d = day(rng.randint(50, 86))
        g.add(acct, g_time(rng, "Transfer", d), f"IMPS-{ref(rng)}-{nm}", rng.choice([63420, 52750, 71180]), "debit", "Transfer", nm, scenario="decoy_large_nonround_new_payee",
              anom_source="generator_scenario_decoy_normal", conf="low", review="yes",
              notes="Hard negative / ambiguous: large NON-round transfer to a new payee. Outside the round-amount definition so labelled normal, but a reviewer may reasonably call it suspicious; flag.")
    # --- odd_hour (customer-initiated debit 01:00-04:59)
    for _ in range(plan.get("odd", 0)):
        c = "Shopping" if "Shopping" not in p["absent"] and p["anom_first"][0] != "Shopping" else "Other"
        if c == "Shopping":
            m = rng.choice(MERCH["Shopping"]); desc = rng.choice([f"UPI/P2M/{ref(rng)}/{m}", f"{m} ONLINE {ref(rng)}"]); amt = rng.choice([1499, 2299, 3499, 4999, 7999, 12999])
        else:
            m = "ATM"; desc = f"ATM WDL XX{rng.randint(1000, 9999)} {city}"; amt = rng.choice([10000, 15000, 20000])
        d = day(rng.randint(15, 87))
        g.add(acct, datetime(d.year, d.month, d.day, rng.randint(1, 4), rng.randint(0, 59), rng.randint(0, 59), tzinfo=IST), desc, amt, "debit", c, m, is_anomaly="true", anomaly_type="odd_hour",
              scenario="odd_hour", anom_source="generator_scenario_injected", conf="medium", review="yes",
              notes="Injected: customer-initiated debit between 01:00 and 04:59 IST in an account with no other customer-initiated activity in that window. Unusual time alone is not proof of fraud.")
    # --- first-seen category
    c, m, amt = p["anom_first"]
    d = day(rng.randint(58, 86))
    desc = f"UPI/P2M/{ref(rng)}/{m}" if c != "Rent" else f"NEFT-{ref(rng)}-{pick_name(rng)}-RENT"
    g.add(acct, g_time(rng, "Shopping", d), desc, amt, "debit", c, m, is_anomaly="true", anomaly_type="unusual_category_first_seen", scenario="first_seen_category",
          anom_source="generator_scenario_injected", conf="medium", review="yes",
          notes=f"Injected: first-ever {c} transaction in this account (none in the preceding history) at >=5x the account's median debit. Category novelty alone is not proof of fraud; may be a legitimate life event.")
    if p.get("decoy_first"):
        c, m, amt = p["decoy_first"]; d = day(rng.randint(40, 86))
        g.add(acct, g_time(rng, "Shopping", d), f"UPI/P2M/{ref(rng)}/{m}", amt, "debit", c, m, scenario="decoy_first_seen_small", anom_source="generator_scenario_decoy_normal",
              conf="medium", review="yes", notes=f"Hard negative: first-ever {c} transaction but a small amount (<5x median); labelled normal by definition.")

def g_time(rng, cat, d):
    return rand_time(rng, cat if cat in HOURS else "Shopping", d)

PLANS = {
 "q01": dict(spike=2, dup=1, round=1, spike_decoy=True, dup_decoy=True),
 "q02": dict(spike=2, dup=1, round=1, odd=2, round_decoy=True),
 "q03": dict(spike=1, dup=2, round=1, odd=2, dup_decoy=True),
 "q04": dict(spike=1, dup=1, round=1),
 "q05": dict(spike=1, dup=1, round=1, dup_decoy=True),
 "q06": dict(spike=1, dup=1, round=1, round_decoy=True),
 "q07": dict(spike=1, dup=1, round=1, odd=2, dup_decoy=True),
 "q08": dict(spike=1, dup=1, round=1, odd=2),
 "q09": dict(spike=1, dup=1, round=1, odd=2, nonround_decoy=True, dup_decoy=True),
 "q10": dict(spike=1, dup=1, round=1, odd=1, spike_decoy=True),
 "q11": dict(spike=1, dup=1, round=1, odd=1, dup_decoy=True),
 "q12": dict(spike=1, dup=1, round=1, odd=1, nonround_decoy=True),
}

def main(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    g = Gen()
    for i, (a, p) in enumerate(sorted(P.items())):
        build_account(g, a, p, i)
    for i, (a, p) in enumerate(sorted(P.items())):
        inject(g, a, p, i, PLANS[a])
    rows = sorted(g.rows, key=lambda r: (r["account_id"], r["when"]))
    for n, r in enumerate(rows, 1):
        r["record_id"] = f"qh_{n:04d}"
        r["tx_date"] = r["when"].strftime("%Y-%m-%d")
        r["occurred_at"] = r["when"].isoformat()
    # any generated non-first-seen normal row dated before anomaly must not contain absent category: assert
    for a, p in P.items():
        ab = set(p["absent"]) | {p["anom_first"][0]}
        first = {}
        for r in rows:
            if r["account_id"] == f"acct_{a}" and r["expected_category"] in ab:
                first.setdefault(r["expected_category"], []).append(r)
        for c, lst in first.items():
            assert lst[0]["scenario"] in ("first_seen_category", "decoy_first_seen_small"), (a, c, lst[0]["scenario"], len(lst))
    import json
    (out / "_rows.json").write_text(json.dumps([{k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in r.items() if k != "used"} for r in rows]))
    print(len(rows), "rows")

if __name__ == "__main__":
    main(Path(sys.argv[1]))
