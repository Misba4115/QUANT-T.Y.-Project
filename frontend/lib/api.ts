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
// Backend: No dedicated route yet — your backend dev
// will need to add GET/PUT /auth/me or similar
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
export const financialApi = {
    addBankAccount: (data: BankAccount) =>
        apiClient.post<ApiResponse<BankAccount>>('/banking-accounts/', data),

    getBankAccounts: () =>
        apiClient.get<ApiResponse<BankAccount[]>>('/banking-accounts/'),
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
