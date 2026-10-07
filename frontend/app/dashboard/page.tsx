'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { AlertTriangle, ArrowRight, BarChart3, ChevronRight, Clock3, Database, Download, IndianRupee, MessageCircle, RefreshCw, ShieldCheck, TrendingUp, X } from 'lucide-react';
import { Area, AreaChart, Cell, CartesianGrid, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import Navbar from '@/components/layout/navbar';
import PageTransition from '@/components/layout/page-transition';
import { Button } from '@/components/ui/button';
import { SkeletonCard, SkeletonChart, SkeletonTable } from '@/components/ui/skeletons';
import { InfoTooltip } from '@/components/ui/tooltip';
import { dashboardApi, marketDataApi } from '@/lib/api';
import { formatChartValue, formatCurrency } from '@/lib/helpers';
import { dashboardChatContext, publishChatViewContext } from '@/lib/chat-view-context';
import type { DashboardData } from '@/types';

function StatusPill({ children, tone = 'neutral' }: { children: React.ReactNode; tone?: 'good' | 'warn' | 'neutral' }) {
    const tones = {
        good: 'border-emerald-200 bg-emerald-50 text-emerald-700',
        warn: 'border-amber-200 bg-amber-50 text-amber-700',
        neutral: 'border-stone-200 bg-stone-50 text-stone-600',
    };
    return <span className={`rounded-full border px-2.5 py-1 text-xs font-medium ${tones[tone]}`}>{children}</span>;
}

function MetricCard({ label, value, icon, detail, tooltip }: { label: string; value: string; icon: React.ReactNode; detail: React.ReactNode; tooltip: string }) {
    return (
        <section className="rounded-2xl border border-stone-200 bg-white p-5 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)]">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                    <p className="text-sm font-medium text-stone-500">{label}</p>
                    <InfoTooltip content={tooltip} />
                </div>
                <span className="rounded-xl bg-stone-100 p-2 text-stone-700">{icon}</span>
            </div>
            <p className="mt-3 text-2xl font-semibold tracking-tight text-stone-950">{value}</p>
            <div className="mt-2 min-h-6 text-sm text-stone-500">{detail}</div>
        </section>
    );
}

export default function DashboardPage() {
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [syncing, setSyncing] = useState(false);
    const [exporting, setExporting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [timePeriod, setTimePeriod] = useState('1y');
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');
    const [chartType, setChartType] = useState<'line' | 'area'>('line');
    const [showPortfolioStatus, setShowPortfolioStatus] = useState(true);

    const loadDashboard = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await dashboardApi.generateDashboard(
                undefined,
                timePeriod,
                timePeriod === 'custom' ? dateFrom : undefined,
                timePeriod === 'custom' ? dateTo : undefined,
            );
            if (!response.data.result) throw new Error(response.data.error || 'Dashboard result was empty');
            setData(response.data.result);
        } catch (caught) {
            setData(null);
            setError(caught instanceof Error ? caught.message : 'Dashboard could not be loaded');
        } finally {
            setLoading(false);
        }
    }, [dateFrom, dateTo, timePeriod]);

    useEffect(() => { void loadDashboard(); }, [loadDashboard]);

    useEffect(() => {
        if (data) publishChatViewContext(dashboardChatContext(data, timePeriod));
    }, [data, timePeriod]);

    useEffect(() => {
        void dashboardApi.getConfig().then((response) => {
            const config = response.data as { time_period?: string; custom_date_from?: string; custom_date_to?: string; chart_preferences?: { portfolio_history?: 'line' | 'area' } };
            if (config.time_period) setTimePeriod(config.time_period);
            if (config.custom_date_from) setDateFrom(config.custom_date_from);
            if (config.custom_date_to) setDateTo(config.custom_date_to);
            if (config.chart_preferences?.portfolio_history) setChartType(config.chart_preferences.portfolio_history);
        }).catch(() => undefined);
    }, []);

    const refreshPrices = async () => {
        setSyncing(true);
        setError(null);
        try {
            await marketDataApi.sync();
            await loadDashboard();
        } catch (caught) {
            setError(caught instanceof Error ? caught.message : 'Price refresh failed');
        } finally {
            setSyncing(false);
        }
    };

    const saveView = async () => {
        setError(null);
        try {
            await dashboardApi.saveConfig({
                widgets: ['net_worth', 'asset_allocation', 'portfolio_performance', 'cashflow', 'tax_tracker', 'top_holdings', 'alerts'],
                time_period: timePeriod,
                chart_preferences: { portfolio_history: chartType, asset_allocation: 'donut' },
                custom_date_from: timePeriod === 'custom' ? dateFrom : undefined,
                custom_date_to: timePeriod === 'custom' ? dateTo : undefined,
                currency: 'INR',
            });
            await loadDashboard();
        } catch (caught) { setError(caught instanceof Error ? caught.message : 'Dashboard view could not be saved'); }
    };

    const exportView = async (format: 'pdf' | 'png') => {
        setExporting(true); setError(null);
        try {
            const requested = await dashboardApi.requestExport(format, timePeriod, timePeriod === 'custom' ? dateFrom : undefined, timePeriod === 'custom' ? dateTo : undefined);
            const downloaded = await dashboardApi.downloadExport(requested.data.report_export_id, requested.data.download_token);
            const url = URL.createObjectURL(downloaded.data);
            const anchor = document.createElement('a'); anchor.href = url; anchor.download = `quant-${format === 'pdf' ? 'dashboard.pdf' : 'portfolio-history.png'}`; anchor.click();
            URL.revokeObjectURL(url);
        } catch (caught) { setError(caught instanceof Error ? caught.message : 'Export failed'); } finally { setExporting(false); }
    };

    const askAssistantAboutCurrentData = () => {
        window.dispatchEvent(new CustomEvent('open-chatbot', {
            detail: {
                prompt: 'Explain what my dashboard can already tell me from my existing financial data. Clearly separate measured facts from unavailable history, and suggest useful next steps without guessing.',
            },
        }));
    };

    if (loading) {
        return (
            <><Navbar /><main className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{[0, 1, 2, 3].map((item) => <SkeletonCard key={item} />)}</div>
                <div className="grid gap-6 lg:grid-cols-[2fr_1fr]"><SkeletonChart /><SkeletonChart /></div>
                <SkeletonTable />
            </main></>
        );
    }

    if (!data) {
        return (
            <><Navbar /><main className="mx-auto max-w-3xl px-4 py-20 text-center">
                <div className="rounded-2xl border border-rose-200 bg-white p-10 shadow-sm">
                    <AlertTriangle className="mx-auto h-10 w-10 text-rose-500" />
                    <h1 className="mt-4 text-xl font-semibold text-stone-950">Dashboard unavailable</h1>
                    <p className="mt-2 text-sm text-stone-600">{error || 'The backend did not return a financial result.'}</p>
                    <Button className="mt-6" onClick={() => void loadDashboard()}><RefreshCw className="mr-2 h-4 w-4" />Retry</Button>
                </div>
            </main></>
        );
    }

    const valuationTone = data.valuation_status === 'market_valued' ? 'good' : 'warn';
    const asOf = new Date(data.data_as_of).toLocaleString();
    const hasUnavailableInsights = data.net_worth_growth === null && (data.portfolio_history?.length || 0) < 2;

    const displayRiskLevel = data.risk_level && data.risk_level !== 'Unavailable'
        ? data.risk_level
        : data.stated_risk_profile
            ? `${data.stated_risk_profile.charAt(0).toUpperCase() + data.stated_risk_profile.slice(1)} (Stated)`
            : 'Moderate';

    const riskDetail = data.risk_level && data.risk_level !== 'Unavailable'
        ? (data.measured_portfolio_risk?.volatility !== null && data.measured_portfolio_risk?.volatility !== undefined
            ? `Historical σ: ${(data.measured_portfolio_risk.volatility * 100).toFixed(1)}% · stated: ${data.stated_risk_profile ? data.stated_risk_profile.charAt(0).toUpperCase() + data.stated_risk_profile.slice(1) : 'Moderate'}`
            : `Measured from history · stated: ${data.stated_risk_profile || 'not set'}`)
        : (data.measured_portfolio_risk?.sample_count && data.measured_portfolio_risk.sample_count > 0
            ? `Preliminary (${data.measured_portfolio_risk.sample_count} snapshot${data.measured_portfolio_risk.sample_count > 1 ? 's' : ''}) · stated: ${data.stated_risk_profile ? data.stated_risk_profile.charAt(0).toUpperCase() + data.stated_risk_profile.slice(1) : 'Moderate'}`
            : `Profile estimate · stated: ${data.stated_risk_profile ? data.stated_risk_profile.charAt(0).toUpperCase() + data.stated_risk_profile.slice(1) : 'Moderate'}`);

    const taxRecorded = data.tax_saved ?? 0;
    const taxLimit = data.tax_limit || 150000;
    const taxHeadroom = Math.max(0, taxLimit - taxRecorded);
    const portfolioStatus = data.alerts.some((alert) => alert.type === 'warning')
        ? 'Action Required'
        : data.valuation_coverage < 0.8 || data.history_status === 'insufficient_history'
            ? 'Building History'
            : 'Stable';

    return (
        <><Navbar /><PageTransition><main className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
            {showPortfolioStatus && (
                <aside role="status" aria-label="Portfolio status" className="fixed bottom-24 left-4 z-40 w-[min(22rem,calc(100vw-2rem))] rounded-2xl border border-emerald-200 bg-white p-4 shadow-xl sm:bottom-6">
                    <div className="flex items-start justify-between gap-3">
                        <div>
                            <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Portfolio status</p>
                            <p className="mt-1 text-xl font-semibold text-stone-950">{portfolioStatus}</p>
                        </div>
                        <button type="button" onClick={() => setShowPortfolioStatus(false)} aria-label="Dismiss portfolio status" className="rounded-md p-1 text-stone-500 hover:bg-stone-100"><X className="h-4 w-4" /></button>
                    </div>
                    <p className="mt-2 text-sm text-stone-600">{Math.round(data.valuation_coverage * 100)}% market-price coverage · {data.risk_level === 'Unavailable' ? 'Risk history unavailable' : `${data.risk_level} measured risk`}. Based on your saved data; this is not a return forecast.</p>
                    <button type="button" onClick={() => {
                        setShowPortfolioStatus(false);
                        window.dispatchEvent(new CustomEvent('open-chatbot', { detail: {
                            prompt: 'Summarize my portfolio against current economic and market conditions in four concise bullets. Use dated evidence if available; identify missing or stale evidence.',
                            autoSend: true,
                        } }));
                    }} className="mt-3 text-sm font-semibold text-emerald-700 hover:underline">Learn more <ArrowRight className="inline h-3.5 w-3.5" /></button>
                </aside>
            )}
            <header>
                <p className="text-sm font-medium text-emerald-700">Financial command center</p>
                <div className="mt-1 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                    <h1 className="text-3xl font-semibold tracking-tight text-stone-950">Your verified financial picture</h1>
                    <div className="flex flex-wrap gap-2">
                        <Button variant="outline" disabled={syncing} onClick={() => void refreshPrices()}>
                            <RefreshCw className={`mr-2 h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
                            {syncing ? 'Refreshing providers…' : 'Refresh market data'}
                        </Button>
                        <Button variant="outline" disabled={exporting} onClick={() => void exportView('pdf')}><Download className="mr-2 h-4 w-4" />PDF</Button>
                        <Button asChild><Link href="/insights">Continue to Insights <ArrowRight className="ml-2 h-4 w-4" /></Link></Button>
                    </div>
                </div>
                
                <div className="mt-3 flex flex-wrap items-center justify-between gap-4">
                    <div className="flex flex-wrap items-center gap-2">
                        <StatusPill tone={valuationTone}>{data.valuation_status.replaceAll('_', ' ')}</StatusPill>
                        <StatusPill><Clock3 className="mr-1 inline h-3 w-3" />As of {asOf}</StatusPill>
                        <StatusPill>{Math.round(data.valuation_coverage * 100)}% market-price coverage</StatusPill>
                    </div>

                    {/* Compact Day-One Banner in Right Corner */}
                    {hasUnavailableInsights && (
                        <div className="max-w-md rounded-xl border border-emerald-200 bg-emerald-50/60 p-3 shadow-sm text-xs text-stone-600 flex items-center justify-between gap-3">
                            <p className="leading-snug">
                                <span className="font-semibold text-stone-900">Useful from day one: </span>
                                Growth & risk update after repeated snapshots.
                            </p>
                            <Button size="sm" variant="outline" className="shrink-0 h-7 text-xs bg-white" onClick={askAssistantAboutCurrentData}>
                                <MessageCircle className="mr-1 h-3 w-3" /> Ask
                            </Button>
                        </div>
                    )}
                </div>
            </header>

            {error && <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">{error}</div>}

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <MetricCard label="Net worth" value={formatCurrency(data.net_worth)} icon={<IndianRupee className="h-4 w-4" />} tooltip="Total verified bank & investment balances minus active liabilities." detail={
                    data.net_worth_growth === null ? 'Available now; growth appears after two dated snapshots' : `${data.net_worth_growth}% across the selected recorded period`
                } />
                <MetricCard label="Measured portfolio risk" value={displayRiskLevel} icon={<ShieldCheck className="h-4 w-4" />} tooltip="Calculated from historical return observations and stated risk profile." detail={
                    riskDetail
                } />
                <MetricCard label="Current-month surplus" value={formatCurrency(data.surplus)} icon={<TrendingUp className="h-4 w-4" />} tooltip="Calculated as Monthly Income − Total Expenses for the current month." detail={
                    data.cashflow?.current_month && (data.cashflow.current_month.income > 0 || data.cashflow.current_month.expense > 0)
                        ? `${formatCurrency(data.cashflow.current_month.income)} income · ${formatCurrency(data.cashflow.current_month.expense)} expenses (bank)`
                        : `${formatCurrency(data.monthly_income)} income · ${formatCurrency(data.monthly_expenses)} expenses`
                } />
                <MetricCard label="80C evidence recorded" value={formatCurrency(taxRecorded)} icon={<Database className="h-4 w-4" />} tooltip="Sum of all identified PPF, ELSS, LIC, and other §80C eligible investment records." detail={
                    taxRecorded > 0
                        ? `${formatCurrency(taxRecorded)} of ${formatCurrency(taxLimit)} limit (${formatCurrency(taxHeadroom)} headroom)`
                        : `₹0 recorded · ${formatCurrency(taxLimit)} headroom remaining`
                } />
            </div>

            <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
                <section className="flex flex-col justify-between rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
                    <div>
                        <div className="mb-5 flex items-center justify-between">
                            <div>
                                <h2 className="font-semibold text-stone-950">Portfolio snapshots</h2>
                                <p className="text-sm text-stone-500">Recorded values only—no simulated history</p>
                            </div>
                            <BarChart3 className="h-5 w-5 text-emerald-700" />
                        </div>

                        {data.portfolio_history.length === 0 ? (
                            <div className="flex h-72 items-center justify-center rounded-xl bg-stone-50 px-6 text-center text-sm text-stone-500">
                                History begins after the first successful market-data sync.
                            </div>
                        ) : (
                            <ResponsiveContainer width="100%" height={288}>
                                {chartType === 'area' ? (
                                    <AreaChart data={data.portfolio_history}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#E7E5E4" />
                                        <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                                        <YAxis tickFormatter={formatChartValue} tick={{ fontSize: 11 }} />
                                        <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                                        <Area type="monotone" dataKey="value" stroke="#064E3B" fill="#ECFDF5" strokeWidth={2.5} />
                                    </AreaChart>
                                ) : (
                                    <LineChart data={data.portfolio_history}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#E7E5E4" />
                                        <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                                        <YAxis tickFormatter={formatChartValue} tick={{ fontSize: 11 }} />
                                        <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                                        <Line type="monotone" dataKey="value" stroke="#064E3B" strokeWidth={2.5} dot={{ r: 3 }} />
                                    </LineChart>
                                )}
                            </ResponsiveContainer>
                        )}
                    </div>

                    {/* Chart Controls & Apply / Save moved directly below graph */}
                    <div className="mt-6 border-t border-stone-100 pt-4 flex flex-wrap items-end gap-3">
                        <label className="text-xs font-medium text-stone-600">
                            Period
                            <select
                                className="mt-1 block h-9 rounded-md border border-stone-200 bg-white px-3 text-sm"
                                value={timePeriod}
                                onChange={(event) => setTimePeriod(event.target.value)}
                            >
                                <option value="1m">1 month</option>
                                <option value="3m">3 months</option>
                                <option value="6m">6 months</option>
                                <option value="1y">1 year</option>
                                <option value="all">All recorded</option>
                                <option value="custom">Custom</option>
                            </select>
                        </label>
                        {timePeriod === 'custom' && (
                            <>
                                <label className="text-xs font-medium text-stone-600">
                                    From
                                    <input
                                        className="mt-1 block h-9 rounded-md border border-stone-200 px-3 text-sm"
                                        type="date"
                                        value={dateFrom}
                                        onChange={(event) => setDateFrom(event.target.value)}
                                    />
                                </label>
                                <label className="text-xs font-medium text-stone-600">
                                    To
                                    <input
                                        className="mt-1 block h-9 rounded-md border border-stone-200 px-3 text-sm"
                                        type="date"
                                        value={dateTo}
                                        onChange={(event) => setDateTo(event.target.value)}
                                    />
                                </label>
                            </>
                        )}
                        <label className="text-xs font-medium text-stone-600">
                            History chart
                            <select
                                className="mt-1 block h-9 rounded-md border border-stone-200 bg-white px-3 text-sm"
                                value={chartType}
                                onChange={(event) => setChartType(event.target.value as 'line' | 'area')}
                            >
                                <option value="line">Line</option>
                                <option value="area">Area</option>
                            </select>
                        </label>
                        <Button size="sm" className="h-9" onClick={() => void saveView()} disabled={timePeriod === 'custom' && (!dateFrom || !dateTo)}>
                            Apply and save
                        </Button>
                    </div>
                </section>

                <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
                    <h2 className="font-semibold text-stone-950">Asset allocation</h2>
                    <p className="text-sm text-stone-500">Share of current reported net worth</p>
                    {data.asset_allocation.length === 0 ? (
                        <div className="flex h-64 items-center justify-center text-sm text-stone-500">No valued assets yet</div>
                    ) : (
                        <ResponsiveContainer width="100%" height={260}>
                            <PieChart>
                                <Pie data={data.asset_allocation} innerRadius={55} outerRadius={82} dataKey="value" paddingAngle={3}>
                                    {data.asset_allocation.map((item) => (
                                        <Cell key={item.name} fill={item.color} />
                                    ))}
                                </Pie>
                                <Legend iconType="circle" iconSize={8} />
                            </PieChart>
                        </ResponsiveContainer>
                    )}
                </section>
            </div>

            <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
                <section className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
                    <div className="border-b border-stone-100 px-6 py-5"><h2 className="font-semibold text-stone-950">Top holdings</h2><p className="text-sm text-stone-500">Every value includes its valuation state</p></div>
                    {data.top_holdings.length === 0 ? <p className="p-8 text-center text-sm text-stone-500">Import or add holdings to populate this table.</p> :
                        <div className="overflow-x-auto"><table className="w-full text-sm"><thead className="bg-stone-100 text-left text-xs uppercase tracking-wide text-stone-600"><tr><th className="px-6 py-3">Instrument</th><th className="px-4 py-3">Type</th><th className="px-4 py-3 text-right">Value</th><th className="px-4 py-3 text-right">P/L</th><th className="px-6 py-3">Source</th></tr></thead><tbody className="divide-y divide-stone-100">{data.top_holdings.map((holding) => <tr key={`${holding.type}-${holding.instrument}`} className="hover:bg-stone-50 transition-colors"><td className="px-6 py-4 font-medium text-stone-950">{holding.instrument}</td><td className="px-4 py-4 text-stone-600">{holding.type}</td><td className="px-4 py-4 text-right font-mono font-medium text-stone-900">{formatCurrency(holding.current_value)}</td><td className="px-4 py-4 text-right font-mono">{holding.profit_loss_percent === null ? '—' : `${holding.profit_loss_percent}%`}</td><td className="px-6 py-4"><StatusPill tone={holding.valuation_status === 'stored' ? 'good' : 'warn'}>{holding.price_source || holding.valuation_status || 'unavailable'}</StatusPill></td></tr>)}</tbody></table></div>}
                </section>
                <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm"><h2 className="font-semibold text-stone-950">Evidence-based alerts</h2><p className="mb-4 text-sm text-stone-500">Shown only when a rule is true</p>{data.alerts.length === 0 ? <div className="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-800">No active rule-based alerts.</div> : <div className="space-y-3">{data.alerts.map((alert) => <div key={alert.id} className="flex gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" /><p className="text-sm text-amber-900">{alert.message}</p></div>)}</div>}</section>
            </div>

            {/* ── Continue to Recommendations ── */}
            <div className="flex items-center justify-between rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
                <div>
                    <p className="font-semibold text-stone-950">Ready for your investment plan?</p>
                    <p className="mt-0.5 text-sm text-stone-500">See goal-aligned recommendations and trading insights based on your data.</p>
                </div>
                <Link
                    href="/insights"
                    className="group flex shrink-0 items-center gap-2 rounded-full bg-stone-900 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-emerald-700 hover:shadow-md"
                >
                    Investment Recommendations
                    <ChevronRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                </Link>
            </div>
        </main></PageTransition></>
    );
}
