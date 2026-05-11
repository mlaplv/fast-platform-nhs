<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  
  // Types
  import type { Product, ProductVariant, ReviewStats } from '$lib/types';
  
  // Stores
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';

  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte';
  
  // Components
  import ProductMobileHeader from './modules/ProductMobileHeader.svelte';
  import ProductMobileOverview from './modules/ProductMobileOverview.svelte';
  import ProductMobileSpecs from './modules/ProductMobileSpecs.svelte';
  import ProductMobileReviews from './modules/ProductMobileReviews.svelte';
  import ProductMobileRecommendations from './modules/ProductMobileRecommendations.svelte';
  import ProductMobileVariantSelector from './modules/ProductMobileVariantSelector.svelte';
  import MobileBottomNav from '$lib/components/storefront/home/MobileBottomNav.svelte';

  interface Props {
    product: Product;
    relatedProducts?: Product[];
    reviewStats?: ReviewStats | null;
  }

  let { product, relatedProducts = [], reviewStats = null }: Props = $props();

  const cartStore = getCartStore();
  const clientUi = getClientUi();

  // --- TAB & SCROLL STATE ---
  let activeTab = $state('overview');
  let showTabs = $state(false);
  let scrollContainer: HTMLElement | undefined = $state();

  function handleScroll() {
    if (!scrollContainer) return;
    const st = scrollContainer.scrollTop;
    showTabs = st > 400;

    const sections = ['overview', 'description', 'reviews', 'recommendations'];
    for (const id of sections.reverse()) {
      const el = document.getElementById(id);
      if (el && el.offsetTop <= st + 100) {
        activeTab = id;
        break;
      }
    }
  }

  function scrollToSection(id: string) {
    const el = document.getElementById(id);
    if (el && scrollContainer) {
      scrollContainer.scrollTo({
        top: el.offsetTop - 80,
        behavior: 'smooth'
      });
    }
  }

  // --- VARIANT & CART STATE ---
  let showVariantSelector = $state(false);
  let selectedVariant = $state<ProductVariant | null>(null);
  let selectedQty = $state(1);

  const variations = $derived(product.tier_variations || product.tierVariations || []);

  function handleVariantConfirm(variant: ProductVariant | null, qty: number) {
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

  // --- FLASH SALE COUNTDOWN ---
  let timeLeft = $state({ hours: 0, minutes: 0, seconds: 0 });
  const flashSaleEnd = $derived(
    product.metadata?.flash_sale_end
      ? new Date(product.metadata.flash_sale_end).getTime()
      : null
  );

  $effect(() => {
    if (!flashSaleEnd) return;
    function updateCountdown() {
      const diff = Math.max(0, flashSaleEnd! - Date.now());
      timeLeft.hours = Math.floor(diff / 3600000);
      timeLeft.minutes = Math.floor((diff % 3600000) / 60000);
      timeLeft.seconds = Math.floor((diff % 60000) / 1000);
    }
    updateCountdown();
    const timer = setInterval(updateCountdown, 1000);
    return () => clearInterval(timer);
  });

  // --- VIRAL SHARING ---
  let viralStep = $state<'idle' | 'sharing' | 'awaiting_confirm' | 'verifying' | 'revealed'>('idle');
  let isViralUnlocked = $state(false);
  let displayRewardLabel = $derived(product.metadata?.viral_suite?.share_promotion?.reward_label || (product.metadata as any)?.reward_label || 'Phần quà bí mật');

  async function shareProduct() {
    const viralSuite = product.metadata?.viral_suite || (product.metadata as any)?.share_promotion;
    const isViralEnabled = viralSuite?.enabled === true || !!viralSuite?.voucher_id;

    if (isViralEnabled && !isViralUnlocked) {
      viralStep = 'sharing';
      try {
        const res = await fetch('/api/v1/client/viral/share-intent', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ product_id: product.id }),
        });
        if (!res.ok) throw new Error('Yêu cầu thất bại');
        const data = await res.json();
        
        sessionStorage.setItem(`viral_intent_${product.id}`, JSON.stringify({
          token: data.token,
          fingerprint: data.fingerprint,
          timestamp: Date.now()
        }));

        // Trigger native share or clipboard
        if (navigator.share) {
          await navigator.share({ title: product.name, url: window.location.href });
        } else {
          await navigator.clipboard.writeText(window.location.href);
          clientUi.showToast('Đã sao chép liên kết!', 'success');
        }
        viralStep = 'awaiting_confirm';
      } catch (e: any) {
        clientUi.showToast(e.message || 'Lỗi khởi tạo chia sẻ', 'error');
        viralStep = 'idle';
      }
      return;
    }

    if (navigator.share) {
      navigator.share({ title: product.name, url: window.location.href });
    } else {
      navigator.clipboard.writeText(window.location.href);
      clientUi.showToast('Đã sao chép liên kết!', 'success');
    }
  }

  async function verifyShare() {
    const savedIntent = sessionStorage.getItem(`viral_intent_${product.id}`);
    if (!savedIntent) { viralStep = 'idle'; return; }
    
    const { token, fingerprint } = JSON.parse(savedIntent);
    const viralSuite = product.metadata?.viral_suite || (product.metadata as any)?.share_promotion;
    const voucherId = viralSuite?.share_promotion?.voucher_id || viralSuite?.voucher_id;

    viralStep = 'verifying';
    try {
      const res = await fetch('/api/v1/client/viral/verify-share', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: product.id, fingerprint, token, voucher_id: voucherId }),
      });
      if (!res.ok) throw new Error('Xác minh thất bại');
      const data = await res.json();
      
      isViralUnlocked = true;
      viralStep = 'revealed';
      localStorage.setItem(`viral_unlocked_${product.id}`, JSON.stringify({ 
        code: data.voucher_code, label: data.voucher_label, unlocked_at: Date.now() 
      }));
      clientUi.showToast('🎉 Đã mở khóa quà tặng!', 'success');
    } catch (e: any) {
      clientUi.showToast(e.message || 'Xác minh thất bại', 'error');
      viralStep = 'idle';
    }
  }

  onMount(() => {
    if (scrollContainer) scrollContainer.addEventListener('scroll', handleScroll);
    return () => {
      if (scrollContainer) scrollContainer.removeEventListener('scroll', handleScroll);
    };
  });
