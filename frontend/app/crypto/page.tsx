'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Upload,
    Plus,
    Trash2,
    Bitcoin,
    ArrowLeft,
    AlertCircle,
    CheckCircle2,
    FileSpreadsheet,
    Edit3,
    X,
    Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import Navbar from '@/components/layout/navbar';
import PageTransition from '@/components/layout/page-transition';
import { useUser } from '@/contexts/user-context';
import { cryptoApi } from '@/lib/api';
import Papa from 'papaparse';
import { validateCSVSchema } from '@/services/csv-schema-validator';
import type { CryptoOut, CryptoCreate } from '@/types';

// =====================
// Component
// =====================
export default function CryptoPage() {
    const router = useRouter();
    const { isAuthenticated, isLoading: authLoading } = useUser();

    // Holdings state
    const [holdings, setHoldings] = useState<CryptoOut[]>([]);
    const [isLoadingHoldings, setIsLoadingHoldings] = useState(true);

    // Tab state
    const [activeTab, setActiveTab] = useState<'holdings' | 'csv' | 'manual'>('holdings');

    // CSV upload
    const [isUploading, setIsUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Manual entry form
    const [formData, setFormData] = useState<CryptoCreate>({
        symbol: '',
        crypto_name: '',
        network: '',
        quantity: 0,
        avg_price: 0,
        exchange: '',
        wallet_address: '',
    });
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Auth guard
    useEffect(() => {
        if (!authLoading && !isAuthenticated) {
            router.replace('/login');
        }
    }, [authLoading, isAuthenticated, router]);

    // Fetch existing holdings
    const fetchHoldings = useCallback(async () => {
        try {
            setIsLoadingHoldings(true);
            const res = await cryptoApi.getCryptoHoldings();
            setHoldings(res.data || []);
        } catch (err) {
            console.warn('Could not fetch crypto holdings:', err);
        } finally {
            setIsLoadingHoldings(false);
        }
    }, []);

    useEffect(() => {
        if (isAuthenticated && !authLoading) {
            fetchHoldings();
        }
    }, [isAuthenticated, authLoading, fetchHoldings]);

    // ── CSV Upload Handler ────────────────────────────────────────
    const handleFileUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (!file.name.endsWith('.csv')) {
            setError('Please upload a CSV file.');
            return;
        }

        setIsUploading(true);
        setUploadStatus('Parsing CSV...');
        setError(null);
        setSuccess(null);

        Papa.parse(file, {
            complete: async (results) => {
                const rawData = results.data as string[][];
                const data = rawData.filter(row => row.some(cell => cell.trim() !== ''));

                if (data.length < 2) {
                    setError('CSV file must have at least a header row and one data row.');
                    setIsUploading(false);
                    return;
                }

                const headers = data[0];
                const rows = data.slice(1);

                // Validate schema
                setUploadStatus('Validating schema...');
                const validation = validateCSVSchema(headers, rows);

                if (!validation.isValid || validation.schemaType !== 'crypto') {
                    setError(
                        validation.schemaType !== 'crypto' && validation.isValid
                            ? 'This CSV was detected as "' + validation.schemaLabel + '" — please upload a crypto holdings CSV.'
                            : `Validation failed: ${validation.errors[0]}`
                    );
                    setIsUploading(false);
                    return;
                }

                // Parse and create each holding
                setUploadStatus('Syncing to backend...');
                const normalizedHeaders = headers.map(h => h.trim().toLowerCase());
                let successCount = 0;
                let failCount = 0;

                for (let i = 0; i < rows.length; i++) {
                    const record: Record<string, string> = {};
                    normalizedHeaders.forEach((h, idx) => {
                        record[h] = rows[i][idx]?.trim() ?? '';
                    });

                    // Skip empty
                    if (!record['symbol']) continue;

                    try {
                        await cryptoApi.createCryptoHolding({
                            symbol: record['symbol'],
                            crypto_name: record['crypto_name'] || record['symbol'],
                            network: record['network'] || undefined,
                            quantity: parseFloat(record['quantity']) || 0,
                            avg_price: parseFloat(record['avg_price']) || 0,
                            exchange: record['exchange'] || undefined,
                            wallet_address: record['wallet_address'] || undefined,
                        });
                        successCount++;
                    } catch {
                        failCount++;
                    }

                    setUploadStatus(`Syncing ${i + 1}/${rows.length}...`);
                }

                setSuccess(`Imported ${successCount} crypto holdings${failCount > 0 ? ` (${failCount} failed)` : ''}.`);
                setIsUploading(false);
                setUploadStatus('');
                fetchHoldings();
            },
            error: (err) => {
                setError(`Failed to parse CSV: ${err.message}`);
                setIsUploading(false);
            },
        });

        if (fileInputRef.current) fileInputRef.current.value = '';
    }, [fetchHoldings]);

    // ── Manual Entry Handler ──────────────────────────────────────
    const handleManualSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.symbol || !formData.crypto_name || formData.quantity <= 0 || formData.avg_price <= 0) {
            setError('Please fill in all required fields with valid values.');
            return;
        }

        setIsSubmitting(true);
        setError(null);
        setSuccess(null);

        try {
            await cryptoApi.createCryptoHolding(formData);
            setSuccess(`${formData.symbol} added successfully!`);
            setFormData({
                symbol: '',
                crypto_name: '',
                network: '',
                quantity: 0,
                avg_price: 0,
                exchange: '',
                wallet_address: '',
            });
            fetchHoldings();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to add crypto holding');
        } finally {
            setIsSubmitting(false);
        }
    };

    // ── Delete Handler ────────────────────────────────────────────
    const handleDelete = async (id: string) => {
        try {
            await cryptoApi.deleteCryptoHolding(id);
            setHoldings(prev => prev.filter(h => h.crypto_holding_id !== id));
            setSuccess('Holding deleted.');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to delete');
        }
    };

    const formatINR = (num: number) => new Intl.NumberFormat('en-IN', {
        style: 'currency', currency: 'INR', maximumFractionDigits: 0,
    }).format(num);

    return (
        <>
            <Navbar />
            <PageTransition>
                <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                    {/* Header */}
                    <div className="mb-8">
                        <button
                            onClick={() => router.push('/input-data')}
                            className="mb-4 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 transition-colors"
                        >
                            <ArrowLeft className="h-4 w-4" />
                            Back to Input Data
                        </button>
                        <div className="flex items-center gap-3">
                            <div className="rounded-lg bg-orange-100 p-2.5">
                                <Bitcoin className="h-7 w-7 text-orange-600" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900">Crypto Holdings</h1>
                                <p className="text-sm text-gray-500">
                                    Manage your cryptocurrency portfolio via CSV import or manual entry.
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Tab Buttons */}
                    <div className="mb-8 flex gap-2">
                        {([
                            { key: 'holdings', label: 'My Holdings', icon: Bitcoin },
                            { key: 'csv', label: 'CSV Upload', icon: Upload },
                            { key: 'manual', label: 'Manual Entry', icon: Plus },
                        ] as const).map(tab => (
                            <Button
                                key={tab.key}
                                variant={activeTab === tab.key ? 'default' : 'outline'}
                                onClick={() => { setActiveTab(tab.key); setError(null); setSuccess(null); }}
                                className={`gap-2 ${activeTab === tab.key ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-md' : ''}`}
                            >
                                <tab.icon className="h-4 w-4" />
                                {tab.label}
                            </Button>
                        ))}
                    </div>

                    {/* Status Messages */}
                    <AnimatePresence>
                        {error && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="mb-6"
                            >
                                <div className="rounded-lg border border-red-200 bg-red-50 p-4 flex items-start gap-3">
                                    <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 shrink-0" />
                                    <p className="text-sm text-red-700">{error}</p>
                                    <button onClick={() => setError(null)} className="ml-auto">
                                        <X className="h-4 w-4 text-red-400" />
                                    </button>
                                </div>
                            </motion.div>
                        )}
                        {success && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="mb-6"
                            >
                                <div className="rounded-lg border border-green-200 bg-green-50 p-4 flex items-center gap-3">
                                    <CheckCircle2 className="h-5 w-5 text-green-600 shrink-0" />
                                    <p className="text-sm text-green-700">{success}</p>
                                    <button onClick={() => setSuccess(null)} className="ml-auto">
                                        <X className="h-4 w-4 text-green-400" />
                                    </button>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Holdings Tab */}
                    {activeTab === 'holdings' && (
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                            {isLoadingHoldings ? (
                                <div className="flex items-center justify-center py-16">
                                    <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                                </div>
                            ) : holdings.length === 0 ? (
                                <div className="rounded-xl border border-gray-100 bg-white p-12 text-center shadow-sm">
                                    <Bitcoin className="mx-auto h-12 w-12 text-gray-300" />
                                    <h3 className="mt-4 text-lg font-semibold text-gray-700">No crypto holdings</h3>
                                    <p className="mt-2 text-sm text-gray-400">
                                        Upload a CSV or add holdings manually to get started.
                                    </p>
                                    <div className="mt-6 flex justify-center gap-3">
                                        <Button variant="outline" onClick={() => setActiveTab('csv')} className="gap-2">
                                            <Upload className="h-4 w-4" /> Upload CSV
                                        </Button>
                                        <Button onClick={() => setActiveTab('manual')} className="gap-2 bg-gradient-to-r from-orange-500 to-amber-500 text-white">
                                            <Plus className="h-4 w-4" /> Add Manually
                                        </Button>
                                    </div>
                                </div>
                            ) : (
                                <div className="rounded-xl border border-gray-100 bg-white shadow-sm overflow-hidden">
                                    <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                                        <h2 className="text-lg font-bold text-gray-900">
                                            Holdings ({holdings.length})
                                        </h2>
                                        <div className="flex gap-2">
                                            <Button variant="outline" size="sm" onClick={() => setActiveTab('csv')} className="gap-1.5">
                                                <Upload className="h-3.5 w-3.5" /> Import CSV
                                            </Button>
                                            <Button size="sm" onClick={() => setActiveTab('manual')} className="gap-1.5 bg-gradient-to-r from-orange-500 to-amber-500 text-white">
                                                <Plus className="h-3.5 w-3.5" /> Add
                                            </Button>
                                        </div>
                                    </div>
                                    <div className="overflow-auto">
                                        <table className="w-full text-sm">
                                            <thead className="bg-gray-50">
                                                <tr>
                                                    <th className="whitespace-nowrap px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Symbol</th>
                                                    <th className="whitespace-nowrap px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Name</th>
                                                    <th className="whitespace-nowrap px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Network</th>
                                                    <th className="whitespace-nowrap px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500">Qty</th>
                                                    <th className="whitespace-nowrap px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500">Avg Price</th>
                                                    <th className="whitespace-nowrap px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500">Current</th>
                                                    <th className="whitespace-nowrap px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">Exchange</th>
                                                    <th className="whitespace-nowrap px-6 py-3 text-center text-xs font-semibold uppercase tracking-wider text-gray-500">Actions</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-50">
                                                {holdings.map((h) => (
                                                    <tr key={h.crypto_holding_id} className="transition-colors hover:bg-orange-50/30">
                                                        <td className="whitespace-nowrap px-6 py-3.5">
                                                            <span className="inline-flex items-center gap-1.5 font-semibold text-gray-900">
                                                                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-orange-100 text-xs font-bold text-orange-700">
                                                                    {h.symbol.charAt(0)}
                                                                </span>
                                                                {h.symbol}
                                                            </span>
                                                        </td>
                                                        <td className="whitespace-nowrap px-6 py-3.5 text-gray-700">{h.crypto_name}</td>
                                                        <td className="whitespace-nowrap px-6 py-3.5 text-gray-500">{h.network || '—'}</td>
                                                        <td className="whitespace-nowrap px-6 py-3.5 text-right font-mono text-gray-900">{h.quantity}</td>
                                                        <td className="whitespace-nowrap px-6 py-3.5 text-right text-gray-700">{formatINR(h.avg_price)}</td>
                                                        <td className="whitespace-nowrap px-6 py-3.5 text-right text-gray-700">{h.current_price ? formatINR(h.current_price) : '—'}</td>
                                                        <td className="whitespace-nowrap px-6 py-3.5 text-gray-500">{h.exchange || '—'}</td>
                                                        <td className="whitespace-nowrap px-6 py-3.5 text-center">
                                                            <Button
                                                                size="sm"
                                                                variant="outline"
                                                                onClick={() => handleDelete(h.crypto_holding_id)}
                                                                className="gap-1 text-red-500 hover:text-red-600 hover:border-red-200"
                                                            >
                                                                <Trash2 className="h-3.5 w-3.5" />
                                                            </Button>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    )}

                    {/* CSV Upload Tab */}
                    {activeTab === 'csv' && (
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                            <div className="rounded-xl border border-gray-100 bg-white p-8 shadow-sm">
                                <div className="flex items-center gap-2 mb-6">
                                    <FileSpreadsheet className="h-5 w-5 text-orange-600" />
                                    <h2 className="text-lg font-bold text-gray-900">Upload Crypto CSV</h2>
                                </div>

                                <input
                                    type="file"
                                    accept=".csv"
                                    ref={fileInputRef}
                                    onChange={handleFileUpload}
                                    className="hidden"
                                    id="crypto-csv-upload"
                                />
                                <label
                                    htmlFor="crypto-csv-upload"
                                    className="flex cursor-pointer flex-col items-center gap-3 rounded-xl border-2 border-dashed border-gray-200 bg-gray-50/50 p-10 transition-all hover:border-orange-300 hover:bg-orange-50/20"
                                >
                                    <div className="rounded-full bg-orange-100 p-4">
                                        <Upload className="h-7 w-7 text-orange-600" />
                                    </div>
                                    <div className="text-center">
                                        <p className="text-sm font-semibold text-gray-700">
                                            {isUploading ? uploadStatus : 'Click to upload crypto holdings CSV'}
                                        </p>
                                        <p className="mt-1 text-xs text-gray-400">
                                            Required columns: symbol, crypto_name, quantity, avg_price
                                        </p>
                                    </div>
                                </label>

                                <div className="mt-6 rounded-lg border border-blue-100 bg-blue-50/50 p-4">
                                    <p className="text-xs font-semibold text-blue-700 mb-2">Expected CSV format:</p>
                                    <code className="block text-xs text-blue-600 font-mono bg-blue-100/50 rounded p-2 overflow-x-auto">
                                        symbol,crypto_name,network,quantity,avg_price,current_price,exchange,wallet_address
                                    </code>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {/* Manual Entry Tab */}
                    {activeTab === 'manual' && (
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                            <div className="rounded-xl border border-gray-100 bg-white p-8 shadow-sm max-w-2xl">
                                <div className="flex items-center gap-2 mb-6">
                                    <Edit3 className="h-5 w-5 text-orange-600" />
                                    <h2 className="text-lg font-bold text-gray-900">Add Crypto Holding</h2>
                                </div>

                                <form onSubmit={handleManualSubmit} className="space-y-5">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <Label htmlFor="crypto-symbol">Symbol *</Label>
                                            <Input
                                                id="crypto-symbol"
                                                placeholder="e.g. BTC"
                                                value={formData.symbol}
                                                onChange={(e) => setFormData(prev => ({ ...prev, symbol: e.target.value.toUpperCase() }))}
                                                className="mt-1.5"
                                                required
                                            />
                                        </div>
                                        <div>
                                            <Label htmlFor="crypto-name">Name *</Label>
                                            <Input
                                                id="crypto-name"
                                                placeholder="e.g. Bitcoin"
                                                value={formData.crypto_name}
                                                onChange={(e) => setFormData(prev => ({ ...prev, crypto_name: e.target.value }))}
                                                className="mt-1.5"
                                                required
                                            />
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <Label htmlFor="crypto-quantity">Quantity *</Label>
                                            <Input
                                                id="crypto-quantity"
                                                type="number"
                                                step="any"
                                                min="0"
                                                placeholder="0.00"
                                                value={formData.quantity || ''}
                                                onChange={(e) => setFormData(prev => ({ ...prev, quantity: parseFloat(e.target.value) || 0 }))}
                                                className="mt-1.5"
                                                required
                                            />
                                        </div>
                                        <div>
                                            <Label htmlFor="crypto-avg-price">Avg Price (INR) *</Label>
                                            <Input
                                                id="crypto-avg-price"
                                                type="number"
                                                step="any"
                                                min="0"
                                                placeholder="0.00"
                                                value={formData.avg_price || ''}
                                                onChange={(e) => setFormData(prev => ({ ...prev, avg_price: parseFloat(e.target.value) || 0 }))}
                                                className="mt-1.5"
                                                required
                                            />
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <Label htmlFor="crypto-network">Network</Label>
                                            <Input
                                                id="crypto-network"
                                                placeholder="e.g. Bitcoin, Ethereum"
                                                value={formData.network || ''}
                                                onChange={(e) => setFormData(prev => ({ ...prev, network: e.target.value }))}
                                                className="mt-1.5"
                                            />
                                        </div>
                                        <div>
                                            <Label htmlFor="crypto-exchange">Exchange</Label>
                                            <Input
                                                id="crypto-exchange"
                                                placeholder="e.g. Coinbase, WazirX"
                                                value={formData.exchange || ''}
                                                onChange={(e) => setFormData(prev => ({ ...prev, exchange: e.target.value }))}
                                                className="mt-1.5"
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <Label htmlFor="crypto-wallet">Wallet Address</Label>
                                        <Input
                                            id="crypto-wallet"
                                            placeholder="Optional wallet address"
                                            value={formData.wallet_address || ''}
                                            onChange={(e) => setFormData(prev => ({ ...prev, wallet_address: e.target.value }))}
                                            className="mt-1.5"
                                        />
                                    </div>

                                    <Button
                                        type="submit"
                                        disabled={isSubmitting}
                                        className="w-full h-11 gap-2 bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-md hover:shadow-lg"
                                    >
                                        {isSubmitting ? (
                                            <><Loader2 className="h-4 w-4 animate-spin" /> Adding...</>
                                        ) : (
                                            <><Plus className="h-4 w-4" /> Add Crypto Holding</>
                                        )}
                                    </Button>
                                </form>
                            </div>
                        </motion.div>
                    )}
                </main>
            </PageTransition>
        </>
    );
}
