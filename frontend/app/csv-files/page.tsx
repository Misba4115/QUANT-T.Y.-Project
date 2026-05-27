'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Upload,
    FileSpreadsheet,
    Eye,
    EyeOff,
    Trash2,
    Table,
    ChevronLeft,
    ChevronRight,
    AlertCircle,
    CheckCircle2,
    ArrowLeft,
    FileWarning,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import Navbar from '@/components/layout/navbar';
import PageTransition from '@/components/layout/page-transition';
import { useUser } from '@/contexts/user-context';
import Papa from 'papaparse';
import { validateCSVSchema, type CSVValidationResult } from '@/services/csv-schema-validator';
import { classifyCSVData } from '@/services/csv-classifier';
import { syncHoldingsToBackend } from '@/services/holdings-sync';

// =====================
// Types
// =====================
interface CSVFile {
    id: string;
    name: string;
    uploadedAt: string;
    headers: string[];
    rows: string[][];
    rowCount: number;
    schemaType: string;
    schemaLabel: string;
    syncStats?: {
        equity: number;
        etf: number;
        mf: number;
        failed: number;
    };
}

const ROWS_PER_PAGE = 100;

export default function CSVFilesPage() {
    const router = useRouter();
    const { isAuthenticated, isLoading: authLoading } = useUser();
    const [csvFiles, setCsvFiles] = useState<CSVFile[]>([]);
    const [viewingFileId, setViewingFileId] = useState<string | null>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [validationResult, setValidationResult] = useState<CSVValidationResult | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Auth guard
    useEffect(() => {
        if (!authLoading && !isAuthenticated) {
            router.replace('/login');
        }
    }, [authLoading, isAuthenticated, router]);

    // Load saved files from localStorage
    useEffect(() => {
        try {
            const stored = localStorage.getItem('quant_csv_files');
            if (stored) setCsvFiles(JSON.parse(stored));
        } catch { /* ignore */ }
    }, []);

    // Persist to localStorage on change
    useEffect(() => {
        localStorage.setItem('quant_csv_files', JSON.stringify(csvFiles));
    }, [csvFiles]);

    const viewingFile = csvFiles.find(f => f.id === viewingFileId) || null;
    const totalPages = viewingFile ? Math.ceil(viewingFile.rows.length / ROWS_PER_PAGE) : 0;
    const paginatedRows = viewingFile
        ? viewingFile.rows.slice((currentPage - 1) * ROWS_PER_PAGE, currentPage * ROWS_PER_PAGE)
        : [];

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
        setValidationResult(null);

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

                // Step 1: Validate schema
                setUploadStatus('Validating schema...');
                const validation = validateCSVSchema(headers, rows);
                setValidationResult(validation);

                if (!validation.isValid) {
                    setError(`File rejected: ${validation.errors[0]}`);
                    setIsUploading(false);
                    return;
                }

                try {
                    // Step 2: Classify and sync if it's a holdings file
                    if (['equities', 'etfs', 'mutual_funds'].includes(validation.schemaType)) {
                        setUploadStatus('Classifying holdings...');
                        const classified = classifyCSVData(headers, rows);
                        const syncResult = await syncHoldingsToBackend(classified, (msg) => {
                            setUploadStatus(msg);
                        });

                        const csvFile: CSVFile = {
                            id: crypto.randomUUID(),
                            name: file.name,
                            uploadedAt: new Date().toLocaleString(),
                            headers,
                            rows,
                            rowCount: rows.length,
                            schemaType: validation.schemaType,
                            schemaLabel: validation.schemaLabel,
                            syncStats: {
                                equity: classified.equity.length,
                                etf: classified.etf.length,
                                mf: classified.mf.length,
                                failed: syncResult.failCount,
                            },
                        };
                        setCsvFiles(prev => [...prev, csvFile]);
                    } else {
                        // Crypto or transactions — just store
                        const csvFile: CSVFile = {
                            id: crypto.randomUUID(),
                            name: file.name,
                            uploadedAt: new Date().toLocaleString(),
                            headers,
                            rows,
                            rowCount: rows.length,
                            schemaType: validation.schemaType,
                            schemaLabel: validation.schemaLabel,
                        };
                        setCsvFiles(prev => [...prev, csvFile]);
                    }

                    setUploadStatus('');
                } catch (err: any) {
                    setError(`Sync failed: ${err.message || 'Unknown error'}`);
                } finally {
                    setIsUploading(false);
                }
            },
            error: (err) => {
                setError(`Failed to parse CSV: ${err.message}`);
                setIsUploading(false);
            },
        });

        if (fileInputRef.current) fileInputRef.current.value = '';
    }, []);

    const handleDelete = useCallback((id: string) => {
        setCsvFiles(prev => prev.filter(f => f.id !== id));
        if (viewingFileId === id) {
            setViewingFileId(null);
            setCurrentPage(1);
        }
    }, [viewingFileId]);

    const handleViewToggle = useCallback((id: string) => {
        if (viewingFileId === id) {
            setViewingFileId(null);
        } else {
            setViewingFileId(id);
            setCurrentPage(1);
        }
    }, [viewingFileId]);

    const schemaBadgeColors: Record<string, string> = {
        equities: 'bg-blue-50 text-blue-700 ring-blue-200',
        etfs: 'bg-amber-50 text-amber-700 ring-amber-200',
        mutual_funds: 'bg-purple-50 text-purple-700 ring-purple-200',
        crypto: 'bg-orange-50 text-orange-700 ring-orange-200',
        transactions: 'bg-green-50 text-green-700 ring-green-200',
    };

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
                        <h1 className="text-2xl font-bold text-gray-900">
                            CSV Files Manager
                        </h1>
                        <p className="mt-1 text-sm text-gray-500">
                            Upload and manage your financial data CSV files. Files are strictly validated against supported formats.
                        </p>
                    </div>

                    {/* Upload Area */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-8"
                    >
                        <input
                            type="file"
                            accept=".csv"
                            ref={fileInputRef}
                            onChange={handleFileUpload}
                            className="hidden"
                            id="csv-upload-page"
                        />
                        <label
                            htmlFor="csv-upload-page"
                            className="flex cursor-pointer flex-col items-center gap-3 rounded-xl border-2 border-dashed border-gray-200 bg-white p-10 transition-all hover:border-blue-300 hover:bg-blue-50/30 hover:shadow-sm"
                        >
                            <div className="rounded-full bg-blue-100 p-4">
                                <Upload className="h-7 w-7 text-blue-600" />
                            </div>
                            <div className="text-center">
                                <p className="text-sm font-semibold text-gray-700">
                                    {isUploading ? uploadStatus : 'Click to upload a CSV file'}
                                </p>
                                <p className="mt-1 text-xs text-gray-400">
                                    Supported: Equities, ETFs, Mutual Funds, Crypto Holdings, Bank Transactions
                                </p>
                            </div>
                        </label>
                    </motion.div>

                    {/* Error */}
                    <AnimatePresence>
                        {error && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="mb-6"
                            >
                                <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                                    <div className="flex items-start gap-3">
                                        <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 shrink-0" />
                                        <div>
                                            <p className="text-sm font-medium text-red-700">{error}</p>
                                            {validationResult && !validationResult.isValid && validationResult.errors.length > 1 && (
                                                <ul className="mt-2 space-y-1 text-xs text-red-600">
                                                    {validationResult.errors.slice(1).map((err, i) => (
                                                        <li key={i}>{err}</li>
                                                    ))}
                                                </ul>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Validation Success */}
                    <AnimatePresence>
                        {validationResult?.isValid && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="mb-6"
                            >
                                <div className="rounded-lg border border-green-200 bg-green-50 p-4 flex items-center gap-3">
                                    <CheckCircle2 className="h-5 w-5 text-green-600 shrink-0" />
                                    <p className="text-sm text-green-700">
                                        <span className="font-semibold">{validationResult.schemaLabel}</span> format detected —
                                        {' '}{validationResult.validRowCount} valid rows processed successfully.
                                    </p>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Files List */}
                    {csvFiles.length === 0 ? (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="rounded-xl border border-gray-100 bg-white p-12 text-center shadow-sm"
                        >
                            <FileWarning className="mx-auto h-12 w-12 text-gray-300" />
                            <h3 className="mt-4 text-lg font-semibold text-gray-700">No CSV files uploaded</h3>
                            <p className="mt-2 text-sm text-gray-400">
                                Upload a CSV file to see it here. Files are validated against supported financial data formats.
                            </p>
                        </motion.div>
                    ) : (
                        <div className="space-y-4">
                            <h2 className="text-lg font-bold text-gray-900">
                                Uploaded Files ({csvFiles.length})
                            </h2>
                            {csvFiles.map((file) => (
                                <motion.div
                                    key={file.id}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm transition-shadow hover:shadow-md"
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            <div className="rounded-lg bg-emerald-50 p-2.5">
                                                <FileSpreadsheet className="h-6 w-6 text-emerald-600" />
                                            </div>
                                            <div>
                                                <p className="text-sm font-semibold text-gray-800">{file.name}</p>
                                                <p className="text-xs text-gray-400">
                                                    {file.rowCount} rows • Uploaded {file.uploadedAt}
                                                </p>
                                                <div className="mt-1.5 flex flex-wrap gap-1.5">
                                                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1 ring-inset ${schemaBadgeColors[file.schemaType] || 'bg-gray-50 text-gray-600 ring-gray-200'}`}>
                                                        {file.schemaLabel}
                                                    </span>
                                                    {file.syncStats && (
                                                        <>
                                                            {file.syncStats.equity > 0 && (
                                                                <span className="inline-flex items-center rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-700 ring-1 ring-inset ring-blue-200">
                                                                    {file.syncStats.equity} Equity
                                                                </span>
                                                            )}
                                                            {file.syncStats.etf > 0 && (
                                                                <span className="inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-700 ring-1 ring-inset ring-amber-200">
                                                                    {file.syncStats.etf} ETF
                                                                </span>
                                                            )}
                                                            {file.syncStats.mf > 0 && (
                                                                <span className="inline-flex items-center rounded-full bg-purple-50 px-2 py-0.5 text-[10px] font-semibold text-purple-700 ring-1 ring-inset ring-purple-200">
                                                                    {file.syncStats.mf} Mutual Fund
                                                                </span>
                                                            )}
                                                            {file.syncStats.failed > 0 && (
                                                                <span className="inline-flex items-center rounded-full bg-red-50 px-2 py-0.5 text-[10px] font-semibold text-red-700 ring-1 ring-inset ring-red-200">
                                                                    {file.syncStats.failed} Failed
                                                                </span>
                                                            )}
                                                        </>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <Button
                                                size="sm"
                                                variant="outline"
                                                onClick={() => handleViewToggle(file.id)}
                                                className="gap-1.5"
                                            >
                                                {viewingFileId === file.id ? (
                                                    <><EyeOff className="h-3.5 w-3.5" /> Hide</>
                                                ) : (
                                                    <><Eye className="h-3.5 w-3.5" /> View</>
                                                )}
                                            </Button>
                                            <Button
                                                size="sm"
                                                variant="outline"
                                                onClick={() => handleDelete(file.id)}
                                                className="gap-1.5 text-red-500 hover:text-red-600 hover:border-red-200"
                                            >
                                                <Trash2 className="h-3.5 w-3.5" />
                                                Delete
                                            </Button>
                                        </div>
                                    </div>

                                    {/* Data Table View */}
                                    <AnimatePresence>
                                        {viewingFileId === file.id && viewingFile && (
                                            <motion.div
                                                initial={{ opacity: 0, height: 0 }}
                                                animate={{ opacity: 1, height: 'auto' }}
                                                exit={{ opacity: 0, height: 0 }}
                                                className="mt-5 overflow-hidden"
                                            >
                                                <div className="flex items-center justify-between mb-3">
                                                    <div className="flex items-center gap-2">
                                                        <Table className="h-4 w-4 text-blue-600" />
                                                        <h4 className="text-sm font-semibold text-gray-700">
                                                            {viewingFile.name}
                                                        </h4>
                                                        <span className="text-xs text-gray-400">
                                                            ({viewingFile.rowCount} total rows)
                                                        </span>
                                                    </div>
                                                </div>

                                                {/* Table */}
                                                <div className="overflow-auto rounded-lg border border-gray-200" style={{ maxHeight: '480px' }}>
                                                    <table className="w-full text-sm">
                                                        <thead className="sticky top-0 bg-gray-50 z-10">
                                                            <tr>
                                                                <th className="whitespace-nowrap border-b border-gray-200 px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-gray-400">
                                                                    #
                                                                </th>
                                                                {viewingFile.headers.map((header, i) => (
                                                                    <th
                                                                        key={i}
                                                                        className="whitespace-nowrap border-b border-gray-200 px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-gray-500"
                                                                    >
                                                                        {header}
                                                                    </th>
                                                                ))}
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {paginatedRows.map((row, ri) => (
                                                                <tr
                                                                    key={ri}
                                                                    className="border-b border-gray-50 transition-colors hover:bg-blue-50/30"
                                                                >
                                                                    <td className="whitespace-nowrap px-4 py-2 text-xs text-gray-400 font-mono">
                                                                        {(currentPage - 1) * ROWS_PER_PAGE + ri + 1}
                                                                    </td>
                                                                    {row.map((cell, ci) => (
                                                                        <td
                                                                            key={ci}
                                                                            className="whitespace-nowrap px-4 py-2 text-gray-700"
                                                                        >
                                                                            {cell}
                                                                        </td>
                                                                    ))}
                                                                </tr>
                                                            ))}
                                                        </tbody>
                                                    </table>
                                                </div>

                                                {/* Pagination */}
                                                {totalPages > 1 && (
                                                    <div className="mt-4 flex items-center justify-between">
                                                        <p className="text-xs text-gray-500">
                                                            Showing rows {(currentPage - 1) * ROWS_PER_PAGE + 1}–{Math.min(currentPage * ROWS_PER_PAGE, viewingFile.rowCount)} of {viewingFile.rowCount}
                                                        </p>
                                                        <div className="flex items-center gap-2">
                                                            <Button
                                                                size="sm"
                                                                variant="outline"
                                                                disabled={currentPage <= 1}
                                                                onClick={() => setCurrentPage(p => p - 1)}
                                                                className="gap-1"
                                                            >
                                                                <ChevronLeft className="h-4 w-4" />
                                                                Previous
                                                            </Button>
                                                            <span className="text-sm font-medium text-gray-600">
                                                                Page {currentPage} of {totalPages}
                                                            </span>
                                                            <Button
                                                                size="sm"
                                                                variant="outline"
                                                                disabled={currentPage >= totalPages}
                                                                onClick={() => setCurrentPage(p => p + 1)}
                                                                className="gap-1"
                                                            >
                                                                Next
                                                                <ChevronRight className="h-4 w-4" />
                                                            </Button>
                                                        </div>
                                                    </div>
                                                )}
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </motion.div>
                            ))}
                        </div>
                    )}
                </main>
            </PageTransition>
        </>
    );
}
