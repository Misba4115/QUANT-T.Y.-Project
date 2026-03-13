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
    age: number;
    monthly_income: number;
    monthly_expenses: number;
    primary_goal: string;
    risk_profile?: string;
}

export interface AuthResponse {
    access_token: string;
    token_type: string;
    user: User;
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
    account_type: 'savings' | 'current' | 'fixed_deposit' | 'recurring_deposit';
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
    profit_loss_percent: number;
}

// Dashboard Types
export interface DashboardData {
    net_worth: number;
    net_worth_growth: number;
    risk_level: 'Low' | 'Medium' | 'High';
    monthly_income: number;
    monthly_expenses: number;
    surplus: number;
    tax_saved: number;
    tax_limit: number;
    portfolio_history: PortfolioDataPoint[];
    asset_allocation: AssetAllocationItem[];
    top_holdings: Holding[];
    alerts: Alert[];
}

export interface PortfolioDataPoint {
    month: string;
    value: number;
}

export interface AssetAllocationItem {
    name: string;
    value: number;
    color: string;
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
    last_synced_at?: string;
    created_at: string;
    updated_at: string;
}

export interface CSVUploadResponse {
    preview: Record<string, any>[];
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

