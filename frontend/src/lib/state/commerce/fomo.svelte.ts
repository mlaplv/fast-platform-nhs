import { browser } from '$app/environment';

/**
 * ELITE V2.2: ActivityItem Schema
 */
export interface ActivityItem {
    type: 'ORDER' | 'VISITORS' | 'TRENDING' | 'URGENCY';
    name?: string;
    action?: string;
    msg?: string;
    time?: string;
    icon: string;
}

/**
 * ELITE V2.2: FomoStore (Neural Social Proof & Scarcity Motor)
 * SSOT for both metrics and live activity notifications.
 */
export class FomoStore {
    // ── Metric State (Deterministic/Real-time) ──────────────────────────
    viewers = $state(0);
    stockLeft = $state(0);
    totalSales = $state(0);

    // ── Activity State (Live Feed) ───────────────────────────────────
    activities = $state<ActivityItem[]>([]);
    currentActivity = $state<ActivityItem | null>(null);
    isActivityVisible = $state(false);
    isInitialized = $state(false);

    private currentIndex = 0;
    private _slug = '';
    private _viewerInterval: ReturnType<typeof setInterval> | null = null;
    private _fetchInterval: ReturnType<typeof setInterval> | null = null;
    private _cycleTimeout: ReturnType<typeof setTimeout> | null = null;

    init(slug: string) {
        if (!browser) return;

        // Elite V2.2: Idempotent initialization - Cleanup existing timers
        this.dispose();

        this._slug = slug;
        this.isInitialized = true;

        // Elite V2.2: Authentic initialization - Pull real data immediately
        this.activities = [];

        this.startViewerPulse();
        this.fetchActivities();
        this.fetchMetrics();
        this.startCycle();

        // Sync with backend every 2 minutes
        this._fetchInterval = setInterval(() => {
            this.fetchActivities();
            this.fetchMetrics();
        }, 120000);
    }

    async fetchMetrics() {
        if (!this._slug) return;
        try {
            const { apiClient } = await import('$lib/utils/apiClient');
            const data = await apiClient.get<{viewers: number, stockLeft: number, totalSales: number}>(`/api/v1/client/fomo/metrics/${this._slug}`);
            if (data) {
                this.viewers = data.viewers;
                this.stockLeft = data.stockLeft;
                this.totalSales = data.totalSales;
            }
        } catch (error) {
            console.error('[FomoStore] Metrics sync failed', error);
        }
    }

    private startViewerPulse() {
        if (this._viewerInterval) clearInterval(this._viewerInterval);
        this._viewerInterval = setInterval(() => {
            this.fetchMetrics();
        }, 180000); // Sync viewers/metrics every 3 minutes (180s)
    }

    async fetchActivities() {
        try {
            const { apiClient } = await import('$lib/utils/apiClient');
            const data = await apiClient.get<ActivityItem[]>('/api/v1/client/fomo/activity');
            if (data && data.length > 0) {
                // Elite V2.2: Pure Authentic Feed (No merging with fake seeds)
                this.activities = data;
            }
        } catch (error) {
            console.error('[FomoStore] Fetch failed', error);
        }
    }

    private startCycle() {
        const run = () => {
            if (this.activities.length === 0) {
                this._cycleTimeout = setTimeout(run, 5000);
                return;
            }

            this.currentActivity = this.activities[this.currentIndex];
            this.isActivityVisible = true;

            this._cycleTimeout = setTimeout(() => {
                this.isActivityVisible = false;
                this.currentIndex = (this.currentIndex + 1) % this.activities.length;

                // Randomized gap (10s - 20s) - Tightened for better viral effect
                const gap = 10000 + Math.random() * 10000;
                this._cycleTimeout = setTimeout(run, gap);
            }, 6000);
        };

        // Elite V2.2: First run starts after 2 seconds to allow layout to settle
        this._cycleTimeout = setTimeout(run, 2000);
    }

    dispose() {
        this.isInitialized = false;
        if (this._viewerInterval) clearInterval(this._viewerInterval);
        if (this._fetchInterval) clearInterval(this._fetchInterval);
        if (this._cycleTimeout) clearTimeout(this._cycleTimeout);
    }
}

export const fomoStore = new FomoStore();
