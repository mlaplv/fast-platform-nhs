<script lang="ts">
  import { type Product, type Category, type Banner } from '$lib/types';
  import { goto } from '$app/navigation';
  import HomeBanner from './HomeBanner.svelte';
  import HomeCategory from './HomeCategory.svelte';
  import HomeFlashDeal from './HomeFlashDeal.svelte';
  import HomeProductGrid from './HomeProductGrid.svelte';
  import CategoryPills from './CategoryPills.svelte';

  interface Props {
    banners: Banner[];
    categories: Category[];
    products: Product[];
    aiProducts: Product[];
  }
  let { banners, categories, products, aiProducts }: Props = $props();

  let activeCatIndex = $state(0);
  
  function handleCatChange(index: number) {
    activeCatIndex = index;
    if (index > 0) {
      const selectedCat = categories[index - 1];
      if (selectedCat) {
        goto(`/${selectedCat.slug}/`);
      }
    }
  }
</script>

<div class="desktop-home-wrapper bg-[#f5f5f5] min-h-screen w-full pb-10">
  <!-- Top Section (White Opaque) -->
  <div class="bg-white w-full border-b border-gray-100 shadow-sm">
    <div class="max-w-[1200px] mx-auto flex flex-col px-4 xl:px-0">
      <HomeBanner {banners} />
      
      <!-- Viral 2026 Category Navigation -->
      <div class="sticky top-[var(--z-header)] bg-white z-[var(--z-category-pills)]">
        <CategoryPills {categories} activeTab={activeCatIndex} onTabChange={handleCatChange} />
      </div>

      <HomeCategory {categories} />
    </div>
  </div>

  <!-- Content Section (Neutral Gray) -->
  <div class="max-w-[1200px] mx-auto mt-6 flex flex-col gap-8 px-4 xl:px-0">
    <HomeFlashDeal {products} />
    <HomeProductGrid {products} productsAi={aiProducts} />
  </div>
</div>
