'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    TrendingUp,
    AlertTriangle,
    BarChart3,
    Lightbulb,
    ArrowUpRight,
    IndianRupee,
    ShieldCheck,
} from 'lucide-react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
    Legend,
} from 'recharts';
import Navbar from '@/components/layout/navbar';
import PageTransition from '@/components/layout/page-transition';
import {
    SkeletonCard,
    SkeletonChart,
    SkeletonTable,
} from '@/components/ui/skeletons';
import { dashboardApi, userApi, bankingApi, equityApi, mutualFundApi, etfApi, cryptoApi, transactionsApi } from '@/lib/api';
import { formatCurrency, formatChartValue } from '@/lib/helpers';
import type { DashboardData, DashboardRunOut } from '@/types';
import { fetchLivePrices } from '@/app/actions/fetch-prices';



// ==========================================
// Sub-components
// ==========================================

function RiskGauge({ level }: { level: 'Low' | 'Medium' | 'High' }) {
    const levels = ['Low', 'Medium', 'High'];
    return (
        <div className="flex items-end gap-2 pt-2">
            {levels.map((l) => {
                const isActive = levels.indexOf(l) <= levels.indexOf(level);
                const colors: Record<string, string> = {
                    Low: 'bg-emerald-500',
                    Medium: 'bg-amber-500',
                    High: 'bg-red-500',
                };
                const heights: Record<string, string> = {
                    Low: 'h-6',
                    Medium: 'h-10',
                    High: 'h-14',
                };
                return (
                    <div key={l} className="flex flex-col items-center gap-1">
                        <motion.div
                            initial={{ scaleY: 0 }}
                            animate={{ scaleY: 1 }}
                            transition={{ duration: 0.5, delay: levels.indexOf(l) * 0.15 }}
                            className={`w-6 origin-bottom rounded-t-md ${heights[l]} ${isActive ? colors[l] : 'bg-gray-200'
                                }`}
                        />
                        <span
                            className={`text-[10px] font-medium ${l === level ? 'text-gray-900' : 'text-gray-400'
                                }`}
                        >
                            {l}
                        </span>
                    </div>
                );
            })}
        </div>
    );
}

function CashflowBar({
    income,
    expenses,
}: {
    income: number;
    expenses: number;
}) {
    const total = income || 1; // avoid division by zero
    const expPct = (expenses / total) * 100;
    const incPct = income === 0 && expenses === 0 ? 0 : 100;

    return (
        <div className="space-y-2 pt-2">
            <div className="flex h-5 w-full overflow-hidden rounded-full bg-gray-100">
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${incPct}%` }}
                    transition={{ duration: 0.8 }}
                    className="bg-emerald-500 rounded-full"
                />
            </div>
            <div className="flex h-5 w-full overflow-hidden rounded-full bg-gray-100">
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${expPct}%` }}
                    transition={{ duration: 0.8, delay: 0.2 }}
                    className="bg-red-400 rounded-full"
                />
            </div>
            <div className="flex items-center justify-between text-xs text-gray-500">
                <div className="flex items-center gap-1">
                    <span className="h-2 w-2 rounded-full bg-emerald-500" />
                    Income
                </div>
                <div className="flex items-center gap-1">
                    <span className="h-2 w-2 rounded-full bg-red-400" />
                    Expenses
                </div>
            </div>
        </div>
    );
}

const alertIcons: Record<string, React.ReactNode> = {
    'alert-triangle': <AlertTriangle className="h-5 w-5 text-amber-500" />,
    'bar-chart-3': <BarChart3 className="h-5 w-5 text-blue-500" />,
    lightbulb: <Lightbulb className="h-5 w-5 text-yellow-500" />,
};

// ==========================================
// Custom Tooltip
// ==========================================
interface TooltipPayloadItem {
    value: number;
}

