'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion, useInView, useScroll, useTransform } from 'framer-motion';
import { ArrowRight, BarChart3, Lock, Shield, ShieldCheck, Sparkles, TrendingUp, Zap } from 'lucide-react';
import { useUser } from '@/contexts/user-context';

/* ───────── Animated Background ───────── */
function AnimatedBackground() {
    return (
        <div className="fixed inset-0 z-0 overflow-hidden bg-neutral-950">
            <motion.div
                animate={{
                    scale: [1, 1.2, 1],
                    opacity: [0.3, 0.5, 0.3],
                    rotate: [0, 90, 0],
                }}
                transition={{
                    duration: 20,
                    repeat: Infinity,
                    ease: 'linear',
                }}
                className="absolute -top-[20%] -left-[10%] h-[70vh] w-[70vw] rounded-full bg-emerald-900/20 blur-[120px]"
            />
            <motion.div
                animate={{
                    scale: [1, 1.5, 1],
                    opacity: [0.2, 0.4, 0.2],
                    rotate: [0, -90, 0],
                }}
                transition={{
                    duration: 25,
                    repeat: Infinity,
                    ease: 'linear',
                }}
                className="absolute -bottom-[20%] -right-[10%] h-[80vh] w-[80vw] rounded-full bg-teal-900/20 blur-[150px]"
            />
            <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-overlay"></div>
        </div>
    );
}

/* ───────── Animated section wrapper ───────── */
function Reveal({ children, className = '', delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
    const ref = useRef(null);
    const inView = useInView(ref, { once: true, margin: '-60px' });
    return (
        <motion.div
            ref={ref}
            initial={{ opacity: 0, y: 40 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1], delay }}
            className={className}
        >
            {children}
        </motion.div>
    );
}

/* ───────── Nav pill indicator ───────── */
function NavPill({ items }: { items: { label: string; href: string }[] }) {
    const [hovered, setHovered] = useState<string | null>(null);
    return (
        <nav className="hidden items-center gap-1 rounded-full border border-neutral-800 bg-neutral-950/50 px-1.5 py-1.5 backdrop-blur-xl md:flex">
            {items.map((item) => (
                <a
                    key={item.href}
                    href={item.href}
                    className="relative rounded-full px-4 py-1.5 text-sm font-medium text-neutral-400 transition-colors hover:text-white"
                    onMouseEnter={() => setHovered(item.href)}
                    onMouseLeave={() => setHovered(null)}
                >
                    {hovered === item.href && (
                        <motion.span
                            layoutId="landing-nav-pill"
                            className="absolute inset-0 rounded-full bg-neutral-800"
                            transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                        />
                    )}
                    <span className="relative z-10">{item.label}</span>
                </a>
            ))}
        </nav>
    );
}

/* ───────── Bento security card ───────── */
function BentoCard({ icon: Icon, title, description, delay }: { icon: React.ElementType; title: string; description: string; delay: number }) {
    return (
        <Reveal delay={delay}>
            <motion.div
                whileHover={{ y: -4, transition: { duration: 0.2 } }}
                className="group rounded-2xl border border-neutral-800 bg-neutral-900/50 p-6 shadow-2xl backdrop-blur-sm transition-all hover:border-neutral-700 hover:bg-neutral-900/80"
            >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-950/50 text-emerald-400 transition-colors group-hover:bg-emerald-900/50 border border-emerald-900/50">
                    <Icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 font-semibold text-white">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-neutral-400">{description}</p>
            </motion.div>
        </Reveal>
    );
}

/* ───────── Insight card ───────── */
function InsightCard({ category, title, readTime, delay }: { category: string; title: string; readTime: string; delay: number }) {
    return (
        <Reveal delay={delay}>
            <motion.div
                whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
                className="group cursor-pointer overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/50 shadow-2xl backdrop-blur-sm transition-all hover:border-neutral-700 hover:bg-neutral-900/80"
            >
                <div className="h-40 bg-gradient-to-br from-neutral-800 to-emerald-950/30 transition-transform group-hover:scale-105" />
                <div className="p-5">
                    <span className="rounded-full bg-emerald-950/50 px-3 py-1 text-xs font-medium text-emerald-400 border border-emerald-900/50">{category}</span>
                    <h3 className="mt-3 font-semibold text-white line-clamp-2">{title}</h3>
                    <p className="mt-2 text-xs text-neutral-500">{readTime}</p>
                </div>
            </motion.div>
        </Reveal>
    );
}

