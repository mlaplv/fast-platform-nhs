<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";

  // Types
  import type { Product, ProductVariant, ReviewStats, BarcodeVerificationResponse } from "$lib/types";

  // Stores
  import { getCartStore } from "$lib/state/commerce/cart.svelte";
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import { supportAgent } from "$lib/state/commerce/supportAgent.svelte";
  import { authStore } from "$lib/state/authStore.svelte";

  // Components
  import ProductMobileHeader from "./modules/ProductMobileHeader.svelte";
  import ProductMobileOverview from "./modules/ProductMobileOverview.svelte";
  import ProductMobileSpecs from "./modules/ProductMobileSpecs.svelte";
  import ProductMobileReviews from "./modules/ProductMobileReviews.svelte";
  import ProductMobileRecommendations from "./modules/ProductMobileRecommendations.svelte";
  import ProductMobileVariantSelector from "./modules/ProductMobileVariantSelector.svelte";
  import MobileBottomNav from "$lib/components/storefront/home/MobileBottomNav.svelte";
  import BottomSheet from "$lib/components/storefront/funnel/mobile/BottomSheet.svelte";
  import ScannerHUD from "../shared/ScannerHUD.svelte";
  import MobileVerificationCenter from "../shared/MobileVerificationCenter.svelte";


  interface Props {
    product: Product;
    relatedProducts?: Product[];
    reviewStats?: ReviewStats | null;
    resolvedLcpUrl?: string;
    isEmbedded?: boolean;
  }

  let { product, relatedProducts = [], reviewStats = null, resolvedLcpUrl, isEmbedded = false }: Props = $props();

  const cartStore = getCartStore();
  const clientUi = getClientUi();

  // --- TAB & SCROLL STATE ---
  let activeTab = $state("overview");
  let isScrollingToSection = $state(false);
  let loadBelowFold = $state(true);
  let showTabs = $state(false);
  let isScrolled = $state(false);
  let isShrunk = $state(false);
  let lastScrollY = 0;
  let scrollRatio = $state(0);
  let hideRatio = $state(0);

  let scrollTicking = false;
  function handleScroll() {
    if (scrollTicking) return;
    scrollTicking = true;
    requestAnimationFrame(() => {
      const st = window.scrollY;
      showTabs = st > 400;
      isScrolled = st > 50;

      // Directional scroll for Bottom Nav (Sync with Home)
      const threshold = 15;
      if (st > lastScrollY + threshold && st > 80) {
        isShrunk = true;
        lastScrollY = st;
      } else if (st < lastScrollY - threshold || st <= 80) {
        isShrunk = false;
        lastScrollY = st;
      }

      // Shrink effect for Header: 0 to 1 over 100px
      scrollRatio = Math.min(1, st / 100);
      // Hide effect for Viral: 0 to 1 between 150px and 350px
      hideRatio = Math.max(0, Math.min(1, (st - 150) / 200));
      scrollTicking = false;
    });
  }

  function scrollToSection(id: string) {
    activeTab = id;
    isScrollingToSection = true;
    setTimeout(() => {
      const el = document.getElementById(id);
      if (el) {
        requestAnimationFrame(() => {
          const rect = el.getBoundingClientRect();
          const scrollTop = window.scrollY || document.documentElement.scrollTop;
          window.scrollTo({
            top: rect.top + scrollTop - 80,
            behavior: "smooth",
          });
        });
      }
      setTimeout(() => {
        isScrollingToSection = false;
      }, 800);
    }, 0);
  }

  // --- VARIANT & CART STATE ---
  let showVariantSelector = $state(false);
  let selectedVariant = $state<ProductVariant | null>(null);
  let selectedQty = $state(1);

  const variations = $derived(
    product.tier_variations || product.tierVariations || [],
  );

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
    goto("/checkout");
  }

  // --- FLASH SALE COUNTDOWN ---
  let timeLeft = $state({ hours: 0, minutes: 0, seconds: 0 });
  const flashSaleEnd = $derived(
    product.metadata?.flash_sale_end
      ? new Date(product.metadata.flash_sale_end).getTime()
      : null,
  );

  $effect(() => {
    if (!flashSaleEnd) {
      timeLeft = { hours: 0, minutes: 0, seconds: 0 };
      return;
    }
    function updateCountdown() {
      const diff = Math.max(0, flashSaleEnd! - Date.now());
      timeLeft = {
        hours: Math.floor(diff / 3600000),
        minutes: Math.floor((diff % 3600000) / 60000),
        seconds: Math.floor((diff % 60000) / 1000)
      };
    }
    updateCountdown();
    const timer = setInterval(updateCountdown, 1000);
    return () => clearInterval(timer);
  });

  // --- VERIFICATION SYSTEM (Elite V2.2) ---
  let isScanning = $state(false);
  let showVerification = $state(false);
  let verificationData = $state<BarcodeVerificationResponse | undefined>(undefined);

  function triggerScan() {
    isScanning = true;
    showVerification = false;
  }

  function handleScanComplete(event: { barcode: string; verificationData?: BarcodeVerificationResponse }) {
    isScanning = false;
    verificationData = event.verificationData;
    showVerification = true;
  }

  // Elite V2.2: Neural Variant Initialization (Sync with Desktop) - pre-paint synchronization
  $effect.pre(() => {
    const _id = product.id; // track product transitions
    if (variations.length > 0) {
      const pVariants = (product.variants || []).filter((v) => v.is_active !== false);
      const defaultV = pVariants.find((v) => v.is_default) || pVariants[0];
      selectedVariant = defaultV || null;
    } else {
      selectedVariant = null;
    }
  });

  // --- VIRAL SHARING ---
  let isViralUnlocked = $state(false);
  $effect(() => {
    const _id = product.id; // track product transitions
    if (typeof window !== "undefined") {
      const userId = authStore.user?.id;
      isViralUnlocked = authStore.isAuthenticated && userId
        ? !!localStorage.getItem(`viral_unlocked_${userId}_${product.id}`)
        : false;
    }
  });

  async function shareProduct() {
    if (navigator.share) {
      try {
        await navigator.share({
          title: product.name,
          url: window.location.href,
        });
      } catch (err) {
        // User cancelled native share or not supported
      }
    } else {
      try {
        await navigator.clipboard.writeText(window.location.href);
        clientUi.showToast("Đã sao chép liên kết!", "success");
      } catch (err) {
        // Clipboard write failed
      }
    }
  }

  let sectionObserver: IntersectionObserver | null = null;

  onMount(() => {
    window.addEventListener("scroll", handleScroll, { passive: true });
    
    const handleOpenVerification = () => triggerScan();
    window.addEventListener("openVerificationCenter", handleOpenVerification);

    // Defer dynamic loading of below-the-fold modules to maximize FCP & LCP PageSpeed metrics
    if (typeof window !== "undefined") {
      if ("requestIdleCallback" in window) {
        requestIdleCallback(() => {
          loadBelowFold = true;
        });
      } else {
        setTimeout(() => {
          loadBelowFold = true;
        }, 200);
      }
    }
    
    // Modern performant IntersectionObserver to eliminate Layout Thrashing (Reflow) on scroll
    const sections = ["overview", "description", "reviews", "recommendations"];
    const observerOptions = {
      root: null,
      rootMargin: "-20% 0px -60% 0px",
      threshold: 0
    };
    
    sectionObserver = new IntersectionObserver((entries) => {
      if (isScrollingToSection) return;
      const intersectingEntry = entries.find(entry => entry.isIntersecting);
      if (intersectingEntry) {
        activeTab = intersectingEntry.target.id;
      }
    }, observerOptions);
    
    sections.forEach(id => {
      const el = document.getElementById(id);
      if (el) sectionObserver?.observe(el);
    });
    
    return () => {
      window.removeEventListener("scroll", handleScroll);
      window.removeEventListener("openVerificationCenter", handleOpenVerification);
      if (sectionObserver) {
        sectionObserver.disconnect();
      }
    };
  });
