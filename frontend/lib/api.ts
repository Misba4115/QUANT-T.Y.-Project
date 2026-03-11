import apiClient from './axios';
import type {
    LoginCredentials,
    RegisterCredentials,
    AuthResponse,
    User,
    BankAccount,
    DashboardData,
    EquityCreate,
    EquityOut,
    MutualFundCreate,
    MutualFundOut,
    ETFCreate,
    ETFOut,
    CryptoCreate,
    CryptoOut,
    CSVUploadResponse,
    CASUploadResponse,
    BankTransactionCreate,
    BankTransactionOut,
    GoalCreate,
    GoalOut,
} from '@/types';

// ==========================================
// Auth API
// Backend: POST /auth/register, POST /auth/login, GET /auth/me
// ==========================================
export const authApi = {
    register: (data: RegisterCredentials) =>
        apiClient.post<AuthResponse>('/auth/register', data),

    login: (data: LoginCredentials) =>
        apiClient.post<AuthResponse>('/auth/login', data),
};

// ==========================================
// User API
// Backend: GET /auth/me, PUT /user/profile
// ==========================================
export const userApi = {
    getProfile: () =>
        apiClient.get<User>('/auth/me'),

    updateProfile: (data: Partial<User>) =>
        apiClient.put<User>('/user/profile', data),
};

// ==========================================
// Banking API
// Backend: GET /banking-accounts/, POST /banking-accounts/
// ==========================================
export const bankingApi = {
    getBankAccounts: () =>
        apiClient.get<BankAccount[]>('/banking-accounts/'),

    addBankAccount: (data: BankAccount) =>
        apiClient.post<BankAccount>('/banking-accounts/', data),
};

// ==========================================
// Holdings API
// Backend: /holdings/{equity|mf|etf|crypto}
// ==========================================

// Equity Holdings
export const equityApi = {
    getEquityHoldings: () =>
        apiClient.get<EquityOut[]>('/holdings/equity'),

    createEquityHolding: (data: EquityCreate) =>
        apiClient.post<EquityOut>('/holdings/equity', data),

    uploadEquityCSV: (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return apiClient.post<CSVUploadResponse>('/holdings/equity/upload-csv', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },

    deleteEquityHolding: (holdingId: string) =>
        apiClient.delete(`/holdings/equity/${holdingId}`),
};

// Mutual Fund Holdings
export const mutualFundApi = {
    getMutualFundHoldings: () =>
        apiClient.get<MutualFundOut[]>('/holdings/mf'),

    createMutualFundHolding: (data: MutualFundCreate) =>
        apiClient.post<MutualFundOut>('/holdings/mf', data),

    uploadCASFile: (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return apiClient.post<CASUploadResponse>('/holdings/mf/upload-cas', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },

    deleteMutualFundHolding: (holdingId: string) =>
        apiClient.delete(`/holdings/mf/${holdingId}`),
};

// ETF Holdings
export const etfApi = {
    getETFHoldings: () =>
        apiClient.get<ETFOut[]>('/holdings/etf'),

    createETFHolding: (data: ETFCreate) =>
        apiClient.post<ETFOut>('/holdings/etf', data),

    deleteETFHolding: (holdingId: string) =>
        apiClient.delete(`/holdings/etf/${holdingId}`),
};

// Crypto Holdings
export const cryptoApi = {
    getCryptoHoldings: () =>
        apiClient.get<CryptoOut[]>('/holdings/crypto'),

    createCryptoHolding: (data: CryptoCreate) =>
        apiClient.post<CryptoOut>('/holdings/crypto', data),

    deleteCryptoHolding: (holdingId: string) =>
        apiClient.delete(`/holdings/crypto/${holdingId}`),
};

// ==========================================
// Transactions API
// Backend: /transactions/bank
// ==========================================
export const transactionsApi = {
    getBankTransactions: () =>
        apiClient.get<BankTransactionOut[]>('/transactions/bank'),

    createBankTransaction: (data: BankTransactionCreate) =>
        apiClient.post<BankTransactionOut>('/transactions/bank', data),

    deleteBankTransaction: (transactionId: string) =>
        apiClient.delete(`/transactions/bank/${transactionId}`),
};

// ==========================================
// Goals API
// Backend: /goals/
// ==========================================
export const goalsApi = {
    getGoals: () =>
        apiClient.get<GoalOut[]>('/goals/'),

    createGoal: (data: GoalCreate) =>
        apiClient.post<GoalOut>('/goals/', data),

    updateGoal: (goalId: string, data: Partial<GoalCreate>) =>
        apiClient.put<GoalOut>(`/goals/${goalId}`, data),

    deleteGoal: (goalId: string) =>
        apiClient.delete(`/goals/${goalId}`),
};

// ==========================================
// Chat API
// Backend: POST /chat/
// ==========================================
export const chatApi = {
    sendMessage: (message: string, conversationId?: string) =>
        apiClient.post<{reply: string; conversation_id: string}>(
            '/chat/',
            { message, conversation_id: conversationId }
        ),
};

// ==========================================
// Dashboard API
// Backend: POST /dashboard/generate, GET /dashboard/result/{run_id}
// ==========================================
export const dashboardApi = {
    generateDashboard: (
        widgets: string[] = ['net_worth', 'asset_allocation', 'portfolio_performance', 'cashflow', 'tax_tracker', 'top_holdings', 'alerts'],
        timePeriod: string = '1y'
    ) =>
        apiClient.post<{ run_id: string }>('/dashboard/generate', {
            widgets,
            time_period: timePeriod,
        }),

    getDashboardResult: (runId: string) =>
        apiClient.get<DashboardData>(`/dashboard/result/${runId}`),
};
