'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
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
    Star,
    Trash2,
    IndianRupee,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import Navbar from '@/components/layout/navbar';
import PageTransition from '@/components/layout/page-transition';
import { SkeletonCard } from '@/components/ui/skeletons';
import { useUser } from '@/contexts/user-context';
import BankingModal, { type LocalBankAccount } from '@/components/input-data/banking-modal';
import InvestmentsPanel, { type CSVFile } from '@/components/input-data/investments-panel';
import TradingPanel, { type TradingAccount } from '@/components/input-data/trading-panel';
import GoalsPanel, { type GoalsData } from '@/components/input-data/goals-panel';
import CryptoPanel from '@/components/input-data/crypto-panel';
import { bankingApi, goalsApi } from '@/lib/api';
import type { GoalOut } from '@/types';

// ==========================================
// Financial Categories (UI constants)
// ==========================================
interface FinancialCategory {
    id: string;
    title: string;
    description: string;
    icon: string;
}

const financialCategories: FinancialCategory[] = [
    {
        id: 'banking',
        title: 'Banking & Accounts',
        description: 'Link your bank accounts and track balances',
        icon: 'building',
    },
    {
        id: 'investments',
        title: 'Investments',
        description: 'Stocks, Mutual Funds, ETFs',
        icon: 'trending-up',
    },
    {
        id: 'trading',
        title: 'Trading',
        description: 'Active trades and positions',
        icon: 'candlestick-chart',
    },
    {
        id: 'crypto',
        title: 'Crypto',
        description: 'Cryptocurrency holdings',
        icon: 'bitcoin',
    },
    {
        id: 'goals',
        title: 'Goals & Planning',
        description: 'Financial goals and milestones',
        icon: 'target',
    },
];

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

const accountTypeLabels: Record<string, string> = {
    savings: 'Savings',
    current: 'Current',
    salary: 'Salary',
    fd: 'Fixed Deposit',
    rd: 'Recurring Deposit',
};

