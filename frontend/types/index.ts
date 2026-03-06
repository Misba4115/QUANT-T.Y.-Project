// ==========================================
// QUANT - Type Definitions
// ==========================================

// Auth Types
export interface LoginCredentials {
    email: string;
    password: string;
}

export interface RegisterCredentials {
    fullName: string;
    email: string;
    password: string;
    confirmPassword: string;
}

export interface AuthResponse {
    token: string;
    user: User;
}

// User Types
export interface User {
    id: string;
    fullName: string;
    email: string;
    avatarUrl?: string;
    profileCompletion: number;
    createdAt: string;
}

// Financial Data Types
export interface BankAccount {
    id?: string;
    accountType: 'savings' | 'current' | 'salary' | 'fd' | 'rd';
    bankName: string;
    accountNickname: string;
    currentBalance: number;
    isPrimary: boolean;
}

export interface Investment {
    id: string;
    instrument: string;
    type: 'Equity' | 'Mutual Fund' | 'ETF' | 'Bond' | 'FD';
    quantity: number;
    currentValue: number;
    investedValue: number;
    profitLossPercent: number;
}

export interface Holding {
    instrument: string;
    type: string;
    quantity: number;
    currentValue: number;
    profitLossPercent: number;
}

// Dashboard Types
export interface DashboardData {
    netWorth: number;
    netWorthGrowth: number;
    riskLevel: 'Low' | 'Medium' | 'High';
    monthlyIncome: number;
    monthlyExpenses: number;
    surplus: number;
    taxSaved: number;
    taxLimit: number;
    portfolioHistory: PortfolioDataPoint[];
    assetAllocation: AssetAllocationItem[];
    topHoldings: Holding[];
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

// Quick Stats Types
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

// Financial Category Card
export interface FinancialCategory {
    id: string;
    title: string;
    description: string;
    icon: string;
    isActive: boolean;
}

// API Response wrapper
export interface ApiResponse<T> {
    success: boolean;
    data: T;
    message?: string;
}
