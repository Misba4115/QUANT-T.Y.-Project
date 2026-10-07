'use client';

import { useCallback, useEffect, useState, type FormEvent, type ReactNode } from 'react';
import { Bookmark, ExternalLink, RefreshCw, Scale, Sparkles, BarChart2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { discoveryApi, selectionKey, scenarioValue, type InvestmentCategory, type Platform, type SavedInvestment } from '@/lib/investment-discovery';
import { formatCurrency } from '@/lib/helpers';

function Choice({ label, value, options, onChange }: { label: string; value: string; options: { id: string; name: string }[]; onChange: (id: string) => void }) {
    return <div className="space-y-1.5"><p className="text-xs font-medium text-slate-500">{label}</p>
        <Select value={value} onValueChange={onChange}><SelectTrigger aria-label={label} className="w-full"><SelectValue /></SelectTrigger>
            <SelectContent>{options.map(option => <SelectItem key={option.id} value={option.id}>{option.name}</SelectItem>)}</SelectContent>
        </Select></div>;
}

function PlatformChips({ label, selected, platforms, onChange }: { label: string; selected: string; platforms: InvestmentCategory['platforms']; onChange: (id: string) => void }) {
    return <div className="space-y-2"><p className="text-xs font-medium text-slate-500">{label}</p>
        <div role="group" aria-label={label} className="flex max-w-full flex-wrap gap-2">{platforms.map(platform =>
            <button key={platform.id} type="button" aria-pressed={selected === platform.id} onClick={() => onChange(platform.id)}
                className={`shrink-0 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors focus-visible:outline-2 focus-visible:outline-emerald-600 ${selected === platform.id ? 'border-emerald-600 bg-emerald-50 text-emerald-800' : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'}`}>
                {platform.name}</button>)}</div></div>;
}

function Calculator({ category, amount, setAmount, years, setYears, suffix, minAmount = 100, large = false }: {
    category: InvestmentCategory; amount: number; setAmount: (amount: number) => void; years: number; setYears: (years: number) => void; suffix: string; minAmount?: number; large?: boolean;
}) {
    const amountId = `amount-${category.id}-${suffix}`;
    const yearsId = `years-${category.id}-${suffix}`;
    const projected = scenarioValue(amount, category.scenario_rate, years);
    return <div className={`rounded-xl border border-slate-100 bg-slate-50 ${large ? 'space-y-5 p-5' : 'space-y-3 p-4'}`}>
        <div className="space-y-1.5"><Label htmlFor={amountId} className="flex justify-between gap-2 text-xs text-slate-600"><span>Investment amount</span><span className="font-semibold text-slate-900">{formatCurrency(amount)}</span></Label>
            <input id={amountId} type="range" min={minAmount} max={1000000} step={100} value={amount} onChange={event => setAmount(Number(event.target.value))} className="w-full accent-emerald-600" />
            {large && <p className="text-[11px] text-slate-400">{formatCurrency(minAmount)} to ₹10,00,000 · one-time investment</p>}</div>
        <div className="space-y-1.5"><Label htmlFor={yearsId} className="flex justify-between gap-2 text-xs text-slate-600"><span>Timeline</span><span className="font-semibold text-slate-900">{years} {years === 1 ? 'year' : 'years'}</span></Label>
            <input id={yearsId} type="range" min={1} max={20} step={1} value={years} onChange={event => setYears(Number(event.target.value))} className="w-full accent-emerald-600" /></div>
        <div className="flex flex-wrap items-end justify-between gap-2 border-t border-slate-200 pt-3"><div><p className="text-[11px] text-slate-500">Illustrative value at {category.scenario_rate}% per year</p>
            <p aria-live="polite" className={`${large ? 'text-2xl' : 'text-xl'} font-bold tracking-tight text-slate-900`}>{formatCurrency(projected)}</p></div>
            <p className="text-xs text-emerald-700">+{formatCurrency(projected - amount)} illustration</p></div>
        {large && <p className="text-xs text-slate-500">Scenario only; excludes fees, tax and inflation. It is not a forecast or bank quote.</p>}
        {years < category.min_years && <p className="text-xs text-amber-700">Below the {category.min_years}-year planning horizon.</p>}
    </div>;
}

function HistoryChart({ category }: { category: InvestmentCategory }) {
    const points = category.analysis.history ?? [];
    if (category.analysis.status !== 'available' || points.length < 2) return <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-center text-xs text-slate-500">Historical chart unavailable until comparable, recent price data is recorded.</div>;
    const values = points.map(point => point.index);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = Math.max(max - min, 1);
    const path = points.map((point, i) => `${i ? 'L' : 'M'} ${(i / (points.length - 1) * 100).toFixed(2)} ${(90 - (point.index - min) / span * 80).toFixed(2)}`).join(' ');
    return <figure className="rounded-xl border border-slate-100 bg-white p-4"><figcaption className="mb-2 text-xs font-semibold text-slate-700">Historical proxy price · indexed to 100</figcaption>
        <svg role="img" aria-label={`${category.name} historical price index from ${points[0].date} to ${points[points.length - 1].date}`} viewBox="0 0 100 100" preserveAspectRatio="none" className="h-40 w-full overflow-visible">
            <path d={path} fill="none" stroke="#059669" strokeWidth="1.4" vectorEffect="non-scaling-stroke" strokeLinecap="round" strokeLinejoin="round" /></svg>
        <div className="mt-2 flex justify-between text-[11px] text-slate-400"><span>{points[0].date}</span><span>{points[points.length - 1].date}</span></div>
        <p className="mt-1 text-[11px] text-slate-400">{category.analysis.proxy} · {category.analysis.provider}</p></figure>;
}

function Analysis({ category }: { category: InvestmentCategory }) {
    const analysis = category.analysis;
    return <div className="rounded-xl bg-slate-50 p-3 text-xs text-slate-500">
        <p className="mb-1 font-semibold text-slate-700">Mean–variance analysis</p>
        {analysis.status === 'available' ? <>
            <p>Historical annual mean: {analysis.mean_pct}% · Price volatility: {analysis.volatility_pct}%</p>
            <p>Research allocation: {analysis.weight_pct}% of eligible proxies</p>
            <p className="mt-1">Proxy: {analysis.proxy} · {analysis.observations} observations · {analysis.provider} · as of {analysis.as_of}</p>
        </> : <p>Not enough comparable history.</p>}
        <p className="mt-1">{analysis.reason}</p>
    </div>;
}

const bankDepositPaths: Record<string, { path: string; source: string }> = {
    hdfc: { path: 'NetBanking → FD/RD → FD → Open FD', source: 'https://www.hdfc.bank.in/need-help/net-banking-faqs' },
    icici: { path: 'Internet Banking → Bank Accounts → Deposits → Create FD', source: 'https://www.icici.bank.in/personal-banking/deposits/fixed-deposit' },
    sbi: { path: 'OnlineSBI or YONO → Deposit → Fixed Deposit', source: 'https://sbi.bank.in/web/yono/deposits' },
    axis: { path: 'Internet Banking → Accounts → Deposits → Open Now', source: 'https://application.axis.bank.in/webforms/axis-support/sub-issues/deposits-FD-CreateFD-1.aspx' },
    kotak: { path: 'Net Banking → Investment → Deposits → Open a Fixed/Recurring Deposit', source: 'https://www.kotak.bank.in/en/help-center/fixed-deposit-and-recurring-deposit/open-fd-rd-features/q229.html' },
};

function ProviderHandoff({ category, platform, optionName, compact = false }: { category: InvestmentCategory; platform: Platform; optionName: string; compact?: boolean }) {
    const isDeposit = category.id === 'deposit';
    const bankPath = bankDepositPaths[platform.id];
    const destination = platform.action_url || platform.url;
    if (!destination) return <p className="text-xs text-slate-500">Find this provider’s official site and confirm its terms before proceeding.</p>;
    return <Dialog>
        <DialogTrigger asChild><Button type="button" size="sm" variant={compact ? 'outline' : 'default'} className={compact ? '' : 'bg-stone-900 text-white hover:bg-emerald-700'}>
            {compact ? `Visit ${platform.name}` : `Open ${platform.name}`}<ExternalLink />
        </Button></DialogTrigger>
        <DialogContent className="max-h-[90dvh] overflow-y-auto rounded-2xl sm:max-w-lg"><DialogHeader><DialogTitle>Before you visit {platform.name}</DialogTitle>
            <DialogDescription>QUANT will open the provider’s site in a new tab. You will sign in and choose the product there.</DialogDescription></DialogHeader>
            <div className="space-y-4 text-sm text-slate-600">
                <p className="rounded-xl bg-slate-50 p-3"><span className="font-medium text-slate-800">Looking for:</span> {optionName}</p>
                <ol className="list-decimal space-y-2 pl-5">{isDeposit ? <>
                    <li>Open the fixed-deposit page and sign in to your bank account, if asked.</li>
                    <li>{bankPath ? `In online banking, look for ${bankPath.path}.` : 'Look for Deposits or Fixed Deposit, then Open FD.'}</li>
                    <li>Choose the amount, term, interest payout and nominee. If you want deposits with different end dates, repeat with a different term for each one.</li>
                </> : <>
                    <li>Open the provider’s product or account page and sign in, if asked.</li>
                    <li>Search for the specific fund, share or asset you intend to review; this card describes a category, not a named product.</li>
                    <li>Check the product name, current price, charges and withdrawal or selling rules before making any decision.</li>
                </>}</ol>
                <p className="text-xs text-slate-500">The provider’s menus and eligibility can change. QUANT’s calculator is an illustration, not a live rate or order quote. Confirm the final terms on the provider’s site.</p>
                {bankPath && <a href={bankPath.source} target="_blank" rel="noopener noreferrer" className="text-xs font-medium text-emerald-700 underline">Bank’s official instructions</a>}
            </div>
            <Button asChild className="w-full bg-stone-900 text-white hover:bg-emerald-700"><a href={destination} target="_blank" rel="noopener noreferrer">Continue to {platform.name}<ExternalLink /></a></Button>
        </DialogContent>
    </Dialog>;
}

function askForSecondOpinion(prompt: string) {
    window.dispatchEvent(new CustomEvent('open-chatbot', { detail: { prompt, autoSend: false } }));
}

function InvestmentCard({ category, saved, busy, save, addPlatform }: { category: InvestmentCategory; saved: SavedInvestment[]; busy: boolean; save: (item: SavedInvestment) => Promise<void>; addPlatform: (categoryId: string, name: string) => Promise<string> }) {
    const [index, setIndex] = useState(0);
    const [platformId, setPlatformId] = useState(category.platforms[0].id);
    const [years, setYears] = useState(5);
    const [amount, setAmount] = useState(10000);
    const [showCustom, setShowCustom] = useState(false);
    const [customName, setCustomName] = useState('');
    const [customBusy, setCustomBusy] = useState(false);
    const [customError, setCustomError] = useState('');
    const option = category.options[index];
    const platform = category.platforms.find(item => item.id === platformId)!;
    const minAmount = platform.minimum_amount;
    const investment = { category_id: category.id, option_id: option.id, platform_id: platformId, years, amount };
    const bookmark = saved.find(item => selectionKey(item) === selectionKey(investment));
    const unchanged = bookmark?.years === years && Number(bookmark?.amount) === amount;
    async function addOwnPlatform(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setCustomBusy(true); setCustomError('');
        try {
            const id = await addPlatform(category.id, customName.trim());
            setPlatformId(id); setCustomName(''); setShowCustom(false);
        } catch { setCustomError('Could not add this provider. Check the name, or try again.'); }
        finally { setCustomBusy(false); }
    }
    return <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-6 py-4"><div className="min-w-0"><h4 className="text-base font-semibold text-slate-900" aria-live="polite">{option.name}</h4>
            <p className="mt-0.5 text-xs text-slate-400">{category.name}</p></div>
            <div className="flex flex-wrap gap-2"><Button type="button" variant="outline" size="sm" disabled={category.options.length < 2} title="Shows another approach in this investment category; platform terms and estimates stay the same." onClick={() => setIndex(value => (value + 1) % category.options.length)}><RefreshCw />See another way to invest</Button>
                <Button variant={bookmark ? 'secondary' : 'outline'} size="sm" disabled={busy || unchanged} onClick={() => void save(investment)}><Bookmark />{unchanged ? 'Saved' : bookmark ? 'Update saved' : 'Save for comparison'}</Button></div></div>
        <div className="grid divide-y divide-slate-200 lg:grid-cols-3 lg:divide-x lg:divide-y-0">
            <div className="flex flex-col justify-between gap-5 p-6"><div className="space-y-4">
                <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-400">Asset snapshot</p>
                <div className="flex items-center justify-between gap-3 text-sm"><span className="text-slate-500">Risk level</span><Badge variant="secondary">{category.risk} risk</Badge></div>
                <div className="space-y-1"><p className="text-sm text-slate-500">Minimum investment</p><p className="text-sm font-semibold text-slate-900">{platform.minimum}</p></div>
            </div><div className="border-t border-slate-100 pt-4"><p className="text-xs text-slate-400">Planning horizon</p><p className="mt-1 text-sm font-semibold text-slate-900">{category.min_years}+ years</p></div></div>
            <div className="min-w-0 p-6"><p className="mb-4 text-[11px] font-semibold uppercase tracking-widest text-slate-400">Plan an investment</p>
                <Calculator category={category} amount={amount} setAmount={setAmount} years={years} setYears={setYears} suffix="card" minAmount={minAmount} />
                {!platform.verified && <p className="mt-2 text-xs text-amber-700">Your provider’s minimum and fees are unknown. The slider starts at ₹100 for illustration only.</p>}</div>
            <div className="flex min-w-0 flex-col justify-between gap-5 p-6"><div className="space-y-4"><p className="text-[11px] font-semibold uppercase tracking-widest text-slate-400">Choose a platform</p>
                <PlatformChips label={`Platforms for ${category.name}`} selected={platformId} platforms={category.platforms} onChange={id => {
                    setPlatformId(id);
                    const selected = category.platforms.find(candidate => candidate.id === id);
                    if (selected) setAmount(value => Math.max(value, selected.minimum_amount));
                }} />
                <button type="button" onClick={() => { setShowCustom(value => !value); setCustomError(''); }} className="text-xs font-medium text-emerald-700 hover:underline">+ Use my bank or broker</button>
                {showCustom && <form onSubmit={event => void addOwnPlatform(event)} className="space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <Label htmlFor={`own-provider-${category.id}`} className="text-xs">Provider name</Label>
                    <div className="flex flex-wrap gap-2"><Input id={`own-provider-${category.id}`} value={customName} onChange={event => setCustomName(event.target.value)} maxLength={80} required placeholder="Your bank or broker" className="min-w-32 flex-1 bg-white" />
                        <Button type="submit" size="sm" disabled={customBusy || !customName.trim()}>{customBusy ? 'Adding…' : 'Add'}</Button></div>
                    <p className="text-xs text-slate-500">Only you can see this provider. Verify its fees and minimum directly.</p>
                    {customError && <p role="alert" className="text-xs text-red-600">{customError}</p>}
                </form>}
            </div><div className="flex flex-wrap gap-2 border-t border-slate-100 pt-4"><ProviderHandoff category={category} platform={platform} optionName={option.name} />
                <Dialog><DialogTrigger asChild><Button variant="outline" size="sm"><BarChart2 />Explore Analysis</Button></DialogTrigger>
                    <DialogContent className="max-h-[90dvh] overflow-y-auto rounded-2xl sm:max-w-6xl"><DialogHeader><DialogTitle>{option.name}</DialogTitle>
                        <DialogDescription>{category.name} · {category.risk} risk · {category.owned ? 'Already in your portfolio' : 'Diversification opportunity'}</DialogDescription></DialogHeader>
                        <div className="grid gap-6 lg:grid-cols-2">
                            <div className="min-w-0 space-y-5"><section className="space-y-2"><h5 className="text-sm font-semibold text-slate-900">What this means for you</h5>{option.detail && <p className="text-sm font-medium text-slate-800">{option.detail}</p>}<p className="text-sm text-slate-600">{category.explanation}</p><p className="text-sm text-slate-600">{category.summary}</p><p className="text-xs text-slate-500">{category.liquidity}</p></section>
                                <section className="space-y-3"><h5 className="text-sm font-semibold text-slate-900">Compare platforms</h5>
                                    <div className="overflow-x-auto rounded-xl border border-slate-200"><table className="w-full min-w-[490px] text-left text-xs"><thead className="bg-slate-50 text-slate-500"><tr><th scope="col" className="p-3">Platform</th><th scope="col" className="p-3">Minimum</th><th scope="col" className="p-3">Fees and terms</th><th scope="col" className="p-3">Ease / reliability</th></tr></thead>
                                        <tbody>{category.platforms.map(candidate => <tr key={candidate.id} className="border-t border-slate-100 align-top text-slate-600"><th scope="row" className="p-3 font-semibold text-slate-800">{candidate.name}</th><td className="p-3">{candidate.minimum}</td><td className="p-3">{candidate.fees}</td><td className="p-3">{candidate.ease}<p className="mt-2 text-slate-400">{candidate.reliability}</p></td></tr>)}</tbody></table></div>
                                    <div className="flex flex-wrap gap-2">{category.platforms.filter(candidate => candidate.action_url).map(candidate => <ProviderHandoff key={candidate.id} category={category} platform={candidate} optionName={option.name} compact />)}</div>
                                    <p className="text-xs text-slate-400">Confirm current fees, product terms and account steps on each official site.</p>
                                    <DialogClose asChild><Button type="button" variant="outline" size="sm" onClick={() => requestAnimationFrame(() => askForSecondOpinion(`Give me a second opinion on ${option.name} through ${platform.name}. Compare it with my recorded portfolio, goals and risk profile. Explain the downsides, alternatives, costs and what current market evidence is missing.`))}>Ask QUANT for a second opinion</Button></DialogClose>
                                </section></div>
                            <div className="min-w-0 space-y-4"><div><h5 className="mb-2 text-sm font-semibold text-slate-900">Quantitative deep dive</h5><Analysis category={category} /></div>
                                <HistoryChart category={category} /><Calculator category={category} amount={amount} setAmount={setAmount} years={years} setYears={setYears} suffix="detail" minAmount={minAmount} large />
                                {!platform.verified && <p className="text-xs text-amber-700">Provider-specific terms are unverified; the calculator is an asset-category illustration.</p>}</div>
                        </div></DialogContent></Dialog></div></div>
        </div>
    </article>;
}

function ComparisonPanel({ categories, riskProfile, saved, busy, save, remove, onSecondOpinion }: { categories: InvestmentCategory[]; riskProfile: string | null; saved: SavedInvestment[]; busy: boolean; save: (item: SavedInvestment) => Promise<void>; remove: (item: SavedInvestment) => Promise<void>; onSecondOpinion: (prompt: string) => void }) {
    const [leftKey, setLeftKey] = useState('');
    const [rightKey, setRightKey] = useState('');
    const [platformOverrides, setPlatformOverrides] = useState<Record<string, string>>({});
    const [years, setYears] = useState(5);
    const [amount, setAmount] = useState('10000');
    const usable = saved.filter(item => categories.some(c => c.id === item.category_id && c.options.some(o => o.id === item.option_id) && c.platforms.some(p => p.id === item.platform_id)));
    const left = usable.find(item => selectionKey(item) === leftKey) ?? usable[0];
    const right = usable.find(item => selectionKey(item) === rightKey) ?? usable[1] ?? usable[0];
    const choices = usable.map(item => { const category = categories.find(c => c.id === item.category_id); return { id: selectionKey(item), name: `${category?.options.find(o => o.id === item.option_id)?.name} · ${category?.platforms.find(p => p.id === item.platform_id)?.name}` }; });
    const validAmount = Number(amount) >= 1 && Number(amount) <= 100000000 && Number.isFinite(Number(amount));
    if (!left || !right) return <div className="space-y-3 rounded-xl border border-dashed border-slate-200 bg-slate-50 p-5 text-sm text-slate-600"><p className="font-medium text-slate-800">No investments saved yet</p><p>Choose “Save for comparison” on a card. You can then compare two platforms for that investment, or save a second type of investment.</p>
        {saved.map(item => <div key={selectionKey(item)} className="flex items-center justify-between gap-2"><span>{item.category_id} · {item.platform_id} (unavailable)</span><Button variant="ghost" size="sm" disabled={busy} onClick={() => void remove(item)}>Remove</Button></div>)}
    </div>;
    const platformFor = (item: SavedInvestment, side: number) => {
        const category = categories.find(c => c.id === item.category_id)!;
        const overrideKey = `${side}:${selectionKey(item)}`;
        return category.platforms.find(p => p.id === platformOverrides[overrideKey])
            ?? category.platforms.find(p => p.id === (side === 1 && selectionKey(left) === selectionKey(right) ? category.platforms.find(p => p.id !== left.platform_id)?.id : item.platform_id))
            ?? category.platforms[0];
    };
    return <div className="space-y-5">
        <div className="rounded-xl bg-slate-50 p-3 text-xs text-slate-600">Based on your recorded holdings and {riskProfile ? `${riskProfile} risk setting` : 'an unrecorded risk setting'}. Historical market figures appear only when comparable, recent prices are available. Live economic indicators are not connected yet, so this view does not make a market-timing claim.</div>
        <div className="grid gap-4 sm:grid-cols-2"><div className="space-y-2"><Label htmlFor="compare-amount">Compare the same amount (₹)</Label><Input id="compare-amount" type="number" min={1} max={100000000} value={amount} onChange={event => setAmount(event.target.value)} aria-invalid={!validAmount} /></div>
            <div className="space-y-2"><Label htmlFor="compare-years">Common timeline: {years} years</Label><input id="compare-years" type="range" min={1} max={20} value={years} onChange={event => setYears(Number(event.target.value))} className="w-full accent-emerald-600" /></div></div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">{[left, right].map((item, side) => {
            const category = categories.find(c => c.id === item.category_id)!;
            const overrideKey = `${side}:${selectionKey(item)}`;
            const platform = platformFor(item, side);
            const candidate = { ...item, platform_id: platform.id, years, amount: Number(amount) };
            return <div key={side} className="space-y-4 rounded-xl border border-slate-200 p-4">
                <Choice label={side === 0 ? 'First saved option' : 'Second saved option'} value={selectionKey(item)} options={choices} onChange={side === 0 ? setLeftKey : setRightKey} />
                <PlatformChips label={`Platform ${side + 1}`} selected={platform.id} platforms={category.platforms} onChange={id => setPlatformOverrides(previous => ({ ...previous, [overrideKey]: id }))} />
                <dl className="space-y-3 text-sm">{[
                     ['Category', category.name], ['In your recorded holdings', category.owned ? 'Yes' : 'No'], ['Risk', category.risk],
                     ['Timeline fit', years >= category.min_years ? `Meets the ${category.min_years}-year planning horizon` : `Shorter than the ${category.min_years}-year planning horizon`],
                     ['Minimum investment', platform.minimum],
                    ['Fees', platform.fees], ['Ease of use (features, not a rating)', platform.ease], ['Reliability', platform.reliability],
                    ['Liquidity', category.liquidity], ['Illustrative future value', validAmount ? `${formatCurrency(scenarioValue(Number(amount), category.scenario_rate, years))} at ${category.scenario_rate}% annually` : 'Enter a valid amount'],
                     ['Saved scenario', `${formatCurrency(Number(item.amount))} over ${item.years} years`],
                     ['Market evidence', category.analysis.status === 'available' ? `Historical category proxy as of ${category.analysis.as_of}` : 'Not enough recent, comparable price history'],
                ].map(([label, value]) => <div key={label}><dt className="text-xs text-slate-400">{label}</dt><dd className="mt-1 text-slate-700">{value}</dd></div>)}</dl>
                {years < category.min_years && <p className="text-xs text-amber-700">Below the {category.min_years}-year planning horizon.</p>}
                 <Analysis category={category} />
                 {riskProfile === 'conservative' && ['High', 'Very high'].includes(category.risk) && <p className="text-xs text-amber-700">This risk level may not fit your conservative setting. Review your goal and ability to absorb a loss.</p>}
                 {platform.url ? <ProviderHandoff category={category} platform={platform} optionName={category.options.find(option => option.id === item.option_id)?.name ?? category.name} compact />
                    : <p className="text-xs text-amber-700">Your provider’s terms are unverified. Check its official site.</p>}
                {platform.checked_on && <p className="text-xs text-slate-400">Sources checked {platform.checked_on}; confirm current terms.</p>}
                <Button variant="outline" size="sm" disabled={busy || !validAmount} onClick={() => void save(candidate)}>Save this combination</Button>
                <div className="border-t border-slate-100 pt-3 text-xs text-slate-500"><p className="mb-1 font-semibold text-slate-700">What this means for you</p>{category.summary}</div>
            </div>;
        })}</div>
        <Button type="button" variant="outline" size="sm" onClick={() => onSecondOpinion(`Give me a balanced second opinion comparing ${categories.find(c => c.id === left.category_id)?.options.find(o => o.id === left.option_id)?.name} through ${platformFor(left, 0).name} with ${categories.find(c => c.id === right.category_id)?.options.find(o => o.id === right.option_id)?.name} through ${platformFor(right, 1).name}. Compare the same ₹${Number(amount).toLocaleString('en-IN')} over ${years} years for my recorded portfolio and goals. Use my risk setting, holdings, costs and dated evidence. Explain reasons to choose neither and what is unknown.`)}>Ask QUANT about this comparison</Button>
        <p className="text-xs text-slate-500">Platform choice changes costs and experience, not the underlying asset’s historical return. These illustrations exclude fees, tax and inflation; losses are possible. Different categories carry different risks.</p>
        <div className="border-t border-slate-100 pt-4"><h3 className="mb-2 text-sm font-semibold text-slate-800">Saved options</h3>
            {saved.map(item => <div key={selectionKey(item)} className="flex items-center justify-between gap-2 py-2 text-xs text-slate-500"><span>{choices.find(c => c.id === selectionKey(item))?.name ?? `${item.category_id} · ${item.platform_id} (unavailable)`}</span><Button variant="ghost" size="sm" disabled={busy} onClick={() => void remove(item)}>Remove</Button></div>)}
        </div>
    </div>;
}

