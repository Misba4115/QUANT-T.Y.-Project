import apiClient from './axios';
import type {
    LoginCredentials,
    RegisterCredentials,
    AuthResponse,
    User,
    BankAccount,
    DashboardData,
    ApiResponse,
} from '@/types';

// ==========================================
// Auth API
// Backend: POST /auth/register, POST /auth/login
// ==========================================
export const authApi = {
    register: (data: RegisterCredentials) =>
        apiClient.post<ApiResponse<AuthResponse>>('/auth/register', data),

    login: (data: LoginCredentials) =>
        apiClient.post<ApiResponse<AuthResponse>>('/auth/login', data),
};

// ==========================================
// User API
// Backend: router included without prefix
// ==========================================
export const userApi = {
    getProfile: () =>
        apiClient.get<ApiResponse<User>>('/user/profile'),

    updateProfile: (data: Partial<User>) =>
        apiClient.put<ApiResponse<User>>('/user/profile', data),
};

// ==========================================
// Banking API
// Backend: GET /banking-accounts/, POST /banking-accounts/
// ==========================================
export const bankingApi = {
    addBankAccount: (data: Partial<BankAccount>) =>
        apiClient.post<ApiResponse<BankAccount>>('/banking-accounts/', data),

    getBankAccounts: () =>
        apiClient.get<ApiResponse<BankAccount[]>>('/banking-accounts/'),

    updateBankAccount: (accountId: string, data: Partial<BankAccount>) =>
        apiClient.put<ApiResponse<BankAccount>>(`/banking-accounts/${accountId}`, data),

    deleteBankAccount: (accountId: string) =>
        apiClient.delete(`/banking-accounts/${accountId}`),
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
        apiClient.post<ApiResponse<{ run_id: string }>>('/dashboard/generate', {
            widgets,
            time_period: timePeriod,
        }),

    getDashboardResult: (runId: string) =>
        apiClient.get<ApiResponse<DashboardData>>(`/dashboard/result/${runId}`),
};
