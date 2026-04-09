<script lang="ts">
  import HomeBanner from './HomeBanner.svelte';
  import HomeCategory from './HomeCategory.svelte';
  import HomeFlashDeal from './HomeFlashDeal.svelte';
  import HomeProductGrid from './HomeProductGrid.svelte';

  interface Props {
    banners: Array<{ id: string; image: string }>;
    categories: Array<{ id: string; name: string; icon: string }>;
    products: Array<{ id: string; name: string; price: number; image: string }>;
  }
  let { banners, categories, products }: Props = $props();
</script>

<div class="desktop-home-wrapper bg-[#f5f5f5] min-h-screen w-full pb-10">
  <!-- Background White Wrapper for Top Section -->
  <div class="bg-white w-full border-b border-gray-200 shadow-sm">
    <div class="max-w-[1200px] mx-auto pt-1 flex flex-col px-4 xl:px-0">
      <HomeBanner {banners} />
      <HomeCategory {categories} />
    </div>
  </div>

  <!-- Background Gray Wrapper for Products Section -->
  <div class="max-w-[1200px] mx-auto mt-4 flex flex-col gap-4 px-4 xl:px-0">
    <HomeFlashDeal />
    <HomeProductGrid {products} />
  </div>
</div>
