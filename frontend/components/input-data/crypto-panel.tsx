'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Upload,
    Plus,
    Trash2,
    Bitcoin,
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
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from '@/components/ui/dialog';
import { cryptoApi } from '@/lib/api';
import Papa from 'papaparse';
import { validateCSVSchema } from '@/services/csv-schema-validator';
import type { CryptoOut, CryptoCreate } from '@/types';

interface CryptoPanelProps {
    open: boolean;
    onClose: () => void;
}

export default function CryptoPanel({ open, onClose }: CryptoPanelProps) {
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
    const [pendingFiles, setPendingFiles] = useState<{ id: string; name: string; headers: string[]; rows: string[][] }[]>([]);
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

    // Fetch existing holdings
    const fetchHoldings = useCallback(async () => {
        if (!open) return;
        try {
            setIsLoadingHoldings(true);
            const res = await cryptoApi.getCryptoHoldings();
            setHoldings(res.data || []);
        } catch (err) {
            console.warn('Could not fetch crypto holdings:', err);
        } finally {
            setIsLoadingHoldings(false);
        }
    }, [open]);

    useEffect(() => {
        if (open) {
            fetchHoldings();
        }
    }, [open, fetchHoldings]);

    // ── CSV Upload Handler ────────────────────────────────────────
    const handleFileUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files || []);
        if (files.length === 0) return;

        setIsUploading(true);
        setError(null);
        setSuccess(null);
        
        const errors: string[] = [];
        const newPending: { id: string; name: string; headers: string[]; rows: string[][] }[] = [];

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (!file.name.endsWith('.csv')) {
                errors.push(`${file.name}: Please upload a CSV file.`);
                continue;
            }

            setUploadStatus(`Parsing ${file.name} (${i + 1}/${files.length})...`);

            await new Promise<void>((resolve) => {
                Papa.parse(file, {
                    complete: async (results) => {
                        try {
                            const rawData = results.data as string[][];
                            const data = rawData.filter(row => row.some(cell => cell.trim() !== ''));

                            if (data.length < 2) {
                                errors.push(`${file.name}: CSV file must have at least a header row and one data row.`);
                                return resolve();
                            }

                            const headers = data[0];
                            const rows = data.slice(1);

                            setUploadStatus(`Validating schema for ${file.name}...`);
                            const validation = validateCSVSchema(headers, rows);

                            if (!validation.isValid || validation.schemaType !== 'crypto') {
                                errors.push(
                                    `${file.name}: ` + (validation.schemaType !== 'crypto' && validation.isValid
                                        ? 'This CSV was detected as "' + validation.schemaLabel + '" — please upload a crypto holdings CSV.'
                                        : `Validation failed: ${validation.errors[0]}`)
                                );
                                return resolve();
                            }

                            newPending.push({
                                id: crypto.randomUUID(),
                                name: file.name,
                                headers: headers.map(h => h.trim().toLowerCase()),
                                rows
                            });

                        } catch (err: any) {
                            errors.push(`${file.name}: Parsing failed (${err.message})`);
                        }
                        resolve();
                    },
                    error: (err) => {
                        errors.push(`${file.name}: Failed to parse CSV (${err.message})`);
                        resolve();
                    },
                });
            });
        }

        if (newPending.length > 0) {
            setPendingFiles(prev => [...prev, ...newPending]);
            setSuccess(`Ready to save ${newPending.length} file(s). Click "Save Data" below to confirm.`);
        }

        if (errors.length > 0) {
            setError(errors.join('\n'));
        }
        
        setIsUploading(false);
        setUploadStatus('');

        if (fileInputRef.current) fileInputRef.current.value = '';
    }, []);

    const handleSavePendingFiles = async () => {
        if (pendingFiles.length === 0) return;
        setIsUploading(true);
        setError(null);
        setSuccess(null);
        
        let totalSuccess = 0;
        let totalFail = 0;

        for (let i = 0; i < pendingFiles.length; i++) {
            const file = pendingFiles[i];
            setUploadStatus(`Syncing ${file.name} to backend...`);
            
            for (let j = 0; j < file.rows.length; j++) {
                const record: Record<string, string> = {};
                file.headers.forEach((h, idx) => {
                    record[h] = file.rows[j][idx]?.trim() ?? '';
                });

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
                    totalSuccess++;
                } catch {
                    totalFail++;
                }
                setUploadStatus(`Syncing ${file.name} (${j + 1}/${file.rows.length})...`);
            }
        }

        setSuccess(`Successfully saved ${totalSuccess} crypto holdings${totalFail > 0 ? " (" + totalFail + " failed)" : ""}.`);
        setPendingFiles([]);
        setIsUploading(false);
        setUploadStatus('');
        fetchHoldings();
    };

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
        <Dialog open={open} onOpenChange={(val) => { if (!val) onClose(); }}>
            <DialogContent className="sm:max-w-5xl max-h-[85vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Crypto Holdings</DialogTitle>
                    <DialogDescription>
                        Manage your cryptocurrency portfolio via CSV import or manual entry.
                    </DialogDescription>
                </DialogHeader>

                {/* Tab Buttons */}
                <div className="mb-6 flex gap-2">
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
                                <div className="overflow-auto max-h-[400px]">
                                    <table className="w-full text-sm">
                                        <thead className="bg-gray-50 sticky top-0">
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
                                multiple
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
                                        {isUploading ? uploadStatus : 'Click to upload crypto holdings CSV(s)'}
                                    </p>
                                    <p className="mt-1 text-xs text-gray-400">
                                        Required columns: symbol, crypto_name, quantity, avg_price
                                    </p>
                                </div>
                            </label>

                            {pendingFiles.length > 0 && (
                                <div className="mt-6 space-y-3">
                                    <h3 className="text-sm font-semibold text-gray-700">Pending Files to Save</h3>
                                    {pendingFiles.map(pf => (
                                        <div key={pf.id} className="flex items-center justify-between bg-orange-50 border border-orange-100 p-3 rounded-lg">
                                            <div className="flex items-center gap-2">
                                                <FileSpreadsheet className="h-4 w-4 text-orange-500" />
                                                <span className="text-sm font-medium text-gray-800">{pf.name}</span>
                                            </div>
                                            <span className="text-xs text-gray-500">{pf.rows.length} rows</span>
                                        </div>
                                    ))}
                                    <Button
                                        onClick={handleSavePendingFiles}
                                        disabled={isUploading}
                                        className="w-full mt-4 bg-gradient-to-r from-orange-500 to-amber-500 text-white"
                                    >
                                        {isUploading ? (
                                            <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> {uploadStatus || 'Saving...'}</>
                                        ) : (
                                            "Save Data to Portfolio"
                                        )}
                                    </Button>
                                </div>
                            )}

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
                        <div className="rounded-xl border border-gray-100 bg-white p-8 shadow-sm max-w-2xl mx-auto">
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
            </DialogContent>
        </Dialog>
    );
}
