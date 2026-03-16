'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Target, ChevronRight, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
export interface GoalsData {
    riskTolerance: string;
    investmentHorizon: string;
    monthlyCapacity: string;
    goalType: string;
    targetAmount?: string;
    targetDate?: string;
    // retirement-specific
    retirementAge?: string;
    currentAge?: string;
    // education-specific
    childAge?: string;
    educationType?: string;
    // emergency fund-specific
    monthsOfExpenses?: string;
}

const RISK_OPTIONS = [
    { value: 'conservative', label: 'Conservative', desc: 'Capital preservation, minimal risk' },
    { value: 'moderate', label: 'Moderate', desc: 'Balanced growth with some risk' },
    { value: 'aggressive', label: 'Aggressive', desc: 'High growth, comfortable with volatility' },
    { value: 'very_aggressive', label: 'Very Aggressive', desc: 'Maximum returns, high risk tolerance' },
];

const HORIZON_OPTIONS = [
    { value: 'short', label: 'Short Term', desc: '< 2 years' },
    { value: 'medium', label: 'Medium Term', desc: '2–5 years' },
    { value: 'long', label: 'Long Term', desc: '5–10 years' },
    { value: 'very_long', label: 'Very Long Term', desc: '10+ years' },
];

const GOAL_TYPES = [
    { value: 'retirement', label: 'Retirement Planning' },
    { value: 'wealth', label: 'Wealth Building' },
    { value: 'education', label: 'Education Fund' },
    { value: 'home', label: 'Home Purchase' },
    { value: 'emergency', label: 'Emergency Fund' },
    { value: 'travel', label: 'Travel / Vacation' },
    { value: 'other', label: 'Other' },
];

interface GoalsPanelProps {
    open: boolean;
    onClose: () => void;
    goalsData: GoalsData | null;
    onSave: (data: GoalsData) => void;
}

