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
        if (!browser) return;
        
        // Elite V2.2: Idempotent initialization - Cleanup existing timers
        this.dispose();
        
        this._slug = slug;
        
        // Viral 2026: Immediate Seed Activities to prevent "cold" storefront
        this.activities = [
            { type: 'ORDER', name: 'Chị Lan', action: 'vừa sở hữu Serum Micsmo', icon: 'ShoppingBag' },
            { type: 'ORDER', name: 'Anh Tuấn', action: 'vừa đặt 02 Tinh chất Phục hồi', icon: 'ShoppingBag' }
        ];
        
        // Initial Seed for metrics (Viral 2026: Hybrid Logic)
        this.viewers = this.getSeedValue(134, 256, 1);
        this.stockLeft = this.getSeedValue(2, 7, 2);
        this.totalSales = this.getSeedValue(12000, 17000, 3);
        
        this.startViewerPulse();
        this.fetchActivities();
        this.startCycle();
        
        // Sync with backend every 2 minutes
        this._fetchInterval = setInterval(() => this.fetchActivities(), 120000);
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
            if (data && data.length > 0) {
                // Elite V2.2: Merge API data with seed, keeping seed as priority for luxury feel
                this.activities = [...this.activities, ...data];
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
        if (this._viewerInterval) clearInterval(this._viewerInterval);
        if (this._fetchInterval) clearInterval(this._fetchInterval);
        if (this._cycleTimeout) clearTimeout(this._cycleTimeout);
    }
}

export const fomoStore = new FomoStore();
