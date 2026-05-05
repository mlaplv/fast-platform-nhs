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
  import ProductDetailRelated from './ProductDetailRelated.svelte';
  import ProductMobileVariantSelector from './ProductMobileVariantSelector.svelte';

  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte';
  import MobileBottomNav from '../home/MobileBottomNav.svelte';
  import type { ProductVariant, ReviewStats } from '$lib/types';

  interface Props {
    product: Product;
    relatedProducts?: Product[];
  }
  let { product, relatedProducts = [] }: Props = $props();

  const cartStore = getCartStore();

  // State: Navigation & Visibility
  let activeTab = $state('overview');
  let showTabs = $state(false);
  let showVariantSelector = $state(false);
  const pVariants = $derived(product.variants || []);
  let selectedVariant = $state<ProductVariant | null>(null);
  
  $effect(() => {
    if (!selectedVariant && pVariants.length > 0) {
      selectedVariant = pVariants.find(v => v.is_default) || pVariants[0];
    }
  });
  let selectedQty = $state(1);

  // State: Flash Sale Countdown
  let timeLeft = $state({ hours: 14, minutes: 9, seconds: 9 });
  let stats = $state<ReviewStats | null>(null);

  onMount(() => {
    // 1. Countdown Timer
    const timer = setInterval(() => {
      if (timeLeft.seconds > 0) timeLeft.seconds--;
      else if (timeLeft.minutes > 0) { timeLeft.minutes--; timeLeft.seconds = 59; }
      else if (timeLeft.hours > 0) { timeLeft.hours--; timeLeft.minutes = 59; timeLeft.seconds = 59; }
    }, 1000);

    // 1.5 Fetch Real Stats (Elite V2.2)
    if (product?.id) {
      fetch(`/api/v1/client/reviews/stats?entity_type=PRODUCT&entity_id=${product.id}`)
        .then(res => res.ok ? res.json() : null)
        .then(data => { if (data) stats = data; })
        .catch(e => console.error('Failed to load mobile product stats:', e));
    }

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

  const variations = $derived(product.tier_variations || product.tierVariations || product.attributes?.tier_variations || product.metadata?.tier_variations || []);

  function handleVariantConfirm(variant: ProductVariant | undefined, qty: number) {
    selectedVariant = variant || null;
    selectedQty = qty;
    showVariantSelector = false;
  }

  function addToCart() {
    if (!selectedVariant && variations.length > 0) {
      showVariantSelector = true;
      return;
    }
    cartStore.addItem(product, selectedVariant || undefined, selectedQty);
  }

  function buyNow() {
    if (!selectedVariant && variations.length > 0) {
      showVariantSelector = true;
      return;
    }
    cartStore.addItem(product, selectedVariant || undefined, selectedQty);
    goto('/checkout');
  }

  // SGE Shield V1.0: Deterministic DOM Entropy (Product Detail Mobile)
  const wrapperTags = ['div', 'article', 'section', 'main'];
  const seedLength = $derived(product?.name ? product.name.length : 10);
  const outerWrapper = $derived(wrapperTags[seedLength % wrapperTags.length]);
  const mainWrapper = $derived(['div', 'main', 'section'][(seedLength + 3) % 3]);
</script>

<svelte:element this={outerWrapper} class="product-mobile-root">

  <!-- 1. STICKY HEADER -->
  <ProductMobileHeader {product} {showTabs} {activeTab} onScrollToSection={scrollToSection} />

  <!-- 2. MAIN CONTENT SECTIONS -->
  <svelte:element this={mainWrapper} class="content-body">
    <div id="overview">
      <ProductMobileOverview 
        {product} 
        {timeLeft} 
        {stats}
        {selectedVariant} 
        selectedQty={selectedQty}
        onOpenSelector={() => showVariantSelector = true} 
      />
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
      <ProductDetailRelated {product} isMobile={true} />
    </div>

  </svelte:element>

  <!-- 5. STICKY BOTTOM NAV -->
  <MobileBottomNav
    isProductMode={true}
    {product}
    onAddToCart={addToCart}
    onBuyNow={buyNow}
    onChatOpen={() => supportAgent.open()}
  />

  <!-- 6. VARIANT SELECTOR MODAL -->
  <ProductMobileVariantSelector 
    {product}
    show={showVariantSelector}
    onClose={() => showVariantSelector = false}
    onConfirm={handleVariantConfirm}
  />

  <div class="h-12"></div>
</svelte:element>

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
