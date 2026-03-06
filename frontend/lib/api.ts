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
// ==========================================
export const authApi = {
    register: (data: RegisterCredentials) =>
        apiClient.post<ApiResponse<AuthResponse>>('/auth/register', data),

    login: (data: LoginCredentials) =>
        apiClient.post<ApiResponse<AuthResponse>>('/auth/login', data),
};

// ==========================================
// User API
// ==========================================
export const userApi = {
    getProfile: () =>
        apiClient.get<ApiResponse<User>>('/user/profile'),

    updateProfile: (data: Partial<User>) =>
        apiClient.put<ApiResponse<User>>('/user/profile', data),
};

// ==========================================
// Financial Data API
// ==========================================
export const financialApi = {
    addBankAccount: (data: BankAccount) =>
        apiClient.post<ApiResponse<BankAccount>>('/financial-data', data),

    getBankAccounts: () =>
        apiClient.get<ApiResponse<BankAccount[]>>('/financial-data/accounts'),
};

// ==========================================
// Dashboard API
// ==========================================
export const dashboardApi = {
    getDashboardData: () =>
        apiClient.get<ApiResponse<DashboardData>>('/dashboard'),
};
