<!-- HomeMobile.svelte - Orchestrator chính -->
<!-- Tuân thủ: file size ≤ 500 dòng, z-index từ constants, không hardcode -->
<script lang="ts">
  import MobileSearchHeader     from './MobileSearchHeader.svelte';
  import MobileBannerCarousel   from './MobileBannerCarousel.svelte';
  import MobileServiceIcons     from './MobileServiceIcons.svelte';
  import MobileFlashSale        from './MobileFlashSale.svelte';
  import MobileProductFeed      from './MobileProductFeed.svelte';
  import MobileBottomNav       from './MobileBottomNav.svelte';

  import type { Product, Category, Banner } from '$lib/types';

  interface Props {
    banners: Banner[];
    categories: Category[];
    products: Product[];
    videos?: Array<{ id: string; url: string; title: string; likes: number; image: string }>;
  }

  let { banners, categories, products, videos }: Props = $props();
</script>

<!-- Wrapper: full page scroll, padding-bottom cho bottom nav -->
<div class="mobile-home-root">

  <!-- Sticky header: search + quick links (đã tích hợp chung) -->
  <MobileSearchHeader />

  <!-- Content scroll area -->
  <div class="mobile-home-content">
    <!-- Banner slidshow -->
    <MobileBannerCarousel {banners} {products} />

    <!-- Service icon shortcuts -->
    <MobileServiceIcons />

    <!-- Flash Sale với countdown -->
    <MobileFlashSale {products} />

    <!-- Tab filter + 2-column product grid -->
    <MobileProductFeed {products} {categories} />
  </div>

  <!-- Sticky bottom nav -->
  <MobileBottomNav />
</div>

<style>
  *,
  *::before,
  *::after { box-sizing: border-box; }

  .mobile-home-root {
    position: relative;
    width: 100%;
    max-width: 100vw;
    min-height: 100dvh;
    background: #f5f5f5;
    /* CSS vars cho child sticky offset */
    --mobile-search-h: 48px;    /* tsh-header: top-row 48px */
    --mobile-header-total: 48px;
  }

  .mobile-home-content {
    padding-bottom: 80px;
  }
</style>
