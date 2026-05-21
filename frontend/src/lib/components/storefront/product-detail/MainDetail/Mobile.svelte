<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";

  // Types
  import type { Product, ProductVariant, ReviewStats, BarcodeVerificationResponse } from "$lib/types";

  // Stores
  import { getCartStore } from "$lib/state/commerce/cart.svelte";
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import { supportAgent } from "$lib/state/commerce/supportAgent.svelte";

  // Components
  import ProductMobileHeader from "./modules/ProductMobileHeader.svelte";
  import ProductMobileOverview from "./modules/ProductMobileOverview.svelte";
  import ProductMobileSpecs from "./modules/ProductMobileSpecs.svelte";
  import ProductMobileReviews from "./modules/ProductMobileReviews.svelte";
  import ProductMobileRecommendations from "./modules/ProductMobileRecommendations.svelte";
  import ProductMobileVariantSelector from "./modules/ProductMobileVariantSelector.svelte";
  import MobileBottomNav from "$lib/components/storefront/home/MobileBottomNav.svelte";
  import BottomSheet from "$lib/components/mobile/BottomSheet.svelte";
  import ScannerHUD from "../shared/ScannerHUD.svelte";
  import MobileVerificationCenter from "../shared/MobileVerificationCenter.svelte";


  interface Props {
    product: Product;
    relatedProducts?: Product[];
    reviewStats?: ReviewStats | null;
  }

  let { product, relatedProducts = [], reviewStats = null }: Props = $props();

  const cartStore = getCartStore();
  const clientUi = getClientUi();

  // --- TAB & SCROLL STATE ---
  let activeTab = $state("overview");
  let showTabs = $state(false);
  let isScrolled = $state(false);
  let isShrunk = $state(false);
  let lastScrollY = 0;
  let scrollRatio = $state(0);
  let hideRatio = $state(0);

  function handleScroll() {
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
  }

  function scrollToSection(id: string) {
    const el = document.getElementById(id);
    if (el) {
      window.scrollTo({
        top: el.offsetTop - 80,
        behavior: "smooth",
      });
    }
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

  // Elite V2.2: Neural Variant Initialization (Sync with Desktop)
  $effect(() => {
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
  let viralStep = $state<
    "idle" | "sharing" | "awaiting_confirm" | "verifying" | "revealed"
  >("idle");
  let isViralUnlocked = $state(false);
  $effect(() => {
    const _id = product.id; // track product transitions
    if (typeof window !== "undefined") {
      isViralUnlocked = !!localStorage.getItem(`viral_unlocked_${product.id}`);
    }
  });
  const displayRewardLabel = $derived(
    product.metadata?.share_promotion?.voucher_label ||
      product.metadata?.share_reward_label ||
      "Phần quà bí mật",
  );

  async function shareProduct() {
    const sharePromotion = product.metadata?.share_promotion;
    const isViralEnabled =
      sharePromotion?.enabled === true || !!sharePromotion?.voucher_id;

    if (isViralEnabled && !isViralUnlocked) {
      viralStep = "sharing";
      try {
        const res = await fetch("/api/v1/client/viral/share-intent", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ product_id: product.id }),
        });
        if (!res.ok) throw new Error("Yêu cầu thất bại");
        const data = await res.json();

        sessionStorage.setItem(
          `viral_intent_${product.id}`,
          JSON.stringify({
            token: data.token,
            fingerprint: data.fingerprint,
            timestamp: Date.now(),
          }),
        );

        // Trigger native share or clipboard
        if (navigator.share) {
          await navigator.share({
            title: product.name,
            url: window.location.href,
          });
        } else {
          await navigator.clipboard.writeText(window.location.href);
          clientUi.showToast("Đã sao chép liên kết!", "success");
        }
        viralStep = "awaiting_confirm";
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Lỗi khởi tạo chia sẻ";
        clientUi.showToast(msg, "error");
        viralStep = "idle";
      }
      return;
    }

    if (navigator.share) {
      navigator.share({ title: product.name, url: window.location.href });
    } else {
      navigator.clipboard.writeText(window.location.href);
      clientUi.showToast("Đã sao chép liên kết!", "success");
    }
  }

  async function verifyShare() {
    const savedIntent = sessionStorage.getItem(`viral_intent_${product.id}`);
    if (!savedIntent) {
      viralStep = "idle";
      return;
    }

    try {
      const { token, fingerprint } = JSON.parse(savedIntent);
      const sharePromotion = product.metadata?.share_promotion;
      const voucherId = sharePromotion?.voucher_id;

      viralStep = "verifying";
      const res = await fetch("/api/v1/client/viral/verify-share", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_id: product.id,
          fingerprint,
          token,
          voucher_id: voucherId,
        }),
      });
      if (!res.ok) throw new Error("Xác minh thất bại");
      const data = await res.json();

      isViralUnlocked = true;
      viralStep = "revealed";
      localStorage.setItem(
        `viral_unlocked_${product.id}`,
        JSON.stringify({
          code: data.voucher_code,
          label: data.voucher_label,
          unlocked_at: Date.now(),
        }),
      );
      clientUi.showToast("🎉 Đã mở khóa quà tặng!", "success");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Xác minh thất bại";
      clientUi.showToast(msg, "error");
      viralStep = "idle";
    }
  }

  let sectionObserver: IntersectionObserver | null = null;

  onMount(() => {
    window.addEventListener("scroll", handleScroll, { passive: true });
    
    const handleOpenVerification = () => triggerScan();
    window.addEventListener("openVerificationCenter", handleOpenVerification);
    
    // Modern performant IntersectionObserver to eliminate Layout Thrashing (Reflow) on scroll
    const sections = ["overview", "description", "reviews", "recommendations"];
    const observerOptions = {
      root: null,
      rootMargin: "-20% 0px -60% 0px",
      threshold: 0
    };
    
    sectionObserver = new IntersectionObserver((entries) => {
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

<div class="product-mobile-root" translate="no">
  <!-- 1. STICKY HEADER -->
  <ProductMobileHeader
    {product}
    {showTabs}
    {scrollRatio}
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
        {isScrolled}
        isHidden={showTabs}
        {hideRatio}
        onOpenSelector={() => (showVariantSelector = true)}
        onTriggerScan={triggerScan}
      />
    </section>

    <div class="section-divider"></div>

    <section id="description">
      <ProductMobileSpecs {product} onTriggerScan={triggerScan} />
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
    {selectedVariant}
    scrolled={isShrunk}
    onAddToCart={addToCart}
    onBuyNow={buyNow}
    onChatOpen={() => supportAgent.open()}
  />

  <!-- 4. VARIANT SELECTOR -->
  <ProductMobileVariantSelector
    {product}
    show={showVariantSelector}
    onClose={() => (showVariantSelector = false)}
    onConfirm={handleVariantConfirm}
  />

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

  <!-- 6. VIRAL OVERLAY -->
  {#if viralStep === "awaiting_confirm"}
    <div class="global-viral-overlay">
      <div class="global-confirm-card">
        <span class="confirm-title">Đã chia sẻ thành công?</span>
        <p class="confirm-sub">
          Xác nhận để mở khóa <span class="reward-label"
            >{displayRewardLabel}</span
          >
        </p>
        <div class="confirm-btns">
          <button class="btn-cancel" onclick={() => (viralStep = "idle")}
            >Hủy</button
          >
          <button class="btn-verify" onclick={verifyShare}>Xác nhận ngay</button
          >
        </div>
      </div>
    </div>
  {/if}

  <div class="h-20"></div>
</div>

<style>
  .product-mobile-root {
    background: #f5f5f5;
    min-height: 100dvh;
    width: 100%;
    position: relative;
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
    background: rgba(0, 0, 0, 0.7);
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
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(238, 77, 45, 0.2);
  }

  .confirm-title {
    font-size: 18px;
    font-weight: 1000;
    color: #000;
    margin-bottom: 8px;
  }
  .confirm-sub {
    font-size: 13px;
    color: #666;
    margin-bottom: 24px;
  }
  .reward-label {
    display: inline-block !important;
    text-transform: lowercase !important;
  }
  .reward-label::first-letter {
    text-transform: uppercase !important;
  }
  .confirm-btns {
    display: flex;
    gap: 12px;
    width: 100%;
  }

  .btn-cancel {
    flex: 1;
    height: 44px;
    border-radius: 8px;
    background: #f5f5f5;
    color: #666;
    border: none;
    font-weight: 800;
    font-size: 13px;
    cursor: pointer;
  }
  .btn-verify {
    flex: 1;
    height: 44px;
    border-radius: 8px;
    background: #ee4d2d;
    color: white;
    border: none;
    font-weight: 1000;
    font-size: 13px;
    box-shadow: 0 4px 12px rgba(238, 77, 45, 0.3);
    cursor: pointer;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
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
