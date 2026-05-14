<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import type { Product, ProductVariant, ReviewStats } from "$lib/types";
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
  import ProductReviews from "../../shared/ProductReviews.svelte";

  import RelatedProducts from "../shared/RelatedProducts.svelte";
  import ScannerHUD from "../shared/ScannerHUD.svelte";
  import VerificationCenter from "../shared/VerificationCenter.svelte";
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

  // Elite Performance Fix P1.2: Khởi tạo từ server-prefetched data
  let stats = $state<ReviewStats | null>(reviewStats);
  let likeCount = $state(0);

  // Sync stats khi server data thay đổi
  $effect(() => {
    if (reviewStats !== undefined) {
      stats = reviewStats;
    }
  });

  // Sync like state with product (Elite V2.2)
  $effect(() => {
    if (product) {
      likeCount = Number(
        product.metadata?.viral_suite?.likes_count ||
          product.metadata?.likes ||
          0,
      );
    }
  });

  // Verification System (Elite V2.2)
  let isScanning = $state(false);
  let showVerification = $state(false);
  let verificationData = $state(null);

  function triggerScan() {
    isScanning = true;
    showVerification = false;
  }

  function handleScanComplete(event: any) {
    isScanning = false;
    verificationData = event.verificationData;
    showVerification = true;
  }

  const variations = $derived(
    product.tier_variations || product.tierVariations || [],
  );
  let selectedIndices = $state<number[]>([]);

  $effect(() => {
    if (selectedIndices.length === 0 && variations.length > 0) {
      const defaultVariant = pVariants.find((v) => v.is_default);
      if (defaultVariant && defaultVariant.tierIndex) {
        selectedIndices = [...defaultVariant.tierIndex];
      } else {
        selectedIndices = variations.map(() => 0);
      }
    }
  });
  let quantity = $state(1);

  const pVariants = $derived(product.variants || []);
  let currentVariant = $derived<ProductVariant | undefined>(
    pVariants.find(
      (v) =>
        v.tierIndex.length === selectedIndices.length &&
        v.tierIndex.every((val, i) => val === selectedIndices[i]),
    ),
  );

  const effectiveTier = $derived.by(() => {
    const comboVariants = pVariants.filter(
      (cv) => cv.attributes && cv.attributes.combo_qty,
    );
    if (comboVariants.length === 0) return currentVariant;
    const sortedTiers = [...comboVariants].sort(
      (a, b) => Number(b.attributes.combo_qty) - Number(a.attributes.combo_qty),
    );
    return (
      sortedTiers.find((t) => Number(t.attributes.combo_qty) <= quantity) ||
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
        discountPrice: minDiscount
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

    const nextVariant = pVariants.find(
      (v) =>
        v.tierIndex.length === selectedIndices.length &&
        v.tierIndex.every((val, i) => val === selectedIndices[i]),
    );
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
      if (matchingVariant && matchingVariant.tierIndex) {
        selectedIndices = [...matchingVariant.tierIndex];
      }
    }
  }

  function addToCart() {
    if (!validateSelection()) return;
    cartStore.addItem(product, currentVariant, quantity);
    clientUi.showToast("Đã thêm sản phẩm vào giỏ hàng", "success");
  }

  const flashSaleEnd = $derived(
    product.metadata?.flash_sale_end
      ? new Date(product.metadata.flash_sale_end).getTime()
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
    let vouchers = [];
    if (
      Array.isArray(product.metadata?.vouchers) &&
      product.metadata.vouchers.length > 0
    ) {
      vouchers = product.metadata.vouchers;
    } else {
      vouchers = cartStore.vouchers.map((v) => ({
        id: v.id,
        label: v.title || v.id,
        sub:
          v.subtitle ||
          (v.type === "SHIPPING"
            ? "Miễn phí vận chuyển"
            : `Giảm ${formatCurrency(v.value)}`),
        type: v.type === "SHIPPING" ? "ship" : "discount",
      }));
    }
    return vouchers.filter((v: { id: string; label?: string }) => {
      const isViral =
        v.id.includes("VIRAL") ||
        (v.label || "").toUpperCase().includes("VIRAL");
      if (!isViral) return true;
      return isViralUnlocked;
    });
  });

  function triggerViralFly() {
    isViralUnlocked = true;
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
      (product.metadata?.brand as string) ||
      (product.attributes?.brand as string) ||
      (product.attributes?.["Thương hiệu"] as string) ||
      "",
    origin:
      (product.metadata?.origin as string) ||
      (product.attributes?.origin as string) ||
      (product.attributes?.["Xuất xứ"] as string) ||
      "",
    weight:
      (product.metadata?.weight as string) ||
      (product.attributes?.weight as string) ||
      (product.attributes?.["Trọng lượng"] as string) ||
      "",
    originalPrice: pDiscountPrice
      ? product.price || product.base_price || 0
      : (product.price || 0) * 1.55,
    salePrice: (pDiscountPrice as number) || (product.price as number) || 0,
  });

  const activePrices = $derived({
    sale: displayPrice.discountPrice || displayPrice.price,
    original: displayPrice.discountPrice
      ? displayPrice.price
      : typeof displayPrice.price === "number"
        ? displayPrice.price * 1.55
        : displayPrice.price,
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

  const helenAdvice = $derived.by(() => {
    const comboVariants = pVariants.filter(
      (cv) => cv.attributes && cv.attributes.combo_qty,
    );
    if (comboVariants.length === 0)
      return "Cơ hội sở hữu liệu trình chuyên sâu với ưu đãi độc quyền.";
    const sortedTiers = [...comboVariants].sort(
      (a, b) => Number(a.attributes.combo_qty) - Number(b.attributes.combo_qty),
    );
    const nextTier = sortedTiers.find(
      (t) => Number(t.attributes.combo_qty) > quantity,
    );
    if (nextTier) {
      const gap = Number(nextTier.attributes.combo_qty) - quantity;
      return `Chỉ thêm ${gap} sản phẩm để nhận trọn vẹn đặc quyền quà tặng đi kèm!`;
    }
    return `Tuyệt vời! Bạn đã sở hữu Liệu Trình Hoàn Mỹ với mức giá tối ưu nhất.`;
  });

  const activeComboQty = $derived(
    effectiveTier?.attributes?.combo_qty ||
      effectiveTier?.attributes?.comboQty ||
      0,
  );
  const activeGifts = $derived(effectiveTier?.attributes?.gifts || []);
</script>

<div class="bg-[#f6f6f6] min-h-screen">
  <!-- BREADCRUMB -->
  <div class="bg-[#f5f5f5] py-4">
    <div
      class="max-w-[1200px] mx-auto px-4 xl:px-0 flex items-center gap-3 text-[11px] text-gray-500 font-bold uppercase tracking-wider"
    >
      <a
        href="/"
        class="flex items-center gap-2 bg-[#ee4d2d] text-white px-2 py-1 hover:brightness-110 transition-all"
      >
        <Diamond size={10} fill="currentColor" />
        <span class="text-[9px] font-black tracking-[0.25em]">OSMO</span>
      </a>
      <span class="opacity-20">/</span>
      <span class="text-gray-400 normal-case tracking-normal font-medium"
        >{product.name}</span
      >
    </div>
  </div>

  <main class="max-w-[1200px] mx-auto bg-white shadow-sm mt-0 p-5">
    <div class="flex flex-col md:flex-row gap-8">
      <div class="relative w-full md:w-[450px] shrink-0">
        <button
          onclick={triggerScan}
          class="absolute top-2 right-2 z-20 w-14 h-14 cursor-pointer hover:scale-105 transition-transform drop-shadow-md bg-transparent border-none p-0 focus:outline-none"
        >
          <img
            src={product?.metadata?.verified_badge_url ||
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
        {displayPrice}
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
        {isViralUnlocked}
        onToggleVoucher={toggleVoucher}
        onSelectOption={selectOption}
        onQuantityChange={handleQuantityChange}
        onAddToCart={addToCart}
        onBuyNow={buyNow}
        onTriggerWriteReview={triggerWriteReview}
        onTriggerViralFly={triggerViralFly}
        onTriggerVerify={triggerScan}
      />
    </div>

    <ProductDetailSections
      {product}
      {productInfo}
      onTriggerScan={triggerScan}
      visibleAttributes={product.attributes
        ? Object.entries(product.attributes).filter(([key, value]) => {
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
          })
        : []}
    />

    <ProductDescription {product} />

    <div id="product-reviews" class="max-w-[1200px] mx-auto mt-6">
      <ProductReviews {product} />
    </div>

    <div class="max-w-[1200px] mx-auto mt-6 mb-12">
      <RelatedProducts {product} initialProducts={relatedProducts} />
    </div>
  </main>

  {#if isScanning}
    <ScannerHUD barcode={productInfo.barcode} oncomplete={handleScanComplete} />
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
          <VerificationCenter {product} {verificationData} />
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  :global(.prose-osmo) {
    font-family: inherit !important;
    font-size: 16px !important;
    line-height: 1.8 !important;
    color: #374151 !important;
  }
  :global(.prose-osmo p) {
    margin-bottom: 1rem !important;
  }
  :global(.prose-osmo h2, .prose-osmo h3) {
    color: #111827 !important;
    font-weight: 800 !important;
    margin-top: 2rem !important;
    margin-bottom: 1rem !important;
    text-transform: uppercase;
  }
  :global(.prose-osmo img) {
    width: 100% !important;
    height: auto !important;
    margin: 1rem auto !important;
    display: block;
  }

  /* Elite V2.2: Floating Verify Button Styles */
  .verify-floating-btn {
    position: relative;
    width: 56px;
    height: 56px;
    background: #00bfa5;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 10px 30px rgba(0, 191, 165, 0.4);
    transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
  }

  .verify-floating-btn:hover {
    transform: scale(1.1) translateY(-5px);
    box-shadow: 0 15px 40px rgba(0, 191, 165, 0.6);
  }

  .btn-inner {
    position: relative;
    z-index: 2;
  }

  .pulse-ring {
    position: absolute;
    inset: -4px;
    border: 2px solid #00bfa5;
    border-radius: 8px;
    opacity: 0;
    animation: verify-pulse 2s infinite;
  }

  @keyframes verify-pulse {
    0% {
      transform: scale(0.95);
      opacity: 0.8;
    }
    100% {
      transform: scale(1.4);
      opacity: 0;
    }
  }

  .btn-tooltip {
    position: absolute;
    left: 70px;
    background: #0a0a0a;
    color: white;
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 800;
    white-space: nowrap;
    opacity: 0;
    pointer-events: none;
    transition: all 0.3s;
    transform: translateX(-10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .verify-floating-btn:hover .btn-tooltip {
    opacity: 1;
    transform: translateX(0);
  }
</style>