// ==========================================
// Main Page
// ==========================================
export default function InputDataPage() {
    const router = useRouter();
    const { user, isAuthenticated, isLoading: authLoading, isNewUser, completeOnboarding } = useUser();
    const [pageLoading, setPageLoading] = useState(true);
    const [activeCategory, setActiveCategory] = useState('banking');

    // ---- Modal states ----
    const [bankingModalOpen, setBankingModalOpen] = useState(false);
    const [investmentsModalOpen, setInvestmentsModalOpen] = useState(false);
    const [tradingModalOpen, setTradingModalOpen] = useState(false);
    const [cryptoModalOpen, setCryptoModalOpen] = useState(false);
    const [goalsModalOpen, setGoalsModalOpen] = useState(false);

    // ---- Local data stores ----
    const [bankAccounts, setBankAccounts] = useState<LocalBankAccount[]>([]);
    const [csvFiles, setCsvFiles] = useState<CSVFile[]>([]);
    const [tradingAccounts, setTradingAccounts] = useState<TradingAccount[]>([]);
    const [goalsData, setGoalsData] = useState<GoalsData | null>(null);
    const [apiGoals, setApiGoals] = useState<GoalOut[]>([]);

    // ==========================================
    // Route Guard
    // ==========================================
    useEffect(() => {
        if (authLoading) return;

        // Not authenticated → redirect to login
        if (!isAuthenticated) {
            router.replace('/login');
            return;
        }

        setPageLoading(false);
    }, [authLoading, isAuthenticated, router]);

    // ---- Fetch from Supabase API on mount (source of truth) ----
    const fetchBankAccountsFromAPI = useCallback(async () => {
        try {
            const res = await bankingApi.getBankAccounts();
            const accounts: LocalBankAccount[] = (res.data || []).map((acc: any) => ({
                id: acc.account_id || acc.id,
                accountType: acc.account_type,
                bankName: acc.institution,
                accountNickname: acc.account_name,
                currentBalance: acc.current_balance || 0,
                isPrimary: acc.is_primary || false,
            }));
            setBankAccounts(accounts);
            localStorage.setItem('quant_bank_accounts', JSON.stringify(accounts));
        } catch (err) {
            console.warn('Could not fetch bank accounts from API, falling back to localStorage', err);
            try {
                const stored = localStorage.getItem('quant_bank_accounts');
                if (stored) setBankAccounts(JSON.parse(stored));
            } catch { /* ignore */ }
        }
    }, []);

    const fetchGoalsFromAPI = useCallback(async () => {
        try {
            const res = await goalsApi.getGoals();
            const goals = res.data || [];
            setApiGoals(goals);

            let local: GoalsData | null = null;
            try {
                const storedGoals = localStorage.getItem('quant_goals_data');
                if (storedGoals) local = JSON.parse(storedGoals);
            } catch { /* ignore */ }

            // If user has goals in Supabase, also set the goalsData for the panel
            if (goals.length > 0) {
                const firstGoal = goals[0];
                setGoalsData((prev) => ({
                    riskTolerance: prev?.riskTolerance || local?.riskTolerance || user?.risk_profile?.toLowerCase() || '',
                    investmentHorizon: prev?.investmentHorizon || local?.investmentHorizon || '',
                    monthlyCapacity: prev?.monthlyCapacity || local?.monthlyCapacity || '',
                    goalType: prev?.goalType || local?.goalType || firstGoal.goal_type || 'custom',
                    // Use API for target amount/date as source of truth if available
                    targetAmount: firstGoal.target_amount ? firstGoal.target_amount.toString() : (prev?.targetAmount || local?.targetAmount || ''),
                    targetDate: firstGoal.target_date || prev?.targetDate || local?.targetDate || '',
                }));
            } else if (local) {
                setGoalsData(local);
            }
            localStorage.setItem('quant_api_goals', JSON.stringify(goals));
        } catch (err) {
            console.warn('Could not fetch goals from API, falling back to localStorage', err);
            try {
                const storedGoals = localStorage.getItem('quant_goals_data');
                if (storedGoals) setGoalsData(JSON.parse(storedGoals));
                const storedApiGoals = localStorage.getItem('quant_api_goals');
                if (storedApiGoals) setApiGoals(JSON.parse(storedApiGoals));
            } catch { /* ignore */ }
        }
    }, [user?.risk_profile]);

    useEffect(() => {
        if (!isAuthenticated || authLoading) return;
        fetchBankAccountsFromAPI();
        fetchGoalsFromAPI();
        // Also load non-API data from localStorage
        try {
            const storedCsv = localStorage.getItem('quant_csv_files');
            if (storedCsv) setCsvFiles(JSON.parse(storedCsv));
            const storedTrading = localStorage.getItem('quant_trading_accounts');
            if (storedTrading) setTradingAccounts(JSON.parse(storedTrading));
        } catch { /* ignore */ }
    }, [isAuthenticated, authLoading, fetchBankAccountsFromAPI, fetchGoalsFromAPI]);

    // ---- Persist CSV & trading to localStorage on change (no API for these yet) ----
    useEffect(() => {
        localStorage.setItem('quant_csv_files', JSON.stringify(csvFiles));
    }, [csvFiles]);

    useEffect(() => {
        localStorage.setItem('quant_trading_accounts', JSON.stringify(tradingAccounts));
    }, [tradingAccounts]);

    useEffect(() => {
        if (goalsData) localStorage.setItem('quant_goals_data', JSON.stringify(goalsData));
    }, [goalsData]);

    // ==========================================
    // Handlers
    // ==========================================
    const handleAddAccount = async (account: LocalBankAccount) => {
        // Sync to Supabase first
        try {
            const res = await bankingApi.addBankAccount({
                account_type: account.accountType,
                account_name: account.accountNickname,
                institution: account.bankName,
                current_balance: account.currentBalance,
                is_primary: account.isPrimary,
                currency: 'INR',
            });
            // Use the API-returned ID
            const savedAccount: LocalBankAccount = {
                ...account,
                id: res.data.account_id || account.id,
            };
            let updated: LocalBankAccount[];
            if (savedAccount.isPrimary) {
                updated = bankAccounts.map((a) => ({ ...a, isPrimary: false }));
                updated.push(savedAccount);
            } else {
                updated = [...bankAccounts, savedAccount];
            }
            setBankAccounts(updated);
            localStorage.setItem('quant_bank_accounts', JSON.stringify(updated));
        } catch (err) {
            console.error('Failed to save bank account to API:', err);
            // Fallback: still add locally
            let updated: LocalBankAccount[];
            if (account.isPrimary) {
                updated = bankAccounts.map((a) => ({ ...a, isPrimary: false }));
                updated.push(account);
            } else {
                updated = [...bankAccounts, account];
            }
            setBankAccounts(updated);
        }
    };

    const handleDeleteAccount = async (id: string) => {
        // Delete from Supabase
        try {
            await bankingApi.deleteBankAccount(id);
        } catch (err) {
            console.error('Failed to delete bank account from API:', err);
        }
        const updated = bankAccounts.filter((a) => a.id !== id);
        setBankAccounts(updated);
        localStorage.setItem('quant_bank_accounts', JSON.stringify(updated));
    };

    const handleSetPrimary = async (id: string) => {
        // Update in Supabase
        try {
            await bankingApi.updateBankAccount(id, { is_primary: true });
        } catch (err) {
            console.error('Failed to update primary account in API:', err);
        }
        const updated = bankAccounts.map((a) => ({
            ...a,
            isPrimary: a.id === id,
        }));
        setBankAccounts(updated);
        localStorage.setItem('quant_bank_accounts', JSON.stringify(updated));
    };

    const handleCategoryClick = (categoryId: string) => {
        setActiveCategory(categoryId);

        // Open the corresponding modal or navigate to dedicated page
        switch (categoryId) {
            case 'banking':
                setBankingModalOpen(true);
                break;
            case 'investments':
                setInvestmentsModalOpen(true);
                break;
            case 'trading':
                setTradingModalOpen(true);
                break;
            case 'crypto':
                setCryptoModalOpen(true);
                break;
            case 'goals':
                setGoalsModalOpen(true);
                break;
        }
    };

    const handleSkipForNow = () => {
        completeOnboarding();
        router.push('/dashboard');
    };

    const handleSaveAndContinue = () => {
        completeOnboarding();
        router.push('/dashboard');
    };

    // ==========================================
    // Derived
    // ==========================================
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

    // ==========================================
    // Loading State
    // ==========================================
    if (authLoading || pageLoading) {
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

    // ==========================================
    // Render
    // ==========================================
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
                            {/* Welcome Section (no progress bar) */}
                            <motion.div variants={itemVariants}>
                                <h1 className="text-2xl font-bold text-gray-900">
                                    Welcome, {firstName}!{' '}
                                    <span className="font-normal text-gray-500">
                                        Let&apos;s set up your financial profile.
                                    </span>
                                </h1>
                                <p className="mt-2 text-sm text-gray-400">
                                    Click on a category below to add your financial data. You can always update this later.
                                </p>
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
                                            onClick={() => handleCategoryClick(cat.id)}
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

                            {/* Banking Accounts List */}
                            <AnimatePresence>
                                {bankAccounts.length > 0 && (
                                    <motion.div
                                        variants={itemVariants}
                                        initial="hidden"
                                        animate="visible"
                                        className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm"
                                    >
                                        <div className="flex items-center justify-between mb-4">
                                            <h2 className="text-lg font-bold text-gray-900">
                                                Your Bank Accounts ({bankAccounts.length})
                                            </h2>
                                            <Button
                                                size="sm"
                                                onClick={() => setBankingModalOpen(true)}
                                                className="gap-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white"
                                            >
                                                <Plus className="h-3.5 w-3.5" />
                                                Add More
                                            </Button>
                                        </div>

                                        <div className="space-y-3">
                                            {bankAccounts.map((account) => (
                                                <motion.div
                                                    key={account.id}
                                                    initial={{ opacity: 0, x: -10 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    className={`flex items-center justify-between rounded-lg border p-4 transition-all ${
                                                        account.isPrimary
                                                            ? 'border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 shadow-sm'
                                                            : 'border-gray-100 bg-white hover:border-gray-200'
                                                    }`}
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <div
                                                            className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                                                                account.isPrimary
                                                                    ? 'bg-blue-100 text-blue-600'
                                                                    : 'bg-gray-100 text-gray-500'
                                                            }`}
                                                        >
                                                            <Building2 className="h-5 w-5" />
                                                        </div>
                                                        <div>
                                                            <div className="flex items-center gap-2">
                                                                <p className="text-sm font-semibold text-gray-800">
                                                                    {account.accountNickname}
                                                                </p>
                                                                {account.isPrimary && (
                                                                    <span className="flex items-center gap-1 rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-blue-700">
                                                                        <Star className="h-2.5 w-2.5" />
                                                                        Primary
                                                                    </span>
                                                                )}
                                                            </div>
                                                            <p className="text-xs text-gray-400">
                                                                {account.bankName} • {accountTypeLabels[account.accountType] || account.accountType}
                                                            </p>
                                                        </div>
                                                    </div>

                                                    <div className="flex items-center gap-3">
                                                        <div className="text-right">
                                                            <p className="flex items-center gap-0.5 text-sm font-bold text-gray-900">
                                                                <IndianRupee className="h-3.5 w-3.5" />
                                                                {account.currentBalance.toLocaleString('en-IN')}
                                                            </p>
                                                        </div>
                                                        <div className="flex gap-1">
                                                            {!account.isPrimary && (
                                                                <Button
                                                                    size="sm"
                                                                    variant="outline"
                                                                    onClick={() => handleSetPrimary(account.id)}
                                                                    className="gap-1 text-xs"
                                                                    title="Set as primary"
                                                                >
                                                                    <Star className="h-3 w-3" />
                                                                </Button>
                                                            )}
                                                            <Button
                                                                size="sm"
                                                                variant="outline"
                                                                onClick={() => handleDeleteAccount(account.id)}
                                                                className="gap-1 text-red-500 hover:text-red-600"
                                                                title="Delete account"
                                                            >
                                                                <Trash2 className="h-3 w-3" />
                                                            </Button>
                                                        </div>
                                                    </div>
                                                </motion.div>
                                            ))}
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>

                            {/* Action Buttons */}
                            <motion.div variants={itemVariants} className="flex items-center gap-3">
                                <Button
                                    onClick={handleSaveAndContinue}
                                    className="bg-gradient-to-r from-blue-600 to-indigo-600 px-8 text-white shadow-md shadow-blue-200 hover:shadow-lg hover:shadow-blue-300"
                                >
                                    Save & Continue to Dashboard
                                </Button>
                                <Button
                                    variant="outline"
                                    className="px-8"
                                    onClick={handleSkipForNow}
                                >
                                    Skip for now
                                </Button>
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
                                            Accounts Added:
                                        </span>
                                        <span className="text-sm font-bold text-gray-900">
                                            {bankAccounts.length}
                                        </span>
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-gray-500">CSV Files:</span>
                                        <span className="text-sm font-bold text-gray-900">
                                            {csvFiles.length}
                                        </span>
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-gray-500">Trading Connected:</span>
                                        <span className="text-sm font-bold text-gray-900">
                                            {tradingAccounts.length}
                                        </span>
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-gray-500">Goals Set:</span>
                                        <span className="text-sm font-bold text-gray-900">
                                            {goalsData ? 'Yes' : 'No'}
                                        </span>
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-gray-500">
                                            Last Updated:
                                        </span>
                                        <span className="flex items-center gap-1 text-sm text-gray-400">
                                            <Clock className="h-3.5 w-3.5" />
                                            Just now
                                        </span>
                                    </div>
                                </div>
                            </motion.div>

                            {/* Onboarding Checklist */}
                            <motion.div
                                variants={itemVariants}
                                className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm"
                            >
                                <h3 className="mb-4 text-base font-bold text-gray-900">
                                    Setup Checklist
                                </h3>
                                <div className="space-y-3">
                                    {[
                                        { label: 'Add a bank account', done: bankAccounts.length > 0 },
                                        { label: 'Upload investment data', done: csvFiles.length > 0 },
                                        { label: 'Connect trading account', done: tradingAccounts.length > 0 },
                                        { label: 'Set financial goals', done: goalsData !== null },
                                    ].map((item) => (
                                        <div
                                            key={item.label}
                                            className="flex items-center gap-2"
                                        >
                                            <CheckCircle2
                                                className={`h-4 w-4 ${
                                                    item.done ? 'text-green-500' : 'text-gray-300'
                                                }`}
                                            />
                                            <span
                                                className={`text-sm ${
                                                    item.done
                                                        ? 'font-medium text-gray-700'
                                                        : 'text-gray-400'
                                                }`}
                                            >
                                                {item.label}
                                            </span>
                                        </div>
                                    ))}
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
                                <button 
                                    className="flex items-center gap-2 text-sm font-medium text-blue-600 transition-colors hover:text-blue-700"
                                    onClick={() => window.dispatchEvent(new Event('open-chatbot'))}
                                >
                                    <MessageCircle className="h-4 w-4" />
                                    Chat with our bot
                                </button>
                            </motion.div>
                        </div>
                    </motion.div>
                </main>
            </PageTransition>

            {/* ===== Modals ===== */}
            <BankingModal
                open={bankingModalOpen}
                onClose={() => setBankingModalOpen(false)}
                onSave={handleAddAccount}
            />

            <InvestmentsPanel
                open={investmentsModalOpen}
                onClose={() => setInvestmentsModalOpen(false)}
                csvFiles={csvFiles}
                onFilesChange={setCsvFiles}
            />

            <CryptoPanel
                open={cryptoModalOpen}
                onClose={() => setCryptoModalOpen(false)}
            />

            <TradingPanel
                open={tradingModalOpen}
                onClose={() => setTradingModalOpen(false)}
                connectedAccounts={tradingAccounts}
                onAccountsChange={setTradingAccounts}
            />

            <GoalsPanel
                open={goalsModalOpen}
                onClose={() => setGoalsModalOpen(false)}
                goalsData={goalsData}
                onSave={setGoalsData}
            />
        </>
    );
}