</script>

<div class="product-mobile-root" class:embedded={isEmbedded} translate="no">
  <!-- 1. STICKY HEADER -->
  {#if !isEmbedded}
    <ProductMobileHeader
      {product}
      {showTabs}
      {scrollRatio}
      {activeTab}
      onScrollToSection={scrollToSection}
      onShare={shareProduct}
    />
  {/if}

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
        {isScrolled}
        isHidden={showTabs}
        {hideRatio}
        onOpenSelector={() => (showVariantSelector = true)}
        onTriggerScan={triggerScan}
        {resolvedLcpUrl}
      />
    </section>

    {#if !isEmbedded}
      <section id="description">
        <ProductMobileSpecs {product} onTriggerScan={triggerScan} />
      </section>

      <section id="reviews">
        {#if loadBelowFold}
          <ProductMobileReviews {product} />
        {:else}
          <div class="h-[250px] bg-white flex flex-col items-center justify-center text-gray-300 gap-2 border-b border-gray-100">
            <div class="w-8 h-8 rounded-full border-2 border-gray-100 animate-spin" style="border-top-color: var(--color-luxury-copper, #C18F7E);"></div>
            <span class="text-[10px] font-black tracking-widest uppercase">Đang tải đánh giá...</span>
          </div>
        {/if}
      </section>

      <section id="recommendations">
        {#if loadBelowFold}
          <ProductMobileRecommendations {relatedProducts} />
        {:else}
          <div class="h-[250px] bg-white flex flex-col items-center justify-center text-gray-300 gap-2">
            <div class="w-8 h-8 rounded-full border-2 border-gray-100 animate-spin" style="border-top-color: var(--color-luxury-copper, #C18F7E);"></div>
            <span class="text-[10px] font-black tracking-widest uppercase">Đang tải gợi ý...</span>
          </div>
        {/if}
      </section>
    {/if}
  </div>

  <!-- 3. FOOTER NAV -->
  <MobileBottomNav
    isProductMode={true}
    {product}
    {selectedVariant}
    scrolled={isShrunk}
    onAddToCart={addToCart}
    onBuyNow={buyNow}
    onChatOpen={() => supportAgent.open()}
  />

  <!-- 4. VARIANT SELECTOR -->
  {#if showVariantSelector}
    <ProductMobileVariantSelector
      {product}
      show={showVariantSelector}
      onClose={() => (showVariantSelector = false)}
      onConfirm={handleVariantConfirm}
    />
  {/if}

  <!-- 5. VERIFICATION OVERLAYS -->
  {#if isScanning}
    <ScannerHUD
      barcode={String(product.metadata?.barcode || product.sku || "")}
      oncomplete={handleScanComplete}
    />
  {/if}

  <BottomSheet bind:active={showVerification} title="Verified">
    <div class="py-2">
      <MobileVerificationCenter {product} {verificationData} />
    </div>
  </BottomSheet>



  {#if !isEmbedded}
    <div class="h-20"></div>
  {/if}
</div>

<style>
  .product-mobile-root {
    background: #f5f5f5;
    min-height: 100dvh;
    width: 100%;
    position: relative;
  }

  .product-mobile-root.embedded {
    min-height: auto !important;
    background: transparent !important;
  }

  .content-body {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }



  .h-20 {
    height: 80px;
  }



  :global(.prose-osmo figure) {
    margin: 1rem 0 !important;
    display: block !important;
    text-align: center !important;
  }

  :global(.prose-osmo figure img) {
    margin-top: 0 !important;
    margin-bottom: 0.25rem !important;
  }

  :global(.prose-osmo figcaption) {
    text-align: center !important;
    display: block !important;
    margin-top: 0.25rem !important;
    font-size: 12px !important;
    color: #6b7280 !important;
    font-style: italic !important;
    line-height: 1.4 !important;
  }

  /* Khử margin và tránh block-break gây vỡ hàng cho p trong li */
  :global(.prose-osmo li p) {
    display: inline !important;
    margin-bottom: 0 !important;
  }
</style>
