'use client';

import { useEffect, useState } from 'react';
import { CheckCircle2, CircleAlert, ShieldCheck } from 'lucide-react';

import Navbar from '@/components/layout/navbar';
import PageTransition from '@/components/layout/page-transition';
import { Button } from '@/components/ui/button';
import { guardianApi } from '@/lib/api';

type GuardianAlert = Awaited<ReturnType<typeof guardianApi.listAlerts>>['data'][number];

export default function GuardianPage() {
    const [alerts, setAlerts] = useState<GuardianAlert[]>([]);
    const [error, setError] = useState<string | null>(null);
    useEffect(() => {
        guardianApi.listAlerts().then((response) => setAlerts(response.data)).catch(() => setError('Guardian evidence could not be loaded.'));
    }, []);
    const feedback = async (alertId: string, verdict: 'expected' | 'incorrect' | 'investigate') => {
        try { await guardianApi.submitFeedback(alertId, verdict); setError(null); } catch { setError('Feedback could not be recorded.'); }
    };
    return <><Navbar /><PageTransition><main className="mx-auto max-w-5xl px-4 py-8 sm:px-6"><header className="mb-6"><p className="text-sm font-medium text-blue-600">Replay-safe monitoring</p><h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-950">Guardian evidence center</h1><p className="mt-2 text-sm text-slate-500">Unusual does not mean fraudulent. Every alert shows the exact rule, observations and version that produced it.</p></header>{error && <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error}</div>}<div className="space-y-4">{alerts.map((alert) => <article key={alert.guardian_alert_id} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-start gap-3"><span className={`rounded-xl p-2 ${alert.severity === 'critical' ? 'bg-rose-50 text-rose-700' : 'bg-amber-50 text-amber-700'}`}><CircleAlert className="h-5 w-5" /></span><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center justify-between gap-2"><h2 className="font-semibold text-slate-950">{alert.title}</h2><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">{alert.alert_type.replaceAll('_', ' ')} · {alert.severity}</span></div><p className="mt-2 text-sm text-slate-600">{alert.explanation}</p><div className="mt-4 rounded-xl bg-slate-50 p-4"><p className="text-xs font-medium uppercase tracking-wide text-slate-500">Evidence · {alert.rule_version}</p><dl className="mt-2 grid gap-2 sm:grid-cols-2">{Object.entries(alert.evidence).map(([key, value]) => <div key={key}><dt className="text-xs text-slate-500">{key.replaceAll('_', ' ')}</dt><dd className="text-sm font-medium text-slate-900">{String(value)}</dd></div>)}</dl></div><div className="mt-4 flex flex-wrap gap-2"><Button size="sm" variant="outline" onClick={() => void feedback(alert.guardian_alert_id, 'expected')}>Expected</Button><Button size="sm" variant="outline" onClick={() => void feedback(alert.guardian_alert_id, 'incorrect')}>Incorrect</Button><Button size="sm" onClick={() => void feedback(alert.guardian_alert_id, 'investigate')}>Investigate</Button></div></div></div></article>)}{alerts.length === 0 && <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center"><ShieldCheck className="mx-auto h-10 w-10 text-emerald-500" /><h2 className="mt-3 font-semibold text-slate-950">No Guardian alerts</h2><p className="mt-1 text-sm text-slate-500">New canonical events will be evaluated by the separate Guardian worker.</p><CheckCircle2 className="mx-auto mt-4 h-5 w-5 text-emerald-500" /></div>}</div></main></PageTransition></>;
}
