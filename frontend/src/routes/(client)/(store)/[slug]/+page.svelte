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
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import TikTokShopLoading from '$lib/components/storefront/product/TikTokShopLoading.svelte';
  import { onMount, untrack } from 'svelte';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();
  const ui = getClientUi();

  // Elite V2.2: Dynamic Layout Sync (Viral 2026 Protocol)
  $effect(() => {
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
</script>

<svelte:head>
  {#if data.type === 'category' || data.type === 'news'}
    <title>{data.categoryName} | Micsmo</title>
  {:else if data.type === 'article'}
    <title>{data.article?.title} | Micsmo</title>
    <meta name="description" content={data.article?.excerpt} />
  {:else if !(data.product?.metadata?.landing_type && data.product.metadata.landing_type !== 'standard')}
    <title>{data.product?.name} | Micsmo</title>
  {/if}
</svelte:head>

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
