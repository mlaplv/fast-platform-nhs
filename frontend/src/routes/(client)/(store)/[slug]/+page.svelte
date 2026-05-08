<script lang="ts">
  import ProductDetailDesktop from '$lib/components/storefront/product-detail/MainDetail/Desktop.svelte';
  import ProductDetailMobile from '$lib/components/storefront/product-detail/MainDetail/Mobile.svelte';
  import ProductListDesktop from '$lib/components/storefront/product/ProductListDesktop.svelte';
  import ProductListMobile from '$lib/components/storefront/product/ProductListMobile.svelte';
  import NewsListDesktop from '$lib/components/storefront/news/NewsListDesktop.svelte';
  import NewsListMobile from '$lib/components/storefront/news/NewsListMobile.svelte';
  import NewsDetailDesktop from '$lib/components/storefront/news-detail/NewsDetailDesktop.svelte';
  import NewsDetailMobile from '$lib/components/storefront/news-detail/NewsDetailMobile.svelte';
  import FunnelPage from '../../[slug]-funnel/+page.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { onMount, untrack } from 'svelte';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();
  const ui = getClientUi();
  const siteUrl = "https://osmo.vn";

  // Elite V2.2: Reactive Funnel Detection (Zero-Latency Sync)
  const landingType = $derived(data.product?.metadata?.landing_type || data.product?.metadata?.landingType || 'standard');
  const isFunnel = $derived(landingType !== 'standard');

  // Elite V2.2: Dynamic Layout Sync (Viral 2026 Protocol)
  $effect(() => {
    if (isFunnel || ui.isMobile) {
      ui.isHeaderHidden = true;
      ui.isFooterHidden = true;
    } else {
      ui.isHeaderHidden = false;
      ui.isFooterHidden = false;
    }

    return () => {
      // Auto-restore on unmount
      ui.isHeaderHidden = false;
      ui.isFooterHidden = false;
    };
  });

  onMount(() => {
    return ui.initObservers();
  });

  // Elite V6.3: Neural Product Sync
  $effect(() => {
    if (data.product?.name) {
      data.product.name = data.product.name.replace(/40gr/g, '40g');
    }
    const pName = data.product?.name || "";
    untrack(() => {
        supportAgent.currentProductName = pName;
    });
    return () => {
        untrack(() => {
            supportAgent.currentProductName = "";
        });
    };
  });
</script>

{#if data.type === 'category' || data.type === 'news'}
  <!-- CATEGORY/NEWS VIEW -->
  {#if data.type === 'news'}
    {#if ui.isMobile}
      <NewsListMobile newsList={data.items} />
    {:else}
      <NewsListDesktop newsList={data.items} categoryName={data.categoryName} />
    {/if}
  {:else}
    {#if ui.isMobile}
      <ProductListMobile products={data.items} categoryName={data.categoryName} facets={data.facets} category={data.category} />
    {:else}
      <ProductListDesktop products={data.items} categoryName={data.categoryName} categorySlug={data.categorySlug} serverTotal={data.serverTotal} facets={data.facets} category={data.category} />
    {/if}
  {/if}
{:else if data.type === 'article'}
  <!-- ARTICLE VIEW -->
  <div class="news-detail-wrapper bg-[#F5F5F5] pb-8">
    {#if ui.isMobile}
      <NewsDetailMobile article={data.article} />
    {:else}
      <NewsDetailDesktop article={data.article} />
    {/if}
  </div>
{:else}
  <!-- PRODUCT DETAIL / FUNNEL VIEW -->
  {#if isFunnel}
    <FunnelPage {data} />
  {:else}
    {#if ui.isMobile}
      <ProductDetailMobile product={data.product} relatedProducts={data.relatedProducts} />
    {:else}
      <ProductDetailDesktop product={data.product} relatedProducts={data.relatedProducts} />
    {/if}
    
    {#if import.meta.env.DEV}
      <div class="fixed bottom-0 left-0 bg-black/80 text-green-400 p-2 text-xs z-50">
        [DEBUG] Landing Type: {landingType}
      </div>
    {/if}
  {/if}
{/if}
