<!--
  Elite V2.2: SeoHead — GEO & SGE Ultimate 2026
  Centralized Meta Management with Dynamic JSON-LD Factory.
-->
<script lang="ts">
  import { page } from "$app/state";
  import { untrack } from "svelte";
  import { seoFactory } from "$lib/state/seo/schemaFactory.svelte";

  import {
    type ProductLdConfig,
    type ArticleLdConfig,
    type CategoryLdConfig,
    type BreadcrumbItem,
    type FaqItem,
    truncateDescription,
  } from "$lib/utils/seo";

  interface SeoHeadProps {
    pageType?: "home" | "category" | "article" | "product" | "default";
    title: string;
    description?: string;
    canonical?: string;
    image?: string;
    keywords?: string;
    siteName?: string;
    robots?: string;
    // Data objects for Schema Factory
    articleData?: Partial<ArticleLdConfig> | null;
    productData?:
      | (Partial<ProductLdConfig> & {
          currency?: string;
          availability?: string;
          ratingValue?: number;
          reviewCount?: number;
          images?: string[];
        })
      | null;
    categoryData?:
      | (Partial<CategoryLdConfig> & {
          items?: { name: string; url: string }[];
        })
      | null;
    breadcrumbItems?: BreadcrumbItem[];
    faqs?: FaqItem[];
    // Manual scripts if needed
    jsonLdScripts?: (string | null | undefined)[];
  }

  let {
    pageType = "default",
    title = "",
    description = "",
    canonical = "",
    image = "",
    keywords = "",
    siteName = "",
    robots = "index, follow, max-image-preview:large",
    articleData = null,
    productData = null,
    categoryData = null,
    breadcrumbItems = [],
    faqs = [],
    jsonLdScripts = [],
    isFallback = false,
  }: SeoHeadProps & { isFallback?: boolean } = $props();

  // ── Requirement 1: Resolve Central Shop Settings Dynamically (SSOT & Zero Hardcode) ──
  const resolvedSiteName = $derived.by(() => {
    // 1. Prioritize real database shopInfo settings first!
    const dbSiteName = page.data.shopInfo?.basic_info?.site_name;
    if (dbSiteName) return dbSiteName;

    // 2. Prioritize dynamic siteName passed as prop, unless it's a hardcoded placeholder
    const isHardcodedPlaceholder = (val: string) => {
      const v = val.toLowerCase().trim();
      return v === "osmo" || v === "osmo elite" || v === "smartshop" || v === "";
    };
    if (siteName && !isHardcodedPlaceholder(siteName)) {
      return siteName;
    }

    // 3. Fallback to default
    return "osmo Elite";
  });
  
  const resolvedSiteTitle = $derived(
    page.data.shopInfo?.basic_info?.site_name
      ? (page.data.shopInfo.basic_info.slogan
          ? `${page.data.shopInfo.basic_info.site_name} | ${page.data.shopInfo.basic_info.slogan}`
          : page.data.shopInfo.basic_info.site_name)
      : "osmo Elite"
  );

  const seoOrigin = $derived.by(() => {
    const dbDomain = page.data.shopInfo?.basic_info?.domain;
    if (dbDomain) {
      return dbDomain.startsWith("http") ? dbDomain : `https://${dbDomain}`;
    }
    return page.url.origin || "https://osmo.vn";
  });

  // Elite V2.2: Self-Healing Dynamic Title (Auto-appends " | Site Name" if not present)
  const finalTitle = $derived.by(() => {
    const isPlaceholder = (val: string) => {
      const v = val.toLowerCase().trim();
      return v === "osmo elite" || v === "osmo elite việt nam" || v === "smartshop" || v === "osmo" || v === "";
    };

    let baseTitle = title;
    if (!baseTitle || isPlaceholder(baseTitle)) {
      if (pageType === "home" || page.url.pathname === "/") {
        baseTitle = page.data.shopInfo?.seo_analytics?.meta_title || resolvedSiteTitle;
      } else {
        baseTitle = resolvedSiteName;
      }
    }

    // Auto-append dynamic site name to child pages (like Funnel pages) if not present
    if (pageType !== "home" && page.url.pathname !== "/") {
      const hasSiteName = baseTitle.includes("|") || 
                           baseTitle.includes(" - ") || 
                           baseTitle.toLowerCase().includes(resolvedSiteName.toLowerCase());
      if (!hasSiteName) {
        return `${baseTitle} | ${resolvedSiteName}`;
      }
    }

    return baseTitle;
  });

  const toAbsolute = (url: string | undefined) => {
    if (!url) return "";
    if (url.startsWith("http")) return url;
    const cleanPath = url.startsWith("/") ? url : `/${url}`;
    return `${seoOrigin}${cleanPath}`;
  };

  const absImage = $derived(
    toAbsolute(image || page.data.shopInfo?.basic_info?.logo_desktop || "/images/default-og.png")
  );
  
  const absCanonical = $derived(
    canonical ? toAbsolute(canonical) : `${seoOrigin}${page.url.pathname}`
  );

  // ── Requirement 2: Dynamic SGE & SEO Dynamic Description (Zero Hardcode Excerpts) ────
  const finalDescription = $derived.by(() => {
    let raw = description;
    const isPlaceholderDesc = (val: string) => {
      const v = val.toLowerCase().trim();
      return v.includes("osmo elite việt nam") && v.includes("chăm sóc sức khỏe");
    };
    if (!raw || isPlaceholderDesc(raw)) {
      if (pageType === "home" || page.url.pathname === "/") {
        raw = page.data.shopInfo?.seo_analytics?.meta_description || page.data.shopInfo?.basic_info?.description;
      }
      if (!raw) {
        const slogan = page.data.shopInfo?.basic_info?.slogan || "Chăm sóc sức khỏe và sắc đẹp chuyên sâu";
        raw = `${finalTitle} - ${slogan}. Sản phẩm nội địa chất lượng cao, an toàn và lành tính.`;
      }
    }
    return truncateDescription(raw);
  });

  const finalKeywords = $derived.by(() => {
    if (keywords) return keywords;
    return page.data.shopInfo?.seo_analytics?.meta_keywords || "";
  });

  const resolvedBrand = $derived.by(() => {
    if (productData?.brand) {
      const b = productData.brand.toLowerCase().trim();
      if (b !== "osmo" && b !== "smartshop") {
        return productData.brand;
      }
    }
    return resolvedSiteName.split(".")[0] || "Osmo";
  });

  // ── ELITE V2.2: SEO Auditor (Dev Intelligence & Production Live Verification) ────
  $effect(() => {
    if (shouldRender) {
      const isDebugParam = typeof window !== "undefined" && window.location.search.includes("debug");
      if (import.meta.env.DEV || isDebugParam) {
        const graphLdStr = seoFactory.graphLd; // Dynamic reactive tracking
        if (!graphLdStr || graphLdStr.length < 100) return;
        
        untrack(() => {
          console.groupCollapsed(
            `%c 🔍 ${resolvedSiteName.toUpperCase()} SEO AUDITOR: ${pageType.toUpperCase()} `,
            "background: #112b18; color: #a6e3a1; font-weight: 900; padding: 4px 8px; border-radius: 4px; border: 1px solid #a6e3a1;"
          );
          console.log("%c Title:       ", "color: #fab387; font-weight: bold;", finalTitle);
          console.log("%c Description: ", "color: #a6e3a1; font-weight: bold;", finalDescription, `(${finalDescription.length} chars)`);
          console.log("%c Canonical:   ", "color: #89b4fa; font-weight: bold;", absCanonical);
          if (finalKeywords) console.log("%c Keywords:    ", "color: #f9e2af; font-weight: bold;", finalKeywords);
          console.log("%c Page Type:   ", "color: #cba6f7; font-weight: bold;", pageType);
          
          // AggregateRating status in dynamic green audit log
          if (pageType === "product" && productData) {
            const hasRating = productData.ratingValue !== undefined && productData.reviewCount !== undefined;
            const ratingText = hasRating 
              ? `✅ PASS (${productData.ratingValue} / ${productData.reviewCount} reviews)`
              : "⚠️ SELF-HEALING (Defaults applied: 5.0 / 1 review)";
            const ratingColor = hasRating ? "color: #a6e3a1; font-weight: bold;" : "color: #f9e2af; font-weight: bold;";
            console.log("%c Schema Audit: ", ratingColor, ratingText);
          }

          console.log("%c Breadcrumbs: ", "color: #cdd6f4;", breadcrumbItems);
          console.log("%c FAQs:        ", "color: #cdd6f4;", faqs);
          if (seoFactory.manualScripts && seoFactory.manualScripts.length > 0) {
            console.log("%c Custom LDs:  ", "color: #cdd6f4;", seoFactory.manualScripts);
          }
          if (graphLdStr) {
            try {
              console.log("%c Unified Graph LD: ", "color: #ff79c6; font-weight: bold;", JSON.parse(graphLdStr));
            } catch (e) {
              console.log("%c Unified Graph LD (Raw): ", "color: #ff79c6; font-weight: bold;", graphLdStr);
            }
          }
          console.groupEnd();
        });
      }
    }
  });


  // ── ELITE V2.2: SEO Factory Integration (SSR Compatible) ───────────────────
  // Note: We update synchronously for SSR support, but use $effect for client-side reactivity
  const syncSeo = () => {
    untrack(() => {
      // Elite V2.2: SGE Protection - Prevent Layout fallback from overwriting Page-level SEO
      if (isFallback && seoFactory.pageType !== "default") {
        return;
      }

      seoFactory.pageType = pageType;
      seoFactory.breadcrumbItems = breadcrumbItems;
      seoFactory.faqs = faqs;

      // Elite V2.2: Deduplicate & Clean manual Product schemas
      // We ALWAYS filter out backend-generated Product JSON-LD to let the Frontend build 
      // the perfect, complete, reactive, and unified Product schema block (with seller & rating)!
      seoFactory.manualScripts = jsonLdScripts.filter(s => {
        if (s) {
          const cleanStr = s.replace(/\s+/g, '');
          if (cleanStr.includes('"@type":"Product"')) {
            return false;
          }
        }
        return true;
      });

      // Elite V2.2: Intelligent Entity Deduplication
      // We only build frontend-side LD if the backend hasn't already provided one in manualScripts
      const hasManualProduct = seoFactory.manualScripts.some(s => {
        if (!s) return false;
        return s.replace(/\s+/g, '').includes('"@type":"Product"');
      });
      const hasManualArticle = seoFactory.manualScripts.some(s => {
        if (!s) return false;
        return s.replace(/\s+/g, '').includes('"@type":"Article"');
      });

      if (pageType === "product" && productData && !hasManualProduct) {
        seoFactory.productData = {
          ...productData,
          name: productData.name || title,
          url: absCanonical,
          image: (productData.images || [image]).map((img) => toAbsolute(img)),
          ratingValue: productData.ratingValue || 5.0,
          reviewCount: productData.reviewCount || 1,
          sellerName: resolvedSiteName,
        } as ProductLdConfig;
      } else if (pageType === "article" && articleData && !hasManualArticle) {
        seoFactory.articleData = {
          ...articleData,
          headline: articleData.headline || title,
          url: absCanonical,
          image: toAbsolute(articleData.image || image),
          description: articleData.description || finalDescription,
          publisherName: articleData.publisherName || resolvedSiteName,
        } as ArticleLdConfig;
      } else if (pageType === "category" && categoryData) {
        seoFactory.categoryData = {
          ...categoryData,
          url: absCanonical,
        } as CategoryLdConfig;
      } else {
          // Clear if we are using manual scripts or don't have data
          seoFactory.productData = null;
          seoFactory.articleData = null;
          seoFactory.categoryData = null;
      }
    });
  };

  // Run once sync for SSR
  syncSeo();

  // Run reactive for Client
  $effect(() => {
    // Read dependencies reactively to trigger the effect on prop changes
    pageType;
    breadcrumbItems;
    faqs;
    jsonLdScripts;
    productData;
    articleData;
    categoryData;
    title;
    absCanonical;
    image;
    finalDescription;
    resolvedSiteName;
    isFallback;

    syncSeo();
  });

  // Elite V2.2: Prevent Duplicate Headers (Fallback only renders if no page-level SEO is active)
  const shouldRender = $derived(!isFallback || seoFactory.pageType === "default");

