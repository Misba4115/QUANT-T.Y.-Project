// ==========================================
// Currency Formatting Utilities
// ==========================================

/**
 * Format a number as Indian Rupee currency
 */
export function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0,
    }).format(amount);
}

/**
 * Format large numbers in lakh/crore notation
 */
export function formatIndianNumber(num: number): string {
    if (num >= 10000000) {
        return `₹${(num / 10000000).toFixed(2)} Cr`;
    }
    if (num >= 100000) {
        return `₹${(num / 100000).toFixed(2)} L`;
    }
    return formatCurrency(num);
}

/**
 * Format Y-axis values for charts
 */
export function formatChartValue(value: number): string {
    if (value >= 100000) {
        return `₹${(value / 100000).toFixed(0)}L`;
    }
    if (value >= 1000) {
        return `₹${(value / 1000).toFixed(0)}K`;
    }
    return `₹${value}`;
}

/**
 * Get user initials from full name
 */
export function getInitials(name: string): string {
    return name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
}
