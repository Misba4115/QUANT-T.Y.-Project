'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X, Send, Bot, User } from 'lucide-react';
import type { ChatMessage, ChatOption } from '@/types';
import { chatApi } from '@/lib/api';
import ReactMarkdown from 'react-markdown';

// ==========================================
// Constants
// ==========================================
const TYPING_SPEED_MS = 18; // ms per character (fast & smooth)
const TYPING_CHUNK_SIZE = 3; // characters per tick for perceived speed

const chatOptions: ChatOption[] = [
    'Stock Market Queries',
    'Mutual Fund Queries',
    'Investment Queries',
    'Portfolio Analysis',
    'Tax Saving Queries',
];

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
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-600">
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
    const [displayedText, setDisplayedText] = useState('');
    const indexRef = useRef(0);
    const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        // Guard against undefined/null content during React state batching
        const text = fullText ?? '';

        // Reset when fullText changes
        if (!isActive) {
            setDisplayedText(text);
            indexRef.current = text.length;
            return;
        }

        indexRef.current = 0;
        setDisplayedText('');

        function tick() {
            indexRef.current = Math.min(
                indexRef.current + TYPING_CHUNK_SIZE,
                text.length
            );
            setDisplayedText(text.slice(0, indexRef.current));

            if (indexRef.current < text.length) {
                timerRef.current = setTimeout(tick, TYPING_SPEED_MS);
            } else {
                onComplete();
            }
        }

        // Small initial delay before typing starts
        timerRef.current = setTimeout(tick, 80);

        return () => {
            if (timerRef.current) clearTimeout(timerRef.current);
        };
    }, [fullText, isActive]); // eslint-disable-line react-hooks/exhaustive-deps

    return displayedText;
}

// ==========================================
// Bot Message with Typing Effect
// ==========================================
function BotMessageBubble({
    message,
    isTyping,
    onTypingComplete,
}: {
    message: ChatMessage;
    isTyping: boolean;
    onTypingComplete: () => void;
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
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-600">
                <Bot className="h-4 w-4" />
            </div>
            <div className="max-w-[75%] rounded-2xl rounded-tl-md bg-gray-100 px-3.5 py-2.5 text-sm leading-relaxed text-gray-800">
                <div className="prose prose-sm max-w-none">
                    <ReactMarkdown
                        components={{
                            strong: ({ node, ...props }) => (
                                <strong
                                    className="font-bold text-blue-700"
                                    {...props}
                                />
                            ),
                            ul: ({ node, ...props }) => (
                                <ul
                                    className="list-disc ml-4 my-2 space-y-1"
                                    {...props}
                                />
                            ),
                            li: ({ node, ...props }) => (
                                <li className="my-1" {...props} />
                            ),
                            p: ({ node, ...props }) => (
                                <p className="mb-2 last:mb-0" {...props} />
                            ),
                        }}
                    >
                        {displayedText}
                    </ReactMarkdown>
                </div>
                {/* Blinking cursor while typing */}
                {isTyping && (
                    <span className="inline-block w-0.5 h-4 bg-gray-400 animate-pulse ml-0.5 align-text-bottom" />
                )}
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
            <div className="max-w-[75%] rounded-2xl rounded-tr-md bg-blue-600 px-3.5 py-2.5 text-sm leading-relaxed text-white">
                {message.content}
            </div>
        </motion.div>
    );
}

// ==========================================
// Main Chatbot Component
// ==========================================
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
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [isThinking, setIsThinking] = useState(false);
    const [typingMessageId, setTypingMessageId] = useState<string | null>(null);
    const [isSending, setIsSending] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [isHydrated, setIsHydrated] = useState(false);

    useEffect(() => {
        setIsHydrated(true);
        const handleOpenChat = () => setIsOpen(true);
        window.addEventListener('open-chatbot', handleOpenChat);
        return () => window.removeEventListener('open-chatbot', handleOpenChat);
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
        content: string
    ): string => {
        const id = `${Date.now()}-${Math.random()}`;
        setMessages((prev) => [
            ...prev,
            { id, sender, content, timestamp: new Date() },
        ]);
        return id;
    };

    const sendMessageToServer = async (text: string) => {
        setIsSending(true);
        setIsThinking(true);

        try {
            const resp = await chatApi.sendMessage(
                text,
                conversationId || undefined
            );
            const data = resp.data;

            // Hide thinking, add bot message, start typing effect
            setIsThinking(false);
            const botMsgId = addMessage('bot', data.reply);
            setTypingMessageId(botMsgId);
            setConversationId(data.conversation_id);
        } catch (error) {
            console.error('Chat error:', error);
            setIsThinking(false);
            const errorId = addMessage(
                'bot',
                'Sorry, I encountered an error. Please try again.'
            );
            setTypingMessageId(errorId);
        } finally {
            setIsSending(false);
            setTimeout(() => setShowOptions(true), 500);
        }
    };

    const handleOptionClick = (option: ChatOption) => {
        if (isSending) return;
        setShowOptions(false);
        addMessage('user', option);
        sendMessageToServer(option);
    };

    const handleSend = async () => {
        if (!inputValue.trim() || isSending) return;
        const msg = inputValue.trim();
        setInputValue('');
        setShowOptions(false);
        addMessage('user', msg);
        await sendMessageToServer(msg);
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
                                        {isThinking
                                            ? 'Thinking...'
                                            : typingMessageId
                                              ? 'Typing...'
                                              : 'Always here to help'}
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
                            {messages.map((msg) =>
                                msg.sender === 'bot' ? (
                                    <BotMessageBubble
                                        key={msg.id}
                                        message={msg}
                                        isTyping={typingMessageId === msg.id}
                                        onTypingComplete={
                                            handleTypingComplete
                                        }
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

                            {/* Quick Options */}
                            <AnimatePresence>
                                {showOptions && !isThinking && !typingMessageId && (
                                    <motion.div
                                        initial={{ opacity: 0, height: 0 }}
                                        animate={{
                                            opacity: 1,
                                            height: 'auto',
                                        }}
                                        exit={{ opacity: 0, height: 0 }}
                                        className="flex flex-wrap gap-1.5 pt-1"
                                    >
                                        {chatOptions.map((option) => (
                                            <button
                                                key={option}
                                                onClick={() =>
                                                    handleOptionClick(option)
                                                }
                                                disabled={isSending}
                                                className="rounded-full border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs font-medium text-blue-700 transition-all hover:bg-blue-100 hover:border-blue-300 disabled:opacity-50 disabled:cursor-not-allowed"
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
                                    onChange={(e) =>
                                        setInputValue(e.target.value)
                                    }
                                    placeholder={
                                        isSending
                                            ? 'Waiting for response...'
                                            : 'Type your message...'
                                    }
                                    disabled={isSending}
                                    className="flex-1 rounded-full border border-gray-200 bg-gray-50 px-4 py-2.5 text-sm outline-none transition-colors focus:border-blue-300 focus:bg-white focus:ring-2 focus:ring-blue-100 disabled:opacity-50 disabled:cursor-not-allowed"
                                />
                                <button
                                    type="submit"
                                    disabled={!inputValue.trim() || isSending}
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
