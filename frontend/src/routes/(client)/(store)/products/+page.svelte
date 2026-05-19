<script lang="ts">
  import ProductListDesktop from '$lib/components/storefront/product/ProductListDesktop.svelte';
  import MobileSearchResultList from '$lib/components/storefront/product/MobileSearchResultList.svelte';
  import TikTokShopLoading from '$lib/components/storefront/product/TikTokShopLoading.svelte';
  import SeoHead from '$lib/components/storefront/seo/SeoHead.svelte';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { onMount } from 'svelte';

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
  const seoTitle = $derived(
    data.searchQuery
      ? `Tìm kiếm "${data.searchQuery}" | osmo Elite`
      : data.brand
        ? `Thương hiệu ${data.brand} chính hãng | osmo Elite`
        : data.origin
          ? `Xuất xứ ${data.origin} | osmo Elite`
          : "Tất cả sản phẩm | osmo Elite"
  );
  const seoDescription = $derived(
    data.searchQuery
      ? `Kết quả tìm kiếm "${data.searchQuery}" - ${data.total} sản phẩm chính hãng tại osmo Elite.`
      : data.brand
        ? `Danh sách sản phẩm thương hiệu ${data.brand} chính hãng nhập khẩu tại osmo Elite. Cam kết chất lượng.`
        : data.origin
          ? `Danh sách sản phẩm xuất xứ từ ${data.origin} chính hãng tại osmo Elite.`
          : "Khám phá toàn bộ sản phẩm chăm sóc sức khỏe chính hãng tại osmo Elite. Cam kết chất lượng, hỗ trợ 24/7."
  );
  const seoRobots = $derived((data.searchQuery || data.brand || data.origin) ? "noindex, nofollow" : "index, follow");

</script>

<SeoHead
  title={seoTitle}
  description={seoDescription}
  canonical="https://osmo/products"
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