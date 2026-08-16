'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Archive, Bell, CheckCheck, ShieldAlert } from 'lucide-react';

import Navbar from '@/components/layout/navbar';
import PageTransition from '@/components/layout/page-transition';
import { Button } from '@/components/ui/button';
import { notificationsApi } from '@/lib/api';
import type { QuantNotification } from '@/types';

export default function NotificationsPage() {
    const [items, setItems] = useState<QuantNotification[]>([]);
    const [error, setError] = useState<string | null>(null);
    useEffect(() => {
        notificationsApi.list().then((response) => { setItems(response.data); setError(null); }).catch(() => setError('Notifications could not be loaded.'));
        const stream = new EventSource('/api/notifications/stream', { withCredentials: true });
        stream.addEventListener('notification', (event) => {
            const item = JSON.parse((event as MessageEvent).data) as QuantNotification;
            setItems((current) => current.some((row) => row.notification_id === item.notification_id) ? current : [item, ...current]);
        });
        return () => stream.close();
    }, []);

    const mark = async (item: QuantNotification, action: 'read' | 'acknowledge' | 'archive') => {
        const response = await notificationsApi.mark(item.notification_id, action);
        setItems((current) => action === 'archive' ? current.filter((row) => row.notification_id !== item.notification_id) : current.map((row) => row.notification_id === item.notification_id ? response.data : row));
    };

    return <><Navbar /><PageTransition><main className="mx-auto max-w-4xl px-4 py-8 sm:px-6"><header className="mb-6"><p className="text-sm font-medium text-blue-600">Live evidence feed</p><h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-950">Notifications</h1><p className="mt-2 text-sm text-slate-500">Alerts are grouped, replayable and linked to their evidence.</p></header>{error && <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error}</div>}<div className="space-y-3">{items.map((item) => <article key={item.notification_id} className={`rounded-2xl border bg-white p-5 shadow-sm ${item.read_at ? 'border-slate-200' : 'border-blue-200 ring-1 ring-blue-100'}`}><div className="flex gap-3"><span className={`mt-0.5 rounded-xl p-2 ${item.severity === 'critical' ? 'bg-rose-50 text-rose-700' : item.severity === 'warning' ? 'bg-amber-50 text-amber-700' : 'bg-blue-50 text-blue-700'}`}>{item.category === 'guardian' ? <ShieldAlert className="h-5 w-5" /> : <Bell className="h-5 w-5" />}</span><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center justify-between gap-2"><h2 className="font-semibold text-slate-950">{item.title}</h2><time className="text-xs text-slate-400">{new Date(item.created_at).toLocaleString()}</time></div><p className="mt-1 text-sm text-slate-600">{item.body}</p><div className="mt-4 flex flex-wrap gap-2">{item.deep_link && <Button size="sm" asChild onClick={() => void mark(item, 'read')}><Link href={item.deep_link}>Review evidence</Link></Button>}<Button size="sm" variant="outline" onClick={() => void mark(item, 'acknowledge')}><CheckCheck className="mr-2 h-4 w-4" />Acknowledge</Button><Button size="sm" variant="outline" onClick={() => void mark(item, 'archive')}><Archive className="mr-2 h-4 w-4" />Archive</Button></div></div></div></article>)}{items.length === 0 && <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center"><Bell className="mx-auto h-8 w-8 text-slate-300" /><p className="mt-3 text-sm text-slate-500">No active notifications.</p></div>}</div></main></PageTransition></>;
}
