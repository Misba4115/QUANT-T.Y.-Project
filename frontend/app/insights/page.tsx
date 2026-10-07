'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import {
    AlertTriangle,
    ArrowRight,
    BarChart2,
    BookOpen,
    CheckCircle2,
    ChevronDown,
    ChevronRight,
    Database,
    Info,
    RefreshCw,
    ShieldCheck,
    Sparkles,
    TrendingDown,
    TrendingUp,
    X,
} from 'lucide-react';

import Navbar from '@/components/layout/navbar';
import PageTransition from '@/components/layout/page-transition';
import InvestmentDiscovery from '@/components/insights/investment-discovery';
import { insightsApi } from '@/lib/api';
import { formatCurrency } from '@/lib/helpers';
import { insightsChatContext, publishChatViewContext } from '@/lib/chat-view-context';
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

function formatAmount(n: number): string {
    if (n >= 1_00_00_000) return `₹${(n / 1_00_00_000).toFixed(2)} Cr`;
    if (n >= 1_00_000) return `₹${(n / 1_00_000).toFixed(2)} L`;
    return formatCurrency(n);
}

// ---------------------------------------------------------------------------
// Small reusable components
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Layer A sub-components (Trading Signals)
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
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-slate-400">{forecast.asset_class}</p>
                    <div className="mt-1.5 flex items-baseline gap-1.5">
                        {isUp ? <TrendingUp className="h-5 w-5 text-emerald-500" /> : isDown ? <TrendingDown className="h-5 w-5 text-red-400" /> : <BarChart2 className="h-5 w-5 text-slate-400" />}
                        <span className={`text-2xl font-bold tracking-tight ${isUp ? 'text-emerald-600' : isDown ? 'text-red-500' : 'text-slate-700'}`}>
                            {forecast.forecast_return_low > 0 ? '+' : ''}{forecast.forecast_return_low.toFixed(1)}% to{' '}
                            {forecast.forecast_return_high > 0 ? '+' : ''}{forecast.forecast_return_high.toFixed(1)}%
                        </span>
                    </div>
                </div>
                <ConfidencePill level={forecast.confidence} />
            </div>
            <div className="mt-4 h-12 rounded-lg overflow-hidden">
                <svg width="100%" height="100%" viewBox="0 0 200 48" preserveAspectRatio="none">
                    <defs>
                        <linearGradient id={`grad-${forecast.asset_class}`} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor={isUp ? '#10b981' : isDown ? '#f87171' : '#94a3b8'} stopOpacity="0.2" />
                            <stop offset="100%" stopColor={isUp ? '#10b981' : isDown ? '#f87171' : '#94a3b8'} stopOpacity="0" />
                        </linearGradient>
                    </defs>
                    <path
                        d={isUp ? 'M0,40 C40,38 80,28 120,20 C160,12 180,8 200,4' : isDown ? 'M0,8 C40,10 80,20 120,28 C160,36 180,40 200,44' : 'M0,24 C40,22 80,26 120,23 C160,20 180,25 200,24'}
                        fill={`url(#grad-${forecast.asset_class})`}
                        stroke={isUp ? '#10b981' : isDown ? '#f87171' : '#94a3b8'}
                        strokeWidth="2"
                        fillOpacity="1"
                    />
                </svg>
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
                <span>30-day horizon</span>
                <span className="flex items-center gap-1"><Info className="h-3 w-3" />Model: {forecast.model.split('-').slice(0, 2).join('-')}</span>
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
            className={`rounded-xl border p-4 ${action.tax_flag ? 'border-amber-200 bg-amber-50/40' : 'border-slate-100 bg-white'}`}
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
// Layer B sub-components (Recommendations)
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Per-Goal Recommendation Panel — unified recommendation journey
// ---------------------------------------------------------------------------

