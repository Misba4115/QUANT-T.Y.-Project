'use client';

import React, { useState } from 'react';
import { Info } from 'lucide-react';

interface InfoTooltipProps {
    content: string;
}

export function InfoTooltip({ content }: InfoTooltipProps) {
    const [visible, setVisible] = useState(false);

    return (
        <span
            className="relative inline-flex cursor-help"
            onMouseEnter={() => setVisible(true)}
            onMouseLeave={() => setVisible(false)}
            onFocus={() => setVisible(true)}
            onBlur={() => setVisible(false)}
            tabIndex={0}
            role="button"
            aria-label="More information"
        >
            <Info className="h-3.5 w-3.5 text-stone-400 hover:text-emerald-600 transition-colors" />
            {visible && (
                <span className="absolute bottom-full left-1/2 z-50 mb-2 w-64 -translate-x-1/2 rounded-lg border border-stone-200 bg-white px-3 py-2.5 text-xs leading-relaxed text-stone-600 shadow-lg shadow-stone-200/50">
                    {content}
                    <span className="absolute -bottom-1 left-1/2 h-2 w-2 -translate-x-1/2 rotate-45 border-b border-r border-stone-200 bg-white" />
                </span>
            )}
        </span>
    );
}
