import apiClient from './axios';

export interface Platform {
    id: string; name: string; url: string; action_url: string; fees: string; ease: string;
    minimum: string; minimum_amount: number; reliability: string; checked_on: string | null; verified: boolean;
}
export interface InvestmentCategory {
    id: string; name: string; explanation: string; risk: string; min_years: number;
    scenario_rate: number; liquidity: string; owned: boolean; reason: string; summary: string;
    options: { id: string; name: string; detail?: string }[]; platforms: Platform[];
    analysis: { status: string; reason: string; mean_pct?: number; volatility_pct?: number;
        weight_pct?: number; observations?: number; proxy?: string; provider?: string; as_of?: string;
        history?: { date: string; index: number }[] };
}
export interface SavedInvestment {
    category_id: string; option_id: string; platform_id: string; years: number; amount: number;
}
export const selectionKey = (item: Pick<SavedInvestment, 'category_id' | 'option_id' | 'platform_id'>) =>
    `${item.category_id}/${item.option_id}/${item.platform_id}`;
export const discoveryApi = {
    get: () => apiClient.get<{ categories: InvestmentCategory[]; risk_profile: string | null }>('/insights/discovery'),
    addPlatform: (category_id: string, name: string) => apiClient.post<{ id: string }>('/insights/platforms', { category_id, name }),
    saved: () => apiClient.get<SavedInvestment[]>('/insights/comparisons'),
    save: (item: SavedInvestment) => apiClient.put<SavedInvestment>('/insights/comparisons', item),
    remove: (item: SavedInvestment) => apiClient.delete(`/insights/comparisons/${selectionKey(item)}`),
};
export function scenarioValue(amount: number, rate: number, years: number) {
    return amount * Math.pow(1 + rate / 100, years);
}
