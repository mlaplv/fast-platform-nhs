<script lang="ts">
  import ProductListDesktop from '$lib/components/storefront/product/ProductListDesktop.svelte';
  import MobileSearchResultList from '$lib/components/storefront/product/MobileSearchResultList.svelte';
  import TikTokShopLoading from '$lib/components/storefront/product/TikTokShopLoading.svelte';
  import SeoHead from '$lib/components/storefront/seo/SeoHead.svelte';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { page } from '$app/stores';

  import type { Product, ProductFacets, Article } from '$lib/types';

  interface PageData {
    products: Product[];
    total: number;
    searchQuery: string;
    facets: ProductFacets | null;
    articles?: Article[];
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
      : 'Tìm kiếm sản phẩm & kiến thức'
  );

  // GEO 2026: SEO Meta
  const siteName = $derived(ui.settings?.basic_info?.site_name || ui.settings?.site_name || "osmo.vn");
  const seoTitle = $derived(
    data.searchQuery
      ? `Tìm kiếm "${data.searchQuery}" | ${siteName}`
      : `Tìm kiếm sản phẩm & kiến thức | ${siteName}`
  );
  const seoDescription = $derived(
    data.searchQuery
      ? `Kết quả tìm kiếm "${data.searchQuery}" - ${data.total} sản phẩm và kiến thức chuyên sâu tại ${siteName}.`
      : `Tìm kiếm toàn bộ sản phẩm và kiến thức chuyên sâu tại ${siteName}.`
  );
</script>

<SeoHead
  title={seoTitle}
  description={seoDescription}
  canonical={$page.url.origin + $page.url.pathname}
  robots="noindex, nofollow"
/>

{#if !ui.isDetermined}
  <TikTokShopLoading variant="grid" />
{:else if ui.isMobile}
  <MobileSearchResultList products={data.products} searchQuery={data.searchQuery} loading={false} articles={data.articles || []} />
{:else}
  <ProductListDesktop
    products={data.products}
    categoryName={searchLabel}
    categorySlug=""
    serverTotal={data.total ?? data.products?.length ?? 0}
    facets={data.facets}
    articles={data.articles || []}
  />
{/if}