/* ═════════════════════════════════════════════ */
/*  LANDING PAGE CONTENT                        */
/* ═════════════════════════════════════════════ */
function LandingPageContent() {
    const heroRef = useRef(null);
    const { scrollYProgress } = useScroll({ target: heroRef, offset: ['start start', 'end start'] });
    const heroOpacity = useTransform(scrollYProgress, [0, 1], [1, 0]);
    const heroScale = useTransform(scrollYProgress, [0, 1], [1, 0.95]);

    const navItems = [
        { label: 'About', href: '#about' },
        { label: 'Privacy & Security', href: '#security' },
        { label: 'Financial Insights', href: '#insights' },
    ];

    return (
        <div className="min-h-screen bg-neutral-950 text-white selection:bg-emerald-500/30 relative">
            <AnimatedBackground />
            {/* ── HEADER ── */}
            <motion.header
                initial={{ y: -30, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.6, ease: 'easeOut' }}
                className="sticky top-0 z-50 border-b border-neutral-800/60 bg-neutral-950/40 backdrop-blur-2xl"
            >
                <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
                    <Link href="/" className="flex items-center gap-2.5">
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-900 shadow-md shadow-emerald-900/50">
                            <span className="text-lg font-bold text-white">Q</span>
                        </div>
                        <span className="text-xl font-bold tracking-tight text-white">QUANT</span>
                    </Link>

                    <NavPill items={navItems} />

                    <div className="flex items-center gap-3">
                        <Link href="/login" className="rounded-full px-4 py-2 text-sm font-medium text-neutral-300 transition-colors hover:bg-neutral-800/60 hover:text-white">
                            Log In
                        </Link>
                        <Link href="/register" className="rounded-full bg-emerald-600 px-5 py-2 text-sm font-semibold text-white shadow-[0_0_15px_rgba(5,150,105,0.3)] transition-all hover:bg-emerald-500 hover:shadow-[0_0_25px_rgba(5,150,105,0.5)] hover:scale-[1.02]">
                            Get Started
                        </Link>
                    </div>
                </div>
            </motion.header>

            {/* ── HERO ── */}
            <motion.section ref={heroRef} style={{ opacity: heroOpacity, scale: heroScale }} className="relative z-10 overflow-hidden pb-20 pt-16 sm:pb-28 sm:pt-24">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <div className="mx-auto max-w-3xl text-center">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 0.2 }}
                        >
                            <span className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-4 py-1.5 text-sm font-medium text-emerald-300 backdrop-blur-md">
                                <Sparkles className="h-3.5 w-3.5" /> AI-Powered Financial Intelligence
                            </span>
                        </motion.div>

                        <motion.h1
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.7, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
                            className="mt-8 text-5xl font-bold leading-[1.1] tracking-tight text-white sm:text-6xl lg:text-7xl drop-shadow-2xl"
                        >
                            Your finances,{' '}
                            <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent drop-shadow-[0_0_30px_rgba(52,211,153,0.3)]">
                                clarified
                            </span>
                        </motion.h1>

                        <motion.p
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.6, delay: 0.5 }}
                            className="mt-6 text-lg leading-relaxed text-neutral-300 sm:text-xl drop-shadow-md"
                        >
                            Track your net worth, analyze investments, optimize taxes, and get
                            AI-powered insights — all from one beautifully simple dashboard.
                        </motion.p>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 0.7 }}
                            className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center"
                        >
                            <Link
                                href="/register"
                                className="group flex items-center gap-2 rounded-full bg-emerald-500 px-8 py-3.5 text-base font-semibold text-neutral-950 shadow-[0_0_20px_rgba(16,185,129,0.4)] transition-all hover:bg-emerald-400 hover:shadow-[0_0_30px_rgba(16,185,129,0.6)] hover:scale-[1.02]"
                            >
                                Start for free
                                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                            </Link>
                            <Link
                                href="/login"
                                className="flex items-center gap-2 rounded-full border border-neutral-700 bg-neutral-900/50 backdrop-blur-md px-8 py-3.5 text-base font-medium text-white transition-all hover:bg-neutral-800 hover:border-neutral-600"
                            >
                                Sign in
                            </Link>
                        </motion.div>
                    </div>

                    {/* Feature row */}
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, delay: 0.9 }}
                        className="mx-auto mt-20 grid max-w-4xl gap-6 sm:grid-cols-3"
                    >
                        {[
                            { icon: BarChart3, label: 'Portfolio Tracking', desc: 'Real-time valuations across all asset classes' },
                            { icon: TrendingUp, label: 'Tax Optimization', desc: 'Evidence-based 80C tracking and reporting' },
                            { icon: Zap, label: 'AI Insights', desc: 'Smart analysis powered by your actual data' },
                        ].map((feat, i) => (
                            <motion.div
                                key={feat.label}
                                whileHover={{ y: -3 }}
                                className="flex items-start gap-4 rounded-2xl border border-neutral-800 bg-neutral-900/40 p-5 shadow-2xl backdrop-blur-md transition-all hover:border-neutral-700"
                            >
                                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                    <feat.icon className="h-5 w-5" />
                                </div>
                                <div>
                                    <p className="font-semibold text-white">{feat.label}</p>
                                    <p className="mt-1 text-sm text-neutral-400">{feat.desc}</p>
                                </div>
                            </motion.div>
                        ))}
                    </motion.div>
                </div>
            </motion.section>

            {/* ── GUIDE VIDEO PLACEHOLDER ── */}
            <section id="guide" className="relative z-10 py-16 sm:py-24">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <Reveal>
                        <p className="text-sm font-medium text-emerald-400">How it works</p>
                        <h2 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">
                            Get started in minutes
                        </h2>
                        <p className="mt-4 max-w-2xl text-lg text-neutral-400">
                            See how QUANT transforms your financial data into clear, actionable insights.
                        </p>
                    </Reveal>

                    {/* Step indicators */}
                    <Reveal delay={0.1}>
                        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-6">
                            {[
                                { step: '01', label: 'What QUANT does' },
                                { step: '02', label: 'What data to provide' },
                                { step: '03', label: 'How recommendations work' },
                            ].map((item, i) => (
                                <div key={item.step} className="flex items-center gap-2">
                                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-emerald-500/20 text-xs font-bold text-emerald-400 border border-emerald-500/30">
                                        {item.step}
                                    </span>
                                    <span className="text-sm text-neutral-300">{item.label}</span>
                                    {i < 2 && <span className="hidden text-neutral-700 sm:block">→</span>}
                                </div>
                            ))}
                        </div>
                    </Reveal>

                    {/* Video placeholder */}
                    <Reveal delay={0.2}>
                        <div className="mt-10 overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/60 shadow-2xl backdrop-blur-sm">
                            {/* Placeholder frame — replace the inner content with a real <video> or embed */}
                            <div className="relative flex aspect-video w-full items-center justify-center bg-gradient-to-br from-neutral-900 via-emerald-950/20 to-neutral-900">
                                {/* Decorative grid */}
                                <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0wIDBoNjB2NjBIMHoiLz48cGF0aCBkPSJNNjAgMEgwdjYwaDYwVjB6TTEgMWg1OHY1OEgxVjF6IiBmaWxsPSIjMjAyMDIwIiBmaWxsLW9wYWNpdHk9Ii4xIi8+PC9nPjwvc3ZnPg==')] opacity-20" />

                                {/* Play button */}
                                <div className="relative flex flex-col items-center gap-5">
                                    <motion.div
                                        whileHover={{ scale: 1.08 }}
                                        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                                        className="flex h-20 w-20 cursor-pointer items-center justify-center rounded-full bg-emerald-500 shadow-[0_0_40px_rgba(16,185,129,0.5)] transition-shadow hover:shadow-[0_0_60px_rgba(16,185,129,0.7)]"
                                    >
                                        <svg className="h-8 w-8 translate-x-0.5 text-neutral-950" viewBox="0 0 24 24" fill="currentColor">
                                            <path d="M8 5v14l11-7z" />
                                        </svg>
                                    </motion.div>
                                    <div className="text-center">
                                        <p className="text-base font-semibold text-white">Watch the walkthrough</p>
                                        <p className="mt-1 text-sm text-neutral-400">Video guide coming soon · ~3 min</p>
                                    </div>
                                </div>

                                {/* Corner label */}
                                <div className="absolute left-4 top-4 flex items-center gap-2 rounded-full border border-neutral-700 bg-neutral-900/80 px-3 py-1.5 text-xs text-neutral-400 backdrop-blur-md">
                                    <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
                                    AI Walkthrough
                                </div>
                            </div>

                            {/* Caption bar */}
                            <div className="flex flex-col gap-4 border-t border-neutral-800 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
                                <p className="text-sm text-neutral-400">
                                    Learn how to upload your holdings, set goals, and get your first recommendations.
                                </p>
                                <Link
                                    href="/register"
                                    className="group flex shrink-0 items-center gap-2 rounded-full bg-emerald-600 px-5 py-2 text-sm font-semibold text-white transition-all hover:bg-emerald-500 hover:scale-[1.02]"
                                >
                                    Get Started <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                                </Link>
                            </div>
                        </div>
                    </Reveal>
                </div>
            </section>

            {/* ── ABOUT ── */}
            <section id="about" className="relative z-10 py-20 sm:py-28">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <Reveal>
                        <p className="text-sm font-medium text-emerald-400">About QUANT</p>
                        <h2 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">
                            Financial intelligence,<br />built for clarity
                        </h2>
                    </Reveal>

                    <div className="mt-12 grid gap-12 lg:grid-cols-2">
                        <Reveal delay={0.1}>
                            <div className="space-y-6">
                                <p className="text-lg leading-relaxed text-neutral-400">
                                    QUANT transforms fragmented financial data into a single, verified picture of your wealth. No guesswork, no fabricated projections — only evidence-based measurements from your actual records.
                                </p>
                                <p className="text-lg leading-relaxed text-neutral-400">
                                    Whether you track stocks, mutual funds, ETFs, crypto, or bank accounts, QUANT normalizes every data source into a unified dashboard that reveals what matters most.
                                </p>
                            </div>
                        </Reveal>
                        <Reveal delay={0.2}>
                            <div className="grid gap-4 sm:grid-cols-2">
                                {[
                                    { value: '100%', label: 'Privacy-first' },
                                    { value: 'Zero', label: 'Fabricated data' },
                                    { value: 'Every', label: 'Asset class covered' },
                                    { value: 'Real-time', label: 'Market valuations' },
                                ].map((stat) => (
                                    <div key={stat.label} className="rounded-2xl border border-neutral-800 bg-neutral-900/50 p-5 backdrop-blur-md">
                                        <p className="text-2xl font-bold text-emerald-400">{stat.value}</p>
                                        <p className="mt-1 text-sm text-neutral-500">{stat.label}</p>
                                    </div>
                                ))}
                            </div>
                        </Reveal>
                    </div>
                </div>
            </section>

            {/* ── SECURITY BENTO ── */}
            <section id="security" className="relative z-10 py-20 sm:py-28">
                <div className="absolute inset-0 bg-neutral-950/80 backdrop-blur-3xl -z-10" />
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <Reveal>
                        <p className="text-sm font-medium text-emerald-400">Privacy & Security</p>
                        <h2 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">
                            Your data never leaves your control
                        </h2>
                        <p className="mt-4 max-w-2xl text-lg text-neutral-400">
                            Every layer of QUANT is designed with privacy at its core. No third-party sharing, no hidden analytics, no compromises.
                        </p>
                    </Reveal>

                    <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                        <BentoCard icon={Shield} title="Private Session Processing" description="All analysis happens within your encrypted session. Your raw data is never exposed to other users or external services." delay={0.1} />
                        <BentoCard icon={Lock} title="Client-Side Isolation" description="Financial parsing and normalization happen in isolated, stateless pipelines. Each session is fully sandboxed with zero cross-contamination." delay={0.2} />
                        <BentoCard icon={ShieldCheck} title="Bank-Grade Encryption" description="TLS 1.3 in transit, AES-256 at rest. Session tokens rotate automatically, and all credentials are stored using industry-standard hashing." delay={0.3} />
                        <BentoCard icon={Zap} title="Instant Data Deletion" description="Delete everything with a single click. No delayed queues, no hidden backups — your data is purged immediately and permanently." delay={0.4} />
                        <BentoCard icon={BarChart3} title="Evidence-Only Metrics" description="QUANT never fabricates projections or simulates history. Every number on your dashboard comes from a verified, traceable source." delay={0.5} />
                        <BentoCard icon={TrendingUp} title="No Third-Party Sharing" description="Your financial data is never sold, shared, or used for advertising. QUANT makes money from the product, not from your data." delay={0.6} />
                    </div>
                </div>
            </section>

            {/* ── FINANCIAL INSIGHTS ── */}
            <section id="insights" className="relative z-10 py-20 sm:py-28">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <Reveal>
                        <p className="text-sm font-medium text-emerald-400">Financial Insights</p>
                        <h2 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">
                            Smarter decisions, backed by data
                        </h2>
                        <p className="mt-4 max-w-2xl text-lg text-neutral-400">
                            Explore insights and strategies powered by real financial intelligence.
                        </p>
                    </Reveal>

                    <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                        <InsightCard category="Portfolio" title="How to track your true net worth without guessing" readTime="5 min read" delay={0.1} />
                        <InsightCard category="Tax" title="Maximizing 80C deductions: an evidence-based approach" readTime="4 min read" delay={0.2} />
                        <InsightCard category="Risk" title="Understanding portfolio risk beyond surface-level labels" readTime="6 min read" delay={0.3} />
                    </div>
                </div>
            </section>

            {/* ── FOOTER ── */}
            <footer className="relative z-10 border-t border-neutral-800 bg-neutral-950">
                <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
                    <div className="flex flex-col gap-8 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                            <Link href="/" className="flex items-center gap-2.5">
                                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-600 to-emerald-900">
                                    <span className="text-sm font-bold text-white">Q</span>
                                </div>
                                <span className="text-lg font-bold tracking-tight text-white">QUANT</span>
                            </Link>
                            <p className="mt-3 max-w-xs text-sm text-neutral-500">
                                Smart financial intelligence for modern investors.
                            </p>
                        </div>
                        <div className="grid gap-8 sm:grid-cols-3">
                            <div>
                                <p className="text-xs font-semibold uppercase tracking-wider text-neutral-600">Product</p>
                                <div className="mt-3 space-y-2">
                                    <a href="#about" className="block text-sm text-neutral-400 hover:text-white">About</a>
                                    <a href="#security" className="block text-sm text-neutral-400 hover:text-white">Security</a>
                                    <a href="#insights" className="block text-sm text-neutral-400 hover:text-white">Insights</a>
                                </div>
                            </div>
                            <div>
                                <p className="text-xs font-semibold uppercase tracking-wider text-neutral-600">Account</p>
                                <div className="mt-3 space-y-2">
                                    <Link href="/login" className="block text-sm text-neutral-400 hover:text-white">Log In</Link>
                                    <Link href="/register" className="block text-sm text-neutral-400 hover:text-white">Create Account</Link>
                                </div>
                            </div>
                            <div>
                                <p className="text-xs font-semibold uppercase tracking-wider text-neutral-600">Legal</p>
                                <div className="mt-3 space-y-2">
                                    <a href="#" className="block text-sm text-neutral-400 hover:text-white">Privacy Policy</a>
                                    <a href="#" className="block text-sm text-neutral-400 hover:text-white">Terms of Service</a>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="mt-10 border-t border-neutral-800 pt-6">
                        <p className="text-xs text-neutral-600">© 2026 QUANT. All rights reserved. This platform does not provide financial advice. All metrics are computed from user-supplied data and publicly available market information.</p>
                    </div>
                </div>
            </footer>
        </div>
    );
}

/* ═════════════════════════════════════════════ */
/*  WRAPPER                                     */
/* ═════════════════════════════════════════════ */
export default function LandingPage() {
    const router = useRouter();
    const { isAuthenticated, isLoading } = useUser();

    useEffect(() => {
        if (!isLoading && isAuthenticated) {
            router.replace('/dashboard');
        }
    }, [isAuthenticated, isLoading, router]);

    if (isLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-neutral-950">
                <div className="flex flex-col items-center gap-4">
                    <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-900 shadow-[0_0_30px_rgba(16,185,129,0.3)]">
                        <span className="text-2xl font-bold text-white">Q</span>
                    </div>
                    <div className="h-1.5 w-32 overflow-hidden rounded-full bg-neutral-800">
                        <div className="h-full w-1/2 animate-pulse rounded-full bg-emerald-500" />
                    </div>
                    <p className="text-sm text-neutral-500">Loading QUANT...</p>
                </div>
            </div>
        );
    }

    if (isAuthenticated) return null;

    return <LandingPageContent />;
}
