import apiClient from './axios';
import type {
    LoginCredentials,
    RegisterCredentials,
    AuthResponse,
    User,
    BankAccount,
    DashboardRunOut,
    ImportBatch,
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
    ConnectorAccount,
    ConnectorSyncPreview,
    NotificationPreference,
    QuantNotification,
    UserPreference,
    JobSchedule,
    InsightsResult,
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

    googleAuth: (idToken: string) =>
        apiClient.post<AuthResponse>('/auth/google', { id_token: idToken }),

    logout: () => apiClient.post<void>('/auth/logout'),
};

// ==========================================
// User API
// Backend: router included without prefix
// ==========================================
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
    addBankAccount: (data: Partial<BankAccount>) =>
        apiClient.post<BankAccount>('/banking-accounts', data),

    getBankAccounts: () =>
        apiClient.get<BankAccount[]>('/banking-accounts'),

    updateBankAccount: (accountId: string, data: Partial<BankAccount>) =>
        apiClient.put<BankAccount>(`/banking-accounts/${accountId}`, data),

    deleteBankAccount: (accountId: string) =>
        apiClient.delete(`/banking-accounts/${accountId}`),
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

    getAssetTransactions: (assetType: 'equity' | 'mf' | 'etf' | 'crypto') =>
        apiClient.get<Array<Record<string, unknown>>>(`/transactions/${assetType}`),

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
        apiClient.get<GoalOut[]>('/goals'),

    createGoal: (data: GoalCreate) =>
        apiClient.post<GoalOut>('/goals', data),

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
        apiClient.post<{reply: string; conversation_id: string; intent: string; agent: string; citations: import('@/types').ChatCitation[]; warnings: string[]}>(
            '/chat',
            { message, conversation_id: conversationId },
            { timeout: 45000 }
        ),
};

export const importApi = {
    list: () => apiClient.get<ImportBatch[]>('/imports'),
    preview: (file: File, options?: { targetType?: string; columnMapping?: Record<string, string>; fileMode?: 'holdings_snapshot' | 'investment_history' | 'bank_transactions' }) => {
        const form = new FormData();
        form.append('file', file);
        if (options) {
            if (options.targetType) form.append('target_type', options.targetType);
            if (options.columnMapping) form.append('column_mapping', JSON.stringify(options.columnMapping));
            if (options.fileMode) form.append('file_mode', options.fileMode);
        }
        return apiClient.post<ImportBatch>('/imports/preview', form, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 60000,
        });
    },
    commit: (batchId: string, columnMapping: Record<string, string> = {}) =>
        apiClient.post<ImportBatch>(`/imports/${batchId}/commit`, { column_mapping: columnMapping }, { timeout: 60000 }),
    get: (batchId: string) => apiClient.get<ImportBatch>(`/imports/${batchId}`),
    downloadNormalized: (batchId: string) => apiClient.get<Blob>(`/imports/${batchId}/normalized.csv`, { responseType: 'blob' }),
    deletePreview: (batchId: string) => apiClient.delete(`/imports/${batchId}`),
};

export const marketDataApi = {
    sync: () => apiClient.post('/market-data/sync', {}, { timeout: 120000 }),
};

// ==========================================
// Dashboard API
// Backend: POST /dashboard/generate, GET /dashboard/result/{run_id}
// ==========================================
export const dashboardApi = {
    generateDashboard: (
        widgets: string[] = ['net_worth', 'asset_allocation', 'portfolio_performance', 'cashflow', 'tax_tracker', 'top_holdings', 'alerts'],
        timePeriod: string = '1y',
        dateFrom?: string,
        dateTo?: string,
    ) =>
        apiClient.post<DashboardRunOut>('/dashboard/generate', {
            widgets,
            time_period: timePeriod,
            date_from: dateFrom,
            date_to: dateTo,
        }, { timeout: 30000 }),

    getDashboardResult: (runId: string) =>
        apiClient.get<DashboardRunOut>(`/dashboard/result/${runId}`),
    getConfig: () => apiClient.get('/dashboard/config'),
    saveConfig: (data: { widgets: string[]; time_period: string; chart_preferences: Record<string, 'line' | 'area' | 'bar' | 'donut'>; custom_date_from?: string; custom_date_to?: string; currency: 'INR' | 'USD' }) =>
        apiClient.put('/dashboard/config', data),
    requestExport: (format: 'pdf' | 'png', timePeriod: string, dateFrom?: string, dateTo?: string) =>
        apiClient.post<{ report_export_id: string; download_token: string; expires_at: string }>('/dashboard/exports', {
            format, time_period: timePeriod, date_from: dateFrom, date_to: dateTo, chart: 'portfolio_history',
        }),
    downloadExport: (exportId: string, token: string) =>
        apiClient.get(`/dashboard/exports/${exportId}/download`, { params: { token }, responseType: 'blob', timeout: 60000 }),
};

