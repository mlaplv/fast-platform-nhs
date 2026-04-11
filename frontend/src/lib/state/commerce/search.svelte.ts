import { browser } from '$app/environment';

export class SearchState {
  // --- Runes ---
  searchQuery = $state('');
  isSearching = $state(false);
  recentSearches = $state<string[]>([]);
  isOverlayOpen = $state(false); // Mobile primarily

  // Removed Violating Hardcoded Mock Arrays
  featuredProducts = $state<any[]>([]);

  // Real DB Results
  searchResults = $state<any[]>([]);
  private _debounceTimer: ReturnType<typeof setTimeout> | null = null;

  // Elite V2.2: Dynamic Placeholder (Root Fix for hardcoding)
  searchPlaceholder = $derived.by(() => {
    if (this.featuredProducts && this.featuredProducts.length > 0) {
      const p = this.featuredProducts[0];
      return `Tìm "${p.name}"...`;
    }
    return "Tìm kiếm sản phẩm...";
  });

  constructor() {
    console.log("SearchState: Initialized Elite V2.2 Search Engine (DB Linked)");
    this.loadHistory();
    this.loadFeatured();
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
    const history = localStorage.getItem('micsmo_search_history');
    if (history) {
      try {
        this.recentSearches = JSON.parse(history);
      } catch (e) {
        this.recentSearches = [];
      }
    }
  }

  saveHistory() {
    if (!browser) return;
    localStorage.setItem('micsmo_search_history', JSON.stringify(this.recentSearches));
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
      return;
    }

    if (this._debounceTimer) clearTimeout(this._debounceTimer);

    this._debounceTimer = setTimeout(async () => {
      this.isSearching = true;
      try {
        const res = await fetch(`/api/v1/client/products?search=${encodeURIComponent(query)}&limit=5`);
        if (res.ok) {
          const json = await res.json();
          // Assuming ProductListResponse { data: [...], total: ... }
          this.searchResults = json.data || [];
        } else {
          this.searchResults = [];
        }
      } catch (e) {
        console.error("Search API error", e);
        this.searchResults = [];
      } finally {
        this.isSearching = false;
      }
    }, 250); // 250ms ultra-fast debounce for Elite UX
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