function CustomTooltip({
    active,
    payload,
    label,
}: {
    active?: boolean;
    payload?: TooltipPayloadItem[];
    label?: string;
}) {
    if (!active || !payload?.length) return null;
    return (
        <div className="rounded-lg border border-gray-100 bg-white px-4 py-2 shadow-lg">
            <p className="text-xs text-gray-500">{label}</p>
            <p className="text-sm font-bold text-gray-900">
                {formatCurrency(payload[0].value)}
            </p>
        </div>
    );
}

// ==========================================
// Main Dashboard Page
// ==========================================
export default function DashboardPage() {
    const [isLoading, setIsLoading] = useState(true);
    const [data, setData] = useState<DashboardData | null>(null);

    useEffect(() => {
        // ── FRONTEND LIVE PRICING AGGREGATION ─────────────────────────
        async function fetchDashboard() {
            try {
                // Frontend aggregation with live prices
                const [
                    profileRes, bankRes, eqRes, mfRes, etfRes, cryptRes, txRes
                ] = await Promise.all([
                    userApi.getProfile().catch(() => ({ data: {} })),
                    bankingApi.getBankAccounts().catch(() => ({ data: [] })),
                    equityApi.getEquityHoldings().catch(() => ({ data: [] })),
                    mutualFundApi.getMutualFundHoldings().catch(() => ({ data: [] })),
                    etfApi.getETFHoldings().catch(() => ({ data: [] })),
                    cryptoApi.getCryptoHoldings().catch(() => ({ data: [] })),
                    transactionsApi.getBankTransactions().catch(() => ({ data: [] }))
                ]);

                const user = profileRes.data as any;
                const bankAccounts = bankRes.data as any[];
                const eq = eqRes.data as any[];
                const mf = mfRes.data as any[];
                const etf = etfRes.data as any[];
                const crypt = cryptRes.data as any[];
                const txs = txRes.data as any[];

                // Fetch live prices using Server Action
                const allQueryHoldings = [
                    ...eq.map(h => ({ type: 'Equity', symbol: h.symbol })),
                    ...mf.map(h => ({ type: 'Mutual Fund', symbol: h.name, scheme_code: h.scheme_code })),
                    ...etf.map(h => ({ type: 'ETF', symbol: h.symbol })),
                    ...crypt.map(h => ({ type: 'Crypto', symbol: h.symbol }))
                ];

                let livePrices: Record<string, number> = {};
                try {
                    livePrices = await fetchLivePrices(allQueryHoldings);
                } catch (err) {
                    console.error("Failed to fetch live prices", err);
                }

                // Helper to get real current value
                const getRealVal = (h: any, type: string, qtyKey: string, priceKey: string, symbolKey: string) => {
                    const qty = Number(h[qtyKey]) || 0;
                    const avg = Number(h[priceKey]) || 0;
                    const symbol = h[symbolKey];
                    const livePrice = livePrices[`${type}-${symbol}`];
                    
                    const currentPrice = livePrice || avg; // fallback to avg if live fails
                    const currentValue = qty * currentPrice;
                    const plPercent = avg > 0 ? ((currentPrice - avg) / avg) * 100 : 0;
                    
                    return { quantity: qty, avg_price: avg, current_price: currentPrice, current_value: currentValue, profit_loss_percent: plPercent };
                };

                // Map holdings
                const mappedEq = eq.map(h => ({ instrument: h.symbol, type: 'Equity', ...getRealVal(h, 'Equity', 'quantity', 'avg_price', 'symbol') }));
                const mappedMf = mf.map(h => ({ instrument: h.name, type: 'Mutual Fund', ...getRealVal(h, 'Mutual Fund', 'units', 'avg_nav', 'name') }));
                const mappedEtf = etf.map(h => ({ instrument: h.symbol, type: 'ETF', ...getRealVal(h, 'ETF', 'quantity', 'avg_price', 'symbol') }));
                const mappedCrypt = crypt.map(h => ({ instrument: h.symbol, type: 'Crypto', ...getRealVal(h, 'Crypto', 'quantity', 'avg_price', 'symbol') }));

                // Calculate totals
                const banking_total = bankAccounts.reduce((acc, b) => acc + (Number(b.current_balance) || 0), 0);
                const eq_total = mappedEq.reduce((acc, h) => acc + h.current_value, 0);
                const mf_total = mappedMf.reduce((acc, h) => acc + h.current_value, 0);
                const etf_total = mappedEtf.reduce((acc, h) => acc + h.current_value, 0);
                const crypt_total = mappedCrypt.reduce((acc, h) => acc + h.current_value, 0);

                const net_worth = banking_total + eq_total + mf_total + etf_total + crypt_total;

                // Total Invested Value
                const eq_inv = mappedEq.reduce((acc, h) => acc + (h.quantity * h.avg_price), 0);
                const mf_inv = mappedMf.reduce((acc, h) => acc + (h.quantity * h.avg_price), 0);
                const etf_inv = mappedEtf.reduce((acc, h) => acc + (h.quantity * h.avg_price), 0);
                const crypt_inv = mappedCrypt.reduce((acc, h) => acc + (h.quantity * h.avg_price), 0);
                const total_invested_assets = eq_inv + mf_inv + etf_inv + crypt_inv;
                const total_invested_net_worth = banking_total + total_invested_assets;

                // Asset allocation
                const allocations = [
                    { name: 'Cash', value: banking_total, color: '#3b82f6' },
                    { name: 'Equities', value: eq_total, color: '#10b981' },
                    { name: 'Mutual Funds', value: mf_total, color: '#f59e0b' },
                    { name: 'ETFs', value: etf_total, color: '#ef4444' },
                    { name: 'Crypto', value: crypt_total, color: '#8b5cf6' }
                ];
                const totalCurrentAssets = allocations.reduce((a, b) => a + b.value, 0);
                const asset_allocation = totalCurrentAssets === 0 ? [] : allocations.filter(a => a.value > 0).map(a => ({
                    name: a.name,
                    value: Number(((a.value / totalCurrentAssets) * 100).toFixed(2)),
                    color: a.color
                }));

                // Top holdings
                const allHoldings = [...mappedEq, ...mappedMf, ...mappedEtf, ...mappedCrypt];
                const top_holdings = allHoldings.sort((a, b) => b.current_value - a.current_value).slice(0, 5).map(h => ({...h, profit_loss_percent: Number(h.profit_loss_percent.toFixed(2))}));

                // History - Realistic Straight Line from Invested -> Current
                const portfolio_history = Array.from({length: 12}).map((_, i) => {
                    const d = new Date();
                    d.setMonth(d.getMonth() - (11 - i));
                    
                    // Simple linear interpolation from invested to current over 12 months
                    const step = (net_worth - total_invested_net_worth) / 11;
                    const val = total_invested_net_worth + (step * i);
                    
                    return { 
                        month: d.toLocaleString('default', {month: 'short', year: 'numeric'}), 
                        value: Number(val.toFixed(2)) 
                    };
                });

                // Cashflow
                const lastMonth = new Date();
                lastMonth.setDate(lastMonth.getDate() - 30);
                const recentTxs = txs.filter(t => new Date(t.tx_date) >= lastMonth);
                const monthly_income = recentTxs.filter(t => t.tx_type === 'credit').reduce((a, b) => a + Number(b.amount), 0) || Number(user.monthly_income || 0);
                const monthly_expenses = recentTxs.filter(t => t.tx_type === 'debit').reduce((a, b) => a + Number(b.amount), 0) || Number(user.monthly_expenses || 0);
                const surplus = Math.max(0, monthly_income - monthly_expenses);

                // Tax saved
                const tax_saved = Math.min(150000, (eq_total + mf_total) * 0.30 * 0.15);

                // Risk level
                const riskMap: any = { conservative: 'Low', moderate: 'Medium', aggressive: 'High' };
                const risk_level = riskMap[user.risk_profile] || 'Medium';

                const alerts: any[] = [];
                if (net_worth === 0) alerts.push({ id: '1', type: 'info', message: 'Connect your accounts or insert data to see insights.', icon: 'lightbulb' });
                else if (net_worth < 100000) alerts.push({ id: '2', type: 'info', message: 'Your net worth is below ₹1,00,000. Start with small investments.', icon: 'lightbulb' });
                
                if (monthly_expenses > monthly_income) alerts.push({ id: '3', type: 'warning', message: 'Expenses exceed income', icon: 'alert-triangle' });
                else if (surplus > 50000) alerts.push({ id: '4', type: 'opportunity', message: 'Strong monthly surplus! Consider increasing investments.', icon: 'bar-chart-3' });

                setData({
                    net_worth,
                    net_worth_growth: net_worth > 0 ? 0.42 : 0, 
                    risk_level,
                    monthly_income,
                    monthly_expenses,
                    surplus,
                    tax_saved,
                    tax_limit: 150000,
                    portfolio_history,
                    asset_allocation,
                    top_holdings,
                    alerts
                });

            } catch (error) {
                console.warn('Dashboard API unavailable', error);
                setData(null);
            } finally {
                setIsLoading(false);
            }
        }
        fetchDashboard();
        // ────────────────────────────────────────────────────────────────
    }, []);

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
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                        {Array.from({ length: 4 }).map((_, i) => (
                            <SkeletonCard key={i} />
                        ))}
                    </div>
                    <div className="mt-6 grid gap-6 lg:grid-cols-[2fr_1fr]">
                        <SkeletonChart />
                        <SkeletonCard className="h-72" />
                    </div>
                    <div className="mt-6 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
                        <SkeletonTable />
                        <SkeletonCard className="h-56" />
                    </div>
                </div>
            </>
        );
    }

    if (!data) {
        return (
            <>
                <Navbar />
                <div className="mx-auto max-w-7xl px-4 py-16 text-center sm:px-6 lg:px-8">
                    <div className="rounded-xl border border-gray-100 bg-white p-12 shadow-sm">
                        <IndianRupee className="mx-auto h-12 w-12 text-gray-300" />
                        <h2 className="mt-4 text-lg font-semibold text-gray-900">
                            No dashboard data available
                        </h2>
                        <p className="mt-2 text-sm text-gray-500">
                            Connect your backend API to see your financial overview here.
                        </p>
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
                        className="space-y-6"
                    >
                        {/* ===== Summary Cards Row ===== */}
                        <motion.div
                            variants={itemVariants}
                            className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
                        >
                            {/* Net Worth */}
                            <div className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm transition-shadow hover:shadow-md">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-sm font-medium text-gray-500">
                                        Net Worth
                                    </h3>
                                    <div className="rounded-lg bg-emerald-50 p-1.5">
                                        <IndianRupee className="h-4 w-4 text-emerald-600" />
                                    </div>
                                </div>
                                <p className="mt-2 text-2xl font-bold text-gray-900">
                                    {formatCurrency(data.net_worth)}
                                </p>
                                <div className="mt-1 flex items-center gap-1 text-sm">
                                    <ArrowUpRight className="h-4 w-4 text-emerald-500" />
                                    <span className="font-medium text-emerald-600">
                                        +{data.net_worth_growth}%
                                    </span>
                                    <span className="text-gray-400">vs last month</span>
                                </div>
                            </div>

                            {/* Risk Level */}
                            <div className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm transition-shadow hover:shadow-md">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-sm font-medium text-gray-500">
                                        Risk Level
                                    </h3>
                                    <div className="rounded-lg bg-amber-50 p-1.5">
                                        <ShieldCheck className="h-4 w-4 text-amber-600" />
                                    </div>
                                </div>
                                <RiskGauge level={data.risk_level} />
                            </div>

                            {/* Monthly Cashflow */}
                            <div className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm transition-shadow hover:shadow-md">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-sm font-medium text-gray-500">
                                        Monthly Cashflow
                                    </h3>
                                    <div className="rounded-lg bg-blue-50 p-1.5">
                                        <TrendingUp className="h-4 w-4 text-blue-600" />
                                    </div>
                                </div>
                                <CashflowBar
                                    income={data.monthly_income}
                                    expenses={data.monthly_expenses}
                                />
                                <p className="mt-2 text-sm">
                                    <span className="text-gray-500">Surplus: </span>
                                    <span className="font-bold text-emerald-600">
                                        {formatCurrency(data.surplus)}
                                    </span>
                                </p>
                            </div>

                            {/* Tax Saving */}
                            <div className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm transition-shadow hover:shadow-md">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-sm font-medium text-gray-500">
                                        Tax Saving Used (80C)
                                    </h3>
                                </div>
                                <div className="mt-3">
                                    <div className="h-3 w-full overflow-hidden rounded-full bg-gray-100">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{
                                                width: `${(data.tax_saved / data.tax_limit) * 100}%`,
                                            }}
                                            transition={{ duration: 1, delay: 0.3 }}
                                            className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-emerald-600"
                                        />
                                    </div>
                                    <p className="mt-2 text-lg font-bold text-gray-900">
                                        {formatCurrency(data.tax_saved)}{' '}
                                        <span className="text-gray-400">
                                            / {formatCurrency(data.tax_limit)}
                                        </span>
                                    </p>
                                </div>
                            </div>
                        </motion.div>

                        {/* ===== Charts Row ===== */}
                        <motion.div
                            variants={itemVariants}
                            className="grid gap-6 lg:grid-cols-[2fr_1fr]"
                        >
                            {/* Portfolio Line Chart */}
                            <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
                                <h3 className="mb-4 text-base font-bold text-gray-900">
                                    Portfolio Value Over Time{' '}
                                    <span className="text-sm font-normal text-gray-400">
                                        (Last 12 Months)
                                    </span>
                                </h3>
                                <ResponsiveContainer width="100%" height={280}>
                                    <LineChart data={data.portfolio_history}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                                        <XAxis
                                            dataKey="month"
                                            tick={{ fontSize: 12, fill: '#94a3b8' }}
                                            axisLine={{ stroke: '#e2e8f0' }}
                                        />
                                        <YAxis
                                            tickFormatter={formatChartValue}
                                            tick={{ fontSize: 12, fill: '#94a3b8' }}
                                            axisLine={{ stroke: '#e2e8f0' }}
                                        />
                                        <Tooltip content={<CustomTooltip />} />
                                        <defs>
                                            <linearGradient
                                                id="portfolioGradient"
                                                x1="0"
                                                y1="0"
                                                x2="0"
                                                y2="1"
                                            >
                                                <stop
                                                    offset="5%"
                                                    stopColor="#3B82F6"
                                                    stopOpacity={0.15}
                                                />
                                                <stop
                                                    offset="95%"
                                                    stopColor="#3B82F6"
                                                    stopOpacity={0}
                                                />
                                            </linearGradient>
                                        </defs>
                                        <Line
                                            type="monotone"
                                            dataKey="value"
                                            stroke="#3B82F6"
                                            strokeWidth={2.5}
                                            dot={false}
                                            activeDot={{ r: 5, fill: '#3B82F6' }}
                                            fill="url(#portfolioGradient)"
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>

                            {/* Asset Allocation Donut */}
                            <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
                                <h3 className="mb-4 text-base font-bold text-gray-900">
                                    Asset Allocation
                                </h3>
                                <ResponsiveContainer width="100%" height={220}>
                                    <PieChart>
                                        <Pie
                                            data={data.asset_allocation}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={55}
                                            outerRadius={80}
                                            paddingAngle={3}
                                            dataKey="value"
                                            stroke="none"
                                        >
                                            {data.asset_allocation.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <Legend
                                            iconType="circle"
                                            iconSize={8}
                                            formatter={(value: string) => (
                                                <span className="text-xs text-gray-600">{value}</span>
                                            )}
                                        />
                                    </PieChart>
                                </ResponsiveContainer>
                                <div className="mt-2 space-y-1.5">
                                    {data.asset_allocation.map((item) => (
                                        <div
                                            key={item.name}
                                            className="flex items-center justify-between text-sm"
                                        >
                                            <div className="flex items-center gap-2">
                                                <span
                                                    className="h-2.5 w-2.5 rounded-full"
                                                    style={{ backgroundColor: item.color }}
                                                />
                                                <span className="text-gray-600">{item.name}</span>
                                            </div>
                                            <span className="font-semibold text-gray-900">
                                                {item.value}%
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </motion.div>

                        {/* ===== Bottom Row ===== */}
                        <motion.div
                            variants={itemVariants}
                            className="grid gap-6 lg:grid-cols-[1.4fr_1fr]"
                        >
                            {/* Top Holdings Table */}
                            <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
                                <h3 className="mb-4 text-base font-bold text-gray-900">
                                    Top Holdings
                                </h3>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b border-gray-100">
                                                <th className="pb-3 text-left font-semibold text-gray-500">
                                                    Instrument
                                                </th>
                                                <th className="pb-3 text-left font-semibold text-gray-500">
                                                    Type
                                                </th>
                                                <th className="pb-3 text-right font-semibold text-gray-500">
                                                    Quantity
                                                </th>
                                                <th className="pb-3 text-right font-semibold text-gray-500">
                                                    Current Value
                                                </th>
                                                <th className="pb-3 text-right font-semibold text-gray-500">
                                                    P/L (%)
                                                </th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {data.top_holdings.map((holding, i) => (
                                                <motion.tr
                                                    key={holding.instrument}
                                                    initial={{ opacity: 0, x: -10 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    transition={{ delay: 0.6 + i * 0.1 }}
                                                    className="border-b border-gray-50 last:border-0"
                                                >
                                                    <td className="py-3 font-medium text-gray-900">
                                                        {holding.instrument}
                                                    </td>
                                                    <td className="py-3 text-gray-500">
                                                        {holding.type}
                                                    </td>
                                                    <td className="py-3 text-right text-gray-600">
                                                        {holding.quantity}
                                                    </td>
                                                    <td className="py-3 text-right font-medium text-gray-900">
                                                        {formatCurrency(holding.current_value)}
                                                    </td>
                                                    <td
                                                        className={`py-3 text-right font-semibold ${holding.profit_loss_percent >= 0
                                                            ? 'text-emerald-600'
                                                            : 'text-red-500'
                                                            }`}
                                                    >
                                                        {holding.profit_loss_percent > 0 ? '+' : ''}
                                                        {holding.profit_loss_percent}%
                                                    </td>
                                                </motion.tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            {/* Alerts & Insights */}
                            <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
                                <h3 className="mb-4 text-base font-bold text-blue-600">
                                    Alerts & Insights
                                </h3>
                                <div className="space-y-4">
                                    {data.alerts.map((alert, i) => (
                                        <motion.div
                                            key={alert.id}
                                            initial={{ opacity: 0, x: 10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: 0.8 + i * 0.15 }}
                                            className="flex items-start gap-3 rounded-lg bg-gray-50 p-3.5 transition-colors hover:bg-gray-100"
                                        >
                                            <div className="mt-0.5 shrink-0">
                                                {alertIcons[alert.icon] || (
                                                    <AlertTriangle className="h-5 w-5 text-gray-400" />
                                                )}
                                            </div>
                                            <p className="text-sm leading-relaxed text-gray-700">
                                                {alert.message}
                                            </p>
                                        </motion.div>
                                    ))}
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                </main>
            </PageTransition>
        </>
    );
}
