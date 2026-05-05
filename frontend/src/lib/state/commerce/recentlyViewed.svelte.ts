import { browser } from '$app/environment';
import type { Product } from '$lib/types';

class RecentlyViewedStore {
  private key = 'osmo_recently_viewed';
  private maxItems = 12;

  items = $state<string[]>([]);
  products = $state<Product[]>([]);

  constructor() {
    if (browser) {
      const saved = localStorage.getItem(this.key);
      if (saved) {
        try {
          this.items = JSON.parse(saved);
        } catch (e) {
          console.error('Failed to parse recently viewed items', e);
        }
      }
    }
  }

  addProduct(productId: string) {
    if (!productId) return;
    
    // Remove if already exists to move to top
    const filtered = this.items.filter(id => id !== productId);
    this.items = [productId, ...filtered].slice(0, this.maxItems);
    
    if (browser) {
      localStorage.setItem(this.key, JSON.stringify(this.items));
    }
  }

  async fetchProducts() {
    if (this.items.length === 0) {
        this.products = [];
        return;
    }

    try {
      // We might need a bulk fetch API, but for now we fetch them via products API with IDs
      // Or just fetch all active products and filter (if the list is small)
      // Elite V2.2: Fetch using search/ids if backend supports it, else individual fetches (cached)
      const res = await fetch(`/api/v1/client/products?ids=${this.items.join(',')}`);
      if (res.ok) {
        const data = await res.json();
        // Sort according to the order in this.items
        const fetchedProducts = data.data || [];
        this.products = this.items
          .map(id => fetchedProducts.find((p: Product) => p.id === id))
          .filter(Boolean) as Product[];
      }
    } catch (e) {
      console.error('Failed to fetch recently viewed products', e);
    }
  }
}

const RECENTLY_VIEWED_KEY = Symbol('recentlyViewed');

let instance: RecentlyViewedStore;

export function getRecentlyViewedStore() {
  if (!instance) {
    instance = new RecentlyViewedStore();
  }
  return instance;
}
