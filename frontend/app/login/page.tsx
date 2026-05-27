'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, Mail, Lock, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useUser } from '@/contexts/user-context';
import { authApi, userApi } from '@/lib/api';

const loginSchema = z.object({
    email: z.string().email('Please enter a valid email address'),
    password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
    const router = useRouter();
    const { login } = useUser();
    const [showPassword, setShowPassword] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [message, setMessage] = useState<string | null>(null);

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<LoginFormData>({
        resolver: zodResolver(loginSchema),
    });

    // ── Google Sign-In ──────────────────────────────────────
    const handleGoogleResponse = useCallback(async (response: any) => {
        setIsSubmitting(true);
        setError(null);
        try {
            const res = await authApi.googleAuth(response.credential);
            const token = res.data.access_token;
            localStorage.setItem('quant_token', token);
            const profileRes = await userApi.getProfile();
            const user = profileRes.data;
            login(user, token);
            setMessage('Login successful! Redirecting...');
            setTimeout(() => {
                router.push(res.data.is_new_user ? '/input-data' : '/dashboard');
            }, 500);
        } catch (err: any) {
            localStorage.removeItem('quant_token');
            const msg = err.response?.data?.detail || 'Google sign-in failed';
            setError(msg);
        } finally {
            setIsSubmitting(false);
        }
    }, [login, router]);

    useEffect(() => {
        const script = document.createElement('script');
        script.src = 'https://accounts.google.com/gsi/client';
        script.async = true;
        script.defer = true;
        script.onload = () => {
            const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
            if (clientId && clientId !== 'YOUR_GOOGLE_CLIENT_ID_HERE' && (window as any).google) {
                (window as any).google.accounts.id.initialize({
                    client_id: clientId,
                    callback: handleGoogleResponse,
                });

                const btnContainer = document.getElementById('googleSignInDiv');
                if (btnContainer) {
                    (window as any).google.accounts.id.renderButton(
                        btnContainer,
                        { theme: 'outline', size: 'large', text: 'signin_with', width: '400' }
                    );
                }
            }
        };
        document.head.appendChild(script);
        return () => { document.head.removeChild(script); };
    }, [handleGoogleResponse]);

    const onSubmit = async (data: LoginFormData) => {
        setIsSubmitting(true);
        setError(null);
        setMessage(null);
        try {
            // Step 1: perform login request
            const loginRes = await authApi.login(data);
            const token = loginRes.data.access_token;

            // Step 2: Store token FIRST so axios interceptor can use it
            localStorage.setItem('quant_token', token);

            // Step 3: fetch profile (now token is in localStorage, axios will use it)
            const profileRes = await userApi.getProfile();
            const user = profileRes.data;

            // Step 4: Update context
            login(user, token);

            setMessage('Login successful! Redirecting...');
            setTimeout(() => {
                router.push('/dashboard');
            }, 500);
        } catch (err: any) {
            // Clear token on error
            localStorage.removeItem('quant_token');
            const msg = err.response?.data?.detail || err.message || 'Login failed';
            setError(msg);
            console.error('login error', err);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="flex min-h-screen">
            {/* Left – Branding Panel */}
            <motion.div
                initial={{ x: -40, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ duration: 0.6, ease: 'easeOut' }}
                className="hidden w-1/2 flex-col justify-between bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950 p-12 lg:flex"
            >
                <div>
                    <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/10 backdrop-blur-sm">
                            <span className="text-xl font-bold text-white">Q</span>
                        </div>
                        <span className="text-2xl font-bold text-white">QUANT</span>
                    </div>
                </div>

                <div className="space-y-6">
                    <h1 className="text-4xl font-bold leading-tight text-white">
                        Smart Financial
                        <br />
                        <span className="bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
                            Intelligence
                        </span>
                    </h1>
                    <p className="max-w-md text-lg leading-relaxed text-blue-200/80">
                        Track your net worth, analyze investments, manage taxes, and get
                        AI-powered financial insights — all in one place.
                    </p>

                    {/* Feature Pills */}
                    <div className="flex flex-wrap gap-2 pt-4">
                        {[
                            'Portfolio Tracking',
                            'Tax Optimization',
                            'AI Insights',
                            'Risk Analysis',
                        ].map((feat) => (
                            <span
                                key={feat}
                                className="rounded-full border border-blue-400/30 bg-blue-500/10 px-4 py-1.5 text-sm text-blue-200 backdrop-blur-sm"
                            >
                                {feat}
                            </span>
                        ))}
                    </div>
                </div>

                <p className="text-sm text-blue-300/50">
                    © 2026 QUANT. All rights reserved.
                </p>
            </motion.div>

            {/* Right – Login Form */}
            <motion.div
                initial={{ x: 40, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ duration: 0.6, ease: 'easeOut', delay: 0.15 }}
                className="flex w-full flex-col items-center justify-center px-6 py-12 lg:w-1/2"
            >
                <div className="w-full max-w-md">
                    {/* Mobile Logo */}
                    <div className="mb-8 flex items-center gap-2 lg:hidden">
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600">
                            <span className="text-lg font-bold text-white">Q</span>
                        </div>
                        <span className="text-xl font-bold text-gray-900">QUANT</span>
                    </div>

                    <div className="mb-8">
                        <h2 className="text-2xl font-bold text-gray-900">Welcome back</h2>
                        <p className="mt-2 text-gray-500">
                            Sign in to access your financial dashboard
                        </p>
                    </div>

                    {error && (
                        <div className={`mb-4 rounded-lg border p-4 ${error.includes('No account found')
                                ? 'border-amber-200 bg-amber-50'
                                : 'border-red-200 bg-red-50'
                            }`}>
                            <div className="flex items-start gap-3">
                                <div className={`mt-0.5 rounded-full p-1 ${error.includes('No account found')
                                        ? 'bg-amber-100 text-amber-600'
                                        : 'bg-red-100 text-red-600'
                                    }`}>
                                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                                    </svg>
                                </div>
                                <div className="flex-1">
                                    <p className={`text-sm font-medium ${error.includes('No account found')
                                            ? 'text-amber-800'
                                            : 'text-red-700'
                                        }`}>
                                        {error}
                                    </p>
                                    {error.includes('No account found') && (
                                        <Link
                                            href="/register"
                                            className="mt-2 inline-flex items-center gap-1 text-sm font-semibold text-amber-700 underline decoration-amber-300 underline-offset-2 hover:text-amber-900"
                                        >
                                            Create an account →
                                        </Link>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                    {message && (
                        <div className="mb-4 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700">
                            {message}
                        </div>
                    )}

                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                        {/* Email */}
                        <div className="space-y-2">
                            <Label htmlFor="email" className="text-sm font-medium text-gray-700">
                                Email Address
                            </Label>
                            <div className="relative">
                                <Mail className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="you@example.com"
                                    className="h-12 pl-11 text-sm"
                                    {...register('email')}
                                />
                            </div>
                            {errors.email && (
                                <p className="text-xs text-red-500">{errors.email.message}</p>
                            )}
                        </div>

                        {/* Password */}
                        <div className="space-y-2">
                            <Label htmlFor="password" className="text-sm font-medium text-gray-700">
                                Password
                            </Label>
                            <div className="relative">
                                <Lock className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                                <Input
                                    id="password"
                                    type={showPassword ? 'text' : 'password'}
                                    placeholder="Enter your password"
                                    className="h-12 pl-11 pr-11 text-sm"
                                    {...register('password')}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                                    tabIndex={-1}
                                >
                                    {showPassword ? (
                                        <EyeOff className="h-4 w-4" />
                                    ) : (
                                        <Eye className="h-4 w-4" />
                                    )}
                                </button>
                            </div>
                            {errors.password && (
                                <p className="text-xs text-red-500">
                                    {errors.password.message}
                                </p>
                            )}
                        </div>

                        {/* Forgot Password */}
                        <div className="flex items-center justify-end">
                            <Link
                                href="#"
                                className="text-sm font-medium text-blue-600 hover:text-blue-700"
                            >
                                Forgot password?
                            </Link>
                        </div>

                        {/* Submit */}
                        <Button
                            type="submit"
                            disabled={isSubmitting}
                            className="h-12 w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-base font-semibold text-white shadow-lg shadow-blue-200 transition-all hover:shadow-xl hover:shadow-blue-300 disabled:opacity-60"
                        >
                            {isSubmitting ? (
                                <span className="flex items-center gap-2">
                                    <svg
                                        className="h-5 w-5 animate-spin"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                    >
                                        <circle
                                            className="opacity-25"
                                            cx="12"
                                            cy="12"
                                            r="10"
                                            stroke="currentColor"
                                            strokeWidth="4"
                                        />
                                        <path
                                            className="opacity-75"
                                            fill="currentColor"
                                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                                        />
                                    </svg>
                                    Signing in...
                                </span>
                            ) : (
                                <span className="flex items-center gap-2">
                                    Sign In
                                    <ArrowRight className="h-4 w-4" />
                                </span>
                            )}
                        </Button>
                    </form>

                    {/* Google Divider */}
                    <div className="my-6 flex items-center gap-4">
                        <div className="h-px flex-1 bg-gray-200" />
                        <span className="text-xs font-medium text-gray-400">
                            OR CONTINUE WITH
                        </span>
                        <div className="h-px flex-1 bg-gray-200" />
                    </div>

                    {/* Google Sign-In Button */}
                    <div id="googleSignInDiv" className="w-full flex justify-center mb-4"></div>

                    {/* Divider */}
                    <div className="my-6 flex items-center gap-4">
                        <div className="h-px flex-1 bg-gray-200" />
                        <span className="text-xs font-medium text-gray-400">
                            DON&apos;T HAVE AN ACCOUNT?
                        </span>
                        <div className="h-px flex-1 bg-gray-200" />
                    </div>

                    <Link href="/register">
                        <Button
                            variant="outline"
                            className="h-12 w-full text-base font-medium"
                        >
                            Create Account
                        </Button>
                    </Link>
                </div>
            </motion.div>
        </div>
    );
}
