import { 
    buildCategoryLd, 
    buildBreadcrumbLd, 
    buildFaqLd, 
    buildGraphLd,
    type CategoryLdConfig,
    type BreadcrumbItem,
    type FaqItem
} from '$lib/utils/seo';



/**
 * Elite V2.5: SEO Schema Factory (Runes-based)
 * Centralized state management for structured data.
 * Ensures zero-hydration mismatch and SGE compatibility.
 * Architecture:
 *   Layer 1 — Input guard  : SeoHead strips FRONTEND_MANAGED_TYPES from jsonLdScripts (containsSchemaType)
 *   Layer 2 — Build        : buildGraphLd() merges all sources, dedup by @type
 *   Layer 3 — Output guard : finalLd parses the rendered JSON and dedup one last time before <head>
 */
class SchemaFactory {
    // Current Page State
    pageType = $state<'home' | 'category' | 'article' | 'product' | 'default'>('default');
    
    // Data Stores
    breadcrumbItems = $state<BreadcrumbItem[]>([]);
    faqs = $state<FaqItem[]>([]);

    categoryData = $state<Partial<CategoryLdConfig> | null>(null);
    
    // Derived JSON-LD Strings
    breadcrumbLd = $derived(this.breadcrumbItems.length > 0 ? buildBreadcrumbLd(this.breadcrumbItems) : null);
    faqLd = $derived(this.faqs.length > 0 ? buildFaqLd(this.faqs) : null);
    manualScripts = $state<(string | null | undefined)[]>([]);
    


    categoryLd = $derived.by(() => {
        if (this.pageType === 'category' && this.categoryData) {
            return buildCategoryLd(this.categoryData as CategoryLdConfig);
        }
        return null;
    });

    /**
     * Elite V2.4: Unified @graph generator for AI Search Engines
     * manualScripts đã được lọc sạch FRONTEND_MANAGED_TYPES ở SeoHead trước khi gán.
     * buildGraphLd() sẽ dedup thêm 1 lần cuối theo @type.
     */
    /**
     * V3.0: Backend Is King — Backend schemas pass through via manualScripts.
     * Frontend only overrides BreadcrumbList (routing-aware) and FAQPage (lazy-loaded).
     * Order matters: last @type wins in buildGraphLd dedup.
     */
    graphLd = $derived.by(() => {
        const scripts = [
            this.categoryLd,
            ...this.manualScripts,  // Backend schemas (Product, Article, Organization, etc.)
            this.breadcrumbLd,      // Frontend breadcrumb overrides backend (routing-aware)
            this.faqLd,             // Frontend FAQ overrides backend (lazy-loaded data)
        ];
        return buildGraphLd(scripts);
    });

    /**
     * V4.0: Pass-through with XSS protection only.
     * Deduplication is handled by buildGraphLd() — no redundant re-parse (KISS).
     */
    finalLd = $derived.by(() => {
        const raw = this.graphLd;
        if (!raw || raw.length < 10) return '';
        return raw.replace(/</g, '\\u003C');
    });

    /**
     * Metadata dùng cho Output Guard monitor ($effect bên ngoài).
     * Expose số lượng entity trong raw graphLd và finalLd để so sánh duplicate.
     */
    get graphEntityCount(): number {
        try {
            if (!this.graphLd) return 0;
            const p = JSON.parse(this.graphLd);
            return Array.isArray(p['@graph']) ? p['@graph'].length : 1;
        } catch { return 0; }
    }

    get finalEntityCount(): number {
        try {
            if (!this.finalLd) return 0;
            const p = JSON.parse(this.finalLd);
            return Array.isArray(p['@graph']) ? p['@graph'].length : 1;
        } catch { return 0; }
    }

    /**
     * Elite V2.4: Hard Clear — wipe ALL state synchronously.
     * Must be called at the TOP of syncSeo() before setting any new props.
     * Prevents stale state accumulation across client-side navigations.
     */
    hardReset() {
        this.pageType = 'default';
        this.breadcrumbItems = [];
        this.faqs = [];
        this.categoryData = null;
        this.manualScripts = [];
    }

    /** @deprecated — use hardReset() */
    reset() { this.hardReset(); }



    setCategory(data: CategoryLdConfig, breadcrumbs: BreadcrumbItem[] = []) {
        this.pageType = 'category';
        this.categoryData = data;
        this.breadcrumbItems = breadcrumbs;
    }
}

// Global Singleton for SEO State
export const seoFactory = new SchemaFactory();
