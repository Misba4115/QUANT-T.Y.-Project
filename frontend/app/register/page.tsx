'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, Mail, Lock, User, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useUser } from '@/contexts/user-context';
import { authApi, userApi } from '@/lib/api';
import axios from 'axios';

const registerSchema = z
    .object({
        name: z.string().min(2, 'Full name is required'),
        email: z.string().email('Please enter a valid email address'),
        password: z
            .string()
            .min(8, 'Password must be at least 8 characters')
            .regex(/[A-Z]/, 'Must contain at least one uppercase letter')
            .regex(/[0-9]/, 'Must contain at least one number'),
        confirmPassword: z.string(),
    })
    .refine((data) => data.password === data.confirmPassword, {
        message: "Passwords don't match",
        path: ['confirmPassword'],
    });

type RegisterFormData = z.infer<typeof registerSchema>;

export default function RegisterPage() {
    const router = useRouter();
    const { login, setNewUser } = useUser();
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirm, setShowConfirm] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [message, setMessage] = useState<string | null>(null);

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<RegisterFormData>({
        resolver: zodResolver(registerSchema),
    });

    // ── Google Sign-Up ──────────────────────────────────────
    const handleGoogleResponse = useCallback(async (response: GoogleCredentialResponse) => {
        setIsSubmitting(true);
        setError(null);
        try {
            const res = await authApi.googleAuth(response.credential);
            const profileRes = await userApi.getProfile();
            const user = profileRes.data;
            login(user);
            if (res.data.is_new_user) setNewUser(true);
            setMessage('Account ready! Redirecting...');
            setTimeout(() => {
                router.push(res.data.is_new_user ? '/input-data' : '/dashboard');
            }, 500);
        } catch (err: unknown) {
            const msg = axios.isAxiosError(err) ? err.response?.data?.detail || err.message : 'Google sign-up failed';
            setError(msg);
        } finally {
            setIsSubmitting(false);
        }
    }, [login, setNewUser, router]);

    useEffect(() => {
        const script = document.createElement('script');
        script.src = 'https://accounts.google.com/gsi/client';
        script.async = true;
        script.defer = true;
        script.onload = () => {
            const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
            if (clientId && clientId !== 'YOUR_GOOGLE_CLIENT_ID_HERE' && window.google) {
                window.google.accounts.id.initialize({
                    client_id: clientId,
                    callback: handleGoogleResponse,
                });
            }
        };
        document.head.appendChild(script);
        return () => { document.head.removeChild(script); };
    }, [handleGoogleResponse]);

    const onSubmit = async (data: RegisterFormData) => {
        setIsSubmitting(true);
        setError(null);
        setMessage(null);
        try {
            await authApi.register({
                name: data.name,
                email: data.email,
                password: data.password,
            });

            // The backend has set an HttpOnly session cookie.
            const profileRes = await userApi.getProfile();
            const user = profileRes.data;
            login(user);
            setNewUser(true);
            setMessage('Registration successful! Redirecting...');
            setTimeout(() => {
                router.push('/input-data');
            }, 500);
        } catch (err: unknown) {
            const msg = axios.isAxiosError(err) ? err.response?.data?.detail || err.message : 'Registration failed';
            setError(msg);
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
                className="hidden w-1/2 flex-col justify-between bg-gradient-to-br from-stone-900 via-emerald-950 to-stone-950 p-12 lg:flex"
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
                        Start Your
                        <br />
                        <span className="bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">
                            Financial Journey
                        </span>
                    </h1>
                    <p className="max-w-md text-lg leading-relaxed text-emerald-200/80">
                        Join thousands of smart investors who trust QUANT to manage,
                        analyze, and optimize their finances.
                    </p>

                    {/* Stats */}
                    <div className="grid grid-cols-3 gap-4 pt-4">
                        {[
                            { label: 'Active Users', value: '10K+' },
                            { label: 'AUM Tracked', value: '₹50Cr+' },
                            { label: 'Insights/Day', value: '1K+' },
                        ].map((stat) => (
                            <div
                                key={stat.label}
                                className="rounded-xl border border-emerald-400/20 bg-emerald-500/10 p-4 text-center backdrop-blur-sm"
                            >
                                <div className="text-2xl font-bold text-white">
                                    {stat.value}
                                </div>
                                <div className="mt-1 text-xs text-emerald-300/70">
                                    {stat.label}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <p className="text-sm text-emerald-300/50">
                    © 2026 QUANT. All rights reserved.
                </p>
            </motion.div>

            {/* Right – Register Form */}
            <motion.div
                initial={{ x: 40, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ duration: 0.6, ease: 'easeOut', delay: 0.15 }}
                className="flex w-full flex-col items-center justify-center bg-[#F9F9F6] px-6 py-12 lg:w-1/2"
            >
                <div className="w-full max-w-md">
                    {/* Mobile Logo */}
                    <div className="mb-8 flex items-center gap-2 lg:hidden">
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-800 to-emerald-950">
                            <span className="text-lg font-bold text-white">Q</span>
                        </div>
                        <span className="text-xl font-bold text-stone-900">QUANT</span>
                    </div>

                    <div className="mb-8">
                        <h2 className="text-2xl font-bold text-stone-900">
                            Create your account
                        </h2>
                        <p className="mt-2 text-stone-500">
                            Get started with your smart financial journey
                        </p>
                    </div>

                    {error && (
                        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                            {error}
                        </div>
                    )}
                    {message && (
                        <div className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
                            {message}
                        </div>
                    )}

                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                        {/* Full Name */}
                        <div className="space-y-2">
                            <Label htmlFor="name" className="text-sm font-medium text-stone-700">
                                Full Name
                            </Label>
                            <div className="relative">
                                <User className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
                                <Input
                                    id="name"
                                    type="text"
                                    placeholder="Rahul Kapoor"
                                    className="h-12 pl-11 text-sm"
                                    {...register('name')}
                                />
                            </div>
                            {errors.name && (
                                <p className="text-xs text-red-500">
                                    {errors.name.message}
                                </p>
                            )}
                        </div>

                        {/* Email */}
                        <div className="space-y-2">
                            <Label htmlFor="email" className="text-sm font-medium text-stone-700">
                                Email Address
                            </Label>
                            <div className="relative">
                                <Mail className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
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
                            <Label htmlFor="password" className="text-sm font-medium text-stone-700">
                                Password
                            </Label>
                            <div className="relative">
                                <Lock className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
                                <Input
                                    id="password"
                                    type={showPassword ? 'text' : 'password'}
                                    placeholder="Create a strong password"
                                    className="h-12 pl-11 pr-11 text-sm"
                                    {...register('password')}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-600"
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

                        {/* Confirm Password */}
                        <div className="space-y-2">
                            <Label htmlFor="confirmPassword" className="text-sm font-medium text-stone-700">
                                Confirm Password
                            </Label>
                            <div className="relative">
                                <Lock className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
                                <Input
                                    id="confirmPassword"
                                    type={showConfirm ? 'text' : 'password'}
                                    placeholder="Re-enter your password"
                                    className="h-12 pl-11 pr-11 text-sm"
                                    {...register('confirmPassword')}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowConfirm(!showConfirm)}
                                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-600"
                                    tabIndex={-1}
                                >
                                    {showConfirm ? (
                                        <EyeOff className="h-4 w-4" />
                                    ) : (
                                        <Eye className="h-4 w-4" />
                                    )}
                                </button>
                            </div>
                            {errors.confirmPassword && (
                                <p className="text-xs text-red-500">
                                    {errors.confirmPassword.message}
                                </p>
                            )}
                        </div>

                        {/* Terms */}
                        <label className="flex items-start gap-2 pt-1 text-sm text-stone-600">
                            <input
                                type="checkbox"
                                className="mt-1 h-4 w-4 rounded border-stone-300 text-emerald-700"
                            />
                            <span>
                                I agree to the{' '}
                                <Link
                                    href="#"
                                    className="font-medium text-emerald-700 hover:text-emerald-800"
                                >
                                    Terms of Service
                                </Link>{' '}
                                and{' '}
                                <Link
                                    href="#"
                                    className="font-medium text-emerald-700 hover:text-emerald-800"
                                >
                                    Privacy Policy
                                </Link>
                            </span>
                        </label>

                        {/* Submit */}
                        <Button
                            type="submit"
                            disabled={isSubmitting}
                            className="h-12 w-full bg-gradient-to-r from-emerald-800 to-emerald-950 text-base font-semibold text-white shadow-lg shadow-emerald-200 transition-all hover:shadow-xl hover:shadow-emerald-300 disabled:opacity-60"
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
                                    Creating account...
                                </span>
                            ) : (
                                <span className="flex items-center gap-2">
                                    Create Account
                                    <ArrowRight className="h-4 w-4" />
                                </span>
                            )}
                        </Button>
                    </form>

                    {/* Google Divider */}
                    <div className="my-6 flex items-center gap-4">
                        <div className="h-px flex-1 bg-stone-200" />
                        <span className="text-xs font-medium text-stone-400">
                            OR CONTINUE WITH
                        </span>
                        <div className="h-px flex-1 bg-stone-200" />
                    </div>

                    {/* Google Sign-Up Button */}
                    <Button
                        type="button"
                        variant="outline"
                        disabled={isSubmitting}
                        onClick={() => {
                            if (window.google?.accounts?.id) {
                                window.google.accounts.id.prompt();
                            } else {
                                setError('Google Sign-In is not configured. Please set up your Google Client ID.');
                            }
                        }}
                        className="h-12 w-full gap-3 text-sm font-medium border-stone-200 hover:bg-stone-50"
                    >
                        <svg className="h-5 w-5" viewBox="0 0 24 24">
                            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
                            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                        </svg>
                        Sign up with Google
                    </Button>

                    {/* Divider */}
                    <div className="my-6 flex items-center gap-4">
                        <div className="h-px flex-1 bg-stone-200" />
                        <span className="text-xs font-medium text-stone-400">
                            ALREADY HAVE AN ACCOUNT?
                        </span>
                        <div className="h-px flex-1 bg-stone-200" />
                    </div>

                    <Link href="/login">
                        <Button
                            variant="outline"
                            className="h-12 w-full text-base font-medium"
                        >
                            Sign In
                        </Button>
                    </Link>
                </div>
            </motion.div>
        </div>
    );
}