export default function InvestmentDiscovery({ children }: { children?: ReactNode }) {
    const [categories, setCategories] = useState<InvestmentCategory[]>([]);
    const [riskProfile, setRiskProfile] = useState<string | null>(null);
    const [saved, setSaved] = useState<SavedInvestment[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [saveError, setSaveError] = useState('');
    const [busy, setBusy] = useState(false);
    const [notice, setNotice] = useState('');
    const [comparisonOpen, setComparisonOpen] = useState(false);
    const load = useCallback(async () => {
        setLoading(true); setError(''); setSaveError('');
        const [discovery, bookmarks] = await Promise.allSettled([discoveryApi.get(), discoveryApi.saved()]);
        if (discovery.status === 'fulfilled') { setCategories(discovery.value.data.categories); setRiskProfile(discovery.value.data.risk_profile); }
        else setError('Could not read your portfolio. Retry to load investment options.');
        if (bookmarks.status === 'fulfilled') setSaved(bookmarks.value.data);
        else setSaveError('Could not load saved comparisons. You can still save an option or retry with Refresh holdings.');
        setLoading(false);
    }, []);
    useEffect(() => { void load(); }, [load]);
    async function save(item: SavedInvestment) {
        if (busy) return;
        setBusy(true); setSaveError(''); setNotice('');
        try {
            const response = await discoveryApi.save(item);
            setSaved(previous => [...previous.filter(value => selectionKey(value) !== selectionKey(item)), response.data]);
            setNotice('Saved for comparison. Reopen Saved comparisons any time.');
        } catch { setSaveError('Could not save this option. Your previous bookmarks are unchanged. Please retry.'); }
        finally { setBusy(false); }
    }
    async function remove(item: SavedInvestment) {
        if (busy) return;
        setBusy(true); setSaveError('');
        try { await discoveryApi.remove(item); setSaved(previous => previous.filter(value => selectionKey(value) !== selectionKey(item))); setNotice('Saved option removed.'); }
        catch { setSaveError('Could not remove this option. Please retry.'); }
        finally { setBusy(false); }
    }
    async function addPlatform(categoryId: string, name: string) {
        const response = await discoveryApi.addPlatform(categoryId, name);
        const refreshed = await discoveryApi.get();
        setCategories(refreshed.data.categories);
        return response.data.id;
    }
    return <section className="mb-10 space-y-5" aria-labelledby="investment-discovery-title">
        <div className="flex flex-wrap items-center justify-between gap-3"><div className="flex items-center gap-2"><Sparkles className="h-5 w-5 text-emerald-600" /><h2 id="investment-discovery-title" className="text-lg font-bold text-slate-900">Investments</h2></div>
            <div className="flex gap-2"><Button variant="outline" size="sm" onClick={() => void load()} disabled={loading || busy}><RefreshCw />Refresh holdings</Button>
                 <Dialog open={comparisonOpen} onOpenChange={setComparisonOpen}><DialogTrigger asChild><Button type="button" variant="outline" size="sm"><Scale />Saved comparisons ({saved.length})</Button></DialogTrigger>
                    <DialogContent className="max-h-[90dvh] overflow-y-auto rounded-2xl sm:max-w-4xl"><DialogHeader><DialogTitle>Compare investments</DialogTitle><DialogDescription>Revisit your saved options and compare two platforms within a category, or two different categories.</DialogDescription></DialogHeader>
                        {saveError && <p role="alert" className="text-sm text-red-600">{saveError}</p>}
                        <p role="status" className="text-xs text-emerald-700">{notice}</p>
                         <ComparisonPanel categories={categories} riskProfile={riskProfile} saved={saved} busy={busy} save={save} remove={remove} onSecondOpinion={prompt => { setComparisonOpen(false); requestAnimationFrame(() => askForSecondOpinion(prompt)); }} />
                    </DialogContent></Dialog>
            </div></div>
        <p className="text-sm text-slate-500">Explore types you do not own first, then review existing investments. Mean–variance analysis balances historical growth with price swings where comparable history exists.</p>
        <p className="text-xs text-slate-400">Fund wrappers and asset exposures can overlap. These are discovery routes, not a complete asset allocation. Missing assets are not automatically suitable investments.</p>
        {loading ? <div role="status" className="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-500">Loading investment options…</div> : error ? <p role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p> : <>
            {saveError && <p role="alert" className="rounded-xl bg-amber-50 p-3 text-xs text-amber-700">{saveError}</p>}
            <p role="status" className="text-xs text-emerald-700">{notice}</p>
            <div className="space-y-4"><h3 className="text-sm font-semibold text-slate-800">Investment opportunities for you</h3>
                 <div className="space-y-4">{categories.filter(category => !category.owned).map(category => <InvestmentCard key={category.id} category={category} saved={saved} busy={busy} save={save} addPlatform={addPlatform} />)}</div>
                {!categories.some(category => !category.owned) && <p className="text-sm text-slate-400">All listed categories appear in your holdings.</p>}
            </div>
        </>}
        {children && <div className="pt-3">{children}</div>}
        {!loading && !error && <div className="space-y-4"><h3 className="text-sm font-semibold text-slate-800">Already in your portfolio</h3>
             <div className="space-y-4">{categories.filter(category => category.owned).map(category => <InvestmentCard key={category.id} category={category} saved={saved} busy={busy} save={save} addPlatform={addPlatform} />)}</div>
            {!categories.some(category => category.owned) && <p className="text-sm text-slate-400">No holdings recorded in these categories yet.</p>}
        </div>}
    </section>;
}
