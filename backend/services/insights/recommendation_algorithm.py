"""Small deterministic discovery catalogue; no inference or market-data calls.

Schema: 001/003 holdings quantity/units, fund category/name, bank account_type
and current_balance. Wrapper ownership (MF/ETF) and gold/debt exposure overlap
intentionally: these cards describe investment routes, not allocation weights.
"""
from copy import deepcopy
from math import isfinite
from uuid import uuid4
from services.insights.mean_variance import analyze


def platform(key, name, url, fees, ease, minimum, action_url=None, minimum_amount=100):
    return dict(id=key, name=name, url=url, action_url=action_url or url, fees=fees, ease=ease,
                minimum=minimum, minimum_amount=minimum_amount,
                reliability="No comparable audited uptime data available. Review service history and support before choosing.",
                checked_on="2026-09-25", verified=True)


ZERODHA = platform("zerodha", "Zerodha", "https://zerodha.com/charges/",
                   "Delivery brokerage ₹0; statutory, DP and applicable account charges extra.",
                   "Kite trading interface; order types require familiarity.", "One exchange-traded unit at its live price", "https://zerodha.com/open-account/")
GROWW = platform("groww", "Groww", "https://groww.in/pricing",
                 "Equity brokerage: lower of ₹20 or 0.1% per order, minimum ₹5; other charges extra.",
                 "Stocks and funds in one app; compare the order preview.", "One exchange-traded unit at its live price", "https://groww.in/")
UPSTOX = platform("upstox", "Upstox", "https://upstox.com/brokerage-charges/",
                  "Stocks and ETFs: up to ₹20 per order; statutory and other charges extra.",
                  "Trading app with stock, ETF and fund discovery.", "One exchange-traded unit at its live price", "https://upstox.com/trading-account/")
ANGEL = platform("angel", "Angel One", "https://www.angelone.in/support/charges-and-cashbacks/brokerage-charges",
                 "Equity delivery: lower of ₹20 or 0.1% per order, minimum ₹5; other charges extra.",
                 "Trading app with stocks, ETFs and mutual funds.", "One exchange-traded unit at its live price", "https://www.angelone.in/open-demat-account")
COIN = platform("coin", "Zerodha Coin", "https://coin.zerodha.com/",
                "Direct funds: zero commission; scheme expenses and possible exit loads apply.",
                "Separate mutual-fund interface linked to Zerodha.", "Scheme-specific; verify initial lump-sum and SIP minimums", "https://zerodha.com/open-account/")
GROW_MF = platform("groww-mf", "Groww", "https://groww.in/mutual-funds",
                   "Direct plans: scheme expenses and possible exit loads apply; check plan pricing.",
                   "Fund discovery and SIP setup alongside stocks.", "Scheme-specific; verify initial lump-sum and SIP minimums")
UPSTOX_MF = platform("upstox-mf", "Upstox", "https://upstox.com/mutual-funds/",
                     "Direct plans: platform says no transaction charge; scheme expenses and possible exit loads apply.",
                     "Fund browsing and SIP setup in the Upstox app.", "Scheme-specific; verify initial lump-sum and SIP minimums")
ANGEL_MF = platform("angel-mf", "Angel One", "https://www.angelone.in/mutual-funds",
                    "Check direct-plan expenses, exit loads and any current platform fees.",
                    "Fund discovery alongside a trading account.", "Scheme-specific; verify initial lump-sum and SIP minimums")
HDFC = platform("hdfc", "HDFC Bank", "https://www.hdfc.bank.in/fixed-deposit/regular-fixed-deposits",
                "Check premature-withdrawal penalties and the selected deposit terms.",
                "Online deposit booking or branch assistance.", "₹5,000 for a regular FD", minimum_amount=5000)
ICICI = platform("icici", "ICICI Bank", "https://www.icici.bank.in/personal-banking/deposits/fixed-deposit",
                 "Check premature-withdrawal penalties and the selected deposit terms.",
                 "Online deposit booking or branch assistance.", "₹10,000 for a regular FD", minimum_amount=10000)
