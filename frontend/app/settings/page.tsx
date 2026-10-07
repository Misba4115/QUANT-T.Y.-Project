'use client';

import { useCallback, useEffect, useState } from 'react';
import { Bell, Cable, Clock3, Inbox, RefreshCw, ShieldCheck, SlidersHorizontal, User } from 'lucide-react';

import Navbar from '@/components/layout/navbar';
import PageTransition from '@/components/layout/page-transition';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { connectorsApi, ingestionInboxApi, jobsApi, notificationsApi, personalizationApi, userApi } from '@/lib/api';
import type { ConnectorAccount, ConnectorSyncPreview, NotificationPreference, UserPreference } from '@/types';
import { useUser } from '@/contexts/user-context';
import { SecurityBadge } from '@/components/ui/security-badge';

const defaultNotifications: NotificationPreference = { in_app_enabled: true, email_enabled: false, minimum_severity: 'info', timezone: 'Asia/Kolkata', weekly_summary: true };
const defaultPreference: UserPreference = { persona: 'guided', explanation_depth: 'balanced', dashboard_emphasis: [], explicit_feedback: {} };

function Section({ icon, title, description, children }: { icon: React.ReactNode; title: string; description: string; children: React.ReactNode }) {
    return <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="mb-5 flex items-start gap-3"><span className="rounded-xl bg-blue-50 p-2 text-blue-700">{icon}</span><div><h2 className="font-semibold text-slate-950">{title}</h2><p className="text-sm text-slate-500">{description}</p></div></div>{children}</section>;
}

