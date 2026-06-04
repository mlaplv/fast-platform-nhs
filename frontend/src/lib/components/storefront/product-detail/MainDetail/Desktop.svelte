<script lang="ts">
  import { untrack } from "svelte";
  import { goto } from "$app/navigation";

  // Types
  import type { Product, ProductVariant, ReviewStats } from "$lib/types";

  // State & Stores
  import { getCartStore } from "$lib/state/commerce/cart.svelte";
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import { authStore } from "$lib/state/authStore.svelte";

  // Utils
  import { processProductVouchers } from "$lib/utils/commerce/voucher";

  // Components
  import ProductReviews from "../shared/ProductReviews.svelte";
  import RelatedProducts from "../shared/RelatedProducts.svelte";
  import { SHOP_CONFIG } from "$lib/constants/shop";
  import ProductGallery from "./modules/Gallery.svelte";
  import ProductPrimaryInfo from "./modules/Info.svelte";
  import ProductDetailSections from "./modules/Sections.svelte";

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
    vouchers?: {
      id: string;
      label: string;
      sub: string;
      type: "ship" | "discount";
    }[];
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
  const metadata = $derived(
    (product.metadata || {}) as ExtendedProductMetadata,
  );

  const likeCount = $derived(
    Number(
      metadata.share_promotion?.likes_count || product.metadata?.["likes"] || 0,
    ),
  );

  const variations = $derived(
    (
      (product.tier_variations ||
        product.tierVariations ||
        []) as RawTierVariation[]
    ).map((v) => ({
      name: v.name || "",
      options: (v.options || []).map((o) =>
        typeof o === "string" ? o : String(o?.name || o?.label || ""),
      ),
      images: (v.images || []).filter((img): img is string => img !== null),
    })),
  );

  const pVariants = $derived(
    (product.variants || []).filter((v) => v.is_active !== false),
  );

  let selectedIndices = $state<number[]>([]);

  // Elite V2.2: O(1) Variant Activity Index Map — prebuilt once per product change
  // Eliminates O(N×M) .find()/.some() per option in Info.svelte
  const variantActivityMap = $derived.by(() => {
    const map = new Map<string, boolean>();
    const rawVariants = product.variants || [];
    for (const v of rawVariants) {
      const idxs = v.tierIndex || v.tier_index || [];
      const isActive = v.attributes?.is_active !== false;
      for (let tIdx = 0; tIdx < idxs.length; tIdx++) {
        const key = `${tIdx}:${idxs[tIdx]}`;
        if (isActive) map.set(key, true);
        else if (!map.has(key)) map.set(key, false);
      }
    }
    return map;
  });

  // Synchronize indices synchronously before paint to prevent layout shifts
  $effect.pre(() => {
    const _id = product.id; // track product transitions
    if (variations.length > 0) {
      const defaultVariant = pVariants.find((v) => v.is_default);
      const dIndices = defaultVariant?.tierIndex || defaultVariant?.tier_index;
      if (dIndices) {
        selectedIndices = [...dIndices];
      } else {
        selectedIndices = variations.map(() => 0);
      }
    } else {
      selectedIndices = [];
    }
  });
  let quantity = $state(1);
  // Pre-rendered for maximum SEO & instantaneous Above-the-fold paint

  const currentVariant = $derived<ProductVariant | undefined>(
    pVariants.find((v) => {
      const vIndices = v.tierIndex || v.tier_index;
      if (!vIndices) return false;
      return (
        vIndices.length === selectedIndices.length &&
        vIndices.every((val, i) => val === selectedIndices[i])
      );
    }),
  );

  // Elite V2.2 Memoized Static Range Calculation
  const priceRange = $derived.by(() => {
    if (pVariants.length === 0) return null;
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
      discountPrice:
        minDiscount !== undefined && maxDiscount !== undefined
          ? formatRange(minDiscount, maxDiscount)
          : undefined,
    };
  });

  const sortedComboVariants = $derived(
    pVariants
      .filter((cv) => cv.attributes && cv.attributes.combo_qty)
      .sort(
        (a, b) =>
          Number(b.attributes?.combo_qty || 0) -
          Number(a.attributes?.combo_qty || 0),
      )
  );

  const effectiveTier = $derived(
    sortedComboVariants.length > 0
      ? (sortedComboVariants.find(
          (t) => Number(t.attributes?.combo_qty || 0) <= quantity,
        ) || currentVariant)
      : currentVariant
  );

  const effectiveUnitPrice = $derived.by(() => {
    const v = effectiveTier;
    if (!v)
      return typeof product.discountPrice === "number"
        ? product.discountPrice
        : product.discount_price || product.price || 0;
    return v.discountPrice || v.discount_price || v.price;
  });

  const displayPrice = $derived.by(() => {
    if (currentVariant) {
      return {
        price: currentVariant.price,
        discountPrice: effectiveUnitPrice,
      };
    }
    if (priceRange) return priceRange;
    return {
      price: product.price,
      discountPrice: product.discountPrice || product.discount_price,
    };
  });

  const currentStock = $derived(
    currentVariant ? currentVariant.stock : product.stock,
  );

  function selectOption(tierIndex: number, optionIndex: number) {
    const newSelected = [...selectedIndices];
    if (newSelected[tierIndex] === optionIndex) {
      newSelected[tierIndex] = -1; // toggle off
    } else {
      newSelected[tierIndex] = optionIndex;
    }
    selectedIndices = newSelected;

    // Sync quantity with combo_qty (Elite V2.2)
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
      // Reset quantity if it exceeds new stock
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

      // SYNC BACK: Auto-select variant matching this quantity (Elite V2.2 Intelligence)
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

  // --- SALES ASSASSIN FOMO & VOUCHER LOGIC ---
  // Elite V2.2: Derive countdown from DB (product.metadata.flash_sale_end)
  const flashSaleEnd = $derived(
    metadata.flash_sale_end
      ? new Date(metadata.flash_sale_end).getTime()
      : null,
  );
  const isFlashSaleActive = $derived(
    flashSaleEnd !== null && flashSaleEnd > Date.now(),
  );
  let timeLeft = $state({ hours: 0, minutes: 0, seconds: 0 });

  /**
   * Elite V2.2: Theo dõi trạng thái mở khóa Viral để kích hoạt hiệu ứng bay
   * Tối ưu hóa truy cập localStorage đồng bộ và cache vào reactive state.
   */
  let isViralUnlocked = $state(false);
  let unlockedVoucherInfo = $state<{ code: string; label?: string } | null>(
    null,
  );

  $effect(() => {
    if (typeof window !== "undefined") {
      const userId = authStore.user?.id;
      const localKey = userId ? `viral_unlocked_${userId}_${product.id}` : null;
      const saved = localKey ? localStorage.getItem(localKey) : null;
      
      if (saved) {
        try {
          const data = JSON.parse(saved);
          unlockedVoucherInfo = data;
          isViralUnlocked = true;
          
          if (data.code) {
            untrack(() => {
              if (!selectedVouchers.includes(data.code)) {
                toggleVoucher(data.code);
              }
            });
          }
          return;
        } catch (e) {
          // Silent fail safe
        }
      }
      unlockedVoucherInfo = null;
      isViralUnlocked = false;
    }
  });

  // Voucher State
  let selectedVouchers = $state<string[]>([]);

  // Use DB vouchers if available
  const productVouchers = $derived.by(() => {
    return processProductVouchers({
      product,
      globalVouchers: cartStore.vouchers,
      isViralUnlocked,
      unlockedVoucherInfo,
      productPrice: effectiveUnitPrice || product.price || 0
    }) as VoucherUI[];
  });

  function triggerViralFly() {
    isViralUnlocked = true; // Cập nhật state để Svelte render voucher vào box ngay
    if (typeof window !== "undefined") {
      const userId = authStore.user?.id;
      const localKey = userId ? `viral_unlocked_${userId}_${product.id}` : null;
      const saved = localKey ? localStorage.getItem(localKey) : null;
      if (saved) {
        try {
          const data = JSON.parse(saved);
          unlockedVoucherInfo = data;
          
          // Elite V2.2: Tự động áp mã voucher vừa mới mở khóa để người dùng không phải click thủ công
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
      // Group-based exclusive selection
      const groupIds = productVouchers
        .filter((v) => v.type === voucher.type)
        .map((v) => v.id);
      selectedVouchers = [
        ...selectedVouchers.filter((v) => !groupIds.includes(v)),
        id,
      ];
    }
  }

  // Elite V2.2: Flash Sale Timer — only create interval when sale is genuinely active
  $effect(() => {
    if (!flashSaleEnd || flashSaleEnd <= Date.now()) {
      timeLeft = { hours: 0, minutes: 0, seconds: 0 };
      return;
    }

    const updateCountdown = () => {
      const diff = Math.max(0, flashSaleEnd! - Date.now());
      if (diff === 0) {
        timeLeft = { hours: 0, minutes: 0, seconds: 0 };
        clearInterval(timer);
        return;
      }
      timeLeft = {
        hours: Math.floor(diff / 3600000),
        minutes: Math.floor((diff % 3600000) / 60000),
        seconds: Math.floor((diff % 60000) / 1000),
      };
    };

    updateCountdown();
    const timer = setInterval(updateCountdown, 1000);
    return () => clearInterval(timer);
  });

  // Extract product details (Dynamic from DB)
  const pDiscountPrice = $derived(
    product.discountPrice || product.discount_price,
  );

  const productInfo = $derived({
    barcode: (product.sku as string) || "N/A",
    brand:
      (product.metadata?.brand as string) ||
      (product.attributes?.["brand"] as string) ||
      (product.attributes?.["Thương hiệu"] as string) ||
      "",
    origin:
      (product.metadata?.origin as string) ||
      (product.attributes?.["origin"] as string) ||
      (product.attributes?.["Xuất xứ"] as string) ||
      "",
    weight:
      (product.metadata?.weight as string) ||
      (product.attributes?.["weight"] as string) ||
      (product.attributes?.["Trọng lượng"] as string) ||
      "",
    originalPrice: pDiscountPrice
      ? product.price || product.base_price || 0
      : product.price || 0,
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

  function triggerVerify() {
    const btn = document.getElementById("btn-verify-product");
    if (btn) {
      btn.click();
    }
  }

  // --- HELEN AI PRICE INTELLIGENCE (VIRAL 2026) ---
  const helenAdvice = $derived(cartStore.getPromotionAdvice(product, quantity).text);

  const activeComboQty = $derived(
    effectiveTier?.attributes?.combo_qty ||
      effectiveTier?.attributes?.comboQty ||
      0,
  );
  const activeGifts = $derived(effectiveTier?.attributes?.gifts || []);

  // Elite Performance V2.2: Intersection Observer Sentinel for Below-the-fold dynamic modules
  let dynamicSection = $state<HTMLElement | null>(null);
  let shouldRenderDynamic = $state(false);

  $effect(() => {
    if (!dynamicSection) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          shouldRenderDynamic = true;
          observer.disconnect();
        }
      },
      { rootMargin: "300px" } // Load 300px before scrolling into view to guarantee seamless zero-wait UX
    );
    observer.observe(dynamicSection);
    return () => observer.disconnect();
  });

  // SGE Shield V1.0: Deterministic DOM Entropy (Product Detail)
  const wrapperTags = ["div", "article", "section", "main"];
  const seedLength = $derived(product?.name ? product.name.length : 10);
  const outerWrapper = $derived(wrapperTags[seedLength % wrapperTags.length]);
  const contentWrapper = $derived(
    wrapperTags[(seedLength + 3) % wrapperTags.length],
  );
  const descWrapper = $derived(
    ["div", "section", "article"][(seedLength + 5) % 3],
  );
</script>

<svelte:element this={outerWrapper} class="bg-[#f6f6f6] min-h-screen">
  <!-- VIRAL 2026: PROFESSIONAL BREADCRUMB -->
  <div class="bg-[#f5f5f5] py-4">
    <div
      class="max-w-[1200px] mx-auto px-4 xl:px-0 flex items-center gap-3 text-[12px] text-gray-400 font-medium"
    >
      <a
        href="/"
        class="text-gray-400 hover:text-[#ee4d2d] transition-all font-black tracking-widest text-[11px]"
      >
        Osmo
      </a>
      <span class="opacity-30">/</span>
      <span class="text-gray-500 font-medium">{product.name}</span>
    </div>
  </div>

  <svelte:element
    this={contentWrapper}
    class="max-w-[1200px] mx-auto bg-white shadow-sm mt-0 rounded-none p-5"
  >
    <div class="flex flex-col md:flex-row gap-4">
      <!-- LEFT: IMAGES & SOCIAL (ProductGallery Module) -->
      <div class="relative shrink-0">
        <button
          onclick={triggerVerify}
          class="absolute top-2 right-2 z-20 w-14 h-14 cursor-pointer hover:opacity-90 drop-shadow-md bg-transparent border-none p-0 focus:outline-none"
        >
          <img
            src={product?.metadata?.verified_badge_url ||
              SHOP_CONFIG.default_badge_url}
            alt="Verified"
            class="w-full h-full object-contain drop-shadow-[0_4px_10px_rgba(0,0,0,0.1)]"
            decoding="async"
            fetchpriority="low"
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

      <!-- RIGHT: PRODUCT INFO (ProductPrimaryInfo Module) -->
      <div class="min-w-0 flex-1">
        <ProductPrimaryInfo
          {product}
          stats={reviewStats}
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
          {variantActivityMap}
          onToggleVoucher={toggleVoucher}
          onSelectOption={selectOption}
          onQuantityChange={handleQuantityChange}
          onAddToCart={addToCart}
          onBuyNow={buyNow}
          onTriggerWriteReview={triggerWriteReview}
          onTriggerViralFly={triggerViralFly}
        />
      </div>
    </div>
  </svelte:element>

  <!-- DETAIL SECTIONS (Specs, Ingredients, Description, FAQs) - Pre-rendered for maximum SEO & instantaneous Above-the-fold paint -->
  <ProductDetailSections
    {product}
    {productInfo}
    visibleAttributes={product.attributes
      ? (Object.entries(product.attributes).filter(([key, value]) => {
          const k = key.toLowerCase().replace(/_/g, " ").trim();
          const brand = productInfo.brand;
          const origin = productInfo.origin;
          const weight = productInfo.weight;
          return !(
            ((k === "xuất xứ" || k === "origin") && origin) ||
            ((k === "trọng lượng" || k === "quy cách" || k === "weight") &&
              weight) ||
            ((k === "mã vạch" || k === "barcode") &&
              productInfo.barcode &&
              productInfo.barcode !== "N/A") ||
            k === "thương hiệu" ||
            k === "brand"
          );
        }) as [string, string | number | Record<string, unknown>][])
      : []}
  />

  <!-- BELOW THE FOLD DYNAMIC SECTIONS -->
  <div bind:this={dynamicSection} class="w-full min-h-[1px]">
    {#if shouldRenderDynamic}
      <!-- REVIEWS SECTION -->
      <ProductReviews {product} />

      <!-- RELATED PRODUCTS -->
      <div class="max-w-[1200px] mx-auto mt-0 mb-12">
        <RelatedProducts {product} initialProducts={relatedProducts} />
      </div>
    {/if}
  </div>
</svelte:element>

<style>
  :global(.prose-osmo) {
    font-family: inherit !important;
    font-size: 15px !important; /* Sleek e-commerce standard (Lazada/Shopee) */
    line-height: 1.6 !important;
    color: #374151 !important; /* text-gray-700 */
  }

  :global(.prose-osmo p) {
    margin-bottom: 1rem !important;
    font-family: inherit !important;
    font-weight: 400 !important;
    letter-spacing: -0.011em !important;
  }

  /* Khử margin và tránh block-break gây vỡ hàng cho p trong li */
  :global(.prose-osmo li p) {
    display: inline !important;
    margin-bottom: 0 !important;
  }

  :global(.prose-osmo span) {
    font-family: inherit !important;
    font-size: inherit !important;
    line-height: inherit !important;
  }

  :global(.prose-osmo h2, .prose-osmo h3) {
    color: #6b7280 !important;
    font-weight: 800 !important;
    margin-top: 0.5rem !important;
    margin-bottom: 1rem !important;
    font-family: inherit !important;
    letter-spacing: -0.025em;
  }

  :global(.prose-osmo h2) {
    font-size: 20px !important;
  }
  :global(.prose-osmo h3) {
    font-size: 18px !important;
  }

  /* Elite V2.2: Multi-level Viral Bullets */
  :global(.prose-osmo ul),
  :global(.prose-osmo ol) {
    list-style: none !important;
    padding-left: 0 !important;
    margin-bottom: 1.5rem !important;
  }

  :global(.prose-osmo ul li),
  :global(.prose-osmo ol li) {
    list-style-type: none !important;
    position: relative !important;
    margin-bottom: 0.75rem !important;
    padding-left: 0 !important;
  }

  :global(.prose-osmo ul li::marker),
  :global(.prose-osmo ol li::marker) {
    content: none !important;
  }

  /* Level 1 Bullet: Viral Sparkle */
  :global(.prose-osmo ul > li::before) {
    content: "✦" !important;
    position: static !important;
    display: inline-block !important;
    color: #ee4d2d !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    margin-right: 0.35rem !important;
  }

  /* Level 2 */
  :global(.prose-osmo ul ul) {
    margin-top: 0.5rem !important;
    margin-bottom: 0.5rem !important;
    padding-left: 0.5rem !important;
  }

  :global(.prose-osmo ul ul > li) {
    padding-left: 1.25rem !important;
    margin-bottom: 0.5rem !important;
  }

  /* Level 2 Bullet: Hollow Dot */
  :global(.prose-osmo ul ul > li::before) {
    content: "" !important;
    position: absolute !important;
    left: 0 !important;
    top: 0.65em !important;
    width: 6px !important;
    height: 6px !important;
    background-color: transparent !important;
    border: 2px solid #ff927b !important;
    border-radius: 50% !important;
  }

  /* Level 3 */
  :global(.prose-osmo ul ul ul) {
    padding-left: 0.5rem !important;
  }

  :global(.prose-osmo ul ul ul > li::before) {
    content: "-" !important;
    position: absolute !important;
    left: 0 !important;
    top: 0 !important;
    color: #9ca3af !important;
    font-weight: bold !important;
    border: none !important;
    background: transparent !important;
    width: auto !important;
    height: auto !important;
    font-size: 16px !important;
  }

  /* Ordered Lists */
  :global(.prose-osmo ol) {
    counter-reset: osmo-counter;
  }
  :global(.prose-osmo ol > li) {
    counter-increment: osmo-counter;
    padding-left: 0 !important;
  }
  :global(.prose-osmo ol > li::before) {
    content: counter(osmo-counter) "." !important;
    position: static !important;
    display: inline-block !important;
    color: #ee4d2d !important;
    font-weight: 900 !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    margin-right: 0.35rem !important;
  }

  :global(.prose-osmo img) {
    max-width: 100% !important;
    height: auto !important;
    margin: 1.5rem auto !important;
    display: block;
    border-radius: 12px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  }

  :global(.prose-osmo figure) {
    margin: 1.5rem auto !important;
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
    font-size: 13px !important;
    color: #6b7280 !important;
    font-style: italic !important;
    line-height: 1.4 !important;
  }

  /* Google SGE Highlights Styling (GEO 2026) */
  :global(.semantic-summary h2) {
    font-size: 16px !important;
    font-weight: 800 !important;
    color: #1f2937 !important;
    margin-top: 0 !important;
    margin-bottom: 12px !important;
    text-transform: none !important;
    letter-spacing: -0.01em !important;
  }
  :global(.semantic-summary h2::first-letter) {
    text-transform: none !important;
  }
  :global(.semantic-summary .product-highlights) {
    list-style-type: none !important;
    padding-left: 0 !important;
    margin: 0 !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
  }
  :global(.semantic-summary .product-highlights li) {
    position: relative !important;
    padding-left: 20px !important;
    font-size: 13.5px !important;
    line-height: 1.6 !important;
    color: #4b5563 !important;
  }
  :global(.semantic-summary .product-highlights li::before) {
    content: "•" !important;
    position: absolute !important;
    left: 4px !important;
    top: 0 !important;
    color: #10b981 !important; /* HSL Emerald Green Bullet */
    font-size: 18px !important;
    line-height: 1.2 !important;
  }
</style>
