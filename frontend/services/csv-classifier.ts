/**
 * CSV Classifier — Categorize parsed CSV rows into Equity, ETF, or Mutual Fund.
 *
 * This runs entirely on the frontend. It takes raw PapaParse output
 * (headers + rows) and returns classified holdings ready to send to the
 * existing backend POST endpoints.
 *
 * Backend schemas referenced:
 *   EquityCreate   → { symbol, equity_name, exchange?, quantity, avg_price, broker?, demat_account? }
 *   MutualFundCreate → { mf_name, scheme_code?, isin?, fund_house?, category?, units, avg_nav, platform?, folio_number? }
 *   ETFCreate      → { symbol, etf_name, isin?, exchange?, category?, quantity, avg_price, broker?, demat_account? }
 */

import type { EquityCreate, MutualFundCreate, ETFCreate } from '@/types';

// ── Heuristic Keywords ───────────────────────────────────────────────────────

const ETF_KEYWORDS = [
    'ETF', 'BEES', 'NIFTYBEES', 'BANKBEES', 'GOLDBEES', 'JUNIORBEES',
    'LIQUIDBEES', 'SETFNIF50', 'SETFNN50', 'MON100',
];

const MF_KEYWORDS = [
    'FUND', 'DIRECT', 'GROWTH', 'DIVIDEND', 'IDCW', 'FLEXI', 'SIP',
    'SCHEME', 'PLAN', 'REGULAR', 'NAV',
];

// ── Types ────────────────────────────────────────────────────────────────────

export type HoldingCategory = 'equity' | 'etf' | 'mf';

export interface ClassifiedRow {
    category: HoldingCategory;
    original: Record<string, string>;      // raw CSV row (header→value)
    equity?: EquityCreate;
    etf?: ETFCreate;
    mf?: MutualFundCreate;
}

export interface ClassificationResult {
    equity: ClassifiedRow[];
    etf: ClassifiedRow[];
    mf: ClassifiedRow[];
    skipped: Record<string, string>[];     // rows that couldn't be parsed
    total: number;
}

// ── Column Mapping Helpers ───────────────────────────────────────────────────
// CSV files from different brokers use different column names. We normalise
// them to lowercase and try several common variants.

function findCol(row: Record<string, string>, ...candidates: string[]): string {
    for (const c of candidates) {
        const key = Object.keys(row).find((k) => k.trim().toLowerCase() === c);
        if (key && row[key]?.trim()) return row[key].trim();
    }
    return '';
}

function parseNumber(raw: string): number {
    if (!raw) return 0;
    return parseFloat(raw.replace(/,/g, '')) || 0;
}

// ── Classify a Single Row ────────────────────────────────────────────────────

function classifyName(symbol: string, name: string): HoldingCategory {
    const upper = `${symbol} ${name}`.toUpperCase();

    // Check MF first — more specific keywords
    if (MF_KEYWORDS.some((kw) => upper.includes(kw))) return 'mf';

    // Then ETF
    if (ETF_KEYWORDS.some((kw) => upper.includes(kw))) return 'etf';

    // Default → equity
    return 'equity';
}

// ── Main Classifier ──────────────────────────────────────────────────────────

/**
 * Takes headers + rows from PapaParse and classifies each into equity / etf / mf.
 * Returns objects shaped to match the backend Create schemas.
 */
export function classifyCSVData(
    headers: string[],
    rows: string[][],
): ClassificationResult {
    const result: ClassificationResult = {
        equity: [],
        etf: [],
        mf: [],
        skipped: [],
        total: rows.length,
    };

    for (const row of rows) {
        // Build header→value map
        const record: Record<string, string> = {};
        headers.forEach((h, i) => {
            record[h.trim().toLowerCase()] = row[i]?.trim() ?? '';
        });

        // Extract common fields
        const symbol = findCol(record, 'stock symbol', 'symbol', 'instrument', 'tradingsymbol', 'scrip');
        const name = findCol(record, 'name', 'company', 'company name', 'instrument name', 'scrip name') || symbol;
        const qtyRaw = findCol(record, 'quantity', 'qty', 'net qty', 'total qty');
        const priceRaw = findCol(record, 'average price', 'avg price', 'avg_price', 'avg. price', 'buy avg', 'buy price', 'avg cost', 'avg nav', 'nav');
        const isin = findCol(record, 'isin');
        const exchange = findCol(record, 'exchange') || 'NSE';

        const quantity = parseNumber(qtyRaw);
        const price = parseNumber(priceRaw);

        if (!symbol || quantity <= 0) {
            result.skipped.push(record);
            continue;
        }

        const category = classifyName(symbol, name);

        const classified: ClassifiedRow = {
            category,
            original: record,
        };

        switch (category) {
            case 'equity':
                classified.equity = {
                    symbol,
                    equity_name: name,
                    exchange,
                    quantity,
                    avg_price: price,
                };
                break;

            case 'etf':
                classified.etf = {
                    symbol,
                    etf_name: name,
                    isin: isin || undefined,
                    exchange,
                    quantity,
                    avg_price: price,
                };
                break;

            case 'mf':
                classified.mf = {
                    mf_name: name,
                    isin: isin || undefined,
                    units: quantity,
                    avg_nav: price,
                };
                break;
        }

        result[category].push(classified);
    }

    return result;
}
