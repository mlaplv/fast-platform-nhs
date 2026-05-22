<script lang="ts">
  import ProductListDesktop from '$lib/components/storefront/product/ProductListDesktop.svelte';
  import MobileSearchResultList from '$lib/components/storefront/product/MobileSearchResultList.svelte';
  import TikTokShopLoading from '$lib/components/storefront/product/TikTokShopLoading.svelte';
  import SeoHead from '$lib/components/storefront/seo/SeoHead.svelte';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { onMount } from 'svelte';
  import { page } from '$app/stores';

  import type { Product, ProductFacets } from '$lib/types';

  interface PageData {
    products: Product[];
    total: number;
    searchQuery: string;
    brand: string;
    origin: string;
    facets: ProductFacets | null;
  }

  let { data }: { data: PageData } = $props();
  const ui = getClientUi();
  const searchStore = getSearchStore();

  // Elite V2.2: Sync global search store with current page data (URL query)
  $effect.pre(() => {
    if (data.searchQuery !== undefined && searchStore.searchQuery !== data.searchQuery) {
       searchStore.searchQuery = data.searchQuery;
    }
  });



  // Elite V2.2: Search context - build proper props for category-oriented components
  const searchLabel = $derived(
    data.searchQuery
      ? `Kết quả tìm kiếm: "${data.searchQuery}"`
      : data.brand
        ? `Thương hiệu: ${data.brand}`
        : data.origin
          ? `Xuất xứ: ${data.origin}`
          : 'Tất cả sản phẩm'
  );

  // GEO 2026: SEO Meta
  const siteName = $derived(ui.settings?.basic_info?.site_name || ui.settings?.site_name || "SmartShop");
  const seoTitle = $derived(
    data.searchQuery
      ? `Tìm kiếm "${data.searchQuery}" | ${siteName}`
      : data.brand
        ? `Thương hiệu ${data.brand} chính hãng | ${siteName}`
        : data.origin
          ? `Xuất xứ ${data.origin} | ${siteName}`
          : `Tất cả sản phẩm | ${siteName}`
  );
  const seoDescription = $derived(
    data.searchQuery
      ? `Kết quả tìm kiếm "${data.searchQuery}" - ${data.total} sản phẩm chính hãng tại ${siteName}.`
      : data.brand
        ? `Danh sách sản phẩm thương hiệu ${data.brand} chính hãng nhập khẩu tại ${siteName}. Cam kết chất lượng.`
        : data.origin
          ? `Danh sách sản phẩm xuất xứ từ ${data.origin} chính hãng tại ${siteName}.`
          : `Khám phá toàn bộ sản phẩm chăm sóc sức khỏe chính hãng tại ${siteName}. Cam kết chất lượng, hỗ trợ 24/7.`
  );
  const seoRobots = "noindex, nofollow";

</script>

<SeoHead
  title={seoTitle}
  description={seoDescription}
  canonical={$page.url.origin + $page.url.pathname}
  robots={seoRobots}
/>

{#if !ui.isDetermined}
  <TikTokShopLoading variant="grid" />
{:else if ui.isMobile}
  <MobileSearchResultList products={data.products} searchQuery={data.searchQuery} loading={false} />
{:else}
  <ProductListDesktop
    products={data.products}
    categoryName={searchLabel}
    categorySlug=""
    serverTotal={data.total ?? data.products?.length ?? 0}
    facets={data.facets}
  />
{/if}