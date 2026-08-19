// ==========================================
// QUANT - Type Definitions
// Aligned with backend Pydantic schemas
// ==========================================

// Auth Types
export interface LoginCredentials {
    email: string;
    password: string;
}

export interface RegisterCredentials {
    name: string;
    email: string;
    password: string;
    confirmPassword?: string;  // frontend-only validation
    phone?: string;
    age?: number;
    monthly_income?: number;
    monthly_expenses?: number;
    primary_goal?: string;
    risk_profile?: string;
}

export interface AuthResponse {
    access_token: string;
    token_type: string;
    is_new_user?: boolean;
}

// User Types (matches backend UserOut)
export interface User {
    user_id: string;
    email: string;
    name: string;
    phone?: string;
    age?: number;
    monthly_income?: number;
    monthly_expenses?: number;
    primary_goal?: string;
    risk_profile?: string;
    created_at: string;
}

// Banking Types (matches backend BankingAccountCreate / BankingAccountOut)
export interface BankAccount {
    account_id?: string;
    user_id?: string;
    account_type: string;  // savings, current, salary, fd, rd, fixed_deposit, recurring_deposit
    account_name: string;
    institution: string;
    account_number?: string;
    current_balance: number;
    currency?: string;
    is_primary: boolean;
    created_at?: string;
    updated_at?: string;
}

// Holdings Types
export interface Holding {
    instrument: string;
    type: string;
    quantity: number;
    current_value: number;
    profit_loss_percent: number | null;
    valuation_status?: 'stored' | 'estimated_cost_basis';
    price_source?: string | null;
    source_timestamp?: string | null;
    last_synced_at?: string | null;
}

// Dashboard Types
export interface DashboardData {
    net_worth: number;
    net_worth_growth: number | null;
    net_worth_growth_status: 'available' | 'insufficient_history';
    risk_level: 'Low' | 'Medium' | 'High' | 'Unavailable';
    stated_risk_profile?: string | null;
    measured_portfolio_risk?: {
        status: string;
        level: 'Low' | 'Medium' | 'High' | null;
        sample_count: number;
        volatility: number | null;
        sharpe_ratio?: number | null;
        cvar_95?: number | null;
        sample_period?: { from: string; to: string } | null;
    };
    monthly_income: number;
    monthly_expenses: number;
    surplus: number;
    tax_saved: number | null;
    tax_limit: number;
    tax_status: string;
    estimated_capital_gains_tax?: number | null;
    tax_rule_version?: string;
    portfolio_history: PortfolioDataPoint[];
    asset_allocation: AssetAllocationItem[];
    top_holdings: Holding[];
    alerts: Alert[];
    history_status: 'available' | 'insufficient_history';
    valuation_coverage: number;
    valuation_status: 'market_valued' | 'partial_estimate' | 'cost_basis_estimate';
    data_as_of: string;
    source_status: Record<string, number>;
}

// Dashboard Run (matches backend DashboardRunOut)
export interface DashboardRunOut {
    run_id: string;
    status: string;   // pending | processing | completed | failed
    result: DashboardData | null;
    error?: string | null;
}

export interface PortfolioDataPoint {
    month: string;
    value: number;
}

export interface AssetAllocationItem {
    name: string;
    value: number;
    color: string;
    amount?: number;
}

export interface ImportRowError {
    row_number: number;
    code: string;
    message: string;
    raw_row?: Record<string, unknown>;
}

export interface ImportMappingDiagnostic {
    code: 'mapping_required';
    message: string;
    reason?: string;
    source_columns: string[];
    automatic_mapping: Record<string, string>;
    suggested_target?: string | null;
    clarification_options?: Array<'holdings_snapshot' | 'investment_history' | 'bank_transactions'>;
    targets: Record<string, {
        required_columns: string[];
        available_columns: string[];
    }>;
}

export interface ImportBatch {
    import_batch_id: string;
    filename: string;
    target_type: string;
    status: 'pending' | 'processing' | 'completed' | 'partial' | 'failed';
    preview_rows: Array<Record<string, unknown>>;
    valid_count: number;
    error_count: number;
    committed_count: number;
    parser_version: string;
    duplicate: boolean;
    column_mapping: {
        source_to_canonical?: Record<string, string>;
        recognized_columns?: string[];
        ignored_columns?: string[];
        user_overrides?: Record<string, string>;
        method?: 'deterministic' | 'llm_headers' | 'user_override' | 'cas_parser';
    };
    row_errors?: ImportRowError[];
    error_message?: string | null;
    created_at?: string | null;
    updated_at?: string | null;
}

export interface Alert {
    id: string;
    type: 'warning' | 'info' | 'opportunity';
    message: string;
    icon: string;
}

// Quick Stats Types (frontend-only, derived from API data)
export interface QuickStats {
    dataCompleteness: number;
    accountsAdded: number;
    holdings: number;
    lastUpdated: string;
}

// Chatbot Types
export interface ChatMessage {
    id: string;
    sender: 'user' | 'bot';
    content: string;
    timestamp: Date;
    citations?: ChatCitation[];
    warnings?: string[];
}

export interface ConnectorAccount {
    connector_account_id: string;
    provider: 'upstox' | 'sandbox';
    display_name: string;
    status: 'pending' | 'connected' | 'reauthorization_required' | 'revoked' | 'error';
    capability_mode: string;
    capabilities: Record<string, boolean>;
    last_successful_sync_at?: string | null;
    last_error?: string | null;
}

