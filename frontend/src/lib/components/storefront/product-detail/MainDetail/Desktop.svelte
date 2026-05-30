<script lang="ts">
  import { onMount, untrack } from "svelte";
  import { goto } from "$app/navigation";

  // Types
  import type { Product, ProductVariant, ReviewStats } from "$lib/types";

  // State & Stores
  import { getCartStore } from "$lib/state/commerce/cart.svelte";
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import { supportAgent } from "$lib/state/commerce/supportAgent.svelte";

  // Utils
  import { resolveMediaUrl } from "$lib/state/utils";
  import { formatCurrency } from "$lib/utils/format";

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

  const effectiveTier = $derived.by(() => {
    const comboVariants = pVariants.filter(
      (cv) => cv.attributes && cv.attributes.combo_qty,
    );
    if (comboVariants.length === 0) return currentVariant;
    const sortedTiers = [...comboVariants].sort(
      (a, b) =>
        Number(b.attributes?.combo_qty || 0) -
        Number(a.attributes?.combo_qty || 0),
    );
    return (
      sortedTiers.find(
        (t) => Number(t.attributes?.combo_qty || 0) <= quantity,
      ) || currentVariant
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

  const displayPrice = $derived.by(() => {
    if (currentVariant) {
      return {
        price: currentVariant.price,
        discountPrice: effectiveUnitPrice,
      };
    }
    // Min max range if not selected
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
        discountPrice:
          minDiscount !== undefined && maxDiscount !== undefined
            ? formatRange(minDiscount, maxDiscount)
            : undefined,
      };
    }

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
      const saved = localStorage.getItem(`viral_unlocked_${product.id}`);
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
    let vouchers: {
      id: string;
      label: string;
      sub: string;
      type: "ship" | "discount";
    }[] = [];

    // 1. Check if product has specific override vouchers in metadata
    if (Array.isArray(metadata.vouchers) && metadata.vouchers.length > 0) {
      vouchers = metadata.vouchers as {
        id: string;
        label: string;
        sub: string;
        type: "ship" | "discount";
        value?: number;
      }[];
    } else {
      // 2. Fallback to global active vouchers from CartStore (Elite V2.2)
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
          type:
            v.type === "SHIPPING" ? ("ship" as const) : ("discount" as const),
          value: v.value || 0,
        }));
    }

    const cleanString = (s: string) => {
      return (s || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toUpperCase();
    };

    const isViralVoucher = (v: { id: string; label?: string }) => {
      const promoVId = metadata.share_promotion?.voucher_id;
      const cleanId = cleanString(v.id);
      const cleanLabel = cleanString(v.label);
      return (
        cleanId.includes("VIRAL") ||
        cleanId.includes("LAN TOA") ||
        cleanLabel.includes("VIRAL") ||
        cleanLabel.includes("LAN TOA") ||
        (promoVId && v.id === promoVId)
      );
    };

    /**
     * Elite V2.2: Intelligent Filtering
     * Lọc bỏ các Voucher Viral để tránh hiện ở khối chung khi CHƯA chia sẻ.
     * Nếu ĐÃ mở khóa (isViralUnlocked), mã sẽ được hiển thị như một phần của hệ thống.
     */
    let vList = vouchers.filter((v: { id: string; label?: string }) => {
      return !isViralVoucher(v) || isViralUnlocked;
    });

    // Elite V2.2 Re-injection: Phục hồi voucher từ session local nếu đã mở khóa
    if (unlockedVoucherInfo) {
      // Filter out existing viral vouchers to prevent duplicates or wrong positions
      vList = vList.filter(
        (v) => !isViralVoucher(v) && v.id !== unlockedVoucherInfo!.code,
      );
      // Prepend at the absolute top (Position #1)
      vList.unshift({
        id: unlockedVoucherInfo.code,
        label: unlockedVoucherInfo.label || "Voucher lan tỏa",
        sub: "Đã mở khóa từ chiến dịch",
        type: "discount",
        value: 79000,
      });
    }

    const getVoucherValue = (v: any) => {
      let rawVal = typeof v.value === "number" ? v.value : 0;
      const subText = String(v.sub || "").toLowerCase();
      const labelText = String(v.label || "").toLowerCase();
      
      const productPrice = effectiveUnitPrice || product.price || 0;

      if (rawVal === 0) {
        const found = cartStore.vouchers.find((x) => x.id === v.id);
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

      const parsed = parseInt(subText.replace(/[^0-9]/g, ""), 10);
      return isNaN(parsed) ? 0 : parsed;
    };

    // Sort by value descending (Giá giảm dần)
    const sorted = [...vList].sort((a, b) => {
      const valA = getVoucherValue(a);
      const valB = getVoucherValue(b);
      return valB - valA;
    });

    // Grouping by type:
    // 1. Viral/Độc quyền Vouchers always at the absolute top
    const viralVouchers = sorted.filter((v) => isViralVoucher(v));
    // 2. Regular discount vouchers
    const regularDiscount = sorted.filter((v) => !isViralVoucher(v) && v.type === "discount");
    // 3. Regular shipping vouchers
    const regularShipping = sorted.filter((v) => !isViralVoucher(v) && v.type === "ship");

    return [...viralVouchers, ...regularDiscount, ...regularShipping] as VoucherUI[];
  });

  /**
   * Elite V2.2: Hiệu ứng bay vào Box giảm giá
   */
  function triggerViralFly() {
    isViralUnlocked = true; // Cập nhật state để Svelte render voucher vào box ngay
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem(`viral_unlocked_${product.id}`);
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
        seconds: Math.floor((diff % 60000) / 1000),
      };
    }

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
  {#if loadBelowFold}
    <!-- REVIEWS SECTION -->
    <ProductReviews {product} />

    <!-- RELATED PRODUCTS -->
    <div class="max-w-[1200px] mx-auto mt-0 mb-12">
      <RelatedProducts {product} initialProducts={relatedProducts} />
    </div>
  {:else}
    <!-- Empty placeholders to eliminate CLS and maintain vertical layout rhythm during load -->
    <div class="max-w-[1200px] mx-auto mt-8 h-[200px] bg-white border border-gray-100 flex flex-col items-center justify-center text-gray-300 gap-2">
      <div class="w-10 h-10 rounded-full border-2 border-gray-100 animate-spin" style="border-top-color: var(--color-luxury-copper, #C18F7E);"></div>
      <span class="text-[11px] font-black tracking-widest uppercase">Đang tải đánh giá và gợi ý...</span>
    </div>
  {/if}
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
