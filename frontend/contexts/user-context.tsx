'use client';

import React, { createContext, useContext, useReducer, useEffect, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import type { User } from '@/types';
import { authApi, userApi } from '@/lib/api';

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
    login: (user: User) => void;
    logout: () => Promise<void>;
    isNewUser: boolean;
    setNewUser: (val: boolean) => void;
    completeOnboarding: () => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

// ==========================================
// Provider
// ==========================================
export function UserProvider({ children }: { children: ReactNode }) {
    const router = useRouter();
    const [state, dispatch] = useReducer(userReducer, initialState);
    const [isNewUser, setIsNewUser] = React.useState(false);

    useEffect(() => {
        // Restore the authenticated user from the HttpOnly session cookie.
        // A hard refresh must not destroy an otherwise valid server session.
        userApi.getProfile()
            .then((res) => dispatch({ type: 'SET_USER', payload: res.data }))
            .catch(() => dispatch({ type: 'LOGOUT' }));
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

    const login = (user: User) => {
        dispatch({ type: 'SET_USER', payload: user });
    };

    const logout = async () => {
        localStorage.removeItem('quant_onboarding_complete');
        setIsNewUser(false);
        dispatch({ type: 'LOGOUT' });
        try {
            await authApi.logout();
        } finally {
            router.push('/login');
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
