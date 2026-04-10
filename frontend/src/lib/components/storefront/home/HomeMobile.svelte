<!-- HomeMobile.svelte - Orchestrator chính -->
<!-- Tuân thủ: file size ≤ 500 dòng, z-index từ constants, không hardcode -->
<script lang="ts">
  import MobileSearchHeader     from './MobileSearchHeader.svelte';
  import MobileBannerCarousel   from './MobileBannerCarousel.svelte';
  import MobileServiceIcons     from './MobileServiceIcons.svelte';
  import MobileFlashSale        from './MobileFlashSale.svelte';
  import MobileProductFeed      from './MobileProductFeed.svelte';
  import MobileBottomNav        from './MobileBottomNav.svelte';

  interface Product {
    id: string;
    name: string;
    price: number;
    image: string;
    sales?: number;
    originalPrice?: number;
    slug?: string;
  }

  interface Props {
    banners: Array<{ id: string; image: string }>;
    categories: Array<{ id: string; name: string; slug: string; image?: string; icon?: string }>;
    products: Array<Product>;
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
    <MobileBannerCarousel {banners} />

    <!-- Service icon shortcuts -->
    <MobileServiceIcons />

    <!-- Flash Sale với countdown -->
    <MobileFlashSale />

    <!-- Tab filter + 2-column product grid -->
    <MobileProductFeed {products} />
  </div>

  <!-- Sticky bottom nav -->
  <MobileBottomNav inboxCount={0} />
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
    --mobile-search-h: 50px;    /* tsh-header: top-row 50px */
    --mobile-header-total: 50px;
  }

  .mobile-home-content {
    padding-bottom: 80px;
  }
</style>
