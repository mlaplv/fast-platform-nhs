<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import type { Product } from '$lib/types';

  // Sub-components (Elite V2.2 Refactored for < 500 lines)
  import ProductMobileHeader from './modules/ProductMobileHeader.svelte';
  import ProductMobileOverview from './modules/ProductMobileOverview.svelte';
  import ProductMobileReviews from './modules/ProductMobileReviews.svelte';
  import ProductMobileSpecs from './modules/ProductMobileSpecs.svelte';
  import RelatedProducts from '../shared/RelatedProducts.svelte';
  import ProductMobileVariantSelector from './modules/ProductMobileVariantSelector.svelte';

  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { shareToPlatform } from '$lib/utils/commerce/viral';
  import MobileBottomNav from '../../home/MobileBottomNav.svelte';
  import type { ProductVariant, ReviewStats } from '$lib/types';

  interface Props {
    product: Product;
    relatedProducts?: Product[];
    reviewStats?: ReviewStats | null;
  }
  let { product, relatedProducts = [], reviewStats = null }: Props = $props();

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
  // Elite Performance Fix P1.2: Khởi tạo từ server-prefetched data — KHÔNG fetch lại trong onMount
  let stats = $state<ReviewStats | null>(reviewStats);

  // Sync stats khi server data thay đổi (navigate giữa các product)
  $effect(() => {
    if (reviewStats !== undefined) {
      stats = reviewStats;
    }
  });

  // Elite V2.2: Global Viral State & Share Engine
  let isViralUnlocked = $state(false);
  let viralStep = $state<'idle' | 'sharing' | 'awaiting_confirm' | 'verifying' | 'revealed'>('idle');

  $effect(() => {
    if (typeof window !== 'undefined') {
      isViralUnlocked = !!localStorage.getItem(`viral_unlocked_${product.id}`);
      if (isViralUnlocked) viralStep = 'revealed';
    }
  });

  let campaignData = $state<any>(null);
  let isCampaignLoaded = $state(false);

  $effect(() => {
    const vId = product.metadata?.viral_suite?.share_promotion?.voucher_id || (product.metadata as any)?.share_promotion?.voucher_id;
    if (vId && !isCampaignLoaded) {
      isCampaignLoaded = true;
      fetch(`/api/v1/client/viral/campaign/${vId}`)
        .then(res => res.json())
        .then(data => { campaignData = data; })
        .catch(() => {});
    }
  });

  const displayRewardLabel = $derived(
    campaignData?.voucher_label || 
    product.metadata?.viral_suite?.share_reward_label || 
    'phần quà đặc quyền'
  );


  const clientUi = getClientUi();

  onMount(() => {
    // 1. Countdown Timer
    const timer = setInterval(() => {
      if (timeLeft.seconds > 0) timeLeft.seconds--;
      else if (timeLeft.minutes > 0) { timeLeft.minutes--; timeLeft.seconds = 59; }
      else if (timeLeft.hours > 0) { timeLeft.hours--; timeLeft.minutes = 59; timeLeft.seconds = 59; }
    }, 1000);

    // 1.5 Stats: Đã được server prefetch và truyền qua prop reviewStats — KHÔNG cần fetch ở đây nữa
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

  async function shareProduct() {
    // Elite V2.2: Intelligence Share Flow (Share-to-Unlock Integrated)
    const viralSuite = product.metadata?.viral_suite || (product.metadata as Record<string, unknown>)?.share_promotion;
    const isViralEnabled = viralSuite?.enabled === true || !!viralSuite?.voucher_id;

    if (isViralEnabled && !isViralUnlocked) {
      // Trigger Viral Intent via the unified engine
      viralStep = 'sharing';
      try {
        const res = await fetch('/api/v1/client/viral/share-intent', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ product_id: product.id }),
        });
        if (!res.ok) throw new Error('Yêu cầu thất bại');
        const data = await res.json();
        
        // Store OTT in temporary state (will be used by confirm step)
        sessionStorage.setItem(`viral_intent_${product.id}`, JSON.stringify({
          token: data.token,
          fingerprint: data.fingerprint,
          timestamp: Date.now()
        }));

        await shareToPlatform('facebook', window.location.href, product.name);
        viralStep = 'awaiting_confirm';
      } catch (e: unknown) {
        clientUi.showToast(e instanceof Error ? e.message : 'Lỗi khởi tạo chia sẻ', 'error');
        viralStep = 'idle';
      }
      return;
    }

    // Standard fallback for already unlocked or non-viral products
    if (typeof navigator !== 'undefined' && navigator.share) {
      try {
        await navigator.share({
          title: product.name,
          text: `Xem ngay ${product.name}!`,
          url: window.location.href
        });
      } catch (_e) { }
    } else if (typeof navigator !== 'undefined' && navigator.clipboard) {
      await navigator.clipboard.writeText(window.location.href);
      clientUi.showToast('Đã sao chép liên kết!', 'success');
    }
  }
  async function verifyShare() {
    const savedIntent = sessionStorage.getItem(`viral_intent_${product.id}`);
    if (!savedIntent) {
      viralStep = 'idle';
      return;
    }
    const { token, fingerprint } = JSON.parse(savedIntent);
    const viralSuite = product.metadata?.viral_suite || (product.metadata as Record<string, unknown>)?.share_promotion;
    const voucherId = viralSuite?.share_promotion?.voucher_id || viralSuite?.voucher_id;

    viralStep = 'verifying';
    try {
      const res = await fetch('/api/v1/client/viral/verify-share', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          product_id: product.id, 
          fingerprint, 
          token, 
          voucher_id: voucherId 
        }),
      });
      if (!res.ok) throw new Error('Xác minh thất bại');
      const data = await res.json();
      
      isViralUnlocked = true;
      viralStep = 'revealed';
      
      localStorage.setItem(`viral_unlocked_${product.id}`, JSON.stringify({ 
        code: data.voucher_code, 
        label: data.voucher_label, 
        unlocked_at: Date.now() 
      }));

      clientUi.showToast('🎉 Đã mở khóa quà tặng!', 'success');
      sessionStorage.removeItem(`viral_intent_${product.id}`);
    } catch (e: unknown) {
      clientUi.showToast(e instanceof Error ? e.message : 'Xác minh thất bại', 'error');
      viralStep = 'idle';
    }
  }
