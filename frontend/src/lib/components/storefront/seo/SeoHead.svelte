<!--
  Elite V2.2: SeoHead — GEO & SGE Ultimate 2026
  Centralized Meta Management with Dynamic JSON-LD Factory.
-->
<script lang="ts">
  import { page } from "$app/state";
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
    siteName = "osmo Elite",
    robots = "index, follow, max-image-preview:large",
    articleData = null,
    productData = null,
    categoryData = null,
    breadcrumbItems = [],
    faqs = [],
    jsonLdScripts = [],
  }: SeoHeadProps = $props();

  // Elite V2.2: Safe Fallback Title (Anti-Die)
  const finalTitle = $derived(title || siteName || "osmo Elite Việt Nam");


  // ── Requirement 1: Absolute URL Normalization (GEO 2026: Force Production) ────
  const seoOrigin = "https://osmo.vn";

  const toAbsolute = (url: string | undefined) => {
    if (!url) return "";
    if (url.startsWith("http")) return url;
    const cleanPath = url.startsWith("/") ? url : `/${url}`;
    return `${seoOrigin}${cleanPath}`;
  };

  const absImage = $derived(toAbsolute(image || "/images/default-og.png"));
  const absCanonical = $derived(
    canonical ? toAbsolute(canonical) : `${seoOrigin}${page.url.pathname}`,
  );


  // ── Requirement 2: Dynamic Human-like Description ─────────────────────────
  const finalDescription = $derived.by(() => {
    if (description) return truncateDescription(description);
    return truncateDescription(
      `${finalTitle} - Giải pháp chăm sóc sức khỏe và sắc đẹp chuyên sâu từ osmo Elite Việt Nam.`,
    );
  });


  // ── ELITE V2.2: SEO Factory Integration (SSR Compatible) ───────────────────
  // Note: We update synchronously for SSR support, but use $effect for client-side reactivity
  const syncSeo = () => {
    seoFactory.pageType = pageType;
    seoFactory.breadcrumbItems = breadcrumbItems;
    seoFactory.faqs = faqs;

    if (pageType === "product" && productData) {
      seoFactory.productData = {
        ...productData,
        name: productData.name || title,
        url: absCanonical,
        image: (productData.images || [image]).map((img) => toAbsolute(img)),
      } as ProductLdConfig;
    } else if (pageType === "article" && articleData) {
      seoFactory.articleData = {
        ...articleData,
        headline: articleData.headline || title,
        url: absCanonical,
        image: toAbsolute(articleData.image || image),
      } as ArticleLdConfig;
    } else if (pageType === "category" && categoryData) {
      seoFactory.categoryData = {
        ...categoryData,
        url: absCanonical,
      } as CategoryLdConfig;
    } else if (pageType === "default") {
        // Clear previous data if switching to default
        seoFactory.productData = null;
        seoFactory.articleData = null;
        seoFactory.categoryData = null;
    }
  };

  // Run once sync for SSR
  syncSeo();

  // Run reactive for Client
  $effect(() => {
    syncSeo();
  });

</script>

<svelte:head>
  <title>{finalTitle}</title>

  <!-- ELITE V2.2: Unified @graph JSON-LD (AI Search Optimization) -->
  {#if seoFactory.graphLd}
    {@html `<script type="application/ld+json">${seoFactory.graphLd}<\/script>`}
  {/if}


  <meta name="description" content={finalDescription} />
  <meta name="google" content="notranslate" />
  {#if keywords}
    <meta name="keywords" content={keywords} />
  {/if}
  <meta name="robots" content={robots} />
  <link rel="canonical" href={absCanonical} />

  <!-- Requirement 3: Global Copyright & Author -->
  <meta
    name="copyright"
    content="Bản quyền thuộc về osmo Elite / Miccosmo Việt Nam"
  />
  <meta name="author" content={articleData?.author || "osmo Elite"} />

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
  <meta property="og:site_name" content={siteName} />
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
    <meta property="product:brand" content={productData.brand || "osmo"} />
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
</svelte:head>
