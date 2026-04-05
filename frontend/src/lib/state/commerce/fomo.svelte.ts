import { browser } from '$app/environment';

/**
 * ELITE V2.2: FomoStore (Marketing Scarcity Motor)
 * Centralizes deterministic FOMO metrics to ensure parity across components.
 */
export class FomoStore {
    viewers = $state(134);
    stockLeft = $state(7);
    totalSales = $state(12400);
    
    private _slug = '';
    private _viewerInterval: ReturnType<typeof setInterval> | null = null;

    init(slug: string) {
        this._slug = slug;
        this.viewers = this.getSeedValue(134, 256, 1);
        this.stockLeft = this.getSeedValue(2, 7, 2);
        this.totalSales = this.getSeedValue(12000, 17000, 3);
        
        if (browser) {
            this.startViewerPulse();
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
            // Subtle pulse within deterministic range using current time as noise
            this.viewers = this.getSeedValue(134, 256, Math.floor(Date.now() / 10000));
        }, 10000);
    }

    dispose() {
        if (this._viewerInterval) clearInterval(this._viewerInterval);
    }
}

// Singleton for Fomo State (Marketing metrics are usually shared across the session)
export const fomoStore = new FomoStore();
