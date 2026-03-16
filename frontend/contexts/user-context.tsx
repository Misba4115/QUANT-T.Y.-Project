'use client';

import React, { createContext, useContext, useReducer, useEffect, type ReactNode } from 'react';
import type { User } from '@/types';

// ==========================================
// State & Actions
// ==========================================
interface UserState {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
}

type UserAction =
    | { type: 'SET_USER'; payload: User }
    | { type: 'LOGOUT' }
    | { type: 'SET_LOADING'; payload: boolean };

const initialState: UserState = {
    user: null,
    isAuthenticated: false,
    isLoading: true,
};

function userReducer(state: UserState, action: UserAction): UserState {
    switch (action.type) {
        case 'SET_USER':
            return { user: action.payload, isAuthenticated: true, isLoading: false };
        case 'LOGOUT':
            return { user: null, isAuthenticated: false, isLoading: false };
        case 'SET_LOADING':
            return { ...state, isLoading: action.payload };
        default:
            return state;
    }
}

// ==========================================
// Context
// ==========================================
interface UserContextType extends UserState {
    login: (user: User, token: string) => void;
    logout: () => void;
    isNewUser: boolean;
    setNewUser: (val: boolean) => void;
    completeOnboarding: () => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

// ==========================================
// Provider
// ==========================================
export function UserProvider({ children }: { children: ReactNode }) {
    const [state, dispatch] = useReducer(userReducer, initialState);
    const [isNewUser, setIsNewUser] = React.useState(false);

    useEffect(() => {
        // Check for existing session on mount
        const token = localStorage.getItem('quant_token');
        const storedUser = localStorage.getItem('quant_user');

        if (token && storedUser) {
            try {
                const user = JSON.parse(storedUser) as User;
                dispatch({ type: 'SET_USER', payload: user });
            } catch {
                dispatch({ type: 'LOGOUT' });
            }
        } else {
            dispatch({ type: 'SET_LOADING', payload: false });
        }
    }, []);

    const setNewUser = (val: boolean) => {
        setIsNewUser(val);
        if (val) {
            localStorage.removeItem('quant_onboarding_complete');
        }
    };

    const completeOnboarding = () => {
        setIsNewUser(false);
        localStorage.setItem('quant_onboarding_complete', 'true');
    };

    const login = (user: User, token: string) => {
        localStorage.setItem('quant_token', token);
        localStorage.setItem('quant_user', JSON.stringify(user));
        dispatch({ type: 'SET_USER', payload: user });
    };

    const logout = () => {
        localStorage.removeItem('quant_token');
        localStorage.removeItem('quant_user');
        localStorage.removeItem('quant_onboarding_complete');
        setIsNewUser(false);
        dispatch({ type: 'LOGOUT' });
        if (typeof window !== 'undefined') {
            window.location.href = '/login';
        }
    };

    return (
        <UserContext.Provider value={{ ...state, login, logout, isNewUser, setNewUser, completeOnboarding }}>
            {children}
        </UserContext.Provider>
    );
}

// ==========================================
// Hook
// ==========================================
export function useUser() {
    const context = useContext(UserContext);
    if (!context) {
        throw new Error('useUser must be used within a UserProvider');
    }
    return context;
}
