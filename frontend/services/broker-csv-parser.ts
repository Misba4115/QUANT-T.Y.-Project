/**
 * Broker CSV Parser — Parse CSV exports from Indian broker platforms.
 *
 * Each broker has a slightly different export format. This service normalizes
 * them all into a common HoldingRow format that can be synced to the backend.
 *
 * Since no free, legitimate broker APIs exist for all platforms, we rely on
 * users exporting CSV/Excel files directly from their broker dashboards.
 */

export interface BrokerHoldingRow {
    symbol: string;
    name: string;
    exchange: string;
    quantity: number;
    avgPrice: number;
    currentPrice: number;
    broker: string;
}

export interface BrokerCSVParseResult {
    broker: string;
    holdings: BrokerHoldingRow[];
    errors: string[];
    rawRowCount: number;
}

export interface BrokerInfo {
    id: string;
    name: string;
    icon: string;
    color: string;
    bgColor: string;
    exportInstructions: string[];
    /** Expected column names in the broker's CSV export */
    expectedColumns: string[];
}

// ── Broker Definitions ───────────────────────────────────────────────────────

export const BROKER_DEFINITIONS: BrokerInfo[] = [
    {
        id: 'zerodha',
        name: 'Zerodha Kite',
        icon: 'Z',
        color: 'text-green-700',
        bgColor: 'bg-green-50 border-green-200',
        exportInstructions: [
            'Log into Kite (kite.zerodha.com)',
            'Go to Portfolio → Holdings',
            'Click the download icon (⬇) at the top right',
            'Select "Download as CSV"',
            'Upload the downloaded file here',
        ],
        expectedColumns: ['tradingsymbol', 'instrument', 'quantity', 'average_price'],
    },
    {
        id: 'groww',
        name: 'Groww',
        icon: 'G',
        color: 'text-blue-700',
        bgColor: 'bg-blue-50 border-blue-200',
        exportInstructions: [
            'Log into Groww (groww.in)',
            'Go to Dashboard → Stocks',
            'Click on "Download Portfolio Report"',
            'Select CSV format',
            'Upload the downloaded file here',
        ],
        expectedColumns: ['symbol', 'company_name', 'quantity', 'avg_price'],
    },
    {
        id: 'upstox',
        name: 'Upstox',
        icon: 'U',
        color: 'text-purple-700',
        bgColor: 'bg-purple-50 border-purple-200',
        exportInstructions: [
            'Log into Upstox Pro (pro.upstox.com)',
            'Go to Portfolio → Holdings',
            'Click the "Export" or download button',
            'Select CSV format',
            'Upload the downloaded file here',
        ],
        expectedColumns: ['symbol', 'company', 'qty', 'avg_cost'],
    },
    {
        id: 'angelone',
        name: 'Angel One',
        icon: 'A',
        color: 'text-red-700',
        bgColor: 'bg-red-50 border-red-200',
        exportInstructions: [
            'Log into Angel One (angelone.in)',
            'Go to Portfolio → Holdings',
            'Click the download/export button',
            'Download as CSV',
            'Upload the downloaded file here',
        ],
        expectedColumns: ['scrip_name', 'symbol', 'quantity', 'avg_price'],
    },
    {
        id: 'icici_direct',
        name: 'ICICI Direct',
        icon: 'I',
        color: 'text-orange-700',
        bgColor: 'bg-orange-50 border-orange-200',
        exportInstructions: [
            'Log into ICICI Direct (icicidirect.com)',
            'Go to Portfolio → Equity',
            'Click "Download" at the top',
            'Select CSV/Excel format',
            'Upload the downloaded file here',
        ],
        expectedColumns: ['stock_symbol', 'stock_name', 'quantity', 'buy_avg'],
    },
];

// ── Column mapping per broker ────────────────────────────────────────────────

interface ColumnMap {
    symbol: string[];
    name: string[];
    quantity: string[];
    avgPrice: string[];
    currentPrice: string[];
    exchange: string[];
}