SBI = platform("sbi", "SBI", "https://sbi.bank.in/web/personal-banking/investments-deposits/deposits/fixed-deposit",
               "Check the chosen term's rate and early-withdrawal terms.",
               "Online SBI, YONO or branch deposit booking.", "₹1,000 for a regular term deposit", minimum_amount=1000)
AXIS = platform("axis", "Axis Bank", "https://www.axis.bank.in/deposits/fixed-deposits",
                "Check the chosen term's rate and early-withdrawal terms.",
                "Online or branch deposit booking.", "₹5,000 for a regular FD", minimum_amount=5000)
KOTAK = platform("kotak", "Kotak Bank", "https://www.kotak.bank.in/en/personal-banking/deposits/fixed-deposit.html",
                 "Check the chosen term's rate and early-withdrawal terms.",
                 "Online or branch deposit booking.", "₹10,000 for a first FD; ₹5,000 thereafter", minimum_amount=10000)


OPTION_DETAILS = {
    "deposit": ["One deposit has one maturity date and one set of bank terms.", "Split the amount across separate deposits with different maturity dates; rates can differ by term."],
    "debt": ["A fund holding shorter-term bonds. Its value can still fall when rates or credit quality change.", "A fund holding very short-term debt. It is not a bank deposit or insured savings account."],
    "mf": ["A fund follows a named stock index, spreading money across its member companies.", "A fund focused on large companies; check whether the specific scheme tracks an index or makes active choices."],
    "etf": ["A broad index fund bought and sold during exchange hours like a share.", "An exchange-traded fund focused on larger companies; its mix can overlap your other stock funds."],
    "gold": ["A market-traded fund that follows gold prices; check its expenses and tracking difference.", "Compare a gold ETF from another fund company for costs, liquidity and tracking difference."],
    "equity": ["Buying one company's shares concentrates your risk in that company.", "Several companies reduce single-company concentration, but each holding still needs monitoring."],
    "crypto": ["Bitcoin is highly volatile and has custody and platform risks.", "Ether is highly volatile and has custody and platform risks."],
}


def category(key, name, explanation, risk, years, rate, liquidity, options, brokers):
    return dict(id=key, name=name, explanation=explanation, risk=risk, min_years=years,
                scenario_rate=rate, liquidity=liquidity,
                options=[dict(id=f"{key}-{i}", name=value, detail=OPTION_DETAILS[key][i]) for i, value in enumerate(options)],
                platforms=brokers)


