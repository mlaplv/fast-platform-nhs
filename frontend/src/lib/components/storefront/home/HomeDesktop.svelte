<script lang="ts">
  import { type Product, type Category, type Banner } from '$lib/types';
  import HomeBanner from './HomeBanner.svelte';
  import HomeCategory from './HomeCategory.svelte';
  import HomeFlashDeal from './HomeFlashDeal.svelte';
  import HomeProductGrid from './HomeProductGrid.svelte';

  interface Props {
    banners: Banner[];
    categories: Category[];
    products: Product[];
    aiProducts: Product[];
  }
  let { banners, categories, products, aiProducts }: Props = $props();
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
    <HomeFlashDeal {products} />
    <HomeProductGrid {products} productsAi={aiProducts} />
  </div>
</div>
