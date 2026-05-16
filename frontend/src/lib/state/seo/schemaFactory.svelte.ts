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

/**
 * Elite V2.2: SEO Schema Factory (Runes-based)
 * Centralized state management for structured data.
 * Ensures zero-hydration mismatch and SGE compatibility.
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
    
    productLd = $derived.by(() => {
        if (this.pageType === 'product' && this.productData) {
            const rawLd = buildProductLd(this.productData as ProductLdConfig);
            try {
                const json = JSON.parse(rawLd);
                // Elite V2.2: SGE Knowledge Graph Injection (mentions)
                const kg = (this.productData as any)?.knowledge_graph;
                if (kg && Array.isArray(kg.entities)) {
                    json.mentions = kg.entities.map((e: any) => ({
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
                const kg = (this.articleData as any)?.knowledge_graph;
                if (kg && Array.isArray(kg.entities)) {
                    json.mentions = kg.entities.map((e: any) => ({
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
     * Unified @graph generator for AI Search Engines (Perplexity, Gemini, ChatGPT)
     */
    graphLd = $derived.by(() => {
        const scripts = [
            this.breadcrumbLd,
            this.faqLd,
            this.productLd,
            this.articleLd,
            this.categoryLd
        ];
        return buildGraphLd(scripts);
    });

    /**
     * Reset state on navigation
     */
    reset() {
        this.pageType = 'default';
        this.breadcrumbItems = [];
        this.faqs = [];
        this.productData = null;
        this.articleData = null;
        this.categoryData = null;
    }

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
