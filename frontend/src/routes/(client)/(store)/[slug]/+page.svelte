<script lang="ts">
  import ProductDetailDesktop from '$lib/components/storefront/product-detail/ProductDetailDesktop.svelte';
  import ProductDetailMobile from '$lib/components/storefront/product-detail/ProductDetailMobile.svelte';
  import ProductListDesktop from '$lib/components/storefront/product/ProductListDesktop.svelte';
  import ProductGrid from '$lib/components/storefront/product/ProductGrid.svelte';
  import ProductListMobile from '$lib/components/storefront/product/ProductListMobile.svelte';
  import NewsListDesktop from '$lib/components/storefront/news/NewsListDesktop.svelte';
  import NewsListMobile from '$lib/components/storefront/news/NewsListMobile.svelte';
  import FunnelPage from '../../[slug]-funnel/+page.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { onMount, untrack } from 'svelte';

  let { data }: { data: any } = $props();
  const ui = getClientUi();

  // Elite V2.2: Dynamic Layout Sync (Viral 2026 Protocol)
  $effect(() => {
    // Luôn ẩn header/footer trên mobile cho trang chi tiết để dùng header/footer riêng (Shopee/TikTok style)
    if (isMobile) {
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
    {#if isMobile}
      <NewsListMobile newsList={data.items} />
    {:else}
      <NewsListDesktop newsList={data.items} categoryName={data.categoryName} />
    {/if}
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
    <!-- GIAO DIỆN CHI TIẾT SẢN PHẨM MẶC ĐỊNH (Zero-Shift Elite V2.2) -->
    <div class:is-mobile-detail={true}>
      <!-- Cấp độ Trình duyệt: Ẩn/Hiện tức thì bằng CSS trước khi JS kịp chạy -->
      <div class="hidden-desktop">
        <ProductDetailMobile product={data.product} />
      </div>
      
      <div class="hidden-mobile">
        <ProductDetailDesktop product={data.product} />
      </div>
    </div>
  {/if}
{/if}
