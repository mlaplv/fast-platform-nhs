<script lang="ts">
  import type { Product, Category, ReviewStats } from '$lib/types';
  import type { Component } from 'svelte';

  import SeoHead from '$lib/components/storefront/seo/SeoHead.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { onMount, untrack } from 'svelte';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte';
  import { afterNavigate } from '$app/navigation';
  import { page } from '$app/state';
  import type { PageData } from './$types';
  type FunnelPageData = PageData;
  import { resolveOptimizedImageUrl } from '$lib/state/utils';

  import MobileFunnelManager from '$lib/components/storefront/funnel/MobileFunnelManager.svelte';
  import DesktopFunnelManager from '$lib/components/storefront/funnel/DesktopFunnelManager.svelte';
  import ProductDetailMobile from '$lib/components/storefront/product-detail/MainDetail/Mobile.svelte';
  import ProductDetailDesktop from '$lib/components/storefront/product-detail/MainDetail/Desktop.svelte';
  import NewsListMobile from '$lib/components/storefront/news/NewsListMobile.svelte';
  import NewsListDesktop from '$lib/components/storefront/news/NewsListDesktop.svelte';
  import ProductListMobile from '$lib/components/storefront/product/ProductListMobile.svelte';
  import ProductListDesktop from '$lib/components/storefront/product/ProductListDesktop.svelte';



  let { data }: { data: PageData } = $props();
  const ui = getClientUi();
  const siteUrl = $derived(page.url.origin);
  const siteName = $derived(ui.settings?.basic_info?.site_name || ui.settings?.name || 'SmartShop');

  interface NewsItem {
    id: string;
    slug: string;
    title: string;
    excerpt?: string;
    featuredImage: string;
    category?: string;
    createdAt?: string;
  }

  // Route Navigation Scroll Restoration Shield
  afterNavigate(() => {
    if (typeof window !== 'undefined') {
      window.scrollTo({ top: 0, behavior: 'instant' });
      setTimeout(() => {
        window.scrollTo({ top: 0, behavior: 'instant' });
      }, 50);
    }
  });

  // Reactive Funnel Detection
  const landingType = $derived(data.product?.metadata?.landing_type || 'standard');
  const isFunnel = $derived(landingType !== 'standard');

  // Dynamic Layout Sync — pre-paint synchronization
  $effect.pre(() => {
    if (isFunnel || ui.isMobile) {
      ui.isHeaderHidden = true;
      ui.isFooterHidden = true;
    } else {
      ui.isHeaderHidden = false;
      ui.isFooterHidden = false;
    }
    return () => {
      ui.isHeaderHidden = false;
      ui.isFooterHidden = false;
    };
  });

  // Neural Product Sync (Reactive Name Only)
  $effect(() => {
    const pName = data.product?.name || '';
    untrack(() => { supportAgent.currentProductName = pName; });
    return () => { untrack(() => { supportAgent.currentProductName = ''; }); };
  });

  // SEO Derived State
  const productSeoMeta = $derived(data.product?.seoMeta || data.product?.seo_meta || null);
  const categorySeoMeta = $derived(data.category?.seoMeta || data.category?.seo_meta || null);

  // Semantic Breadcrumb Logic
  const breadcrumbItems = $derived.by(() => {
    const items = [{ name: 'Trang chủ', url: '/' }];
    if (data.type === 'category') {
      items.push({ name: data.categoryName, url: `/${data.categorySlug}/` });
    } else if (data.type === 'product' && data.product) {
      if (data.product.category_name && data.product.category_slug) {
        items.push({ name: data.product.category_name, url: `/${data.product.category_slug}/` });
      }
      items.push({ name: data.product.name, url: `/${data.product.slug}` });
    }
    return items;
  });

  const pageFaqs = $derived(data.product?.metadata?.faqs || []);

  interface CategoryPageData {
    type: 'category';
    categoryName: string;
    categorySlug: string;
    category: Category | null;
    serverTotal: number;
    items: Product[];
    facets?: Record<string, unknown> | null;
  }
  interface ProductPageData {
    type: 'product';
    product: Product;
    reviewStats: ReviewStats | null;
    relatedProducts: Product[];
  }
  interface NewsPageData {
    type: 'news';
    categoryName: string;
    items: NewsItem[];
  }

  const categoryData = $derived(data.type === 'category' ? (data as unknown as CategoryPageData) : null);
  const productData = $derived(data.type === 'product' ? (data as unknown as ProductPageData) : null);
  const newsData = $derived(data.type === 'news' ? (data as unknown as NewsPageData) : null);
  const funnelPageData = $derived(isFunnel && productData ? (productData as unknown as FunnelPageData) : null);