export default function GoalsPanel({ open, onClose, goalsData, onSave }: GoalsPanelProps) {
    const [formData, setFormData] = useState<GoalsData>(
        goalsData ?? {
            riskTolerance: '',
            investmentHorizon: '',
            monthlyCapacity: '',
            goalType: '',
        }
    );
    const [saved, setSaved] = useState(false);

    const updateField = (field: keyof GoalsData, value: string) => {
        setFormData((prev) => ({ ...prev, [field]: value }));
        setSaved(false);
    };

    const handleSave = () => {
        onSave(formData);
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    const showGoalDetails = formData.goalType !== '';
    const showRetirement = formData.goalType === 'retirement';
    const showEducation = formData.goalType === 'education';
    const showEmergency = formData.goalType === 'emergency';

    return (
        <Dialog open={open} onOpenChange={(val) => { if (!val) onClose(); }}>
            <DialogContent className="sm:max-w-xl max-h-[85vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Goals & Planning</DialogTitle>
                    <DialogDescription>
                        Tell us about your investment personality and financial goals.
                    </DialogDescription>
                </DialogHeader>

                <div className="mt-4 space-y-6">
                    {/* Risk Tolerance */}
                    <div className="space-y-3">
                        <Label className="text-sm font-semibold text-gray-700">
                            Risk Tolerance
                        </Label>
                        <div className="grid grid-cols-2 gap-2">
                            {RISK_OPTIONS.map((opt) => (
                                <button
                                    key={opt.value}
                                    type="button"
                                    onClick={() => updateField('riskTolerance', opt.value)}
                                    className={`rounded-lg border-2 p-3 text-left transition-all ${
                                        formData.riskTolerance === opt.value
                                            ? 'border-blue-500 bg-blue-50/50 shadow-sm'
                                            : 'border-gray-100 bg-white hover:border-gray-200'
                                    }`}
                                >
                                    <p className="text-sm font-medium text-gray-800">{opt.label}</p>
                                    <p className="mt-0.5 text-xs text-gray-400">{opt.desc}</p>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Investment Horizon */}
                    <AnimatePresence>
                        {formData.riskTolerance && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="space-y-3 overflow-hidden"
                            >
                                <Label className="text-sm font-semibold text-gray-700">
                                    Investment Horizon
                                </Label>
                                <div className="grid grid-cols-2 gap-2">
                                    {HORIZON_OPTIONS.map((opt) => (
                                        <button
                                            key={opt.value}
                                            type="button"
                                            onClick={() => updateField('investmentHorizon', opt.value)}
                                            className={`rounded-lg border-2 p-3 text-left transition-all ${
                                                formData.investmentHorizon === opt.value
                                                    ? 'border-blue-500 bg-blue-50/50 shadow-sm'
                                                    : 'border-gray-100 bg-white hover:border-gray-200'
                                            }`}
                                        >
                                            <p className="text-sm font-medium text-gray-800">{opt.label}</p>
                                            <p className="mt-0.5 text-xs text-gray-400">{opt.desc}</p>
                                        </button>
                                    ))}
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Monthly Investment Capacity */}
                    <AnimatePresence>
                        {formData.investmentHorizon && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="space-y-2 overflow-hidden"
                            >
                                <Label className="text-sm font-semibold text-gray-700">
                                    Monthly Investment Capacity (₹)
                                </Label>
                                <Input
                                    type="number"
                                    placeholder="e.g. 25000"
                                    className="h-11"
                                    value={formData.monthlyCapacity}
                                    onChange={(e) => updateField('monthlyCapacity', e.target.value)}
                                />
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Goal Type */}
                    <AnimatePresence>
                        {formData.monthlyCapacity && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="space-y-2 overflow-hidden"
                            >
                                <Label className="text-sm font-semibold text-gray-700">
                                    Primary Financial Goal
                                </Label>
                                <Select
                                    value={formData.goalType}
                                    onValueChange={(val) => updateField('goalType', val)}
                                >
                                    <SelectTrigger className="h-11">
                                        <SelectValue placeholder="Select goal type" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {GOAL_TYPES.map((g) => (
                                            <SelectItem key={g.value} value={g.value}>
                                                {g.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Dynamic Goal-specific fields */}
                    <AnimatePresence>
                        {showGoalDetails && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="space-y-4 overflow-hidden rounded-lg border border-blue-100 bg-blue-50/30 p-4"
                            >
                                <p className="text-xs font-semibold uppercase tracking-wider text-blue-600">
                                    Goal Details
                                </p>

                                <div className="grid gap-4 sm:grid-cols-2">
                                    <div className="space-y-2">
                                        <Label className="text-sm text-gray-700">Target Amount (₹)</Label>
                                        <Input
                                            type="number"
                                            placeholder="e.g. 5000000"
                                            className="h-11"
                                            value={formData.targetAmount ?? ''}
                                            onChange={(e) => updateField('targetAmount', e.target.value)}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label className="text-sm text-gray-700">Target Date</Label>
                                        <Input
                                            type="date"
                                            className="h-11"
                                            value={formData.targetDate ?? ''}
                                            onChange={(e) => updateField('targetDate', e.target.value)}
                                        />
                                    </div>
                                </div>

                                {/* Retirement-specific */}
                                {showRetirement && (
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        className="grid gap-4 sm:grid-cols-2"
                                    >
                                        <div className="space-y-2">
                                            <Label className="text-sm text-gray-700">Current Age</Label>
                                            <Input
                                                type="number"
                                                placeholder="e.g. 30"
                                                className="h-11"
                                                value={formData.currentAge ?? ''}
                                                onChange={(e) => updateField('currentAge', e.target.value)}
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label className="text-sm text-gray-700">Desired Retirement Age</Label>
                                            <Input
                                                type="number"
                                                placeholder="e.g. 60"
                                                className="h-11"
                                                value={formData.retirementAge ?? ''}
                                                onChange={(e) => updateField('retirementAge', e.target.value)}
                                            />
                                        </div>
                                    </motion.div>
                                )}

                                {/* Education-specific */}
                                {showEducation && (
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        className="grid gap-4 sm:grid-cols-2"
                                    >
                                        <div className="space-y-2">
                                            <Label className="text-sm text-gray-700">Child&apos;s Current Age</Label>
                                            <Input
                                                type="number"
                                                placeholder="e.g. 5"
                                                className="h-11"
                                                value={formData.childAge ?? ''}
                                                onChange={(e) => updateField('childAge', e.target.value)}
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label className="text-sm text-gray-700">Education Type</Label>
                                            <Select
                                                value={formData.educationType ?? ''}
                                                onValueChange={(val) => updateField('educationType', val)}
                                            >
                                                <SelectTrigger className="h-11">
                                                    <SelectValue placeholder="Select type" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="undergraduate">Undergraduate</SelectItem>
                                                    <SelectItem value="postgraduate">Postgraduate</SelectItem>
                                                    <SelectItem value="abroad">Study Abroad</SelectItem>
                                                    <SelectItem value="professional">Professional Course</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                    </motion.div>
                                )}

                                {/* Emergency Fund-specific */}
                                {showEmergency && (
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        className="space-y-2"
                                    >
                                        <Label className="text-sm text-gray-700">Months of Expenses to Cover</Label>
                                        <Select
                                            value={formData.monthsOfExpenses ?? ''}
                                            onValueChange={(val) => updateField('monthsOfExpenses', val)}
                                        >
                                            <SelectTrigger className="h-11">
                                                <SelectValue placeholder="Select months" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="3">3 Months</SelectItem>
                                                <SelectItem value="6">6 Months</SelectItem>
                                                <SelectItem value="9">9 Months</SelectItem>
                                                <SelectItem value="12">12 Months</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </motion.div>
                                )}
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Save Button */}
                    <div className="flex items-center gap-3 pt-2">
                        <Button
                            onClick={handleSave}
                            className="gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 px-8 text-white shadow-md shadow-blue-200 hover:shadow-lg hover:shadow-blue-300"
                        >
                            {saved ? (
                                <>
                                    <CheckCircle2 className="h-4 w-4" />
                                    Saved!
                                </>
                            ) : (
                                <>
                                    <Target className="h-4 w-4" />
                                    Save Goals
                                </>
                            )}
                        </Button>
                        <Button variant="outline" className="px-8" onClick={onClose}>
                            Cancel
                        </Button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
