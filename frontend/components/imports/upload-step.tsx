import { SecurityBadge } from '@/components/ui/security-badge';

export function UploadStep({ number, title, security }: { number: number; title: string; security: string }) {
    return <div className="mb-3 space-y-1.5">
        <div className="flex flex-wrap items-center gap-2"><h2 className="text-xs font-bold uppercase tracking-widest text-stone-500">
            <span className="mr-2 text-stone-950">{String(number).padStart(2, '0')}</span>{title}
        </h2><SecurityBadge label="Protected import" /></div>
        <p className="text-xs leading-relaxed text-stone-500">{security}</p>
    </div>;
}
