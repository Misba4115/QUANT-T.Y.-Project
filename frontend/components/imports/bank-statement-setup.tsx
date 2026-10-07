'use client';

import { FormEvent, useEffect, useState } from 'react';
import axios from 'axios';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { bankingApi } from '@/lib/api';
import type { BankAccount, StatementFrequency } from '@/types';
import { UploadStep } from '@/components/imports/upload-step';

export interface BankStatementDetails {
    accountId: string;
    statementFrequency: StatementFrequency;
}

export function BankStatementSetup({ value, onChange, disabled }: {
    value: BankStatementDetails;
    onChange: (value: BankStatementDetails) => void;
    disabled: boolean;
}) {
    const [accounts, setAccounts] = useState<BankAccount[]>([]);
    const [loadFailed, setLoadFailed] = useState(false);
    const [loading, setLoading] = useState(true);
    const [savingAccount, setSavingAccount] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [account, setAccount] = useState({ account_type: 'savings', account_name: '', institution: '', current_balance: '' });
    const [showForm, setShowForm] = useState(false);
    const [reload, setReload] = useState(0);

    useEffect(() => {
        let cancelled = false;
        bankingApi.getBankAccounts().then(({ data }) => {
            if (!cancelled) { setAccounts(data); setShowForm(data.length === 0); setError(null); setLoadFailed(false); }
        }).catch(() => {
            if (!cancelled) { setLoadFailed(true); setError('Could not load bank accounts. Retry before adding an account.'); }
        }).finally(() => { if (!cancelled) setLoading(false); });
        return () => { cancelled = true; };
    }, [reload]);

    const addAccount = async (event: FormEvent) => {
        event.preventDefault();
        if (savingAccount || loading || loadFailed || disabled) return;
        if (!account.institution.trim()) {
            setError('Enter your bank name.');
            return;
        }
        setSavingAccount(true);
        setError(null);
        try {
            const { data } = await bankingApi.addBankAccount({
                ...account, account_name: account.account_name.trim() || account.institution.trim(), institution: account.institution.trim(),
                current_balance: Number(account.current_balance), currency: 'INR', is_primary: accounts.length === 0,
            });
            if (!data.account_id) throw new Error('The saved account did not return an ID. Reload accounts before continuing.');
            setAccounts((previous) => [...previous, data]);
            onChange({ ...value, accountId: data.account_id });
            setShowForm(false);
            setAccount({ account_type: 'savings', account_name: '', institution: '', current_balance: '' });
        } catch (caught) {
            setError(axios.isAxiosError(caught) && typeof caught.response?.data?.detail === 'string'
                ? caught.response.data.detail : 'Could not save the bank account. Please try again.');
        } finally { setSavingAccount(false); }
    };
    const preventScrollChange = (event: React.WheelEvent<HTMLInputElement>) => event.currentTarget.blur();

    return (
        <div className="w-full border-t border-emerald-100 bg-emerald-50/30 p-5">
            <UploadStep number={2} title="Add your bank details" security="Only accounts belonging to your signed-in profile can be linked to an import. QUANT does not ask for bank passwords or PINs." />
            <p className="mb-4 text-sm text-stone-600">Choose a saved account or add one once, then upload its statement.</p>
            {error && <div role="alert" className="mb-3 text-sm text-rose-700">{error} {loadFailed && <button type="button" className="underline" onClick={() => { setLoading(true); setReload((v) => v + 1); }}>Retry loading accounts</button>}</div>}
            <fieldset disabled={disabled || loading || loadFailed || savingAccount} className="space-y-4 disabled:opacity-60">
                <div>
                    <Label htmlFor="statement-account">Bank account</Label>
                    <select id="statement-account" className="mt-1 h-10 w-full rounded-md border border-stone-200 bg-white px-3 text-sm" value={showForm ? 'new' : value.accountId} onChange={(event) => {
                        setShowForm(event.target.value === 'new');
                        onChange({ ...value, accountId: event.target.value === 'new' ? '' : event.target.value });
                    }}>
                        <option value="">{loading ? 'Loading accounts…' : 'Select an account'}</option>
                        {accounts.filter((item) => item.account_id).map((item) => <option key={item.account_id} value={item.account_id}>{item.institution} — {item.account_name}</option>)}
                        <option value="new">Add a new bank account</option>
                    </select>
                </div>
                {showForm && (
                    <form className="mt-6 space-y-4" onSubmit={addAccount}>
                        <div><Label htmlFor="institution">Bank name</Label><Input id="institution" className="mt-1" required maxLength={120} value={account.institution} onChange={(event) => setAccount({ ...account, institution: event.target.value })} placeholder="Bank name" /></div>
                        <div><Label htmlFor="account-type">Account type</Label><select id="account-type" className="mt-1 h-10 w-full rounded-md border border-stone-200 bg-white px-3 text-sm" value={account.account_type} onChange={(event) => setAccount({ ...account, account_type: event.target.value })}><option value="savings">Savings</option><option value="current">Current</option><option value="fixed_deposit">Fixed deposit</option><option value="recurring_deposit">Recurring deposit</option></select></div>
                        <div><Label htmlFor="balance">Current balance (INR)</Label><Input id="balance" className="mt-1" required min="0" step="0.01" type="number" value={account.current_balance} onChange={(event) => setAccount({ ...account, current_balance: event.target.value })} onWheel={preventScrollChange} /></div>
                        <div><Label htmlFor="account-name">Account nickname (optional)</Label><Input id="account-name" className="mt-1" maxLength={120} value={account.account_name} onChange={(event) => setAccount({ ...account, account_name: event.target.value })} placeholder="Primary savings" /><p className="mt-1 text-xs text-stone-500">If left blank, we’ll use the bank name to identify this account.</p></div>
                        <Button className="w-full" disabled={savingAccount || loading}>{savingAccount && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Save account</Button>
                    </form>

                )}
                <div>
                    <Label htmlFor="statement-frequency">Statement frequency</Label>
                    <select id="statement-frequency" className="mt-1 h-10 w-full rounded-md border border-stone-200 bg-white px-3 text-sm" value={value.statementFrequency} onChange={(event) => onChange({ ...value, statementFrequency: event.target.value as StatementFrequency })}>
                        <option value="weekly">Weekly</option><option value="monthly">Monthly</option><option value="quarterly">Quarterly</option><option value="6_months">6 months</option><option value="yearly">Yearly</option>
                    </select>
                    <p className="mt-2 text-xs text-stone-500">Saved with this import. Transaction dates and amounts stay as reported in your statement.</p>
                </div>
            </fieldset>
            {value.accountId && !showForm && <p role="status" className="mt-3 text-sm text-emerald-700">Bank details ready. Continue to upload your statement below.</p>}
        </div>
    );
}
