<!--
  Elite V2.2: SeoHead — GEO & SGE Ultimate 2026
  Centralized Meta Management with Dynamic JSON-LD Factory.
-->
<script lang="ts">
  import { page } from '$app/stores';
  import { 
    buildGraphLd, 
    buildWebSiteLd, 
    buildOrganizationLd, 
    buildCategoryLd, 
    buildArticleLd, 
    buildProductLd,
    truncateDescription 
  } from '$lib/utils/seo';

  interface SeoHeadProps {
    pageType?: 'home' | 'category' | 'article' | 'product' | 'default';
    title: string;
    description?: string;
    canonical?: string;
    image?: string;
    keywords?: string;
    siteName?: string;
    robots?: string;
    // Data objects for Schema Factory
    articleData?: any;
    productData?: any;
    categoryData?: any;
    // Manual scripts if needed
    jsonLdScripts?: (string | null | undefined)[];
  }

  let {
    pageType = 'default',
    title,
    description = "",
    canonical = "",
    image = "",
    keywords = "",
    siteName = "osmo Elite",
    robots = "index, follow, max-image-preview:large",
    articleData = null,
    productData = null,
    categoryData = null,
    jsonLdScripts = []
  }: SeoHeadProps = $props();

  // ── Requirement 1: Absolute URL Normalization ────────────────────────────────
  const origin = $derived($page.url.origin || 'https://osmo.vn');
  
  const toAbsolute = (url: string | undefined) => {
    if (!url) return '';
    if (url.startsWith('http')) return url;
    const cleanPath = url.startsWith('/') ? url : `/${url}`;
    return `${origin}${cleanPath}`;
  };

  const absImage = $derived(toAbsolute(image));
  const absCanonical = $derived(canonical ? toAbsolute(canonical) : $page.url.href);

  // ── Requirement 2: Dynamic Human-like Description ─────────────────────────
  const finalDescription = $derived.by(() => {
    if (description) return truncateDescription(description);
    // Elite V2.2: Context-aware fallback to avoid "AI Footprints"
    return truncateDescription(`${title} - Giải pháp chăm sóc sức khỏe và sắc đẹp chuyên sâu từ osmo Elite Việt Nam.`);
  });

  // ── Requirement 4: Dynamic Schema JSON-LD Factory ──────────────────────────
  const generatedScripts = $derived.by(() => {
    // GEO 2026: Force production origin for all SEO metadata to prevent hydration mismatch
    const seoOrigin = 'https://osmo.vn';

    const toAbsSeo = (url: string | undefined) => {
      if (!url) return '';
      if (url.startsWith('http')) return url;
      const cleanPath = url.startsWith('/') ? url : `/${url}`;
      return `${seoOrigin}${cleanPath}`;
    };

    // Helper to extract JSON and normalize relative URLs inside it
    const processLd = (str: string | null | undefined): string | null => {
      if (!str) return null;
      let jsonStr = str;
      const match = str.match(/<script[^>]*>([\s\S]*?)<\/script>/i);
      if (match) jsonStr = match[1].trim();

      // GEO 2026: Deep Absolute URL Replacement inside JSON
      jsonStr = jsonStr.replace(/("(url|image|logo|contentUrl)":\s*")(\/[^"]+)/g, `$1${seoOrigin}$3`);
      
      // Elite V2.2: Global Text Normalization for Audit (40gr -> 40g)
      jsonStr = jsonStr.replace(/40gr/g, '40g');

      return jsonStr;
    };

    let rawScripts: (string | null | undefined)[] = jsonLdScripts.map(processLd);
    let productScript: string | null = null;
    
    // Elite V2.2: Intelligent Deep Filtering
    const scripts = rawScripts.filter(s => {
      if (!s) return false;
      try {
        const parsed = JSON.parse(s);
        if (parsed["@type"] === 'Product') return false;
        if (parsed["@graph"]) {
          parsed["@graph"] = parsed["@graph"].filter((e: any) => e["@type"] !== 'Product');
          return parsed["@graph"].length > 0;
        }
        return true;
      } catch (e) { return true; }
    });

    // Build specialized Product Schema
    if (pageType === 'product' && productData) {
      // Clean up 40gr -> 40g for SEO consistency
      const cleanName = (productData.name || title).replace(/40gr/g, '40g');
      
      productScript = buildProductLd({
        name: cleanName,
        image: (productData.images || [image]).map((img: string) => toAbsSeo(img)),
        description: productData.description || finalDescription,
        brand: productData.brand || "osmo",
        sku: productData.sku || "",
        url: canonical ? toAbsSeo(canonical) : absCanonical,
        price: productData.price || 0,
        priceCurrency: productData.currency || "VND",
        availability: productData.availability || "InStock",
        ratingValue: productData.ratingValue || 5.0,
        reviewCount: productData.reviewCount || 1
      });
    }

    switch (pageType) {
      case 'home':
        scripts.push(buildWebSiteLd(siteName, seoOrigin));
        scripts.push(buildOrganizationLd({
          name: siteName,
          url: seoOrigin,
          logo: toAbsSeo('/favicon.svg'),
          description: finalDescription
        }));
        break;
        
      case 'category':
        if (categoryData) {
          scripts.push(buildCategoryLd({
            name: (categoryData.name || title).replace(/40gr/g, '40g'),
            url: canonical ? toAbsSeo(canonical) : absCanonical,
            description: finalDescription,
            numberOfItems: categoryData.items?.length || 0,
            items: categoryData.items?.map((it: any) => ({
              name: it.name.replace(/40gr/g, '40g'),
              url: toAbsSeo(it.url)
            }))
          }));
        }
        break;
        
      case 'article':
        if (articleData) {
          scripts.push(buildArticleLd({
            headline: (articleData.headline || title).replace(/40gr/g, '40g'),
            description: finalDescription,
            url: canonical ? toAbsSeo(canonical) : absCanonical,
            image: toAbsSeo(articleData.image || image),
            datePublished: articleData.datePublished || new Date().toISOString(),
            author: articleData.author || "osmo Elite",
            publisherName: "osmo Elite",
            publisherLogo: toAbsSeo('/favicon.svg')
          }));
        }
        break;
    }
    
    return { graph: buildGraphLd(scripts), product: productScript };
  });

  const seoData = $derived(generatedScripts);

  // ── SEO DEBUG HUB (Elite V2.2) ─────────────────────────────────────────────
  import { browser } from '$app/environment';
  $effect(() => {
    if (browser && pageType === 'product') {
      console.group('🚀 [GEO/SGE DEBUG] - PRODUCT SCHEMA');
      console.log('• Page Type:', pageType);
      console.log('• Product Data:', productData);
      console.log('• Rating/Review:', {
        rating: productData?.ratingValue,
        count: productData?.reviewCount
      });
      console.log('• Final JSON-LD String (Product):');
      console.log(seoData.product);
      console.log('• Final JSON-LD String (Graph):');
      console.log(seoData.graph);
      console.groupEnd();
    }
  });
