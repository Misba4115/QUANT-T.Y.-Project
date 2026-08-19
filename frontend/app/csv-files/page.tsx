'use client';

import { ChangeEvent, DragEvent, useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { AlertCircle, CheckCircle2, Download, Eye, FileClock, FileSpreadsheet, Loader2, RefreshCw, ShieldCheck, Sparkles, Trash2, UploadCloud, X } from 'lucide-react';

import Navbar from '@/components/layout/navbar';
import PageTransition from '@/components/layout/page-transition';
import { Button } from '@/components/ui/button';
import { InfoTooltip } from '@/components/ui/tooltip';
import { importApi } from '@/lib/api';
import { IMPORT_TEMPLATES } from '@/lib/import-templates';
import type { ImportBatch, ImportMappingDiagnostic } from '@/types';
import { useUser } from '@/contexts/user-context';

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

export default function DataImportsPage() {
    const router = useRouter();
    const { isAuthenticated, isLoading: sessionLoading } = useUser();
    const inputRef = useRef<HTMLInputElement>(null);
    const [file, setFile] = useState<File | null>(null);
    const [batch, setBatch] = useState<ImportBatch | null>(null);
    const [busy, setBusy] = useState<'preview' | 'commit' | 'delete' | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [dragging, setDragging] = useState(false);
    const [mappingDiagnostic, setMappingDiagnostic] = useState<ImportMappingDiagnostic | null>(null);
    const [selectedTarget, setSelectedTarget] = useState('');
    const [manualMapping, setManualMapping] = useState<Record<string, string>>({});
    const [importHistory, setImportHistory] = useState<ImportBatch[]>([]);
    const [historyLoading, setHistoryLoading] = useState(true);
    const [historyBusy, setHistoryBusy] = useState<string | null>(null);
    const [showBatchData, setShowBatchData] = useState(true);
    const batchRef = useRef<HTMLDivElement>(null);

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
            // Scroll the inline viewer into view
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

    const previewRows = batch?.preview_rows.slice(0, 20) || [];
    const columns = Array.from(new Set(previewRows.flatMap((row) => Object.keys(row).filter((column) => !column.startsWith('_')))));
    const committed = batch?.status === 'completed' || batch?.status === 'partial';
    const sourceMapping = batch?.column_mapping?.source_to_canonical || {};
    const changedMappings = Object.entries(sourceMapping).filter(([source, canonical]) => source !== canonical);
    const recognizedColumns = batch?.column_mapping?.recognized_columns || [];
    const ignoredColumns = batch?.column_mapping?.ignored_columns || [];

    // Detect if a column looks like it has amounts (for right-align + monospace)
    const isAmountColumn = (col: string) => /amount|value|balance|price|nav|cost|debit|credit|quantity|units/i.test(col);

    if (sessionLoading || !isAuthenticated) {
        return <main className="flex min-h-screen items-center justify-center text-sm text-stone-500"><Loader2 className="mr-2 h-4 w-4 animate-spin" />Checking your secure session…</main>;
    }

    return (
        <><Navbar /><PageTransition><main className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
            <header>
                <p className="text-sm font-medium text-emerald-700">Secure data intake</p>
                <h1 className="mt-1 text-3xl font-semibold tracking-tight text-stone-950">Preview before anything is saved</h1>
                <p className="mt-2 max-w-3xl text-sm text-stone-600">Upload a bank statement, portfolio export, or investment history. QUANT will organize the columns into a clean, reviewable preview.</p>
            </header>

            <section className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)]">
                <div className="flex flex-col gap-3 border-b border-stone-100 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex items-start gap-3">
                        <span className="rounded-xl bg-emerald-50 p-2 text-emerald-700"><FileClock className="h-5 w-5" /></span>
                        <div><h2 className="font-semibold text-stone-950">Your imports</h2><p className="text-sm text-stone-500">Cleaned copies stay available across sessions.</p></div>
                    </div>
                    <Button variant="outline" disabled={historyLoading} onClick={() => void loadHistory()}><RefreshCw className={`mr-2 h-4 w-4 ${historyLoading ? 'animate-spin' : ''}`} />Refresh</Button>
                </div>
                {historyLoading ? (
                    <div className="flex items-center justify-center px-6 py-10 text-sm text-stone-500"><Loader2 className="mr-2 h-4 w-4 animate-spin" />Loading your import history…</div>
                ) : importHistory.length === 0 ? (
                    <div className="px-6 py-10 text-center text-sm text-stone-500">Your cleaned imports will appear here after the first preview.</div>
                ) : (
                    <div className="divide-y divide-stone-100">
                        {importHistory.map((item) => (
                            <div key={item.import_batch_id} className="flex flex-col">
                                <div className="flex flex-col gap-4 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
                                <div className="min-w-0">
                                    <div className="flex flex-wrap items-center gap-2"><p className="truncate font-medium text-stone-950">{item.filename}</p><span className={`rounded-full px-2.5 py-1 text-xs font-medium ${item.status === 'completed' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : item.status === 'failed' ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-amber-50 text-amber-700 border border-amber-200'}`}>{item.status}</span></div>
                                    <p className="mt-1 text-xs text-stone-500">{targetLabel(item.target_type)} · {item.valid_count} cleaned rows{item.created_at ? ` · ${new Date(item.created_at).toLocaleString()}` : ''}</p>
                                </div>
                                <div className="flex shrink-0 flex-wrap gap-2">
                                    <Button variant="outline" disabled={historyBusy === item.import_batch_id} onClick={() => void openSavedImport(item.import_batch_id)}><Eye className="mr-2 h-4 w-4" />View cleaned data</Button>
                                    <Button variant="outline" disabled={historyBusy === item.import_batch_id || item.valid_count === 0} onClick={() => void downloadCleanedImport(item)}><Download className="mr-2 h-4 w-4" />Clean CSV</Button>
                                </div>
                                </div>
                                {batch?.import_batch_id === item.import_batch_id && showBatchData && (
                                    <div className="px-6 pb-6 pt-2" ref={batchRef}>
                                        <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
                                            <div className="flex flex-col gap-4 border-b border-stone-100 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
                                                <div className="flex items-start gap-3"><FileSpreadsheet className="mt-0.5 h-5 w-5 text-emerald-700" /><div><h2 className="font-semibold text-stone-950">{batch.filename}</h2><p className="text-sm text-stone-500">Detected as {targetLabel(batch.target_type)}</p></div></div>
                                                <div className="flex items-center gap-3">
                                                    <div className="flex flex-wrap gap-2 text-xs font-medium"><span className="rounded-full bg-emerald-50 px-3 py-1.5 text-emerald-700 border border-emerald-200">{batch.valid_count} valid</span>{batch.error_count > 0 && <span className="rounded-full bg-rose-50 px-3 py-1.5 text-rose-700 border border-rose-200">{batch.error_count} errors</span>}<span className="rounded-full bg-stone-100 px-3 py-1.5 text-stone-700">{batch.status}</span></div>
                                                    <button onClick={() => setShowBatchData(false)} className="rounded-lg p-1.5 text-stone-400 hover:bg-stone-100 hover:text-stone-600 transition-colors" aria-label="Close viewer"><X className="h-5 w-5" /></button>
                                                </div>
                                            </div>

                                            {previewRows.length > 0 && <div className="overflow-x-auto"><table className="min-w-full text-sm"><thead className="bg-stone-100 text-left text-xs font-medium uppercase tracking-wider text-stone-600"><tr>{columns.map((column) => <th key={column} className={`whitespace-nowrap px-4 py-3 ${isAmountColumn(column) ? 'text-right' : ''}`}>{column.replaceAll('_', ' ')}</th>)}</tr></thead><tbody className="divide-y divide-stone-100">{previewRows.map((row, index) => <tr key={String(row._row_hash || index)} className="bg-white hover:bg-stone-50 transition-colors">{columns.map((column) => <td key={column} className={`max-w-64 truncate whitespace-nowrap px-4 py-3 ${isAmountColumn(column) ? 'text-right font-mono text-stone-900' : 'text-stone-700'}`}>{String(row[column] ?? '—')}</td>)}</tr>)}</tbody></table>{batch.preview_rows.length > 20 && <p className="border-t border-stone-100 px-4 py-3 text-xs text-stone-500">Showing 20 of {batch.preview_rows.length} valid rows.</p>}</div>}

                                            {batch.row_errors && batch.row_errors.length > 0 && <div className="border-t border-rose-100 bg-rose-50/50 p-5"><h3 className="font-medium text-rose-900">Rows requiring correction</h3><ul className="mt-2 space-y-1 text-sm text-rose-800">{batch.row_errors.slice(0, 10).map((row) => <li key={`${row.row_number}-${row.code}`}>Row {row.row_number}: {row.message}</li>)}</ul></div>}

                                            <div className="flex flex-col gap-3 border-t border-stone-100 bg-stone-50 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
                                                <div className="text-sm text-stone-600">{batch.status === 'completed' || batch.status === 'partial' ? <span className="flex items-center gap-2 font-medium text-emerald-700"><CheckCircle2 className="h-4 w-4" />{batch.committed_count} rows saved</span> : <span className="flex items-center gap-2"><ShieldCheck className="h-4 w-4" />Nothing has been saved yet.</span>}</div>
                                                <div className="flex gap-2">
                                                    <Button variant="outline" disabled={busy !== null} onClick={() => void clearData()}><Trash2 className="mr-2 h-4 w-4" />Delete file</Button>
                                                    {batch.status !== 'completed' && batch.status !== 'partial' && <Button disabled={busy !== null || batch.valid_count === 0} onClick={() => void commit()}>{busy === 'commit' && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Confirm and save</Button>}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </section>

            <section className="grid gap-4 sm:grid-cols-3">
                {[
                    ['1', 'Preview safely', 'Nothing is written until you approve.'],
                    ['2', 'Review your data', 'See organized rows and any issues found.'],
                    ['3', 'Save once', 'Duplicates are automatically prevented.'],
                ].map(([number, title, description]) => <div key={number} className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm"><div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-50 text-sm font-semibold text-emerald-700">{number}</div><h2 className="mt-3 font-semibold text-stone-950">{title}</h2><p className="mt-1 text-sm text-stone-500">{description}</p></div>)}
            </section>

            <section className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
                <input ref={inputRef} className="sr-only" id="financial-file" type="file" accept=".csv,.xlsx,.pdf" onChange={selectFile} />
                <div
                    onDragEnter={(event) => { event.preventDefault(); setDragging(true); }}
                    onDragOver={(event) => event.preventDefault()}
                    onDragLeave={() => setDragging(false)}
                    onDrop={dropFile}
                    className={`flex min-h-56 flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center transition ${dragging ? 'border-emerald-500 bg-emerald-50' : 'border-stone-300 bg-stone-50'}`}
                >
                    {busy === 'preview' ? <Loader2 className="h-10 w-10 animate-spin text-emerald-600" /> : <UploadCloud className="h-10 w-10 text-stone-400" />}
                    <h2 className="mt-4 text-lg font-semibold text-stone-950">{busy === 'preview' ? 'Organizing your file…' : 'Drop your transactions or holdings file here'}</h2>
                    <p className="mt-1 text-sm text-stone-500">CSV, XLSX, or text-based CAS PDF. Nothing is saved until you approve the preview.</p>
                    <Button className="mt-5" variant="outline" disabled={busy !== null} onClick={() => inputRef.current?.click()}>Choose file</Button>
                    {file && <p className="mt-3 text-xs text-stone-500">Selected: {file.name} · {(file.size / 1024).toFixed(1)} KB</p>}
                </div>
            </section>

            {error && <div className="flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800"><AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />{error}</div>}

            {mappingDiagnostic && (
                <section className="rounded-2xl border border-amber-200 bg-amber-50/40 p-6 shadow-sm">
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
                        <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-stone-800">Advanced: map the columns myself <span className="font-normal text-stone-500">(optional)</span></summary>
                        <div className="border-t border-stone-100 p-4">
                    <p className="text-sm text-stone-600">Use this only if you know what the file&apos;s columns represent. Your original file will not be changed.</p>
                    <label className="mt-4 block text-sm font-medium text-stone-800" htmlFor="mapping-target">The rows in this file are</label>
                    <select
                        id="mapping-target"
                        value={selectedTarget}
                        onChange={(event) => changeTarget(event.target.value)}
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
                                        onChange={(event) => setManualMapping((current) => ({ ...current, [source]: event.target.value }))}
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
                </section>
            )}

            <details className="group rounded-2xl border border-stone-200 bg-white shadow-sm">
                <summary className="cursor-pointer list-none px-6 py-5 text-sm font-medium text-stone-800">
                    Prefer starting from a template? <span className="font-normal text-stone-500">Browse optional samples and guides</span>
                </summary>
                <div className="border-t border-stone-100 px-6 pb-6 pt-5">
                    <p className="text-sm text-stone-500">Templates remain available if you prefer a fixed layout. The same columns work in XLSX.</p>
                    <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                        {IMPORT_TEMPLATES.map((template) => (
                            <div key={template.id} className="flex flex-col rounded-xl border border-stone-200 bg-stone-50 p-4">
                                <h3 className="font-medium text-stone-950">{template.label}</h3>
                                <p className="mt-1 flex-1 text-xs leading-5 text-stone-500">{template.description}</p>
                                <Button className="mt-3 w-full" variant="outline" size="sm" asChild>
                                    <a href={`/import-templates/${template.id}`} download={template.filename}>
                                        <Download className="mr-2 h-4 w-4" />{template.downloadLabel ?? 'Download template'}
                                    </a>
                                </Button>
                            </div>
                        ))}
                    </div>
                </div>
            </details>
        </main></PageTransition></>
    );
}
