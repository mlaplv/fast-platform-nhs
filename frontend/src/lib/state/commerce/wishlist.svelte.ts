import { browser } from '$app/environment';

/**
 * Elite V2.2: Wishlist (Favorite) Nanobot Store
 * 
 * Manages product "likes" with high-performance persistence and cross-component sync.
 * Uses individual localStorage keys for compatibility with legacy implementations.
 */
class WishlistStore {
  /** 
   * Reactive map of product ID -> liked status
   * Using Record for O(1) lookup and Svelte 5 reactivity compatibility.
   */
  items = $state<Record<string, boolean>>({});

  constructor() {
    if (browser) {
      this.loadFromStorage();
    }
  }

  /**
   * Scans localStorage for existing likes to initialize state.
   * Handles the 'vfl_liked_{id}' pattern used in Desktop/Funnel versions.
   */
  private loadFromStorage() {
    try {
      const loaded: Record<string, boolean> = {};
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key?.startsWith('vfl_liked_')) {
          const val = localStorage.getItem(key);
          if (val === 'true') {
            const id = key.replace('vfl_liked_', '');
            loaded[id] = true;
          }
        }
      }
      this.items = loaded;
    } catch (e) {
      console.error("[WishlistStore] Failed to load from storage:", e);
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
    
    // Persist to storage
    if (browser) {
      try {
        localStorage.setItem(`vfl_liked_${productId}`, String(newStatus));
      } catch (e) {
        console.warn("[WishlistStore] Storage full or quota exceeded", e);
      }
    }
  }
}

// Global Singleton for app-wide synchronization
export const wishlistStore = new WishlistStore();
