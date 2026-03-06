'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useUser } from '@/contexts/user-context';

export default function Home() {
    const router = useRouter();
    const { isAuthenticated, isLoading } = useUser();

    useEffect(() => {
        if (!isLoading) {
            if (isAuthenticated) {
                router.replace('/dashboard');
            } else {
                router.replace('/login');
            }
        }
    }, [isAuthenticated, isLoading, router]);

    return (
        <div className="flex min-h-screen items-center justify-center bg-gray-50">
            <div className="flex flex-col items-center gap-4">
                <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 shadow-lg shadow-blue-200">
                    <span className="text-2xl font-bold text-white">Q</span>
                </div>
                <div className="h-1.5 w-32 overflow-hidden rounded-full bg-gray-200">
                    <div className="h-full w-1/2 animate-pulse rounded-full bg-blue-500" />
                </div>
                <p className="text-sm text-gray-400">Loading QUANT...</p>
            </div>
        </div>
    );
}
