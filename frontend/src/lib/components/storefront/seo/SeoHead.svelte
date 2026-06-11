<!--
  Elite V2.4: SeoHead — GEO & SGE Ultimate 2026
  Centralized Meta Management with Dynamic JSON-LD Factory.
  Zero-Duplicate Structured Data Architecture. Hard Clear Pattern.
-->
<script lang="ts">
  import { page } from "$app/state";
  import { browser } from "$app/environment";
  import { untrack } from "svelte";
  import { seoFactory } from "$lib/state/seo/schemaFactory.svelte";
  import {
    type ProductLdConfig,
    type ArticleLdConfig,
    type CategoryLdConfig,
    type BreadcrumbItem,
    type FaqItem,
    containsSchemaType,
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

  // ── Resolve Central Shop Settings Dynamically (SSOT & Zero Hardcode) ──
  const resolvedSiteName = $derived.by(() => {
    const dbSiteName = page.data.shopInfo?.basic_info?.site_name;
    if (dbSiteName) return dbSiteName;
    if (siteName && siteName.trim()) return siteName;
    if (page.url.hostname) {
      const name = page.url.hostname.split(".")[0];
      return name.charAt(0).toUpperCase() + name.slice(1);
    }
    return "SmartShop";
  });

  const resolvedSiteTitle = $derived(
    page.data.shopInfo?.basic_info?.site_name
      ? (page.data.shopInfo.basic_info.slogan
          ? `${page.data.shopInfo.basic_info.site_name} | ${page.data.shopInfo.basic_info.slogan}`
          : page.data.shopInfo.basic_info.site_name)
      : resolvedSiteName
  );

  const seoOrigin = $derived.by(() => {
    const dbDomain = page.data.shopInfo?.basic_info?.domain;
    if (dbDomain) {
      return dbDomain.startsWith("http") ? dbDomain : `https://${dbDomain}`;
    }
    return page.url.origin;
  });

  // Self-Healing Dynamic Title (Auto-appends " | Site Name" if not present)
  const finalTitle = $derived.by(() => {
    const isPlaceholder = (val: string) => {
      const v = val.toLowerCase().trim();
      return v === "" || v === "smartshop";
    };

    let baseTitle = title;
    if (!baseTitle || isPlaceholder(baseTitle)) {
      if (pageType === "home" || page.url.pathname === "/") {
        baseTitle = page.data.shopInfo?.seo_analytics?.meta_title || resolvedSiteTitle;
      } else {
        baseTitle = resolvedSiteName;
      }
    }

    // Auto-append dynamic site name to child pages if not present
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

  const absImageType = $derived.by(() => {
    if (!absImage) return "image/jpeg";
    const lower = absImage.toLowerCase();
    if (lower.endsWith(".webp")) return "image/webp";
    if (lower.endsWith(".png")) return "image/png";
    if (lower.endsWith(".gif")) return "image/gif";
    if (lower.endsWith(".svg")) return "image/svg+xml";
    return "image/jpeg";
  });

  const absCanonical = $derived(
    canonical ? toAbsolute(canonical) : `${seoOrigin}${page.url.pathname}`
  );

  // ── Dynamic SGE & SEO Dynamic Description (Zero Hardcode Excerpts) ────
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
      if (b && b !== "smartshop") {
        return productData.brand;
      }
    }
    const fallbackBrand = resolvedSiteName.split(".")[0];
    return fallbackBrand.charAt(0).toUpperCase() + fallbackBrand.slice(1);
  });

  $effect(() => {
    if (shouldRender) {
      const graphLdStr = seoFactory.finalLd;
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
              console.log("%c Unified Graph LD (finalLd): ", "color: #ff79c6; font-weight: bold;", JSON.parse(graphLdStr));
            } catch (e) {
              console.log("%c Unified Graph LD (Raw): ", "color: #ff79c6; font-weight: bold;", graphLdStr);
            }
          }
          console.groupEnd();
        });
      }
  });

  // ── Output Guard Monitor — $effect riêng, KHÔNG untrack ──────────────────
  // $derived KHÔNG được có side effects — log phải đặt ở đây.
  // finalLd là reactive dependency → $effect tự kích hoạt mỗi khi schema thay đổi.
  $effect(() => {
    const finalStr = seoFactory.finalLd; // ← dependency tracking (không untrack)
    if (!finalStr || finalStr.length < 10) return;

    // Parse để đếm và hiển thị entities
    let graph: Record<string, unknown>[] = [];
    let parsedFinal: Record<string, unknown> | null = null;
    try {
      parsedFinal = JSON.parse(finalStr);
      graph = Array.isArray(parsedFinal?.['@graph']) ? (parsedFinal['@graph'] as Record<string, unknown>[]) : [];
    } catch { return; }

    const rawCount  = seoFactory.graphEntityCount;
    const cleanCount = seoFactory.finalEntityCount;
    const removed   = rawCount - cleanCount;

    const hasRemoved = removed > 0;
    const badge = hasRemoved
      ? "background:#4a0000;color:#ff6b6b;font-weight:900;padding:3px 8px;border-radius:4px;border:1px solid #ff6b6b;"
      : "background:#0a2e1a;color:#69db7c;font-weight:900;padding:3px 8px;border-radius:4px;border:1px solid #69db7c;";

    console.group(
      `%c ${hasRemoved ? "⚠️" : "✅"} SEO OUTPUT GUARD — ${cleanCount} entities in @graph `,
      badge
    );

    if (hasRemoved) {
      console.warn(`%c 🗑 Removed ${removed} duplicate(s) from @graph`, "color:#ff6b6b;font-weight:bold;");
    } else {
      console.log("%c ✔ Zero duplicates detected", "color:#69db7c;font-weight:bold;");
    }

    const typesList = graph.map(e =>
      Array.isArray(e["@type"]) ? (e["@type"] as string[]).join("/") : String(e["@type"] ?? "?")
    );
    console.log("%c Types in @graph:", "color:#a9e34b;font-weight:bold;", typesList.join("  •  "));

    graph.forEach((entity, i) => {
      const t = Array.isArray(entity["@type"])
        ? (entity["@type"] as string[]).join("/")
        : String(entity["@type"] ?? "unknown");
      console.log(`%c [${i + 1}] ${t}`, "color:#74c0fc;", entity);
    });

    console.groupEnd();
  });

  // ── V2.4: Schema Types that the frontend ALWAYS rebuilds ──
  // Backend duplicates MUST be stripped unconditionally to prevent Google "Duplicate" errors.
  const FRONTEND_MANAGED_TYPES: string[] = [
    'Product', 'BreadcrumbList', 'FAQPage', 'Article', 'CollectionPage',
    'Organization', 'WebSite'
  ];

  // ── V2.4: SEO Factory Integration (SSR Compatible, Hard Clear) ──────────
  const syncSeo = () => {
    untrack(() => {
      // SGE Protection - Prevent Layout fallback from overwriting Page-level SEO
      if (isFallback && seoFactory.pageType !== "default") {
        return;
      }

      // ── V2.4 HARD CLEAR: Wipe all stale state FIRST ──
      // This is the core fix: prevents FAQ/schema state from previous page
      // bleeding into the current page during client-side navigation.
      seoFactory.hardReset();

      seoFactory.pageType = pageType;
      seoFactory.breadcrumbItems = breadcrumbItems.map(item => ({
        ...item,
        url: toAbsolute(item.url)
      }));
      
      // Filter out empty or invalid FAQ items
      const validFaqs = (faqs || []).filter(f => f && f.question?.trim() && f.answer?.trim());
      seoFactory.faqs = validFaqs;

      // ── CORE FIX V2.4: Deep-scan Backend Deduplication ──
      // containsSchemaType() scans both flat and nested @graph structures.
      // Catches FAQPage even when backend wraps it inside an @graph array.
      seoFactory.manualScripts = (jsonLdScripts || []).filter(s => {
        if (!s) return false;
        for (const type of FRONTEND_MANAGED_TYPES) {
          if (containsSchemaType(s, type)) return false;
        }
        return true;
      });

      // ── Build frontend-side LD based on pageType ──
      if (pageType === "product" && productData) {
        seoFactory.productData = {
          ...productData,
          name: productData.name || title,
          url: absCanonical,
          image: (productData.images || [image]).map((img) => toAbsolute(img)),
          ratingValue: productData.ratingValue || 5.0,
          reviewCount: productData.reviewCount || 1,
          sellerName: resolvedSiteName,
        } as ProductLdConfig;
        // Clear other entity types to prevent cross-contamination
        seoFactory.articleData = null;
        seoFactory.categoryData = null;
      } else if (pageType === "article" && articleData) {
        seoFactory.articleData = {
          ...articleData,
          headline: articleData.headline || title,
          url: absCanonical,
          image: toAbsolute(articleData.image || image),
          description: articleData.description || finalDescription,
          publisherName: articleData.publisherName || resolvedSiteName,
        } as ArticleLdConfig;
        seoFactory.productData = null;
        seoFactory.categoryData = null;
      } else if (pageType === "category" && categoryData) {
        seoFactory.categoryData = {
          ...categoryData,
          url: absCanonical,
        } as CategoryLdConfig;
        seoFactory.productData = null;
        seoFactory.articleData = null;
      } else {
        seoFactory.productData = null;
        seoFactory.articleData = null;
        seoFactory.categoryData = null;
      }
    });
  };

  // Run once sync for SSR
  syncSeo();

  // Run reactive for Client — read all dependencies to trigger on prop changes
  $effect(() => {
    pageType; breadcrumbItems; faqs; jsonLdScripts;
    productData; articleData; categoryData;
    title; absCanonical; image; finalDescription;
    resolvedSiteName; isFallback;

    syncSeo();
  });

  // Prevent Duplicate Headers (Fallback only renders if no page-level SEO is active)
  const shouldRender = $derived(!isFallback || seoFactory.pageType === "default");
</script>

<svelte:head>
  {#if shouldRender}
    <title>{finalTitle}</title>

    <!--
      ==========================================================================
      JSON-LD STRUCTURED DATA — UNIFIED @graph (GEO & SGE 2026)
      ==========================================================================
      All schemas are compiled into a single "@graph" array by SchemaFactory.
      Backend-injected duplicates are stripped unconditionally in syncSeo().
      The @graph output is deduplicated by @type in buildGraphLd().
      ==========================================================================
    -->
    {#if !browser && seoFactory.finalLd}
      {@html `<script type="application/ld+json" id="seo-schema-graph">${seoFactory.finalLd}</script>`}
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

    <!-- Global Copyright & Author -->
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
      <meta property="og:image:type" content={absImageType} />
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
