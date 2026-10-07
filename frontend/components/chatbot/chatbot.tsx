'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { MessageCircle, X, Send, Bot, User, ShieldCheck } from 'lucide-react';
import type { ChatAnalysisSection, ChatMessage } from '@/types';
import { chatApi } from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import { usePathname } from 'next/navigation';
import { isAxiosError } from 'axios';
import { CHAT_VIEW_CONTEXT_EVENT, type ChatViewContext } from '@/lib/chat-view-context';
import { useUser } from '@/contexts/user-context';

// ==========================================
// Constants
// ==========================================
const quickActionGroups = [
    { title: 'Start here', actions: [{ label: 'Explain this page', prompt: 'Explain the key points on the page I am viewing, using my records in plain language.' }, { label: 'What do I own?', prompt: 'Summarize the asset types in my portfolio in plain language.' }] },
    { title: 'Check my finances', actions: [{ label: 'Spot my risks', prompt: 'What are the main measurable risks in my portfolio right now?' }, { label: 'Check cash flow', prompt: 'How much money is coming in and going out, based on my records?' }] },
    { title: 'Plan next steps', actions: [{ label: 'Compare options', prompt: 'Give me a second opinion on the investment options in Insights using my portfolio, goals, risk profile, costs and available evidence. Explain what is unknown.' }, { label: 'Track my goals', prompt: 'How am I doing against my recorded financial goals?' }] },
];

const metricLabels: Record<string, { label: string; currency?: boolean }> = {
    net_worth: { label: 'Net worth', currency: true }, total_income: { label: 'Money in', currency: true },
    total_expenses: { label: 'Money out', currency: true }, surplus: { label: 'Remaining', currency: true },
    estimated_capital_gains_tax: { label: 'Estimated tax', currency: true }, anomaly_count: { label: 'Unusual transactions' },
};
const sectionNames: Record<string, string> = { portfolio: 'Your portfolio', cashflow: 'Cash flow', tax: 'Tax picture', guardian: 'Account activity' };

function followUpsFor(intent?: string, page?: string): string[] {
    if (intent === 'portfolio' || intent === 'multi_agent') return ['Which holding needs attention?', 'Explain my portfolio risk'];
    if (intent === 'tax') return ['What is my 80C headroom?', 'Explain the tax estimate'];
    if (intent === 'cashflow') return ['Where did I spend most?', 'Can I improve my cash buffer?'];
    if (page === '/insights') return ['Explain my top opportunity', 'How does this affect my goal?'];
    return ['Summarize my holdings', 'What should I look at next?'];
}

