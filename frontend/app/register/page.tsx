'use client';

import React, { useState } from 'react';
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

const registerSchema = z
    .object({
        fullName: z.string().min(2, 'Full name is required'),
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
    const { login } = useUser();
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirm, setShowConfirm] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<RegisterFormData>({
        resolver: zodResolver(registerSchema),
    });

    const onSubmit = async (data: RegisterFormData) => {
        setIsSubmitting(true);
        try {
            // TODO: Replace with actual API call
            // const res = await authApi.register(data);
            // login(res.data.data.user, res.data.data.token);

            await new Promise((resolve) => setTimeout(resolve, 1200));
            login(
                {
                    id: '1',
                    fullName: data.fullName,
                    email: data.email,
                    profileCompletion: 20,
                    createdAt: new Date().toISOString(),
                },
                'mock_jwt_token_456'
            );
            router.push('/input-data');
        } catch {
            // Error handling will be added when backend is ready
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
                        Start Your
                        <br />
                        <span className="bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
                            Financial Journey
                        </span>
                    </h1>
                    <p className="max-w-md text-lg leading-relaxed text-blue-200/80">
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
                                className="rounded-xl border border-blue-400/20 bg-blue-500/10 p-4 text-center backdrop-blur-sm"
                            >
                                <div className="text-2xl font-bold text-white">
                                    {stat.value}
                                </div>
                                <div className="mt-1 text-xs text-blue-300/70">
                                    {stat.label}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <p className="text-sm text-blue-300/50">
                    © 2026 QUANT. All rights reserved.
                </p>
            </motion.div>

            {/* Right – Register Form */}
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
                        <h2 className="text-2xl font-bold text-gray-900">
                            Create your account
                        </h2>
                        <p className="mt-2 text-gray-500">
                            Get started with your smart financial journey
                        </p>
                    </div>

                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                        {/* Full Name */}
                        <div className="space-y-2">
                            <Label htmlFor="fullName" className="text-sm font-medium text-gray-700">
                                Full Name
                            </Label>
                            <div className="relative">
                                <User className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                                <Input
                                    id="fullName"
                                    type="text"
                                    placeholder="Rahul Kapoor"
                                    className="h-12 pl-11 text-sm"
                                    {...register('fullName')}
                                />
                            </div>
                            {errors.fullName && (
                                <p className="text-xs text-red-500">
                                    {errors.fullName.message}
                                </p>
                            )}
                        </div>

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
                                    placeholder="Create a strong password"
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

                        {/* Confirm Password */}
                        <div className="space-y-2">
                            <Label htmlFor="confirmPassword" className="text-sm font-medium text-gray-700">
                                Confirm Password
                            </Label>
                            <div className="relative">
                                <Lock className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
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
                                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
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
                        <label className="flex items-start gap-2 pt-1 text-sm text-gray-600">
                            <input
                                type="checkbox"
                                className="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600"
                            />
                            <span>
                                I agree to the{' '}
                                <Link
                                    href="#"
                                    className="font-medium text-blue-600 hover:text-blue-700"
                                >
                                    Terms of Service
                                </Link>{' '}
                                and{' '}
                                <Link
                                    href="#"
                                    className="font-medium text-blue-600 hover:text-blue-700"
                                >
                                    Privacy Policy
                                </Link>
                            </span>
                        </label>

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

                    {/* Divider */}
                    <div className="my-6 flex items-center gap-4">
                        <div className="h-px flex-1 bg-gray-200" />
                        <span className="text-xs font-medium text-gray-400">
                            ALREADY HAVE AN ACCOUNT?
                        </span>
                        <div className="h-px flex-1 bg-gray-200" />
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