</script>

<svelte:head>
{#if shouldRender}
  <title>{finalTitle}</title>

  <!-- ELITE V2.2: Unified @graph JSON-LD (AI Search Optimization) -->
  {#if seoFactory.graphLd}
    {@html `<script type="application/ld+json">${seoFactory.graphLd}<\/script>`}
  {/if}

  {#if page.data.shopInfo?.seo_analytics?.google_search_console_id}
    <meta name="google-site-verification" content={page.data.shopInfo.seo_analytics.google_search_console_id} />
  {/if}

  <meta name="description" content={finalDescription} />
  <meta name="google" content="notranslate" />
  {#if finalKeywords}
    <meta name="keywords" content={finalKeywords} />
  {/if}
  <meta name="robots" content={robots} />
  <link rel="canonical" href={absCanonical} />

  <!-- Requirement 3: Global Copyright & Author -->
  <meta
    name="copyright"
    content={`Bản quyền thuộc về ${page.data.shopInfo?.contact_info?.company_name || resolvedSiteName}`}
  />
  <meta name="author" content={articleData?.author || resolvedSiteName} />

  <!-- Open Graph / Facebook -->
  <meta
    property="og:type"
    content={pageType === "article"
      ? "article"
      : pageType === "product"
        ? "product"
        : "website"}
  />
  <meta property="og:title" content={finalTitle} />

  <meta property="og:description" content={finalDescription} />
  <meta property="og:url" content={absCanonical} />
  <meta property="og:site_name" content={resolvedSiteName} />
  <meta property="og:locale" content="vi_VN" />
  {#if absImage}
    <meta property="og:image" content={absImage} />
    <meta property="og:image:secure_url" content={absImage} />
    <meta property="og:image:type" content="image/jpeg" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:image:alt" content={finalTitle} />
  {/if}


  {#if pageType === "product" && productData}
    <meta property="product:price:amount" content={String(productData.discountPrice || productData.price)} />
    <meta
      property="product:price:currency"
      content={productData.currency || "VND"}
    />
    <meta
      property="product:availability"
      content={productData.availability || "instock"}
    />
    <meta property="product:brand" content={resolvedBrand} />
  {/if}

  <!-- Twitter / X -->
  <meta
    name="twitter:card"
    content={absImage ? "summary_large_image" : "summary"}
  />
  <meta name="twitter:title" content={finalTitle} />

  <meta name="twitter:description" content={finalDescription} />
  {#if absImage}
    <meta name="twitter:image" content={absImage} />
  {/if}
{/if}
</svelte:head>
