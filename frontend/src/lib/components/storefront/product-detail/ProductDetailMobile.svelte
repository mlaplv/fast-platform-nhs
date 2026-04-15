<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import type { Product } from '$lib/types';

  // Sub-components (Elite V2.2 Refactored for < 500 lines)
  import ProductMobileHeader from './ProductMobileHeader.svelte';
  import ProductMobileOverview from './ProductMobileOverview.svelte';
  import ProductMobileReviews from './ProductMobileReviews.svelte';
  import ProductMobileSpecs from './ProductMobileSpecs.svelte';
  import ProductMobileRecommendations from './ProductMobileRecommendations.svelte';
  import MobileBottomNav from '../home/MobileBottomNav.svelte';

  interface Props {
    product: Product;
    relatedProducts?: Product[];
  }
  let { product, relatedProducts = [] }: Props = $props();

  const cartStore = getCartStore();

  // State: Navigation & Visibility
  let activeTab = $state('overview');
  let showTabs = $state(false);
  let sectionRefs = $state<Record<string, HTMLElement | null>>({
    overview: null,
    reviews: null,
    description: null,
    recommendations: null
  });

  // State: Flash Sale Countdown
  let timeLeft = $state({ hours: 14, minutes: 9, seconds: 9 });

  onMount(() => {
    // 1. Countdown Timer
    const timer = setInterval(() => {
      if (timeLeft.seconds > 0) timeLeft.seconds--;
      else if (timeLeft.minutes > 0) { timeLeft.minutes--; timeLeft.seconds = 59; }
      else if (timeLeft.hours > 0) { timeLeft.hours--; timeLeft.minutes = 59; timeLeft.seconds = 59; }
    }, 1000);

    // 2. Scroll Observer for Tabs
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) activeTab = entry.target.id;
      });
    }, { rootMargin: '-110px 0px -80% 0px' });

    ['overview', 'reviews', 'description', 'recommendations'].forEach(id => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    // 3. Tab Visibility Logic
    const handleScroll = () => { showTabs = window.scrollY > 300; };
    window.addEventListener('scroll', handleScroll);

    return () => {
      clearInterval(timer);
      observer.disconnect();
      window.removeEventListener('scroll', handleScroll);
    };
  });

  function scrollToSection(id: string) {
    activeTab = id;
    const element = document.getElementById(id);
    if (element) {
      const headerHeight = 90;
      const rect = element.getBoundingClientRect();
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      window.scrollTo({ top: rect.top + scrollTop - headerHeight, behavior: 'smooth' });
    }
  }

  function buyNow() {
    // Elite V2.2: Direct checkout path (TikTok Shop / Shopee style) bypassed modal
    const defaultVariant = product.variants && product.variants.length > 0 ? product.variants[0] : undefined;
    cartStore.addItem(product, defaultVariant);
    goto('/checkout');
  }
</script>

<div class="product-mobile-root">

  <!-- 1. STICKY HEADER -->
  <ProductMobileHeader {product} {showTabs} {activeTab} onScrollToSection={scrollToSection} />

  <!-- 2. MAIN CONTENT SECTIONS -->
  <main class="content-body">
    <div id="overview">
      <ProductMobileOverview {product} {timeLeft} />
    </div>
    
    <div class="section-divider"></div>

    <div id="reviews">
      <ProductMobileReviews {product} />
    </div>

    <div class="section-divider"></div>

    <div id="description">
      <ProductMobileSpecs {product} />
    </div>

    <div class="section-divider"></div>

    <div id="recommendations">
      <ProductMobileRecommendations {relatedProducts} />
    </div>
  </main>

  <!-- 5. STICKY BOTTOM NAV -->
  <MobileBottomNav
    isProductMode={true}
    {product}
    onAddToCart={() => cartStore.addItem(product)}
    onBuyNow={buyNow}
    onChatOpen={() => {}}
  />

  <div class="h-12"></div>
</div>

<style>
  .product-mobile-root {
    background: #f5f5f5;
    min-height: 100vh;
    width: 100%;
  }

  .content-body {
    display: flex;
    flex-direction: column;
  }

  .section-divider {
    height: 8px;
    background: #f5f5f5;
  }

  .h-12 {
    height: 48px;
  }
</style>