export const connectorsApi = {
    list: () => apiClient.get<ConnectorAccount[]>('/connectors'),
    authorizeUpstox: () => apiClient.post<{ authorization_url: string }>('/connectors/upstox/authorize'),
    previewSync: (accountId: string) => apiClient.post<ConnectorSyncPreview>(`/connectors/${accountId}/sync/preview`),
    commitSync: (runId: string) => apiClient.post(`/connectors/sync/${runId}/commit`),
    revoke: (accountId: string) => apiClient.delete(`/connectors/${accountId}`),
};

export const notificationsApi = {
    list: () => apiClient.get<QuantNotification[]>('/notifications'),
    getPreferences: () => apiClient.get<NotificationPreference>('/notifications/preferences'),
    savePreferences: (data: Partial<NotificationPreference>) => apiClient.put<NotificationPreference>('/notifications/preferences', data),
    mark: (notificationId: string, action: 'read' | 'acknowledge' | 'archive') =>
        apiClient.patch<QuantNotification>(`/notifications/${notificationId}`, { action }),
};

export const jobsApi = {
    list: () => apiClient.get<JobSchedule[]>('/jobs'),
    configurePriceSync: (intervalSeconds: number, enabled: boolean) =>
        apiClient.put<JobSchedule>('/jobs/price-sync', { interval_seconds: intervalSeconds, enabled }),
};

export const ingestionInboxApi = {
    setup: (allowedSenders: string[]) => apiClient.post<{ forwarding_address: string; warning: string }>('/ingestion-inbox/setup', { allowed_senders: allowedSenders }),
    revoke: () => apiClient.delete('/ingestion-inbox/setup'),
};

export const personalizationApi = {
    getPreferences: () => apiClient.get<UserPreference>('/personalization/preferences'),
    savePreferences: (data: Partial<UserPreference>) => apiClient.put<UserPreference>('/personalization/preferences', data),
    resetPreferences: () => apiClient.delete<UserPreference>('/personalization/preferences'),
    latestRisk: () => apiClient.get('/personalization/risk-assessments/latest'),
    assessRisk: (data: Record<string, number | null>) => apiClient.post('/personalization/risk-assessments', data),
};

export const guardianApi = {
    listAlerts: () => apiClient.get<Array<{ guardian_alert_id: string; alert_type: string; severity: string; title: string; explanation: string; evidence: Record<string, unknown>; rule_version: string; created_at: string }>>('/guardian/alerts'),
    submitFeedback: (alertId: string, verdict: 'expected' | 'incorrect' | 'investigate', note?: string) =>
        apiClient.put(`/guardian/alerts/${alertId}/feedback`, { verdict, note }),
};

export const analyticsApi = {
    indicators: (data: { instrument: string; dates: string[]; adjusted_closes: number[]; source: string }) => apiClient.post('/analytics/indicators', data),
    forecast: (data: { instrument: string; dates: string[]; adjusted_closes: number[]; source: string; window?: number }) => apiClient.post('/analytics/forecast', data),
    syntheticSandbox: (seed = 42, days = 252) => apiClient.post('/analytics/synthetic-sandbox', { seed, days }),
};

// ==========================================
// Insights & Trading API
// Backend: POST /insights/generate, GET /insights/latest
// ==========================================
export const insightsApi = {
    generate: () =>
        apiClient.post<InsightsResult>('/insights/generate', {}, { timeout: 45000 }),

    latest: () =>
        apiClient.get<InsightsResult>('/insights/latest', { timeout: 15000 }),
};
