import type { DashboardData, InsightsResult } from '@/types';

export const CHAT_VIEW_CONTEXT_EVENT = 'quant-chat-view-context';

export interface ChatViewContext {
    path: '/dashboard' | '/insights';
    hint: string;
}

// A short view hint is sent only with a chat request; raw dashboard/insights data stays local.
export function dashboardChatContext(data: DashboardData, period: string): ChatViewContext {
    const coverage = Math.round(Math.max(0, Math.min(1, data.valuation_coverage)) * 100);
    return {
        path: '/dashboard',
        hint: `Dashboard period=${period}; holdings=${data.top_holdings.length}; asset types=${data.asset_allocation.map(item => item.name).slice(0, 5).join(', ') || 'none recorded'}; price coverage=${coverage}%; risk=${data.risk_level}; history=${data.history_status}.`.slice(0, 210),
    };
}

export function insightsChatContext(data: InsightsResult): ChatViewContext {
    return {
        path: '/insights',
        hint: `Insights as of=${data.generated_at.slice(0, 10)}; held asset types=${data.user_context.asset_classes_held.join(', ') || 'none recorded'}; trading=${data.layer_a.status}; goals=${data.layer_b.status}; goal gaps=${data.layer_b.goal_gaps.length}.`.slice(0, 210),
    };
}

export function publishChatViewContext(context: ChatViewContext): void {
    window.dispatchEvent(new CustomEvent<ChatViewContext>(CHAT_VIEW_CONTEXT_EVENT, { detail: context }));
}