</script>

<svelte:element this="div" class="product-mobile-root" bind:this={scrollContainer}>
  <!-- 1. STICKY HEADER -->
  <ProductMobileHeader 
    {product} 
    {showTabs} 
    {activeTab} 
    onScrollToSection={scrollToSection} 
    onShare={shareProduct} 
  />

  <!-- 2. MAIN CONTENT -->
  <div class="content-body">
    <section id="overview">
      <ProductMobileOverview 
        {product} 
        {timeLeft} 
        stats={reviewStats}
        {selectedVariant} 
        {selectedQty}
        bind:isViralUnlocked
        onOpenSelector={() => showVariantSelector = true} 
      />
    </section>

    <div class="section-divider"></div>

    <section id="description">
      <ProductMobileSpecs {product} />
    </section>

    <div class="section-divider"></div>

    <section id="reviews">
      <ProductMobileReviews {product} />
    </section>

    <div class="section-divider"></div>

    <section id="recommendations">
      <ProductMobileRecommendations {relatedProducts} />
    </section>
  </div>

  <!-- 3. FOOTER NAV -->
  <MobileBottomNav
    isProductMode={true}
    {product}
    onAddToCart={addToCart}
    onBuyNow={buyNow}
    onChatOpen={() => supportAgent.open()}
  />

  <!-- 4. VARIANT SELECTOR -->
  <ProductMobileVariantSelector 
    {product}
    show={showVariantSelector}
    onClose={() => showVariantSelector = false}
    onConfirm={handleVariantConfirm}
  />

  <!-- 5. VIRAL OVERLAY -->
  {#if viralStep === 'awaiting_confirm'}
    <div class="global-viral-overlay">
      <div class="global-confirm-card">
        <span class="confirm-title">Đã chia sẻ thành công?</span>
        <p class="confirm-sub">Xác nhận để mở khóa <span class="reward-label">{displayRewardLabel}</span></p>
        <div class="confirm-btns">
          <button class="btn-cancel" onclick={() => viralStep = 'idle'}>Hủy</button>
          <button class="btn-verify" onclick={verifyShare}>Xác nhận ngay</button>
        </div>
      </div>
    </div>
  {/if}

  <div class="h-20"></div>
</svelte:element>

<style>
  .product-mobile-root {
    background: #f5f5f5;
    height: 100vh;
    width: 100%;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
  }

  .content-body {
    display: flex;
    flex-direction: column;
  }

  .section-divider {
    height: 8px;
    background: #f5f5f5;
  }

  .h-20 {
    height: 80px;
  }

  /* Viral Global UI */
  .global-viral-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.7);
    backdrop-filter: blur(8px);
    z-index: var(--z-overlay, 20000);
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
  .reward-label { display: inline-block !important; text-transform: lowercase !important; }
  .reward-label::first-letter { text-transform: uppercase !important; }
  .confirm-btns { display: flex; gap: 12px; width: 100%; }
  
  .btn-cancel { flex: 1; height: 44px; border-radius: 8px; background: #f5f5f5; color: #666; border: none; font-weight: 800; font-size: 13px; cursor: pointer; }
  .btn-verify { flex: 1; height: 44px; border-radius: 8px; background: #ee4d2d; color: white; border: none; font-weight: 1000; font-size: 13px; box-shadow: 0 4px 12px rgba(238, 77, 45, 0.3); cursor: pointer; }

  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
