<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import type { Product, ProductVariant, ReviewStats, BarcodeVerificationResponse } from "$lib/types";
  import { getCartStore } from "$lib/state/commerce/cart.svelte";
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import { supportAgent } from "$lib/state/commerce/supportAgent.svelte";
  import { formatCurrency } from "$lib/utils/format";
  import Diamond from "@lucide/svelte/icons/diamond";

  // Modules
  import { SHOP_CONFIG } from "$lib/constants/shop";
  import ProductGallery from "./modules/Gallery.svelte";
  import ProductPrimaryInfo from "./modules/Info.svelte";
  import ProductDetailSections from "./modules/Specs.svelte";
  import ProductDescription from "./modules/Description.svelte";

  // Below-fold sections: lazy-loaded via {#await} to reduce initial bundle
  // Lazy-load heavy modal components (reduce initial bundle ~200KB)
  import type { Component } from "svelte";
  let ScannerHUDComponent = $state<Component<Record<string, unknown>> | null>(null);
  let VerificationCenterComponent = $state<Component<Record<string, unknown>> | null>(null);
  async function loadScannerHUD() {
    if (!ScannerHUDComponent) {
      const mod = await import("../shared/ScannerHUD.svelte");
      ScannerHUDComponent = mod.default as Component<Record<string, unknown>>;
    }
  }
  async function loadVerificationCenter() {
    if (!VerificationCenterComponent) {
      const mod = await import("../shared/VerificationCenter.svelte");
      VerificationCenterComponent = mod.default as Component<Record<string, unknown>>;
    }
  }

  let ProductReviewsComponent = $state<Component<Record<string, unknown>> | null>(null);
  let RelatedProductsComponent = $state<Component<Record<string, unknown>> | null>(null);
  let loadBelowFold = $state(false);

  onMount(() => {
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
  });

  $effect(() => {
    if (loadBelowFold) {
      import("../../shared/ProductReviews.svelte").then((mod) => {
        ProductReviewsComponent = mod.default as Component<Record<string, unknown>>;
      });
      import("../shared/RelatedProducts.svelte").then((mod) => {
        RelatedProductsComponent = mod.default as Component<Record<string, unknown>>;
      });
    }
  });
  import X from "@lucide/svelte/icons/x";
  import { portal } from "$lib/core/actions/portal";
  import { Z_INDEX_CLIENT } from "$lib/core/constants/zIndex";
  import { fade, scale } from "svelte/transition";

  const cartStore = getCartStore();
  const clientUi = getClientUi();

  interface Props {
    product: Product;
    relatedProducts?: Product[];
    reviewStats?: ReviewStats | null;
  }
  let { product, relatedProducts = [], reviewStats = null }: Props = $props();

  interface ExtendedProductMetadata {
    share_promotion?: {
      voucher_id?: string;
      likes_count?: number;
    };
    viral_suite?: {
      likes_count?: number;
    };
    vouchers?: { id: string; label: string; sub: string; type: "ship" | "discount" }[];
    flash_sale_end?: string;
    brand?: string;
    origin?: string;
    weight?: string;
  }

  interface RawTierVariation {
    name?: string;
    options?: (string | { name?: string; label?: string })[];
    images?: (string | null)[];
  }

  interface VoucherUI {
    id: string;
    label: string;
    sub: string;
    type: "ship" | "discount";
  }

  // Elite Performance Sync (V2.2)
  const metadata = $derived((product.metadata || {}) as ExtendedProductMetadata);

  // Elite Performance Fix: Derived from server-prefetched and reactive data
  const stats = $derived<ReviewStats | null>(reviewStats);
  const likeCount = $derived(
    Number(
      metadata.viral_suite?.likes_count ||
        product.metadata?.likes ||
        0,
    )
  );

  // Verification System (Elite V2.2)
  let isScanning = $state(false);
  let showVerification = $state(false);
  let verificationData = $state<BarcodeVerificationResponse | undefined>(undefined);

  async function triggerScan() {
    await loadScannerHUD();
    isScanning = true;
    showVerification = false;
  }

  async function handleScanComplete(data: { barcode: string; verificationData?: BarcodeVerificationResponse }) {
    isScanning = false;
    if (data.verificationData) {
      verificationData = data.verificationData;
      await loadVerificationCenter();
      showVerification = true;
    }
  }

  const variations = $derived(
    ((product.tier_variations || product.tierVariations || []) as RawTierVariation[]).map(v => ({
      name: v.name || "",
      options: (v.options || []).map((o) => typeof o === "string" ? o : String(o?.name || o?.label || "")),
      images: (v.images || []).filter((img): img is string => img !== null)
    }))
  );
  let selectedIndices = $state<number[]>([]);

  $effect(() => {
    if (selectedIndices.length === 0 && variations.length > 0) {
      const defaultVariant = pVariants.find((v) => v.is_default);
      const dIndices = defaultVariant?.tierIndex || defaultVariant?.tier_index;
      if (dIndices) {
        selectedIndices = [...dIndices];
      } else {
        selectedIndices = variations.map(() => 0);
      }
    }
  });
  let quantity = $state(1);

  const pVariants = $derived(product.variants || []);
  let currentVariant = $derived<ProductVariant | undefined>(
    pVariants.find((v) => {
      const vIndices = v.tierIndex || v.tier_index;
      if (!vIndices) return false;
      return (
        vIndices.length === selectedIndices.length &&
        vIndices.every((val, i) => val === selectedIndices[i])
      );
    }),
  );

  const effectiveTier = $derived.by(() => {
    const comboVariants = pVariants.filter(
      (cv) => cv.attributes && cv.attributes.combo_qty,
    );
    if (comboVariants.length === 0) return currentVariant;
    const sortedTiers = [...comboVariants].sort(
      (a, b) => Number(b.attributes?.combo_qty || 0) - Number(a.attributes?.combo_qty || 0),
    );
    return (
      sortedTiers.find((t) => Number(t.attributes?.combo_qty || 0) <= quantity) ||
      currentVariant
    );
  });

  const effectiveUnitPrice = $derived.by(() => {
    const v = effectiveTier;
    if (!v)
      return typeof product.discountPrice === "number"
        ? product.discountPrice
        : product.discount_price || product.price || 0;
    return v.discountPrice || v.discount_price || v.price;
  });

  let displayPrice = $derived.by(() => {
    if (currentVariant) {
      return {
        price: currentVariant.price,
        discountPrice: effectiveUnitPrice,
      };
    }
    if (pVariants.length > 0) {
      const prices = pVariants
        .map((v) => Number(v.price))
        .filter((p) => !isNaN(p));
      const discountPrices = pVariants
        .map((v) => v.discountPrice || v.discount_price)
        .filter((p) => p != null && !isNaN(Number(p)))
        .map((p) => Number(p));

      const minPrice = prices.length > 0 ? Math.min(...prices) : 0;
      const maxPrice = prices.length > 0 ? Math.max(...prices) : 0;

      const minDiscount =
        discountPrices.length > 0 ? Math.min(...discountPrices) : undefined;
      const maxDiscount =
        discountPrices.length > 0 ? Math.max(...discountPrices) : undefined;

      const formatRange = (min: number, max: number) =>
        min === max
          ? min.toLocaleString("vi-VN")
          : `${min.toLocaleString("vi-VN")} - ${max.toLocaleString("vi-VN")}`;

      return {
        price: formatRange(minPrice, maxPrice),
        discountPrice: (minDiscount !== undefined && maxDiscount !== undefined)
          ? formatRange(minDiscount, maxDiscount)
          : undefined,
      };
    }
    return {
      price: product.price,
      discountPrice: product.discountPrice || product.discount_price,
    };
  });

  let currentStock = $derived(
    currentVariant ? currentVariant.stock : product.stock,
  );

  function selectOption(tierIndex: number, optionIndex: number) {
    const newSelected = [...selectedIndices];
    if (newSelected[tierIndex] === optionIndex) {
      newSelected[tierIndex] = -1;
    } else {
      newSelected[tierIndex] = optionIndex;
    }
    selectedIndices = newSelected;

    const nextVariant = pVariants.find((v) => {
      const vIndices = v.tierIndex || v.tier_index;
      if (!vIndices) return false;
      return (
        vIndices.length === selectedIndices.length &&
        vIndices.every((val, i) => val === selectedIndices[i])
      );
    });
    if (nextVariant?.attributes?.combo_qty) {
      quantity = Number(nextVariant.attributes.combo_qty);
    } else if (quantity > currentStock) {
      quantity = currentStock > 0 ? 1 : 0;
    }
  }

  function validateSelection(): boolean {
    if (variations.length > 0 && selectedIndices.includes(-1)) {
      clientUi.showToast("Vui lòng chọn phân loại hàng", "error");
      return false;
    }
    if (quantity < 1 || quantity > currentStock) {
      clientUi.showToast("Số lượng không hợp lệ", "error");
      return false;
    }
    return true;
  }

  function handleQuantityChange(delta: number) {
    const newVal = quantity + delta;
    const maxStock = currentStock || 99;
    if (newVal >= 1 && newVal <= maxStock) {
      quantity = newVal;
      const matchingVariant = pVariants.find(
        (v) => Number(v.attributes?.combo_qty || 0) === quantity,
      );
      const mIndices = matchingVariant?.tierIndex || matchingVariant?.tier_index;
      if (mIndices) {
        selectedIndices = [...mIndices];
      }
    }
  }

  function addToCart() {
    if (!validateSelection()) return;
    cartStore.addItem(product, currentVariant, quantity);
    clientUi.showToast("Đã thêm sản phẩm vào giỏ hàng", "success");
  }

  const flashSaleEnd = $derived(
    metadata.flash_sale_end
      ? new Date(metadata.flash_sale_end).getTime()
      : null,
  );
  const isFlashSaleActive = $derived(
    flashSaleEnd !== null && flashSaleEnd > Date.now(),
  );
  let timeLeft = $state({ hours: 0, minutes: 0, seconds: 0 });

  let isViralUnlocked = $state(false);
  $effect(() => {
    if (typeof window !== "undefined") {
      isViralUnlocked = !!localStorage.getItem(`viral_unlocked_${product.id}`);
    }
  });

  let selectedVouchers = $state<string[]>([]);
  const productVouchers = $derived.by(() => {
    let vouchers: { id: string; label: string; sub: string; type: "ship" | "discount"; value?: number }[] = [];
    if (
      Array.isArray(metadata.vouchers) &&
      metadata.vouchers.length > 0
    ) {
      vouchers = metadata.vouchers as { id: string; label: string; sub: string; type: "ship" | "discount"; value?: number }[];
    } else {
      vouchers = cartStore.vouchers
        .filter((v) => {
          const applicableIds = v.metadata_json?.applicable_product_ids || [];
          if (applicableIds && applicableIds.length > 0) {
            return applicableIds.includes(product.id);
          }
          return true;
        })
        .map((v) => ({
          id: v.id,
          label: v.title || v.id,
          sub:
            v.subtitle ||
            (v.type === "SHIPPING"
              ? "Miễn phí vận chuyển"
              : v.type === "PERCENT"
                ? `Giảm ${v.value}%`
                : `Giảm ${formatCurrency(v.value)}`),
          type: v.type === "SHIPPING" ? ("ship" as const) : ("discount" as const),
          value: v.value || 0,
        }));
    }

    const cleanString = (s: string) => {
      return (s || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toUpperCase();
    };

    const isViralVoucher = (v: { id: string; label?: string }) => {
      const cleanId = cleanString(v.id);
      const cleanLabel = cleanString(v.label || '');
      return cleanId.includes('VIRAL') || 
             cleanId.includes('LAN TOA') || 
             cleanLabel.includes('VIRAL') || 
             cleanLabel.includes('LAN TOA');
    };

    let vList = vouchers.filter((v: { id: string; label?: string }) => {
      return !isViralVoucher(v) || isViralUnlocked;
    });

    // Elite V2.2 Re-injection: Phục hồi voucher từ session local nếu đã mở khóa
    if (typeof window !== 'undefined' && isViralUnlocked) {
      const saved = localStorage.getItem(`viral_unlocked_${product.id}`);
      if (saved) {
        try {
          const data = JSON.parse(saved);
          // Filter out existing viral vouchers to prevent duplicates or wrong positions
          vList = vList.filter(v => !isViralVoucher(v) && v.id !== data.code);
          // Prepend at the absolute top (Position #1)
          vList.unshift({
            id: data.code,
            label: data.label || 'Voucher lan tỏa',
            sub: 'Đã mở khóa từ chiến dịch',
            type: 'discount' as "ship" | "discount",
            value: data.value || 79000
          });
        } catch (e) { console.warn('[Desktop] Viral voucher parse error — localStorage key may be corrupted:', e); }
      }
    }

    const getVoucherValue = (v: any) => {
      let rawVal = typeof v.value === 'number' ? v.value : 0;
      const subText = String(v.sub || "").toLowerCase();
      const labelText = String(v.label || "").toLowerCase();

      const productPrice = effectiveUnitPrice || product.price || 0;

      if (rawVal === 0) {
        const found = cartStore.vouchers.find(x => x.id === v.id);
        if (found) {
          rawVal = found.value || 0;
          if (found.type === 'PERCENT') {
            return (productPrice * rawVal) / 100;
          }
        }
      }

      if (subText.includes("%") || labelText.includes("%")) {
        const parsedPercent = parseInt((v.sub || v.label || "").replace(/[^0-9]/g, ""), 10);
        if (!isNaN(parsedPercent)) {
          return (productPrice * parsedPercent) / 100;
        }
      }

      if (rawVal > 0) {
        if (rawVal <= 100 && (v.type === 'percent' || String(v.id).toLowerCase().includes('pct') || subText.includes('%'))) {
          return (productPrice * rawVal) / 100;
        }
        return rawVal;
      }

      const parsed = parseInt(subText.replace(/[^0-9]/g, ''), 10);
      return isNaN(parsed) ? 0 : parsed;
    };

    // Sort by value descending (Giá giảm dần)
    const sorted = [...vList].sort((a, b) => {
      const valA = getVoucherValue(a);
      const valB = getVoucherValue(b);
      return valB - valA;
    });

    // Grouping by type:
    // 1. Viral/Độc quyền always at the absolute top
    const viralVouchers = sorted.filter(v => isViralVoucher(v));
    // 2. Regular discount vouchers
    const regularDiscount = sorted.filter(v => !isViralVoucher(v) && v.type === 'discount');
    // 3. Regular shipping vouchers
    const regularShipping = sorted.filter(v => !isViralVoucher(v) && v.type === 'ship');

    return [...viralVouchers, ...regularDiscount, ...regularShipping] as VoucherUI[];
  });

  function triggerViralFly() {
    isViralUnlocked = true;
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(`viral_unlocked_${product.id}`);
      if (saved) {
        try {
          const data = JSON.parse(saved);
          if (data.code && !selectedVouchers.includes(data.code)) {
            toggleVoucher(data.code);
          }
        } catch (e) {
          console.error('Failed to parse saved viral voucher', e);
        }
      }
    }
  }

  function toggleVoucher(id: string) {
    const voucher = productVouchers.find((v) => v.id === id);
    if (!voucher) return;
    if (selectedVouchers.includes(id)) {
      selectedVouchers = selectedVouchers.filter((v) => v !== id);
    } else {
      const groupIds = productVouchers
        .filter((v) => v.type === voucher.type)
        .map((v) => v.id);
      selectedVouchers = [
        ...selectedVouchers.filter((v) => !groupIds.includes(v)),
        id,
      ];
    }
  }

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

  const pDiscountPrice = $derived(
    product.discountPrice || product.discount_price,
  );
  const productInfo = $derived({
    barcode: (product.sku as string) || "N/A",
    brand:
      metadata.brand ||
      (product.attributes?.brand as string) ||
      (product.attributes?.["Thương hiệu"] as string) ||
      "",
    origin:
      metadata.origin ||
      (product.attributes?.origin as string) ||
      (product.attributes?.["Xuất xứ"] as string) ||
      "",
    weight:
      metadata.weight ||
      (product.attributes?.weight as string) ||
      (product.attributes?.["Trọng lượng"] as string) ||
      "",
    originalPrice: product.price || 0,
    salePrice: (pDiscountPrice as number) || (product.price as number) || 0,
  });

  const activePrices = $derived({
    sale: displayPrice.discountPrice || displayPrice.price,
    original: displayPrice.price,
  });

  function buyNow() {
    if (!validateSelection()) return;
    cartStore.buyNow(product, currentVariant, quantity);
    goto("/checkout");
  }

  function triggerWriteReview() {
    const el = document.getElementById("product-reviews");
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
      setTimeout(() => {
        const btn = document.getElementById("btn-write-review");
        if (btn) btn.click();
      }, 600);
    }
  }

  function handleViewFullIngredients() {
    const el = document.getElementById("product-description") || document.querySelector(".description-container");
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  }

  const helenAdvice = $derived(cartStore.getPromotionAdvice(product, quantity).text);

  const activeComboQty = $derived(
    effectiveTier?.attributes?.combo_qty ||
      effectiveTier?.attributes?.comboQty ||
      0,
  );
  const activeGifts = $derived(effectiveTier?.attributes?.gifts || []);
