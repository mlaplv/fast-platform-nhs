<script lang="ts">
  import ProductListDesktop from '$lib/components/storefront/product/ProductListDesktop.svelte';
  import ProductListMobile from '$lib/components/storefront/product/ProductListMobile.svelte';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import { onMount } from 'svelte';

  let { data }: { data: any } = $props();

  const searchStore = getSearchStore();
  let isMobile = $state(false);

  // Elite V2.2: Sync global search store with current page data (URL query)
  $effect(() => {
    if (data.searchQuery !== undefined && searchStore.searchQuery !== data.searchQuery) {
       searchStore.searchQuery = data.searchQuery;
    }
  });

  onMount(() => {
    isMobile = window.innerWidth < 768;
    const handleResize = () => {
      isMobile = window.innerWidth < 768;
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  });

  // Elite V2.2: Search context - build proper props for category-oriented components
  const searchLabel = $derived(data.searchQuery ? `Kết quả tìm kiếm: "${data.searchQuery}"` : 'Tất cả sản phẩm');
</script>

{#if isMobile}
  <ProductListMobile products={data.products} searchQuery={data.searchQuery} />
{:else}
  <ProductListDesktop 
    products={data.products} 
    categoryName={searchLabel}
    categorySlug=""
    serverTotal={data.total ?? data.products?.length ?? 0}
    facets={data.facets}
  />
{/if}