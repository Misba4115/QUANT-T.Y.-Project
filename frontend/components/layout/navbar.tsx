'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import {
    Bell,
    ChevronDown,
    LogOut,
    Settings,
    User as UserIcon,
} from 'lucide-react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { useUser } from '@/contexts/user-context';
import { getInitials } from '@/lib/helpers';
import { notificationsApi } from '@/lib/api';

const navLinks = [
    { label: 'Input Data', href: '/input-data' },
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Guardian', href: '/guardian' },
    { label: 'Settings', href: '/settings' },
];

export default function Navbar() {
    const pathname = usePathname();
    const { user, logout } = useUser();
    const [unreadNotifications, setUnreadNotifications] = useState(0);

    useEffect(() => {
        if (!user) return;
        void notificationsApi.list().then((response) => {
            setUnreadNotifications(response.data.filter((item) => !item.read_at).length);
        }).catch(() => undefined);
    }, [user]);

    const displayName = user?.name || 'Guest User';
    const initials = getInitials(displayName);

    return (
        <motion.header
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
            className="sticky top-0 z-50 w-full border-b border-gray-100 bg-white/80 backdrop-blur-xl"
        >
            <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
                {/* Logo */}
                <Link href="/dashboard" className="flex items-center gap-2.5">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 shadow-md shadow-blue-200">
                        <span className="text-lg font-bold text-white">Q</span>
                    </div>
                    <div className="flex flex-col">
                        <span className="text-xl font-bold tracking-tight text-gray-900">
                            QUANT
                        </span>
                        <span className="hidden text-[10px] leading-none text-gray-400 sm:block">
                            Smart Financial Intelligence
                        </span>
                    </div>
                </Link>

                {/* Nav Links */}
                <nav className="hidden items-center gap-1 md:flex">
                    {navLinks.map((link) => {
                        const isActive = pathname === link.href;
                        return (
                            <Link
                                key={link.href}
                                href={link.href}
                                className="relative px-4 py-2 text-sm font-medium transition-colors"
                            >
                                <span
                                    className={
                                        isActive
                                            ? 'text-blue-600'
                                            : 'text-gray-600 hover:text-gray-900'
                                    }
                                >
                                    {link.label}
                                </span>
                                {isActive && (
                                    <motion.div
                                        layoutId="navbar-indicator"
                                        className="absolute inset-x-2 -bottom-[13px] h-0.5 rounded-full bg-blue-600"
                                        transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                                    />
                                )}
                            </Link>
                        );
                    })}
                </nav>

                {/* Right Section */}
                <div className="flex items-center gap-3">
                    {/* Notifications */}
                    <Link
                        href="/notifications"
                        className="relative rounded-full p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700"
                        aria-label="Notifications"
                    >
                        <Bell className="h-5 w-5" />
                        {unreadNotifications > 0 && (
                            <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-red-500 ring-2 ring-white" />
                        )}
                    </Link>

                    {/* User Dropdown */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <button className="flex items-center gap-2 rounded-full py-1 pl-1 pr-3 transition-colors hover:bg-gray-50">
                                <Avatar className="h-8 w-8 border-2 border-blue-100">
                                    <AvatarFallback className="bg-gradient-to-br from-blue-500 to-indigo-500 text-xs font-semibold text-white">
                                        {initials}
                                    </AvatarFallback>
                                </Avatar>
                                <span className="hidden text-sm font-medium text-gray-700 sm:block">
                                    {displayName.split(' ')[0]}{' '}
                                    {displayName.split(' ')[1]?.[0]
                                        ? displayName.split(' ')[1][0] + '.'
                                        : ''}
                                </span>
                                <ChevronDown className="h-3.5 w-3.5 text-gray-400" />
                            </button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-48">
                            <DropdownMenuItem asChild>
                                <Link href="/settings" className="flex items-center gap-2">
                                    <UserIcon className="h-4 w-4" />
                                    <span>Profile</span>
                                </Link>
                            </DropdownMenuItem>
                            <DropdownMenuItem asChild>
                                <Link href="/settings" className="flex items-center gap-2">
                                    <Settings className="h-4 w-4" />
                                    <span>Settings</span>
                                </Link>
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                                onClick={logout}
                                className="flex items-center gap-2 text-red-600 focus:text-red-600"
                            >
                                <LogOut className="h-4 w-4" />
                                <span>Log out</span>
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>

                    {/* Mobile Nav */}
                    <div className="flex items-center md:hidden">
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild><button aria-label="Open navigation"><Badge variant="outline" className="text-xs">Menu</Badge></button></DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                                {navLinks.map((link) => <DropdownMenuItem key={link.href} asChild><Link href={link.href}>{link.label}</Link></DropdownMenuItem>)}
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                </div>
            </div>
        </motion.header>
    );
}