CATALOG = [
    category("deposit", "Bank fixed deposits", "Put money in a bank for a chosen period at the rate offered when you open it. Early withdrawals can reduce interest.",
             "Low", 1, 6, "Term-dependent; early withdrawal may incur a penalty.",
             ["One fixed deposit", "Several fixed deposits with different end dates"], [HDFC, ICICI, SBI, AXIS, KOTAK]),
    category("debt", "Bond and liquid funds", "A fund that lends to governments or companies. Interest-rate moves and borrower defaults can cause losses.",
             "Medium", 3, 5, "Redemption timing and exit load depend on the scheme.",
             ["Short-term bond fund", "Liquid fund for short-term savings"], [COIN, GROW_MF, UPSTOX_MF, ANGEL_MF]),
    category("mf", "Share mutual funds", "Pool your money with other investors. A diversified equity fund holds shares in many companies.",
             "High", 5, 8, "Scheme-specific redemption and exit-load rules.",
             ["Index fund holding many companies", "Fund focused on large companies"], [COIN, GROW_MF, UPSTOX_MF, ANGEL_MF]),
    category("etf", "Stock market funds (ETFs)", "Buy a basket of investments like a share. Price can differ from the value of the underlying basket.",
             "High", 5, 8, "Exchange hours; spreads and trading volume affect exits.",
             ["ETF tracking the wider stock market", "ETF focused on large companies"], [ZERODHA, GROWW, UPSTOX, ANGEL]),
    category("gold", "Gold funds", "Gold funds track gold prices without storing jewellery. They can diversify holdings but do not provide fixed income.",
             "High", 5, 4, "Exchange hours; spreads and fund expenses apply.",
             ["Gold ETF", "Gold ETF from another fund company"], [ZERODHA, GROWW, UPSTOX, ANGEL]),
    category("equity", "Individual company shares", "Own a small part of a company. Individual shares need research and can lose substantial value.",
             "High", 5, 8, "Exchange hours; liquidity varies by company.",
             ["Shares in one established company", "Shares across several companies"], [ZERODHA, GROWW, UPSTOX, ANGEL]),
    category("crypto", "Crypto (digital assets)", "Digital tokens with extreme price and custody risks. Missing crypto is not a portfolio gap that needs filling.",
             "Very high", 5, 0, "Platform withdrawal restrictions and liquidity vary.",
             ["Bitcoin — educational only", "Ether — educational only"], [
                 platform("coindcx", "CoinDCX", "https://coindcx.com/fees", "Fees vary by product and tier; verify the order quote.", "Spot trading via an exchange account.", "Verify the selected token's current order minimum"),
                 platform("coinswitch", "CoinSwitch", "https://coinswitch.co/", "Review quoted spread and product-specific fees.", "App-based spot purchases.", "From ₹100; verify product eligibility"),
             ]),
]


def available_platforms(db, user_id):
    """Read the provider registry; retain built-in choices until migration 010 is applied."""
    grouped = {item["id"]: deepcopy(item["platforms"]) for item in CATALOG}
    try:
        registry = []
        offset = 0
        while True:
            rows = db.table("investment_platforms").select("*").order("id").range(offset, offset + 499).execute().data or []
            registry.extend(rows)
            if len(rows) < 500:
                break
            offset += 500
        if any(row.get("user_id") is None for row in registry):
            grouped = {item["id"]: [] for item in CATALOG}
        for row in registry:
            if row.get("user_id") not in (None, user_id):
                continue
            for category_id in row.get("category_ids") or []:
                if category_id not in grouped:
                    continue
                entry = {key: row.get(key) for key in ("id", "name", "url", "action_url", "fees", "ease", "minimum", "minimum_amount", "reliability", "checked_on", "verified")}
                if row.get("user_id"):
                    entry.update(url="", action_url="", fees="Check with provider", ease="Your own provider; check its account features.",
                                 minimum="Check with provider", minimum_amount=100,
                                 reliability="Not independently verified. Check the provider's official terms and service history.", checked_on=None, verified=False)
                choices = grouped[category_id]
                choices[:] = [p for p in choices if p["id"] != entry["id"]]
                choices.append(entry)
        for item in CATALOG:
            if not grouped[item["id"]]:
                grouped[item["id"]] = deepcopy(item["platforms"])
    except Exception:
        # Discovery remains usable before deployment applies the provider migration.
        pass
    return grouped


def valid_selection(category_id, option_id, platform_id, db=None, user_id=None):
    if not any(c["id"] == category_id and any(o["id"] == option_id for o in c["options"]) for c in CATALOG):
        return False
    platforms = available_platforms(db, user_id) if db is not None else {c["id"]: c["platforms"] for c in CATALOG}
    return any(p["id"] == platform_id for p in platforms[category_id])


def create_custom_platform(db, user_id, category_id, name):
    if category_id not in {item["id"] for item in CATALOG}:
        raise ValueError("Unknown investment category")
    clean_name = " ".join(name.split())
    if not clean_name or len(clean_name) > 80:
        raise ValueError("Provider name must be 1–80 characters")
    existing = available_platforms(db, user_id)[category_id]
    if any(p["name"].casefold() == clean_name.casefold() for p in existing):
        raise ValueError("This provider is already available for the category")
    row = dict(id=f"custom-{uuid4()}", user_id=user_id, category_ids=[category_id], name=clean_name,
               url=None, action_url=None, fees=None, ease=None, minimum=None, minimum_amount=None,
               reliability=None, checked_on=None, verified=False)
    db.table("investment_platforms").insert(row).execute()
    return row["id"]