</script>

<svelte:element this={outerWrapper} class="product-mobile-root">

  <!-- 1. STICKY HEADER -->
  <ProductMobileHeader {product} {showTabs} {activeTab} onScrollToSection={scrollToSection} onShare={shareProduct} />

  <!-- 2. MAIN CONTENT SECTIONS -->
  <svelte:element this={mainWrapper} class="content-body">
    <div id="overview">
      <ProductMobileOverview 
        {product} 
        {timeLeft} 
        {stats}
        {selectedVariant} 
        selectedQty={selectedQty}
        bind:isViralUnlocked
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
      <RelatedProducts {product} isMobile={true} initialProducts={relatedProducts} />
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

  <ProductMobileVariantSelector 
    {product}
    show={showVariantSelector}
    onClose={() => showVariantSelector = false}
    onConfirm={handleVariantConfirm}
  />

  <!-- 7. GLOBAL VIRAL CONFIRMATION (Elite V2026) -->
  {#if viralStep === 'awaiting_confirm'}
    <div class="global-viral-overlay">
      <div class="global-confirm-card">
        <span class="confirm-title">Đã chia sẻ thành công?</span>
        <p class="confirm-sub">Xác nhận để mở khóa {displayRewardLabel}</p>
        <div class="confirm-btns">
          <button class="btn-cancel" onclick={() => viralStep = 'idle'}>Hủy</button>
          <button class="btn-verify" onclick={verifyShare}>XÁC NHẬN NGAY</button>
        </div>
      </div>
    </div>
  {/if}

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

  /* Viral Global UI */
  .global-viral-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.7);
    backdrop-filter: blur(8px);
    z-index: 2000;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    animation: fadeIn 0.3s ease;
  }

  .global-confirm-card {
    background: white;
    width: 100%;
    max-width: 320px;
    border-radius: 12px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    box-shadow: 0 20px 50px rgba(0,0,0,0.3);
    border: 1px solid rgba(238, 77, 45, 0.2);
  }

  .confirm-title { font-size: 18px; font-weight: 1000; color: #000; margin-bottom: 8px; }
  .confirm-sub { font-size: 13px; color: #666; margin-bottom: 24px; }
  .confirm-btns { display: flex; gap: 12px; width: 100%; }
  
  .btn-cancel { flex: 1; height: 44px; border-radius: 8px; background: #f5f5f5; color: #666; border: none; font-weight: 800; font-size: 13px; }
  .btn-verify { flex: 1; height: 44px; border-radius: 8px; background: #ee4d2d; color: white; border: none; font-weight: 1000; font-size: 13px; box-shadow: 0 4px 12px rgba(238, 77, 45, 0.3); }

  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
