/**
 * ============================================================
 * QUANT — Dashboard Mock Data
 * ============================================================
 *
 * Temporary mock data for frontend dashboard development.
 *
 * ⚡ TO REMOVE:
 *   1. Delete this file
 *   2. In dashboard/page.tsx, remove the `MOCK_DASHBOARD_DATA` import
 *   3. Uncomment the real `fetchDashboard()` API call in the useEffect
 *   4. The rest of the dashboard code needs ZERO changes
 *
 * All values use Indian Rupees (₹) and realistic Indian-market instruments.
 * ============================================================
 */

import type {
    DashboardData,
    PortfolioDataPoint,
    AssetAllocationItem,
    Holding,
    Alert,
} from '@/types';

// ── Portfolio History (last 12 months) ───────────────────────────────────────
const portfolioHistory: PortfolioDataPoint[] = [
    { month: 'Apr 25', value: 1420000 },
    { month: 'May 25', value: 1475000 },
    { month: 'Jun 25', value: 1510000 },
    { month: 'Jul 25', value: 1485000 },
    { month: 'Aug 25', value: 1560000 },
    { month: 'Sep 25', value: 1620000 },
    { month: 'Oct 25', value: 1595000 },
    { month: 'Nov 25', value: 1680000 },
    { month: 'Dec 25', value: 1725000 },
    { month: 'Jan 26', value: 1780000 },
    { month: 'Feb 26', value: 1850000 },
    { month: 'Mar 26', value: 1925000 },
];

// ── Asset Allocation ─────────────────────────────────────────────────────────
const assetAllocation: AssetAllocationItem[] = [
    { name: 'Equity',        value: 45, color: '#3B82F6' },  // blue
    { name: 'Mutual Funds',  value: 25, color: '#10B981' },  // emerald
    { name: 'Fixed Deposits', value: 15, color: '#F59E0B' }, // amber
    { name: 'Gold / ETF',    value: 10, color: '#EF4444' },  // red
    { name: 'Crypto',        value: 5,  color: '#8B5CF6' },  // violet
];

// ── Top Holdings ─────────────────────────────────────────────────────────────
const topHoldings: Holding[] = [
    {
        instrument: 'Reliance Industries',
        type: 'Equity',
        quantity: 50,
        current_value: 152500,
        profit_loss_percent: 18.4,
    },
    {
        instrument: 'HDFC Bank',
        type: 'Equity',
        quantity: 80,
        current_value: 137600,
        profit_loss_percent: 12.7,
    },
    {
        instrument: 'Nifty 50 Index Fund',
        type: 'Mutual Fund',
        quantity: 450,
        current_value: 225000,
        profit_loss_percent: 22.1,
    },
    {
        instrument: 'SBI Bluechip Fund',
        type: 'Mutual Fund',
        quantity: 320,
        current_value: 168000,
        profit_loss_percent: 9.8,
    },
    {
        instrument: 'Infosys',
        type: 'Equity',
        quantity: 60,
        current_value: 108000,
        profit_loss_percent: -3.2,
    },
    {
        instrument: 'TCS',
        type: 'Equity',
        quantity: 25,
        current_value: 98750,
        profit_loss_percent: 7.5,
    },
    {
        instrument: 'Gold BeES',
        type: 'ETF',
        quantity: 100,
        current_value: 62000,
        profit_loss_percent: 14.3,
    },
];

// ── Alerts & Insights ────────────────────────────────────────────────────────
const alerts: Alert[] = [
    {
        id: 'alert-1',
        type: 'warning',
        message:
            'Your emergency fund covers only 2.1 months of expenses. Consider building it to at least 6 months (₹1,80,000).',
        icon: 'alert-triangle',
    },
    {
        id: 'alert-2',
        type: 'opportunity',
        message:
            'You have ₹62,000 remaining in your 80C limit. Investing in ELSS before March 31 could save up to ₹18,600 in taxes.',
        icon: 'lightbulb',
    },
    {
        id: 'alert-3',
        type: 'info',
        message:
            'Your portfolio has outperformed the Nifty 50 by 4.2% over the last 6 months. Equity allocation is well-balanced.',
        icon: 'bar-chart-3',
    },
];

// ── Complete Dashboard Data  ────────────────────────────────────────────────
/**
 * This is the single export consumed by the dashboard page.
 * Its shape exactly matches `DashboardData` from `@/types`.
 *
 * When the real backend is ready, the dashboard page will fetch
 * this same shape from `dashboardApi.getDashboardResult(runId)`
 * and the UI code stays identical.
 */
export const MOCK_DASHBOARD_DATA: DashboardData = {
    // ── Summary Cards ──────────────────────────────────
    net_worth: 1925000,
    net_worth_growth: 8.6,
    risk_level: 'Medium',

    // ── Cashflow ───────────────────────────────────────
    monthly_income: 85000,
    monthly_expenses: 52000,
    surplus: 33000,

    // ── Tax ────────────────────────────────────────────
    tax_saved: 88000,
    tax_limit: 150000,

    // ── Charts & Tables ────────────────────────────────
    portfolio_history: portfolioHistory,
    asset_allocation: assetAllocation,
    top_holdings: topHoldings,
    alerts,
};
