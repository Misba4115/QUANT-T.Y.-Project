'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
    Building2,
    TrendingUp,
    CandlestickChart,
    Bitcoin,
    Target,
    Plus,
    HelpCircle,
    MessageCircle,
    Clock,
    CheckCircle2,
    IndianRupee,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import Navbar from '@/components/layout/navbar';
import PageTransition from '@/components/layout/page-transition';
import { SkeletonCard } from '@/components/ui/skeletons';
import { useUser } from '@/contexts/user-context';
import type { QuickStats, FinancialCategory, BankAccount } from '@/types';
import { bankingApi } from '@/lib/api';

// ==========================================
// Financial Categories (UI constants)
// ==========================================
const financialCategories: FinancialCategory[] = [
    {
        id: 'banking',
        title: 'Banking & Accounts',
        description: 'Link your bank accounts and track balances',
        icon: 'building',
        isActive: true,
    },
    {
        id: 'investments',
        title: 'Investments',
        description: 'Stocks, Mutual Funds, ETFs',
        icon: 'trending-up',
        isActive: false,
    },
    {
        id: 'trading',
        title: 'Trading',
        description: 'Active trades and positions',
        icon: 'candlestick-chart',
        isActive: false,
    },
    {
        id: 'crypto',
        title: 'Crypto',
        description: 'Cryptocurrency holdings',
        icon: 'bitcoin',
        isActive: false,
    },
    {
        id: 'goals',
        title: 'Goals & Planning',
        description: 'Financial goals and milestones',
        icon: 'target',
        isActive: false,
    },
];

// ==========================================
// Form Schema
// ==========================================
const bankAccountSchema = z.object({
    accountType: z.string().min(1, 'Account type is required'),
    bankName: z.string().min(1, 'Bank name is required'),
    accountNickname: z.string().min(1, 'Account nickname is required'),
    currentBalance: z.string().min(1, 'Current balance is required'),
    isPrimary: z.boolean(),
});

type BankAccountForm = z.infer<typeof bankAccountSchema>;

// ==========================================
// Sub-components
// ==========================================
const categoryIcons: Record<string, React.ReactNode> = {
    building: <Building2 className="h-8 w-8" />,
    'trending-up': <TrendingUp className="h-8 w-8" />,
    'candlestick-chart': <CandlestickChart className="h-8 w-8" />,
    bitcoin: <Bitcoin className="h-8 w-8" />,
    target: <Target className="h-8 w-8" />,
};

const iconColors: Record<string, string> = {
    building: 'text-blue-600 bg-blue-50 border-blue-200',
    'trending-up': 'text-emerald-600 bg-emerald-50 border-emerald-200',
    'candlestick-chart': 'text-red-600 bg-red-50 border-red-200',
    bitcoin: 'text-orange-600 bg-orange-50 border-orange-200',
    target: 'text-indigo-600 bg-indigo-50 border-indigo-200',
};

