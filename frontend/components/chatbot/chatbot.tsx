'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X, Send, Bot, User } from 'lucide-react';
import type { ChatMessage, ChatOption } from '@/types';

const chatOptions: ChatOption[] = [
    'Stock Market Queries',
    'Mutual Fund Queries',
    'Investment Queries',
    'Portfolio Analysis',
    'Tax Saving Queries',
];

const placeholderResponses: Record<ChatOption, string> = {
    'Stock Market Queries':
        'I can help you with stock market analysis, recommendations, and trends. Our RAG-based analysis system is being set up — stay tuned for real-time insights!',
    'Mutual Fund Queries':
        'I can assist with mutual fund selection, SIP calculations, and fund comparisons. The full analysis engine will be available soon!',
    'Investment Queries':
        'Looking for investment advice? I can guide you on portfolio diversification, asset allocation, and investment strategies. Detailed analysis coming soon!',
    'Portfolio Analysis':
        'I can analyze your portfolio performance, risk metrics, and suggest rebalancing strategies. Advanced portfolio analytics are being integrated!',
    'Tax Saving Queries':
        'I can help you understand Section 80C, 80D, and other tax-saving options. Detailed tax optimization recommendations coming soon!',
};

export default function Chatbot() {
    const [isOpen, setIsOpen] = useState(false);
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
    const [showOptions, setShowOptions] = useState(true);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [isHydrated, setIsHydrated] = useState(false);

    useEffect(() => {
        setIsHydrated(true);
    }, []);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const addMessage = (sender: 'user' | 'bot', content: string) => {
        setMessages((prev) => [
            ...prev,
            {
                id: `${Date.now()}-${Math.random()}`,
                sender,
                content,
                timestamp: new Date(),
            },
        ]);
    };

    const handleOptionClick = (option: ChatOption) => {
        setShowOptions(false);
        addMessage('user', option);
        setTimeout(() => {
            addMessage('bot', placeholderResponses[option]);
            setTimeout(() => setShowOptions(true), 500);
        }, 800);
    };

    const handleSend = () => {
        if (!inputValue.trim()) return;
        const msg = inputValue.trim();
        setInputValue('');
        setShowOptions(false);
        addMessage('user', msg);
        setTimeout(() => {
            addMessage(
                'bot',
                "Thanks for your question! I'm currently in demo mode. Once the backend RAG system is connected, I'll provide detailed, data-driven answers."
            );
            setTimeout(() => setShowOptions(true), 500);
        }, 1000);
    };

    return (
        <>
            {/* Floating Button */}
            <AnimatePresence>
                {!isOpen && (
                    <motion.button
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0, opacity: 0 }}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => setIsOpen(true)}
                        className="fixed bottom-6 right-6 z-[9999] flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-300/50 transition-shadow hover:shadow-xl hover:shadow-blue-300/60"
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
                        initial={{ opacity: 0, y: 20, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 20, scale: 0.95 }}
                        transition={{ duration: 0.25, ease: 'easeOut' }}
                        className="fixed bottom-6 right-6 z-[9999] flex h-[520px] w-[380px] flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-2xl"
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between bg-gradient-to-r from-blue-600 to-indigo-600 px-5 py-4">
                            <div className="flex items-center gap-3">
                                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/20 backdrop-blur-sm">
                                    <Bot className="h-5 w-5 text-white" />
                                </div>
                                <div>
                                    <h3 className="text-sm font-semibold text-white">
                                        Quant Assistant
                                    </h3>
                                    <p className="text-[11px] text-blue-100">
                                        Always here to help
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={() => setIsOpen(false)}
                                className="rounded-full p-1.5 text-white/80 transition-colors hover:bg-white/20 hover:text-white"
                                aria-label="Close chat"
                            >
                                <X className="h-4 w-4" />
                            </button>
                        </div>

                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-3">
                            {messages.map((msg) => (
                                <motion.div
                                    key={msg.id}
                                    initial={{ opacity: 0, y: 8 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={`flex items-start gap-2 ${msg.sender === 'user' ? 'flex-row-reverse' : ''
                                        }`}
                                >
                                    <div
                                        className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${msg.sender === 'bot'
                                                ? 'bg-blue-100 text-blue-600'
                                                : 'bg-gray-100 text-gray-600'
                                            }`}
                                    >
                                        {msg.sender === 'bot' ? (
                                            <Bot className="h-4 w-4" />
                                        ) : (
                                            <User className="h-4 w-4" />
                                        )}
                                    </div>
                                    <div
                                        className={`max-w-[75%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${msg.sender === 'bot'
                                                ? 'rounded-tl-md bg-gray-100 text-gray-800'
                                                : 'rounded-tr-md bg-blue-600 text-white'
                                            }`}
                                    >
                                        {msg.content}
                                    </div>
                                </motion.div>
                            ))}

                            {/* Quick Options */}
                            <AnimatePresence>
                                {showOptions && (
                                    <motion.div
                                        initial={{ opacity: 0, height: 0 }}
                                        animate={{ opacity: 1, height: 'auto' }}
                                        exit={{ opacity: 0, height: 0 }}
                                        className="flex flex-wrap gap-1.5 pt-1"
                                    >
                                        {chatOptions.map((option) => (
                                            <button
                                                key={option}
                                                onClick={() => handleOptionClick(option)}
                                                className="rounded-full border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs font-medium text-blue-700 transition-all hover:bg-blue-100 hover:border-blue-300"
                                            >
                                                {option}
                                            </button>
                                        ))}
                                    </motion.div>
                                )}
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
                                    onChange={(e) => setInputValue(e.target.value)}
                                    placeholder="Type your message..."
                                    className="flex-1 rounded-full border border-gray-200 bg-gray-50 px-4 py-2.5 text-sm outline-none transition-colors focus:border-blue-300 focus:bg-white focus:ring-2 focus:ring-blue-100"
                                />
                                <button
                                    type="submit"
                                    disabled={!inputValue.trim()}
                                    className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-600 text-white transition-all hover:bg-blue-700 disabled:opacity-40 disabled:hover:bg-blue-600"
                                    aria-label="Send message"
                                >
                                    <Send className="h-4 w-4" />
                                </button>
                            </form>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}
