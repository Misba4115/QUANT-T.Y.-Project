'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import axios from 'axios';
import { Bitcoin, FileUp, Loader2, Plus, RefreshCw, Trash2 } from 'lucide-react';

import Navbar from '@/components/layout/navbar';
import PageTransition from '@/components/layout/page-transition';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cryptoApi } from '@/lib/api';
import { formatCurrency } from '@/lib/helpers';
import type { CryptoCreate, CryptoOut } from '@/types';

const EMPTY: CryptoCreate = { symbol: '', crypto_name: '', network: '', quantity: 0, avg_price: 0, exchange: '', wallet_address: '' };

function errorMessage(error: unknown): string {
    if (axios.isAxiosError(error)) return String(error.response?.data?.detail || error.message);
    return error instanceof Error ? error.message : 'The request failed.';
}

export default function CryptoPage() {
    const [holdings, setHoldings] = useState<CryptoOut[]>([]);
    const [form, setForm] = useState<CryptoCreate>(EMPTY);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [notice, setNotice] = useState<string | null>(null);

    const refresh = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await cryptoApi.getCryptoHoldings();
            setHoldings(response.data);
        } catch (caught) {
            setError(errorMessage(caught));
        } finally {
            setLoading(false);
        }
    }, []);
    useEffect(() => { void refresh(); }, [refresh]);

    const submit = async (event: FormEvent) => {
        event.preventDefault();
        setSaving(true);
        setError(null);
        setNotice(null);
        try {
            await cryptoApi.createCryptoHolding(form);
            setForm(EMPTY);
            setNotice('Crypto holding saved. Market value remains clearly labeled until a provider price is available.');
            await refresh();
        } catch (caught) {
            setError(errorMessage(caught));
        } finally {
            setSaving(false);
        }
    };

    const remove = async (id: string) => {
        setError(null);
        try {
            await cryptoApi.deleteCryptoHolding(id);
            setHoldings((current) => current.filter((holding) => holding.crypto_holding_id !== id));
        } catch (caught) {
            setError(errorMessage(caught));
        }
    };

    return (
        <><Navbar /><PageTransition><main className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
            <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-sm font-medium text-orange-600">Digital assets</p><h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-950">Crypto holdings</h1><p className="mt-2 text-sm text-slate-600">Manual records and confirmed imports share the same persisted backend source.</p></div><div className="flex gap-2"><Button variant="outline" onClick={() => void refresh()} disabled={loading}><RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />Refresh</Button><Button asChild><Link href="/csv-files"><FileUp className="mr-2 h-4 w-4" />Secure import</Link></Button></div></header>
            {error && <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error}</div>}{notice && <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">{notice}</div>}
            <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
                <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"><div className="border-b border-slate-100 px-6 py-5"><h2 className="font-semibold text-slate-950">Recorded holdings</h2><p className="text-sm text-slate-500">Provider provenance appears after market-data synchronization.</p></div>{loading ? <div className="flex h-48 items-center justify-center"><Loader2 className="h-6 w-6 animate-spin text-slate-400" /></div> : holdings.length === 0 ? <div className="p-12 text-center"><Bitcoin className="mx-auto h-10 w-10 text-slate-300" /><p className="mt-3 text-sm text-slate-500">No crypto holdings recorded.</p></div> : <div className="divide-y divide-slate-100">{holdings.map((holding) => <div key={holding.crypto_holding_id} className="flex items-center justify-between gap-4 px-6 py-4"><div><p className="font-medium text-slate-950">{holding.symbol} <span className="font-normal text-slate-500">· {holding.crypto_name}</span></p><p className="mt-1 text-xs text-slate-500">{holding.quantity} units · cost basis {formatCurrency(holding.avg_price)} · source {holding.price_source || 'user entry'}</p></div><div className="flex items-center gap-4"><p className="text-right text-sm font-medium text-slate-900">{holding.current_value === null || holding.current_value === undefined ? 'Not valued' : formatCurrency(holding.current_value)}</p><Button size="icon-sm" variant="ghost" aria-label={`Delete ${holding.symbol}`} onClick={() => void remove(holding.crypto_holding_id)}><Trash2 className="h-4 w-4 text-rose-500" /></Button></div></div>)}</div>}</section>
                <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-center gap-3"><span className="rounded-xl bg-orange-50 p-2 text-orange-700"><Plus className="h-5 w-5" /></span><div><h2 className="font-semibold text-slate-950">Manual holding</h2><p className="text-sm text-slate-500">Quantity and cost basis are required.</p></div></div><form className="mt-6 space-y-4" onSubmit={submit}><div className="grid grid-cols-2 gap-3"><div><Label htmlFor="symbol">Symbol</Label><Input id="symbol" required maxLength={32} value={form.symbol} onChange={(event) => setForm({ ...form, symbol: event.target.value.toUpperCase() })} /></div><div><Label htmlFor="name">Asset name</Label><Input id="name" required maxLength={120} value={form.crypto_name} onChange={(event) => setForm({ ...form, crypto_name: event.target.value })} /></div></div><div className="grid grid-cols-2 gap-3"><div><Label htmlFor="quantity">Quantity</Label><Input id="quantity" required min="0.00000001" step="any" type="number" value={form.quantity || ''} onChange={(event) => setForm({ ...form, quantity: Number(event.target.value) })} /></div><div><Label htmlFor="price">Average price (INR)</Label><Input id="price" required min="0" step="0.01" type="number" value={form.avg_price || ''} onChange={(event) => setForm({ ...form, avg_price: Number(event.target.value) })} /></div></div><div><Label htmlFor="exchange">Exchange or wallet</Label><Input id="exchange" maxLength={120} value={form.exchange || ''} onChange={(event) => setForm({ ...form, exchange: event.target.value })} /></div><Button className="w-full" disabled={saving}>{saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Save holding</Button></form></section>
            </div>
        </main></PageTransition></>
    );
}
