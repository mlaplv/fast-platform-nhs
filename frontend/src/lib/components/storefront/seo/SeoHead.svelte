<!--
  Elite V2.2: SeoHead — Reusable SEO Head Component
  GEO 2026: Centralized meta tags, OG, Twitter Cards, JSON-LD injection.
  
  Usage:
    <SeoHead
      title="Product Name | Brand"
      description="..."
      canonical="https://micsmo.com/slug"
      ogType="product"
      ogImage="https://..."
      jsonLdScripts={[productLd, breadcrumbLd]}
    />
-->
<script lang="ts">
  interface SeoHeadProps {
    title: string;
    description: string;
    canonical: string;
    ogType?: string;
    ogImage?: string;
    ogImageAlt?: string;
    siteName?: string;
    keywords?: string;
    robots?: string;
    jsonLdScripts?: string[];
  }

  let {
    title,
    description,
    canonical,
    ogType = "website",
    ogImage = "",
    ogImageAlt = "",
    siteName = "Micsmo Elite",
    keywords = "",
    robots = "index, follow, max-image-preview:large",
    jsonLdScripts = [],
  }: SeoHeadProps = $props();
</script>

<svelte:head>
  <title>{title}</title>
  <meta name="description" content={description} />
  {#if keywords}
    <meta name="keywords" content={keywords} />
  {/if}
  <meta name="robots" content={robots} />
  <link rel="canonical" href={canonical} />

  <!-- Open Graph (Facebook, Zalo, Threads) -->
  <meta property="og:type" content={ogType} />
  <meta property="og:title" content={title} />
  <meta property="og:description" content={description} />
  <meta property="og:url" content={canonical} />
  <meta property="og:site_name" content={siteName} />
  <meta property="og:locale" content="vi_VN" />
  {#if ogImage}
    <meta property="og:image" content={ogImage} />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    {#if ogImageAlt}
      <meta property="og:image:alt" content={ogImageAlt} />
    {/if}
  {/if}

  <!-- Twitter / X Card -->
  <meta name="twitter:card" content={ogImage ? "summary_large_image" : "summary"} />
  <meta name="twitter:title" content={title} />
  <meta name="twitter:description" content={description} />
  {#if ogImage}
    <meta name="twitter:image" content={ogImage} />
  {/if}

  <!-- JSON-LD Structured Data (GEO 2026) -->
  {#each jsonLdScripts as ldScript}
    {#if ldScript}
      <!-- eslint-disable-next-line svelte/no-at-html-tags -->
      {@html `<script type="application/ld+json">${ldScript}</script>`}
    {/if}
  {/each}
</svelte:head>
