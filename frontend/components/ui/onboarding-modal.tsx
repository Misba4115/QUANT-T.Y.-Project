'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldCheck, Sparkles, UserCheck, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useUser } from '@/contexts/user-context';

const cards = [
    {
        icon: ShieldCheck,
        title: 'Private & Isolated',
        description: 'Your data is encrypted in transit and at rest. Nothing ever leaves your secure session — all processing happens within your private, isolated environment.',
        color: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    },
    {
        icon: Sparkles,
        title: 'Smart Financial Structuring',
        description: 'Your CSV and CAS statements are automatically organized into clear, readable summaries. Raw transaction trails are never stored or exposed — only structured insights.',
        color: 'bg-stone-50 text-stone-700 border-stone-200',
    },
    {
        icon: UserCheck,
        title: '100% User Control',
        description: 'You retain complete ownership of your data at all times. Permanently delete everything with a single click — no questions asked, no residual copies.',
        color: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    },
];

export function OnboardingModal() {
    const { completeOnboarding } = useUser();
    const [dismissed, setDismissed] = useState(false);
    const [suppressForSession, setSuppressForSession] = useState(false);

    const handleDismiss = () => {
        setDismissed(true);
        if (suppressForSession) {
            sessionStorage.setItem('quant_onboarding_dismissed', 'true');
        }
        completeOnboarding();
    };

    if (dismissed || sessionStorage.getItem('quant_onboarding_dismissed') === 'true') {
        return null;
    }

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
            >
                <motion.div
                    initial={{ scale: 0.95, opacity: 0, y: 20 }}
                    animate={{ scale: 1, opacity: 1, y: 0 }}
                    exit={{ scale: 0.95, opacity: 0 }}
                    transition={{ duration: 0.3, ease: 'easeOut' }}
                    className="w-full max-w-2xl rounded-2xl border border-stone-200 bg-white p-8 shadow-2xl"
                >
                    <div className="text-center mb-6">
                        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50">
                            <ShieldCheck className="h-6 w-6 text-emerald-700" />
                        </div>
                        <h2 className="mt-4 text-xl font-semibold text-stone-900">How We Protect & Process Your Financial Data</h2>
                        <p className="mt-2 text-sm text-stone-500">Your privacy and security are built into every layer of QUANT.</p>
                    </div>

                    <div className="grid gap-4 sm:grid-cols-3">
                        {cards.map((card, index) => (
                            <motion.div
                                key={card.title}
                                initial={{ opacity: 0, y: 15 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.1 + index * 0.1 }}
                                className={`rounded-xl border p-5 ${card.color}`}
                            >
                                <card.icon className="h-6 w-6 mb-3" />
                                <h3 className="font-semibold text-sm">{card.title}</h3>
                                <p className="mt-2 text-xs leading-relaxed opacity-80">{card.description}</p>
                            </motion.div>
                        ))}
                    </div>

                    <div className="mt-6 flex flex-col items-center gap-3">
                        <Button
                            onClick={handleDismiss}
                            className="bg-emerald-800 text-white hover:bg-emerald-900 px-8"
                        >
                            Continue to Dashboard
                            <ArrowRight className="ml-2 h-4 w-4" />
                        </Button>
                        <label className="flex items-center gap-2 text-xs text-stone-500 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={suppressForSession}
                                onChange={(e) => setSuppressForSession(e.target.checked)}
                                className="h-3.5 w-3.5 rounded border-stone-300 text-emerald-700"
                            />
                            Don&apos;t show again this session
                        </label>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}
