import { equityApi, mutualFundApi, etfApi } from '@/lib/api';
import type { ClassificationResult } from './csv-classifier';

/**
 * Service to sync classified CSV rows to the backend.
 * Uses the existing single-item POST endpoints but batches concurrent requests
 * to avoid overwhelming the server.
 */
export async function syncHoldingsToBackend(
    data: ClassificationResult,
    onProgress?: (message: string) => void
) {
    let successCount = 0;
    let failCount = 0;

    // Helper to chunk arrays to process in parallel batches of N
    const processInChunks = async <T>(
        items: T[],
        chunkSize: number,
        processor: (item: T) => Promise<void>
    ) => {
        for (let i = 0; i < items.length; i += chunkSize) {
            const chunk = items.slice(i, i + chunkSize);
            const promises = chunk.map((item) =>
                processor(item)
                    .then(() => {
                        successCount++;
                    })
                    .catch((err) => {
                        console.error('Failed to push item to backend:', item, err);
                        failCount++;
                    })
            );
            await Promise.allSettled(promises);
        }
    };

    // 1. Sync Equities
    if (data.equity.length > 0) {
        onProgress?.(`Syncing ${data.equity.length} Equities...`);
        await processInChunks(data.equity, 10, async (row) => {
            if (row.equity) {
                await equityApi.createEquityHolding(row.equity);
            }
        });
    }

    // 2. Sync ETFs
    if (data.etf.length > 0) {
        onProgress?.(`Syncing ${data.etf.length} ETFs...`);
        await processInChunks(data.etf, 10, async (row) => {
            if (row.etf) {
                await etfApi.createETFHolding(row.etf);
            }
        });
    }

    // 3. Sync Mutual Funds
    if (data.mf.length > 0) {
        onProgress?.(`Syncing ${data.mf.length} Mutual Funds...`);
        await processInChunks(data.mf, 10, async (row) => {
            if (row.mf) {
                await mutualFundApi.createMutualFundHolding(row.mf);
            }
        });
    }

    return { successCount, failCount, total: successCount + failCount };
}
