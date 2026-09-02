'use client';

import { ChangeEvent, DragEvent, useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import {
    AlertCircle, ArrowRight, Bitcoin, Building2, CheckCircle2, ChevronRight,
    Coins, Download, Eye, FileClock, FileSpreadsheet, Goal, Landmark,
    Loader2, Lock, RefreshCw, ShieldCheck, Trash2, TrendingUp, UploadCloud, X,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

import Navbar from '@/components/layout/navbar';
import PageTransition from '@/components/layout/page-transition';
import { Button } from '@/components/ui/button';
import { InfoTooltip } from '@/components/ui/tooltip';
import { importApi } from '@/lib/api';
import { IMPORT_TEMPLATES } from '@/lib/import-templates';
import type { ImportBatch, ImportMappingDiagnostic } from '@/types';
import { useUser } from '@/contexts/user-context';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function errorMessage(error: unknown): string {
    if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;
        if (typeof detail === 'string') return detail;
        if (detail && typeof detail === 'object' && 'message' in detail) return String(detail.message);
        return error.message;
    }
    return error instanceof Error ? error.message : 'The import could not be processed.';
}

function targetLabel(target: string): string {
    return target.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function mappingMethodLabel(method?: string): string {
    if (method === 'llm_headers') return 'Columns matched automatically';
    if (method === 'user_override') return 'Custom mapping applied';
    if (method === 'cas_parser') return 'CAS statement recognized';
    return 'Columns recognized automatically';
}

const isAmountColumn = (col: string) =>
    /amount|value|balance|price|nav|cost|debit|credit|quantity|units/i.test(col);

// ---------------------------------------------------------------------------
// Category config — matches ref image order
// ---------------------------------------------------------------------------

type CategoryKey = 'bank' | 'equity' | 'mf' | 'etf' | 'crypto' | 'transactions' | 'goals';

const CATEGORIES: {
    key: CategoryKey;
    label: string;
    desc: string;
    icon: React.ElementType;
    templateId?: string;
    action: 'upload' | 'goal';
}[] = [
    { key: 'bank',         label: 'Bank accounts',   desc: 'Bank statements and account records',           icon: Landmark,    templateId: 'bank-transactions', action: 'upload' },
    { key: 'equity',       label: 'Equity holdings', desc: 'NSE/BSE holdings and broker exports',           icon: TrendingUp,  templateId: 'equities',          action: 'upload' },
    { key: 'mf',           label: 'Mutual funds',    desc: 'Fund holdings and acquisition information',     icon: Building2,   templateId: 'mutual-funds',      action: 'upload' },
    { key: 'etf',          label: 'ETFs',            desc: 'Exchange-traded fund positions',                icon: Coins,       templateId: 'etfs',              action: 'upload' },
    { key: 'crypto',       label: 'Crypto holdings', desc: 'Token quantities held on exchanges or wallets', icon: Bitcoin,     templateId: 'crypto',            action: 'upload' },
    { key: 'transactions', label: 'Transactions',    desc: 'Investment and financial transactions',         icon: RefreshCw,   templateId: 'investment-transactions', action: 'upload' },
    { key: 'goals',        label: 'Goals',           desc: 'Financial goals and targets',                  icon: Goal,        action: 'goal' },
];

const STEPPER = [
    { num: '01', label: 'Choose data' },
    { num: '02', label: 'Upload file' },
    { num: '03', label: 'Review data' },
    { num: '04', label: 'Save import' },
];

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function DataImportsPage() {
    const router = useRouter();
    const { isAuthenticated, isLoading: sessionLoading } = useUser();
    const inputRef = useRef<HTMLInputElement>(null);

    // Upload state
    const [activeCategory, setActiveCategory] = useState<CategoryKey | null>(null);
    const [file, setFile] = useState<File | null>(null);
    const [batch, setBatch] = useState<ImportBatch | null>(null);
    const [busy, setBusy] = useState<'preview' | 'commit' | 'delete' | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [dragging, setDragging] = useState(false);

    // Mapping state (unchanged logic)
    const [mappingDiagnostic, setMappingDiagnostic] = useState<ImportMappingDiagnostic | null>(null);
    const [selectedTarget, setSelectedTarget] = useState('');
    const [manualMapping, setManualMapping] = useState<Record<string, string>>({});

    // History state
    const [importHistory, setImportHistory] = useState<ImportBatch[]>([]);
    const [historyLoading, setHistoryLoading] = useState(true);
    const [historyBusy, setHistoryBusy] = useState<string | null>(null);
    const [showBatchData, setShowBatchData] = useState(true);
    const batchRef = useRef<HTMLDivElement>(null);

    // Templates panel
    const [showTemplates, setShowTemplates] = useState(false);

    // ---------------------------------------------------------------------------
    // Data loading
    // ---------------------------------------------------------------------------

    const loadHistory = useCallback(async () => {
        setHistoryLoading(true);
        try {
            const response = await importApi.list();
            setImportHistory(response.data);
        } catch (caught) {
            setError(errorMessage(caught));
        } finally {
            setHistoryLoading(false);
        }
    }, []);

    useEffect(() => {
        if (sessionLoading) return;
        if (!isAuthenticated) {
            router.replace('/login?reason=session_required');
            return;
        }
        void loadHistory();
    }, [isAuthenticated, loadHistory, router, sessionLoading]);

    // ---------------------------------------------------------------------------
    // Upload logic (unchanged from original)
    // ---------------------------------------------------------------------------

    const mappingForTarget = (diagnostic: ImportMappingDiagnostic, target: string) => {
        const available = new Set(diagnostic.targets[target]?.available_columns || []);
        return Object.fromEntries(
            diagnostic.source_columns.map((source) => {
                const automatic = diagnostic.automatic_mapping[source];
                return [source, available.has(automatic) ? automatic : ''];
            }),
        );
    };

    const preview = async (
        selected: File,
        mappingOptions?: { targetType?: string; columnMapping?: Record<string, string>; fileMode?: 'holdings_snapshot' | 'investment_history' | 'bank_transactions' },
    ) => {
        setFile(selected);
        setBatch(null);
        setError(null);
        setBusy('preview');
        setShowBatchData(true);
        try {
            const response = await importApi.preview(selected, mappingOptions);
            setBatch(response.data);
            setMappingDiagnostic(null);
        } catch (caught) {
            if (axios.isAxiosError(caught)) {
                const detail = caught.response?.data?.detail as ImportMappingDiagnostic | undefined;
                if (detail?.code === 'mapping_required') {
                    const target = detail.suggested_target && detail.targets[detail.suggested_target]
                        ? detail.suggested_target
                        : Object.keys(detail.targets)[0];
                    setMappingDiagnostic(detail);
                    setSelectedTarget(target);
                    setManualMapping(mappingForTarget(detail, target));
                    return;
                }
            }
            setError(errorMessage(caught));
        } finally {
            setBusy(null);
        }
    };

    const selectFile = (event: ChangeEvent<HTMLInputElement>) => {
        const selected = event.target.files?.[0];
        if (selected) void preview(selected);
    };

    const dropFile = (event: DragEvent<HTMLDivElement>) => {
        event.preventDefault();
        setDragging(false);
        const selected = event.dataTransfer.files?.[0];
        if (selected) void preview(selected);
    };

    const changeTarget = (target: string) => {
        setSelectedTarget(target);
        if (mappingDiagnostic) setManualMapping(mappingForTarget(mappingDiagnostic, target));
        setError(null);
    };

    const applyMapping = () => {
        if (!file || !mappingDiagnostic || !selectedTarget) return;
        const selectedFields = new Set(Object.values(manualMapping).filter(Boolean));
        const required = mappingDiagnostic.targets[selectedTarget]?.required_columns || [];
        const missing = required.filter((field) => !selectedFields.has(field));
        if (selectedTarget === 'bank_transactions' && !['amount', 'debit', 'credit'].some((field) => selectedFields.has(field))) {
            missing.push('amount, debit, or credit');
        }
        if (missing.length) {
            setError(`Map the required fields first: ${missing.join(', ')}`);
            return;
        }
        const chosenMapping = Object.fromEntries(Object.entries(manualMapping).filter(([, value]) => value));
        void preview(file, { targetType: selectedTarget, columnMapping: chosenMapping });
    };

    const clarifyFile = (fileMode: 'holdings_snapshot' | 'investment_history' | 'bank_transactions') => {
        if (!file) return;
        void preview(file, { fileMode });
    };

    const commit = async () => {
        if (!batch) return;
        setError(null);
        setBusy('commit');
        try {
            const response = await importApi.commit(batch.import_batch_id);
            setBatch(response.data);
            await loadHistory();
        } catch (caught) {
            setError(errorMessage(caught));
        } finally {
            setBusy(null);
        }
    };

    const openSavedImport = async (batchId: string) => {
        setHistoryBusy(batchId);
        setError(null);
        try {
            const response = await importApi.get(batchId);
            setBatch(response.data);
            setFile(null);
            setMappingDiagnostic(null);
            setShowBatchData(true);
            setTimeout(() => batchRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
        } catch (caught) {
            setError(errorMessage(caught));
        } finally {
            setHistoryBusy(null);
        }
    };

    const downloadCleanedImport = async (item: ImportBatch) => {
        setHistoryBusy(item.import_batch_id);
        setError(null);
        try {
            const response = await importApi.downloadNormalized(item.import_batch_id);
            const url = URL.createObjectURL(response.data);
            const anchor = document.createElement('a');
            anchor.href = url;
            anchor.download = `${item.filename.replace(/\.[^.]+$/, '') || 'quant-import'}-normalized.csv`;
            anchor.click();
            URL.revokeObjectURL(url);
        } catch (caught) {
            setError(errorMessage(caught));
        } finally {
            setHistoryBusy(null);
        }
    };

    const discard = async () => {
        if (!batch) return;
        setError(null);
        setBusy('delete');
        try {
            await importApi.deletePreview(batch.import_batch_id);
            setBatch(null);
            setFile(null);
            setShowBatchData(false);
            if (inputRef.current) inputRef.current.value = '';
        } catch (caught) {
            setError(errorMessage(caught));
        } finally {
            setBusy(null);
        }
    };

    const clearData = async () => {
        if (!batch) return;
        setError(null);
        setBusy('delete');
        try {
            await importApi.deletePreview(batch.import_batch_id);
            setBatch(null);
            setFile(null);
            setShowBatchData(false);
            if (inputRef.current) inputRef.current.value = '';
            await loadHistory();
        } catch (caught) {
            setError(errorMessage(caught));
        } finally {
            setBusy(null);
        }
    };

    // ---------------------------------------------------------------------------
    // Derived state
    // ---------------------------------------------------------------------------

    const previewRows = batch?.preview_rows.slice(0, 20) || [];
    const columns = Array.from(new Set(previewRows.flatMap((row) => Object.keys(row).filter((col) => !col.startsWith('_')))));
    const committed = batch?.status === 'completed' || batch?.status === 'partial';

    const activeCategoryInfo = CATEGORIES.find((c) => c.key === activeCategory);
    const templateForCategory = activeCategoryInfo?.templateId
        ? IMPORT_TEMPLATES.find((t) => t.id === activeCategoryInfo.templateId)
        : undefined;

    if (sessionLoading || !isAuthenticated) {
        return <main className="flex min-h-screen items-center justify-center text-sm text-stone-500"><Loader2 className="mr-2 h-4 w-4 animate-spin" />Checking your secure session…</main>;
    }

    return (
        <><Navbar /><PageTransition>
            <div className="min-h-screen bg-stone-50/50">
                <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">

                    {/* ── HEADER ── */}
                    <header className="mb-8">
                        <p className="text-sm font-semibold uppercase tracking-wider text-emerald-700">Secure Importer</p>
                        <div className="mt-1 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                            <h1 className="text-3xl font-semibold leading-tight tracking-tight text-stone-950 sm:text-4xl">
                                Bring your financial data<br className="hidden sm:block" /> into QUANT.
                            </h1>
                            <div className="flex gap-2">
                                <Button asChild><Link href="/dashboard">Continue to Dashboard <ArrowRight className="ml-2 h-4 w-4" /></Link></Button>
                            </div>
                        </div>
                        <p className="mt-3 max-w-lg text-sm leading-relaxed text-stone-500">
                            Upload statements, holdings and transaction files. Every file is validated before it becomes part of your financial picture.
                        </p>
                    </header>

                    {error && (
                        <div className="mb-6 flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
                            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />{error}
                            <button className="ml-auto text-rose-400 hover:text-rose-600" onClick={() => setError(null)}><X className="h-4 w-4" /></button>
                        </div>
                    )}

                    {/* ═══════════════════════════════════════════
                        01  CHOOSE WHAT YOU WANT TO IMPORT
                    ════════════════════════════════════════════ */}
                    <section className="mb-6">
                        <p className="mb-3 text-xs font-bold uppercase tracking-widest text-stone-500">
                            <span className="mr-2 text-stone-950">01</span>Choose what you want to import
                        </p>

                        <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
                            {CATEGORIES.map((cat, i) => {
                                const Icon = cat.icon;
                                const isActive = activeCategory === cat.key;
                                const template = cat.templateId ? IMPORT_TEMPLATES.find((t) => t.id === cat.templateId) : undefined;

                                return (
                                    <div
                                        key={cat.key}
                                        className={`flex items-center gap-4 px-5 py-4 transition-colors ${i > 0 ? 'border-t border-stone-100' : ''} ${isActive ? 'bg-emerald-50/70' : 'hover:bg-stone-50'}`}
                                    >
                                        {/* Icon */}
                                        <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border ${isActive ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-stone-200 bg-stone-50 text-stone-500'}`}>
                                            <Icon className="h-5 w-5" />
                                        </div>

                                        {/* Label */}
                                        <div className="flex-1 min-w-0">
                                            <p className="font-semibold text-stone-950">{cat.label}</p>
                                            <p className="text-xs text-stone-500">{cat.desc}</p>
                                        </div>

                                        {/* Actions */}
                                        <div className="flex shrink-0 items-center gap-2">
                                            {/* Template download button */}
                                            {template && (
                                                <a
                                                    href={`/import-templates/${template.id}`}
                                                    download={template.filename}
                                                    className="flex items-center gap-1.5 rounded-lg border border-stone-200 bg-white px-3 py-2 text-xs font-medium text-stone-600 transition hover:border-stone-300 hover:bg-stone-50"
                                                >
                                                    <Download className="h-3.5 w-3.5" />
                                                    Template
                                                </a>
                                            )}

                                            {/* Upload / Add goal */}
                                            {cat.action === 'goal' ? (
                                                <Link
                                                    href="/input-data"
                                                    className="flex items-center gap-1.5 rounded-lg bg-stone-900 px-4 py-2 text-xs font-semibold text-white transition hover:bg-stone-800"
                                                >
                                                    Add goal <ArrowRight className="h-3.5 w-3.5" />
                                                </Link>
                                            ) : (
                                                <button
                                                    onClick={() => {
                                                        setActiveCategory(cat.key);
                                                        setBatch(null);
                                                        setFile(null);
                                                        setError(null);
                                                        setMappingDiagnostic(null);
                                                        setTimeout(() => document.getElementById('upload-section')?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 50);
                                                    }}
                                                    className={`flex items-center gap-1.5 rounded-lg px-4 py-2 text-xs font-semibold transition ${isActive ? 'bg-emerald-700 text-white hover:bg-emerald-600' : 'bg-stone-900 text-white hover:bg-stone-800'}`}
                                                >
                                                    {isActive ? 'Selected' : 'Upload'} <ArrowRight className="h-3.5 w-3.5" />
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </section>

                    {/* ═══════════════════════════════════════════
                        02  UPLOAD YOUR DATA
                    ════════════════════════════════════════════ */}
                    <section className="mb-6" id="upload-section">
                        <p className="mb-3 text-xs font-bold uppercase tracking-widest text-stone-500">
                            <span className="mr-2 text-stone-950">02</span>Upload your data
                        </p>

                        <input
                            ref={inputRef}
                            className="sr-only"
                            id="financial-file"
                            type="file"
                            accept=".csv,.xlsx,.pdf"
                            onChange={selectFile}
                        />

                        <div
                            onDragEnter={(e) => { e.preventDefault(); setDragging(true); }}
                            onDragOver={(e) => e.preventDefault()}
                            onDragLeave={() => setDragging(false)}
                            onDrop={dropFile}
                            className={`flex min-h-52 flex-col items-center justify-center rounded-2xl border-2 border-dashed px-8 py-10 text-center transition-colors ${dragging ? 'border-emerald-500 bg-emerald-50' : 'border-stone-300 bg-white'}`}
                        >
                            {busy === 'preview' ? (
                                <Loader2 className="h-10 w-10 animate-spin text-emerald-600" />
                            ) : (
                                <div className="flex h-12 w-12 items-center justify-center rounded-full border border-stone-200 bg-stone-50 shadow-sm">
                                    <UploadCloud className="h-6 w-6 text-stone-500" />
                                </div>
                            )}

                            <p className="mt-3 text-sm font-semibold text-stone-950">
                                {busy === 'preview' ? 'Organizing your file…' : (
                                    <>
                                        Importing:{' '}
                                        {activeCategoryInfo
                                            ? <span className="text-emerald-700">{activeCategoryInfo.label}</span>
                                            : <span className="text-stone-400">Select a category above</span>
                                        }
                                    </>
                                )}
                            </p>
                            <p className="mt-1 text-sm text-stone-500">Drop your file here or choose a file from your computer</p>
                            <p className="mt-0.5 text-xs text-stone-400">CSV · XLSX · PDF</p>

                            <Button
                                className="mt-4"
                                onClick={() => inputRef.current?.click()}
                                disabled={busy !== null || !activeCategory}
                            >
                                Choose file
                            </Button>

                            <p className="mt-3 flex items-center gap-1.5 text-xs text-stone-400">
                                <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                                Your files are encrypted and never shared.
                            </p>

                            {file && <p className="mt-2 text-xs text-stone-500">Selected: {file.name} · {(file.size / 1024).toFixed(1)} KB</p>}
                        </div>

                        {/* Mapping diagnostic (unchanged logic, re-styled) */}
                        {mappingDiagnostic && (
                            <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50/40 p-6">
                                <div className="flex items-start gap-3">
                                    <div className="rounded-full bg-amber-100 p-2 text-amber-700"><FileSpreadsheet className="h-5 w-5" /></div>
                                    <div>
                                        <p className="text-sm font-medium text-amber-800">This file needs a closer look</p>
                                        <h2 className="mt-1 text-xl font-semibold text-stone-950">We couldn&apos;t automatically recognize the columns</h2>
                                        <p className="mt-1 max-w-3xl text-sm text-stone-600">No data has been saved. This may be an unsupported format or a file with unusual column names.</p>
                                    </div>
                                </div>

                                <div className="mt-5 flex flex-wrap gap-3">
                                    <Button variant="outline" onClick={() => inputRef.current?.click()}>Choose another file</Button>
                                    <Button variant="outline" asChild><Link href="/input-data">Enter an account or goal</Link></Button>
                                </div>

                                <div className="mt-5 rounded-xl border border-emerald-100 bg-white p-4">
                                    <p className="font-medium text-stone-950">What kind of information does this file contain?</p>
                                    <p className="mt-1 text-sm text-stone-500">Choose one description and we&apos;ll retry the column matching.</p>
                                    <div className="mt-4 flex flex-wrap gap-2">
                                        <Button disabled={busy !== null} onClick={() => clarifyFile('holdings_snapshot')}>Current holdings or positions</Button>
                                        <Button disabled={busy !== null} onClick={() => clarifyFile('investment_history')}>Investment transaction history</Button>
                                        <Button disabled={busy !== null} onClick={() => clarifyFile('bank_transactions')}>Bank transactions</Button>
                                    </div>
                                </div>

                                <details className="mt-5 rounded-xl border border-stone-200 bg-white">
                                    <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-stone-800">
                                        Advanced: map the columns myself <span className="font-normal text-stone-500">(optional)</span>
                                    </summary>
                                    <div className="border-t border-stone-100 p-4">
                                        <p className="text-sm text-stone-600">Use this only if you know what the file&apos;s columns represent.</p>
                                        <label className="mt-4 block text-sm font-medium text-stone-800" htmlFor="mapping-target">The rows in this file are</label>
                                        <select
                                            id="mapping-target"
                                            value={selectedTarget}
                                            onChange={(e) => changeTarget(e.target.value)}
                                            className="mt-2 h-11 w-full rounded-lg border border-stone-300 bg-white px-3 text-sm text-stone-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 sm:max-w-md"
                                        >
                                            {Object.keys(mappingDiagnostic.targets).map((target) => (
                                                <option key={target} value={target}>{targetLabel(target)}</option>
                                            ))}
                                        </select>

                                        <div className="mt-5 overflow-hidden rounded-xl border border-stone-200">
                                            <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-4 bg-stone-100 px-4 py-3 text-xs font-medium uppercase tracking-wider text-stone-600">
                                                <span>Your column</span><span>Use it as <InfoTooltip content="Automatically categorized to standard financial formats." /></span>
                                            </div>
                                            <div className="divide-y divide-stone-100">
                                                {mappingDiagnostic.source_columns.map((source) => (
                                                    <div key={source} className="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)] items-center gap-4 px-4 py-3">
                                                        <span className="truncate text-sm font-medium text-stone-800" title={source}>{source}</span>
                                                        <select
                                                            aria-label={`Map ${source}`}
                                                            value={manualMapping[source] || ''}
                                                            onChange={(e) => setManualMapping((cur) => ({ ...cur, [source]: e.target.value }))}
                                                            className="h-9 min-w-0 rounded-md border border-stone-300 bg-white px-2 text-sm text-stone-800"
                                                        >
                                                            <option value="">Ignore this column</option>
                                                            {mappingDiagnostic.targets[selectedTarget]?.available_columns.map((field) => (
                                                                <option key={field} value={field}>{field.replaceAll('_', ' ')}</option>
                                                            ))}
                                                        </select>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>

                                        <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                                            <p className="text-xs text-stone-500">Your original file remains unchanged. You will review the organized rows next.</p>
                                            <Button disabled={busy !== null} onClick={applyMapping}>
                                                {busy === 'preview' && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Apply mapping and preview
                                            </Button>
                                        </div>
                                    </div>
                                </details>
                            </div>
                        )}

                        {/* Preview panel */}
                        <AnimatePresence>
                            {batch && showBatchData && (
                                <motion.div
                                    initial={{ opacity: 0, y: 8 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: 8 }}
                                    ref={batchRef}
                                    className="mt-4 overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm"
                                >
                                    {/* Batch header */}
                                    <div className="flex flex-col gap-4 border-b border-stone-100 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
                                        <div className="flex items-start gap-3">
                                            <FileSpreadsheet className="mt-0.5 h-5 w-5 text-emerald-700" />
                                            <div>
                                                <h2 className="font-semibold text-stone-950">{batch.filename}</h2>
                                                <p className="text-sm text-stone-500">Detected as {targetLabel(batch.target_type)} · {mappingMethodLabel(batch.column_mapping?.mapping_method)}</p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <div className="flex flex-wrap gap-2 text-xs font-medium">
                                                <span className="rounded-full bg-emerald-50 px-3 py-1.5 text-emerald-700 border border-emerald-200">{batch.valid_count} valid</span>
                                                {batch.error_count > 0 && <span className="rounded-full bg-rose-50 px-3 py-1.5 text-rose-700 border border-rose-200">{batch.error_count} errors</span>}
                                                <span className="rounded-full bg-stone-100 px-3 py-1.5 text-stone-700">{batch.status}</span>
                                            </div>
                                            <button onClick={() => setShowBatchData(false)} className="rounded-lg p-1.5 text-stone-400 hover:bg-stone-100 transition-colors"><X className="h-5 w-5" /></button>
                                        </div>
                                    </div>

                                    {/* Preview table */}
                                    {previewRows.length > 0 && (
                                        <div className="overflow-x-auto">
                                            <table className="min-w-full text-sm">
                                                <thead className="bg-stone-100 text-left text-xs font-medium uppercase tracking-wider text-stone-600">
                                                    <tr>{columns.map((col) => <th key={col} className={`whitespace-nowrap px-4 py-3 ${isAmountColumn(col) ? 'text-right' : ''}`}>{col.replaceAll('_', ' ')}</th>)}</tr>
                                                </thead>
                                                <tbody className="divide-y divide-stone-100">
                                                    {previewRows.map((row, idx) => (
                                                        <tr key={String(row._row_hash || idx)} className="bg-white hover:bg-stone-50 transition-colors">
                                                            {columns.map((col) => (
                                                                <td key={col} className={`max-w-64 truncate whitespace-nowrap px-4 py-3 ${isAmountColumn(col) ? 'text-right font-mono text-stone-900' : 'text-stone-700'}`}>{String(row[col] ?? '—')}</td>
                                                            ))}
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                            {batch.preview_rows.length > 20 && (
                                                <p className="border-t border-stone-100 px-4 py-3 text-xs text-stone-500">Showing 20 of {batch.preview_rows.length} valid rows.</p>
                                            )}
                                        </div>
                                    )}

                                    {/* Row errors */}
                                    {batch.row_errors && batch.row_errors.length > 0 && (
                                        <div className="border-t border-rose-100 bg-rose-50/50 p-5">
                                            <h3 className="font-medium text-rose-900">Rows requiring correction</h3>
                                            <ul className="mt-2 space-y-1 text-sm text-rose-800">
                                                {batch.row_errors.slice(0, 10).map((row) => (
                                                    <li key={`${row.row_number}-${row.code}`}>Row {row.row_number}: {row.message}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}

                                    {/* Batch actions */}
                                    <div className="flex flex-col gap-3 border-t border-stone-100 bg-stone-50 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
                                        <div className="text-sm text-stone-600">
                                            {committed
                                                ? <span className="flex items-center gap-2 font-medium text-emerald-700"><CheckCircle2 className="h-4 w-4" />{batch.committed_count} rows saved to your profile</span>
                                                : <span className="flex items-center gap-2"><ShieldCheck className="h-4 w-4" />Nothing has been saved yet.</span>
                                            }
                                        </div>
                                        <div className="flex gap-2">
                                            <Button variant="outline" disabled={busy !== null} onClick={() => void clearData()}>
                                                <Trash2 className="mr-2 h-4 w-4" />Delete file
                                            </Button>
                                            {!committed && (
                                                <Button disabled={busy !== null || batch.valid_count === 0} onClick={() => void commit()}>
                                                    {busy === 'commit' && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Confirm and save
                                                </Button>
                                            )}
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </section>

                    {/* ═══════════════════════════════════════════
                        03  YOUR UPLOADED FILES
                    ════════════════════════════════════════════ */}
                    <section className="mb-6">
                        <div className="mb-3 flex items-center justify-between">
                            <p className="text-xs font-bold uppercase tracking-widest text-stone-500">
                                <span className="mr-2 text-stone-950">03</span>Your uploaded files
                            </p>
                            <Button variant="outline" size="sm" disabled={historyLoading} onClick={() => void loadHistory()}>
                                <RefreshCw className={`mr-2 h-3.5 w-3.5 ${historyLoading ? 'animate-spin' : ''}`} />Refresh
                            </Button>
                        </div>

                        <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
                            {historyLoading ? (
                                <div className="flex items-center justify-center py-12 text-sm text-stone-500">
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />Loading your import history…
                                </div>
                            ) : importHistory.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-16 text-center">
                                    <FileClock className="h-8 w-8 text-stone-300 mb-3" />
                                    <p className="text-sm font-medium text-stone-600">No files uploaded yet</p>
                                    <p className="mt-1 text-xs text-stone-400">Your cleaned imports will appear here after the first upload.</p>
                                </div>
                            ) : (
                                <>
                                    {/* Table header */}
                                    <div className="hidden grid-cols-[minmax(0,2fr)_130px_110px_170px_140px] gap-4 border-b border-stone-100 bg-stone-50 px-5 py-3 text-xs font-semibold uppercase tracking-wider text-stone-400 sm:grid">
                                        <span>File</span><span>Category</span><span>Status</span><span>Uploaded on</span><span>Actions</span>
                                    </div>

                                    <div className="divide-y divide-stone-100">
                                        {importHistory.map((item) => (
                                            <div key={item.import_batch_id}>
                                                <div className="grid grid-cols-1 gap-3 px-5 py-4 sm:grid-cols-[minmax(0,2fr)_130px_110px_170px_140px] sm:items-center sm:gap-4">
                                                    {/* File */}
                                                    <div className="flex items-center gap-3 min-w-0">
                                                        <FileSpreadsheet className="h-5 w-5 shrink-0 text-stone-400" />
                                                        <div className="min-w-0">
                                                            <p className="truncate text-sm font-medium text-stone-950">{item.filename}</p>
                                                            <p className="text-xs text-stone-400">{item.valid_count} rows</p>
                                                        </div>
                                                    </div>

                                                    {/* Category pill */}
                                                    <span className="inline-flex w-fit items-center rounded-full border border-stone-200 bg-stone-50 px-2.5 py-1 text-xs font-medium text-stone-700">
                                                        {targetLabel(item.target_type)}
                                                    </span>

                                                    {/* Status */}
                                                    <span className={`inline-flex w-fit items-center gap-1.5 text-xs font-medium ${item.status === 'completed' ? 'text-emerald-700' : item.status === 'failed' ? 'text-rose-700' : 'text-amber-700'}`}>
                                                        <span className={`h-2 w-2 rounded-full ${item.status === 'completed' ? 'bg-emerald-500' : item.status === 'failed' ? 'bg-rose-500' : 'bg-amber-500'}`} />
                                                        {item.status === 'completed' ? 'Clean' : item.status === 'failed' ? 'Failed' : item.status === 'pending_review' ? 'Needs review' : 'Processing'}
                                                    </span>

                                                    {/* Date */}
                                                    <span className="text-xs text-stone-400">
                                                        {item.created_at ? new Date(item.created_at).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }) : '—'}
                                                    </span>

                                                    {/* Actions */}
                                                    <div className="flex items-center gap-3">
                                                        <button
                                                            onClick={() => void openSavedImport(item.import_batch_id)}
                                                            disabled={historyBusy === item.import_batch_id}
                                                            className="text-xs font-semibold text-stone-700 hover:text-stone-950 disabled:opacity-50"
                                                        >
                                                            {historyBusy === item.import_batch_id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Review'}
                                                        </button>
                                                        <button
                                                            onClick={() => void clearData()}
                                                            disabled={historyBusy === item.import_batch_id}
                                                            className="text-rose-400 hover:text-rose-600 disabled:opacity-50"
                                                            aria-label="Delete import"
                                                        >
                                                            <Trash2 className="h-4 w-4" />
                                                        </button>
                                                    </div>
                                                </div>

                                                {/* Inline batch viewer */}
                                                {batch?.import_batch_id === item.import_batch_id && showBatchData && (
                                                    <div className="border-t border-stone-100 bg-stone-50 px-5 pb-5 pt-4" ref={batchRef}>
                                                        <div className="overflow-hidden rounded-xl border border-stone-200 bg-white">
                                                            <div className="flex flex-col gap-4 border-b border-stone-100 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
                                                                <div className="flex items-start gap-3">
                                                                    <FileSpreadsheet className="mt-0.5 h-5 w-5 text-emerald-700" />
                                                                    <div>
                                                                        <h2 className="font-semibold text-stone-950">{batch.filename}</h2>
                                                                        <p className="text-sm text-stone-500">Detected as {targetLabel(batch.target_type)}</p>
                                                                    </div>
                                                                </div>
                                                                <div className="flex items-center gap-3">
                                                                    <div className="flex flex-wrap gap-2 text-xs font-medium">
                                                                        <span className="rounded-full bg-emerald-50 px-3 py-1.5 text-emerald-700 border border-emerald-200">{batch.valid_count} valid</span>
                                                                        {batch.error_count > 0 && <span className="rounded-full bg-rose-50 px-3 py-1.5 text-rose-700 border border-rose-200">{batch.error_count} errors</span>}
                                                                    </div>
                                                                    <button onClick={() => setShowBatchData(false)} className="rounded-lg p-1.5 text-stone-400 hover:bg-stone-100"><X className="h-5 w-5" /></button>
                                                                </div>
                                                            </div>

                                                            {previewRows.length > 0 && (
                                                                <div className="overflow-x-auto">
                                                                    <table className="min-w-full text-sm">
                                                                        <thead className="bg-stone-100 text-left text-xs font-medium uppercase tracking-wider text-stone-600">
                                                                            <tr>{columns.map((col) => <th key={col} className={`whitespace-nowrap px-4 py-3 ${isAmountColumn(col) ? 'text-right' : ''}`}>{col.replaceAll('_', ' ')}</th>)}</tr>
                                                                        </thead>
                                                                        <tbody className="divide-y divide-stone-100">
                                                                            {previewRows.map((row, idx) => (
                                                                                <tr key={String(row._row_hash || idx)} className="bg-white hover:bg-stone-50 transition-colors">
                                                                                    {columns.map((col) => (
                                                                                        <td key={col} className={`max-w-64 truncate whitespace-nowrap px-4 py-3 ${isAmountColumn(col) ? 'text-right font-mono text-stone-900' : 'text-stone-700'}`}>{String(row[col] ?? '—')}</td>
                                                                                    ))}
                                                                                </tr>
                                                                            ))}
                                                                        </tbody>
                                                                    </table>
                                                                    {batch.preview_rows.length > 20 && <p className="border-t border-stone-100 px-4 py-3 text-xs text-stone-500">Showing 20 of {batch.preview_rows.length} valid rows.</p>}
                                                                </div>
                                                            )}

                                                            <div className="flex flex-col gap-3 border-t border-stone-100 bg-stone-50 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
                                                                <div className="text-sm text-stone-600">
                                                                    {committed
                                                                        ? <span className="flex items-center gap-2 font-medium text-emerald-700"><CheckCircle2 className="h-4 w-4" />{batch.committed_count} rows saved</span>
                                                                        : <span className="flex items-center gap-2"><ShieldCheck className="h-4 w-4" />Nothing has been saved yet.</span>
                                                                    }
                                                                </div>
                                                                <div className="flex gap-2">
                                                                    <Button variant="outline" size="sm" disabled={busy !== null} onClick={() => void clearData()}><Trash2 className="mr-2 h-4 w-4" />Delete file</Button>
                                                                    {!committed && (
                                                                        <Button size="sm" disabled={busy !== null || batch.valid_count === 0} onClick={() => void commit()}>
                                                                            {busy === 'commit' && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Confirm and save
                                                                        </Button>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>

                                    {/* View all link */}
                                    <div className="border-t border-stone-100 px-5 py-3">
                                        <button
                                            onClick={() => void loadHistory()}
                                            className="flex items-center gap-1.5 text-sm font-semibold text-emerald-700 hover:underline"
                                        >
                                            View all files <ArrowRight className="h-3.5 w-3.5" />
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    </section>



                </main>
            </div>
        </PageTransition></>
    );
}
