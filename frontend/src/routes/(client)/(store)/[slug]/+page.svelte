<script lang="ts">
  import ProductDetailDesktop from '$lib/components/storefront/product-detail/ProductDetailDesktop.svelte';
  import ProductDetailMobile from '$lib/components/storefront/product-detail/ProductDetailMobile.svelte';
  import ProductListDesktop from '$lib/components/storefront/product/ProductListDesktop.svelte';
  import ProductGrid from '$lib/components/storefront/product/ProductGrid.svelte';
  import ProductListMobile from '$lib/components/storefront/product/ProductListMobile.svelte';
  import NewsListDesktop from '$lib/components/storefront/news/NewsListDesktop.svelte';
  import NewsListMobile from '$lib/components/storefront/news/NewsListMobile.svelte';
  import NewsDetailDesktop from '$lib/components/storefront/news-detail/NewsDetailDesktop.svelte';
  import NewsDetailMobile from '$lib/components/storefront/news-detail/NewsDetailMobile.svelte';
  import FunnelPage from '../../[slug]-funnel/+page.svelte';
  import SeoHead from '$lib/components/storefront/seo/SeoHead.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import TikTokShopLoading from '$lib/components/storefront/product/TikTokShopLoading.svelte';
  import { onMount, untrack } from 'svelte';
  import {
    buildBreadcrumbLd,
    buildCategoryLd,
    buildArticleLd,
    truncateDescription,
  } from '$lib/utils/seo';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();
  const ui = getClientUi();

  const siteUrl = "https://micsmo.com";

  // Elite V2.2: Dynamic Layout Sync (Viral 2026 Protocol)
  $effect.pre(() => {
    // Luôn ẩn header/footer trên mobile cho trang chi tiết để dùng header/footer riêng (Shopee/TikTok style)
    if (ui.isMobile) {
      ui.isHeaderHidden = true;
      ui.isFooterHidden = true;
    }

    const isFunnel = data.product?.metadata?.landing_type && data.product.metadata.landing_type !== 'standard';

    if (isFunnel) {
      ui.isHeaderHidden = true;
      ui.isFooterHidden = true;
    }

    return () => {
      // Auto-restore on unmount or transition back to standard
      ui.isHeaderHidden = false;
      ui.isFooterHidden = false;
    };
  });

  onMount(() => {
    return ui.initObservers();
  });

  // ═══════════════════════════════════════════════════════════════════════════
  // GEO 2026: SEO Derived State for each page type
  // ═══════════════════════════════════════════════════════════════════════════

  // --- Product Detail (Standard) ---
  const productSeoMeta = $derived(data.product?.seoMeta || data.product?.seo_meta || null);
  const isStandardProduct = $derived(
    data.type === 'product' &&
    !(data.product?.metadata?.landing_type && data.product.metadata.landing_type !== 'standard')
  );

  // --- Category / News List ---
  const categoryCanonical = $derived(`${siteUrl}/${data.categorySlug}/`);
  const categoryDescription = $derived(
    data.type === 'category'
      ? `Khám phá ${data.categoryName} chính hãng tại Micsmo Elite. ${data.serverTotal || data.items?.length || 0} sản phẩm, cam kết chất lượng.`
      : `${data.categoryName} - Hướng dẫn và kiến thức sức khỏe tại Micsmo Elite.`
  );
  const categoryBreadcrumbLd = $derived(
    (data.type === 'category' || data.type === 'news')
      ? buildBreadcrumbLd([
          { name: "Trang chủ", url: siteUrl },
          { name: data.categoryName || "", url: categoryCanonical },
        ])
      : ""
  );
  const categoryLd = $derived(
    data.type === 'category'
      ? buildCategoryLd({
          name: data.categoryName || "",
          url: categoryCanonical,
          description: categoryDescription,
          numberOfItems: data.serverTotal || data.items?.length || 0,
          items: (data.items || []).slice(0, 10).map((p: { name: string; slug: string }) => ({
            name: p.name,
            url: `${siteUrl}/${p.slug}`,
          })),
        })
      : ""
  );

  // --- Article Detail ---
  const articleLd = $derived(
    data.type === 'article' && data.article
      ? buildArticleLd({
          headline: data.article.title,
          description: data.article.excerpt || "",
          url: `${siteUrl}/${data.article.slug}`,
          image: data.article.featured_image || "",
          datePublished: data.article.created_at || new Date().toISOString(),
          author: data.article.author || "Micsmo Elite",
          publisherName: "Micsmo Elite",
        })
      : ""
  );
  const articleBreadcrumbLd = $derived(
    data.type === 'article' && data.article
      ? buildBreadcrumbLd([
          { name: "Trang chủ", url: siteUrl },
          { name: "Bài viết", url: `${siteUrl}/bai-viet` },
          { name: data.article.title, url: `${siteUrl}/${data.article.slug}` },
        ])
      : ""
  );
