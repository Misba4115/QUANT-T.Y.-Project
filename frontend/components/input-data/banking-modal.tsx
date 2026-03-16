'use client';

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { IndianRupee } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
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
export interface LocalBankAccount {
    id: string;
    accountType: string;
    bankName: string;
    accountNickname: string;
    currentBalance: number;
    isPrimary: boolean;
}

const bankAccountSchema = z.object({
    accountType: z.string().min(1, 'Account type is required'),
    bankName: z.string().min(1, 'Bank name is required'),
    accountNickname: z.string().min(1, 'Account nickname is required'),
    currentBalance: z.string().min(1, 'Current balance is required'),
    isPrimary: z.boolean(),
});

type BankAccountForm = z.infer<typeof bankAccountSchema>;

interface BankingModalProps {
    open: boolean;
    onClose: () => void;
    onSave: (account: LocalBankAccount) => void;
}

export default function BankingModal({ open, onClose, onSave }: BankingModalProps) {
    const {
        register,
        handleSubmit,
        setValue,
        watch,
        reset,
        formState: { errors },
    } = useForm<BankAccountForm>({
        resolver: zodResolver(bankAccountSchema),
        defaultValues: {
            isPrimary: false,
            accountType: '',
        },
    });

    const isPrimary = watch('isPrimary');

    const onSubmit = (data: BankAccountForm) => {
        const account: LocalBankAccount = {
            id: crypto.randomUUID(),
            accountType: data.accountType,
            bankName: data.bankName,
            accountNickname: data.accountNickname,
            currentBalance: parseFloat(data.currentBalance),
            isPrimary: data.isPrimary,
        };
        onSave(account);
        reset();
        onClose();
    };

    return (
        <Dialog open={open} onOpenChange={(val) => { if (!val) onClose(); }}>
            <DialogContent className="sm:max-w-lg">
                <DialogHeader>
                    <DialogTitle>Add Bank Account</DialogTitle>
                    <DialogDescription>
                        Enter your bank account details below.
                    </DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 pt-2">
                    <div className="grid gap-4 sm:grid-cols-2">
                        {/* Account Type */}
                        <div className="space-y-2">
                            <Label className="text-sm font-medium text-gray-700">
                                Account Type
                            </Label>
                            <Select onValueChange={(val) => setValue('accountType', val)}>
                                <SelectTrigger className="h-11">
                                    <SelectValue placeholder="Select type" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="savings">Savings</SelectItem>
                                    <SelectItem value="current">Current</SelectItem>
                                    <SelectItem value="salary">Salary</SelectItem>
                                    <SelectItem value="fd">Fixed Deposit</SelectItem>
                                    <SelectItem value="rd">Recurring Deposit</SelectItem>
                                </SelectContent>
                            </Select>
                            {errors.accountType && (
                                <p className="text-xs text-red-500">{errors.accountType.message}</p>
                            )}
                        </div>

                        {/* Bank Name */}
                        <div className="space-y-2">
                            <Label className="text-sm font-medium text-gray-700">
                                Bank Name
                            </Label>
                            <Input
                                placeholder="HDFC, ICICI, SBI, etc..."
                                className="h-11"
                                {...register('bankName')}
                            />
                            {errors.bankName && (
                                <p className="text-xs text-red-500">{errors.bankName.message}</p>
                            )}
                        </div>
                    </div>

                    <div className="grid gap-4 sm:grid-cols-2">
                        {/* Account Nickname */}
                        <div className="space-y-2">
                            <Label className="text-sm font-medium text-gray-700">
                                Account Nickname
                            </Label>
                            <Input
                                placeholder="e.g. HDFC Main Savings"
                                className="h-11"
                                {...register('accountNickname')}
                            />
                            {errors.accountNickname && (
                                <p className="text-xs text-red-500">{errors.accountNickname.message}</p>
                            )}
                        </div>

                        {/* Current Balance */}
                        <div className="space-y-2">
                            <Label className="text-sm font-medium text-gray-700">
                                Current Balance
                            </Label>
                            <div className="relative">
                                <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400">
                                    <IndianRupee className="h-4 w-4" />
                                </div>
                                <Input
                                    type="number"
                                    placeholder="0"
                                    className="h-11 pl-10"
                                    {...register('currentBalance')}
                                />
                            </div>
                            {errors.currentBalance && (
                                <p className="text-xs text-red-500">{errors.currentBalance.message}</p>
                            )}
                        </div>
                    </div>

                    {/* Primary Toggle */}
                    <div className="flex items-center gap-3">
                        <Switch
                            checked={isPrimary}
                            onCheckedChange={(val) => setValue('isPrimary', val)}
                        />
                        <Label className="text-sm text-gray-600">
                            Set as primary account
                        </Label>
                    </div>

                    {/* Buttons */}
                    <div className="flex items-center gap-3 pt-2">
                        <Button
                            type="submit"
                            className="bg-gradient-to-r from-blue-600 to-indigo-600 px-8 text-white shadow-md shadow-blue-200 hover:shadow-lg hover:shadow-blue-300"
                        >
                            Add Account
                        </Button>
                        <Button type="button" variant="outline" className="px-8" onClick={onClose}>
                            Cancel
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
}
