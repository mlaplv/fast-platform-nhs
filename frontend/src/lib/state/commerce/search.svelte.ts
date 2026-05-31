import { browser } from '$app/environment';
import type { Product, Article } from '$lib/types';
import { authStore } from '../authStore.svelte';

export class SearchState {
  // --- Runes ---
  searchQuery = $state('');
  isSearching = $state(false);
  recentSearches = $state<string[]>([]);
  isOverlayOpen = $state(false); // Mobile primarily

  // Removed Violating Hardcoded Mock Arrays
  featuredProducts = $state<Product[]>([]);

  // Real DB Results
  searchResults = $state<Product[]>([]);
  searchArticleResults = $state<Article[]>([]);

  // Elite V2.2: Dynamic Placeholder (Root Fix for hardcoding & derived_inert warning)
  get searchPlaceholder() {
    if (this.featuredProducts && this.featuredProducts.length > 0) {
      const p = this.featuredProducts[0];
      return `Tìm "${p.name}"...`;
    }
    return "Tìm kiếm sản phẩm...";
  }

  get storageKey() {
    const userId = authStore.user?.id;
    return userId ? `osmo:storefront:${userId}:search_history` : 'osmo:storefront:guest:search_history';
  }

  constructor() {
    if (browser) {
      $effect.root(() => {
        $effect(() => {
          // Watch authStore.user?.id to reactively reload search history on login/logout
          const _ = authStore.user?.id;
          this.loadHistory();
        });
      });
    }
  }

  async ensureFeaturedLoaded() {
    if (this.featuredProducts.length === 0) {
      await this.loadFeatured();
    }
  }

  // --- Logic ---
  async loadFeatured() {
    if (!browser) return;
    try {
      // Pull actual DB data for trending/featured UI regions
      const res = await fetch('/api/v1/client/products?featured_only=true&limit=6');
      if (res.ok) {
        const json = await res.json();
        this.featuredProducts = json.data || [];
      }
    } catch (e) {
      console.error("Failed to load featured products", e);
    }
  }
  loadHistory() {
    if (!browser) return;
    const key = this.storageKey;
    const history = localStorage.getItem(key);
    if (history) {
      try {
        this.recentSearches = JSON.parse(history);
      } catch (e) {
        this.recentSearches = [];
      }
    } else {
      // Fallback/migration from legacy key
      const legacyKey = 'osmo_search_history';
      const legacyHistory = localStorage.getItem(legacyKey);
      if (legacyHistory) {
        try {
          this.recentSearches = JSON.parse(legacyHistory);
          this.saveHistory();
          localStorage.removeItem(legacyKey);
        } catch (e) {
          this.recentSearches = [];
        }
      } else {
        this.recentSearches = [];
      }
    }
  }

  saveHistory() {
    if (!browser) return;
    localStorage.setItem(this.storageKey, JSON.stringify(this.recentSearches));
  }

  addSearch(term: string) {
    if (!term.trim()) return;
    const filtered = this.recentSearches.filter(s => s !== term);
    this.recentSearches = [term, ...filtered].slice(0, 10);
    this.saveHistory();
  }

  async triggerSearch(query: string) {
    this.searchQuery = query;
    if (!query.trim()) {
      this.searchResults = [];
      this.isSearching = false;
      return;
    }

    // Elite V2.2: Direct fetch — debounce is handled by SmartSearch.$effect (300ms)
    // No double debounce to ensure <300ms perceived latency
    this.isSearching = true;

    try {
      // Neural Sync Search: Execute Products & News search in parallel
      const [prodRes, newsRes] = await Promise.all([
        fetch(`/api/v1/client/products?search=${encodeURIComponent(query)}&limit=5`),
        fetch(`/api/v1/client/news/search?q=${encodeURIComponent(query)}&limit=5`)
      ]);

      if (prodRes.ok) {
        const prodJson = await prodRes.json();
        this.searchResults = prodJson.data || [];
      } else {
        this.searchResults = [];
      }

      if (newsRes.ok) {
        this.searchArticleResults = await newsRes.json();
      } else {
        this.searchArticleResults = [];
      }
    } catch (e) {
      console.error("Neural Search API error", e);
      this.searchResults = [];
      this.searchArticleResults = [];
    } finally {
      this.isSearching = false;
    }
  }

  removeSearch(term: string) {
    this.recentSearches = this.recentSearches.filter(s => s !== term);
    this.saveHistory();
  }

  clearHistory() {
    this.recentSearches = [];
    this.saveHistory();
  }
}

// Global Singleton (Standard for Elite V2.2)
let searchInstance: SearchState;

export function getSearchStore() {
  if (!searchInstance) {
    searchInstance = new SearchState();
  }
  return searchInstance;
}
