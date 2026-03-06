'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { User, Bell, Shield, Palette, HelpCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import Navbar from '@/components/layout/navbar';
import PageTransition from '@/components/layout/page-transition';
import { useUser } from '@/contexts/user-context';

export default function SettingsPage() {
    const { user } = useUser();

    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: { staggerChildren: 0.08 },
        },
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
    };

    return (
        <>
            <Navbar />
            <PageTransition>
                <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
                    <motion.div
                        variants={containerVariants}
                        initial="hidden"
                        animate="visible"
                        className="space-y-8"
                    >
                        <motion.div variants={itemVariants}>
                            <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
                            <p className="mt-1 text-gray-500">
                                Manage your account preferences and configurations
                            </p>
                        </motion.div>

                        {/* Profile Section */}
                        <motion.div
                            variants={itemVariants}
                            className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm"
                        >
                            <div className="mb-4 flex items-center gap-2">
                                <User className="h-5 w-5 text-blue-600" />
                                <h2 className="text-lg font-semibold text-gray-900">
                                    Profile Information
                                </h2>
                            </div>
                            <div className="space-y-4">
                                <div className="grid gap-4 sm:grid-cols-2">
                                    <div className="space-y-2">
                                        <Label className="text-sm text-gray-700">Full Name</Label>
                                        <Input
                                            defaultValue={user?.fullName || ''}
                                            placeholder="Your full name"
                                            className="h-11"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label className="text-sm text-gray-700">Email</Label>
                                        <Input
                                            defaultValue={user?.email || ''}
                                            placeholder="you@example.com"
                                            className="h-11"
                                            disabled
                                        />
                                    </div>
                                </div>
                                <Button className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-200">
                                    Save Changes
                                </Button>
                            </div>
                        </motion.div>

                        {/* Notifications */}
                        <motion.div
                            variants={itemVariants}
                            className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm"
                        >
                            <div className="mb-4 flex items-center gap-2">
                                <Bell className="h-5 w-5 text-blue-600" />
                                <h2 className="text-lg font-semibold text-gray-900">
                                    Notifications
                                </h2>
                            </div>
                            <div className="space-y-4">
                                {[
                                    {
                                        label: 'Email Notifications',
                                        desc: 'Receive portfolio updates via email',
                                    },
                                    {
                                        label: 'Price Alerts',
                                        desc: 'Get notified when assets hit target prices',
                                    },
                                    {
                                        label: 'Weekly Summary',
                                        desc: 'Receive a weekly financial summary',
                                    },
                                ].map((item) => (
                                    <div
                                        key={item.label}
                                        className="flex items-center justify-between"
                                    >
                                        <div>
                                            <p className="text-sm font-medium text-gray-900">
                                                {item.label}
                                            </p>
                                            <p className="text-xs text-gray-400">{item.desc}</p>
                                        </div>
                                        <Switch defaultChecked />
                                    </div>
                                ))}
                            </div>
                        </motion.div>

                        <Separator />

                        {/* Security */}
                        <motion.div
                            variants={itemVariants}
                            className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm"
                        >
                            <div className="mb-4 flex items-center gap-2">
                                <Shield className="h-5 w-5 text-blue-600" />
                                <h2 className="text-lg font-semibold text-gray-900">
                                    Security
                                </h2>
                            </div>
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm font-medium text-gray-900">
                                            Two-Factor Authentication
                                        </p>
                                        <p className="text-xs text-gray-400">
                                            Add an extra layer of security
                                        </p>
                                    </div>
                                    <Switch />
                                </div>
                                <Button variant="outline">Change Password</Button>
                            </div>
                        </motion.div>

                        {/* Preferences */}
                        <motion.div
                            variants={itemVariants}
                            className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm"
                        >
                            <div className="mb-4 flex items-center gap-2">
                                <Palette className="h-5 w-5 text-blue-600" />
                                <h2 className="text-lg font-semibold text-gray-900">
                                    Preferences
                                </h2>
                            </div>
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-gray-900">
                                        Dark Mode
                                    </p>
                                    <p className="text-xs text-gray-400">
                                        Switch to dark theme (Coming soon)
                                    </p>
                                </div>
                                <Switch disabled />
                            </div>
                        </motion.div>

                        {/* Help */}
                        <motion.div
                            variants={itemVariants}
                            className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm"
                        >
                            <div className="mb-4 flex items-center gap-2">
                                <HelpCircle className="h-5 w-5 text-blue-600" />
                                <h2 className="text-lg font-semibold text-gray-900">
                                    Help & Support
                                </h2>
                            </div>
                            <p className="text-sm text-gray-500">
                                Need help? Use the Quant Assistant chatbot or email us at{' '}
                                <a
                                    href="mailto:support@quant.app"
                                    className="font-medium text-blue-600 hover:text-blue-700"
                                >
                                    support@quant.app
                                </a>
                            </p>
                        </motion.div>
                    </motion.div>
                </main>
            </PageTransition>
        </>
    );
}