export interface ConnectorSyncPreview {
    connector_sync_run_id: string;
    status: string;
    additions: number;
    updates: number;
    duplicates: number;
    conflicts: number;
    preview: Array<Record<string, unknown>>;
}

export interface NotificationPreference {
    in_app_enabled: boolean;
    email_enabled: boolean;
    minimum_severity: 'info' | 'warning' | 'critical';
    quiet_hours_start?: string | null;
    quiet_hours_end?: string | null;
    timezone: string;
    weekly_summary: boolean;
}

export interface QuantNotification {
    notification_id: string;
    event_key: string;
    category: string;
    severity: 'info' | 'warning' | 'critical';
    title: string;
    body: string;
    deep_link?: string | null;
    read_at?: string | null;
    acknowledged_at?: string | null;
    archived_at?: string | null;
    created_at: string;
}

export interface UserPreference {
    persona: 'guided' | 'analytical' | 'minimal';
    explanation_depth: 'concise' | 'balanced' | 'detailed';
    dashboard_emphasis: string[];
    explicit_feedback: Record<string, 'more' | 'less' | 'neutral'>;
}

export interface JobSchedule {
    job_schedule_id: string;
    job_type: string;
    enabled: boolean;
    interval_seconds: number;
    next_run_at: string;
    last_run_at?: string | null;
}

export interface ChatCitation {
    citation_id: string;
    title: string;
    source_type: 'private_import' | 'public_knowledge';
    source_url?: string | null;
    authority?: string | null;
    locator?: string | null;
}

export type ChatOption =
    | 'Stock Market Queries'
    | 'Mutual Fund Queries'
    | 'Investment Queries'
    | 'Portfolio Analysis'
    | 'Tax Saving Queries';

// Financial Category Card (frontend-only UI config)
export interface FinancialCategory {
    id: string;
    title: string;
    description: string;
    icon: string;
    isActive: boolean;
}

// ==========================================
// Holdings Types (Equity, Mutual Fund, ETF, Crypto)
// ==========================================

export interface EquityCreate {
    symbol: string;
    equity_name: string;
    exchange?: string;
    quantity: number;
    avg_price: number;
    broker?: string;
    demat_account?: string;
}

export interface EquityOut extends EquityCreate {
    equity_holding_id: string;
    user_id: string;
    current_price?: number;
    current_value?: number;
    last_synced_at?: string;
    created_at: string;
    updated_at: string;
}

export interface MutualFundCreate {
    mf_name: string;
    scheme_code?: string;
    isin?: string;
    fund_house?: string;
    category?: string;
    units: number;
    avg_nav: number;
    platform?: string;
    folio_number?: string;
}

export interface MutualFundOut extends MutualFundCreate {
    mf_holding_id: string;
    user_id: string;
    current_nav?: number;
    current_value?: number;
    last_synced_at?: string;
    created_at: string;
    updated_at: string;
}

export interface ETFCreate {
    symbol: string;
    etf_name: string;
    isin?: string;
    exchange?: string;
    category?: string;
    quantity: number;
    avg_price: number;
    broker?: string;
    demat_account?: string;
}

export interface ETFOut extends ETFCreate {
    etf_holding_id: string;
    user_id: string;
    current_price?: number;
    current_value?: number;
    last_synced_at?: string;
    created_at: string;
    updated_at: string;
}

export interface CryptoCreate {
    symbol: string;
    crypto_name: string;
    network?: string;
    quantity: number;
    avg_price: number;
    exchange?: string;
    wallet_address?: string;
}

export interface CryptoOut extends CryptoCreate {
    crypto_holding_id: string;
    user_id: string;
    current_price?: number;
    current_value?: number;
    price_source?: string | null;
    last_synced_at?: string;
    created_at: string;
    updated_at: string;
}

export interface CSVUploadResponse {
    preview: Record<string, unknown>[];
    row_count: number;
    inserted: boolean;
}

export interface CASUploadResponse {
    filename: string;
    size_bytes: number;
    content_type?: string;
    preview: string;
    inserted: boolean;
}

// ==========================================
// Transaction Types
// ==========================================

export interface BankTransactionCreate {
    account_id?: string;
    tx_date: string;
    description: string;
    amount: number;
    tx_type: 'debit' | 'credit';
    category?: string;
}

export interface BankTransactionOut extends BankTransactionCreate {
    bank_tx_id: string;
    user_id: string;
    created_at: string;
}

// ==========================================
// Goal Types
// ==========================================

export interface GoalCreate {
    goal_name: string;
    goal_type?: string;
    target_amount?: number;
    current_saved: number;
    target_date?: string;
}

export interface GoalOut extends GoalCreate {
    goal_id: string;
    user_id: string;
    created_at: string;
}

export interface InsightObservation {
    code: string;
    value: number | string;
    evidence_scope: string;
}

export interface InsightReadiness {
    status: 'available' | 'insufficient_data';
    context_version: string;
    data_as_of?: string | null;
    observations: InsightObservation[];
    blockers: string[];
    required_user_decisions: string[];
    algorithm_status: 'not_implemented';
    recommendations: never[];
    evidence_count: number;
}

