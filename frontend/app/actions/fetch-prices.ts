'use server';

import yahooFinance from 'yahoo-finance2';

// Notices are not suppressed to avoid TS errors in this version

export async function fetchLivePrices(holdings: { type: string; symbol: string; scheme_code?: string }[]) {
    const prices: Record<string, number> = {};
    const promises: Promise<void>[] = [];

    for (const h of holdings) {
        if (h.type === 'Equity' || h.type === 'ETF') {
            const querySymbol = `${h.symbol}.NS`;
            promises.push(
                (yahooFinance as any).quote(querySymbol).then((res: any) => {
                    if (res && res.regularMarketPrice) {
                        prices[`${h.type}-${h.symbol}`] = res.regularMarketPrice;
                    }
                }).catch((err: any) => {
                    console.warn(`Failed to fetch price for ${querySymbol}:`, err.message);
                })
            );
        } else if (h.type === 'Crypto') {
            // e.g. BTC -> BTC-INR
            const querySymbol = `${h.symbol}-INR`;
            promises.push(
                (yahooFinance as any).quote(querySymbol).then((res: any) => {
                    if (res && res.regularMarketPrice) {
                        prices[`${h.type}-${h.symbol}`] = res.regularMarketPrice;
                    }
                }).catch((err: any) => {
                    console.warn(`Failed to fetch price for ${querySymbol}:`, err.message);
                })
            );
        } else if (h.type === 'Mutual Fund' && h.scheme_code) {
            // Fetch from AMFI
            promises.push(
                fetch(`https://api.mfapi.in/mf/${h.scheme_code}`)
                    .then(res => res.json())
                    .then(data => {
                        if (data && data.data && data.data.length > 0) {
                            const nav = parseFloat(data.data[0].nav);
                            prices[`${h.type}-${h.symbol}`] = nav;
                        }
                    })
                    .catch(err => {
                        console.warn(`Failed to fetch NAV for ${h.scheme_code}:`, err.message);
                    })
            );
        }
    }

    await Promise.allSettled(promises);
    return prices;
}
