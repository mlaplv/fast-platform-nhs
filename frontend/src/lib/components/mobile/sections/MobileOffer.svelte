<script lang="ts">
  /**
   * ELITE V2.2 - MOBILE OFFER SECTION (iPhone 18 Aesthetic)
   * TikTok Shop Viral Strategy Implementation.
   * Following R00: NO HARDCODING | SENIOR ARCHITECT STANDARDS.
   */
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';
  import AddressSelector from '$lib/components/mobile/checkout/AddressSelector.svelte';
  import { fomoStore } from '$lib/state/commerce/fomo.svelte';
  import { SHOP_CONFIG, OFFER_CONSTANTS, PRIVACY_CONSTANTS } from '$lib/constants/shop';
  import { resolveMediaUrl } from '$lib/state/utils';
  import type { ProductVariant, Product, Voucher } from '$lib/types';
  import ShoppingCart from "@lucide/svelte/icons/shopping-cart";
  import Check from "@lucide/svelte/icons/check";
  import Gift from "@lucide/svelte/icons/gift";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Flame from "@lucide/svelte/icons/flame";
  import Star from "@lucide/svelte/icons/star";
  import ShoppingBag from "@lucide/svelte/icons/shopping-bag";
  import Info from "@lucide/svelte/icons/info";
  import { formatCurrency } from '$lib/utils/format';
  import { fade, fly, scale } from 'svelte/transition';
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  import { onMount } from 'svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import ShareToUnlockPromoMobile from '$lib/components/storefront/product-detail/shared/ShareToUnlockPromoMobile.svelte';

  interface MobileOfferProps {
    product?: Product;
    onOpenDetails?: () => void;
  }

  interface ExtendedVariant extends ProductVariant {
    image_url?: string;
    imageUrl?: string;
    image?: string;
  }

  // --- Props & State (Runes) ---
  let { product: propProduct, onOpenDetails }: MobileOfferProps = $props();
  const shopStore = getShopStore();
  const cartStore = getCartStore();
  
  const product: Product | null = $derived(
    liveEditStore.isEditMode && liveEditStore.dirtyProduct 
      ? liveEditStore.dirtyProduct 
      : (propProduct || shopStore.product)
  );

  const variants: ProductVariant[] = $derived(product?.variants || []);
  const metadata = $derived((product?.metadata || {}) as Record<string, string | undefined>);

  // Elite V2.2: Unbreakable UI Index Tracking
  let userSelectedIndex = $state<number | null>(null);

  const foundIndex: number = $derived(variants.findIndex(v => {
    if (v.id != null && shopStore.variant?.id != null) return String(v.id) === String(shopStore.variant.id);
    if (v.sku != null && shopStore.variant?.sku != null) return String(v.sku) === String(shopStore.variant.sku);
    return v === shopStore.variant;
  }));

  const selectedIndex: number = $derived(
    userSelectedIndex !== null 
      ? userSelectedIndex 
      : (foundIndex !== -1 ? foundIndex : 0)
  );
  const selectedVariant: ProductVariant | null = $derived(variants[selectedIndex] ?? variants[0] ?? null);

  const h1: string = $derived(
    metadata.offer_headline_1 || (product?.name ? product.name.split(' ')[0] : "Siêu ưu đãi")
  );
  const h2: string = $derived(
    metadata.offer_headline_2 || (product?.name ? product.name.split(' ').slice(1).join(' ') : "độc quyền")
  );

  const variantImages = $derived(variants.map((v, i) => {
    const ev = v as ExtendedVariant;
    const tierVar = product?.tierVariations?.[0] || product?.tier_variations?.[0];
    const optIdx = v.tierIndex?.[0] ?? v.tier_index?.[0] ?? i;
    const mobImg = tierVar?.mobile_images?.[optIdx] || tierVar?.mobileImages?.[optIdx];
    const deskImg = tierVar?.images?.[optIdx];
    return resolveMediaUrl(
      ev.image_url || ev.imageUrl || ev.image || 
      mobImg || deskImg ||
      (product?.images && product.images[i]) || 
      (product?.images && product.images[0])
    );
  }));

  // Elite V2.2: Secure Viral State (Reactive Sync)
  let isViralUnlocked = $state(false);
  
  $effect(() => {
    if (product?.id && typeof window !== 'undefined') {
      isViralUnlocked = localStorage.getItem(`viral_unlocked_${product.id}`) !== null;
    }
  });

  // Elite V2.2: Auto-apply viral voucher upon unlock for instant premium feeling
  $effect(() => {
    if (isViralUnlocked && product?.id) {
      const saved = localStorage.getItem(`viral_unlocked_${product.id}`);
      if (saved) {
        try {
          const data = JSON.parse(saved);
          if (data.code && !shopStore.selectedVoucherIds.includes(data.code)) {
            shopStore.toggleVoucher(data.code);
          }
        } catch (e) {
          // Silent safe fail
        }
      }
    }
  });

  const getVoucherValue = (v: any) => {
    let rawVal = typeof v.value === 'number' ? v.value : 0;
    const subText = String(v.sub || "").toLowerCase();
    const labelText = String(v.label || "").toLowerCase();

    const productPrice = selectedVariant?.discountPrice || selectedVariant?.price || product?.price || 0;

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

  const productVouchers = $derived.by(() => {
    const rawVouchers = (cartStore.vouchers && cartStore.vouchers.length > 0 ? cartStore.vouchers : []) as Voucher[];

    let list = rawVouchers.map((v) => ({
      id: v.id,
      label: v.title || v.id || 'ƯU ĐÃI',
      sub: v.type === 'SHIPPING' ? 'Miễn phí vận chuyển' : (v.type === 'PERCENT' ? `GIẢM ${v.value}%` : `GIẢM ${formatCurrency(v.value || 0)}`),
      type: v.type === 'SHIPPING' ? 'ship' : 'discount',
      value: v.value || 0,
      type_raw: v.type
    }));

    const cleanString = (s: string) => {
      return (s || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toUpperCase();
    };

    const isViralVoucher = (v: { id: string; label?: string }) => {
      const cleanId = cleanString(v.id);
      const cleanLabel = cleanString(v.label);
      return cleanId.includes('VIRAL') || 
             cleanId.includes('LAN TOA') || 
             cleanLabel.includes('VIRAL') || 
             cleanLabel.includes('LAN TOA');
    };

    // Elite V2.2 Re-injection: Phục hồi voucher từ session local nếu đã mở khóa
    if (typeof window !== 'undefined' && isViralUnlocked && product?.id) {
      const saved = localStorage.getItem(`viral_unlocked_${product.id}`);
      if (saved) {
        try {
          const data = JSON.parse(saved);
          // Filter out existing viral vouchers to prevent duplicates or wrong positions
          list = list.filter(v => !isViralVoucher(v) && v.id !== data.code);
          // Prepend at the absolute top (Position #1)
          list.unshift({
            id: data.code,
            label: data.label || 'VOUCHER LAN TỎA',
            sub: 'Đã mở khóa từ chiến dịch',
            type: 'discount',
            value: 79000,
            type_raw: 'FIXED'
          });
        } catch (e) {}
      }
    }

    // Sort by value descending (Giá giảm dần)
    const sorted = [...list].sort((a, b) => {
      const valA = getVoucherValue(a);
      const valB = getVoucherValue(b);
      return valB - valA;
    });

    // Grouping by type:
    // 1. Viral/Độc quyền Vouchers always at the absolute top
    const viralVouchers = sorted.filter(v => isViralVoucher(v));
    // 2. Regular discount vouchers
    const regularDiscount = sorted.filter(v => !isViralVoucher(v) && v.type === 'discount');
    // 3. Regular shipping vouchers
    const regularShipping = sorted.filter(v => !isViralVoucher(v) && v.type === 'ship');

    return [...viralVouchers, ...regularDiscount, ...regularShipping];
  });

  // --- FOMO Simulation (Elite V2.2) ---
  // Elite V2.2: Synchronized FOMO Metrics
  const viralViewers = $derived(fomoStore.viewers);
  
  onMount(() => {
    if (product?.slug) {
      fomoStore.init(product.slug);
    }
    return () => {
      fomoStore.dispose();
    };
  });

  function getVariantTitle(v: ProductVariant): string {
    if (!product?.tierVariations?.length || !v.tierIndex?.length) return v.sku || 'Combo';
    return v.tierIndex.map((optIdx: number, tierIdx: number) => {
      const option = product.tierVariations![tierIdx]?.options[optIdx] as string | { name?: string; label?: string } | undefined;
      return typeof option === 'string' ? option : (typeof option === 'object' && option ? (option.name || option.label || '') : '');
    }).filter(Boolean).join(' - ') || v.sku || 'Combo';
  }

  const handleSelect = (i: number) => {
    const v = variants[i];
    if (v) {
      userSelectedIndex = i;
      shopStore.selectVariant(v);
    }
  };

  function handleVoucherClick(v: Voucher | { id: string }) {
    if (v.id) {
      shopStore.toggleVoucher(v.id);
    }
  }

  const noiseSvg = `data:image/svg+xml,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noiseFilter)"/%3E%3C/svg%3E`;

  // 🚀 SYNC CLOUD VOUCHERS TO FUNNEL STORE (Elite V2.2)
  function resolveGiftUrl(slug: string): string {
    if (!slug) return '';
    if (slug.startsWith('http://') || slug.startsWith('https://')) return slug;
    const cleanSlug = slug.startsWith('/') ? slug.slice(1) : slug;
    return `/${cleanSlug}`;
  }
</script>

<div class="h-full w-full container flex flex-col !px-0 !max-w-none pt-[var(--mobile-top-space)] pb-[var(--mobile-bottom-space)] relative overflow-hidden bg-black text-white">
  <!-- 🌊 Premium Ambient Liquid Background -->
  <div class="absolute inset-0 pointer-events-none overflow-hidden">
    <div class="absolute top-[-10%] left-[-10%] w-[120%] h-[120%] opacity-40">
      <div class="absolute top-[20%] right-[-10%] w-[70%] h-[70%] rounded-full bg-[#FFB7C5]/10 blur-[120px] animate-[pulse_8s_infinite]"></div>
      <div class="absolute bottom-[10%] left-[-20%] w-[80%] h-[80%] rounded-full bg-[#E8D5B0]/5 blur-[140px] animate-[pulse_12s_infinite_reverse]"></div>
      <div class="absolute top-[40%] left-[10%] w-[40%] h-[40%] rounded-full bg-[#FFB7C5]/10 blur-[100px] animate-pulse"></div>
    </div>
    <div class="absolute inset-0 opacity-[0.03] mix-blend-overlay pointer-events-none" style="background-image: url('{noiseSvg}')"></div>
  </div>

  <!-- 🚀 COMPACT HEADER -->
  <div class="mt-4 mb-2 text-center w-full !px-4 z-surface shrink-0">
    <div class="flex items-center justify-center gap-2 mb-2" in:fly={{ y: -10 }}>
       <div class="bg-[#FFB7C5]/20 backdrop-blur-md border border-[#FFB7C5]/30 rounded-full px-3 py-0.5 flex items-center gap-2">
          <div class="w-1 h-1 rounded-full bg-[#FFB7C5] animate-pulse shadow-[0_0_8px_rgba(255,183,197,0.8)]"></div>
          <span class="offer-status-label text-[9px] font-bold text-white/90 tracking-tight italic">
            <span class="text-[#FFB7C5]">{viralViewers.toLocaleString()}</span> 
            <EditableWrapper path="metadata.offer_viewers_suffix" type="text" label="SỬA NHÃN" class="inline" as="span">
              {metadata.offer_viewers_suffix || 'đang xem'}
            </EditableWrapper>
          </span>
       </div>
    </div>

    <h3 class="text-3xl font-black text-center italic tracking-tighter leading-tight mb-2">
      <span class="bg-clip-text text-transparent bg-gradient-to-br from-white via-white to-white/40">
        <EditableWrapper path="metadata.offer_headline_1" type="text" label="SỬA TIÊU ĐỀ 1" class="inline" as="span">{h1}</EditableWrapper>
      </span>
      <br/>
      <span class="bg-clip-text text-transparent bg-gradient-to-br from-[#FFB7C5] via-[#E8D5B0] to-white drop-shadow-[0_0_20px_rgba(255,183,197,0.5)]">
        <EditableWrapper path="metadata.offer_headline_2" type="text" label="SỬA TIÊU ĐỀ 2" class="inline" as="span">{h2}</EditableWrapper>
      </span>
    </h3>

    <div class="flex items-center justify-center gap-4 mt-2">
        <div class="flex items-center gap-1.5">
           <ShoppingBag class="w-2.5 h-2.5 text-[#FFB7C5]" />
           <EditableWrapper path="metadata.offer_sales_label" type="text" label="SỬA NHÃN BÁN HÀNG" class="inline" as="span">
             <span class="offer-meta-label text-[10px] text-white/40 font-bold tracking-widest italic">{(fomoStore.totalSales || product?.orderCount || 0).toLocaleString()} {metadata.offer_sales_label || 'đã bán'}</span>
           </EditableWrapper>
        </div>
        {#if product?.metadata?.reviews_trust_score}
        <div class="flex items-center gap-1.5">
           <Star class="w-2.5 h-2.5 text-amber-400 fill-amber-400" />
           <EditableWrapper path="metadata.offer_rating_label" type="text" label="SỬA NHÃN RATING" class="inline" as="span">
             <span class="offer-meta-label text-[10px] text-white/40 font-bold tracking-widest italic">{product.metadata.reviews_trust_score.toFixed(1)}/5 ({product.metadata.review_count || 0} đánh giá)</span>
           </EditableWrapper>
        </div>
        {/if}
    </div>
  </div>

  <!-- 📜 MAIN SCROLLABLE CONTENT -->
  <div class="flex-1 flex flex-col z-[var(--z-surface)] overflow-y-auto no-scrollbar pb-10 !px-0 gap-2">
    <!-- 🔥 Viral Share Bar (Inline variant for Funnel) -->
    {#if product}
      <div class="px-4">
        {#key product.id}
          <ShareToUnlockPromoMobile
            product={product}
            variant="funnel"
            onUnlock={() => isViralUnlocked = true}
          />
        {/key}
      </div>
    {/if}
    <!-- 🎛️ VARIANT SELECTOR -->
    <div class="flex flex-col">
      {#each variants as variant, i (variant.id || i)}
         {@const cQty = variant.attributes?.combo_qty || 1}
         {@const priceData = shopStore.calculateAdjustedPrice(variant, 1)}
         {@const vPrice = priceData.final}
         {@const isActive = selectedIndex === i}
         {@const variantTitle = getVariantTitle(variant)}
         {@const resolvedGifts = variant.attributes?.gifts?.length ? variant.attributes.gifts : variant?.gifts?.length ? variant.gifts : product?.gifts || []}
         
           <div 
            role="button"
            tabindex="0"
            onclick={() => handleSelect(i)}
            onkeydown={(e) => e.key === 'Enter' && handleSelect(i)}
            class="relative w-full text-left transition-all duration-500 h-[125px] flex items-center overflow-hidden cursor-pointer {isActive ? 'bg-white/[0.08] border-b border-white/20 z-10' : 'bg-transparent border-b border-white/5 opacity-40'}"
          >
             <div class="absolute inset-0 bg-gradient-to-r from-[#FFB7C5]/15 via-transparent to-[#E8D5B0]/10 pointer-events-none transition-opacity duration-500 {isActive ? 'opacity-100' : 'opacity-0'}"></div>
             
             <!-- 🖼️ FULL HEIGHT EDGE IMAGE -->
             <div class="w-[100px] h-full shrink-0 relative bg-white/5 overflow-hidden">
                {#if variantImages[i]}
                  <img 
                    src={variantImages[i]} 
                    alt="{product?.name ? product.name + ' - ' : ''}{getVariantTitle(variant)}" 
                    loading="lazy"
                    decoding="async"
                    width="100"
                    height="125"
                    class="w-full h-full object-cover transition-all {isActive ? 'brightness-110' : 'grayscale-[40%]'}" 
                  />
                {:else}
                   <div class="w-full h-full flex items-center justify-center">
                      <ShoppingCart class="w-8 h-8 text-white/5" />
                   </div>
                {/if}
                <div class="absolute inset-0 ring-4 ring-inset ring-[#FFB7C5]/20 shadow-[inset_0_0_40px_rgba(255,183,197,0.2)] transition-opacity duration-500 {isActive ? 'opacity-100' : 'opacity-0'}"></div>
             </div>

             <div class="flex-1 flex flex-col justify-center px-5 py-2 min-w-0">
                <div class="flex items-center gap-2 mb-1.5">
                   {#if i === 1}
                      <div class="offer-badge best-seller bg-gradient-to-r from-amber-400 to-orange-500 text-black px-1.5 py-0.5 rounded-sm font-bold text-[10px] tracking-widest flex items-center gap-1 shadow-md shadow-amber-500/10">
                        <Flame class="w-3 h-3 fill-black" /> Bán chạy
                      </div>
                   {/if}
                   {#if cQty > 1}
                      <div class="offer-badge combo-badge bg-[#FFB7C5]/10 border border-[#FFB7C5]/30 text-[#FFB7C5] px-1.5 py-0.5 rounded-sm font-bold text-[10px] tracking-widest">Combo x{cQty}</div>
                   {/if}
                </div>

                <span class="variant-title font-black tracking-tight italic text-[18px] leading-tight transition-all truncate {isActive ? 'text-white drop-shadow-md' : 'text-white/40'}">{getVariantTitle(variant)}</span>
                
                <div class="flex flex-col mt-0.5 w-full">
                    <div class="flex items-baseline gap-2">
                       <span class="font-black text-[20px] italic tracking-tighter leading-none transition-colors duration-300 {isActive ? 'text-[#FFB7C5]' : 'text-[#FFB7C5]/40'}">{formatCurrency(vPrice)}</span>
                       {#if variant.price > vPrice}
                         <span class="text-[12px] text-white/20 line-through font-bold">{formatCurrency(variant.price)}</span>
                       {/if}
                    </div>
                    
                    <div class="flex items-center gap-1.5 mt-1.5 w-full flex-wrap">
                       <div class="flex items-center gap-1 bg-[#FFB7C5]/10 border border-[#FFB7C5]/20 px-1.5 py-0.5 rounded-full w-fit shrink-0 transition-all duration-300 transform-gpu origin-left {isActive ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}">
                          <Sparkles class="w-2 h-2 text-[#FFB7C5] {isActive ? 'animate-pulse' : ''}" />
                          <span class="offer-points-label text-[8.5px] font-bold text-[#FFB7C5] tracking-widest whitespace-nowrap">+{Math.floor(vPrice / 100000)} điểm</span>
                       </div>
                       {#if resolvedGifts.length > 0}
                          {#if resolvedGifts[0].slug}
                             <a 
                               href={resolveGiftUrl(resolvedGifts[0].slug)} 
                               onclick={(e) => e.stopPropagation()} 
                               class="flex items-center gap-1 bg-[#FFB7C5]/10 border border-[#FFB7C5]/20 backdrop-blur-md pl-0.5 pr-1.5 py-0.5 rounded-full shadow-[0_0_10px_rgba(255,183,197,0.1)] shrink-0 transition-all duration-300 hover:bg-[#FFB7C5]/20 hover:border-[#FFB7C5]/40 {isActive ? 'opacity-100' : 'opacity-50'}"
                               style="text-decoration: none;"
                             >
                                <div class="w-3.5 h-3.5 rounded-full overflow-hidden bg-white/80 shrink-0 flex items-center justify-center relative">
                                   {#if resolvedGifts[0].image && resolvedGifts[0].image !== "/uploads/img/osmo/sp1.png"}
                                      <img src={resolveMediaUrl(resolvedGifts[0].image)} alt={resolvedGifts[0].name} class="w-full h-full object-cover" />
                                   {:else}
                                      <img src={resolveMediaUrl(product?.images?.[0] || '')} alt={resolvedGifts[0].name} class="w-full h-full object-cover mix-blend-multiply" />
                                   {/if}
                                </div>
                                <span class="text-[8.5px] font-bold text-white/90 truncate max-w-[95px] leading-none tracking-tight drop-shadow-sm" style="text-transform: none;">
                                  Tặng {resolvedGifts[0].name}
                                  <span class="inline-block text-[6px] font-black text-[#FFB7C5] bg-[#FFB7C5]/10 border border-[#FFB7C5]/20 px-1 rounded uppercase tracking-wider ml-0.5">Xem</span>
                                </span>
                                <span class="text-[8px] font-black text-[#FFB7C5] leading-none drop-shadow-[0_0_5px_rgba(255,183,197,0.5)]">x{resolvedGifts[0].qty || resolvedGifts[0].quantity || 1}</span>
                             </a>
                          {:else}
                             <div class="flex items-center gap-1 bg-[#FFB7C5]/10 border border-[#FFB7C5]/20 backdrop-blur-md pl-0.5 pr-1.5 py-0.5 rounded-full shadow-[0_0_10px_rgba(255,183,197,0.1)] shrink-0 transition-all duration-300 {isActive ? 'opacity-100' : 'opacity-50'}">
                                <div class="w-3.5 h-3.5 rounded-full overflow-hidden bg-white/80 shrink-0 flex items-center justify-center">
                                   {#if resolvedGifts[0].image && resolvedGifts[0].image !== "/uploads/img/osmo/sp1.png"}
                                      <img src={resolveMediaUrl(resolvedGifts[0].image)} alt={resolvedGifts[0].name} class="w-full h-full object-cover" />
                                   {:else}
                                      <img src={resolveMediaUrl(product?.images?.[0] || '')} alt={resolvedGifts[0].name} class="w-full h-full object-cover mix-blend-multiply" />
                                   {/if}
                                </div>
                                <span class="text-[8.5px] font-bold text-white/90 truncate max-w-[95px] leading-none tracking-tight drop-shadow-sm" style="text-transform: none;">Tặng {resolvedGifts[0].name}</span>
                                <span class="text-[8px] font-black text-[#FFB7C5] leading-none drop-shadow-[0_0_5px_rgba(255,183,197,0.5)]">x{resolvedGifts[0].qty || resolvedGifts[0].quantity || 1}</span>
                             </div>
                          {/if}
                       {/if}
                    </div>
                </div>

                <div class="w-full h-1 bg-white/5 rounded-full mt-2.5 overflow-hidden shadow-inner transition-opacity duration-300 {isActive ? 'opacity-100' : 'opacity-0'}">
                   <div class="h-full bg-[#FFB7C5] shadow-[0_0_15px_rgba(255,183,197,0.8)] transition-all duration-700 ease-out" style="width: {isActive ? Math.max(10, 90 - (i * 20)) : 0}%"></div>
                </div>
             </div>
             
             <!-- ℹ️ VIEW DETAILS BUTTON (Viral iOS Style) -->
             <button 
               class="absolute right-4 top-4 flex flex-col items-center gap-1 group/info active:scale-95 transition-all z-20"
               onclick={(e) => {
                 e.stopPropagation();
                 if (onOpenDetails) onOpenDetails();
               }}
             >
                <div class="w-6 h-6 rounded-full border border-white/40 flex items-center justify-center group-hover/info:border-white transition-colors">
                   <Info class="w-3.5 h-3.5 text-white/60 group-hover/info:text-white" />
                </div>
                <span class="offer-info-label text-[10px] font-bold text-white/30 tracking-widest group-hover/info:text-white/60">Chi tiết</span>
             </button>


          </div>
       {/each}
    </div>



     <!-- 🎫 PIXEL-PERFECT VOUCHER 1:1 (Redemption Version) -->
     {#if productVouchers.length > 0}
     {@const sortedVouchers = [...productVouchers].sort((a, b) => {
         const aApplied = shopStore.selectedVoucherIds.includes(a.id);
         const bApplied = shopStore.selectedVoucherIds.includes(b.id);
         if (aApplied && !bApplied) return -1;
         if (!aApplied && bApplied) return 1;
         const valA = getVoucherValue(a); const valB = getVoucherValue(b); return valB - valA;
     })}
     <div class="px-4 mt-4 mb-2 z-surface shrink-0" in:fade>
        <div class="flex items-center justify-between mb-1.5 px-1">
           <span class="text-[10px] font-black text-white/30 tracking-[0.2em] italic flex items-center gap-2">
              Mã giảm giá ưu đãi
           </span>
        </div>
       <div class="flex flex-row gap-2 overflow-x-auto no-scrollbar pt-4 pb-2 -mx-4 px-3">
          {#each sortedVouchers as v}
             {@const isApplied = shopStore.selectedVoucherIds.includes(v.id)}
             <button 
               onclick={() => handleVoucherClick(v)}
               class="flex-shrink-0 relative w-fit min-w-[120px] h-[60px] transition-all duration-300 transform active:scale-[0.97] overflow-visible group"
             >
                <!-- 📦 Postage Stamp Body (Advanced Composite Mask) -->
                <div 
                  class="flex h-full w-full relative overflow-visible shadow-xl transition-all duration-500 {isApplied ? 'scale-105 rotate-[1.5deg] z-20' : 'opacity-95 hover:opacity-100 hover:scale-[1.02]'}"
                  style="
                    background: linear-gradient(135deg, #FFB7C5 0%, #E8D5B0 100%);
                    --r: 6px;
                    --s: 16px;
                    -webkit-mask: 
                      radial-gradient(var(--r) at var(--r) 50%, #0000 98%, #000) calc(-1 * var(--r)) 50% / 100% var(--s),
                      radial-gradient(var(--r) at 50% var(--r), #0000 98%, #000) 50% calc(-1 * var(--r)) / var(--s) 100%;
                    mask: 
                      radial-gradient(var(--r) at var(--r) 50%, #0000 98%, #000) calc(-1 * var(--r)) 50% / 100% var(--s),
                      radial-gradient(var(--r) at 50% var(--r), #0000 98%, #000) 50% calc(-1 * var(--r)) / var(--s) 100%;
                    -webkit-mask-composite: destination-in;
                    mask-composite: intersect;
                  "
                >
                   <!-- 📝 Content (Stamp Center) -->
                   <div class="flex-1 flex flex-col items-center justify-center px-4 py-1.5 min-w-0 bg-white/20 backdrop-blur-[2px] m-1 border border-black/5">
                      <div class="flex flex-col items-center justify-center leading-none">
                         <span class="text-[14px] font-[1000] text-[#111111] tracking-tighter whitespace-nowrap drop-shadow-sm">{v.label}</span>
                      </div>
                      
                      <!-- 🖋️ Postage Mark Detail -->
                      <div class="absolute top-1 right-2 opacity-30 rotate-12">
                         <Sparkles class="w-3.5 h-3.5 text-black" />
                      </div>
                      <div class="absolute bottom-1.5 left-3 opacity-10 font-[serif] text-[7px] font-bold tracking-widest text-black">Miccosmo Elite</div>
                   </div>
                </div>

                <!-- ✅ Stick Badge (Postage Seal Style) - MOVED OUTSIDE MASKED CONTAINER -->
                {#if isApplied}
                   <div class="absolute -top-[6px] -right-[6px] w-[28px] h-[28px] rounded-full bg-[#FFB7C5] shadow-2xl border-2 border-white flex items-center justify-center z-30" in:scale>
                      <Check class="w-4 h-4 text-black stroke-[4]" />
                   </div>
                {/if}
             </button>
          {/each}
       </div>
    </div>
    {/if}
  </div>
  
  <!-- 🛰️ CTA HUD -->
  <div class="mt-auto pt-2 pb-2 relative bg-gradient-to-t from-black via-black/95 to-transparent shrink-0" style="z-index: {Z_INDEX_CLIENT.OVERLAY};">

      <div class="px-3 pb-2">
        <button
           onclick={() => { 
             if (!selectedVariant) return;
             shopStore.openCheckout(cartStore, product as Product); 
           }}
           class="w-full h-[70px] rounded-[2rem] font-black text-[15px] tracking-[0.1em] flex items-center justify-center transition-all duration-700 italic active:scale-95 bg-white/10 backdrop-blur-3xl border border-white/20 shadow-2xl relative group overflow-hidden pointer-events-auto cursor-pointer"
         >
           <div class="absolute inset-0 bg-gradient-to-r from-[#FFB7C5]/20 via-transparent to-[#FFB7C5]/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
           <div class="relative z-10 flex items-center justify-between w-full px-4 gap-2">
              <div class="flex flex-col text-left leading-tight">
                <span class="cta-selection-label text-white text-[11px] font-black italic">Chọn combo x{shopStore.variant?.attributes?.combo_qty || 1}</span>
                <div class="flex items-center gap-1.5 mt-0.5">
                   <span class="cta-points-label text-[9px] text-[#FFB7C5] font-bold tracking-widest bg-[#FFB7C5]/10 px-1.5 py-0.5 rounded-full border border-[#FFB7C5]/20 whitespace-nowrap">Tích +{Math.floor(shopStore.totalAmount / 100000)} điểm</span>
                   <EditableWrapper path="metadata.offer_shipping_label" type="text" label="SỬA NHÃN SHIP" class="inline" as="span">
                     <span class="cta-ship-label text-[10px] text-white/30 font-bold tracking-widest italic">• {metadata.offer_shipping_label || 'Freeship'}</span>
                   </EditableWrapper>
                </div>
              </div>
              <div class="flex items-center gap-3 ml-auto">
                 <div class="flex flex-col items-end leading-none">
                    {#if (shopStore.originalPrice * shopStore.quantity) > shopStore.totalAmount}
                      <span class="text-[9px] text-white/20 line-through font-bold">{formatCurrency(shopStore.originalPrice * shopStore.quantity)}</span>
                    {/if}
                    <span class="text-[#FFB7C5] text-[20px] font-black drop-shadow-[0_0_10px_rgba(255,183,197,0.4)]">{formatCurrency(shopStore.totalAmount)}</span>
                 </div>
                 <div class="w-10 h-10 rounded-2xl bg-[#FFB7C5]/20 flex items-center justify-center border border-[#FFB7C5]/30">
                    <ShoppingCart class="w-5 h-5 text-[#FFB7C5]" />
                 </div>
              </div>
           </div>
        </button>
      </div>
  </div>
</div>

<style>
  .no-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .no-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }

  /* Elite V2.2: Offer Sentence-Case Fix */
  .offer-status-label, .offer-meta-label, .variant-title, 
  .offer-gift-label, .offer-info-label, .voucher-sub-label,
  .cta-selection-label, .cta-ship-label {
    text-transform: lowercase;
    display: inline-block;
  }
  .offer-status-label::first-letter, .offer-meta-label::first-letter, 
  .variant-title::first-letter, .offer-gift-label::first-letter, 
  .offer-info-label::first-letter, .voucher-sub-label::first-letter, .cta-selection-label::first-letter, 
  .cta-ship-label::first-letter {
    text-transform: uppercase;
  }
</style>
