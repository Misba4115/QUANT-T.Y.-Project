export interface ImportTemplate {
    id: string;
    label: string;
    description: string;
    filename: string;
    requiredColumns: string[];
    csv: string;
    contentType?: string;
    downloadLabel?: string;
}

export const IMPORT_TEMPLATES: ImportTemplate[] = [
    {
        id: 'investment-transactions',
        label: 'Mixed investment transactions',
        description: 'Canonical tradebook layout for exports from Zerodha, Groww, Upstox, Angel One, ICICI Direct, HDFC Securities, Kotak Securities, and similar brokers.',
        filename: 'quant-investment-transactions-template.csv',
        requiredColumns: ['asset_type', 'tx_date', 'tx_type', 'quantity', 'price'],
        csv: 'transaction_id,tx_date,asset_type,symbol,asset_name,tx_type,quantity,price,amount,platform\n' +
            '1,2026-08-01,Stock,INFY,Infosys Limited,BUY,4,1500,6000,Zerodha\n' +
            '2,2026-08-05,MutualFund,AXISBLUECHIP,Axis Bluechip Fund,SIP,25,40,1000,Groww\n',
    },
    {
        id: 'equities',
        label: 'Equity holdings',
        description: 'Canonical NSE/BSE holdings layout for common broker and demat exports; map the source headers during preview.',
        filename: 'quant-equity-holdings-template.csv',
        requiredColumns: ['symbol', 'equity_name', 'quantity', 'avg_price'],
        csv: 'symbol,equity_name,exchange,quantity,avg_price,current_price,broker,demat_account\n' +
            'INFY,Infosys Limited,NSE,10,1450,1600,Zerodha,Primary Demat\n',
    },
    {
        id: 'broker-tradebook',
        label: 'Broker tradebook',
        description: 'Buy/sell sample for common Indian broker exports. This is an accepted normalization layout, not a claim that every broker uses identical headers.',
        filename: 'quant-broker-tradebook-template.csv',
        requiredColumns: ['tx_date', 'tx_type', 'symbol', 'quantity', 'price'],
        csv: 'trade_id,tx_date,tx_type,symbol,exchange,quantity,price,fees,broker\n' +
            'T-001,2026-08-01,buy,INFY,NSE,4,1500,20,Zerodha\n' +
            'T-002,2026-08-12,sell,INFY,NSE,1,1600,8,Zerodha\n',
    },
    {
        id: 'mutual-funds',
        label: 'Mutual funds',
        description: 'Fund units, acquisition NAV, and optional current NAV.',
        filename: 'quant-mutual-funds-template.csv',
        requiredColumns: ['mf_name', 'units', 'avg_nav'],
        csv: 'mf_name,scheme_code,isin,fund_house,category,units,avg_nav,current_nav,platform,folio_number\n' +
            'Example Flexi Cap Fund,123456,INF000000001,Example AMC,Equity,125.5,82.4,91.2,CAMS,XXXX001\n',
    },
    {
        id: 'mf-sip-history',
        label: 'Mutual fund & SIP history',
        description: 'Purchase, SIP, redemption, and switch transactions exported by an AMC, registrar, bank, or investment platform.',
        filename: 'quant-mf-sip-history-template.csv',
        requiredColumns: ['tx_date', 'tx_type', 'mf_name', 'units', 'nav'],
        csv: 'transaction_id,tx_date,tx_type,mf_name,scheme_code,isin,folio_number,units,nav,amount,platform\n' +
            'MF-001,2026-08-05,sip,Example Flexi Cap Fund,123456,INF000000001,XXXX001,12.5,80,1000,CAMS\n' +
            'MF-002,2026-08-10,redemption,Example Flexi Cap Fund,123456,INF000000001,XXXX001,5,82,410,CAMS\n',
    },
    {
        id: 'etfs',
        label: 'ETF holdings',
        description: 'Exchange-traded fund units held through a broker.',
        filename: 'quant-etf-holdings-template.csv',
        requiredColumns: ['symbol', 'etf_name', 'quantity', 'avg_price'],
        csv: 'symbol,etf_name,isin,exchange,category,quantity,avg_price,current_price,broker,demat_account\n' +
            'NIFTYBEES,Nippon India ETF Nifty BeES,INF000000002,NSE,Index,20,245,252,Zerodha,Primary Demat\n',
    },
    {
        id: 'crypto',
        label: 'Crypto holdings',
        description: 'Token quantities held on an exchange or wallet.',
        filename: 'quant-crypto-holdings-template.csv',
        requiredColumns: ['symbol', 'crypto_name', 'quantity', 'avg_price'],
        csv: 'symbol,crypto_name,network,quantity,avg_price,current_price,exchange,wallet_address\n' +
            'BTC,Bitcoin,Bitcoin,0.05,4500000,5000000,CoinDCX,\n',
    },
    {
        id: 'bank-transactions',
        label: 'Bank transactions',
        description: 'Credits and debits from a bank statement export.',
        filename: 'quant-bank-transactions-template.csv',
        requiredColumns: ['tx_date', 'description', 'amount', 'tx_type'],
        csv: 'tx_date,description,amount,tx_type,category\n' +
            '2026-08-01,Monthly salary,100000,credit,Income\n' +
            '2026-08-02,Grocery purchase,2500,debit,Food\n',
    },
    {
        id: 'cas-text-pdf-guide',
        label: 'CAS PDF upload guide',
        description: 'Use a password-free, text-based CAMS/KFintech or NSDL/CDSL CAS PDF. Scans need OCR and are rejected for manual review at this stage.',
        filename: 'quant-cas-upload-guide.txt',
        requiredColumns: [],
        contentType: 'text/plain; charset=utf-8',
        downloadLabel: 'Download guide',
        csv: 'Accepted: password-free, text-based CAMS/KFintech mutual-fund CAS or NSDL/CDSL demat CAS PDF.\nNot auto-committed: scanned/image-only, password-protected, or low-confidence documents.\nUpload the original PDF on the Import data page and review every normalized row before confirming.\n',
    },
];