const BROKER_COLUMN_MAPS: Record<string, ColumnMap> = {
    zerodha: {
        symbol: ['tradingsymbol', 'symbol', 'instrument'],
        name: ['instrument', 'tradingsymbol', 'company'],
        quantity: ['quantity', 'qty', 'net_qty'],
        avgPrice: ['average_price', 'avg_price', 'buy_avg'],
        currentPrice: ['last_price', 'ltp', 'current_price'],
        exchange: ['exchange'],
    },
    groww: {
        symbol: ['symbol', 'stock_symbol', 'scrip'],
        name: ['company_name', 'name', 'stock_name'],
        quantity: ['quantity', 'qty', 'shares'],
        avgPrice: ['avg_price', 'average_price', 'buy_avg'],
        currentPrice: ['current_price', 'ltp', 'market_price'],
        exchange: ['exchange'],
    },
    upstox: {
        symbol: ['symbol', 'tradingsymbol', 'scrip'],
        name: ['company', 'instrument_name', 'name'],
        quantity: ['qty', 'quantity', 'net_qty'],
        avgPrice: ['avg_cost', 'average_price', 'buy_price'],
        currentPrice: ['ltp', 'current_price', 'market_price'],
        exchange: ['exchange', 'segment'],
    },
    angelone: {
        symbol: ['symbol', 'scrip_name', 'tradingsymbol'],
        name: ['scrip_name', 'company', 'name'],
        quantity: ['quantity', 'qty', 'net_qty'],
        avgPrice: ['avg_price', 'buy_avg', 'average_price'],
        currentPrice: ['ltp', 'current_price', 'close'],
        exchange: ['exchange'],
    },
    icici_direct: {
        symbol: ['stock_symbol', 'symbol', 'scrip_code'],
        name: ['stock_name', 'company_name', 'scrip_name'],
        quantity: ['quantity', 'qty', 'holding_qty'],
        avgPrice: ['buy_avg', 'avg_price', 'purchase_price'],
        currentPrice: ['current_price', 'ltp', 'market_price'],
        exchange: ['exchange'],
    },
};

// ── Generic parser that auto-detects broker ──────────────────────────────────

function findColumn(headers: string[], candidates: string[]): number {
    const normalized = headers.map(h => h.trim().toLowerCase().replace(/[\s-]+/g, '_'));
    for (const candidate of candidates) {
        const idx = normalized.indexOf(candidate.toLowerCase());
        if (idx !== -1) return idx;
    }
    return -1;
}

/**
 * Auto-detect which broker the CSV is from and parse it.
 */
export function parseBrokerCSV(
    headers: string[],
    rows: string[][],
    brokerId?: string,
): BrokerCSVParseResult {
    // Try to detect broker
    let detectedBroker = brokerId;
    let bestScore = 0;

    if (!detectedBroker) {
        for (const [id, colMap] of Object.entries(BROKER_COLUMN_MAPS)) {
            const allCandidates = [
                ...colMap.symbol,
                ...colMap.name,
                ...colMap.quantity,
                ...colMap.avgPrice,
            ];
            const matchCount = allCandidates.filter(c =>
                headers.some(h => h.trim().toLowerCase().replace(/[\s-]+/g, '_') === c.toLowerCase())
            ).length;
            if (matchCount > bestScore) {
                bestScore = matchCount;
                detectedBroker = id;
            }
        }
    }

    if (!detectedBroker || !BROKER_COLUMN_MAPS[detectedBroker]) {
        // Fallback: try generic column names
        detectedBroker = 'generic';
    }

    const colMap = BROKER_COLUMN_MAPS[detectedBroker] || BROKER_COLUMN_MAPS['zerodha'];
    const brokerDef = BROKER_DEFINITIONS.find(b => b.id === detectedBroker);

    const symbolIdx = findColumn(headers, colMap.symbol);
    const nameIdx = findColumn(headers, colMap.name);
    const qtyIdx = findColumn(headers, colMap.quantity);
    const avgPriceIdx = findColumn(headers, colMap.avgPrice);
    const currentPriceIdx = findColumn(headers, colMap.currentPrice);
    const exchangeIdx = findColumn(headers, colMap.exchange);

    const errors: string[] = [];

    if (symbolIdx === -1) errors.push('Could not find a symbol/tradingsymbol column');
    if (qtyIdx === -1) errors.push('Could not find a quantity column');
    if (avgPriceIdx === -1) errors.push('Could not find an average price column');

    if (errors.length > 0) {
        return {
            broker: brokerDef?.name || detectedBroker || 'Unknown',
            holdings: [],
            errors,
            rawRowCount: rows.length,
        };
    }

    const holdings: BrokerHoldingRow[] = [];

    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const symbol = row[symbolIdx]?.trim();
        if (!symbol) continue;

        const qty = parseFloat(row[qtyIdx]?.replace(/,/g, '') || '0');
        const avg = parseFloat(row[avgPriceIdx]?.replace(/,/g, '') || '0');

        if (isNaN(qty) || qty <= 0) {
            errors.push(`Row ${i + 1}: Invalid quantity for ${symbol}`);
            continue;
        }

        holdings.push({
            symbol,
            name: nameIdx !== -1 ? (row[nameIdx]?.trim() || symbol) : symbol,
            exchange: exchangeIdx !== -1 ? (row[exchangeIdx]?.trim() || 'NSE') : 'NSE',
            quantity: qty,
            avgPrice: isNaN(avg) ? 0 : avg,
            currentPrice: currentPriceIdx !== -1 ? parseFloat(row[currentPriceIdx]?.replace(/,/g, '') || '0') || 0 : 0,
            broker: brokerDef?.name || detectedBroker || 'Unknown',
        });
    }

    return {
        broker: brokerDef?.name || detectedBroker || 'Unknown',
        holdings,
        errors: errors.length > 20 ? [...errors.slice(0, 20), `... and ${errors.length - 20} more`] : errors,
        rawRowCount: rows.length,
    };
}
