'use client';

import { useCallback, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    AlertTriangle,
    BarChart2,
    BookOpen,
    CheckCircle2,
    ChevronDown,
    ChevronRight,
    Clock,
    Info,
    RefreshCw,
    ShieldCheck,
    Sparkles,
    Star,
    Target,
    TrendingDown,
    TrendingUp,
} from 'lucide-react';

import Navbar from '@/components/layout/navbar';
import PageTransition from '@/components/layout/page-transition';
import { insightsApi } from '@/lib/api';
import { formatCurrency } from '@/lib/helpers';
import type {
    AssetForecast,
    GoalGap,
    InsightsResult,
    InstrumentSuggestion,
    RebalanceAction,
} from '@/types';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function timeAgo(iso: string): string {
    const diff = (Date.now() - new Date(iso).getTime()) / 1000;
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
}

function capitalise(s: string): string {
    return s.charAt(0).toUpperCase() + s.slice(1);
}

// ---------------------------------------------------------------------------
// Small reusable components
// ---------------------------------------------------------------------------

function LayerTab({
    label,
    active,
    icon,
    onClick,
    id,
}: {
    label: string;
    active: boolean;
    icon: React.ReactNode;
    onClick: () => void;
    id: string;
}) {
    return (
        <button
            id={id}
            onClick={onClick}
            className={`flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold transition-all duration-200 ${
                active
                    ? 'bg-white text-blue-700 shadow-sm ring-1 ring-blue-100'
                    : 'text-slate-500 hover:text-slate-800'
            }`}
        >
            {icon}
            {label}
        </button>
    );
}

function ConfidencePill({ level }: { level: 'High' | 'Medium' | 'Low' }) {
    const styles = {
        High: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        Medium: 'bg-amber-50 text-amber-700 border-amber-200',
        Low: 'bg-red-50 text-red-700 border-red-200',
    };
    return (
        <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles[level]}`}>
            {level} confidence
        </span>
    );
}

function SignalBadge({ signal }: { signal: 'HOLD' | 'REDUCE' | 'ADD' }) {
    const styles = {
        HOLD: 'bg-slate-100 text-slate-700 border-slate-200',
        REDUCE: 'bg-amber-50 text-amber-700 border-amber-200',
        ADD: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    };
    return (
        <span className={`rounded-lg border px-3 py-1.5 text-xs font-bold tracking-wide ${styles[signal]}`}>
            {signal}
        </span>
    );
}

function RiskBadge({ level }: { level: 'Low' | 'Medium' | 'High' }) {
    const styles = {
        Low: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        Medium: 'bg-amber-50 text-amber-700 border-amber-200',
        High: 'bg-red-50 text-red-700 border-red-200',
    };
    return (
        <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles[level]}`}>
            {level}
        </span>
    );
}

// ---------------------------------------------------------------------------
// Layer A sub-components
// ---------------------------------------------------------------------------

function ForecastCard({ forecast, index }: { forecast: AssetForecast; index: number }) {
    const isUp = forecast.direction === 'up';
    const isDown = forecast.direction === 'down';

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.08 }}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow"
        >
            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-slate-400">
                        {forecast.asset_class}
                    </p>
                    <div className="mt-1.5 flex items-baseline gap-1.5">
                        {isUp ? (
                            <TrendingUp className="h-5 w-5 text-emerald-500" />
                        ) : isDown ? (
                            <TrendingDown className="h-5 w-5 text-red-400" />
                        ) : (
                            <BarChart2 className="h-5 w-5 text-slate-400" />
                        )}
                        <span
                            className={`text-2xl font-bold tracking-tight ${
                                isUp ? 'text-emerald-600' : isDown ? 'text-red-500' : 'text-slate-700'
                            }`}
                        >
                            {forecast.forecast_return_low > 0 ? '+' : ''}
                            {forecast.forecast_return_low.toFixed(1)}% to{' '}
                            {forecast.forecast_return_high > 0 ? '+' : ''}
                            {forecast.forecast_return_high.toFixed(1)}%
                        </span>
                    </div>
                </div>
                <ConfidencePill level={forecast.confidence} />
            </div>

            {/* Mini sparkline visual (decorative gradient line) */}
            <div className="mt-4 h-12 rounded-lg overflow-hidden">
                <svg width="100%" height="100%" viewBox="0 0 200 48" preserveAspectRatio="none">
                    <defs>
                        <linearGradient id={`grad-${forecast.asset_class}`} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor={isUp ? '#10b981' : isDown ? '#f87171' : '#94a3b8'} stopOpacity="0.2" />
                            <stop offset="100%" stopColor={isUp ? '#10b981' : isDown ? '#f87171' : '#94a3b8'} stopOpacity="0" />
                        </linearGradient>
                    </defs>
                    <path
                        d={
                            isUp
                                ? 'M0,40 C40,38 80,28 120,20 C160,12 180,8 200,4'
                                : isDown
                                ? 'M0,8 C40,10 80,20 120,28 C160,36 180,40 200,44'
                                : 'M0,24 C40,22 80,26 120,23 C160,20 180,25 200,24'
                        }
                        fill={`url(#grad-${forecast.asset_class})`}
                        stroke={isUp ? '#10b981' : isDown ? '#f87171' : '#94a3b8'}
                        strokeWidth="2"
                        fillOpacity="1"
                    />
                </svg>
            </div>

            <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
                <span>30-day horizon</span>
                <span className="flex items-center gap-1">
                    <Info className="h-3 w-3" />
                    Model: {forecast.model.split('-').slice(0, 2).join('-')}
                </span>
            </div>
        </motion.div>
    );
}

