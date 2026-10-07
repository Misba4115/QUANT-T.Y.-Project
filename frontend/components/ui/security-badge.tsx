import { ShieldCheck } from 'lucide-react';

export function SecurityBadge({ label }: { label: string }) {
    return <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold normal-case tracking-normal text-emerald-800">
        <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />{label}
    </span>;
}