function GoalRecommendationPanel({
    gap,
    suggestion,
    priorityAction,
}: {
    gap: GoalGap;
    suggestion?: InstrumentSuggestion;
    priorityAction?: InsightsResult['layer_b']['priority_action'];
}) {
    const [investAmount, setInvestAmount] = useState(gap.required_monthly_sip > 0 ? gap.required_monthly_sip : 5000);

    const [calculatedAt] = useState(() => Date.now());
    const maxSlider = Math.max(gap.required_monthly_sip * 3, 50000);
    const monthsRemaining = gap.target_date
        ? Math.max(1, Math.round((new Date(gap.target_date).getTime() - calculatedAt) / (1000 * 60 * 60 * 24 * 30)))
        : 60;
    const estimatedReturn = 0.12;
    const monthlyRate = estimatedReturn / 12;
    const futureValue = investAmount * ((Math.pow(1 + monthlyRate, monthsRemaining) - 1) / monthlyRate) * (1 + monthlyRate);
    const projectedTotal = gap.current_amount + futureValue;
    const projectedProgress = gap.target_amount > 0 ? Math.min(100, (projectedTotal / gap.target_amount) * 100) : 100;
    const currentProgress = gap.target_amount > 0 ? Math.min(100, (gap.current_amount / gap.target_amount) * 100) : 0;

    return (
        <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden">

            {/* ── Compact goal header ─────────────────────────────────── */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
                <div className="flex items-center gap-3">
                    <div className={`h-2 w-2 rounded-full flex-shrink-0 ${gap.on_track ? 'bg-emerald-500' : 'bg-amber-400'}`} />
                    <div>
                        <p className="font-semibold text-slate-900 leading-tight">{gap.goal_name}</p>
                        <p className="text-xs text-slate-400 mt-0.5 capitalize">{gap.horizon}-term · Target {formatCurrency(gap.target_amount)}</p>
                    </div>
                </div>
                <span className={`text-xs font-semibold ${gap.on_track ? 'text-emerald-600' : 'text-amber-600'}`}>
                    {gap.on_track ? 'On track' : `${gap.shortfall_pct.toFixed(0)}% short`}
                </span>
            </div>

            {/* ── Three-stage flow ────────────────────────────────────── */}
            {/* Each column is a flex-col with 4 fixed zones so elements align row-for-row across columns:
                Zone A — section label (fixed height)
                Zone B — supporting details (flex-grow, fills space)
                Zone C — major value (fixed height, the "hero" number/action per column)
                Zone D — progress/slider bar (fixed height, always at bottom)
            */}
            <div className="grid grid-cols-1 lg:grid-cols-3 divide-y-2 lg:divide-y-0 lg:divide-x-2 divide-slate-200">

                {/* STAGE 1 — Where you are */}
                <div className="flex flex-col px-6 py-6 min-h-[320px]">
                    {/* Zone A — label */}
                    <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-400 mb-5">Where you are</p>

                    {/* Zone B — supporting detail rows */}
                    <div className="flex-1 space-y-3">
                        <div className="flex items-baseline justify-between">
                            <span className="text-sm text-slate-500">Target</span>
                            <span className="text-sm font-semibold text-slate-900">{formatCurrency(gap.target_amount)}</span>
                        </div>
                        <div className="flex items-baseline justify-between">
                            <span className="text-sm text-slate-500">Saved so far</span>
                            <span className="text-sm font-semibold text-emerald-700">{formatCurrency(gap.current_amount)}</span>
                        </div>
                        <div className="flex items-baseline justify-between">
                            <span className="text-sm text-slate-500">Remaining</span>
                            <span className="text-sm font-semibold text-slate-700">{formatCurrency(Math.max(0, gap.gap))}</span>
                        </div>
                        {gap.target_date && (
                            <div className="flex items-baseline justify-between">
                                <span className="text-sm text-slate-500">Target date</span>
                                <span className="text-sm font-semibold text-slate-700">{gap.target_date}</span>
                            </div>
                        )}
                    </div>

                    {/* Zone C — major value: suggested SIP */}
                    <div className="pt-5 mt-5 border-t border-slate-100 h-[68px] flex flex-col justify-center">
                        {!gap.on_track && gap.required_monthly_sip > 0 ? (
                            <>
                                <p className="text-xs text-slate-400 mb-1">Suggested monthly SIP</p>
                                <p className="text-xl font-bold text-slate-900">{formatCurrency(gap.required_monthly_sip)}<span className="text-sm font-normal text-slate-400 ml-1">/mo</span></p>
                            </>
                        ) : (
                            <p className="text-sm font-semibold text-emerald-700 flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-emerald-500 inline-block" />On track — keep it up</p>
                        )}
                    </div>

                    {/* Zone D — progress bar */}
                    <div className="mt-5">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-slate-400">Progress</span>
                            <span className="text-xs font-semibold text-slate-600">{currentProgress.toFixed(0)}%</span>
                        </div>
                        <div className="h-1.5 w-full rounded-full bg-slate-100">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${currentProgress}%` }}
                                transition={{ duration: 0.8, ease: 'easeOut' }}
                                className={`h-full rounded-full ${gap.on_track ? 'bg-emerald-500' : 'bg-amber-400'}`}
                            />
                        </div>
                    </div>
                </div>

                {/* STAGE 2 — What to do */}
                <div className="flex flex-col px-6 py-6 min-h-[320px]">
                    {/* Zone A — label */}
                    <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-400 mb-5">What to do</p>

                    {/* Zone B — supporting detail: instrument */}
                    <div className="flex-1">
                        {suggestion && (
                            <div className="space-y-1">
                                <p className="text-xs text-slate-400">Recommended instrument</p>
                                <div className="flex items-start justify-between gap-3 mt-1">
                                    <div>
                                        <p className="text-sm font-semibold text-slate-900">{suggestion.name}</p>
                                        <p className="mt-0.5 text-xs text-slate-500 leading-relaxed">{suggestion.rationale}</p>
                                    </div>
                                    <span className={`flex-shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold border mt-0.5
                                        ${suggestion.risk_level === 'Low' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : suggestion.risk_level === 'High' ? 'bg-red-50 text-red-700 border-red-200' : 'bg-amber-50 text-amber-700 border-amber-200'}`}>
                                        {suggestion.risk_level} risk
                                    </span>
                                </div>
                                {priorityAction && (
                                    <p className="mt-3 text-xs text-slate-500 leading-relaxed">{priorityAction.description}</p>
                                )}
                            </div>
                        )}
                        {!suggestion && priorityAction && (
                            <p className="text-xs text-slate-500 leading-relaxed">{priorityAction.description}</p>
                        )}
                    </div>

                    {/* Zone C — major value: the action headline */}
                    <div className="pt-5 mt-5 border-t border-slate-100 h-[68px] flex flex-col justify-center">
                        {priorityAction ? (
                            <>
                                <p className="text-xs text-slate-400 mb-1">Priority action</p>
                                <p className="text-base font-bold text-slate-900 leading-snug truncate" title={priorityAction.action}>{priorityAction.action}</p>
                            </>
                        ) : (
                            <p className="text-sm text-slate-400">Continue your current investment plan.</p>
                        )}
                    </div>

                    {/* Zone D — slider (replaces progress bar, same height zone) */}
                    <div className="mt-5">
                        <div className="flex items-baseline justify-between mb-2">
                            <span className="text-xs text-slate-400">Monthly investment</span>
                            <span className="text-xs font-semibold text-emerald-700">{formatAmount(investAmount)}</span>
                        </div>
                        <input
                            type="range"
                            min={500}
                            max={maxSlider}
                            step={500}
                            value={investAmount}
                            onChange={e => setInvestAmount(Number(e.target.value))}
                            className="w-full h-1.5 rounded-full accent-emerald-600 cursor-pointer"
                        />
                        <div className="flex justify-between mt-1.5 text-[10px] text-slate-300">
                            <span>₹500</span>
                            <span>{formatAmount(maxSlider)}</span>
                        </div>
                    </div>
                </div>

                {/* STAGE 3 — What to expect */}
                <div className="flex flex-col px-6 py-6 bg-slate-50/40 min-h-[320px]">
                    {/* Zone A — label */}
                    <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-400 mb-5">What to expect</p>

                    {/* Zone B — supporting detail: breakdown */}
                    <div className="flex-1 space-y-3">
                        <div className="flex items-baseline justify-between">
                            <span className="text-sm text-slate-500">Current savings</span>
                            <span className="text-sm font-semibold text-slate-700">{formatCurrency(gap.current_amount)}</span>
                        </div>
                        <div className="flex items-baseline justify-between">
                            <span className="text-sm text-slate-500">SIP growth</span>
                            <span className="text-sm font-semibold text-emerald-700">+ {formatAmount(futureValue)}</span>
                        </div>
                        <div className="flex items-baseline justify-between">
                            <span className="text-sm text-slate-500">Goal target</span>
                            <span className="text-sm font-semibold text-slate-700">{formatCurrency(gap.target_amount)}</span>
                        </div>
                        <div className="flex items-baseline justify-between">
                            <span className="text-sm text-slate-500">Period</span>
                            <span className="text-sm font-semibold text-slate-700">{monthsRemaining} months</span>
                        </div>
                    </div>

                    {/* Zone C — major value: projected total */}
                    <div className="pt-5 mt-5 border-t border-slate-100 h-[68px] flex flex-col justify-center">
                        <p className="text-xs text-slate-400 mb-1">Projected value</p>
                        <motion.p
                            key={investAmount}
                            initial={{ opacity: 0.6, y: 3 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.2 }}
                            className="text-xl font-bold text-slate-900 tracking-tight"
                        >
                            {formatAmount(projectedTotal)}
                        </motion.p>
                    </div>

                    {/* Zone D — projected progress bar (same zone as col-1 progress bar) */}
                    <div className="mt-5">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-slate-400">Projected progress</span>
                            <span className="text-xs font-semibold text-slate-600">{projectedProgress.toFixed(0)}%</span>
                        </div>
                        <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden relative">
                            <div className="absolute left-0 top-0 h-full rounded-full bg-emerald-200" style={{ width: `${Math.min(100, projectedProgress)}%` }} />
                            <div className="absolute left-0 top-0 h-full rounded-full bg-emerald-600" style={{ width: `${currentProgress}%` }} />
                        </div>
                        <div className="mt-2 flex items-center gap-3 text-[10px] text-slate-400">
                            <span className="flex items-center gap-1"><span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-600" />Now</span>
                            <span className="flex items-center gap-1"><span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-200" />Projected</span>
                            <span className="ml-auto text-[9px] text-slate-300">12% p.a. est.</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}


// ---------------------------------------------------------------------------
// Final Review Modal
// ---------------------------------------------------------------------------

function FinalReviewModal({
    data,
    onClose,
}: {
    data: InsightsResult;
    onClose: () => void;
}) {
    const [confirmed, setConfirmed] = useState(false);
    const layerBAvailable = data.layer_b.status === 'available';
    const layerAAvailable = data.layer_a.status === 'available';

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
            <motion.div
                initial={{ opacity: 0, scale: 0.96, y: 10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.96, y: 10 }}
                transition={{ duration: 0.2 }}
                className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-slate-200 bg-white shadow-2xl"
            >
                {!confirmed ? (
                    <>
                        {/* Header */}
                        <div className="sticky top-0 flex items-center justify-between border-b border-slate-100 bg-white px-6 py-4 z-10">
                            <div>
                                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Final Review</p>
                                <h2 className="mt-0.5 text-lg font-bold text-slate-900">Is everything correct?</h2>
                            </div>
                            <button onClick={onClose} className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100"><X className="h-5 w-5" /></button>
                        </div>

                        {/* Summary sections */}
                        <div className="divide-y divide-slate-100 px-6 py-2">

                            {/* Financial data */}
                            <div className="py-4">
                                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Financial Data</p>
                                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                                    {[
                                        { label: 'Data generated', value: timeAgo(data.generated_at) },
                                        { label: 'Layer A', value: layerAAvailable ? 'Available' : 'No holdings' },
                                        { label: 'Layer B', value: layerBAvailable ? 'Available' : 'No goals' },
                                    ].map(s => (
                                        <div key={s.label} className="rounded-xl bg-slate-50 p-3">
                                            <p className="text-xs text-slate-400">{s.label}</p>
                                            <p className="mt-0.5 text-sm font-semibold text-slate-800">{s.value}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Goals */}
                            {layerBAvailable && data.layer_b.goal_gaps.length > 0 && (
                                <div className="py-4">
                                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Goals</p>
                                    <div className="space-y-2">
                                        {data.layer_b.goal_gaps.map(g => (
                                            <div key={g.goal_id ?? g.goal_name} className="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3">
                                                <div>
                                                    <p className="text-sm font-medium text-slate-800">{g.goal_name}</p>
                                                    <p className="text-xs text-slate-500">{formatCurrency(g.current_amount)} of {formatCurrency(g.target_amount)}</p>
                                                </div>
                                                <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${g.on_track ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}>
                                                    {g.on_track ? 'On track' : 'Needs attention'}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Recommendations */}
                            {layerBAvailable && data.layer_b.priority_action && (
                                <div className="py-4">
                                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Investment Recommendation</p>
                                    <div className="rounded-xl border border-blue-100 bg-blue-50 p-4">
                                        <p className="text-sm font-semibold text-blue-800">{data.layer_b.priority_action.action}</p>
                                        <p className="mt-1 text-xs text-slate-600">{data.layer_b.priority_action.description}</p>
                                        <div className="mt-2 flex gap-3 text-xs">
                                            <span className="text-slate-500">Impact: <strong>{data.layer_b.priority_action.impact}</strong></span>
                                            <span className="text-slate-500">Effort: <strong>{data.layer_b.priority_action.effort}</strong></span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Trading */}
                            {layerAAvailable && (
                                <div className="py-4">
                                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Trading Insights</p>
                                    <div className="space-y-2">
                                        {data.layer_a.rebalance_actions.slice(0, 3).map(a => (
                                            <div key={a.asset_class} className="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3">
                                                <p className="text-sm font-medium text-slate-800">{a.asset_class}</p>
                                                <SignalBadge signal={a.signal} />
                                            </div>
                                        ))}
                                    </div>
                                    <p className="mt-2 text-xs text-slate-400">All signals are advisory only. No trades are executed.</p>
                                </div>
                            )}
                        </div>

                        {/* Footer actions */}
                        <div className="sticky bottom-0 border-t border-slate-100 bg-white px-6 py-4">
                            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                                <p className="text-xs text-slate-400">Confirmation does not execute any trades or transactions.</p>
                                <div className="flex gap-3">
                                    <button
                                        onClick={onClose}
                                        className="flex-1 rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 sm:flex-none"
                                    >
                                        Go Back &amp; Edit
                                    </button>
                                    <button
                                        onClick={() => setConfirmed(true)}
                                        className="flex-1 rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-500 sm:flex-none"
                                    >
                                        Confirm &amp; Proceed
                                    </button>
                                </div>
                            </div>
                        </div>
                    </>
                ) : (
                    /* Success state */
                    <motion.div
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex flex-col items-center justify-center py-16 px-8 text-center"
                    >
                        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100">
                            <CheckCircle2 className="h-8 w-8 text-emerald-600" />
                        </div>
                        <h2 className="mt-5 text-xl font-bold text-slate-900">Plan confirmed!</h2>
                        <p className="mt-2 text-sm text-slate-500 max-w-sm">
                            Your investment plan has been noted. No trades have been executed. You can revisit and adjust at any time.
                        </p>
                        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                            <button
                                onClick={onClose}
                                className="rounded-xl border border-slate-200 bg-white px-6 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                            >
                                Stay here
                            </button>
                            <Link
                                href="/dashboard"
                                className="flex items-center gap-2 rounded-xl bg-stone-900 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-700"
                            >
                                Go to Dashboard <ArrowRight className="h-4 w-4" />
                            </Link>
                        </div>
                    </motion.div>
                )}
            </motion.div>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Empty states
// ---------------------------------------------------------------------------

function NoDataState() {
    return (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 py-20 text-center px-8">
            <Database className="h-12 w-12 text-slate-300 mb-4" />
            <p className="font-semibold text-slate-700 text-lg">No financial data uploaded yet</p>
            <p className="mt-2 text-sm text-slate-400 max-w-sm">
                Upload your current holdings to generate personalized insights and recommendations.
            </p>
            <Link
                href="/input-data"
                className="mt-6 flex items-center gap-2 rounded-xl bg-stone-900 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-700"
            >
                Upload your current holdings <ArrowRight className="h-4 w-4" />
            </Link>
        </div>
    );
}

function EmptyState({ title, body }: { title: string; body: string }) {
    return (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 py-16 text-center px-8">
            <BarChart2 className="h-10 w-10 text-slate-300 mb-3" />
            <p className="font-semibold text-slate-600">{title}</p>
            <p className="mt-1.5 text-sm text-slate-400 max-w-xs">{body}</p>
            <Link
                href="/input-data"
                className="mt-4 flex items-center gap-1.5 text-sm font-medium text-emerald-700 hover:underline"
            >
                Go to Input Data <ChevronRight className="h-4 w-4" />
            </Link>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function InsightsPage() {
    const [data, setData] = useState<InsightsResult | null>(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [gcOpen, setGcOpen] = useState(false);
    const [showFinalReview, setShowFinalReview] = useState(false);

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

    useEffect(() => {
        if (data) publishChatViewContext(insightsChatContext(data));
    }, [data]);

    const layerAAvailable = data?.layer_a.status === 'available';
    const layerBAvailable = data?.layer_b.status === 'available';
    const hasAnyData = layerAAvailable || layerBAvailable;

    return (
        <PageTransition>
            <div className="min-h-screen bg-slate-50">
                <Navbar />

                {showFinalReview && data && (
                    <AnimatePresence>
                        <FinalReviewModal data={data} onClose={() => setShowFinalReview(false)} />
                    </AnimatePresence>
                )}

                <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">

                    {/* ── Page header ──────────────────────────────────────── */}
                    <div className="mb-6">
                        <p className="text-sm font-medium text-emerald-700">Insights &amp; Trading</p>
                        <div className="mt-1 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                            <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
                                Personalized guidance,{' '}
                                <span className="bg-gradient-to-r from-emerald-800 to-emerald-600 bg-clip-text text-transparent">
                                    grounded in evidence
                                </span>
                            </h1>
                            <div className="flex flex-shrink-0 gap-2">
                                <button
                                    id="insights-refresh-btn"
                                    onClick={() => void load(true)}
                                    disabled={refreshing || loading}
                                    className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:opacity-50"
                                >
                                    <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                                    {refreshing ? 'Refreshing…' : 'Refresh now'}
                                </button>
                            </div>
                        </div>
                        <p className="mt-1.5 text-sm text-slate-500">
                            Goal-aligned investment recommendations, then market trading signals.
                        </p>
                    </div>

                    <InvestmentDiscovery>
                        {!loading && !error && data && hasAnyData && (
                            <section>
                                <div className="mb-4 flex flex-wrap items-center gap-3">
                                    <Sparkles className="h-5 w-5 text-emerald-600" />
                                    <h2 className="text-lg font-bold text-slate-900">Goal planning</h2>
                                    <span className="rounded-full bg-indigo-50 border border-indigo-100 px-2.5 py-0.5 text-xs font-medium text-indigo-600">
                                        Goal-driven
                                    </span>
                                </div>

                                {!layerBAvailable ? (
                                    <EmptyState
                                        title="No goals found"
                                        body="Add financial goals under Input Data to see how your portfolio tracks toward them."
                                    />
                                ) : (
                                    <div className="space-y-6">
                                        {data.layer_b.goal_gaps.map((gap, i) => (
                                            <GoalRecommendationPanel
                                                key={gap.goal_id ?? i}
                                                gap={gap}
                                                suggestion={data.layer_b.instrument_suggestions.find(s => s.driven_by_goal === gap.goal_name) ?? data.layer_b.instrument_suggestions[i]}
                                                priorityAction={data.layer_b.priority_action}
                                            />
                                        ))}
                                    </div>
                                )}
                            </section>
                        )}
                    </InvestmentDiscovery>

                    {/* ── Loading skeleton ─────────────────────────────── */}
                    {loading && (
                        <div className="space-y-4 animate-pulse">
                            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                                {[1, 2, 3].map(i => <div key={i} className="h-48 rounded-2xl bg-white border border-slate-200" />)}
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

                    {/* ── No data at all ───────────────────────────────── */}
                    {!loading && !error && data && !hasAnyData && <NoDataState />}

                    {/* ── Main content ─────────────────────────────────── */}
                    {!loading && !error && data && hasAnyData && (
                        <div className="space-y-10">

                            {/* ═══════════════════════════════════════════════
                                SECTION 2 — TRADING SIGNALS
                            ═══════════════════════════════════════════════ */}
                            <section>
                                <div className="mb-4 flex flex-wrap items-center gap-3">
                                    <TrendingUp className="h-5 w-5 text-slate-700" />
                                    <h2 className="text-lg font-bold text-slate-900">Trading Insights</h2>
                                    <span className="rounded-full bg-slate-100 border border-slate-200 px-2.5 py-0.5 text-xs font-medium text-slate-600">
                                        Market signals
                                    </span>
                                </div>

                                {!layerAAvailable ? (
                                    <EmptyState
                                        title="No holdings found"
                                        body="Add equity, mutual fund, ETF, or crypto holdings under Input Data to see trading signals."
                                    />
                                ) : (
                                    <div className="space-y-6">
                                        {/* Market Outlook */}
                                        <section className="rounded-2xl border border-slate-200 bg-slate-50 p-6">
                                            <div className="mb-4 flex flex-wrap items-center gap-3">
                                                <h3 className="text-base font-bold text-slate-800">
                                                    Market outlook{' '}
                                                    <span className="font-normal text-slate-400">(for your holdings)</span>
                                                </h3>
                                                <span className="rounded-full bg-emerald-50 border border-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-700">
                                                    AI-powered forecast
                                                </span>
                                            </div>
                                            <p className="mb-5 text-sm text-slate-500">30-day return forecast for your current asset classes</p>
                                            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                                                {data.layer_a.asset_forecasts.map((f, i) => (
                                                    <ForecastCard key={f.asset_class} forecast={f} index={i} />
                                                ))}
                                            </div>
                                            <p className="mt-4 flex items-center gap-1.5 text-xs text-slate-400">
                                                <Info className="h-3.5 w-3.5" />
                                                Forecasts are not guarantees. They represent model-based return ranges with confidence levels.
                                            </p>
                                        </section>

                                        {/* Suggested Actions */}
                                        <section className="rounded-2xl border border-slate-200 bg-white p-6">
                                            <div className="mb-4 flex flex-wrap items-center gap-3">
                                                <h3 className="text-base font-bold text-slate-800">
                                                    Suggested actions{' '}
                                                    <span className="font-normal text-slate-400">(for your holdings)</span>
                                                </h3>
                                                {data.gc_sec.arbiter.tax_flags_raised > 0 && (
                                                    <span className="rounded-full bg-amber-50 border border-amber-200 px-2.5 py-0.5 text-xs font-medium text-amber-600">
                                                        {data.gc_sec.arbiter.tax_flags_raised} tax flag{data.gc_sec.arbiter.tax_flags_raised > 1 ? 's' : ''}
                                                    </span>
                                                )}
                                            </div>
                                            <p className="mb-4 text-sm text-slate-500">Tax and risk reviewed</p>
                                            <div className="space-y-3">
                                                {data.layer_a.rebalance_actions.map((a, i) => (
                                                    <ActionRow key={a.asset_class} action={a} index={i} />
                                                ))}
                                            </div>
                                            <p className="mt-4 text-xs text-slate-400">All actions are advisory only. No trades are executed.</p>
                                        </section>
                                    </div>
                                )}
                            </section>

                            {/* ── GC-SEC footer accordion ─────────────────────── */}
                            <motion.section
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 0.3 }}
                                className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden"
                            >
                                <button
                                    id="gc-sec-accordion-btn"
                                    onClick={() => setGcOpen(v => !v)}
                                    className="flex w-full items-center justify-between px-6 py-4 text-left hover:bg-slate-50 transition-colors"
                                >
                                    <div className="flex items-center gap-2.5">
                                        <ShieldCheck className="h-5 w-5 text-blue-500" />
                                        <div>
                                            <span className="text-sm font-semibold text-slate-700">Why these recommendations?</span>
                                            <p className="text-xs text-slate-400 mt-0.5">
                                                Our multi-model AI analyses market trends, your financial profile, tax impact, and goals — then verifies everything through our{' '}
                                                <span className="rounded bg-blue-100 px-1.5 py-0.5 font-mono text-xs text-blue-700">GC-SEC</span>{' '}check.
                                            </p>
                                        </div>
                                    </div>
                                    <ChevronDown className={`h-4 w-4 text-slate-400 transition-transform ${gcOpen ? 'rotate-180' : ''}`} />
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
                                                        {data.gc_sec.grounding.checks_performed} values verified against Portfolio Analytics.{' '}
                                                        {data.gc_sec.grounding.corrections_applied} correction{data.gc_sec.grounding.corrections_applied !== 1 ? 's' : ''} applied.
                                                    </p>
                                                </div>
                                                <div className="rounded-xl bg-slate-50 p-4">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <ShieldCheck className="h-4 w-4 text-blue-500" />
                                                        <p className="text-xs font-semibold text-slate-700">Step 2 — Arbiter</p>
                                                    </div>
                                                    <p className="text-xs text-slate-500">
                                                        Risk profile: <span className="font-medium text-slate-700">{capitalise(data.gc_sec.arbiter.risk_profile_applied)}</span>.{' '}
                                                        {data.gc_sec.arbiter.tax_flags_raised > 0 ? `${data.gc_sec.arbiter.tax_flags_raised} tax constraint(s) flagged.` : 'No tax constraints triggered.'}
                                                    </p>
                                                </div>
                                                <div className="rounded-xl bg-slate-50 p-4">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <BookOpen className="h-4 w-4 text-purple-500" />
                                                        <p className="text-xs font-semibold text-slate-700">Step 3 — Calibration</p>
                                                    </div>
                                                    <p className="text-xs text-slate-500">
                                                        Outcome logging active. Calibration compares predictions against realised results over time.
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
                        </div>
                    )}
                </main>
            </div>
        </PageTransition>
    );
}