function ActionRow({ action, index }: { action: RebalanceAction; index: number }) {
    return (
        <motion.div
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.06 }}
            className={`rounded-xl border p-4 ${
                action.tax_flag ? 'border-amber-200 bg-amber-50/40' : 'border-slate-100 bg-white'
            }`}
        >
            <div className="flex items-start gap-3">
                <SignalBadge signal={action.signal} />
                <div className="min-w-0 flex-1">
                    <p className="font-semibold text-slate-800 text-sm">{action.asset_class}</p>
                    <p className="mt-0.5 text-xs text-slate-500">{action.reason}</p>
                    {action.tax_flag && (
                        <div className="mt-2 flex items-start gap-1.5 rounded-lg bg-amber-50 p-2 text-xs text-amber-700 border border-amber-200">
                            <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" />
                            <span>{action.tax_flag}</span>
                        </div>
                    )}
                </div>
                <div className="text-right text-xs text-slate-400 whitespace-nowrap">
                    <p>Current: {action.current_weight_pct.toFixed(1)}%</p>
                    <p>Target: {action.target_weight_pct.toFixed(1)}%</p>
                </div>
            </div>
        </motion.div>
    );
}

// ---------------------------------------------------------------------------
// Layer B sub-components
// ---------------------------------------------------------------------------

function GoalCard({ gap, index }: { gap: GoalGap; index: number }) {
    const progress = gap.target_amount > 0
        ? Math.min(100, (gap.current_amount / gap.target_amount) * 100)
        : 0;

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.07 }}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
        >
            <div className="flex items-start justify-between">
                <div className="flex items-center gap-2.5">
                    <div className={`rounded-xl p-2 ${gap.on_track ? 'bg-emerald-50' : 'bg-blue-50'}`}>
                        <Target className={`h-4 w-4 ${gap.on_track ? 'text-emerald-600' : 'text-blue-600'}`} />
                    </div>
                    <div>
                        <p className="font-semibold text-slate-800">{gap.goal_name}</p>
                        <p className="text-xs text-slate-400 capitalize">{gap.horizon}-term · {gap.target_date ?? 'No date set'}</p>
                    </div>
                </div>
                <div className="text-right">
                    <p className="text-xs text-slate-400">Target</p>
                    <p className="font-semibold text-slate-700">{formatCurrency(gap.target_amount)}</p>
                </div>
            </div>

            {/* Progress bar */}
            <div className="mt-4">
                <div className="flex items-center justify-between text-xs text-slate-500 mb-1.5">
                    <span>{formatCurrency(gap.current_amount)} saved</span>
                    <span>{progress.toFixed(0)}%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                    <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.8, ease: 'easeOut', delay: index * 0.07 + 0.2 }}
                        className={`h-full rounded-full ${gap.on_track ? 'bg-emerald-500' : 'bg-blue-500'}`}
                    />
                </div>
            </div>

            {/* Gap summary */}
            {!gap.on_track && (
                <div className="mt-4 flex items-center justify-between rounded-lg bg-blue-50 px-4 py-3">
                    <div>
                        <p className="text-xs text-blue-600 font-medium">You are</p>
                        <p className="text-xl font-bold text-blue-700">{gap.shortfall_pct.toFixed(0)}% short</p>
                        <p className="text-xs text-blue-500">at current pace</p>
                    </div>
                    <div className="text-right">
                        <p className="text-xs text-slate-500">Gap</p>
                        <p className="font-semibold text-slate-700">{formatCurrency(gap.gap)}</p>
                        {gap.required_monthly_sip > 0 && (
                            <>
                                <p className="mt-1 text-xs text-slate-400">Suggested SIP</p>
                                <p className="text-sm font-semibold text-blue-600">{formatCurrency(gap.required_monthly_sip)}/mo</p>
                            </>
                        )}
                    </div>
                </div>
            )}

            {gap.on_track && (
                <div className="mt-4 flex items-center gap-2 rounded-lg bg-emerald-50 px-4 py-3">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    <p className="text-sm font-medium text-emerald-700">On track — keep it up!</p>
                </div>
            )}
        </motion.div>
    );
}

