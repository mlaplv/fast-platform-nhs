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
    stockLeft = $state(7);
    totalSales = $state(12400);

    // ── Activity State (Live Feed) ───────────────────────────────────
    activities = $state<ActivityItem[]>([]);
    currentActivity = $state<ActivityItem | null>(null);
    isActivityVisible = $state(false);
    
    private currentIndex = 0;
    private _slug = '';
    private _viewerInterval: ReturnType<typeof setInterval> | null = null;
    private _fetchInterval: ReturnType<typeof setInterval> | null = null;
    private _cycleTimeout: ReturnType<typeof setTimeout> | null = null;

    init(slug: string) {
        this._slug = slug;
        
        // Initial Seed for metrics (Viral 2026: Hybrid Logic)
        this.viewers = this.getSeedValue(134, 256, 1);
        this.stockLeft = this.getSeedValue(2, 7, 2);
        this.totalSales = this.getSeedValue(12000, 17000, 3);
        
        if (browser) {
            this.startViewerPulse();
            this.fetchActivities();
            this.startCycle();
            
            // Sync with backend every 2 minutes
            this._fetchInterval = setInterval(() => this.fetchActivities(), 120000);
        }
    }

    private getSeedValue(min: number, max: number, offset = 0) {
        const seed = this._slug || 'default';
        let hash = offset;
        for (let i = 0; i < seed.length; i++) {
            hash = seed.charCodeAt(i) + ((hash << 5) - hash);
        }
        return min + (Math.abs(hash) % (max - min + 1));
    }

    private startViewerPulse() {
        if (this._viewerInterval) clearInterval(this._viewerInterval);
        this._viewerInterval = setInterval(() => {
            this.viewers = this.getSeedValue(134, 256, Math.floor(Date.now() / 10000));
        }, 10000);
    }

    async fetchActivities() {
        try {
            const { apiClient } = await import('$lib/utils/apiClient');
            const data = await apiClient.get<ActivityItem[]>('https://api.micsmo.com/api/v1/client/fomo/activity');
            if (data) {
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
                
                // Randomized gap (15s - 30s)
                const gap = 15000 + Math.random() * 15000;
                this._cycleTimeout = setTimeout(run, gap);
            }, 8000);
        };

        run();
    }

    dispose() {
        if (this._viewerInterval) clearInterval(this._viewerInterval);
        if (this._fetchInterval) clearInterval(this._fetchInterval);
        if (this._cycleTimeout) clearTimeout(this._cycleTimeout);
    }
}

export const fomoStore = new FomoStore();