</script>

<svelte:head>
  <title>{title}</title>

  <!-- JSON-LD Structured Data (GEO 2026: Split Injection) -->
  {#if seoData.graph}
    {@html `<script type="application/ld+json">${seoData.graph}</script>`}
  {/if}

  {#if seoData.product}
    {@html `<script type="application/ld+json">${seoData.product}</script>`}
  {/if}

  <meta name="description" content={finalDescription} />
  {#if keywords}
    <meta name="keywords" content={keywords} />
  {/if}
  <meta name="robots" content={robots} />
  <link rel="canonical" href={absCanonical} />
  
  <!-- Requirement 3: Global Copyright & Author -->
  <meta name="copyright" content="Bản quyền thuộc về osmo Elite / Miccosmo Việt Nam" />
  <meta name="author" content="osmo Elite" />

  <!-- Open Graph / Facebook -->
  <meta property="og:type" content={pageType === 'article' ? 'article' : (pageType === 'product' ? 'product' : 'website')} />
  <meta property="og:title" content={title} />
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
    <meta property="og:image:alt" content={title} />
  {/if}

  {#if pageType === 'product' && productData}
    <meta property="product:price:amount" content={String(productData.price)} />
    <meta property="product:price:currency" content={productData.currency || "VND"} />
    <meta property="product:availability" content={productData.availability || "instock"} />
    <meta property="product:brand" content={productData.brand || "osmo"} />
  {/if}

  <!-- Twitter / X -->
  <meta name="twitter:card" content={absImage ? "summary_large_image" : "summary"} />
  <meta name="twitter:title" content={title} />
  <meta name="twitter:description" content={finalDescription} />
  {#if absImage}
    <meta name="twitter:image" content={absImage} />
  {/if}
</svelte:head>