</script>

<div class="min-h-screen" style="background: linear-gradient(135deg, #f0fdf4 0%, #fff7ed 100%);">
  <!-- BREADCRUMB -->
  <div class="py-4" style="background: rgba(255, 255, 255, 0.4); backdrop-filter: blur(10px); border-bottom: 1px solid rgba(13, 148, 136, 0.05);">
    <div
      class="max-w-[1200px] mx-auto px-4 xl:px-0 flex items-center gap-3 text-[11px] text-gray-500 font-bold tracking-wider"
    >
      <a
        href="/"
        class="flex items-center gap-2 bg-gradient-to-r from-[#0d9488] to-[#0f766e] text-white px-3 py-1 rounded-[4px] hover:brightness-110 transition-all shadow-sm"
      >
        <Diamond size={10} fill="currentColor" />
        <span class="text-[9px] font-black tracking-[0.25em]">OSMO</span>
      </a>
      <span class="opacity-25 text-[#0d9488]">/</span>
      <span class="text-gray-600 normal-case tracking-normal font-semibold"
        >{product.name}</span
      >
    </div>
  </div>

  <main class="max-w-[1200px] mx-auto mt-6 p-6" style="background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.8); box-shadow: 0 20px 60px rgba(15, 23, 42, 0.04); border-radius: 12px;">
    <div class="flex flex-col md:flex-row gap-8">
      <div class="relative w-full md:w-[450px] shrink-0">
        <button
          onclick={triggerScan}
          class="absolute top-2 right-2 z-20 w-14 h-14 cursor-pointer hover:scale-105 transition-transform drop-shadow-md bg-transparent border-none p-0 focus:outline-none"
        >
          <img
            src={(product?.metadata?.verified_badge_url as string) ||
              SHOP_CONFIG.default_badge_url}
            alt="Verified"
            class="w-full h-full object-contain drop-shadow-[0_4px_10px_rgba(0,0,0,0.1)]"
          />
        </button>
        <ProductGallery
          {product}
          {likeCount}
          {isFlashSaleActive}
          {productInfo}
          {selectedIndices}
          {variations}
        />
      </div>

      <ProductPrimaryInfo
        {product}
        {stats}
        {activePrices}
        {helenAdvice}
        {productVouchers}
        {selectedVouchers}
        {variations}
        {selectedIndices}
        {quantity}
        {currentStock}
        {activeComboQty}
        {activeGifts}
        {isFlashSaleActive}
        {timeLeft}
        onToggleVoucher={toggleVoucher}
        onSelectOption={selectOption}
        onQuantityChange={handleQuantityChange}
        onAddToCart={addToCart}
        onBuyNow={buyNow}
        onWriteReview={triggerWriteReview}
        onViralUnlock={triggerViralFly}
        onTriggerVerify={triggerScan}
      />
    </div>

    <ProductDetailSections
      {product}
      {productInfo}
      onViewFullIngredients={handleViewFullIngredients}
      onTriggerScan={triggerScan}
      visibleAttributes={product.attributes
        ? (Object.entries(product.attributes).filter(([key, value]) => {
            const k = key.toLowerCase().replace(/_/g, " ").trim();
            return !(
              k === "xuất xứ" ||
              k === "origin" ||
              k === "trọng lượng" ||
              k === "quy cách" ||
              k === "weight" ||
              k === "mã vạch" ||
              k === "barcode" ||
              k === "thương hiệu" ||
              k === "brand"
            );
          }) as [string, string | number | boolean | null][])
        : []}
    />

    <ProductDescription {product} />

    <div id="product-reviews" class="max-w-[1200px] mx-auto mt-6">
      {#if loadBelowFold && ProductReviewsComponent}
        <ProductReviewsComponent {product} />
      {:else}
        <div class="h-[250px] bg-white rounded-lg flex flex-col items-center justify-center text-gray-300 gap-2 border border-gray-100 animate-pulse">
          <div class="w-8 h-8 rounded-full border-2 border-gray-100 animate-spin" style="border-top-color: var(--color-luxury-copper, #C18F7E);"></div>
          <span class="text-[10px] font-black tracking-widest uppercase">Đang tải đánh giá chuyên sâu...</span>
        </div>
      {/if}
    </div>

    <div class="max-w-[1200px] mx-auto mt-6 mb-12">
      {#if loadBelowFold && RelatedProductsComponent}
        <RelatedProductsComponent {product} initialProducts={relatedProducts} />
      {:else}
        <div class="h-[300px] bg-white rounded-lg flex flex-col items-center justify-center text-gray-300 gap-2 border border-gray-100 animate-pulse">
          <div class="w-8 h-8 rounded-full border-2 border-gray-100 animate-spin" style="border-top-color: var(--color-luxury-copper, #C18F7E);"></div>
          <span class="text-[10px] font-black tracking-widest uppercase">Đang gợi ý sản phẩm liên quan...</span>
        </div>
      {/if}
    </div>
  </main>

  {#if isScanning && ScannerHUDComponent}
    <svelte:component this={ScannerHUDComponent} barcode={productInfo.barcode} oncomplete={handleScanComplete} />
  {/if}

  {#if showVerification}
    <div
      use:portal
      transition:fade={{ duration: 200 }}
      class="fixed inset-0 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xl"
      style:z-index={Z_INDEX_CLIENT.MODAL + 100}
      onclick={() => (showVerification = false)}
    >
      <div
        transition:scale={{ duration: 300, start: 0.95 }}
        class="bg-[#0a0a0a]/90 backdrop-blur-3xl w-full max-w-5xl p-0 shadow-[0_20px_100px_rgba(0,0,0,1)] border border-white/10 rounded-[5px] overflow-hidden relative"
        onclick={(e) => e.stopPropagation()}
      >
        <button
          class="absolute top-0 right-0 text-white/40 hover:text-white z-20 transition-all w-8 h-8 flex items-center justify-center hover:bg-white/10 rounded-bl-[5px]"
          onclick={() => (showVerification = false)}
        >
          <X size={18} />
        </button>

        <div
          class="relative z-10 pt-10 px-10 pb-2 max-h-[90vh] overflow-y-auto custom-scrollbar"
        >
          {#if VerificationCenterComponent}
            <svelte:component this={VerificationCenterComponent} {product} {verificationData} />
          {/if}
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  /* Performance: CSS Containment to prevent layout thrashing */
  :global(#product-reviews),
  :global(.description-container) {
    contain: layout style;
  }

  :global(.prose-osmo) {
    font-family: inherit !important;
    font-size: 15px !important; /* Sleek e-commerce standard (Lazada/Shopee) */
    line-height: 1.6 !important;
    color: #374151 !important;
  }
  :global(.prose-osmo p) {
    margin-bottom: 1rem !important;
    font-weight: 400 !important;
    letter-spacing: -0.011em !important;
  }
  :global(.prose-osmo h2, .prose-osmo h3) {
    color: #6b7280 !important;
    font-weight: 800 !important;
    margin-top: 2rem !important;
    margin-bottom: 1rem !important;
    text-transform: lowercase !important;
  }

  :global(.prose-osmo h2::first-letter, .prose-osmo h3::first-letter) {
    text-transform: uppercase !important;
  }
  :global(.prose-osmo img) {
    width: 100% !important;
    height: auto !important;
    margin: 1rem auto !important;
    display: block;
  }

</style>
