"""
Tax Optimization Engine — Indian Tax Rules + RAG
"""
# Rule constants (as per Indian Income Tax Act)
SECTION_80C_LIMIT = 150_000          # ₹1,50,000 per financial year
LTCG_EQUITY_EXEMPTION = 100_000      # ₹1,00,000 free per year
LTCG_EQUITY_RATE = 0.10              # 10% above exemption (equity held > 1 yr)
STCG_EQUITY_RATE = 0.15              # 15% (equity held < 1 yr)
LTCG_HOLDING_PERIOD_DAYS = 365       # 1 year for equity / ETFs


def run_tax_agent(user_id: str, db) -> dict:
    """
    Estimate tax exposure and suggest optimizations.

    Steps:
      1. Fetch user income and profile (monthly_income → annualise)
      2. Fetch all equity + ETF + MF transactions to compute:
           a. Realised LTCG (held > 1 year, equity > ₹1L → 10%)
           b. Realised STCG (held < 1 year → 15%)
      3. Compute 80C headroom:
           a. Check ELSS MF investments in current FY
           b. Check PPF / LIC from goals/transactions if tagged
           c. Headroom = ₹1,50,000 - already_invested_80c
      4. Compute unrealised LTCG (tax-harvesting opportunities)
      5. Use RAG to fetch and include plain-language tax tips from Qdrant

    Returns:
        {
            "section_80c_used": float,
            "section_80c_headroom": float,
            "realised_ltcg": float,
            "realised_stcg": float,
            "estimated_ltcg_tax": float,
            "estimated_stcg_tax": float,
            "tax_suggestions": [str, ...]
        }

    TODO: implement
    """
    raise NotImplementedError("Tax agent not implemented yet")
