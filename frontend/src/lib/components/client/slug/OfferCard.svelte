<script lang="ts">
  import { getShopStore } from "$lib/state/commerce/shop.svelte.ts";
  import { getCartStore } from "$lib/state/commerce/cart.svelte.ts";
  import { resolveMediaUrl } from "$lib/state/utils";
  import { liveEditStore } from "$lib/state/commerce/liveEdit.svelte";
  import EditableWrapper from "$lib/components/admin/EditableWrapper.svelte";
  import type { Product, ProductVariant, Voucher } from "$lib/types";
  import { SHOP_CONFIG } from "$lib/constants/shop";
  import OfferVoucherSheet from "./OfferVoucherSheet.svelte";
  import { formatCurrency } from "$lib/utils/format";
  import Ticket from "@lucide/svelte/icons/ticket";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Zap from "@lucide/svelte/icons/zap";
  import ArrowRight from "@lucide/svelte/icons/arrow-right";
  import ShoppingCart from "@lucide/svelte/icons/shopping-cart";
  import Info from "@lucide/svelte/icons/info";
  import Check from "@lucide/svelte/icons/check";
  import Flame from "@lucide/svelte/icons/flame";

  interface MktLabels {
    sub: string;
    timer_prefix: string;
    shipping_prefix: string;
    savings_prefix: string;
    booking_suffix: string;
    trust_verified_by: string;
    compliance_note: string;
    label_activation: string;
    label_full_treatment: string;
    label_expert_choice: string;
    cta_start: string;
    cta_full: string;
  }

  const {
    variant,
    idx,
    product,
    variantsCount,
    mkt,
    productVouchers,
    onOpenVouchers,
    onTriggerScan,
    onOpenDetails,
  } = $props<{
    variant: ProductVariant;
    idx: number;
    product: Product | null;
    variantsCount: number;
    mkt: MktLabels;
    productVouchers: Voucher[];
    onOpenVouchers: (id: string) => void;
    onTriggerScan?: () => void;
    onOpenDetails?: () => void;
  }>();

  const shopStore = getShopStore();
  const cartStore = getCartStore();

  const isCardActive = $derived(shopStore.variant?.id === variant.id);
  const displayQty = $derived(
    isCardActive
      ? shopStore.variant?.attributes?.combo_qty || shopStore.quantity
      : variant.attributes?.combo_qty || 1,
  );

  // --- ELITE V2.2: DYNAMIC COMBO PRICING ENGINE ---
  const comboQty = $derived(variant.attributes?.combo_qty || 1);

  function getVariantTitle(v: ProductVariant) {
    const qty = v.attributes?.combo_qty || 1;
    const qtySuffix = qty > 1 ? ` - BỘ ${qty} MÓN` : "";
    if (product?.tierVariations?.length && v.tierIndex?.length) {
      const title = v.tierIndex
        .map((optIdx, tierIdx) => {
          const option = product.tierVariations![tierIdx]?.options[optIdx];
          return typeof option === "string"
            ? option
            : typeof option === "object" && option
              ? option.name || option.label || ""
              : "";
        })
        .filter(Boolean)
        .join(" - ");
      return title + qtySuffix;
    }
    return (v.sku || "Combo") + qtySuffix;
  }

  const variantTitle = $derived(getVariantTitle(variant));
  const resolvedGifts = $derived(
    variant?.gifts?.length
      ? variant.gifts
      : variant.attributes?.gifts?.length
        ? variant.attributes.gifts
        : variantTitle === "Dứt điểm" ||
            variantTitle.toLowerCase().includes("mua 3") ||
            comboQty === 3
          ? [
              {
                name: "Miccosmo Beppin Body Virgin White Serum 30g",
                image: "/uploads/img/osmo/sp1.png",
                quantity: 1,
                type: "PRODUCT",
              },
            ]
          : product?.gifts || [],
  );

  function getGiftPrice(gift: any): number {
    if (gift.price) return gift.price;
    const name = gift.name || "";
    const nameLower = name.toLowerCase();

    // Look up table matching db seed prices
    if (nameLower.includes("virgin white") || nameLower.includes("beppin body"))
      return 600000;
    if (
      nameLower.includes("wrinkle serum") ||
      nameLower.includes("hurry harry")
    )
      return 850000;
    if (nameLower.includes("rich gold cream")) return 790000;
    if (
      nameLower.includes("gold essence") ||
      nameLower.includes("whitening cream")
    )
      return 690000;
    if (nameLower.includes("rich gold gel") || nameLower.includes("neck cream"))
      return 650000;
    if (
      nameLower.includes("eye cream") ||
      nameLower.includes("placenta pack") ||
      nameLower.includes("rich gold essence")
    )
      return 600000;
    if (nameLower.includes("placenta essence")) return 550000;
    if (
      nameLower.includes("placenta wash") ||
      nameLower.includes("placenta cream")
    )
      return 450000;
    if (nameLower.includes("hand balm")) return 400000;
    if (nameLower.includes("golgo shot")) return 550000;

    // Fallback to a default premium gift price
    return 600000;
  }

  // Base unit prices (DB source)
  const unitPrice = $derived(variant.discountPrice || variant.price || 0);
  const unitOriginalPrice = $derived(variant.price || 0);

  // Adjusted prices (including vouchers) - Grid shows UNIT price as primary
  const unitPriceInfo = $derived(
    shopStore.calculateAdjustedPrice(variant, 1, shopStore.selectedVoucherIds),
  );
  const finalUnitPrice = $derived(unitPriceInfo.final);

  // Total package values
  const totalPackagePrice = $derived(finalUnitPrice * comboQty);
  const totalOriginalPackagePrice = $derived(unitOriginalPrice * comboQty);

  const voucherDiscountPerUnit = $derived(unitPriceInfo.voucherDiscount);
  const totalSavings = $derived(totalOriginalPackagePrice - totalPackagePrice);

  const selectedVouchers = $derived(
    (shopStore.vouchers || []).filter((v) =>
      shopStore.selectedVoucherIds.includes(v.id),
    ),
  );
  const shippingVoucher = $derived(
    selectedVouchers.find((v) => v.type === "SHIPPING"),
  );
  const discountVoucher = $derived(
    selectedVouchers.find((v) => v.type !== "SHIPPING"),
  );

  const sortedProductVouchers = $derived.by(() => {
    const cleanString = (s: string) => {
      return (s || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toUpperCase();
    };

    const isViralVoucher = (v: Voucher) => {
      const cleanId = cleanString(v.id);
      const cleanLabel = cleanString(v.label || v.title || "");
      return (
        v.is_viral ||
        cleanId.includes("VIRAL") ||
        cleanId.includes("LAN TOA") ||
        cleanLabel.includes("VIRAL") ||
        cleanLabel.includes("LAN TOA")
      );
    };

    const getVoucherValue = (v: Voucher) => {
      let rawVal = v.value || 0;
      const productPrice = finalUnitPrice || unitPrice || 0;
      const subText = String(v.sub || v.subtitle || "").toLowerCase();
      const labelText = String(v.label || v.title || "").toLowerCase();

      if (
        v.type === "PERCENT" ||
        subText.includes("%") ||
        labelText.includes("%")
      ) {
        return (productPrice * rawVal) / 100;
      }
      return rawVal;
    };

    // Sort by value descending (Giá giảm dần)
    const sorted = [...productVouchers].sort((a, b) => {
      const valA = getVoucherValue(a);
      const valB = getVoucherValue(b);
      return valB - valA;
    });

    // Grouping by type:
    // 1. Viral/Độc quyền Vouchers always at the absolute top
    const viralVouchers = sorted.filter((v) => isViralVoucher(v));
    // 2. Regular discount/gift vouchers
    const regularDiscount = sorted.filter(
      (v) => !isViralVoucher(v) && v.type !== "ship",
    );
    // 3. Regular shipping vouchers
    const regularShipping = sorted.filter(
      (v) => !isViralVoucher(v) && v.type === "ship",
    );

    return [...viralVouchers, ...regularDiscount, ...regularShipping];
  });

  // Elite V2.2: Realistic FOMO - Deterministic stock based on variant ID
  const displayStock = $derived.by(() => {
    if (variant.stock && variant.stock < 10) return variant.stock;
    const hash = [...String(variant.id)].reduce(
      (a, b) => a + b.charCodeAt(0),
      0,
    );
    return (hash % 6) + 3;
  });

  // --- MEMOIZED FEATURES (ELITE V2.2: NO FUNCTION-IN-RENDER) ---
  const features = $derived.by(() => {
    const variantRaw = variant as ProductVariant & {
      attributes?: { features?: string[]; combo_qty?: number };
    };
    let list = [...(variantRaw.attributes?.features || [])];
    if (list.length === 0) {
      const fallbackIdx = idx > 0 ? 1 : 0;
      list = [...(SHOP_CONFIG.default_features[fallbackIdx] || [])];
    }
    list = list.filter(
      (f) =>
        !["Cam kết hoàn tiền ẩn danh", "Tặng kèm Voucher"].some((term) =>
          f.includes(term),
        ),
    );

    let currentQty = displayQty;
    let displayQtyStr = currentQty < 10 ? `0${currentQty}` : `${currentQty}`;
  });

  const variantImage = $derived.by(() => {
    const tierVar =
      product?.tierVariations?.[0] || product?.tier_varations?.[0];
    const optIdx = variant.tierIndex?.[0] ?? variant.tier_index?.[0] ?? idx;
    const deskImg = tierVar?.images?.[optIdx];
    return resolveMediaUrl(
      deskImg || product?.images?.[idx] || product?.images?.[0] || "",
    );
  });

  let isNavigating = $state(false);

  function selectVariant() {
    shopStore.selectVariant(variant);
  }

  function handleCheckout(e: MouseEvent) {
    e.stopPropagation();
    if (isNavigating) return;

    isNavigating = true;
    shopStore.selectVariant(variant);
    if (product) {
      const qty = variant.attributes?.combo_qty || 1;
      cartStore.buyNow(product, variant, qty, shopStore.selectedVoucherIds);
    }

    // Elite V2.2: Smooth cinematic delay before navigation
    setTimeout(() => {
      window.location.href = "/checkout";
    }, 150);
  }

  function handleTriggerVerify(e: MouseEvent) {
    e.stopPropagation();
    onTriggerScan?.();
  }
</script>

<div
  class="relative h-full z-10 {variantsCount >= 3 ? 'min-w-0 snap-center' : ''}"
>
  <div
    class="absolute -top-4 left-1/2 -translate-x-1/2 flex flex-wrap gap-2 justify-center w-[120%] z-[60] pointer-events-none mt-1"
  >
    {#if idx === 1 && !isCardActive}
      <div
        class="px-5 py-2 expert-choice-ribbon text-white font-black text-[9px] tracking-[0.4em] rounded-xl shadow-[0_10px_30px_rgba(0,0,0,0.5)] backdrop-blur-md"
      >
        {mkt.label_expert_choice}
      </div>
    {/if}
  </div>

  <!-- 📦 PRODUCT CARD CONTENT -->
  <div
    onclick={selectVariant}
    onkeydown={(e) => e.key === "Enter" && selectVariant()}
    role="button"
    tabindex="0"
    class="package-card overflow-hidden text-left flex flex-col h-full relative cursor-pointer {idx ===
    1
      ? 'popular'
      : ''} {isCardActive
      ? 'active border-luxury-sakura shadow-[0_8px_24px_rgba(255,183,197,0.15)]'
      : ''}"
  >
    <div class="variant-image-hero relative w-full h-[320px] overflow-hidden">
      <div
        class="absolute inset-0 bg-radial-at-t from-luxury-sakura/10 to-transparent pointer-events-none transition-opacity duration-700 {isCardActive
          ? 'opacity-100'
          : 'opacity-0'}"
      ></div>
      <img
        src={variantImage}
        alt="{product?.name ? product.name + ' - ' : ''}{getVariantTitle(
          variant,
        )}"
        loading="lazy"
        decoding="async"
        class="w-full h-full object-cover drop-shadow-[0_40px_30px_rgba(0,0,0,0.7)] transform hover:scale-110 transition-transform duration-1000 z-10 relative"
      />
      <img
        src={variantImage}
        alt=""
        aria-hidden="true"
        loading="lazy"
        decoding="async"
        class="absolute top-[75%] left-0 w-full h-full object-cover scale-y-[-1] opacity-30 blur-lg grayscale pointer-events-none"
      />
      <div class="absolute top-6 left-6 z-20">
        <EditableWrapper
          path={idx === 0
            ? "metadata.offer_label_activation"
            : "metadata.offer_label_full_treatment"}
          type="text"
          label="SỬA NHÃN"
          class="block"
        >
          <p
            class="text-[10px] font-bold {idx >= 1
              ? 'text-luxury-sakura'
              : 'text-slate-200'} px-3 py-1.5 rounded-full bg-black/40 backdrop-blur-md border border-white/10 shadow-sm leading-none first-letter:uppercase lowercase"
          >
            {idx === 0 ? mkt.label_activation : mkt.label_full_treatment}
          </p>
        </EditableWrapper>
      </div>

      <button
        onclick={handleTriggerVerify}
        class="absolute top-4 right-4 z-30 w-12 h-12 cursor-pointer hover:scale-105 transition-transform drop-shadow-md bg-transparent border-none p-0 focus:outline-none pointer-events-auto"
      >
        <img
          src={product?.metadata?.verified_badge_url ||
            SHOP_CONFIG.default_badge_url}
          alt="Verified"
          class="w-full h-full object-contain drop-shadow-[0_4px_10px_rgba(0,0,0,0.1)]"
        />
      </button>

      <div class="liquid-specular-highlight"></div>

      <!-- 🎁 [ELITE V2.2] COMPACT VIRAL LIQUID-GLASS GIFT OVERLAY -->
      {#if resolvedGifts && resolvedGifts.length > 0}
        <div
          class="absolute bottom-2.5 left-2.5 right-2.5 z-30 transition-all duration-500 {isCardActive
            ? 'scale-[1.01]'
            : ''}"
        >
          <div
            class="relative w-full overflow-hidden white-glass-overlay rounded-2xl p-1.5 px-3 flex items-center justify-between gap-2 select-none"
          >
            <!-- Shimmer effect -->
            <div
              class="absolute inset-0 w-[200%] translate-x-[-100%] bg-gradient-to-r from-transparent via-white/40 to-transparent animate-shimmer-fast pointer-events-none"
            ></div>

            <div class="flex items-center gap-1.5 min-w-0 flex-1 relative z-10">
              <!-- Gift Item list (rendered inline) -->
              <div class="flex items-center gap-2 min-w-0 flex-1">
                {#each resolvedGifts as gift}
                  {#if gift.slug}
                    <a
                      href="/{gift.slug}"
                      onclick={(e) => e.stopPropagation()}
                      class="flex items-center gap-2 min-w-0 flex-1 group/gift-item hover:opacity-90 transition-opacity"
                      style="text-decoration: none;"
                    >
                      <div
                        class="w-8 h-8 bg-white border border-slate-200/50 rounded-lg overflow-hidden shrink-0 flex items-center justify-center shadow-sm"
                      >
                        {#if gift.image && gift.image !== "/uploads/img/osmo/sp1.png"}
                          <img
                            src={resolveMediaUrl(gift.image)}
                            alt={gift.name}
                            class="w-full h-full object-cover"
                          />
                        {:else}
                          <img
                            src={resolveMediaUrl(product?.images?.[0] || "")}
                            alt={gift.name}
                            class="w-full h-full object-cover"
                          />
                        {/if}
                      </div>
                      <div
                        class="flex flex-col min-w-0 flex-1 justify-center text-left"
                      >
                        <span
                          class="text-slate-800 font-black text-[9px] tracking-tight truncate leading-tight group-hover/gift-item:text-luxury-sakura transition-colors"
                          style="text-transform: none;"
                        >
                          {gift.name}
                        </span>
                        <span
                          class="text-viral-gradient text-[8.5px] tracking-tight leading-tight mt-0.5 truncate"
                          style="text-transform: none;"
                        >
                          Quà tặng độc quyền trị giá {formatCurrency(
                            getGiftPrice(gift) *
                              (gift.qty || gift.quantity || 1),
                          )}
                        </span>
                      </div>
                    </a>
                  {:else}
                    <div class="flex items-center gap-2 min-w-0 flex-1">
                      <div
                        class="w-8 h-8 bg-white border border-slate-200/50 rounded-lg overflow-hidden shrink-0 flex items-center justify-center shadow-sm"
                      >
                        {#if gift.image && gift.image !== "/uploads/img/osmo/sp1.png"}
                          <img
                            src={resolveMediaUrl(gift.image)}
                            alt={gift.name}
                            class="w-full h-full object-cover"
                          />
                        {:else}
                          <img
                            src={resolveMediaUrl(product?.images?.[0] || "")}
                            alt={gift.name}
                            class="w-full h-full object-cover"
                          />
                        {/if}
                      </div>
                      <div
                        class="flex flex-col min-w-0 flex-1 justify-center text-left"
                      >
                        <span
                          class="text-slate-800 font-black text-[9px] tracking-tight truncate leading-tight"
                          style="text-transform: none;"
                        >
                          {gift.name}
                        </span>
                        <span
                          class="text-viral-gradient text-[8.5px] tracking-tight leading-tight mt-0.5 truncate"
                          style="text-transform: none;"
                        >
                          Quà tặng độc quyền trị giá {formatCurrency(
                            getGiftPrice(gift) *
                              (gift.qty || gift.quantity || 1),
                          )}
                        </span>
                      </div>
                    </div>
                  {/if}

                  <!-- Quantity Badge -->
                  <span
                    class="text-rose-700 font-black text-[9px] shrink-0 px-2 py-0.5 flex items-center justify-center bg-rose-500/15 border border-rose-500/20 rounded-full tabular-nums shadow-sm"
                  >
                    x{gift.qty || gift.quantity || 1}
                  </span>
                {/each}
              </div>
            </div>
          </div>
        </div>
      {/if}
    </div>

    <div class="px-5 pb-6 pt-2 flex flex-col flex-grow relative z-20">
      <div
        class="elite-price-cluster flex flex-col items-center md:items-start gap-0 mb-2"
      >
        {#if variant.attributes?.combo_qty && variant.attributes.combo_qty > 1}
          <div
            class="combo-volume-badge mb-1.5 flex items-center gap-1 px-2.5 py-1 rounded-md bg-luxury-sakura/10 border border-luxury-sakura/20"
          >
            <Ticket class="w-2.5 h-2.5 text-luxury-sakura" />
            <span
              class="text-[9px] font-black text-luxury-sakura tracking-[0.2em]"
              >Số lượng: {variant.attributes.combo_qty} Sản phẩm</span
            >
          </div>
        {/if}
        <h2
          class="text-[15px] font-black text-white italic tracking-tighter text-center md:text-left leading-none mb-1"
        >
          {getVariantTitle(variant)}
        </h2>
        <div class="flex items-baseline gap-2 leading-none mt-1">
          <span
            class="text-3xl font-black text-white tabular-nums leading-none tracking-tighter"
            >{formatCurrency(finalUnitPrice)}</span
          >
          <span class="text-[10px] font-bold text-white/40 tracking-widest"
            >/ Sản phẩm</span
          >
        </div>

        {#if comboQty > 1}
          <div class="flex items-center gap-2 mt-1 mb-1">
            <span
              class="text-[11px] font-bold text-luxury-sakura/80 tabular-nums"
              >Tổng gói: {formatCurrency(totalPackagePrice)}</span
            >
            {#if totalOriginalPackagePrice > totalPackagePrice}
              <span
                class="text-[10px] text-white/20 line-through tabular-nums decoration-white/20"
                >{formatCurrency(totalOriginalPackagePrice)}</span
              >
            {/if}
          </div>
        {:else if unitOriginalPrice > finalUnitPrice}
          <div class="mt-1 mb-1">
            <span
              class="text-[11px] text-white/20 line-through tabular-nums decoration-white/20"
              >{formatCurrency(unitOriginalPrice)}</span
            >
          </div>
        {/if}

        <div
          class="flex flex-wrap items-center gap-2 mt-1.5 min-h-[20px] relative z-20"
        >
          {#if sortedProductVouchers.filter( (v) => shopStore.selectedVoucherIds.includes(v.id), ).length > 0}
            {#each sortedProductVouchers.filter( (v) => shopStore.selectedVoucherIds.includes(v.id), ) as v}
              <span
                class="text-[11px] font-black text-luxury-sakura leading-none flex items-center"
              >
                {v.label.toLowerCase().includes("freeship") &&
                v.sub.toLowerCase().includes("freeship")
                  ? "GIẢM " +
                    v.label.replace(/FREESHIP/gi, "").trim() +
                    (isNaN(Number(v.label.replace(/FREESHIP/gi, "")))
                      ? ""
                      : "K")
                  : v.label}
                <span class="text-white ml-1 font-bold">
                  {v.sub
                    .replace(/FREESHIP\s*[đĐ]0/gi, "FREESHIP")
                    .replace(/^[đĐ]/, "") + (v.sub.match(/^[đĐ]/) ? "₫" : "")}
                </span>
              </span>
            {/each}
          {:else if sortedProductVouchers.length > 0}
            {@const bestV = sortedProductVouchers[0]}
            <span
              class="text-[11px] font-black text-luxury-sakura leading-none flex items-center"
            >
              {bestV.label.toLowerCase().includes("freeship") &&
              bestV.sub.toLowerCase().includes("freeship")
                ? "GIẢM " +
                  bestV.label.replace(/FREESHIP/gi, "").trim() +
                  (isNaN(Number(bestV.label.replace(/FREESHIP/gi, "")))
                    ? ""
                    : "K")
                : bestV.label}
              <span class="text-white ml-1 font-bold">
                {bestV.sub
                  .replace(/FREESHIP\s*[đĐ]0/gi, "FREESHIP")
                  .replace(/^[đĐ]/, "") + (bestV.sub.match(/^[đĐ]/) ? "₫" : "")}
              </span>
            </span>
          {/if}

          {#if sortedProductVouchers.length > 0}
            <button
              type="button"
              onclick={(e) => {
                e.stopPropagation();
                onOpenVouchers(variant.id);
              }}
              class="text-[10px] font-bold text-luxury-sakura hover:underline flex items-center gap-0.5 ml-2 cursor-pointer bg-transparent border-none p-0 focus:outline-none relative z-30"
            >
              Xem thêm
              <ArrowRight
                size={8}
                class="text-luxury-sakura animate-bounce-x"
              />
            </button>
          {/if}
        </div>

        {#if totalSavings > 0}
          <div class="mt-[3px] flex items-center gap-2">
            <div
              class="ultimate-savings-box metallic-shimmer text-[8px] text-black font-black tracking-wider flex items-center gap-1.5 bg-gradient-to-r from-[#FFD700] via-[#FDB931] to-[#FFD700] px-2.5 py-1 rounded-full border border-white/20 shadow-lg transform active:scale-95 transition-all"
            >
              <span
                class="w-1.5 h-1.5 rounded-full bg-red-600 animate-led-red-pulse shadow-[0_0_8px_#ff0000]"
              ></span>
              <EditableWrapper
                path="metadata.offer_savings_prefix"
                type="text"
                label="SỬA TIỀN TỐ"
                class="inline"
                as="span"
              >
                <span>{mkt.savings_prefix}</span>
              </EditableWrapper>
              <span class="tabular-nums">{formatCurrency(totalSavings)}</span>
            </div>

            <!-- 🧧 [ELITE V2.2] LOYALTY REWARD BADGE -->
            <div
              class="flex items-center gap-1.5 bg-luxury-sakura/10 border border-luxury-sakura/30 px-2 py-0.5 rounded-full shadow-[0_0_15px_rgba(255,183,197,0.1)]"
            >
              <Sparkles class="w-2 h-2 text-luxury-sakura animate-pulse" />
              <span
                class="text-[8px] font-black text-luxury-sakura tracking-widest leading-none"
                >+{Math.floor(totalPackagePrice / 100000)} điểm</span
              >
            </div>
          </div>
        {/if}
      </div>

      <p
        class="flex items-center gap-2 text-[8px] font-bold tracking-[0.1em] text-white/40 border-t border-white/5 pt-2"
      >
        <span class="text-luxury-sakura">●</span> SPECS:
        <EditableWrapper
          path="metadata.weight"
          type="text"
          label="SỬA TRỌNG LƯỢNG"
          class="inline"
          as="span"
        >
          {product?.metadata?.weight || "30G"}
        </EditableWrapper>
        <span class="mx-1">-</span>
        <EditableWrapper
          path="metadata.origin"
          type="text"
          label="SỬA XUẤT XỨ"
          class="inline"
          as="span"
        >
          {product?.metadata?.origin || "JAPAN"}
        </EditableWrapper>
        <span class="mx-1">|</span> MÃ VẠCH: {variant.sku ||
          product?.sku ||
          "N/A"}
      </p>

      <ul class="bullet-list space-y-3 mb-6 mt-4">
        {#each features as feature, featureIdx}
          <li class="flex items-start gap-3">
            <span
              class="text-luxury-sakura font-black text-[10px] mt-0.5 shrink-0"
              >✦</span
            >
            <EditableWrapper
              path="variants.{idx}.attributes.features.{featureIdx}"
              type="text"
              label="SỬA ĐẶC TÍNH"
              class="block"
              as="div"
            >
              {#if featureIdx === 0}<h2
                  class="text-[11px] font-black tracking-widest text-white/90 leading-relaxed block"
                >
                  {feature.replace(/^[+!*-]/, "").trim()}
                </h2>{:else}<span
                  class="text-[11px] font-black tracking-widest text-white/90 leading-relaxed block"
                  >{feature.replace(/^[+!*-]/, "").trim()}</span
                >{/if}
            </EditableWrapper>
          </li>
        {/each}
        <li class="flex items-start gap-3">
          <span
            class="text-luxury-sakura font-black text-[10px] mt-0.5 shrink-0"
            >✦</span
          >
          <EditableWrapper
            path="metadata.policy_check_label"
            type="text"
            label="SỬA CAM KẾT 1"
            class="flex-1 block"
            as="div"
          >
            <a
              href="/chinh-sach-kiem-hang.html"
              target="_blank"
              rel="noopener noreferrer"
              class="text-[11px] font-black tracking-widest text-luxury-sakura hover:underline leading-relaxed block w-full"
            >
              {product?.metadata?.policy_check_label ||
                "Kiểm tra hàng trước nhận"}
            </a>
          </EditableWrapper>
        </li>
        <li class="flex items-start gap-3">
          <span
            class="text-luxury-sakura font-black text-[10px] mt-0.5 shrink-0"
            >✦</span
          >
          <EditableWrapper
            path="metadata.policy_return_label"
            type="text"
            label="SỬA CAM KẾT 2"
            class="flex-1 block"
            as="div"
          >
            <a
              href="/chinh-sach-doi-tra-hoan-tien.html"
              target="_blank"
              rel="noopener noreferrer"
              class="text-[11px] font-black tracking-widest text-luxury-sakura hover:underline leading-relaxed block w-full"
            >
              {product?.metadata?.policy_return_label || "Đổi trả 7 ngày"}
            </a>
          </EditableWrapper>
        </li>
        {#if onOpenDetails}
          <li class="flex items-start gap-3">
            <span
              class="text-luxury-sakura font-black text-[10px] mt-0.5 shrink-0"
              >✦</span
            >
            <button
              type="button"
              onclick={(e) => {
                e.stopPropagation();
                onOpenDetails();
              }}
              class="text-[11px] font-black tracking-widest text-luxury-sakura hover:underline leading-relaxed text-left block w-full bg-transparent border-none p-0 cursor-pointer focus:outline-none"
            >
              Xem chi tiết
            </button>
          </li>
        {/if}
      </ul>

      <button
        onclick={handleCheckout}
        disabled={isNavigating}
        class="liquid-cta-viral text-white min-h-[76px] rounded-2xl font-black shadow-2xl relative overflow-hidden flex flex-col items-center justify-center px-5 w-full mt-4 transition-all duration-500 {isCardActive
          ? 'scale-[1.03] ring-2 ring-white/30'
          : ''} {isNavigating
          ? 'opacity-90 saturate-[0.8] cursor-wait'
          : 'cursor-pointer'}"
      >
        {#if isNavigating}
          <div
            class="absolute inset-0 bg-white/10 backdrop-blur-sm z-20 flex items-center justify-center"
          >
            <div
              class="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin"
            ></div>
          </div>
        {/if}
        <div
          class="fomo-header-viral text-[7px] font-black tracking-[0.3em] text-white/60 mb-1 flex items-center justify-center gap-3 w-full"
        >
          <div class="flex items-center gap-1">
            <Zap size={8} class="text-yellow-300/80 fill-yellow-300/80" />
            CHỈ CÒN {displayStock} SUẤT
          </div>
          <span class="w-1 h-1 rounded-full bg-white/20"></span>
          <div class="flex items-center gap-1">
            <Sparkles size={8} class="text-blue-200/80" />
            {shippingVoucher ? "Miễn phí vận chuyển" : "GIAO HÀNG BẢO MẬT"}
          </div>
        </div>

        <div
          class="relative z-10 flex items-center justify-between w-full pointer-events-none"
        >
          <div class="flex items-center gap-3.5 text-left">
            <div
              class="bg-white/15 p-2 rounded-xl backdrop-blur-xl border border-white/10 shadow-[inner_0_1px_1px_rgba(255,255,255,0.2)]"
            >
              <ShoppingCart
                class="w-6 h-6 text-white drop-shadow-md"
                strokeWidth={2}
              />
            </div>
            <div class="flex flex-col justify-center">
              <span
                class="text-[14px] font-black tracking-[0.2em] text-white leading-none mb-1 text-shadow-sm"
              >
                MUA NGAY
              </span>
              <span class="text-[9px] text-white/80 font-bold tracking-[0.1em]">
                Xem chi tiết • {formatCurrency(totalPackagePrice)}
              </span>
            </div>
          </div>
          <div
            class="bg-white/10 p-2 rounded-full border border-white/5 shadow-lg"
          >
            <ArrowRight class="w-3.5 h-3.5 text-white/90 animate-bounce-x" />
          </div>
        </div>
      </button>
    </div>
  </div>

  <!-- 🌙 VOUCHER BOTTOM SHEET (OUTSIDE CONTENT BOX TO FIX CLIPPING) -->
  {#if liveEditStore.openPopoverId === variant.id}
    <div
      class="absolute inset-0 z-[100] {isCardActive
        ? 'scale-[1.03] -translate-y-2'
        : ''} transition-all duration-700 pointer-events-none"
    >
      <OfferVoucherSheet
        {variant}
        {idx}
        {productVouchers}
        voucherSortOrder={shopStore.voucherSortOrder || "none"}
        activeOfferTab={shopStore.activeOfferTab || {}}
        onClose={() => liveEditStore.togglePopover(null)}
        onToggleSort={() => shopStore.toggleVoucherSort()}
        onVoucherClick={(v) => shopStore.toggleVoucher(v.id)}
        onSetTab={(i, tab) => shopStore.setOfferTab(i, tab)}
      />
    </div>
  {/if}
</div>

<style>
  .white-glass-overlay {
    background: rgba(255, 255, 255, 0.16) !important;
    backdrop-filter: blur(32px) saturate(210%) !important;
    -webkit-backdrop-filter: blur(32px) saturate(210%) !important;
    border: 1.5px solid rgba(255, 255, 255, 0.55) !important;
    box-shadow:
      0 16px 40px rgba(0, 0, 0, 0.12),
      inset 0 1.5px 1.5px rgba(255, 255, 255, 0.75) !important;
  }
  .text-viral-gradient {
    background: linear-gradient(to right, #ff1a53, #ff6a1a) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    font-weight: 900 !important;
  }
  @keyframes shimmer-fast {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }
  .animate-shimmer-fast {
    animation: shimmer-fast 3s infinite linear;
  }
</style>