export default function SettingsPage() {
    const { user, login } = useUser();
    const [fullName, setFullName] = useState('');
    const [connections, setConnections] = useState<ConnectorAccount[]>([]);
    const [syncPreview, setSyncPreview] = useState<ConnectorSyncPreview | null>(null);
    const [notifications, setNotifications] = useState(defaultNotifications);
    const [preference, setPreference] = useState(defaultPreference);
    const [priceSyncEnabled, setPriceSyncEnabled] = useState(false);
    const [priceSyncHours, setPriceSyncHours] = useState(6);
    const [forwardingAddress, setForwardingAddress] = useState<string | null>(null);
    const [risk, setRisk] = useState({ loss_tolerance: 2, emergency_months: 6, time_horizon_years: 8, income_stability: 2, liability_ratio: 0.2, concentration_ratio: 0.3, illiquid_ratio: 0.1, knowledge_level: 2 });
    const [riskResult, setRiskResult] = useState<Record<string, unknown> | null>(null);
    const [busy, setBusy] = useState<string | null>(null);
    const [notice, setNotice] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        try {
            const [connectorResponse, notificationResponse, preferenceResponse, jobsResponse, riskResponse] = await Promise.all([connectorsApi.list(), notificationsApi.getPreferences(), personalizationApi.getPreferences(), jobsApi.list(), personalizationApi.latestRisk()]);
            setConnections(connectorResponse.data); setNotifications(notificationResponse.data); setPreference(preferenceResponse.data); setRiskResult(riskResponse.data || null);
            const schedule = jobsResponse.data.find((item) => item.job_type === 'price_sync');
            if (schedule) { setPriceSyncEnabled(schedule.enabled); setPriceSyncHours(Math.max(1, Math.round(schedule.interval_seconds / 3600))); }
        } catch { setError('Some settings could not be loaded. Existing financial data was not changed.'); }
    }, []);

    useEffect(() => { setFullName(user?.name || ''); void load(); }, [load, user?.name]);

    const run = async (key: string, action: () => Promise<void>, success: string) => {
        setBusy(key); setError(null); setNotice(null);
        try { await action(); setNotice(success); } catch (caught) { setError(caught instanceof Error ? caught.message : 'The operation failed safely.'); } finally { setBusy(null); }
    };

    const activeConnections = connections.filter((item) => item.status !== 'revoked');
    const saveProfile = () => run('profile', async () => { const response = await userApi.updateProfile({ name: fullName }); login(response.data); }, 'Profile saved.');
    const connectUpstox = () => run('upstox', async () => { const response = await connectorsApi.authorizeUpstox(); window.location.assign(response.data.authorization_url); }, 'Opening Upstox authorization…');
    const previewSync = (accountId: string) => run('sync', async () => { const response = await connectorsApi.previewSync(accountId); setSyncPreview(response.data); }, 'Sync preview is ready. Review it before committing.');
    const commitSync = () => syncPreview && run('commit', async () => { await connectorsApi.commitSync(syncPreview.connector_sync_run_id); setSyncPreview(null); await load(); }, 'Broker records committed; valuation refresh was queued.');

    return <><Navbar /><PageTransition><main className="mx-auto max-w-4xl space-y-6 px-4 py-8 sm:px-6">
        <header><p className="text-sm font-medium text-emerald-700">Control center</p><h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-950">Connections, privacy and preferences</h1><p className="mt-2 text-sm text-slate-500">Every connection is read-only, revocable and independently degradable.</p></header>
        {notice && <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{notice}</div>}
        {error && <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</div>}

        <Section icon={<User className="h-5 w-5" />} title="Profile" description="Your authenticated identity and display name."><div className="grid gap-4 sm:grid-cols-2"><div><Label>Full name</Label><Input className="mt-2" value={fullName} onChange={(event) => setFullName(event.target.value)} /></div><div><Label>Email</Label><Input className="mt-2" value={user?.email || ''} disabled /></div></div><Button className="mt-4" disabled={busy === 'profile' || !fullName.trim()} onClick={() => void saveProfile()}>{busy === 'profile' ? 'Saving…' : 'Save profile'}</Button></Section>

        <Section icon={<Cable className="h-5 w-5" />} title="Broker connections" description="Review-first, read-only sync. Live trading is not available.">
            <div className="mb-4 flex flex-wrap gap-2"><SecurityBadge label="Read-only broker access" /><SecurityBadge label="Encrypted connector credentials" /></div>
            <div className="space-y-3">{activeConnections.map((account) => <div key={account.connector_account_id} className="flex flex-col gap-3 rounded-xl border border-slate-200 p-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-medium text-slate-900">{account.display_name}</p><p className="text-xs text-slate-500">{account.provider} · {account.status.replaceAll('_', ' ')} · Last sync {account.last_successful_sync_at ? new Date(account.last_successful_sync_at).toLocaleString() : 'never'}</p></div><div className="flex gap-2"><Button variant="outline" disabled={busy === 'sync'} onClick={() => void previewSync(account.connector_account_id)}><RefreshCw className="mr-2 h-4 w-4" />Preview sync</Button><Button variant="outline" onClick={() => void run('revoke', async () => { await connectorsApi.revoke(account.connector_account_id); await load(); }, 'Connection revoked and credentials deleted.')}>Disconnect</Button></div></div>)}</div>
            {activeConnections.length === 0 && <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">No broker is connected. Manual entry and file upload remain available.</p>}
            <Button className="mt-4" disabled={busy === 'upstox'} onClick={() => void connectUpstox()}>Connect Upstox</Button><p className="mt-2 text-xs text-slate-500">Authorization occurs on Upstox. QUANT never receives your broker password.</p>
            {syncPreview && <div className="mt-4 rounded-xl border border-blue-200 bg-blue-50 p-4"><p className="font-medium text-blue-950">Review sync</p><p className="mt-1 text-sm text-blue-800">{syncPreview.additions} additions · {syncPreview.updates} updates · {syncPreview.duplicates} unchanged · {syncPreview.conflicts} conflicts</p><Button className="mt-3" disabled={busy === 'commit'} onClick={() => void commitSync()}>Commit reviewed changes</Button></div>}
        </Section>

        <Section icon={<Inbox className="h-5 w-5" />} title="Statement forwarding" description="A private address prepares an import preview and never commits automatically.">
            {forwardingAddress ? <div className="rounded-xl border border-amber-200 bg-amber-50 p-4"><p className="text-xs font-medium uppercase tracking-wide text-amber-700">Shown once</p><p className="mt-1 break-all font-mono text-sm text-amber-950">{forwardingAddress}</p></div> : <p className="text-sm text-slate-600">Only messages from your account email are accepted by default.</p>}
            <div className="mt-4 flex gap-2"><Button disabled={busy === 'inbox'} onClick={() => void run('inbox', async () => { const response = await ingestionInboxApi.setup(user?.email ? [user.email] : []); setForwardingAddress(response.data.forwarding_address); }, 'Forwarding inbox created. Save the address now.')}>Create or rotate address</Button><Button variant="outline" onClick={() => void run('inbox-revoke', async () => { await ingestionInboxApi.revoke(); setForwardingAddress(null); }, 'Forwarding inbox revoked.')}>Revoke</Button></div>
        </Section>

        <Section icon={<Bell className="h-5 w-5" />} title="Notifications" description="In-app delivery is primary. Email receives a redacted summary only.">
            <div className="space-y-4"><label className="flex items-center justify-between"><span><span className="block text-sm font-medium">In-app alerts</span><span className="text-xs text-slate-500">Authenticated live delivery and replay</span></span><Switch checked={notifications.in_app_enabled} onCheckedChange={(value) => setNotifications({ ...notifications, in_app_enabled: value })} /></label><label className="flex items-center justify-between"><span><span className="block text-sm font-medium">Redacted email summaries</span><span className="text-xs text-slate-500">No raw financial details</span></span><Switch checked={notifications.email_enabled} onCheckedChange={(value) => setNotifications({ ...notifications, email_enabled: value })} /></label><label className="flex items-center justify-between"><span className="text-sm font-medium">Weekly summary</span><Switch checked={notifications.weekly_summary} onCheckedChange={(value) => setNotifications({ ...notifications, weekly_summary: value })} /></label><div className="grid gap-3 sm:grid-cols-3"><div><Label>Minimum severity</Label><select className="mt-2 h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm" value={notifications.minimum_severity} onChange={(event) => setNotifications({ ...notifications, minimum_severity: event.target.value as NotificationPreference['minimum_severity'] })}><option value="info">Info</option><option value="warning">Warning</option><option value="critical">Critical</option></select></div><div><Label>Quiet start</Label><Input type="time" className="mt-2" value={notifications.quiet_hours_start?.slice(0, 5) || ''} onChange={(event) => setNotifications({ ...notifications, quiet_hours_start: event.target.value || null })} /></div><div><Label>Quiet end</Label><Input type="time" className="mt-2" value={notifications.quiet_hours_end?.slice(0, 5) || ''} onChange={(event) => setNotifications({ ...notifications, quiet_hours_end: event.target.value || null })} /></div></div></div><Button className="mt-4" onClick={() => void run('notifications', async () => { const response = await notificationsApi.savePreferences(notifications); setNotifications(response.data); }, 'Notification preferences saved.')}>Save notification preferences</Button>
        </Section>

        <Section icon={<Clock3 className="h-5 w-5" />} title="Price refresh automation" description="Runs in the separate worker with idempotency and stale-price protection."><div className="flex items-center justify-between"><div><p className="text-sm font-medium">Scheduled refresh</p><p className="text-xs text-slate-500">Provider limits and market schedules still apply.</p></div><Switch checked={priceSyncEnabled} onCheckedChange={setPriceSyncEnabled} /></div><div className="mt-4 max-w-xs"><Label>Interval (hours)</Label><Input className="mt-2" type="number" min={1} max={168} value={priceSyncHours} onChange={(event) => setPriceSyncHours(Number(event.target.value))} /></div><Button className="mt-4" onClick={() => void run('schedule', async () => { await jobsApi.configurePriceSync(priceSyncHours * 3600, priceSyncEnabled); }, 'Price refresh schedule saved.')}>Save schedule</Button></Section>

        <Section icon={<SlidersHorizontal className="h-5 w-5" />} title="Explanation preferences" description="Personas change emphasis and depth only; never financial calculations."><div className="grid gap-4 sm:grid-cols-2"><div><Label>Persona</Label><select className="mt-2 h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm" value={preference.persona} onChange={(event) => setPreference({ ...preference, persona: event.target.value as UserPreference['persona'] })}><option value="guided">Guided</option><option value="analytical">Analytical</option><option value="minimal">Minimal</option></select></div><div><Label>Explanation depth</Label><select className="mt-2 h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm" value={preference.explanation_depth} onChange={(event) => setPreference({ ...preference, explanation_depth: event.target.value as UserPreference['explanation_depth'] })}><option value="concise">Concise</option><option value="balanced">Balanced</option><option value="detailed">Detailed</option></select></div></div><div className="mt-4 flex gap-2"><Button onClick={() => void run('persona', async () => { const response = await personalizationApi.savePreferences(preference); setPreference(response.data); }, 'Explanation preferences saved.')}>Save preferences</Button><Button variant="outline" onClick={() => void run('persona-reset', async () => { const response = await personalizationApi.resetPreferences(); setPreference(response.data); }, 'Preferences reset.')}>Reset</Button></div></Section>

        <Section icon={<ShieldCheck className="h-5 w-5" />} title="Risk capacity assessment" description="Versioned dimensions for capacity, horizon, concentration, liquidity, tolerance and experience."><div className="grid gap-3 sm:grid-cols-2">{Object.entries(risk).map(([key, value]) => <div key={key}><Label>{key.replaceAll('_', ' ')}</Label><Input className="mt-2" type="number" step={key.includes('ratio') ? 0.05 : 1} value={value} onChange={(event) => setRisk({ ...risk, [key]: Number(event.target.value) })} /></div>)}</div><Button className="mt-4" onClick={() => void run('risk', async () => { const response = await personalizationApi.assessRisk(risk); setRiskResult(response.data); }, 'Risk assessment recorded with its model version.')}>Record assessment</Button>{riskResult && <pre className="mt-4 overflow-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-100">{JSON.stringify(riskResult, null, 2)}</pre>}</Section>
    </main></PageTransition></>;
}
