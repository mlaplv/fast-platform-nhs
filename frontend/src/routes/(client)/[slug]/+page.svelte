<script lang="ts">
  import ProductDetailDesktop from '$lib/components/storefront/product-detail/ProductDetailDesktop.svelte';
  import ProductDetailMobile from '$lib/components/storefront/product-detail/ProductDetailMobile.svelte';
  import ProductListDesktop from '$lib/components/storefront/product/ProductListDesktop.svelte';
  import ProductGrid from '$lib/components/storefront/product/ProductGrid.svelte';
  import ProductListMobile from '$lib/components/storefront/product/ProductListMobile.svelte';
  import NewsListDesktop from '$lib/components/storefront/news/NewsListDesktop.svelte';
  import NewsListMobile from '$lib/components/storefront/news/NewsListMobile.svelte';
  import FunnelPage from '../[slug]-funnel/+page.svelte';
  import { onMount } from 'svelte';

  let { data }: { data: any } = $props();

  let isMobile = $state(false);

  onMount(() => {
    isMobile = window.innerWidth < 768;
    const handleResize = () => {
      isMobile = window.innerWidth < 768;
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  });
</script>

<svelte:head>
  {#if data.type === 'category' || data.type === 'news'}
    <title>{data.categoryName} | Micsmo</title>
  {:else if !(data.product?.metadata?.landing_type && data.product.metadata.landing_type !== 'standard')}
    <title>{data.product?.name} | Micsmo</title>
  {/if}
</svelte:head>

{#if data.type === 'category' || data.type === 'news'}
  {#if data.type === 'news'}
    <div class="news-page-wrapper bg-[#F5F5F7] min-h-screen">
      {#if isMobile}
        <NewsListMobile newsList={data.items} />
      {:else}
        <div class="max-w-7xl mx-auto p-6 md:p-12 pt-8">
            <h1 class="text-5xl font-black text-black tracking-tighter uppercase mb-8">{data.categoryName}</h1>
            <NewsListDesktop newsList={data.items} />
        </div>
      {/if}
    </div>
  {:else}
    <!-- GIAO DIỆN DANH MỤC SẢN PHẨM TRẮNG SẠCH (TMĐT 2026) -->
    {#if isMobile}
      <ProductListMobile products={data.items} />
    {:else}
      <ProductListDesktop products={data.items} categoryName={data.categoryName} />
    {/if}
  {/if}
{:else}
  <!-- KIỂM TRA METADATA: HIỂN THỊ FUNNEL (LANDING PAGE) HOẶC DETAIL PAGE -->
  {#if data.product?.metadata?.landing_type && data.product.metadata.landing_type !== 'standard'}
    <!-- Funnel component already handles its own <svelte:head> -->
    <FunnelPage {data} />
  {:else}
    <!-- GIAO DIỆN CHI TIẾT SẢN PHẨM MẶC ĐỊNH -->
    {#if isMobile}
      <ProductDetailMobile product={data.product} />
    {:else}
      <ProductDetailDesktop product={data.product} />
    {/if}
    
    <!-- DEV DEBUG OVERLAY -->
    {#if import.meta.env.DEV}
      <div class="fixed bottom-0 left-0 bg-black/80 text-green-400 p-2 text-xs z-50">
        [DEBUG] Landing Type: {data.product?.metadata?.landing_type || 'undefined/standard'}
      </div>
    {/if}
  {/if}
{/if}
