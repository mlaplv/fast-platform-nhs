import { browser } from '$app/environment';
import { authStore } from '../authStore.svelte';

/**
 * Elite V2.2: Wishlist (Favorite) Nanobot Store
 * 
 * Manages product "likes" with high-performance persistence and cross-component sync.
 */
class WishlistStore {
  /** 
   * Reactive map of product ID -> liked status
   * Using Record for O(1) lookup and Svelte 5 reactivity compatibility.
   */
  items = $state<Record<string, boolean>>({});

  get storageKey() {
    const userId = authStore.user?.id;
    return userId ? `osmo:storefront:${userId}:wishlist` : 'osmo:storefront:guest:wishlist';
  }

  constructor() {
    if (browser) {
      $effect.root(() => {
        $effect(() => {
          // Watch authStore.user?.id to reactively reload wishlist on login/logout
          const _ = authStore.user?.id;
          this.loadFromStorage();
        });
      });
    }
  }

  /**
   * Scans namespaced storage or fallback to legacy individual keys to initialize state.
   */
  private loadFromStorage() {
    try {
      const key = this.storageKey;
      const saved = localStorage.getItem(key);
      if (saved) {
        this.items = JSON.parse(saved);
      } else {
        // Fallback / legacy individual keys migration
        const loaded: Record<string, boolean> = {};
        const legacyKeys: string[] = [];
        let migrated = false;
        
        for (let i = 0; i < localStorage.length; i++) {
          const k = localStorage.key(i);
          if (k?.startsWith('vfl_liked_')) {
            const val = localStorage.getItem(k);
            if (val === 'true') {
              const id = k.replace('vfl_liked_', '');
              loaded[id] = true;
              migrated = true;
            }
            legacyKeys.push(k);
          }
        }
        this.items = loaded;
        
        if (migrated) {
          this.save();
          // Cleanup legacy individual keys to avoid polluting
          legacyKeys.forEach(k => localStorage.removeItem(k));
        }
      }
    } catch (e) {
      console.error("[WishlistStore] Failed to load from storage:", e);
    }
  }

  private save() {
    if (!browser) return;
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.items));
    } catch (e) {
      console.warn("[WishlistStore] Storage full or quota exceeded", e);
    }
  }

  /**
   * Check if a product is liked
   */
  isLiked(productId: string): boolean {
    return !!this.items[productId];
  }

  /**
   * Toggle like status for a product
   */
  toggle(productId: string) {
    if (!productId) return;
    
    const currentStatus = !!this.items[productId];
    const newStatus = !currentStatus;
    
    // Update reactive state
    this.items[productId] = newStatus;
    
    // Persist to namespaced storage
    this.save();
  }
}

// Global Singleton for app-wide synchronization
export const wishlistStore = new WishlistStore();
