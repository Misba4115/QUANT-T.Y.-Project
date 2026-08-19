'use client';

import { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, BarChart3, Clock3, Database, Download, IndianRupee, MessageCircle, RefreshCw, ShieldCheck, TrendingUp } from 'lucide-react';
import { Area, AreaChart, Cell, CartesianGrid, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import Navbar from '@/components/layout/navbar';
import PageTransition from '@/components/layout/page-transition';
import { Button } from '@/components/ui/button';
import { SkeletonCard, SkeletonChart, SkeletonTable } from '@/components/ui/skeletons';
import { InfoTooltip } from '@/components/ui/tooltip';
import { dashboardApi, marketDataApi } from '@/lib/api';
import { formatChartValue, formatCurrency } from '@/lib/helpers';
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
    const hasUnavailableInsights = data.net_worth_growth === null || data.risk_level === 'Unavailable' || data.tax_saved === null;

    return (
        <><Navbar /><PageTransition><main className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
            <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div>
                    <p className="text-sm font-medium text-emerald-700">Financial command center</p>
                    <h1 className="mt-1 text-3xl font-semibold tracking-tight text-stone-950">Your verified financial picture</h1>
                    <div className="mt-3 flex flex-wrap items-center gap-2">
                        <StatusPill tone={valuationTone}>{data.valuation_status.replaceAll('_', ' ')}</StatusPill>
                        <StatusPill><Clock3 className="mr-1 inline h-3 w-3" />As of {asOf}</StatusPill>
                        <StatusPill>{Math.round(data.valuation_coverage * 100)}% market-price coverage</StatusPill>
                    </div>
                </div>
                <div className="flex flex-wrap gap-2"><Button variant="outline" disabled={syncing} onClick={() => void refreshPrices()}><RefreshCw className={`mr-2 h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />{syncing ? 'Refreshing providers…' : 'Refresh market data'}</Button><Button variant="outline" disabled={exporting} onClick={() => void exportView('pdf')}><Download className="mr-2 h-4 w-4" />PDF</Button><Button variant="outline" disabled={exporting} onClick={() => void exportView('png')}><Download className="mr-2 h-4 w-4" />PNG</Button></div>
            </header>

            <section className="flex flex-wrap items-end gap-3 rounded-2xl border border-stone-200 bg-white p-4 shadow-sm"><label className="text-xs font-medium text-stone-600">Period<select className="mt-1 block h-9 rounded-md border border-stone-200 bg-white px-3 text-sm" value={timePeriod} onChange={(event) => setTimePeriod(event.target.value)}><option value="1m">1 month</option><option value="3m">3 months</option><option value="6m">6 months</option><option value="1y">1 year</option><option value="all">All recorded</option><option value="custom">Custom</option></select></label>{timePeriod === 'custom' && <><label className="text-xs font-medium text-stone-600">From<input className="mt-1 block h-9 rounded-md border border-stone-200 px-3 text-sm" type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} /></label><label className="text-xs font-medium text-stone-600">To<input className="mt-1 block h-9 rounded-md border border-stone-200 px-3 text-sm" type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} /></label></>}<label className="text-xs font-medium text-stone-600">History chart<select className="mt-1 block h-9 rounded-md border border-stone-200 bg-white px-3 text-sm" value={chartType} onChange={(event) => setChartType(event.target.value as 'line' | 'area')}><option value="line">Line</option><option value="area">Area</option></select></label><Button onClick={() => void saveView()} disabled={timePeriod === 'custom' && (!dateFrom || !dateTo)}>Apply and save</Button></section>

            {error && <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">{error}</div>}

            {hasUnavailableInsights && <section className="flex flex-col gap-4 rounded-2xl border border-emerald-200 bg-gradient-to-r from-emerald-50 to-stone-50 p-5 sm:flex-row sm:items-center sm:justify-between">
                <div className="max-w-3xl">
                    <h2 className="font-semibold text-stone-950">Your dashboard is useful from day one</h2>
                    <p className="mt-1 text-sm leading-6 text-stone-600">
                        Net worth, balances, allocation, holdings and recorded cashflow use everything you have already added. Growth and measured risk need repeated dated snapshots, while 80C needs an eligible transaction record. QUANT leaves only those measurements unavailable instead of guessing.
                    </p>
                </div>
                <Button className="shrink-0" onClick={askAssistantAboutCurrentData}><MessageCircle className="mr-2 h-4 w-4" />Ask about my current data</Button>
            </section>}

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <MetricCard label="Net worth" value={formatCurrency(data.net_worth)} icon={<IndianRupee className="h-4 w-4" />} tooltip="Total verified bank & investment balances minus active liabilities." detail={
                    data.net_worth_growth === null ? 'Available now; growth appears after two dated snapshots' : `${data.net_worth_growth}% across the selected recorded period`
                } />
                <MetricCard label="Measured portfolio risk" value={data.risk_level} icon={<ShieldCheck className="h-4 w-4" />} tooltip="Calculated from historical return observations using standard deviation of returns." detail={
                    data.risk_level === 'Unavailable' ? `Needs 30 return observations; ${data.measured_portfolio_risk?.sample_count || 0} recorded so far` : `Measured from history · stated preference: ${data.stated_risk_profile || 'not set'}`
                } />
                <MetricCard label="Current-month surplus" value={formatCurrency(data.surplus)} icon={<TrendingUp className="h-4 w-4" />} tooltip="Calculated as Monthly Income − Total Expenses for the current month." detail={
                    `${formatCurrency(data.monthly_income)} income · ${formatCurrency(data.monthly_expenses)} expenses`
                } />
                <MetricCard label="80C evidence recorded" value={data.tax_saved === null ? 'Unavailable' : formatCurrency(data.tax_saved)} icon={<Database className="h-4 w-4" />} tooltip="Sum of all identified PPF, ELSS, LIC, and other §80C eligible investment records." detail={
                    data.tax_saved === null ? 'Add or categorize an eligible PPF, ELSS, LIC or 80C record' : `Recorded evidence against the ${formatCurrency(data.tax_limit)} limit`
                } />
            </div>

            <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
                <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
                    <div className="mb-5 flex items-center justify-between"><div><h2 className="font-semibold text-stone-950">Portfolio snapshots</h2><p className="text-sm text-stone-500">Recorded values only—no simulated history</p></div><BarChart3 className="h-5 w-5 text-emerald-700" /></div>
                    {data.portfolio_history.length === 0 ? <div className="flex h-72 items-center justify-center rounded-xl bg-stone-50 px-6 text-center text-sm text-stone-500">History begins after the first successful market-data sync.</div> :
                        <ResponsiveContainer width="100%" height={288}>{chartType === 'area' ? <AreaChart data={data.portfolio_history}><CartesianGrid strokeDasharray="3 3" stroke="#E7E5E4" /><XAxis dataKey="month" tick={{ fontSize: 11 }} /><YAxis tickFormatter={formatChartValue} tick={{ fontSize: 11 }} /><Tooltip formatter={(value) => formatCurrency(Number(value))} /><Area type="monotone" dataKey="value" stroke="#064E3B" fill="#ECFDF5" strokeWidth={2.5} /></AreaChart> : <LineChart data={data.portfolio_history}><CartesianGrid strokeDasharray="3 3" stroke="#E7E5E4" /><XAxis dataKey="month" tick={{ fontSize: 11 }} /><YAxis tickFormatter={formatChartValue} tick={{ fontSize: 11 }} /><Tooltip formatter={(value) => formatCurrency(Number(value))} /><Line type="monotone" dataKey="value" stroke="#064E3B" strokeWidth={2.5} dot={{ r: 3 }} /></LineChart>}</ResponsiveContainer>}
                </section>
                <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
                    <h2 className="font-semibold text-stone-950">Asset allocation</h2><p className="text-sm text-stone-500">Share of current reported net worth</p>
                    {data.asset_allocation.length === 0 ? <div className="flex h-64 items-center justify-center text-sm text-stone-500">No valued assets yet</div> :
                        <ResponsiveContainer width="100%" height={260}><PieChart><Pie data={data.asset_allocation} innerRadius={55} outerRadius={82} dataKey="value" paddingAngle={3}>{data.asset_allocation.map((item) => <Cell key={item.name} fill={item.color} />)}</Pie><Legend iconType="circle" iconSize={8} /></PieChart></ResponsiveContainer>}
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
        </main></PageTransition></>
    );
}
