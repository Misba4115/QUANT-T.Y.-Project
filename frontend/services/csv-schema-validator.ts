/**
 * CSV Schema Validator — Strict validation for CSV files against known financial data schemas.
 *
 * Validates that uploaded CSVs match one of the known formats (equities, ETFs,
 * mutual funds, crypto, transactions) based on the sample_data schemas.
 * Rejects irrelevant or malformed files entirely.
 */

export type CSVSchemaType = 'equities' | 'etfs' | 'mutual_funds' | 'crypto' | 'transactions' | 'unknown';

export interface CSVSchemaDefinition {
    type: CSVSchemaType;
    label: string;
    requiredHeaders: string[];
    optionalHeaders: string[];
    /** Validate a single row's data values */
    validateRow: (row: Record<string, string>, rowIndex: number) => string | null;
}

// ── Schema Definitions (based on sample_data/*.csv formats) ──────────────────

const numericPositive = (val: string, field: string, rowIdx: number): string | null => {
    if (!val || val.trim() === '') return `Row ${rowIdx}: "${field}" is empty`;
    const num = parseFloat(val.replace(/,/g, ''));
    if (isNaN(num)) return `Row ${rowIdx}: "${field}" must be a number (got "${val}")`;
    if (num < 0) return `Row ${rowIdx}: "${field}" must be positive (got ${num})`;
    return null;
};

const numericAny = (val: string, field: string, rowIdx: number): string | null => {
    if (!val || val.trim() === '') return `Row ${rowIdx}: "${field}" is empty`;
    const num = parseFloat(val.replace(/,/g, ''));
    if (isNaN(num)) return `Row ${rowIdx}: "${field}" must be a number (got "${val}")`;
    return null;
};

const nonEmpty = (val: string, field: string, rowIdx: number): string | null => {
    if (!val || val.trim() === '') return `Row ${rowIdx}: "${field}" is required`;
    return null;
};

const SCHEMAS: CSVSchemaDefinition[] = [
    {
        type: 'equities',
        label: 'Equity Holdings',
        requiredHeaders: ['symbol', 'equity_name', 'quantity', 'avg_price'],
        optionalHeaders: ['exchange', 'current_price', 'broker', 'demat_account'],
        validateRow: (row, idx) => {
            return nonEmpty(row['symbol'], 'symbol', idx)
                || nonEmpty(row['equity_name'], 'equity_name', idx)
                || numericPositive(row['quantity'], 'quantity', idx)
                || numericPositive(row['avg_price'], 'avg_price', idx);
        },
    },
    {
        type: 'etfs',
        label: 'ETF Holdings',
        requiredHeaders: ['symbol', 'etf_name', 'quantity', 'avg_price'],
        optionalHeaders: ['isin', 'exchange', 'category', 'current_price', 'broker', 'demat_account'],
        validateRow: (row, idx) => {
            return nonEmpty(row['symbol'], 'symbol', idx)
                || nonEmpty(row['etf_name'], 'etf_name', idx)
                || numericPositive(row['quantity'], 'quantity', idx)
                || numericPositive(row['avg_price'], 'avg_price', idx);
        },
    },
    {
        type: 'mutual_funds',
        label: 'Mutual Fund Holdings',
        requiredHeaders: ['mf_name', 'units', 'avg_nav'],
        optionalHeaders: ['scheme_code', 'isin', 'fund_house', 'category', 'current_nav', 'platform', 'folio_number'],
        validateRow: (row, idx) => {
            return nonEmpty(row['mf_name'], 'mf_name', idx)
                || numericPositive(row['units'], 'units', idx)
                || numericPositive(row['avg_nav'], 'avg_nav', idx);
        },
    },
    {
        type: 'crypto',
        label: 'Crypto Holdings',
        requiredHeaders: ['symbol', 'crypto_name', 'quantity', 'avg_price'],
        optionalHeaders: ['network', 'current_price', 'exchange', 'wallet_address'],
        validateRow: (row, idx) => {
            return nonEmpty(row['symbol'], 'symbol', idx)
                || nonEmpty(row['crypto_name'], 'crypto_name', idx)
                || numericPositive(row['quantity'], 'quantity', idx)
                || numericPositive(row['avg_price'], 'avg_price', idx);
        },
    },
    {
        type: 'transactions',
        label: 'Bank Transactions',
        requiredHeaders: ['tx_date', 'description', 'amount', 'tx_type'],
        optionalHeaders: ['account_id', 'category'],
        validateRow: (row, idx) => {
            return nonEmpty(row['tx_date'], 'tx_date', idx)
                || nonEmpty(row['description'], 'description', idx)
                || numericAny(row['amount'], 'amount', idx)
                || nonEmpty(row['tx_type'], 'tx_type', idx);
        },
    },
];

