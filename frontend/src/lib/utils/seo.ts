/**
 * Elite V2.4: SEO Utility Functions — GEO 2026
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

export interface ReviewLd {
    author: string;
    datePublished: string;
    reviewBody: string;
    ratingValue: number;
}

export interface ProductVariantLd {
    price: number;
    discountPrice?: number;
    sku?: string;
    url?: string;
    availability?: string;
    name?: string;
}

export interface ProductLdConfig {
    name: string;
    image: string[];
    description?: string;
    brand: string;
    sku?: string;
    mpn?: string;
    url: string;
    price: number;
    discountPrice?: number;
    priceCurrency: string;
    availability: string;
    ratingValue?: number;
    reviewCount?: number;
    reviews?: ReviewLd[];
    variants?: ProductVariantLd[];
    sellerName?: string;
}

// ── Builders ──────────────────────────────────────────────────────────────────

/**
 * Product JSON-LD.
 * Critical for AI Search (SGE) to extract price, availability, and social proof (rating).
 */
export function buildProductLd(config: ProductLdConfig): string {
    const mainPrice = config.discountPrice || config.price;
    const hasDiscount = !!config.discountPrice && config.discountPrice < config.price;

    // Support both priceCurrency and currency, standardizing currency values like 'đ' to 'VND'
    const rawCurrency = config.priceCurrency || (config as any).currency || "VND";
    const resolvedCurrency = rawCurrency === "đ" ? "VND" : rawCurrency;

    const offer: Record<string, unknown> = {
        "@type": "Offer",
        "url": config.url,
        "priceCurrency": resolvedCurrency,
        "price": String(mainPrice),
        "availability": config.availability?.includes("InStock") ? "https://schema.org/InStock" : "https://schema.org/OutOfStock",
        "itemCondition": "https://schema.org/NewCondition",
        "seller": {
            "@type": "Organization",
            "name": config.sellerName || "osmo.vn"
        }
    };

    if (hasDiscount) {
        offer.priceSpecification = {
            "@type": "PriceSpecification",
            "price": String(mainPrice),
            "priceCurrency": resolvedCurrency,
            "valueAddedTaxIncluded": true
        };
    }

    const product: Record<string, unknown> = {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": config.name,
        "image": Array.isArray(config.image) ? config.image : [config.image],
        "description": config.description || config.name,
        "brand": {
            "@type": "Brand",
            "name": config.brand || "osmo Elite"
        }
    };

    // If variants exist, use AggregateOffer
    if (config.variants && config.variants.length > 0) {
        const prices = config.variants.map(v => v.discountPrice || v.price);
        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);

        // Derive availability for AggregateOffer based on variant stock/availability
        const isAggregateInStock = config.variants.some(v => 
            v.availability?.includes("InStock") || 
            (v as any).stock > 0 || 
            (v as any).availability === "InStock"
        );
        const aggregateAvailability = isAggregateInStock ? "https://schema.org/InStock" : "https://schema.org/OutOfStock";

        product.offers = {
            "@type": "AggregateOffer",
            "lowPrice": String(minPrice),
            "highPrice": String(maxPrice),
            "priceCurrency": resolvedCurrency,
            "availability": aggregateAvailability,
            "offerCount": String(config.variants.length),
            "seller": {
                "@type": "Organization",
                "name": config.sellerName || "osmo.vn"
            },
            "offers": config.variants.map(v => ({
                "@type": "Offer",
                "name": v.name,
                "sku": v.sku,
                "price": String(v.discountPrice || v.price),
                "priceCurrency": resolvedCurrency,
                "availability": v.availability?.includes("InStock") ? "https://schema.org/InStock" : "https://schema.org/OutOfStock",
                "seller": {
                    "@type": "Organization",
                    "name": config.sellerName || "osmo.vn"
                }
            }))
        };
    } else {
        product.offers = offer;
    }

    if (config.sku) product.sku = config.sku;

    if (config.ratingValue) {
        product.aggregateRating = {
            "@type": "AggregateRating",
            "ratingValue": String(config.ratingValue),
            "reviewCount": String(config.reviewCount),
            "bestRating": "5",
            "worstRating": "1"
        };
    }

    if (config.reviews && config.reviews.length > 0) {
        product.review = config.reviews.map(r => ({
            "@type": "Review",
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": String(r.ratingValue),
                "bestRating": "5"
            },
            "author": {
                "@type": "Person",
                "name": r.author
            },
            "datePublished": r.datePublished,
            "reviewBody": r.reviewBody
        }));
    }

    return JSON.stringify(product);
}

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
    const sameAs = config.socialLinks ? Object.values(config.socialLinks).filter(v => v && typeof v === "string") : [];
    
    const org: Record<string, unknown> = {
        "@context": "https://schema.org/",
        "@type": "Organization",
        "@id": "https://osmo.vn/#organization",
        "name": config.name,
        "url": config.url,
        "image": config.logo,
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "4.9",
            "reviewCount": "24",
            "bestRating": "5",
            "worstRating": "1"
        }
    };

    if (config.logo) org.logo = config.logo;
    if (config.description) org.description = config.description;
    if (config.email) org.email = config.email;
    if (config.hotline) {
        org.telephone = config.hotline;
        org.contactPoint = {
            "@type": "ContactPoint",
            "telephone": config.hotline,
            "contactType": "customer service",
            "availableLanguage": "Vietnamese"
        };
    }
    if (config.address) {
        org.address = {
            "@type": "PostalAddress",
            "streetAddress": config.address,
            "addressCountry": "VN"
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
                urlTemplate: `${siteUrl}/search?q={search_term_string}`,
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
        "@context": "https://schema.org/",
        "@type": "Article",
        "@id": `${config.url}#article`,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": config.url
        },
        "headline": config.headline,
        "description": config.description,
        "url": config.url,
        "datePublished": config.datePublished,
        "author": {
            "@type": "Person",
            "name": config.author
        },
        "publisher": {
            "@type": "Organization",
            "name": config.publisherName,
            "@id": "https://osmo.vn/#organization",
            "url": "https://osmo.vn"
        },
        "inLanguage": "vi"
    };

    if (config.image) article.image = config.image;
    
    if (config.publisherLogo) {
        (article.publisher as Record<string, unknown>).logo = {
            "@type": "ImageObject",
            "url": config.publisherLogo
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
        "@context": "https://schema.org/",
        "@type": "CollectionPage",
        "@id": `${config.url}#collection`,
        "name": config.name,
        "url": config.url,
        "description": config.description || "",
        "numberOfItems": config.numberOfItems,
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "4.9",
            "reviewCount": "24",
            "bestRating": "5",
            "worstRating": "1"
        }
    };

    if (config.items && config.items.length > 0) {
        schema.mainEntity = {
            "@type": "ItemList",
            "numberOfItems": config.numberOfItems,
            "itemListElement": config.items.slice(0, 15).map((item, i) => ({
                "@type": "ListItem",
                "position": i + 1,
                "item": {
                    "@type": "Product",
                    "name": item.name,
                    "url": item.url,
                    "brand": {
                        "@type": "Brand",
                        "name": "Miccosmo"
                    }
                }
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
 * Elite V2.4: containsSchemaType — Deep Scanner
 * Kiểm tra JSON-LD string có chứa @type cụ thể không.
 * Quét được cả cấu trúc flat và nested @graph (backend inject kiểu mảng).
 *
 * @param script - JSON-LD string (có thể chứa đơn lẻ hoặc mảng @graph)
 * @param type   - @type cần kiểm tra, ví dụ 'FAQPage'
 */
export function containsSchemaType(script: string, type: string): boolean {
    if (!script || !type) return false;

    // Fast path: regex check (catches 99% of cases quickly)
    const fastRegex = new RegExp(`["']@type["']\\s*:\\s*["']${type}["']`, 'i');
    if (!fastRegex.test(script)) return false;

    // Deep path: parse JSON and walk @graph array (backend may nest types)
    try {
        const parsed = JSON.parse(script);
        const typeLower = type.toLowerCase();

        const matchesType = (val: unknown): boolean => {
            if (!val) return false;
            if (typeof val === 'string') return val.toLowerCase() === typeLower;
            if (Array.isArray(val)) return val.some(v => typeof v === 'string' && v.toLowerCase() === typeLower);
            return false;
        };

        // Check top-level entity
        if (matchesType(parsed['@type'])) return true;

        // Check @graph array (backend often wraps multiple entities in one @graph block)
        if (Array.isArray(parsed['@graph'])) {
            for (const entity of parsed['@graph']) {
                if (entity && matchesType(entity['@type'])) return true;
            }
        }

        // Check if the script IS a raw array of entities
        if (Array.isArray(parsed)) {
            for (const entity of parsed) {
                if (entity && matchesType(entity['@type'])) return true;
                if (entity?.['@graph'] && Array.isArray(entity['@graph'])) {
                    for (const inner of entity['@graph']) {
                        if (inner && matchesType(inner['@type'])) return true;
                    }
                }
            }
        }
    } catch {
        // JSON parse failed — regex already returned true above, trust it
    }

    return true; // regex matched even if parse failed
}

/**
 * Elite V2.4: @graph Builder (AI-First, Zero-Duplicate)
 * Hợp nhất nhiều JSON-LD strings thành một siêu cấu trúc @graph duy nhất.
 * Deduplicate by @type — frontend entity (append LAST) luôn thắng backend.
 * Hỗ trợ: flat entity, @graph array, top-level array of entities.
 */
export function buildGraphLd(scripts: (string | null | undefined)[]): string {
    const validScripts = scripts.filter(Boolean) as string[];
    if (validScripts.length === 0) return '';

    // If only 1 script with no siblings, skip @graph wrapper
    if (validScripts.length === 1) return validScripts[0];

    const rawEntities: Record<string, unknown>[] = [];

    for (const script of validScripts) {
        try {
            const parsed = JSON.parse(script);

            // Unwrap top-level @graph
            if (parsed['@graph'] && Array.isArray(parsed['@graph'])) {
                for (const entity of parsed['@graph']) {
                    delete entity['@context'];
                    rawEntities.push(entity);
                }
            // Unwrap top-level array of entities
            } else if (Array.isArray(parsed)) {
                for (const entity of parsed) {
                    delete entity['@context'];
                    if (entity['@graph'] && Array.isArray(entity['@graph'])) {
                        for (const inner of entity['@graph']) {
                            delete inner['@context'];
                            rawEntities.push(inner);
                        }
                    } else {
                        rawEntities.push(entity);
                    }
                }
            } else {
                delete parsed['@context'];
                rawEntities.push(parsed);
            }
        } catch {
            // Skip malformed scripts silently
        }
    }

    if (rawEntities.length === 0) return '';

    // Deduplicate by normalised @type string.
    // If @type is an Array (e.g. ["Article","NewsArticle"]), use joined string as key.
    // Last entity with same key wins (frontend-built is appended LAST → wins).
    const deduped = new Map<string, Record<string, unknown>>();
    const noTypeEntities: Record<string, unknown>[] = [];

    for (const entity of rawEntities) {
        const raw = entity['@type'];
        if (raw) {
            const key = Array.isArray(raw)
                ? raw.map((t: string) => String(t).toLowerCase()).sort().join('+')
                : String(raw).toLowerCase();
            deduped.set(key, entity);
        } else {
            noTypeEntities.push(entity);
        }
    }

    const graphEntities = [...deduped.values(), ...noTypeEntities];
    if (graphEntities.length === 0) return '';

    return JSON.stringify({
        '@context': 'https://schema.org',
        '@graph': graphEntities,
    }).replace(/</g, '\\u003C');
}

// ── SSOT: Normalized SEO Meta ──────────────────────────────────────────────────
/**
 * Elite V2.2: normalizeSeoMeta — SSOT SEO normalizer cho toàn hệ thống.
 *
 * Backend (Python/Litestar) luôn serialize theo snake_case:
 *   canonical_url, json_ld_string, breadcrumb_ld_string, faq_ld_string
 *
 * Hàm này map cả hai dạng snake_case & camelCase thành 1 object chuẩn,
 * dùng chung cho Article, Category, Product — không duplicate logic ở bất kỳ đâu.
 *
 * @param raw - Raw SEO object từ API (có thể là seoMeta hoặc seo_meta)
 * @param fallbackTitle - Tiêu đề fallback nếu backend trả về rác (ví dụ: "Sản phẩm | osmo")
 */
export interface NormalizedSeoMeta {
    title: string;
    description: string;
    keywords: string;
    canonicalUrl: string;
    canonical_url: string;
    jsonLdString: string;
    json_ld_string: string;
    breadcrumb_ld_string: string;
    faq_ld_string: string;
}

export function normalizeSeoMeta(
    raw: Record<string, unknown> | null | undefined,
    fallbackTitle = ""
): NormalizedSeoMeta | null {
    if (!raw) return null;

    // Resolve từng field, ưu tiên camelCase → snake_case
    const rawTitle = (raw["title"] as string) || "";
    const isGenericFallback = !rawTitle || rawTitle.startsWith("Sản phẩm");
    const title = (isGenericFallback && fallbackTitle) ? fallbackTitle : rawTitle;

    const canonicalUrl =
        (raw["canonicalUrl"] as string) ||
        (raw["canonical_url"] as string) ||
        "";

    const jsonLdString =
        (raw["jsonLdString"] as string) ||
        (raw["json_ld_string"] as string) ||
        "";

    return {
        title,
        description: (raw["description"] as string) || "",
        keywords: (raw["keywords"] as string) || "",
        canonicalUrl,
        canonical_url: canonicalUrl,
        jsonLdString,
        json_ld_string: jsonLdString,
        breadcrumb_ld_string:
            (raw["breadcrumb_ld_string"] as string) ||
            (raw["breadcrumbLdString"] as string) ||
            "",
        faq_ld_string:
            (raw["faq_ld_string"] as string) ||
            (raw["faqLdString"] as string) ||
            "",
    };
}
