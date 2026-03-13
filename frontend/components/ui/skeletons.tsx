'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

export function SkeletonCard({ className = '' }: { className?: string }) {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className={`animate-pulse rounded-xl border border-gray-100 bg-white p-6 ${className}`}
        >
            <div className="mb-4 h-4 w-3/4 rounded bg-gray-200" />
            <div className="mb-2 h-8 w-1/2 rounded bg-gray-200" />
            <div className="h-3 w-1/3 rounded bg-gray-100" />
        </motion.div>
    );
}

export function SkeletonChart({ className = '' }: { className?: string }) {
    const [heights, setHeights] = useState<number[]>();

    useEffect(() => {
        setHeights(Array.from({ length: 12 }).map(() => 30 + Math.random() * 70));
    }, []);

    const barHeights = heights || Array.from({ length: 12 }).map(() => 50);

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className={`animate-pulse rounded-xl border border-gray-100 bg-white p-6 ${className}`}
        >
            <div className="mb-4 h-4 w-1/3 rounded bg-gray-200" />
            <div className="flex h-48 items-end gap-2">
                {barHeights.map((h, i) => (
                    <div
                        key={i}
                        className="flex-1 rounded-t bg-gray-100"
                        style={{ height: `${h}%` }}
                    />
                ))}
            </div>
        </motion.div>
    );
}

export function SkeletonTable({ className = '' }: { className?: string }) {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className={`animate-pulse rounded-xl border border-gray-100 bg-white p-6 ${className}`}
        >
            <div className="mb-4 h-4 w-1/4 rounded bg-gray-200" />
            {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="mb-3 flex gap-4">
                    <div className="h-4 flex-1 rounded bg-gray-100" />
                    <div className="h-4 w-20 rounded bg-gray-100" />
                    <div className="h-4 w-16 rounded bg-gray-100" />
                    <div className="h-4 w-24 rounded bg-gray-100" />
                </div>
            ))}
        </motion.div>
    );
}