// ==========================================
// Main Page
// ==========================================
export default function InputDataPage() {
    const { user } = useUser();
    const [isLoading, setIsLoading] = useState(true);
    const [activeCategory, setActiveCategory] = useState('banking');
    const [quickStats, setQuickStats] = useState<QuickStats>({
        dataCompleteness: 0,
        accountsAdded: 0,
        holdings: 0,
        lastUpdated: '--',
    });

    const {
        register,
        handleSubmit,
        setValue,
        watch,
        formState: { errors },
    } = useForm<BankAccountForm>({
        resolver: zodResolver(bankAccountSchema),
        defaultValues: {
            isPrimary: true,
            accountType: '',
        },
    });

    const isPrimary = watch('isPrimary');

    // helper for pulling bank accounts; reused by effect and submit handler
    const fetchQuickStats = async () => {
        try {
            const res = await bankingApi.getBankAccounts();
            const accounts = res.data.data;
            setQuickStats({
                dataCompleteness: 0, // placeholder until profile completion is implemented
                accountsAdded: accounts?.length ?? 0,
                holdings: accounts?.length ?? 0,
                lastUpdated: 'Just now',
            });
        } catch (error) {
            console.error('Error fetching bank accounts:', error);
            // API not available yet — leave defaults
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchQuickStats();
    }, []); // dependency removed until profileCompletion exists

    const onSubmit = async (data: BankAccountForm) => {
        try {
            await bankingApi.addBankAccount({
                account_type: data.accountType as BankAccount['account_type'],
                institution: data.bankName,
                account_name: data.accountNickname,
                current_balance: parseFloat(data.currentBalance),
                is_primary: data.isPrimary,
            });
            alert('Account saved successfully!');
            // refresh stats/list
            fetchQuickStats();
        } catch (error) {
            console.error('Error saving account:', error);
            alert('Could not save — backend may not be connected yet.');
        }
    };

    const displayName = user?.name || 'User';
    const firstName = displayName.split(' ')[0];

    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: { staggerChildren: 0.08 },
        },
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
    };

    if (isLoading) {
        return (
            <>
                <Navbar />
                <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                    <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
                        <div className="space-y-6">
                            <SkeletonCard />
                            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-5">
                                {Array.from({ length: 5 }).map((_, i) => (
                                    <SkeletonCard key={i} />
                                ))}
                            </div>
                            <SkeletonCard className="h-64" />
                        </div>
                        <div className="space-y-4">
                            <SkeletonCard />
                            <SkeletonCard />
                        </div>
                    </div>
                </div>
            </>
        );
    }

    return (
        <>
            <Navbar />
            <PageTransition>
                <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                    <motion.div
                        variants={containerVariants}
                        initial="hidden"
                        animate="visible"
                        className="grid gap-8 lg:grid-cols-[1fr_320px]"
                    >
                        {/* ===== Left Column ===== */}
                        <div className="space-y-8">
                            {/* Welcome Section */}
                            <motion.div variants={itemVariants}>
                                <h1 className="text-2xl font-bold text-gray-900">
                                    Welcome back, {firstName}!{' '}
                                    <span className="font-normal text-gray-500">
                                        Let&apos;s keep your financial data up to date.
                                    </span>
                                </h1>
                                <div className="mt-3 flex items-center gap-3">
                                    <div className="flex items-center gap-2">
                                        <CheckCircle2 className="h-4 w-4 text-blue-600" />
                                        <span className="text-sm font-medium text-gray-600">
                                            Profile: 0% complete
                                        </span>
                                    </div>
                                    <div className="h-2 w-32 overflow-hidden rounded-full bg-gray-100">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{
                                                width: `0%`,
                                            }}
                                            transition={{ duration: 1, delay: 0.5 }}
                                            className="h-full rounded-full bg-gradient-to-r from-blue-500 to-blue-600"
                                        />
                                    </div>
                                </div>
                            </motion.div>

                            {/* Financial Category Cards */}
                            <motion.div
                                variants={itemVariants}
                                className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-5"
                            >
                                {financialCategories.map((cat) => {
                                    const isActive = activeCategory === cat.id;
                                    return (
                                        <motion.button
                                            key={cat.id}
                                            whileHover={{ y: -4 }}
                                            whileTap={{ scale: 0.97 }}
                                            onClick={() => setActiveCategory(cat.id)}
                                            className={`group flex flex-col items-center rounded-xl border-2 p-4 text-center transition-all ${isActive
                                                ? `${iconColors[cat.icon]} shadow-md`
                                                : 'border-gray-100 bg-white hover:border-gray-200 hover:shadow-sm'
                                                }`}
                                        >
                                            <div
                                                className={`mb-3 rounded-lg p-2 ${isActive
                                                    ? iconColors[cat.icon]
                                                    : 'bg-gray-50 text-gray-400 group-hover:bg-gray-100 group-hover:text-gray-600'
                                                    }`}
                                            >
                                                {categoryIcons[cat.icon]}
                                            </div>
                                            <h3
                                                className={`text-sm font-semibold ${isActive ? 'text-gray-900' : 'text-gray-700'
                                                    }`}
                                            >
                                                {cat.title}
                                            </h3>
                                            <p className="mt-1 text-xs text-gray-400 leading-tight">
                                                {cat.description}
                                            </p>
                                            <span
                                                className={`mt-3 inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${isActive
                                                    ? 'bg-blue-600 text-white'
                                                    : 'border border-gray-200 text-gray-600 group-hover:border-blue-200 group-hover:text-blue-600'
                                                    }`}
                                            >
                                                <Plus className="h-3 w-3" />
                                                Add/Update
                                            </span>
                                        </motion.button>
                                    );
                                })}
                            </motion.div>

                            {/* Banking & Accounts Form */}
                            <motion.div
                                variants={itemVariants}
                                className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm"
                            >
                                <h2 className="mb-6 text-lg font-bold text-gray-900">
                                    Banking & Accounts Details
                                </h2>
                                <form
                                    onSubmit={handleSubmit(onSubmit)}
                                    className="space-y-5"
                                >
                                    {/* Account Type */}
                                    <div className="grid gap-4 sm:grid-cols-2">
                                        <div className="space-y-2">
                                            <Label className="text-sm font-medium text-gray-700">
                                                Account Type:
                                            </Label>
                                            <Select
                                                onValueChange={(val) => setValue('accountType', val)}
                                            >
                                                <SelectTrigger className="h-11">
                                                    <SelectValue placeholder="Select type" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="savings">Savings</SelectItem>
                                                    <SelectItem value="current">Current</SelectItem>
                                                    <SelectItem value="salary">Salary</SelectItem>
                                                    <SelectItem value="fd">Fixed Deposit</SelectItem>
                                                    <SelectItem value="rd">
                                                        Recurring Deposit
                                                    </SelectItem>
                                                </SelectContent>
                                            </Select>
                                            {errors.accountType && (
                                                <p className="text-xs text-red-500">
                                                    {errors.accountType.message}
                                                </p>
                                            )}
                                        </div>

                                        {/* Bank Name */}
                                        <div className="space-y-2">
                                            <Label className="text-sm font-medium text-gray-700">
                                                Bank Name:
                                            </Label>
                                            <Input
                                                placeholder="HDFC, ICICI, SBI, etc..."
                                                className="h-11"
                                                {...register('bankName')}
                                            />
                                            {errors.bankName && (
                                                <p className="text-xs text-red-500">
                                                    {errors.bankName.message}
                                                </p>
                                            )}
                                        </div>
                                    </div>

                                    <div className="grid gap-4 sm:grid-cols-2">
                                        {/* Account Nickname */}
                                        <div className="space-y-2">
                                            <Label className="text-sm font-medium text-gray-700">
                                                Account Nickname:
                                            </Label>
                                            <Input
                                                placeholder="e.g. HDFC Main Savings"
                                                className="h-11"
                                                {...register('accountNickname')}
                                            />
                                            {errors.accountNickname && (
                                                <p className="text-xs text-red-500">
                                                    {errors.accountNickname.message}
                                                </p>
                                            )}
                                        </div>

                                        {/* Current Balance */}
                                        <div className="space-y-2">
                                            <Label className="text-sm font-medium text-gray-700">
                                                Current Balance:
                                            </Label>
                                            <div className="relative">
                                                <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400">
                                                    <IndianRupee className="h-4 w-4" />
                                                </div>
                                                <Input
                                                    type="number"
                                                    placeholder="0"
                                                    className="h-11 pl-10"
                                                    {...register('currentBalance')}
                                                />
                                            </div>
                                            {errors.currentBalance && (
                                                <p className="text-xs text-red-500">
                                                    {errors.currentBalance.message}
                                                </p>
                                            )}
                                        </div>
                                    </div>

                                    {/* Primary Toggle */}
                                    <div className="flex items-center gap-3">
                                        <Switch
                                            checked={isPrimary}
                                            onCheckedChange={(val) => setValue('isPrimary', val)}
                                        />
                                        <Label className="text-sm text-gray-600">
                                            Set as primary account
                                        </Label>
                                    </div>

                                    {/* Buttons */}
                                    <div className="flex items-center gap-3 pt-2">
                                        <Button
                                            type="submit"
                                            className="bg-gradient-to-r from-blue-600 to-indigo-600 px-8 text-white shadow-md shadow-blue-200 hover:shadow-lg hover:shadow-blue-300"
                                        >
                                            Save & Continue
                                        </Button>
                                        <Button type="button" variant="outline" className="px-8">
                                            Skip for now
                                        </Button>
                                    </div>
                                </form>
                            </motion.div>
                        </div>

                        {/* ===== Right Column ===== */}
                        <div className="space-y-6">
                            {/* Quick Stats */}
                            <motion.div
                                variants={itemVariants}
                                className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm"
                            >
                                <h3 className="mb-4 text-base font-bold text-gray-900">
                                    Quick Stats
                                </h3>
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-gray-500">
                                            Data Completeness:
                                        </span>
                                        <span className="text-sm font-bold text-blue-600">
                                            {quickStats.dataCompleteness}%
                                        </span>
                                    </div>
                                    <Progress
                                        value={quickStats.dataCompleteness}
                                        className="h-2"
                                    />

                                    <div className="flex items-center justify-between pt-2">
                                        <span className="text-sm text-gray-500">
                                            Accounts Added:
                                        </span>
                                        <span className="text-sm font-bold text-gray-900">
                                            {quickStats.accountsAdded}
                                        </span>
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-gray-500">Holdings:</span>
                                        <span className="text-sm font-bold text-gray-900">
                                            {quickStats.holdings}
                                        </span>
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-gray-500">
                                            Last Updated:
                                        </span>
                                        <span className="flex items-center gap-1 text-sm text-gray-400">
                                            <Clock className="h-3.5 w-3.5" />
                                            {quickStats.lastUpdated}
                                        </span>
                                    </div>
                                </div>
                            </motion.div>

                            {/* Help Card */}
                            <motion.div
                                variants={itemVariants}
                                className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm"
                            >
                                <div className="flex items-center gap-2 mb-3">
                                    <HelpCircle className="h-5 w-5 text-gray-400" />
                                    <h3 className="text-base font-bold text-gray-900">
                                        Need Help?
                                    </h3>
                                </div>
                                <button className="flex items-center gap-2 text-sm font-medium text-blue-600 transition-colors hover:text-blue-700">
                                    <MessageCircle className="h-4 w-4" />
                                    Chat with our bot
                                </button>
                            </motion.div>
                        </div>
                    </motion.div>
                </main>
            </PageTransition>
        </>
    );
}
