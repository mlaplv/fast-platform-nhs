/**
 * Elite V2.2: SEO Utility Functions — GEO 2026
 *
 * Centralized JSON-LD builders for Schema.org structured data.
 * Used by SeoHead.svelte and page components to generate
 * structured data that AI crawlers (ChatGPT, Gemini, Perplexity, Claude) can cite.
 *
 * Rule: Zero hardcode — all values flow from shopInfo/API config.
 */

// ── Types ─────────────────────────────────────────────────────────────────────

export interface BreadcrumbItem {
    name: string;
    url: string;
}

export interface OrganizationConfig {
    name: string;
    url: string;
    logo?: string;
    description?: string;
    hotline?: string;
    email?: string;
    address?: string;
    socialLinks?: {
        facebook?: string;
        tiktok?: string;
        zalo?: string;
    };
}

export interface ArticleLdConfig {
    headline: string;
    description: string;
    url: string;
    image?: string;
    datePublished: string;
    author: string;
    publisherName: string;
    publisherLogo?: string;
}

export interface CategoryLdConfig {
    name: string;
    url: string;
    description?: string;
    numberOfItems: number;
    items?: { name: string; url: string }[];
}

export interface FaqItem {
    question: string;
    answer: string;
}

// ── Builders ──────────────────────────────────────────────────────────────────

/**
 * BreadcrumbList JSON-LD.
 * AI crawlers use breadcrumbs to understand site hierarchy for citation context.
 */
export function buildBreadcrumbLd(items: BreadcrumbItem[]): string {
    const listItems = items.map((item, index) => ({
        "@type": "ListItem",
        position: index + 1,
        name: item.name,
        item: {
            "@id": item.url
        },
    }));

    return JSON.stringify({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        itemListElement: listItems,
    });
}

/**
 * Organization JSON-LD.
 * Critical for Google Knowledge Panel + AI Search trust signals.
 */
export function buildOrganizationLd(config: OrganizationConfig): string {
    const sameAs: string[] = [];
    if (config.socialLinks?.facebook) sameAs.push(config.socialLinks.facebook);
    if (config.socialLinks?.tiktok) sameAs.push(config.socialLinks.tiktok);
    if (config.socialLinks?.zalo) sameAs.push(config.socialLinks.zalo);

    const org: Record<string, unknown> = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": `${config.url}#organization`,
        name: config.name,
        url: config.url,
    };

    if (config.logo) org.logo = config.logo;
    if (config.description) org.description = config.description;
    if (config.email) org.email = config.email;
    if (config.hotline) {
        org.telephone = config.hotline;
        org.contactPoint = {
            "@type": "ContactPoint",
            telephone: config.hotline,
            contactType: "customer service",
            availableLanguage: "Vietnamese",
        };
    }
    if (config.address) {
        org.address = {
            "@type": "PostalAddress",
            streetAddress: config.address,
            addressCountry: "VN",
        };
    }
    if (sameAs.length > 0) org.sameAs = sameAs;

    return JSON.stringify(org);
}

/**
 * WebSite + SearchAction JSON-LD.
 * Enables Google Sitelinks Search Box + AI Search source recognition.
 */
export function buildWebSiteLd(siteName: string, siteUrl: string): string {
    return JSON.stringify({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "@id": `${siteUrl}#website`,
        name: siteName,
        url: siteUrl,
        potentialAction: {
            "@type": "SearchAction",
            target: {
                "@type": "EntryPoint",
                urlTemplate: `${siteUrl}/products?q={search_term_string}`,
            },
            "query-input": "required name=search_term_string",
        },
    });
}

/**
 * Article JSON-LD (NewsArticle variant).
 * AI crawlers heavily weight structured article data for citation.
 */
export function buildArticleLd(config: ArticleLdConfig): string {
    const article: Record<string, unknown> = {
        "@context": "https://schema.org",
        "@type": "Article",
        "@id": `${config.url}#article`,
        headline: config.headline,
        description: config.description,
        url: config.url,
        datePublished: config.datePublished,
        author: {
            "@type": "Person",
            name: config.author,
        },
        publisher: {
            "@type": "Organization",
            name: config.publisherName,
        },
        inLanguage: "vi",
    };

    if (config.image) article.image = config.image;
    if (config.publisherLogo) {
        (article.publisher as Record<string, unknown>).logo = {
            "@type": "ImageObject",
            url: config.publisherLogo,
        };
    }

    return JSON.stringify(article);
}

/**
 * CollectionPage + ItemList JSON-LD.
 * Used for Category pages to help AI understand product groupings.
 */
export function buildCategoryLd(config: CategoryLdConfig): string {
    const schema: Record<string, unknown> = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "@id": `${config.url}#collection`,
        name: config.name,
        url: config.url,
        numberOfItems: config.numberOfItems,
    };

    if (config.description) schema.description = config.description;

    if (config.items && config.items.length > 0) {
        schema.mainEntity = {
            "@type": "ItemList",
            numberOfItems: config.numberOfItems,
            itemListElement: config.items.slice(0, 10).map((item, i) => ({
                "@type": "ListItem",
                position: i + 1,
                name: item.name,
                url: item.url,
            })),
        };
    }

    return JSON.stringify(schema);
}

/**
 * FAQPage JSON-LD from FAQ items.
 * GEO 2026: AI Search engines strongly prefer FAQ structured data for direct answers.
 */
export function buildFaqLd(faqs: FaqItem[]): string {
    if (!faqs?.length) return "";

    return JSON.stringify({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        mainEntity: faqs
            .filter((f) => f.question && f.answer)
            .map((f) => ({
                "@type": "Question",
                name: f.question,
                acceptedAnswer: {
                    "@type": "Answer",
                    text: f.answer,
                },
            })),
    });
}

/**
 * Truncate text for meta description (150-160 chars).
 * Cuts at word boundary to avoid broken words.
 */
export function truncateDescription(text: string, maxLen: number = 160): string {
    if (!text) return "";
    // Strip HTML
    const clean = text.replace(/<[^>]+>/g, "").trim();
    if (clean.length <= maxLen) return clean;
    const truncated = clean.substring(0, maxLen - 3);
    const lastSpace = truncated.lastIndexOf(" ");
    return (lastSpace > maxLen - 23 ? truncated.substring(0, lastSpace) : truncated) + "…";
}

/**
 * Micsmo Elite V2.2: @graph Builder (AI-First)
 * Hợp nhất nhiều JSON-LD strings thành một siêu cấu trúc @graph duy nhất.
 * Giảm phân mảnh, tăng tốc độ phân tích cho Google AI Review.
 */
export function buildGraphLd(scripts: (string | null | undefined)[]): string {
    const validScripts = scripts.filter(Boolean) as string[];
    if (validScripts.length === 0) return "";
    
    // Nếu chỉ có 1 script, không cần @graph
    if (validScripts.length === 1) return validScripts[0];

    const graphEntities: unknown[] = [];
    
    for (const script of validScripts) {
        try {
            const parsed = JSON.parse(script);
            // Nếu bản thân nó đã là @graph, merge mảng đó vào
            if (parsed["@graph"] && Array.isArray(parsed["@graph"])) {
                graphEntities.push(...parsed["@graph"]);
            } else {
                // Xóa @context cấp độ con (để chuyển lên root)
                delete parsed["@context"];
                graphEntities.push(parsed);
            }
        } catch (e) {
            console.error("Failed to parse JSON-LD script for @graph:", e);
        }
    }

    if (graphEntities.length === 0) return "";

    return JSON.stringify({
        "@context": "https://schema.org",
        "@graph": graphEntities
    }).replace(/</g, '\\u003C');
}
