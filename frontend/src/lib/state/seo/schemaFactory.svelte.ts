import { 
    buildProductLd, 
    buildArticleLd, 
    buildCategoryLd, 
    buildBreadcrumbLd, 
    buildFaqLd, 
    buildGraphLd,
    type ProductLdConfig,
    type ArticleLdConfig,
    type CategoryLdConfig,
    type BreadcrumbItem,
    type FaqItem
} from '$lib/utils/seo';

interface KnowledgeGraphEntity {
    name: string;
    description: string;
}

interface KnowledgeGraph {
    knowledge_graph?: {
        entities?: KnowledgeGraphEntity[];
    };
}

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
    productData = $state<Partial<ProductLdConfig> | null>(null);
    articleData = $state<Partial<ArticleLdConfig> | null>(null);
    categoryData = $state<Partial<CategoryLdConfig> | null>(null);
    
    // Derived JSON-LD Strings
    breadcrumbLd = $derived(this.breadcrumbItems.length > 0 ? buildBreadcrumbLd(this.breadcrumbItems) : null);
    faqLd = $derived(this.faqs.length > 0 ? buildFaqLd(this.faqs) : null);
    manualScripts = $state<(string | null | undefined)[]>([]);
    
    productLd = $derived.by(() => {
        if (this.pageType === 'product' && this.productData) {
            const rawLd = buildProductLd(this.productData as ProductLdConfig);
            try {
                const json = JSON.parse(rawLd);
                // Elite V2.2: SGE Knowledge Graph Injection (mentions)
                const kg = (this.productData as Partial<ProductLdConfig> & KnowledgeGraph)?.knowledge_graph;
                if (kg && Array.isArray(kg.entities)) {
                    json.mentions = kg.entities.map((e: KnowledgeGraphEntity) => ({
                        "@type": "Thing",
                        "name": e.name,
                        "description": e.description
                    }));
                }

                return JSON.stringify(json);
            } catch (e) {
                return rawLd;
            }
        }
        return null;
    });

    articleLd = $derived.by(() => {
        if (this.pageType === 'article' && this.articleData) {
            const rawLd = buildArticleLd(this.articleData as ArticleLdConfig);
            try {
                const json = JSON.parse(rawLd);
                // Elite V2.2: SGE Knowledge Graph Injection (mentions)
                const kg = (this.articleData as Partial<ArticleLdConfig> & KnowledgeGraph)?.knowledge_graph;
                if (kg && Array.isArray(kg.entities)) {
                    json.mentions = kg.entities.map((e: KnowledgeGraphEntity) => ({
                        "@type": "Thing",
                        "name": e.name,
                        "description": e.description
                    }));
                }

                return JSON.stringify(json);
            } catch (e) {
                return rawLd;
            }
        }
        return null;
    });

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
    graphLd = $derived.by(() => {
        const scripts = [
            this.productLd,
            this.articleLd,
            this.categoryLd,
            this.breadcrumbLd,
            this.faqLd,           // FAQ luôn cuối → override bất kỳ FAQPage từ manualScripts
            ...this.manualScripts  // chỉ còn schema an toàn (LocalBusiness, WebSite, v.v.)
        ];
        return buildGraphLd(scripts);
    });

    /**
     * Elite V2.5: Output Guard — Lớp kiểm soát đầu ra cuối cùng (PURE COMPUTATION).
     * Không có side effects — log được thực hiện bằng $effect riêng trong SeoHead.
     *
     *   1. Dedup @graph theo normalized @type key (case-insensitive, Array-aware)
     *   2. Lọc entity không hợp lệ (rỗng, thiếu @type)
     *   3. Re-serialize thành chuỗi JSON sạch
     */
    finalLd = $derived.by(() => {
        const raw = this.graphLd;
        if (!raw || raw.length < 10) return '';

        try {
            const parsed = JSON.parse(raw);
            const graph = parsed['@graph'];

            // Not a @graph structure — return as-is (single entity)
            if (!Array.isArray(graph)) return raw;

            // ── Dedup Pass: normalize @type → unique key ──
            const seen = new Map<string, Record<string, unknown>>();
            const noType: Record<string, unknown>[] = [];

            for (const entity of graph) {
                if (!entity || typeof entity !== 'object') continue;
                const rawType = entity['@type'];
                if (!rawType && Object.keys(entity).length === 0) continue;
                if (!rawType) { noType.push(entity); continue; }

                const key = Array.isArray(rawType)
                    ? rawType.map((t: string) => String(t).toLowerCase()).sort().join('+')
                    : String(rawType).toLowerCase();
                seen.set(key, entity); // last wins
            }

            const cleanGraph = [...seen.values(), ...noType];
            if (cleanGraph.length === 0) return '';

            return JSON.stringify({
                '@context': 'https://schema.org',
                '@graph': cleanGraph,
            }).replace(/</g, '\\u003C');

        } catch {
            return raw;
        }
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
        this.productData = null;
        this.articleData = null;
        this.categoryData = null;
        this.manualScripts = [];
    }

    /** @deprecated — use hardReset() */
    reset() { this.hardReset(); }

    /**
     * Contextual update for SGE Entities
     */
    setProduct(data: ProductLdConfig, breadcrumbs: BreadcrumbItem[] = [], faqs: FaqItem[] = []) {
        this.pageType = 'product';
        this.productData = data;
        this.breadcrumbItems = breadcrumbs;
        this.faqs = faqs;
    }

    setArticle(data: ArticleLdConfig, breadcrumbs: BreadcrumbItem[] = [], faqs: FaqItem[] = []) {
        this.pageType = 'article';
        this.articleData = data;
        this.breadcrumbItems = breadcrumbs;
        this.faqs = faqs;
    }

    setCategory(data: CategoryLdConfig, breadcrumbs: BreadcrumbItem[] = []) {
        this.pageType = 'category';
        this.categoryData = data;
        this.breadcrumbItems = breadcrumbs;
    }
}

// Global Singleton for SEO State
export const seoFactory = new SchemaFactory();
