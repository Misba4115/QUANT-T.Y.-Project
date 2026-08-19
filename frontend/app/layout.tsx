import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { UserProvider } from "@/contexts/user-context";
import Chatbot from "@/components/chatbot/chatbot";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "QUANT — Smart Financial Intelligence",
  description:
    "Track your net worth, analyze investments, manage taxes, and get AI-powered financial insights — all in one place.",
  keywords: [
    "finance",
    "investment",
    "portfolio",
    "dashboard",
    "net worth",
    "tax saving",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-scroll-behavior="smooth">
      <body className={`${inter.variable} font-sans antialiased bg-[#F9F9F6]`} suppressHydrationWarning>
        <UserProvider>
          {children}
          <Chatbot />
        </UserProvider>
      </body>
    </html>
  );
}
