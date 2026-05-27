'use client';

import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Upload,
    CheckCircle2,
    FileSpreadsheet,
    Trash2,
    ChevronDown,
    ChevronUp,
    AlertCircle,
    Info,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from '@/components/ui/dialog';
import Papa from 'papaparse';
import {
    BROKER_DEFINITIONS,
    parseBrokerCSV,
    type BrokerInfo,
    type BrokerHoldingRow,
    type BrokerCSVParseResult,
} from '@/services/broker-csv-parser';
import { equityApi } from '@/lib/api';

// =====================
// Types
// =====================
export interface TradingAccount {
    id: string;
    platform: string;
    icon: string;
    color: string;
    bgColor: string;
    connected: boolean;
    connectedAt?: string;
    accountId?: string;
    holdingsCount?: number;
}

interface TradingPanelProps {
    open: boolean;
    onClose: () => void;
    connectedAccounts: TradingAccount[];
    onAccountsChange: (accounts: TradingAccount[]) => void;
}

export default function TradingPanel({
    open,
    onClose,
    connectedAccounts,
    onAccountsChange,
}: TradingPanelProps) {
    const [expandedBroker, setExpandedBroker] = useState<string | null>(null);
    const [uploading, setUploading] = useState<string | null>(null);
    const [uploadResult, setUploadResult] = useState<BrokerCSVParseResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [syncProgress, setSyncProgress] = useState('');
    const fileInputRefs = useRef<Record<string, HTMLInputElement | null>>({});

    const handleFileUpload = async (brokerId: string, e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (!file.name.endsWith('.csv')) {
            setError('Please upload a CSV file.');
            return;
        }

        setUploading(brokerId);
        setError(null);
        setUploadResult(null);
        setSyncProgress('Parsing CSV...');

        Papa.parse(file, {
            complete: async (results) => {
                const rawData = results.data as string[][];
                const data = rawData.filter(row => row.some(cell => cell.trim() !== ''));

                if (data.length < 2) {
                    setError('CSV must have at least a header row and one data row.');
                    setUploading(null);
                    return;
                }

                const headers = data[0];
                const rows = data.slice(1);

                // Parse with broker-specific logic
                setSyncProgress('Detecting format...');
                const result = parseBrokerCSV(headers, rows, brokerId);
                setUploadResult(result);

                if (result.holdings.length === 0) {
                    setError('No valid holdings found in the CSV. ' + (result.errors[0] || ''));
                    setUploading(null);
                    return;
                }

                // Sync each holding to backend
                setSyncProgress(`Syncing ${result.holdings.length} holdings...`);
                let successCount = 0;
                let failCount = 0;

                for (let i = 0; i < result.holdings.length; i++) {
                    const h = result.holdings[i];
                    try {
                        await equityApi.createEquityHolding({
                            symbol: h.symbol,
                            equity_name: h.name,
                            exchange: h.exchange,
                            quantity: h.quantity,
                            avg_price: h.avgPrice,
                            broker: h.broker,
                        });
                        successCount++;
                    } catch {
                        failCount++;
                    }
                    setSyncProgress(`Syncing ${i + 1}/${result.holdings.length}...`);
                }

                // Update connected accounts
                const brokerDef = BROKER_DEFINITIONS.find(b => b.id === brokerId);
                if (brokerDef) {
                    const account: TradingAccount = {
                        id: brokerId,
                        platform: brokerDef.name,
                        icon: brokerDef.icon,
                        color: brokerDef.color,
                        bgColor: brokerDef.bgColor,
                        connected: true,
                        connectedAt: new Date().toLocaleString(),
                        accountId: `CSV-${file.name}`,
                        holdingsCount: successCount,
                    };

                    const existing = connectedAccounts.filter(a => a.id !== brokerId);
                    onAccountsChange([...existing, account]);
                }

                setSyncProgress(`Done! ${successCount} synced${failCount > 0 ? `, ${failCount} failed` : ''}`);
                setTimeout(() => {
                    setUploading(null);
                    setSyncProgress('');
                }, 2000);
            },
            error: (err) => {
                setError(`Failed to parse: ${err.message}`);
                setUploading(null);
            },
        });

        // Reset input
        const ref = fileInputRefs.current[brokerId];
        if (ref) ref.value = '';
    };

    const handleDisconnect = (id: string) => {
        onAccountsChange(connectedAccounts.filter(a => a.id !== id));
        setUploadResult(null);
    };

    const isConnected = (id: string) => connectedAccounts.some(a => a.id === id);

    return (
        <Dialog open={open} onOpenChange={(val) => { if (!val) { onClose(); setUploadResult(null); setError(null); } }}>
            <DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Import Broker Holdings</DialogTitle>
                    <DialogDescription>
                        Upload CSV files exported from your broker platforms. Select your broker below for specific instructions.
                    </DialogDescription>
                </DialogHeader>

                {/* Info Banner */}
                <div className="rounded-lg border border-blue-100 bg-blue-50/50 p-3 flex items-start gap-2">
                    <Info className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" />
                    <p className="text-xs text-blue-700">
                        Export your holdings as CSV from your broker&apos;s web dashboard, then upload here. 
                        Your data stays secure and is only stored in your account.
                    </p>
                </div>

                {/* Error */}
                <AnimatePresence>
                    {error && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                        >
                            <div className="rounded-lg border border-red-200 bg-red-50 p-3 flex items-start gap-2">
                                <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
                                <p className="text-sm text-red-700">{error}</p>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Broker List */}
                <div className="mt-2 space-y-3">
                    {BROKER_DEFINITIONS.map((broker) => {
                        const connected = isConnected(broker.id);
                        const account = connectedAccounts.find(a => a.id === broker.id);
                        const isExpanded = expandedBroker === broker.id;
                        const isLoading = uploading === broker.id;

                        return (
                            <motion.div
                                key={broker.id}
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={`rounded-xl border transition-all ${
                                    connected
                                        ? `${broker.bgColor} shadow-sm`
                                        : 'border-gray-100 bg-white hover:border-gray-200'
                                }`}
                            >
                                {/* Broker Header */}
                                <div className="flex items-center justify-between p-4">
                                    <div className="flex items-center gap-3">
                                        <div
                                            className={`flex h-10 w-10 items-center justify-center rounded-lg border text-lg font-bold ${
                                                connected ? broker.bgColor + ' ' + broker.color : 'border-gray-200 bg-gray-50 text-gray-400'
                                            }`}
                                        >
                                            {broker.icon}
                                        </div>
                                        <div>
                                            <p className="text-sm font-semibold text-gray-800">
                                                {broker.name}
                                            </p>
                                            {connected && account ? (
                                                <p className="text-xs text-gray-500">
                                                    {account.holdingsCount} holdings imported • {account.connectedAt}
                                                </p>
                                            ) : (
                                                <p className="text-xs text-gray-400">Upload CSV to import</p>
                                            )}
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2">
                                        {connected && (
                                            <>
                                                <span className="flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-1 text-xs font-medium text-green-700">
                                                    <CheckCircle2 className="h-3 w-3" />
                                                    Imported
                                                </span>
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    onClick={() => handleDisconnect(broker.id)}
                                                    className="gap-1 text-red-500 hover:text-red-600"
                                                >
                                                    <Trash2 className="h-3.5 w-3.5" />
                                                </Button>
                                            </>
                                        )}
                                        <Button
                                            size="sm"
                                            variant="outline"
                                            onClick={() => setExpandedBroker(isExpanded ? null : broker.id)}
                                            className="gap-1"
                                        >
                                            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                                            {connected ? 'Re-import' : 'Import'}
                                        </Button>
                                    </div>
                                </div>

                                {/* Expanded Section */}
                                <AnimatePresence>
                                    {isExpanded && (
                                        <motion.div
                                            initial={{ opacity: 0, height: 0 }}
                                            animate={{ opacity: 1, height: 'auto' }}
                                            exit={{ opacity: 0, height: 0 }}
                                            className="overflow-hidden"
                                        >
                                            <div className="border-t border-gray-100 px-4 pb-4 pt-3">
                                                {/* Instructions */}
                                                <div className="mb-4 rounded-lg bg-gray-50 p-3">
                                                    <p className="text-xs font-semibold text-gray-600 mb-2">
                                                        How to export from {broker.name}:
                                                    </p>
                                                    <ol className="space-y-1 text-xs text-gray-500">
                                                        {broker.exportInstructions.map((step, i) => (
                                                            <li key={i} className="flex gap-2">
                                                                <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-gray-200 text-[10px] font-bold text-gray-600">
                                                                    {i + 1}
                                                                </span>
                                                                {step}
                                                            </li>
                                                        ))}
                                                    </ol>
                                                </div>

                                                {/* Upload Area */}
                                                <input
                                                    type="file"
                                                    accept=".csv"
                                                    ref={(el) => { fileInputRefs.current[broker.id] = el; }}
                                                    onChange={(e) => handleFileUpload(broker.id, e)}
                                                    className="hidden"
                                                    id={`broker-upload-${broker.id}`}
                                                />
                                                <label
                                                    htmlFor={`broker-upload-${broker.id}`}
                                                    className={`flex cursor-pointer items-center gap-3 rounded-lg border-2 border-dashed p-4 transition-all ${
                                                        isLoading
                                                            ? 'border-blue-300 bg-blue-50/50'
                                                            : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50/20'
                                                    }`}
                                                >
                                                    <div className="rounded-full bg-blue-100 p-2">
                                                        {isLoading ? (
                                                            <svg className="h-5 w-5 animate-spin text-blue-600" viewBox="0 0 24 24" fill="none">
                                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                                            </svg>
                                                        ) : (
                                                            <Upload className="h-5 w-5 text-blue-600" />
                                                        )}
                                                    </div>
                                                    <div>
                                                        <p className="text-sm font-medium text-gray-700">
                                                            {isLoading ? syncProgress : `Upload ${broker.name} CSV`}
                                                        </p>
                                                        <p className="text-xs text-gray-400">
                                                            .csv files only
                                                        </p>
                                                    </div>
                                                </label>

                                                {/* Upload Result */}
                                                {uploadResult && uploading === null && expandedBroker === broker.id && (
                                                    <div className="mt-3 rounded-lg border border-green-200 bg-green-50 p-3">
                                                        <div className="flex items-center gap-2">
                                                            <CheckCircle2 className="h-4 w-4 text-green-600" />
                                                            <p className="text-sm font-medium text-green-700">
                                                                {uploadResult.holdings.length} holdings parsed from {uploadResult.broker}
                                                            </p>
                                                        </div>
                                                        {uploadResult.errors.length > 0 && (
                                                            <p className="mt-1 text-xs text-amber-600">
                                                                {uploadResult.errors.length} warnings
                                                            </p>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </motion.div>
                        );
                    })}
                </div>

                {/* Summary */}
                {connectedAccounts.length > 0 && (
                    <div className="mt-4 rounded-lg border border-blue-100 bg-blue-50/50 p-4">
                        <p className="text-sm font-medium text-blue-800">
                            {connectedAccounts.length} broker{connectedAccounts.length > 1 ? 's' : ''} imported
                        </p>
                        <p className="mt-1 text-xs text-blue-600">
                            Total: {connectedAccounts.reduce((sum, a) => sum + (a.holdingsCount || 0), 0)} holdings synced to your portfolio.
                        </p>
                    </div>
                )}
            </DialogContent>
        </Dialog>
    );
}
