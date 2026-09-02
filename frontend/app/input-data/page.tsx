'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { Building2, Coins, Database, FileUp, Goal, Landmark, Loader2, Plus, RefreshCw, ShieldCheck, TrendingUp } from 'lucide-react';

import Navbar from '@/components/layout/navbar';
import PageTransition from '@/components/layout/page-transition';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { OnboardingModal } from '@/components/ui/onboarding-modal';
import { bankingApi, cryptoApi, equityApi, etfApi, goalsApi, mutualFundApi, transactionsApi } from '@/lib/api';
import { useUser } from '@/contexts/user-context';

interface Inventory {
    bankAccounts: number;
    equities: number;
    mutualFunds: number;
    etfs: number;
    crypto: number;
    transactions: number;
    goals: number;
}

const EMPTY: Inventory = { bankAccounts: 0, equities: 0, mutualFunds: 0, etfs: 0, crypto: 0, transactions: 0, goals: 0 };

function message(error: unknown): string {
    if (axios.isAxiosError(error)) return String(error.response?.data?.detail || error.message);
    return error instanceof Error ? error.message : 'The request failed.';
}

export default function InputDataPage() {
    const router = useRouter();
    const { isAuthenticated, isLoading: sessionLoading, isNewUser } = useUser();
    const [inventory, setInventory] = useState<Inventory>(EMPTY);
    const [loading, setLoading] = useState(true);
    const [savingAccount, setSavingAccount] = useState(false);
    const [savingGoal, setSavingGoal] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [notice, setNotice] = useState<string | null>(null);
    const [account, setAccount] = useState({ account_type: 'savings', account_name: '', institution: '', current_balance: '' });
    const [goal, setGoal] = useState({ goal_name: '', goal_type: 'custom', target_amount: '', current_saved: '', target_date: '' });

    const refresh = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [banks, equities, mutualFunds, etfs, crypto, bankTransactions, equityTransactions, mfTransactions, etfTransactions, cryptoTransactions, goals] = await Promise.all([
                bankingApi.getBankAccounts(), equityApi.getEquityHoldings(), mutualFundApi.getMutualFundHoldings(),
                etfApi.getETFHoldings(), cryptoApi.getCryptoHoldings(), transactionsApi.getBankTransactions(),
                transactionsApi.getAssetTransactions('equity'), transactionsApi.getAssetTransactions('mf'),
                transactionsApi.getAssetTransactions('etf'), transactionsApi.getAssetTransactions('crypto'), goalsApi.getGoals(),
            ]);
            setInventory({
                bankAccounts: banks.data.length, equities: equities.data.length, mutualFunds: mutualFunds.data.length,
                etfs: etfs.data.length, crypto: crypto.data.length,
                transactions: bankTransactions.data.length + equityTransactions.data.length + mfTransactions.data.length + etfTransactions.data.length + cryptoTransactions.data.length,
                goals: goals.data.length,
            });
        } catch (caught) {
            setError(message(caught));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (sessionLoading) return;
        if (!isAuthenticated) {
            router.replace('/login?reason=session_required');
            return;
        }
        void refresh();
    }, [isAuthenticated, refresh, router, sessionLoading]);

    const addAccount = async (event: FormEvent) => {
        event.preventDefault();
        setSavingAccount(true);
        setError(null);
        setNotice(null);
        try {
            await bankingApi.addBankAccount({
                account_type: account.account_type,
                account_name: account.account_name,
                institution: account.institution,
                current_balance: Number(account.current_balance),
                currency: 'INR',
                is_primary: inventory.bankAccounts === 0,
            });
            setAccount({ account_type: 'savings', account_name: '', institution: '', current_balance: '' });
            setNotice('Bank account saved to your profile.');
            await refresh();
        } catch (caught) {
            setError(message(caught));
        } finally {
            setSavingAccount(false);
        }
    };

    const addGoal = async (event: FormEvent) => {
        event.preventDefault();
        setSavingGoal(true);
        setError(null);
        setNotice(null);
        try {
            await goalsApi.createGoal({
                goal_name: goal.goal_name,
                goal_type: goal.goal_type,
                target_amount: goal.target_amount ? Number(goal.target_amount) : undefined,
                current_saved: goal.current_saved ? Number(goal.current_saved) : 0,
                target_date: goal.target_date || undefined,
            });
            setGoal({ goal_name: '', goal_type: 'custom', target_amount: '', current_saved: '', target_date: '' });
            setNotice('Financial goal saved to your profile.');
            await refresh();
        } catch (caught) {
            setError(message(caught));
        } finally {
            setSavingGoal(false);
        }
    };

    const preventScrollChange = (e: React.WheelEvent<HTMLInputElement>) => {
        e.currentTarget.blur();
    };

    const cards = [
        ['Bank accounts', inventory.bankAccounts, Landmark], ['Equity holdings', inventory.equities, TrendingUp],
        ['Mutual funds', inventory.mutualFunds, Building2], ['ETFs', inventory.etfs, Database],
        ['Crypto holdings', inventory.crypto, Coins], ['Transactions', inventory.transactions, ShieldCheck],
        ['Goals', inventory.goals, Goal],
    ] as const;

    if (sessionLoading || !isAuthenticated) {
        return <main className="flex min-h-screen items-center justify-center text-sm text-stone-500"><Loader2 className="mr-2 h-4 w-4 animate-spin" />Checking your secure session…</main>;
    }

    return (
        <><Navbar /><PageTransition><main className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
            {isNewUser && <OnboardingModal />}

            <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div><p className="text-sm font-medium text-emerald-700">Data control center</p><h1 className="mt-1 text-3xl font-semibold tracking-tight text-stone-950">Connected financial records</h1><p className="mt-2 max-w-2xl text-sm text-stone-600">Add your bank accounts, investment holdings, and financial goals.</p></div>
                <div className="flex gap-2"><Button variant="outline" disabled={loading} onClick={() => void refresh()}><RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />Refresh</Button><Button asChild><Link href="/csv-files"><FileUp className="mr-2 h-4 w-4" />Import file</Link></Button><Button variant="outline" asChild><Link href="/dashboard">Dashboard</Link></Button></div>
            </header>

            {error && <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error}</div>}
            {notice && <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">{notice}</div>}

            <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {cards.map(([label, value, Icon]) => <div key={label} className="rounded-2xl border border-stone-200 bg-white p-5 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)]"><div className="flex items-center justify-between"><p className="text-sm font-medium text-stone-500">{label}</p><Icon className="h-4 w-4 text-emerald-700" /></div><p className="mt-3 text-3xl font-semibold text-stone-950">{loading ? '—' : value}</p><p className="mt-1 text-xs text-stone-400">Saved records</p></div>)}
            </section>

            <div className="grid gap-6 lg:grid-cols-2">
                <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)]">
                    <div className="flex items-center gap-3"><span className="rounded-xl bg-emerald-50 p-2 text-emerald-700"><Plus className="h-5 w-5" /></span><div><h2 className="font-semibold text-stone-950">Add a bank account</h2><p className="text-sm text-stone-500">Accounts are always entered here, never inferred from an uploaded file.</p></div></div>
                    <form className="mt-6 space-y-4" onSubmit={addAccount}>
                        <div><Label htmlFor="account-type">Account type</Label><select id="account-type" className="mt-1 h-10 w-full rounded-md border border-stone-200 bg-white px-3 text-sm" value={account.account_type} onChange={(event) => setAccount({ ...account, account_type: event.target.value })}><option value="savings">Savings</option><option value="current">Current</option><option value="fixed_deposit">Fixed deposit</option><option value="recurring_deposit">Recurring deposit</option></select></div>
                        <div><Label htmlFor="account-name">Account name</Label><Input id="account-name" className="mt-1" required maxLength={120} value={account.account_name} onChange={(event) => setAccount({ ...account, account_name: event.target.value })} placeholder="Primary savings" /></div>
                        <div><Label htmlFor="institution">Institution</Label><Input id="institution" className="mt-1" required maxLength={120} value={account.institution} onChange={(event) => setAccount({ ...account, institution: event.target.value })} placeholder="Bank name" /></div>
                        <div><Label htmlFor="balance">Current balance (INR)</Label><Input id="balance" className="mt-1" required min="0" step="0.01" type="number" value={account.current_balance} onChange={(event) => setAccount({ ...account, current_balance: event.target.value })} onWheel={preventScrollChange} /></div>
                        <Button className="w-full" disabled={savingAccount}>{savingAccount && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Save account</Button>
                    </form>
                </section>

                <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)]">
                    <div className="flex items-center gap-3"><span className="rounded-xl bg-emerald-50 p-2 text-emerald-700"><Goal className="h-5 w-5" /></span><div><h2 className="font-semibold text-stone-950">Add a financial goal</h2><p className="text-sm text-stone-500">Tell QUANT what you are working toward in your own words.</p></div></div>
                    <form className="mt-6 space-y-4" onSubmit={addGoal}>
                        <div><Label htmlFor="goal-name">Goal name</Label><Input id="goal-name" className="mt-1" required maxLength={160} value={goal.goal_name} onChange={(event) => setGoal({ ...goal, goal_name: event.target.value })} placeholder="Buy a home" /></div>
                        <div><Label htmlFor="goal-type">Goal type</Label><select id="goal-type" className="mt-1 h-10 w-full rounded-md border border-stone-200 bg-white px-3 text-sm" value={goal.goal_type} onChange={(event) => setGoal({ ...goal, goal_type: event.target.value })}><option value="custom">Custom</option><option value="house">Home</option><option value="retirement">Retirement</option><option value="education">Education</option><option value="emergency">Emergency fund</option><option value="wealth">Wealth building</option></select></div>
                        <div className="grid gap-4 sm:grid-cols-2"><div><Label htmlFor="goal-target">Target amount (INR)</Label><Input id="goal-target" className="mt-1" min="0.01" step="0.01" type="number" value={goal.target_amount} onChange={(event) => setGoal({ ...goal, target_amount: event.target.value })} placeholder="5000000" onWheel={preventScrollChange} /></div><div><Label htmlFor="goal-saved">Already saved (INR)</Label><Input id="goal-saved" className="mt-1" min="0" step="0.01" type="number" value={goal.current_saved} onChange={(event) => setGoal({ ...goal, current_saved: event.target.value })} placeholder="0" onWheel={preventScrollChange} /></div></div>
                        <div><Label htmlFor="goal-date">Target date (optional)</Label><Input id="goal-date" className="mt-1" type="date" value={goal.target_date} onChange={(event) => setGoal({ ...goal, target_date: event.target.value })} /></div>
                        <Button className="w-full" disabled={savingGoal}>{savingGoal && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Save goal</Button>
                    </form>
                </section>

                <section className="rounded-2xl border border-stone-200 bg-[#09090B] p-7 text-white shadow-sm lg:col-span-2">
                    <ShieldCheck className="h-8 w-8 text-emerald-400" /><h2 className="mt-5 text-2xl font-semibold">One import path for every supported file</h2><p className="mt-3 max-w-xl text-sm leading-6 text-stone-300">Upload your bank statements, portfolio exports, or CAS reports. QUANT will preview and validate every row before saving — invalid entries are never silently imported.</p>
                    <div className="mt-6 grid gap-3 sm:grid-cols-2">{['Smart column matching', 'Zerodha and Upstox exports', 'Common bank transaction statements', 'CAMS/KFintech text PDFs'].map((item) => <div key={item} className="rounded-xl border border-stone-700 bg-stone-900 p-3 text-sm text-stone-200">{item}</div>)}</div>
                    <Button className="mt-7 bg-white text-stone-950 hover:bg-stone-100" asChild><Link href="/csv-files">Open secure importer</Link></Button>
                </section>
            </div>
        </main></PageTransition></>
    );
}
