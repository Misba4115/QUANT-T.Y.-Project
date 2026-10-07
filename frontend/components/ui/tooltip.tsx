'use client';

import { useState } from 'react';
import { Info } from 'lucide-react';
import { Tooltip as TooltipPrimitive } from 'radix-ui';

export function InfoTooltip({ content }: { content: string }) {
    const [open, setOpen] = useState(false);

    return (
        <TooltipPrimitive.Provider delayDuration={150}>
            <TooltipPrimitive.Root open={open} onOpenChange={setOpen}>
                <TooltipPrimitive.Trigger asChild onClick={(event) => { event.preventDefault(); setOpen(true); }}>
                    <button type="button" aria-label="More information" className="inline-flex shrink-0 cursor-help items-center rounded-full p-1 text-stone-500 hover:text-emerald-700 focus-visible:outline-2 focus-visible:outline-emerald-700">
                        <Info aria-hidden="true" className="h-3.5 w-3.5" />
                    </button>
                </TooltipPrimitive.Trigger>
                <TooltipPrimitive.Portal>
                    <TooltipPrimitive.Content side="top" sideOffset={5} collisionPadding={12} className="z-[10000] max-w-[calc(100vw-24px)] w-64 rounded-lg border border-stone-200 bg-white px-3 py-2.5 text-xs font-normal normal-case leading-relaxed tracking-normal text-stone-700 shadow-lg">
                        {content}
                        <TooltipPrimitive.Arrow className="fill-white" />
                    </TooltipPrimitive.Content>
                </TooltipPrimitive.Portal>
            </TooltipPrimitive.Root>
        </TooltipPrimitive.Provider>
    );
}
