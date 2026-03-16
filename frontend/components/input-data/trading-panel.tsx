'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link2, CheckCircle2, ExternalLink, Unlink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from '@/components/ui/dialog';

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
}

const BROKERAGES: Omit<TradingAccount, 'connected' | 'connectedAt' | 'accountId'>[] = [
    { id: 'zerodha', platform: 'Zerodha Kite', icon: 'Z', color: 'text-green-700', bgColor: 'bg-green-50 border-green-200' },
    { id: 'groww', platform: 'Groww', icon: 'G', color: 'text-blue-700', bgColor: 'bg-blue-50 border-blue-200' },
    { id: 'upstox', platform: 'Upstox', icon: 'U', color: 'text-purple-700', bgColor: 'bg-purple-50 border-purple-200' },
    { id: 'angelone', platform: 'Angel One', icon: 'A', color: 'text-red-700', bgColor: 'bg-red-50 border-red-200' },
    { id: 'icici_direct', platform: 'ICICI Direct', icon: 'I', color: 'text-orange-700', bgColor: 'bg-orange-50 border-orange-200' },
    { id: '5paisa', platform: '5Paisa', icon: '5', color: 'text-teal-700', bgColor: 'bg-teal-50 border-teal-200' },
];

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
    const [connecting, setConnecting] = useState<string | null>(null);

    const handleConnect = async (brokerage: typeof BROKERAGES[0]) => {
        setConnecting(brokerage.id);

        // Simulate connection delay
        await new Promise((r) => setTimeout(r, 1500));

        const account: TradingAccount = {
            ...brokerage,
            connected: true,
            connectedAt: new Date().toLocaleString(),
            accountId: `${brokerage.id.toUpperCase()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`,
        };

        const existing = connectedAccounts.filter((a) => a.id !== brokerage.id);
        onAccountsChange([...existing, account]);
        setConnecting(null);
    };

    const handleDisconnect = (id: string) => {
        onAccountsChange(connectedAccounts.filter((a) => a.id !== id));
    };

    const isConnected = (id: string) => connectedAccounts.some((a) => a.id === id);

    return (
        <Dialog open={open} onOpenChange={(val) => { if (!val) onClose(); }}>
            <DialogContent className="sm:max-w-xl max-h-[85vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Trading Accounts</DialogTitle>
                    <DialogDescription>
                        Connect your brokerage accounts to sync trading data. (Simulated — no real API calls)
                    </DialogDescription>
                </DialogHeader>

                <div className="mt-4 space-y-3">
                    {BROKERAGES.map((broker) => {
                        const connected = isConnected(broker.id);
                        const account = connectedAccounts.find((a) => a.id === broker.id);
                        const isLoading = connecting === broker.id;

                        return (
                            <motion.div
                                key={broker.id}
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={`flex items-center justify-between rounded-xl border p-4 transition-all ${
                                    connected
                                        ? `${broker.bgColor} shadow-sm`
                                        : 'border-gray-100 bg-white hover:border-gray-200'
                                }`}
                            >
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
                                            {broker.platform}
                                        </p>
                                        {connected && account ? (
                                            <p className="text-xs text-gray-500">
                                                ID: {account.accountId} • Connected {account.connectedAt}
                                            </p>
                                        ) : (
                                            <p className="text-xs text-gray-400">Not connected</p>
                                        )}
                                    </div>
                                </div>

                                {connected ? (
                                    <div className="flex items-center gap-2">
                                        <span className="flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-1 text-xs font-medium text-green-700">
                                            <CheckCircle2 className="h-3 w-3" />
                                            Connected
                                        </span>
                                        <Button
                                            size="sm"
                                            variant="outline"
                                            onClick={() => handleDisconnect(broker.id)}
                                            className="gap-1 text-red-500 hover:text-red-600"
                                        >
                                            <Unlink className="h-3.5 w-3.5" />
                                        </Button>
                                    </div>
                                ) : (
                                    <Button
                                        size="sm"
                                        onClick={() => handleConnect(broker)}
                                        disabled={isLoading}
                                        className="gap-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white"
                                    >
                                        {isLoading ? (
                                            <>
                                                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                                </svg>
                                                Connecting...
                                            </>
                                        ) : (
                                            <>
                                                <Link2 className="h-3.5 w-3.5" />
                                                Connect
                                            </>
                                        )}
                                    </Button>
                                )}
                            </motion.div>
                        );
                    })}
                </div>

                {/* Connected Summary */}
                {connectedAccounts.length > 0 && (
                    <div className="mt-4 rounded-lg border border-blue-100 bg-blue-50/50 p-4">
                        <p className="text-sm font-medium text-blue-800">
                            {connectedAccounts.length} account{connectedAccounts.length > 1 ? 's' : ''} connected
                        </p>
                        <p className="mt-1 text-xs text-blue-600">
                            Your trading data will be synced once backend integration is live.
                        </p>
                    </div>
                )}
            </DialogContent>
        </Dialog>
    );
}