def positive(value):
    try:
        number = float(value or 0)
        return isfinite(number) and number > 0
    except (TypeError, ValueError):
        return False


def build_recommendations(db, user_id):
    # Paginated queries avoid PostgREST row caps hiding held categories.
    tables = {"equity": ("equity_holdings", "quantity"), "mf": ("mutual_fund_holdings", "units"),
              "etf": ("etf_holdings", "quantity"), "crypto": ("crypto_holdings", "quantity"),
              "deposit": ("banking_accounts", "current_balance")}
    owned = set()
    proxies = {"etf": ("ETF", "NIFTYBEES"), "gold": ("ETF", "GOLDBEES")}
    for key, (table, amount) in tables.items():
        # Paginate all rows: gold/debt can occur beyond the first API page.
        offset = 0
        while True:
            rows = db.table(table).select("*").eq("user_id", user_id).order(
                {"equity": "equity_holding_id", "mf": "mf_holding_id", "etf": "etf_holding_id",
                 "crypto": "crypto_holding_id", "deposit": "account_id"}[key]
            ).range(offset, offset + 499).execute().data or []
            for row in rows:
                if not positive(row.get(amount)):
                    continue
                if key == "deposit":
                    if row.get("account_type") in {"fixed_deposit", "recurring_deposit"}:
                        owned.add(key)
                    continue
                owned.add(key)
                exposure = key
                if key in {"mf", "etf"}:
                    label = " ".join(str(row.get(field) or "") for field in ("category", "mf_name", "etf_name", "symbol")).lower()
                    if "gold" in label:
                        owned.add("gold")
                        exposure = "gold"
                    if any(token in label for token in ("debt", "liquid", "bond", "gilt", "money market", "overnight")):
                        owned.add("debt")
                        exposure = "debt"
                instrument = row.get("scheme_code" if key == "mf" else "symbol")
                if instrument and exposure not in proxies:
                    proxies[exposure] = ({"equity": "Equity", "mf": "Mutual Fund", "etf": "ETF", "crypto": "Crypto"}[key], str(instrument))
            if len(rows) < 500:
                break
            offset += 500
    profile = db.table("users").select("risk_profile").eq("user_id", user_id).limit(1).execute().data or []
    risk = profile[0].get("risk_profile") if profile else None
    try:
        analysis = analyze(db, user_id, proxies, risk)
    except Exception:
        analysis = {}  # Missing price evidence must not prevent discovery or fabricate metrics.
    result = deepcopy(CATALOG)
    platforms = available_platforms(db, user_id)
    for item in result:
        item["platforms"] = platforms[item["id"]]
        item["owned"] = item["id"] in owned
        item["analysis"] = analysis.get(item["id"], {"status": "unavailable", "reason": "No comparable price history for this category. Scenario calculator only."})
        item["summary"] = f"{item['name']} has {item['risk'].lower()} risk. Consider a horizon of at least {item['min_years']} years and check withdrawal rules. " + (
            "The model balances past average growth against price swings; its allocation is a research example, not a buy instruction."
            if item["analysis"]["status"] == "available" else "There is not enough history to judge its return versus risk; the calculator uses an illustration only.")
        item["reason"] = "Present in your uploaded holdings." if item["owned"] else "Not found in your uploaded holdings; check investments outside QUANT."
        if risk == "conservative" and item["risk"] in {"High", "Very high"}:
            item["reason"] += " Higher risk than your conservative profile; explore for education only."
    return {"categories": sorted(result, key=lambda item: (item["owned"], -item["analysis"].get("weight_pct", -1))), "risk_profile": risk}
