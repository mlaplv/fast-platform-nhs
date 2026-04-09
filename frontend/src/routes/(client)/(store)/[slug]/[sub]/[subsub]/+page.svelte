<script lang="ts">
  import HomeProductGrid from '$lib/components/storefront/home/HomeProductGrid.svelte';
  import ProductListMobile from '$lib/components/storefront/product/ProductListMobile.svelte';
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
  <title>{data.categoryName || 'Danh mục'} | Micsmo Elite</title>
</svelte:head>

<div class="category-page-wrapper bg-[#010101] min-h-screen">
  {#if isMobile}
    <div class="fixed top-0 left-0 w-full z-50 p-6 pointer-events-none">
      <span class="bg-red-600 text-white px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest shadow-lg">
        {data.categoryName}
      </span>
    </div>
    <ProductListMobile products={data.items} />
  {:else}
    <div class="max-w-7xl mx-auto p-6 md:p-12 pt-8">
      <div class="mb-4">
        <span class="bg-red-600 text-white px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest mb-4 inline-block shadow-lg shadow-red-600/20">
          Danh mục Cấp 3
        </span>
        <h1 class="text-5xl font-black text-white tracking-tighter italic uppercase drop-shadow-lg">{data.categoryName}</h1>
        <div class="h-1 w-24 bg-red-600 rounded-full mt-4 shadow-[0_0_10px_#dc2626]"></div>
      </div>
      <HomeProductGrid products={data.items} />
    </div>
  {/if}
</div>