// ── Validation Result ────────────────────────────────────────────────────────

export interface CSVValidationResult {
    isValid: boolean;
    schemaType: CSVSchemaType;
    schemaLabel: string;
    errors: string[];
    warnings: string[];
    validRowCount: number;
    invalidRowCount: number;
    totalRowCount: number;
}

// ── Main Validation Function ─────────────────────────────────────────────────

/**
 * Detect the CSV schema type from headers and validate all data rows.
 * Returns detailed validation results including per-row errors.
 */
export function validateCSVSchema(
    headers: string[],
    rows: string[][],
): CSVValidationResult {
    const normalizedHeaders = headers.map(h => h.trim().toLowerCase());

    // Try to match a schema
    let bestMatch: CSVSchemaDefinition | null = null;
    let bestScore = 0;

    for (const schema of SCHEMAS) {
        const matchedRequired = schema.requiredHeaders.filter(rh =>
            normalizedHeaders.includes(rh)
        );
        const score = matchedRequired.length / schema.requiredHeaders.length;

        if (score > bestScore) {
            bestScore = score;
            bestMatch = schema;
        }
    }

    // No match found
    if (!bestMatch || bestScore < 0.75) {
        const knownSchemas = SCHEMAS.map(s => `${s.label} (${s.requiredHeaders.join(', ')})`);
        return {
            isValid: false,
            schemaType: 'unknown',
            schemaLabel: 'Unknown',
            errors: [
                'This CSV does not match any supported format.',
                'Supported formats:',
                ...knownSchemas.map(s => `  • ${s}`),
            ],
            warnings: [],
            validRowCount: 0,
            invalidRowCount: rows.length,
            totalRowCount: rows.length,
        };
    }

    // Check for missing required headers
    const missingHeaders = bestMatch.requiredHeaders.filter(
        rh => !normalizedHeaders.includes(rh)
    );

    if (missingHeaders.length > 0) {
        return {
            isValid: false,
            schemaType: bestMatch.type,
            schemaLabel: bestMatch.label,
            errors: [
                `Missing required columns: ${missingHeaders.join(', ')}`,
                `Expected columns: ${bestMatch.requiredHeaders.join(', ')}`,
            ],
            warnings: [],
            validRowCount: 0,
            invalidRowCount: rows.length,
            totalRowCount: rows.length,
        };
    }

    // Validate each row
    const errors: string[] = [];
    const warnings: string[] = [];
    let validRowCount = 0;
    let invalidRowCount = 0;

    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        // Build record with normalized headers
        const record: Record<string, string> = {};
        normalizedHeaders.forEach((h, idx) => {
            record[h] = row[idx]?.trim() ?? '';
        });

        // Skip completely empty rows
        if (Object.values(record).every(v => v === '')) {
            warnings.push(`Row ${i + 1}: Empty row skipped`);
            continue;
        }

        const rowError = bestMatch.validateRow(record, i + 1);
        if (rowError) {
            errors.push(rowError);
            invalidRowCount++;
            // Limit error reporting to first 20 row errors
            if (errors.length >= 20) {
                errors.push(`... and ${rows.length - i - 1} more rows not checked`);
                break;
            }
        } else {
            validRowCount++;
        }
    }

    return {
        isValid: errors.length === 0,
        schemaType: bestMatch.type,
        schemaLabel: bestMatch.label,
        errors,
        warnings,
        validRowCount,
        invalidRowCount,
        totalRowCount: rows.length,
    };
}
