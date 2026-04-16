<script lang="ts">
  import ProductListDesktop from '$lib/components/storefront/product/ProductListDesktop.svelte';
  import MobileSearchResultList from '$lib/components/storefront/product/MobileSearchResultList.svelte';
  import TikTokShopLoading from '$lib/components/storefront/product/TikTokShopLoading.svelte';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { onMount } from 'svelte';

  import type { Product, ProductFacets } from '$lib/types';

  interface PageData {
    products: Product[];
    total: number;
    searchQuery: string;
    facets: ProductFacets | null;
  }

  let { data }: { data: PageData } = $props();
  const ui = getClientUi();
  const searchStore = getSearchStore();

  // Elite V2.2: Sync global search store with current page data (URL query)
  $effect(() => {
    if (data.searchQuery !== undefined && searchStore.searchQuery !== data.searchQuery) {
       searchStore.searchQuery = data.searchQuery;
    }
  });

  onMount(() => {
    return ui.initObservers();
  });

  // Elite V2.2: Search context - build proper props for category-oriented components
  const searchLabel = $derived(data.searchQuery ? `Kết quả tìm kiếm: "${data.searchQuery}"` : 'Tất cả sản phẩm');
</script>

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