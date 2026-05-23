<script lang="ts">
  import { onMount } from 'svelte';
  import ChevronLeft from "@lucide/svelte/icons/chevron-left";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import Zap from "@lucide/svelte/icons/zap";
  import Bookmark from "@lucide/svelte/icons/bookmark";
  import Gift from "@lucide/svelte/icons/gift";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Package from "@lucide/svelte/icons/package";
  import Volume2 from "@lucide/svelte/icons/volume-2";
  import VolumeX from "@lucide/svelte/icons/volume-x";
  import Heart from "@lucide/svelte/icons/heart";
  
  import { wishlistStore } from '$lib/state/commerce/wishlist.svelte';
  
  // Types
  import type { Product, ProductVariant, ReviewStats } from '$lib/types';
  
  // State & Stores
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte';
  
  // Utils
  import { resolveMediaUrl } from '$lib/state/utils';
  import { formatCurrency, formatNumber } from '$lib/utils/format';
  
  // Components
  import ViralShareBarMobile from '../../shared/ViralShareBarMobile.svelte';
  import ShareToUnlockPromoMobile from '../../shared/ShareToUnlockPromoMobile.svelte';
  import ProductMobileMedia from './ProductMobileMedia.svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';

  /** Detect video URL: mp4, webm, mov, ogg … (mirrored from Desktop) */
  function isVideoUrl(url: string | undefined | null): boolean {
    if (!url) return false;
    const clean = url.split('?')[0].toLowerCase();
    return /\.(mp4|webm|mov|ogg|ogv|avi|mkv)$/.test(clean);
  }
  
  interface Props {
    product: Product;
    timeLeft: { hours: number; minutes: number; seconds: number };
    selectedVariant?: ProductVariant | null;
    selectedQty?: number;
    onOpenSelector?: () => void;
    stats?: import('$lib/types').ReviewStats | null;
    isViralUnlocked?: boolean;
    isScrolled?: boolean;
    isHidden?: boolean;
    scrollRatio?: number;
    hideRatio?: number;
    onTriggerScan?: () => void;
  }

  let { 
    product, timeLeft, selectedVariant, selectedQty = 1, 
    onOpenSelector, stats, isViralUnlocked = $bindable(), 
    isScrolled = false, isHidden = false, 
    scrollRatio = 0, hideRatio = 0,
    onTriggerScan
  }: Props = $props();
  const cartStore = getCartStore();
  const clientUi = getClientUi();

  // --- LIKE / BOOKMARK STATE ---
  let likeAnimating = $state(false);
  const isLiked = $derived(wishlistStore.isLiked(product.id));
  const baseLikeCount = $derived(Number(product.metadata?.viral_suite?.likes_count || product.metadata?.likes || 0));
  const likeCount = $derived(baseLikeCount + (isLiked ? 1 : 0));

  function toggleLike() {
    const wasLiked = isLiked;
    wishlistStore.toggle(product.id);
    
    if (!wasLiked) {
      clientUi.showToast('Đã thêm sản phẩm vào mục Yêu thích', 'success');
      likeAnimating = true;
      setTimeout(() => { likeAnimating = false; }, 300);
    }
  }

  // --- FLASH SALE CONDITIONAL ---
  const flashSaleEnd = $derived(
    product.metadata?.flash_sale_end
      ? new Date(product.metadata.flash_sale_end).getTime()
      : null
  );
  const isFlashSaleActive = $derived(
    flashSaleEnd !== null && flashSaleEnd > Date.now()
  );

  const pVariants = $derived((product.variants || []).filter(v => v.attributes?.is_active !== false));
  const variations = $derived(product.tier_variations || product.tierVariations || product.attributes?.tier_variations || product.metadata?.tier_variations || []);

  // Helper to check if a specific option is active
  function isOptionActive(tIdx: number, oIdx: number): boolean {
    const rawVariants = product.variants || [];
    if (variations.length === 1) {
      const v = rawVariants.find(x => {
        const idxs = x.tierIndex || x.tier_index || [];
        return idxs[0] === oIdx;
      });
      return v?.attributes?.is_active !== false;
    }
    return rawVariants.some(x => {
      const idxs = x.tierIndex || x.tier_index || [];
      return idxs[tIdx] === oIdx && x.attributes?.is_active !== false;
    });
  }

  // Carousel State
  let activeImageIndex = $state(0);
  let carouselRef: HTMLElement | null = $state(null);

  // ─── Shopee-style Video State (Mobile) ───────────────────────────
  let videoEl = $state<HTMLVideoElement | null>(null);
  let videoMuted = $state(true);

  const videoStartTime = $derived(
    typeof product.metadata?.video_start_time === 'number'
      ? product.metadata.video_start_time
      : 0
  );
  const videoEndTime = $derived(
    typeof product.metadata?.video_end_time === 'number'
      ? product.metadata.video_end_time
      : null
  );

  function handleTimeUpdate() {
    if (!videoEl) return;
    if (videoEndTime !== null && videoEl.currentTime >= videoEndTime) {
      videoEl.currentTime = videoStartTime;
      videoEl.play().catch(() => {});
    }
  }

  /** Auto-play video when carousel scrolls to a video slide */
  $effect(() => {
    const currentUrl = displayImages[activeImageIndex];
    if (videoEl && isVideoUrl(currentUrl)) {
      videoEl.load();
      videoEl.muted = videoMuted;
      const onMeta = () => {
        if (videoEl) {
          videoEl.currentTime = videoStartTime;
          videoEl.play().catch(() => {});
        }
      };
      videoEl.addEventListener('loadedmetadata', onMeta, { once: true });
      return () => videoEl?.removeEventListener('loadedmetadata', onMeta);
    }
  });

  function toggleMute() {
    videoMuted = !videoMuted;
    if (videoEl) videoEl.muted = videoMuted;
  }
  
  // Voucher State
  let vouchersListRef: HTMLElement | null = $state(null);
  let isAtStart = $state(true);
  let isAtEnd = $state(false);
  let selectedVouchers = $state<string[]>([]);
  
  let mounted = $state(false);
  onMount(() => { mounted = true; });

  function triggerViralFly() {
    isViralUnlocked = true;
  }

  function formatCount(count: number): string {
    if (count >= 1000) return (count / 1000).toFixed(1).replace('.0', '') + 'k';
    return count.toString();
  }

  const formatPrice = (p: number) => p.toLocaleString('vi-VN');
  
  const displayImages = $derived(product.images?.length > 0 ? product.images : [product.images?.[0] || '']);
  
  const vouchers = $derived.by(() => {
    const list: Array<{ id: string; label: string; sub: string; type: string }> = 
      Array.isArray(product.metadata?.vouchers) && product.metadata.vouchers.length > 0
        ? product.metadata.vouchers
        : cartStore.vouchers
            .filter(v => {
              const applicableIds = v.metadata_json?.applicable_product_ids || [];
              if (applicableIds && applicableIds.length > 0) {
                return applicableIds.includes(product.id);
              }
              return true;
            })
            .map(v => ({
              id: v.id,
              label: v.title || v.id,
              sub: v.subtitle || (v.type === 'SHIPPING' ? 'Miễn phí vận chuyển' : `Giảm ${formatCurrency(v.value)}`),
              type: (v.type === 'SHIPPING' || v.type === 'ship') ? 'ship' : 'discount'
            }));

    const cleanString = (s: string) => {
      return (s || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toUpperCase();
    };

    const isViralVoucher = (v: { id: string; label?: string }) => {
      const promoVId = product.metadata?.share_promotion?.voucher_id;
      const cleanId = cleanString(v.id);
      const cleanLabel = cleanString(v.label);
      return cleanId.includes('VIRAL') || 
             cleanId.includes('LAN TOA') || 
             cleanLabel.includes('VIRAL') || 
             cleanLabel.includes('LAN TOA') ||
             (promoVId && v.id === promoVId);
    };

    let vouchersList = list.filter((v: { id: string; label?: string }) => {
      if (!mounted) return !isViralVoucher(v);
      return !isViralVoucher(v) || isViralUnlocked;
    });

    if (mounted && isViralUnlocked) {
      const saved = localStorage.getItem(`viral_unlocked_${product.id}`);
      if (saved) {
        try {
          const data = JSON.parse(saved);
          // Filter out existing viral vouchers to prevent duplicates or wrong positions
          vouchersList = vouchersList.filter(v => !isViralVoucher(v) && v.id !== data.code);
          // Prepend at the absolute top (Position #1)
          vouchersList.unshift({
            id: data.code,
            label: data.label || 'Voucher lan tỏa',
            sub: 'Đã mở khóa từ chiến dịch',
            type: 'discount'
          });
        } catch (e) {}
      }
    }

    // VOUCHER LAN TỎA 79K: LUỐN Ở VỊ TRÍ SỐ 1
    const viralVouchers = vouchersList.filter(v => isViralVoucher(v));
    const regularVouchers = vouchersList.filter(v => !isViralVoucher(v));

    return [...viralVouchers, ...regularVouchers];
  });

  const activeVariant = $derived(selectedVariant || pVariants?.[0]);
  
  const effectiveUnitPrice = $derived.by(() => {
    const v = activeVariant;
    if (!v) return product.discountPrice || product.discount_price || product.price || 0;
    
    const comboVariants = pVariants.filter(cv => cv.attributes && cv.attributes.combo_qty);
    const qty = selectedQty;
    
    if (comboVariants.length > 0) {
      const sortedTiers = [...comboVariants].sort((a, b) => Number(b.attributes.combo_qty) - Number(a.attributes.combo_qty));
      const bestTier = sortedTiers.find(t => Number(t.attributes.combo_qty) <= qty);
      const finalV = bestTier || v;
      return finalV.discountPrice || finalV.discount_price || finalV.price;
    }
    return v.discountPrice || v.discount_price || v.price;
  });

  const displaySalePrice = $derived(effectiveUnitPrice);
  const displayOriginalPrice = $derived(activeVariant?.price || product.price || 0);
  const displayDiscountPercent = $derived(
    displayOriginalPrice > displaySalePrice 
      ? Math.round(((displayOriginalPrice - displaySalePrice) / displayOriginalPrice) * 100)
      : 0
  );

  function handleCarouselScroll(e: Event) {
    if (!carouselRef) return;
    const scrollLeft = (e.target as HTMLElement).scrollLeft;
    const width = carouselRef.offsetWidth;
    activeImageIndex = Math.round(scrollLeft / width);
  }

  function toggleVoucher(id: string) {
    const voucher = vouchers.find(v => v.id === id);
    if (!voucher) return;
    if (selectedVouchers.includes(id)) {
      selectedVouchers = selectedVouchers.filter(v => v !== id);
    } else {
      const groupIds = vouchers.filter(v => v.type === voucher.type).map(v => v.id);
      selectedVouchers = [...selectedVouchers.filter(v => !groupIds.includes(v)), id];
    }
  }

  function scrollVouchers(direction: 'next' | 'prev') {
    if (vouchersListRef) {
      const amount = direction === 'next' ? 140 : -140;
      vouchersListRef.scrollBy({ left: amount, behavior: 'smooth' });
    }
  }

  function handleVoucherScroll() {
    if (!vouchersListRef) return;
    const { scrollLeft, scrollWidth, clientWidth } = vouchersListRef;
    isAtStart = scrollLeft <= 5;
    isAtEnd = scrollLeft + clientWidth >= scrollWidth - 5;
  }

  const activeComboQty = $derived((selectedVariant || pVariants?.[0])?.attributes?.combo_qty || (selectedVariant || pVariants?.[0])?.attributes?.comboQty || product.metadata?.combo_qty || 0);
  const activeGifts = $derived((selectedVariant || pVariants?.[0])?.attributes?.gifts || product.metadata?.gifts || []);
  const helenAdvice = $derived.by(() => {
    const comboVariants = pVariants.filter(cv => cv.attributes && (cv.attributes.combo_qty || cv.attributes.comboQty));
    if (comboVariants.length === 0) return "Cơ hội sở hữu liệu trình chuyên sâu với ưu đãi độc quyền. Hãy chọn số lượng phù hợp để tối ưu kết quả.";
    
    const sortedTiers = [...comboVariants].sort((a, b) => Number(a.attributes.combo_qty || a.attributes.comboQty) - Number(b.attributes.combo_qty || b.attributes.comboQty));
    const currentQty = selectedQty;
    const nextTier = sortedTiers.find(t => Number(t.attributes.combo_qty || t.attributes.comboQty) > currentQty);
    
    if (nextTier) {
      const gap = Number(nextTier.attributes.combo_qty || nextTier.attributes.comboQty) - currentQty;
      const nextUnitPrice = nextTier.discountPrice || nextTier.discount_price || nextTier.price;
      const currentUnitPrice = effectiveUnitPrice;
      const savingsPerUnit = currentUnitPrice - nextUnitPrice;
      
      if (savingsPerUnit > 0) {
        return `Nâng cấp thêm ${gap} sp để giảm thêm ${formatCurrency(savingsPerUnit)}/sp!`;
      }
      return `Thêm ${gap} sản phẩm để nhận trọn vẹn quà tặng độc quyền!`;
    }
    
    return `Tuyệt vời! Bạn đã nhận mức giá tối ưu nhất từ ${supportAgent.config.agentName}.`;
  });
</script>

<section id="overview" class="overview-section">
  <!-- MEDIA SECTION (Extracted) -->
  <ProductMobileMedia
    {product}
    {displayImages}
    {activeImageIndex}
    bind:videoEl
    {videoMuted}
    {videoEndTime}
    {handleTimeUpdate}
    {toggleMute}
    {handleCarouselScroll}
    {triggerViralFly}
    onThumbClick={(i) => {
      activeImageIndex = i;
      carouselRef?.scrollTo({ left: i * carouselRef.clientWidth, behavior: 'smooth' });
    }}
    bind:carouselRef
    {isVideoUrl}
  />

  <section class="flash-sale-banner" class:is-flash={isFlashSaleActive}>
    <div class="fs-left">
      <div class="flex items-center gap-1.5">
        {#if displayDiscountPercent > 0}
          <div class="discount-percent">-{displayDiscountPercent}%</div>
        {/if}
        <div class="freeship-fomo">
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          Freeship
        </div>
      </div>
      <div class="price-container">
        <span class="price-label">{isFlashSaleActive ? 'Từ' : 'Giá từ'}</span>
        <span class="price-value">{formatCurrency(displaySalePrice)}</span>
      </div>
      {#if displayOriginalPrice > displaySalePrice}
        <div class="original-price">{formatCurrency(displayOriginalPrice)}</div>
      {/if}
    </div>
    
    <div class="fs-right">
      <div class="fs-title">
        <Zap size={18} fill="white" />
        <span>F⚡ASH SALE</span>
      </div>
      <div class="fs-countdown">
        <span>Kết thúc sau</span>
        <div class="time-box font-mono tabular-nums">
          {#if isFlashSaleActive && timeLeft}
            <span>{timeLeft.hours.toString().padStart(2, '0')}</span>
            <span class="separator">:</span>
            <span>{timeLeft.minutes.toString().padStart(2, '0')}</span>
            <span class="separator">:</span>
            <span>{timeLeft.seconds.toString().padStart(2, '0')}</span>
          {:else}
            <span>{mounted ? (23 - new Date().getHours()).toString().padStart(2, '0') : '00'}</span>
            <span class="separator">:</span>
            <span>{mounted ? (59 - new Date().getMinutes()).toString().padStart(2, '0') : '00'}</span>
            <span class="separator">:</span>
            <span>{mounted ? (59 - new Date().getSeconds()).toString().padStart(2, '0') : '00'}</span>
          {/if}
        </div>
      </div>
    </div>
  </section>

  <!-- INFO SECTION -->
  <section class="info-content">
    <!-- Vouchers -->
    <div class="vouchers-outer">
      {#if !isAtStart}<button class="scroll-btn prev" onclick={() => scrollVouchers('prev')}><ChevronLeft size={14} /></button>{/if}
      <div class="vouchers-container">
        <div class="vouchers-list" bind:this={vouchersListRef} onscroll={handleVoucherScroll}>
          {#each vouchers as v}
            {@const isApplied = selectedVouchers.includes(v.id)}
            <button type="button" class="ticket-wrapper" onclick={() => toggleVoucher(v.id)}>
              <div class="ticket" class:active={isApplied}>
                <div class="ticket-content flex items-center justify-center h-full">
                   <span class="main">{v.label}</span>
                </div>
              </div>
              {#if isApplied}
                <div class="active-badge">
                  <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                </div>
              {/if}
            </button>
          {/each}
        </div>
      </div>
      {#if !isAtEnd}<button class="scroll-btn next" onclick={() => scrollVouchers('next')}><ChevronRight size={14} /></button>{/if}
    </div>

    <!-- Title & Stats -->
    <div class="title-row mt-2">
      <h1 class="product-title">{product.name.replace(/40gr/g, '40g')}</h1>
    </div>

    <div class="product-stats-row mb-2">
      {#if stats?.total_count || product.metadata?.review_count}
        <div class="rating-box">
          <span class="scoreText">{stats?.average_rating || product.metadata?.reviews_trust_score || '5.0'}</span>
          <div class="stars">
            {#each Array(5) as _, i}
              <svg class="w-2.5 h-2.5 {i < Math.floor(stats?.average_rating || Number(product.metadata?.reviews_trust_score) || 5) ? 'text-luxury-copper' : 'text-gray-300'}" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            {/each}
          </div>
        </div>
        <div class="divider"></div>
      {/if}
      <div class="sold-count">{product.order_count_text || `Đã bán ${formatNumber(product.orderCount) || 0}`}</div>
      
      {#if product.sku || product.metadata?.barcode}
        <button 
          onclick={() => onTriggerScan?.()}
          class="ml-auto flex items-center gap-1.5 px-2 py-1 bg-green-50/50 rounded-lg border border-green-100/50 active:scale-95 transition-all transform translate-y-[-10px]"
        >
          <div class="flex flex-col items-end">
            <span class="text-[7px] font-black text-green-600 tracking-[0.2em] uppercase leading-none mb-0.5">Mã vạch</span>
            <span class="text-[10px] font-black text-gray-900 tracking-tighter leading-none">{product.sku || product.metadata?.barcode}</span>
          </div>
          <div class="w-1.5 h-1.5 bg-green-500 rounded-full animate-ping shrink-0"></div>
        </button>
      {/if}
    </div>

    {#if variations.length > 0}
      <div class="w-full py-3 border-y border-gray-50 my-2">
        <div class="flex items-center justify-between mb-2 px-1">
          <span class="text-[12px] text-gray-400 font-bold tracking-wider">
            {variations.length === 1 ? variations[0].name : 'Lựa chọn'}
          </span>
          {#if variations.length > 1}
            <button onclick={onOpenSelector} class="text-[11px] text-[#ee4d2d] font-bold flex items-center gap-0.5">
              Thay đổi <ChevronRight size={12} />
            </button>
          {/if}
        </div>
        
        <div class="flex gap-3 overflow-x-auto pb-2 scrollbar-hide no-scrollbar">
          {#if variations.length === 1}
            {#each variations[0].options as option, oIdx}
               {#if isOptionActive(0, oIdx)}
                 {@const isSelected = (selectedVariant?.tierIndex?.[0] ?? selectedVariant?.tier_index?.[0]) === oIdx}
                 <button 
                   onclick={() => onOpenSelector()} 
                   class="relative shrink-0 px-5 py-2.5 border-2 text-[12px] font-black tracking-tight transition-all
                   {isSelected ? 'border-[#ee4d2d] text-[#ee4d2d] bg-[#ee4d2d]/5' : 'bg-gray-50 border-gray-100 text-gray-500'}"
                 >
                   {option}
                   {#if isSelected}
                      <div class="absolute top-[-2px] right-[-2px] w-0 h-0 border-t-[8px] border-t-[#ee4d2d] border-l-[8px] border-l-transparent"></div>
                   {/if}
                 </button>
               {/if}
            {/each}
          {:else}
            <button 
              onclick={onOpenSelector}
              class="w-full flex items-center justify-between bg-gray-50/50 p-3 rounded-xl border border-gray-100"
            >
              <span class="text-[13px] font-black text-gray-900">
                {selectedVariant ? selectedVariant.tierIndex.map((idx, i) => variations?.[i]?.options?.[idx] || '').filter(Boolean).join(', ') : 'Chạm để chọn phân loại...'}
              </span>
              <ChevronRight size={16} class="text-gray-400" />
            </button>
          {/if}
        </div>
      </div>
    {/if}

    {#if activeComboQty > 1 || activeGifts.length > 0}
      <div class="mb-4 relative overflow-hidden bg-white border border-[#ee4d2d]/10 rounded-xl p-3 shadow-sm">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <div class="w-6 h-6 rounded-full bg-[#ee4d2d] flex items-center justify-center text-white shrink-0">
                <Gift size={14} />
              </div>
              <span class="text-[12px] font-black text-gray-900">Ưu đãi độc quyền</span>
            </div>
            
            <div class="flex items-center gap-1 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-100">
               <div class="w-1 h-1 bg-blue-400 rounded-full animate-ping"></div>
               <span class="text-[8px] text-blue-600 font-black tracking-tighter">Gợi ý từ Helen</span>
            </div>
          </div>

          <div class="mb-3 px-1">
             <p class="text-[11px] text-slate-500 font-medium leading-relaxed italic">
                "{helenAdvice}"
             </p>
          </div>
          
          {#if activeGifts.length > 0}
            <div class="flex flex-wrap gap-2">
               {#each activeGifts as gift}
                  <div class="flex items-center gap-2 bg-[#fdf2f2]/50 p-1.5 pr-3 rounded-lg border border-[#ee4d2d]/5">
                     <div class="w-8 h-8 rounded-md overflow-hidden bg-white border border-gray-100 shrink-0">
                        {#if gift.image}
                           <img src={resolveMediaUrl(gift.image)} alt={gift.name} class="w-full h-full object-cover" />
                        {:else}
                           <div class="w-full h-full flex items-center justify-center text-gray-200"><Package size={12} /></div>
                        {/if}
                     </div>
                     <div class="flex flex-col">
                        <span class="text-[11px] font-bold text-gray-900 leading-tight truncate max-w-[1200px]">{gift.name}</span>
                        <span class="text-[9px] text-[#ee4d2d] font-black italic">Tặng x{gift.qty}</span>
                     </div>
                  </div>
               {/each}
            </div>
          {/if}
      </div>
    {/if}

    <!-- VIRAL SHARE BAR (Mobile Floating) -->
    <ViralShareBarMobile 
      {product} 
      variant="mobile" 
      likeCount={baseLikeCount}
      scrolled={isScrolled}
      forceHidden={isHidden}
      {scrollRatio}
      {hideRatio}
    />
  </section>
</section>

<style>
  /* Elite V2.2: Unified Flash Sale Banner Styles */
  .flash-sale-banner { 
    background: linear-gradient(90deg, #ee4d2d, #ff7337); color: white; display: flex; padding: 6px 12px; justify-content: space-between; align-items: center; position: relative; overflow: hidden;
    box-shadow: 0 4px 15px rgba(238, 77, 45, 0.2);
  }

  .fs-left { flex: 1; z-index: 1; }
  .discount-percent { background: white; color: #ee4d2d; border: 1px solid white; width: max-content; padding: 0 4px; font-size: 11px; font-weight: 900; border-radius: 2px; }
  .freeship-fomo { background: #E3B5A4; color: white; font-size: 10px; font-weight: 900; padding: 0 4px; border-radius: 2px; display: flex; align-items: center; gap: 2px; height: 16px; }
  .price-container { display: flex; align-items: center; gap: 4px; margin-top: 2px; }
  .price-label { font-size: 13px; color: white; opacity: 0.9; }
  .price-value { font-size: 20px; font-weight: 900; letter-spacing: -0.5px; }
  .original-price { font-size: 11px; text-decoration: line-through; color: rgba(255,255,255,0.7); }
  
  .fs-right { text-align: right; z-index: 1; display: flex; flex-direction: column; align-items: flex-end; }
  .fs-title { display: flex; align-items: center; gap: 4px; font-weight: 900; font-size: 16px; font-style: italic; }
  .fs-countdown { font-size: 11px; display: flex; align-items: center; gap: 4px; font-weight: 700; }
  .time-box { display: flex; gap: 2px; align-items: center; }
  .time-box span { background: rgba(0,0,0,0.3); color: white; padding: 2px 6px; border-radius: 4px; font-weight: 1000; border: 1px solid rgba(255,255,255,0.2); min-width: 28px; text-align: center; font-size: 13px; }
  .time-box .separator { background: none; border: none; padding: 0; min-width: 4px; opacity: 0.8; text-align: center; font-weight: 1000; }

  .info-content { background: white; padding: 10px 5px 2px 5px; }
  .vouchers-outer { position: relative; margin-bottom: 12px; margin-left: -5px; margin-right: -5px; }
  .vouchers-list {
    display: flex;
    gap: 8px;
    overflow-x: auto;
    scrollbar-width: none;
    padding: 0 5px;
    scroll-padding: 0 5px;
  }
  .vouchers-list::-webkit-scrollbar { display: none; }
  .ticket { background: #fffaf9; border: 1px dashed var(--color-luxury-copper, #C18F7E); color: var(--color-luxury-copper, #C18F7E); padding: 4px 10px; border-radius: 4px; font-size: 11px; white-space: nowrap; font-weight: 700; }
  .ticket.active { background: var(--color-luxury-copper, #C18F7E); color: white; border-style: solid; }
  .ticket-wrapper { position: relative; background: none; border: none; padding: 0; }
  .active-badge { position: absolute; top: -4px; right: -4px; background: var(--color-luxury-peach, #E3B5A4); color: white; border-radius: 50%; width: 14px; height: 14px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
  .scroll-btn {
    position: absolute; top: 50%; transform: translateY(-50%); background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(0, 0, 0, 0.05); border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; z-index: 10;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1); color: var(--color-luxury-copper, #C18F7E); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); -webkit-tap-highlight-color: transparent;
  }
  .scroll-btn:active { scale: 0.85; background: white; }
  .scroll-btn.prev { left: 4px; }
  .scroll-btn.next { right: 4px; }

  .title-row { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 8px; }
  .product-title { font-size: 16px; font-weight: 800; line-height: 1.4; color: #222; flex: 1; margin: 0; }
  .bookmark-btn { background: none; border: none; color: #666; padding: 0; transition: color 0.3s; }
  .bookmark-active { color: #ff424f !important; }

  .product-stats-row { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #888; }
  .rating-box { display: flex; align-items: center; gap: 4px; color: #222; font-weight: 900; }
  .stars { display: flex; align-items: center; gap: 1px; }
  .divider { width: 1px; height: 10px; background: #eee; }
  .trust-badge { padding: 2px 8px; border-radius: 4px; font-size: 10px; letter-spacing: 0.05em; }

  /* CSS Variables for global sync */
  .overview-section { --z-media-promo: var(--z-index-media-promo, 10); }
</style>