</script>

<!-- ═══════════════════════════════════════════════════════════════════════════
     GEO 2026: SEO HEAD — Full Meta + OG + JSON-LD per page type
     ═══════════════════════════════════════════════════════════════════════════ -->

{#if data.type === 'category' || data.type === 'news'}
  <SeoHead
    title="{data.categoryName} | Micsmo Elite"
    description={categoryDescription}
    canonical={categoryCanonical}
    siteName="Micsmo Elite"
    jsonLdScripts={[categoryBreadcrumbLd, categoryLd]}
  />

{:else if data.type === 'article' && data.article}
  <SeoHead
    title="{data.article.title} | Micsmo Elite"
    description={truncateDescription(data.article.excerpt || "")}
    canonical="{siteUrl}/{data.article.slug}"
    ogType="article"
    ogImage={data.article.featured_image || ""}
    ogImageAlt={data.article.title}
    siteName="Micsmo Elite"
    jsonLdScripts={[articleLd, articleBreadcrumbLd]}
  />

{:else if isStandardProduct && productSeoMeta}
  <!-- Product Detail (Standard) — Full SEO from backend seoMeta -->
  <SeoHead
    title="{productSeoMeta.title}"
    description={productSeoMeta.description}
    canonical={productSeoMeta.canonical_url}
    ogType="product"
    ogImage={data.product?.images?.[0] || ""}
    ogImageAlt={productSeoMeta.title}
    keywords={productSeoMeta.keywords}
    siteName="Micsmo Elite"
    jsonLdScripts={[
      productSeoMeta.json_ld_string,
      productSeoMeta.breadcrumb_ld_string,
      productSeoMeta.faq_ld_string,
    ]}
  />

{:else if isStandardProduct}
  <!-- Product Detail fallback (no seoMeta from backend) -->
  <SeoHead
    title="{data.product?.name || 'Sản phẩm'} | Micsmo"
    description={data.product?.short_description || data.product?.name || "Sản phẩm chính hãng tại Micsmo Elite."}
    canonical="{siteUrl}/{data.product?.slug || ''}"
    siteName="Micsmo Elite"
  />

{:else if data.type === 'product'}
  <!-- Funnel pages handle their own <svelte:head> -->
{/if}

<!-- ═══════════════════════════════════════════════════════════════════════════
     CONTENT RENDERING
     ═══════════════════════════════════════════════════════════════════════════ -->

{#if !ui.isDetermined}
  <TikTokShopLoading variant={data.type === 'product' ? 'detail' : 'grid'} />
{:else}
  {#if data.type === 'category' || data.type === 'news'}
    {#if data.type === 'news'}
      {#if ui.isMobile}
        <NewsListMobile newsList={data.items} />
      {:else}
        <NewsListDesktop newsList={data.items} categoryName={data.categoryName} />
      {/if}
    {:else}
      <!-- GIAO DIỆN DANH MỤC SẢN PHẨM TRẮNG SẠCH (TMĐT 2026) -->
      {#if ui.isMobile}
        <ProductListMobile
          products={data.items}
          categoryName={data.categoryName}
          facets={data.facets}
        />
      {:else}
        <ProductListDesktop
          products={data.items}
          categoryName={data.categoryName}
          categorySlug={data.categorySlug}
          serverTotal={data.serverTotal}
        />
      {/if}
    {/if}
  {:else if data.type === 'article'}
    <!-- GIAO DIỆN CHI TIẾT BÀI VIẾT (FRIENDLY URL ELITE) -->
    <div class="news-detail-wrapper bg-[#F5F5F5] pb-8">
      {#if ui.isMobile}
        <NewsDetailMobile article={data.article} />
      {:else}
        <NewsDetailDesktop article={data.article} />
      {/if}
    </div>
  {:else}
    <!-- KIỂM TRA METADATA: HIỂN THỊ FUNNEL (LANDING PAGE) HOẶC DETAIL PAGE -->
    {#if data.product?.metadata?.landing_type && data.product.metadata.landing_type !== 'standard'}
      <!-- Funnel component already handles its own <svelte:head> -->
      <FunnelPage {data} />
    {:else}
      <!-- GIAO DIỆN CHI TIẾT SẢN PHẨM MẶC ĐỊNH (Zero-Shift Elite V2.2) -->
      {#if ui.isMobile}
        <ProductDetailMobile product={data.product} relatedProducts={data.relatedProducts} />
      {:else}
        <ProductDetailDesktop product={data.product} relatedProducts={data.relatedProducts} />
      {/if}
    {/if}
  {/if}
{/if}