</script>
<svelte:head>
  {#if productData?.product}
    {#if data.isMobile}
      {#if data.resolvedMobileLcpUrl}
        {@const isVideo = /\.(mp4|webm|mov|ogg|ogv|avi|mkv)$/.test(data.resolvedMobileLcpUrl.split('?')[0].toLowerCase())}
        {#if !isVideo}
          <link 
            rel="preload" 
            as="image" 
            href={data.resolvedMobileLcpUrl} 
            fetchpriority="high" 
            type="image/webp" 
          />
        {/if}
      {/if}
    {:else}
      {#if data.resolvedDesktopLcpUrl}
        {@const isVideo = /\.(mp4|webm|mov|ogg|ogv|avi|mkv)$/.test(data.resolvedDesktopLcpUrl.split('?')[0].toLowerCase())}
        {#if !isVideo}
          <link 
            rel="preload" 
            as="image" 
            href={data.resolvedDesktopLcpUrl} 
            fetchpriority="high" 
            type="image/webp" 
          />
        {/if}
      {/if}
    {/if}
  {/if}
</svelte:head>


<!-- SEO HEAD (SGE & AI SEARCH COMPLIANT) -->
{#if data.type === 'category' || data.type === 'news'}
  <SeoHead
    pageType="category"
    title={categorySeoMeta?.title || `${data.categoryName} | ${siteName}`}
    description={categorySeoMeta?.description || `${data.categoryName} - Sản phẩm chính hãng.`}
    canonical={categorySeoMeta?.canonical_url || `${siteUrl}/${data.categorySlug}/`}
    keywords={categorySeoMeta?.keywords || ""}
    {breadcrumbItems}
    categoryData={{
      name: data.categoryName,
      items: categoryData?.items?.map((it) => ({ name: it.name, url: `/${it.slug}` }))
    }}
    jsonLdScripts={[categorySeoMeta?.json_ld_string, categorySeoMeta?.breadcrumb_ld_string, categorySeoMeta?.faq_ld_string].filter(Boolean)}
  />

{:else if data.type === 'product' && !isFunnel && productData}
  <SeoHead
    pageType="product"
    title={productSeoMeta?.title || `${productData.product.name} | ${siteName}`}
    description={productSeoMeta?.description || productData.product.short_description || productData.product.shortDescription || productData.product.description || ""}
    canonical={productSeoMeta?.canonical_url || `${siteUrl}/${productData.product.slug}`}
    image={productData.product.images?.[0]}
    {breadcrumbItems}
    faqs={pageFaqs}
    productData={{
      name: productData.product.name,
      images: Array.from(new Set([
        ...(productData.product.images || []),
        ...(productData.product.tierVariations?.[0]?.images || [])
      ])).filter(Boolean),
      description: productSeoMeta?.description || productData.product.short_description || productData.product.shortDescription || "",
      brand: (productData.product.attributes?.brand as string) || (productData.product.attributes?.['Thương hiệu'] as string) || siteName,
      sku: productData.product.sku,
      price: productData.product.price,
      discountPrice: productData.product.discountPrice || productData.product.discount_price,
      variants: productData.product.variants?.map((v: {sku?: string, price: number, discountPrice?: number, discount_price?: number, stock: number}) => ({
          name: v.sku || productData.product.name,
          price: v.price,
          discountPrice: v.discountPrice || v.discount_price,
          sku: v.sku,
          availability: v.stock > 0 ? "InStock" : "OutOfStock"
      })),
      currency: "VND",
      availability: productData.product.stock > 0 ? 'InStock' : 'OutOfStock',
      ratingValue: productData.reviewStats?.average_rating || 5,
      reviewCount: productData.reviewStats?.total_count || 1,
      knowledge_graph: productData.product.metadata?.knowledge_graph
    }}
    jsonLdScripts={[productSeoMeta?.json_ld_string, productSeoMeta?.breadcrumb_ld_string, productSeoMeta?.faq_ld_string].filter(Boolean)}
  />
{/if}

{#snippet Skeleton(type: string)}
  {#if type === 'product'}
    <!-- Luxury Product Details Skeleton -->
    <div class="max-w-7xl mx-auto px-4 py-8 grid grid-cols-1 md:grid-cols-2 gap-12 animate-pulse mt-[5vh]" style="width: 100%;">
      <!-- Left Column: Image Skeleton with Aspect-Ratio matching exactly to avoid CLS -->
      <div class="w-full aspect-square rounded-2xl bg-stone-200 dark:bg-stone-800 flex items-center justify-center">
        <svg class="w-12 h-12 text-stone-300 dark:text-stone-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </div>
      <!-- Right Column: Details Skeleton matching typography layout -->
      <div class="flex flex-col gap-6 py-4">
        <div class="h-4 w-1/4 bg-stone-200 dark:bg-stone-800 rounded-full"></div>
        <div class="h-8 w-3/4 bg-stone-200 dark:bg-stone-800 rounded-lg"></div>
        <div class="h-6 w-1/3 bg-stone-200 dark:bg-stone-800 rounded-full mt-2"></div>
        <div class="h-20 w-full bg-stone-200 dark:bg-stone-800 rounded-xl mt-4"></div>
        <div class="h-12 w-full bg-stone-200 dark:bg-stone-800 rounded-xl mt-8"></div>
      </div>
    </div>
  {:else}
    <!-- Grid/List Page Skeleton with Aspect-Ratio matching exactly to avoid CLS -->
    <div class="max-w-7xl mx-auto px-4 py-8 grid grid-cols-2 md:grid-cols-4 gap-6 animate-pulse mt-[5vh]" style="width: 100%;">
      {#each Array(4) as _}
        <div class="flex flex-col gap-4">
          <div class="w-full aspect-[3/4] rounded-2xl bg-stone-200 dark:bg-stone-800"></div>
          <div class="h-4 w-2/3 bg-stone-200 dark:bg-stone-800 rounded-full"></div>
          <div class="h-4 w-1/3 bg-stone-200 dark:bg-stone-800 rounded-full"></div>
        </div>
      {/each}
    </div>
  {/if}
{/snippet}

{#if data.type === 'product' && isFunnel}
  {#if data.isMobile}
    <MobileFunnelManager data={data} />
  {:else}
    <DesktopFunnelManager data={data} />
  {/if}
{:else if data.type === 'product'}
  {#if data.isMobile}
    <ProductDetailMobile product={data.product} relatedProducts={data.relatedProducts} reviewStats={data.reviewStats} resolvedLcpUrl={data.resolvedMobileLcpUrl} />
  {:else}
    <ProductDetailDesktop product={data.product} relatedProducts={data.relatedProducts} reviewStats={data.reviewStats} resolvedLcpUrl={data.resolvedDesktopLcpUrl} />
  {/if}
{:else if data.type === 'news'}
  {#if data.isMobile}
    <NewsListMobile newsList={data.items} categoryName={data.categoryName} serverTotal={data.serverTotal} />
  {:else}
    <NewsListDesktop newsList={data.items} categoryName={data.categoryName} serverTotal={data.serverTotal} />
  {/if}
{:else if data.type === 'category'}
  {#if data.isMobile}
    <ProductListMobile products={data.items} categoryName={data.categoryName} categorySlug={data.categorySlug} serverTotal={data.serverTotal} facets={data.facets} category={data.category} />
  {:else}
    <ProductListDesktop products={data.items} categoryName={data.categoryName} categorySlug={data.categorySlug} serverTotal={data.serverTotal} facets={data.facets} category={data.category} />
  {/if}
{:else}
  {@render Skeleton(data.type)}
{/if}