function InsightCard({ section }: { section: ChatAnalysisSection }) {
    const metrics = Object.entries(section.metrics || {}).filter(([key, value]) => key in metricLabels && typeof value === 'number' && Number.isFinite(value)).slice(0, 2);
    const coverage = section.specialist === 'portfolio' && typeof section.metrics?.valuation_coverage === 'number'
        ? Math.round(Math.max(0, Math.min(1, section.metrics.valuation_coverage)) * 100) : null;
    if (!metrics.length && coverage === null) return null;
    return <div className="mt-3 rounded-xl border border-emerald-100 bg-white p-3 shadow-sm">
        <p className="mb-2 text-xs font-semibold text-slate-700">{sectionNames[section.specialist] || section.specialist}</p>
        <div className="grid grid-cols-2 gap-2">{metrics.map(([key, value]) => <div key={key} className="rounded-lg bg-slate-50 p-2">
            <p className="text-[11px] text-slate-500">{metricLabels[key].label}</p>
            <p className="mt-0.5 text-sm font-semibold text-slate-900">{metricLabels[key].currency ? `₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : Number(value).toLocaleString('en-IN')}</p>
        </div>)}</div>
        {coverage !== null && <div className="mt-3"><div className="mb-1 flex justify-between text-[11px] text-slate-500"><span>Holdings with prices</span><span>{coverage}%</span></div>
            <div className="h-1.5 rounded-full bg-slate-100"><div className="h-1.5 rounded-full bg-emerald-500" style={{ width: `${coverage}%` }} /></div></div>}
    </div>;
}

function chatErrorMessage(error: unknown): string {
    if (!isAxiosError(error)) {
        return 'The assistant could not complete this request. Please try again.';
    }
    if (!error.response) {
        return error.code === 'ECONNABORTED'
            ? 'The assistant took too long to respond. Please try a shorter request.'
            : 'The QUANT API is not reachable. Confirm the backend is running on port 8000 and try again.';
    }
    if (error.response.status === 401) {
        return 'Your session has expired. Please sign in again before using the assistant.';
    }
    const payload = error.response.data as { detail?: unknown; message?: unknown; request_id?: unknown } | undefined;
    const safeDetail = typeof payload?.detail === 'string'
        ? payload.detail
        : typeof payload?.message === 'string'
            ? payload.message
            : null;
    if (safeDetail) return safeDetail;
    const requestId = typeof payload?.request_id === 'string'
        ? payload.request_id
        : error.response.headers?.['x-request-id'];
    return `The assistant service encountered a server error.${requestId ? ` Request ID: ${requestId}` : ''}`;
}

// ==========================================
// Thinking Indicator Component
// ==========================================
function ThinkingIndicator() {
    return (
        <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="flex items-start gap-2"
        >
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                <Bot className="h-4 w-4" />
            </div>
            <div className="rounded-2xl rounded-tl-md bg-gray-100 px-4 py-3">
                <div className="flex items-center gap-1.5">
                    {[0, 1, 2].map((i) => (
                        <motion.span
                            key={i}
                            className="block h-2 w-2 rounded-full bg-gray-400"
                            animate={{
                                y: [0, -6, 0],
                                opacity: [0.4, 1, 0.4],
                            }}
                            transition={{
                                duration: 0.8,
                                repeat: Infinity,
                                delay: i * 0.15,
                                ease: 'easeInOut',
                            }}
                        />
                    ))}
                    <span className="ml-1 text-xs text-gray-400">Thinking</span>
                </div>
            </div>
        </motion.div>
    );
}

// ==========================================
// Typing Effect Hook
// ==========================================
function useTypingEffect(
    fullText: string,
    isActive: boolean,
    onComplete: () => void
) {
    useEffect(() => {
        if (!isActive) return;
        const timer = setTimeout(onComplete, 180);
        return () => clearTimeout(timer);
    }, [isActive, onComplete]);

    return fullText ?? '';
}

// ==========================================
// Bot Message with Typing Effect
// ==========================================
function BotMessageBubble({
    message,
    isTyping,
    onTypingComplete,
    followUps,
    onFollowUp,
}: {
    message: ChatMessage;
    isTyping: boolean;
    onTypingComplete: () => void;
    followUps: string[];
    onFollowUp: (prompt: string) => void;
}) {
    const displayedText = useTypingEffect(
        message.content,
        isTyping,
        onTypingComplete
    );

    return (
        <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-start gap-2"
        >
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                <Bot className="h-4 w-4" />
            </div>
            <div className="max-w-[88%] rounded-2xl rounded-tl-md border border-stone-200/90 bg-stone-50/90 px-4 py-3 text-sm leading-relaxed text-stone-800 shadow-sm">
                <div className="prose prose-sm max-w-none text-stone-800">
                    <ReactMarkdown
                        components={{
                            h3: ({ node: _node, ...props }) => {
                                void _node;
                                return <h3 className="font-semibold text-stone-900 text-sm mt-3 mb-1.5 first:mt-0 tracking-tight" {...props} />;
                            },
                            h4: ({ node: _node, ...props }) => {
                                void _node;
                                return <h4 className="font-medium text-stone-800 text-xs mt-2 mb-1" {...props} />;
                            },
                            strong: ({ node: _node, ...props }) => {
                                void _node;
                                return <strong className="font-semibold text-emerald-950" {...props} />;
                            },
                            ul: ({ node: _node, ...props }) => {
                                void _node;
                                return <ul className="list-disc ml-4 my-2 space-y-1 text-stone-700" {...props} />;
                            },
                            ol: ({ node: _node, ...props }) => {
                                void _node;
                                return <ol className="list-decimal ml-4 my-2 space-y-1.5 text-stone-700" {...props} />;
                            },
                            li: ({ node: _node, ...props }) => {
                                void _node;
                                return <li className="my-0.5 leading-snug" {...props} />;
                            },
                            p: ({ node: _node, ...props }) => {
                                void _node;
                                return <p className="mb-2.5 last:mb-0 leading-relaxed text-stone-700" {...props} />;
                            },
                        }}
                    >
                        {displayedText}
                    </ReactMarkdown>
                </div>
                {!isTyping && message.analysis_sections?.map((section) => <InsightCard key={section.specialist} section={section} />)}
                {/* Blinking cursor while typing */}
                {isTyping && (
                    <span className="inline-block w-0.5 h-4 bg-gray-400 animate-pulse ml-0.5 align-text-bottom" />
                )}
                {!isTyping && message.citations && message.citations.length > 0 && (
                    <div className="mt-3 border-t border-gray-200 pt-2 text-xs text-gray-600">
                        <p className="mb-1 font-semibold text-gray-700">Evidence</p>
                        {message.citations.map((citation) => (
                            <p key={citation.citation_id}>
                                {citation.source_url ? <a className="text-blue-700 underline" href={citation.source_url} target="_blank" rel="noreferrer">{citation.title}</a> : citation.title}
                                {citation.authority ? ` · ${citation.authority}` : ''}
                            </p>
                        ))}
                    </div>
                )}
                {!isTyping && message.warnings && message.warnings.length > 0 && (
                    <div className="mt-2 rounded-lg bg-amber-50 p-2 text-xs text-amber-800">{message.warnings.join(' ')}</div>
                )}
                {!isTyping && followUps.length > 0 && <div className="mt-3 flex flex-wrap gap-1.5 border-t border-stone-200 pt-3">
                    {followUps.map(prompt => <button key={prompt} type="button" onClick={() => onFollowUp(prompt)} className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[11px] font-medium text-emerald-800 hover:bg-emerald-100">{prompt}</button>)}
                </div>}
            </div>
        </motion.div>
    );
}

// ==========================================
// User Message Bubble
// ==========================================
function UserMessageBubble({ message }: { message: ChatMessage }) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-start gap-2 flex-row-reverse"
        >
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gray-100 text-gray-600">
                <User className="h-4 w-4" />
            </div>
            <div className="max-w-[75%] rounded-2xl rounded-tr-md bg-emerald-600 px-3.5 py-2.5 text-sm leading-relaxed text-white">
                {message.content}
            </div>
        </motion.div>
    );
}

// ==========================================
// Main Chatbot Component
// ==========================================
export default function Chatbot() {
    const pathname = usePathname();
    const prefersReducedMotion = useReducedMotion();
    const { user } = useUser();
    const [isOpen, setIsOpen] = useState(false);
    const [disclaimerOpen, setDisclaimerOpen] = useState(false);
    const [pendingAutoPrompt, setPendingAutoPrompt] = useState<string | null>(null);
    const [messages, setMessages] = useState<ChatMessage[]>([
        {
            id: '1',
            sender: 'bot',
            content:
                "Hi! I'm Quant Assistant. What would you like to ask today?",
            timestamp: new Date(),
        },
    ]);
    const [inputValue, setInputValue] = useState('');
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [isThinking, setIsThinking] = useState(false);
    const [typingMessageId, setTypingMessageId] = useState<string | null>(null);
    const [isSending, setIsSending] = useState(false);
    const [viewContext, setViewContext] = useState<ChatViewContext | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const sendingRef = useRef(false);
    const acknowledgmentKey = `quant-chat-notice-v1:${user?.user_id || 'guest'}`;
    const openChat = () => {
        try { setDisclaimerOpen(window.localStorage.getItem(acknowledgmentKey) !== 'yes'); }
        catch { setDisclaimerOpen(true); }
        setIsOpen(true);
    };
    useEffect(() => {
        if (!isOpen) return;
        try { setDisclaimerOpen(window.localStorage.getItem(acknowledgmentKey) !== 'yes'); }
        catch { setDisclaimerOpen(true); }
    }, [isOpen, acknowledgmentKey]);
    useEffect(() => {
        const updateContext = (event: Event) => setViewContext((event as CustomEvent<ChatViewContext>).detail);
        window.addEventListener(CHAT_VIEW_CONTEXT_EVENT, updateContext);
        return () => window.removeEventListener(CHAT_VIEW_CONTEXT_EVENT, updateContext);
    }, []);

    // Auto-scroll to bottom when messages change OR during typing
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isThinking, typingMessageId]);

    const handleTypingComplete = useCallback(() => {
        setTypingMessageId(null);
    }, []);

    const addMessage = (
        sender: 'user' | 'bot',
        content: string,
        metadata?: Pick<ChatMessage, 'citations' | 'warnings' | 'analysis_sections' | 'intent'>
    ): string => {
        const id = crypto.randomUUID();
        setMessages((prev) => [
            ...prev,
            { id, sender, content, timestamp: new Date(), ...metadata },
        ]);
        return id;
    };

    const sendMessageToServer = async (text: string) => {
        if (sendingRef.current) return;
        sendingRef.current = true;
        setIsSending(true);
        setIsThinking(true);

        try {
            const pageHint = pathname === '/dashboard' || pathname === '/insights'
                ? `Active page: ${pathname === '/dashboard' ? 'Dashboard' : 'Insights'}. ${viewContext?.path === pathname ? viewContext.hint : ''}`
                : undefined;
            const resp = await chatApi.sendMessage(
                text,
                conversationId || undefined,
                pageHint,
            );
            const data = resp.data;

            // Hide thinking, add bot message, start typing effect
            setIsThinking(false);
            const botMsgId = addMessage('bot', data.reply, {
                citations: data.citations,
                warnings: data.warnings,
                analysis_sections: data.analysis_sections,
                intent: data.intent,
            });
            setTypingMessageId(botMsgId);
            setConversationId(data.conversation_id);
        } catch (error) {
            console.warn('Chat request failed:', error);
            setIsThinking(false);
            const errorId = addMessage(
                'bot',
                chatErrorMessage(error)
            );
            setTypingMessageId(errorId);
        } finally {
            sendingRef.current = false;
            setIsSending(false);
        }
    };

    const sendPrompt = (prompt: string) => {
        if (sendingRef.current || disclaimerOpen) return;
        addMessage('user', prompt);
        void sendMessageToServer(prompt);
    };

    const handleSend = async () => {
        if (!inputValue.trim() || isSending || disclaimerOpen) return;
        const msg = inputValue.trim();
        setInputValue('');
        addMessage('user', msg);
        await sendMessageToServer(msg);
    };

    useEffect(() => {
        const handleOpenChat = (event: Event) => {
            openChat();
            const { prompt, autoSend } = (event as CustomEvent<{ prompt?: string; autoSend?: boolean }>).detail || {};
            if (!prompt) return;
            if (autoSend && !sendingRef.current) {
                setInputValue('');
                let acknowledged = false;
                try { acknowledged = window.localStorage.getItem(acknowledgmentKey) === 'yes'; } catch { /* Show notice below. */ }
                if (acknowledged) sendPrompt(prompt);
                else setPendingAutoPrompt(prompt);
            } else if (!autoSend) {
                setInputValue(prompt);
            }
        };
        window.addEventListener('open-chatbot', handleOpenChat);
        return () => window.removeEventListener('open-chatbot', handleOpenChat);
    });

    const acknowledgeNotice = () => {
        try { window.localStorage.setItem(acknowledgmentKey, 'yes'); } catch { /* Current session still proceeds. */ }
        setDisclaimerOpen(false);
        if (pendingAutoPrompt) {
            const prompt = pendingAutoPrompt;
            setPendingAutoPrompt(null);
            addMessage('user', prompt);
            void sendMessageToServer(prompt);
        }
    };

    if (pathname === '/' || pathname === '/login' || pathname === '/register') return null;

    return (
        <>
            <span id="quant-chat-layout-signal" data-open={isOpen ? 'true' : 'false'} hidden aria-hidden="true" />
            {/* Floating Button */}
            <AnimatePresence>
                {!isOpen && (
                    <motion.button
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0, opacity: 0 }}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={openChat}
                        className="fixed bottom-6 right-6 z-[9999] flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-emerald-600 to-teal-600 text-white shadow-lg shadow-emerald-900/50 transition-shadow hover:shadow-xl hover:shadow-emerald-900/60"
                        aria-label="Open chat"
                    >
                        <MessageCircle className="h-6 w-6" />
                    </motion.button>
                )}
            </AnimatePresence>

            {/* Tooltip */}
            <AnimatePresence>
                {!isOpen && (
                    <motion.div
                        initial={{ opacity: 0, x: 10 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 10 }}
                        className="fixed bottom-8 right-[88px] z-[9999] hidden rounded-lg bg-gray-800 px-3 py-1.5 text-sm font-medium text-white shadow-lg sm:block"
                    >
                        Ask anything
                        <div className="absolute -right-1 top-1/2 h-2 w-2 -translate-y-1/2 rotate-45 bg-gray-800" />
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Chat Window */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={prefersReducedMotion ? false : { x: '100%' }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ x: '100%' }}
                        transition={{ duration: prefersReducedMotion ? 0 : 0.4, ease: [0.22, 1, 0.36, 1] }}
                        className="fixed inset-y-0 right-0 z-[9999] flex h-dvh w-full flex-col overflow-hidden border-l border-gray-200 bg-white shadow-2xl will-change-transform lg:w-[var(--quant-chat-panel-width)]"
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between bg-gradient-to-r from-emerald-600 to-teal-600 px-5 py-4">
                            <div className="flex items-center gap-3">
                                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/20 backdrop-blur-sm">
                                    <Bot className="h-5 w-5 text-white" />
                                </div>
                                <div>
                                    <h3 className="text-sm font-semibold text-white">
                                        Quant Assistant
                                    </h3>
                                    <p className="text-[11px] text-blue-100">
                                        {isThinking
                                            ? 'Thinking...'
                                            : typingMessageId
                                                ? 'Typing...'
                                                : 'Always here to help'}
                                    </p>
                                </div>
                                <span className="rounded-full bg-white/15 px-2 py-1 text-[10px] font-medium text-white"><ShieldCheck className="mr-1 inline h-3 w-3" />Scoped context</span>
                            </div>
                            <button
                                onClick={() => setIsOpen(false)}
                                className="rounded-full p-1.5 text-white/80 transition-colors hover:bg-white/20 hover:text-white"
                                aria-label="Close chat"
                            >
                                <X className="h-4 w-4" />
                            </button>
                        </div>

                         <div className="border-b border-slate-100 bg-slate-50/70 px-4 py-3" aria-label="Quick questions">
                             <div className="space-y-2.5">{quickActionGroups.map(group => <div key={group.title} className="space-y-1.5">
                                 <p className="text-[11px] font-semibold text-slate-600">{group.title}</p>
                                 <div className="grid grid-cols-2 gap-1.5">{group.actions.map(action => <button key={action.label} type="button" disabled={isSending || disclaimerOpen} onClick={() => sendPrompt(action.prompt)}
                                     className="min-w-0 rounded-full border border-slate-200 bg-white px-2.5 py-1 text-center text-[11px] font-medium text-slate-700 hover:border-emerald-300 hover:text-emerald-700 disabled:opacity-50">{action.label}</button>)}</div>
                             </div>)}</div>
                        </div>

                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-3">
                            {messages.map((msg) =>
                                msg.sender === 'bot' ? (
                                    <BotMessageBubble
                                        key={msg.id}
                                        message={msg}
                                        isTyping={typingMessageId === msg.id}
                                        onTypingComplete={
                                            handleTypingComplete
                                        }
                                        followUps={msg.id === messages[messages.length - 1]?.id && msg.intent && !isSending ? followUpsFor(msg.intent, pathname) : []}
                                        onFollowUp={sendPrompt}
                                    />
                                ) : (
                                    <UserMessageBubble
                                        key={msg.id}
                                        message={msg}
                                    />
                                )
                            )}

                            {/* Thinking Animation */}
                            <AnimatePresence>
                                {isThinking && <ThinkingIndicator />}
                            </AnimatePresence>

                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input */}
                        <div className="border-t border-gray-100 p-3">
                            <form
                                onSubmit={(e) => {
                                    e.preventDefault();
                                    handleSend();
                                }}
                                className="flex items-center gap-2"
                            >
                                <input
                                    type="text"
                                    value={inputValue}
                                    onChange={(e) =>
                                        setInputValue(e.target.value)
                                    }
                                    placeholder={
                                        isSending
                                            ? 'Waiting for response...'
                                            : 'Type your message...'
                                    }
                                    disabled={isSending || disclaimerOpen}
                                    className="flex-1 rounded-full border border-gray-200 bg-gray-50 px-4 py-2.5 text-sm outline-none transition-colors focus:border-blue-300 focus:bg-white focus:ring-2 focus:ring-blue-100 disabled:opacity-50 disabled:cursor-not-allowed"
                                />
                                <button
                                    type="submit"
                                    disabled={!inputValue.trim() || isSending || disclaimerOpen}
                                    className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-600 text-white transition-all hover:bg-emerald-700 disabled:opacity-40 disabled:hover:bg-emerald-600"
                                    aria-label="Send message"
                                >
                                    <Send className="h-4 w-4" />
                                </button>
                            </form>
                        </div>
                        {disclaimerOpen && <div className="absolute inset-0 z-20 flex items-center justify-center bg-white/95 p-6" role="dialog" aria-modal="true" aria-labelledby="chat-notice-title">
                            <div className="w-full rounded-2xl border border-slate-200 bg-white p-6 shadow-xl">
                                <button type="button" aria-label="Close chat notice" onClick={() => { setIsOpen(false); setPendingAutoPrompt(null); }} className="float-right rounded-full p-1 text-slate-500 hover:bg-slate-100"><X className="h-4 w-4" /></button>
                                <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700"><ShieldCheck className="h-5 w-5" /></div>
                                <h3 id="chat-notice-title" className="text-lg font-semibold text-slate-950">Before we chat</h3>
                                <p className="mt-2 text-sm leading-6 text-slate-600">QUANT explains your financial records and research; it is not a financial advisor. Investment values can change, and any decision should fit your circumstances. Chat messages are saved to your account.</p>
                                <button type="button" onClick={acknowledgeNotice} className="mt-5 w-full rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700">I understand</button>
                            </div>
                        </div>}
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}