function SuggestionRow({ suggestion, index }: { suggestion: InstrumentSuggestion; index: number }) {
    const icons = ['📊', '🌐', '🏅', '🏦'];
    return (
        <motion.div
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.07 }}
            className="flex items-center justify-between rounded-xl border border-slate-100 bg-white p-4 hover:bg-slate-50 transition-colors"
        >
            <div className="flex items-center gap-3">
                <span className="text-xl">{icons[index % icons.length]}</span>
                <div>
                    <p className="font-semibold text-slate-800 text-sm">{suggestion.name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{suggestion.rationale}</p>
                    {suggestion.driven_by_goal && (
                        <p className="text-xs text-blue-500 mt-0.5">For: {suggestion.driven_by_goal}</p>
                    )}
                </div>
            </div>
            <div className="flex-shrink-0">
                <RiskBadge level={suggestion.risk_level} />
            </div>
        </motion.div>
    );
}

// ---------------------------------------------------------------------------
// Empty states
// ---------------------------------------------------------------------------

function EmptyState({ title, body }: { title: string; body: string }) {
    return (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 py-16 text-center px-8">
            <BarChart2 className="h-10 w-10 text-slate-300 mb-3" />
            <p className="font-semibold text-slate-600">{title}</p>
            <p className="mt-1.5 text-sm text-slate-400 max-w-xs">{body}</p>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

type ActiveLayer = 'trading' | 'recommendations';

export default function InsightsPage() {
    const [data, setData] = useState<InsightsResult | null>(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [activeLayer, setActiveLayer] = useState<ActiveLayer>('trading');
    const [gcOpen, setGcOpen] = useState(false);

    const load = useCallback(async (force = false) => {
        if (force) setRefreshing(true);
        else setLoading(true);
        setError(null);
        try {
            const response = force
                ? await insightsApi.generate()
                : await insightsApi.latest();
            setData(response.data);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Could not load insights');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, []);

    useEffect(() => { void load(); }, [load]);

    const layerAAvailable = data?.layer_a.status === 'available';
    const layerBAvailable = data?.layer_b.status === 'available';

    return (
        <PageTransition>
            <div className="min-h-screen bg-slate-50">
                <Navbar />

                <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">

                    {/* ── Page header ──────────────────────────────────────── */}
                    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                            <p className="text-sm font-medium text-blue-600">Insights &amp; Trading</p>
                            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
                                Personalized guidance,{' '}
                                <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                                    grounded in evidence
                                </span>
                            </h1>
                            <p className="mt-1.5 text-sm text-slate-500">
                                Two layers of intelligence working together to help you make smarter financial decisions.
                            </p>
                        </div>

                        {/* Status + refresh */}
                        <div className="flex flex-shrink-0 items-start gap-3">
                            {data && (
                                <div className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs shadow-sm">
                                    <div className="flex items-center gap-2 text-slate-500">
                                        <Clock className="h-3.5 w-3.5" />
                                        <span>Updated {timeAgo(data.generated_at)}</span>
                                    </div>
                                </div>
                            )}
                            <button
                                id="insights-refresh-btn"
                                onClick={() => void load(true)}
                                disabled={refreshing || loading}
                                className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:opacity-50"
                            >
                                <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                                {refreshing ? 'Refreshing…' : 'Refresh now'}
                            </button>
                        </div>
                    </div>

                    {/* ── Layer switcher tabs ───────────────────────────── */}
                    <div className="mb-6 flex items-center rounded-2xl border border-slate-200 bg-slate-100 p-1 w-fit">
                        <LayerTab
                            id="tab-trading-signals"
                            label="Trading Signals"
                            active={activeLayer === 'trading'}
                            icon={<TrendingUp className="h-4 w-4" />}
                            onClick={() => setActiveLayer('trading')}
                        />
                        <LayerTab
                            id="tab-investment-recommendations"
                            label="Investment Recommendations"
                            active={activeLayer === 'recommendations'}
                            icon={<Sparkles className="h-4 w-4" />}
                            onClick={() => setActiveLayer('recommendations')}
                        />
                    </div>

                    {/* ── Loading skeleton ─────────────────────────────── */}
                    {loading && (
                        <div className="space-y-4 animate-pulse">
                            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                                {[1, 2, 3].map((i) => (
                                    <div key={i} className="h-48 rounded-2xl bg-white border border-slate-200" />
                                ))}
                            </div>
                            <div className="h-64 rounded-2xl bg-white border border-slate-200" />
                        </div>
                    )}

                    {/* ── Error state ──────────────────────────────────── */}
                    {!loading && error && (
                        <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-center">
                            <AlertTriangle className="mx-auto h-8 w-8 text-red-400 mb-2" />
                            <p className="font-semibold text-red-700">Could not load insights</p>
                            <p className="mt-1 text-sm text-red-500">{error}</p>
                            <button
                                onClick={() => void load()}
                                className="mt-4 rounded-lg bg-red-100 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-200 transition-colors"
                            >
                                Try again
                            </button>
                        </div>
                    )}

                    {/* ── Main content ─────────────────────────────────── */}
                    {!loading && !error && data && (
                        <AnimatePresence mode="wait">
                            {/* ═══════════════════════════════════════════════
                                LAYER A — TRADING SIGNALS
                            ═══════════════════════════════════════════════ */}
                            {activeLayer === 'trading' && (
                                <motion.div
                                    key="trading"
                                    initial={{ opacity: 0, y: 8 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -8 }}
                                    transition={{ duration: 0.2 }}
                                    className="space-y-6"
                                >
                                    {!layerAAvailable ? (
                                        <EmptyState
                                            title="No holdings found"
                                            body="Add equity, mutual fund, ETF, or crypto holdings under Input Data to see trading signals for your portfolio."
                                        />
                                    ) : (
                                        <>
                                            {/* Market Outlook */}
                                            <section className="rounded-2xl border border-slate-200 bg-slate-50 p-6">
                                                <div className="mb-4 flex flex-wrap items-center gap-3">
                                                    <h2 className="text-base font-bold text-slate-800">
                                                        Market outlook{' '}
                                                        <span className="font-normal text-slate-400">
                                                            (for your holdings)
                                                        </span>
                                                    </h2>
                                                    <span className="rounded-full bg-blue-50 border border-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-600">
                                                        AI-powered forecast
                                                    </span>
                                                </div>
                                                <p className="mb-5 text-sm text-slate-500">
                                                    30-day return forecast for your current asset classes
                                                </p>
                                                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                                                    {data.layer_a.asset_forecasts.map((f, i) => (
                                                        <ForecastCard key={f.asset_class} forecast={f} index={i} />
                                                    ))}
                                                </div>
                                                <p className="mt-4 flex items-center gap-1.5 text-xs text-slate-400">
                                                    <Info className="h-3.5 w-3.5" />
                                                    Forecasts are not guarantees. They represent model-based return
                                                    ranges with confidence levels.
                                                </p>
                                            </section>

                                            {/* Suggested Actions */}
                                            <section className="rounded-2xl border border-slate-200 bg-white p-6">
                                                <div className="mb-4 flex flex-wrap items-center gap-3">
                                                    <h2 className="text-base font-bold text-slate-800">
                                                        Suggested actions{' '}
                                                        <span className="font-normal text-slate-400">
                                                            (for your holdings)
                                                        </span>
                                                    </h2>
                                                    {data.gc_sec.arbiter.tax_flags_raised > 0 && (
                                                        <span className="rounded-full bg-amber-50 border border-amber-200 px-2.5 py-0.5 text-xs font-medium text-amber-600">
                                                            {data.gc_sec.arbiter.tax_flags_raised} tax flag
                                                            {data.gc_sec.arbiter.tax_flags_raised > 1 ? 's' : ''}
                                                        </span>
                                                    )}
                                                </div>
                                                <p className="mb-4 text-sm text-slate-500">Tax and risk reviewed</p>
                                                <div className="space-y-3">
                                                    {data.layer_a.rebalance_actions.map((a, i) => (
                                                        <ActionRow key={a.asset_class} action={a} index={i} />
                                                    ))}
                                                </div>
                                                <p className="mt-4 text-xs text-slate-400">
                                                    All actions are advisory only. No trades are executed.
                                                </p>
                                            </section>
                                        </>
                                    )}
                                </motion.div>
                            )}

                            {/* ═══════════════════════════════════════════════
                                LAYER B — INVESTMENT RECOMMENDATIONS
                            ═══════════════════════════════════════════════ */}
                            {activeLayer === 'recommendations' && (
                                <motion.div
                                    key="recommendations"
                                    initial={{ opacity: 0, y: 8 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -8 }}
                                    transition={{ duration: 0.2 }}
                                    className="space-y-6"
                                >
                                    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                                        {/* ── Goal Alignment ── (lg: col-span-2) */}
                                        <section className="rounded-2xl border border-slate-200 bg-slate-50 p-6 lg:col-span-2">
                                            <div className="mb-4 flex flex-wrap items-center gap-3">
                                                <h2 className="text-base font-bold text-slate-800">
                                                    Goal alignment
                                                </h2>
                                                <span className="rounded-full bg-indigo-50 border border-indigo-100 px-2.5 py-0.5 text-xs font-medium text-indigo-600">
                                                    Goal-driven
                                                </span>
                                            </div>
                                            <p className="mb-4 text-sm text-slate-500">Are you on track?</p>

                                            {!layerBAvailable ? (
                                                <EmptyState
                                                    title="No goals found"
                                                    body="Add financial goals under Input Data to see how your portfolio tracks toward them."
                                                />
                                            ) : (
                                                <div className="space-y-4">
                                                    {data.layer_b.goal_gaps.map((g, i) => (
                                                        <GoalCard key={g.goal_id ?? i} gap={g} index={i} />
                                                    ))}
                                                </div>
                                            )}
                                        </section>

                                        {/* ── Priority Action ── (lg: col-span-1) */}
                                        <section className="flex flex-col gap-6">
                                            {data.layer_b.priority_action && (
                                                <motion.div
                                                    initial={{ opacity: 0, scale: 0.97 }}
                                                    animate={{ opacity: 1, scale: 1 }}
                                                    className="rounded-2xl border border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50 p-6 shadow-sm"
                                                >
                                                    <div className="mb-3 flex items-center gap-2">
                                                        <Star className="h-5 w-5 text-amber-500 fill-amber-400" />
                                                        <h2 className="text-sm font-bold text-slate-800">
                                                            Priority action for you
                                                        </h2>
                                                    </div>
                                                    <p className="text-xs text-slate-500 mb-3">
                                                        Focus on the highest impact change
                                                    </p>
                                                    <div className="rounded-xl bg-white/80 border border-blue-100 p-4">
                                                        <p className="text-sm font-semibold text-blue-700">
                                                            {data.layer_b.priority_action.action}
                                                        </p>
                                                        <p className="mt-2 text-sm text-slate-600">
                                                            {data.layer_b.priority_action.description}
                                                        </p>
                                                        <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
                                                            <div>
                                                                <p className="text-slate-400">Impact</p>
                                                                <p className="font-semibold text-slate-700">
                                                                    {data.layer_b.priority_action.impact}
                                                                </p>
                                                            </div>
                                                            <div>
                                                                <p className="text-slate-400">Effort</p>
                                                                <p className="font-semibold text-slate-700">
                                                                    {data.layer_b.priority_action.effort}
                                                                </p>
                                                            </div>
                                                            <div>
                                                                <p className="text-slate-400">Horizon</p>
                                                                <p className="font-semibold text-slate-700">
                                                                    {data.layer_b.priority_action.time_horizon}
                                                                </p>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </motion.div>
                                            )}
                                        </section>
                                    </div>

                                    {/* ── New Instrument Suggestions ── */}
                                    {layerBAvailable && data.layer_b.instrument_suggestions.length > 0 && (
                                        <section className="rounded-2xl border border-slate-200 bg-white p-6">
                                            <div className="mb-4 flex flex-wrap items-center gap-3">
                                                <h2 className="text-base font-bold text-slate-800">
                                                    New instrument suggestions
                                                </h2>
                                                <span className="text-xs text-slate-400">
                                                    Consider adding for better diversification
                                                </span>
                                            </div>
                                            <div className="space-y-3">
                                                {data.layer_b.instrument_suggestions.map((s, i) => (
                                                    <SuggestionRow key={s.name} suggestion={s} index={i} />
                                                ))}
                                            </div>
                                        </section>
                                    )}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    )}

                    {/* ── GC-SEC footer accordion ─────────────────────── */}
                    {data && !loading && (
                        <motion.section
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.3 }}
                            className="mt-6 rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden"
                        >
                            <button
                                id="gc-sec-accordion-btn"
                                onClick={() => setGcOpen((v) => !v)}
                                className="flex w-full items-center justify-between px-6 py-4 text-left hover:bg-slate-50 transition-colors"
                            >
                                <div className="flex items-center gap-2.5">
                                    <ShieldCheck className="h-5 w-5 text-blue-500" />
                                    <div>
                                        <span className="text-sm font-semibold text-slate-700">
                                            Why these recommendations?
                                        </span>
                                        <p className="text-xs text-slate-400 mt-0.5">
                                            Our multi-model AI analyses market trends, your financial profile, tax
                                            impact, and goals — then verifies everything through our{' '}
                                            <span className="rounded bg-blue-100 px-1.5 py-0.5 font-mono text-xs text-blue-700">
                                                GC-SEC
                                            </span>{' '}
                                            check.
                                        </p>
                                    </div>
                                </div>
                                <ChevronDown
                                    className={`h-4 w-4 text-slate-400 transition-transform ${gcOpen ? 'rotate-180' : ''}`}
                                />
                            </button>

                            <AnimatePresence>
                                {gcOpen && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        transition={{ duration: 0.2 }}
                                        className="overflow-hidden border-t border-slate-100"
                                    >
                                        <div className="grid grid-cols-1 gap-4 px-6 py-5 sm:grid-cols-3">
                                            <div className="rounded-xl bg-slate-50 p-4">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                                                    <p className="text-xs font-semibold text-slate-700">Step 1 — Grounding</p>
                                                </div>
                                                <p className="text-xs text-slate-500">
                                                    {data.gc_sec.grounding.checks_performed} values verified against
                                                    Portfolio Analytics.{' '}
                                                    {data.gc_sec.grounding.corrections_applied} correction
                                                    {data.gc_sec.grounding.corrections_applied !== 1 ? 's' : ''} applied.
                                                </p>
                                            </div>
                                            <div className="rounded-xl bg-slate-50 p-4">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <ShieldCheck className="h-4 w-4 text-blue-500" />
                                                    <p className="text-xs font-semibold text-slate-700">Step 2 — Arbiter</p>
                                                </div>
                                                <p className="text-xs text-slate-500">
                                                    Risk profile:{' '}
                                                    <span className="font-medium text-slate-700">
                                                        {capitalise(data.gc_sec.arbiter.risk_profile_applied)}
                                                    </span>
                                                    .{' '}
                                                    {data.gc_sec.arbiter.tax_flags_raised > 0
                                                        ? `${data.gc_sec.arbiter.tax_flags_raised} tax constraint(s) flagged.`
                                                        : 'No tax constraints triggered.'}
                                                </p>
                                            </div>
                                            <div className="rounded-xl bg-slate-50 p-4">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <BookOpen className="h-4 w-4 text-purple-500" />
                                                    <p className="text-xs font-semibold text-slate-700">Step 3 — Calibration</p>
                                                </div>
                                                <p className="text-xs text-slate-500">
                                                    Outcome logging active. Calibration compares predictions against
                                                    realised results over time.
                                                </p>
                                            </div>
                                        </div>
                                        <div className="px-6 pb-4">
                                            <p className="rounded-lg bg-amber-50 border border-amber-100 px-4 py-2.5 text-xs text-amber-700">
                                                {data.gc_sec.disclaimer}
                                            </p>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </motion.section>
                    )}
                </main>
            </div>
        </PageTransition>
    );
}
