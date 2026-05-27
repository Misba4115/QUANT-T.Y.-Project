'use client';

import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileSpreadsheet, Eye, Trash2, Table } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from '@/components/ui/dialog';
import Papa from 'papaparse';
import { classifyCSVData, type ClassificationResult } from '@/services/csv-classifier';
import { syncHoldingsToBackend } from '@/services/holdings-sync';

// =====================
// Types
// =====================
export interface CSVFile {
    id: string;
    name: string;
    uploadedAt: string;
    headers: string[];
    rows: string[][];
    rowCount: number;
    syncStats?: {
        equity: number;
        etf: number;
        mf: number;
        failed: number;
    };
}

interface InvestmentsPanelProps {
    open: boolean;
    onClose: () => void;
    csvFiles: CSVFile[];
    onFilesChange: (files: CSVFile[]) => void;
}

export default function InvestmentsPanel({
    open,
    onClose,
    csvFiles,
    onFilesChange,
}: InvestmentsPanelProps) {
    const [viewingFile, setViewingFile] = useState<CSVFile | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState<string>('');
    const [error, setError] = useState<string | null>(null);
    const [pendingFiles, setPendingFiles] = useState<{ id: string; name: string; headers: string[]; rows: string[][] }[]>([]);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files || []);
        if (files.length === 0) return;

        setIsUploading(true);
        setError(null);
        
        const errors: string[] = [];
        const newPending: { id: string; name: string; headers: string[]; rows: string[][] }[] = [];

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (!file.name.endsWith('.csv')) {
                errors.push(`${file.name}: Not a CSV file.`);
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
                                errors.push(`${file.name}: Needs at least a header and one row.`);
                                return resolve();
                            }

                            newPending.push({
                                id: crypto.randomUUID(),
                                name: file.name,
                                headers: data[0],
                                rows: data.slice(1)
                            });
                        } catch (err: any) {
                            errors.push(`${file.name}: Parsing failed (${err.message})`);
                        }
                        resolve();
                    },
                    error: (err) => {
                        errors.push(`${file.name}: Parse failed (${err.message})`);
                        resolve();
                    }
                });
            });
        }

        if (newPending.length > 0) {
            setPendingFiles(prev => [...prev, ...newPending]);
        }
        
        if (errors.length > 0) {
            setError(errors.join('\n'));
        }
        
        setIsUploading(false);
        setUploadStatus('');

        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const handleSavePendingFiles = async () => {
        if (pendingFiles.length === 0) return;
        setIsUploading(true);
        setError(null);
        
        const newCsvFiles: CSVFile[] = [];
        const errors: string[] = [];

        for (const file of pendingFiles) {
            setUploadStatus(`Classifying ${file.name}...`);
            try {
                const classified = classifyCSVData(file.headers, file.rows);

                const syncResult = await syncHoldingsToBackend(classified, (msg) => {
                    setUploadStatus(`${file.name}: ${msg}`);
                });

                newCsvFiles.push({
                    id: file.id,
                    name: file.name,
                    uploadedAt: new Date().toLocaleString(),
                    headers: file.headers,
                    rows: file.rows,
                    rowCount: file.rows.length,
                    syncStats: {
                        equity: classified.equity.length,
                        etf: classified.etf.length,
                        mf: classified.mf.length,
                        failed: syncResult.failCount,
                    }
                });
            } catch (err: any) {
                console.error("Sync error:", err);
                errors.push(`${file.name}: Sync failed (${err.message || 'Unknown'})`);
            }
        }

        if (newCsvFiles.length > 0) {
            onFilesChange([...csvFiles, ...newCsvFiles]);
        }
        
        if (errors.length > 0) {
            setError(errors.join('\n'));
        }
        
        setPendingFiles([]);
        setIsUploading(false);
        setUploadStatus('');
    };

    const handleDelete = (id: string) => {
        onFilesChange(csvFiles.filter((f) => f.id !== id));
        if (viewingFile?.id === id) {
            setViewingFile(null);
        }
    };

    return (
        <Dialog open={open} onOpenChange={(val) => { if (!val) { onClose(); setViewingFile(null); } }}>
            <DialogContent className="sm:max-w-5xl max-h-[85vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Investments — CSV Upload</DialogTitle>
                    <DialogDescription>
                        Upload CSV files containing your investment data.
                    </DialogDescription>
                </DialogHeader>

                {/* Upload Area */}
                <div className="mt-2">
                    <input
                        type="file"
                        accept=".csv"
                        ref={fileInputRef}
                        onChange={handleFileUpload}
                        className="hidden"
                        id="csv-upload"
                        multiple
                    />
                    <label
                        htmlFor="csv-upload"
                        className="flex cursor-pointer flex-col items-center gap-3 rounded-xl border-2 border-dashed border-gray-200 bg-gray-50/50 p-8 transition-colors hover:border-blue-300 hover:bg-blue-50/30"
                    >
                        <div className="rounded-full bg-blue-100 p-3">
                            <Upload className="h-6 w-6 text-blue-600" />
                        </div>
                        <div className="text-center">
                            <p className="text-sm font-semibold text-gray-700">
                                {isUploading && pendingFiles.length === 0 ? uploadStatus : 'Click to upload CSV file(s)'}
                            </p>
                            <p className="mt-1 text-xs text-gray-400">
                                Supports .csv files with headers
                            </p>
                        </div>
                    </label>
                </div>

                {pendingFiles.length > 0 && (
                    <div className="mt-4 space-y-3">
                        <h3 className="text-sm font-semibold text-gray-700">Pending Files to Save</h3>
                        {pendingFiles.map(pf => (
                            <div key={pf.id} className="flex items-center justify-between bg-blue-50 border border-blue-100 p-3 rounded-lg">
                                <div className="flex items-center gap-2">
                                    <FileSpreadsheet className="h-4 w-4 text-blue-500" />
                                    <span className="text-sm font-medium text-gray-800">{pf.name}</span>
                                </div>
                                <span className="text-xs text-gray-500">{pf.rows.length} rows</span>
                            </div>
                        ))}
                        <Button
                            onClick={handleSavePendingFiles}
                            disabled={isUploading}
                            className="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white"
                        >
                            {isUploading ? (
                                <>{uploadStatus || 'Saving...'}</>
                            ) : (
                                "Save Data to Portfolio"
                            )}
                        </Button>
                    </div>
                )}

                {error && (
                    <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                        {error}
                    </div>
                )}

                {/* Uploaded Files List */}
                {csvFiles.length > 0 && (
                    <div className="mt-4 space-y-3">
                        <h3 className="text-sm font-semibold text-gray-700">
                            Uploaded Files ({csvFiles.length})
                        </h3>
                        {csvFiles.map((file) => (
                            <motion.div
                                key={file.id}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="flex items-center justify-between rounded-lg border border-gray-100 bg-white p-4 shadow-sm"
                            >
                                <div className="flex items-center gap-3">
                                    <div className="rounded-lg bg-emerald-50 p-2">
                                        <FileSpreadsheet className="h-5 w-5 text-emerald-600" />
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium text-gray-800">{file.name}</p>
                                        <p className="text-xs text-gray-400">
                                            {file.rowCount} rows • Uploaded {file.uploadedAt}
                                        </p>
                                        {file.syncStats && (
                                            <div className="mt-1.5 flex flex-wrap gap-1.5">
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
                                            </div>
                                        )}
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => setViewingFile(viewingFile?.id === file.id ? null : file)}
                                        className="gap-1.5"
                                    >
                                        <Eye className="h-3.5 w-3.5" />
                                        {viewingFile?.id === file.id ? 'Hide' : 'View'}
                                    </Button>
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => handleDelete(file.id)}
                                        className="gap-1.5 text-red-500 hover:text-red-600"
                                    >
                                        <Trash2 className="h-3.5 w-3.5" />
                                    </Button>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                )}

                {/* Data Table View */}
                <AnimatePresence>
                    {viewingFile && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="mt-4 overflow-hidden"
                        >
                            <div className="flex items-center gap-2 mb-3">
                                <Table className="h-4 w-4 text-blue-600" />
                                <h4 className="text-sm font-semibold text-gray-700">
                                    {viewingFile.name}
                                </h4>
                            </div>
                            <div className="max-h-64 overflow-auto rounded-lg border border-gray-200">
                                <table className="w-full text-sm">
                                    <thead className="sticky top-0 bg-gray-50">
                                        <tr>
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
                                        {viewingFile.rows.slice(0, 50).map((row, ri) => (
                                            <tr
                                                key={ri}
                                                className="border-b border-gray-50 transition-colors hover:bg-blue-50/30"
                                            >
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
                                {viewingFile.rows.length > 50 && (
                                    <div className="bg-gray-50 px-4 py-2 text-center text-xs text-gray-400">
                                        Showing first 50 of {viewingFile.rows.length} rows
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </DialogContent>
        </Dialog>
    );
}
