<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Minus from "@lucide/svelte/icons/minus";
  import Plus from "@lucide/svelte/icons/plus";
  import ShoppingCart from "@lucide/svelte/icons/shopping-cart";
  import Gift from "@lucide/svelte/icons/gift";
  import Package from "@lucide/svelte/icons/package";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Diamond from "@lucide/svelte/icons/diamond";
  import Beaker from "@lucide/svelte/icons/beaker";
  import FlaskConical from "@lucide/svelte/icons/flask-conical";
  import Info from "@lucide/svelte/icons/info";
  import Volume2 from "@lucide/svelte/icons/volume-2";
  import VolumeX from "@lucide/svelte/icons/volume-x";
  
  // Types
  import type { Product, ProductVariant, ReviewStats } from '$lib/types';
  
  // State & Stores
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte';
  
  // Utils
  import { getIngredientIcon } from '$lib/utils/product';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { formatCurrency } from '$lib/utils/format';
  
  // Components
  import ProductDetailReviews from './ProductDetailReviews.svelte';
  import ProductDetailRelated from './ProductDetailRelated.svelte';
  import ViralShareBarDesktop from './ViralShareBarDesktop.svelte';
  import ShareToUnlockPromoDesktop from './ShareToUnlockPromoDesktop.svelte';
  import HelenIcon from '$lib/components/client/support/HelenIcon.svelte';
  import InteractiveDashboard from '$lib/components/ui/InteractiveDashboard.svelte';


  function isJson(str: string): boolean {
    if (typeof str !== 'string' || !str) return false;
    try {
      const parsed: Record<string, unknown> = JSON.parse(str);
      return typeof parsed === 'object' && parsed !== null && ('hero_headline' in parsed || 'spec_bento' in parsed);
    } catch {
      return false;
    }
  }

  /** Detect video URL: mp4, webm, mov, ogg … */
  function isVideoUrl(url: string | undefined | null): boolean {
    if (!url) return false;
    const clean = url.split('?')[0].toLowerCase();
    return /\.(mp4|webm|mov|ogg|ogv|avi|mkv)$/.test(clean);
  }

  // ─── Shopee-style Video State ───────────────────────────────────
  let videoEl = $state<HTMLVideoElement | null>(null);
  let videoMuted = $state(true);

  /** Đọc trim config từ metadata của sản phẩm */
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

  /** timeupdate listener — custom loop từ startTime → endTime */
  function handleTimeUpdate() {
    if (!videoEl) return;
    if (videoEndTime !== null && videoEl.currentTime >= videoEndTime) {
      videoEl.currentTime = videoStartTime;
      videoEl.play().catch(() => {});
    }
  }

  /** Khi currentImage thay đổi sang video → reset & autoplay từ startTime */
  $effect(() => {
    if (videoEl && isVideoUrl(currentImage)) {
      videoEl.load();
      videoEl.muted = videoMuted;
      // Sau khi có metadata mới seek được
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

  const cartStore = getCartStore();
  const clientUi = getClientUi();

  interface Props {
    product: Product;
  }
  let { product }: Props = $props();

  let stats = $state<ReviewStats | null>(null);
  let likeCount = $state(0);

  // Sync like state with product (Elite V2.2)
  $effect(() => {
    if (product) {
      likeCount = Number(product.metadata?.viral_suite?.likes_count || product.metadata?.likes || 0);
    }
  });

  onMount(async () => {
    if (product?.id) {
      try {
        const res = await fetch(`/api/v1/client/reviews/stats?entity_type=PRODUCT&entity_id=${product.id}`);
        if (res.ok) stats = await res.json();
      } catch (e) {
        console.error('Failed to load product stats:', e);
      }
    }
  });

  const variations = $derived(product.tier_variations || product.tierVariations || []);
  let selectedIndices = $state<number[]>([]);
  
  $effect(() => {
    if (selectedIndices.length === 0 && variations.length > 0) {
      const defaultVariant = pVariants.find(v => v.is_default);
      if (defaultVariant && defaultVariant.tierIndex) {
        selectedIndices = [...defaultVariant.tierIndex];
      } else {
        selectedIndices = variations.map(() => 0);
      }
    }
  });
  let quantity = $state(1);
  let activeImageIndex = $state(0);

  const pVariants = $derived(product.variants || []);
  let currentVariant = $derived<ProductVariant | undefined>(
    pVariants.find(v => 
      v.tierIndex.length === selectedIndices.length && 
      v.tierIndex.every((val, i) => val === selectedIndices[i])
    )
  );

  let currentImage = $derived.by(() => {
    if (selectedIndices[0] >= 0 && variations?.[0]?.images?.[selectedIndices[0]]) {
      return variations[0].images[selectedIndices[0]];
    }
    const pImages = product.images || [];
    return pImages[activeImageIndex] || pImages[0] || '/placeholder.png';
  });

  const effectiveTier = $derived.by(() => {
    const comboVariants = pVariants.filter(cv => cv.attributes && cv.attributes.combo_qty);
    if (comboVariants.length === 0) return currentVariant;
    const sortedTiers = [...comboVariants].sort((a, b) => Number(b.attributes.combo_qty) - Number(a.attributes.combo_qty));
    return sortedTiers.find(t => Number(t.attributes.combo_qty) <= quantity) || currentVariant;
  });

  const effectiveUnitPrice = $derived.by(() => {
    const v = effectiveTier;
    if (!v) return typeof product.discountPrice === 'number' ? product.discountPrice : (product.discount_price || product.price || 0);
    return v.discountPrice || v.discount_price || v.price;
  });

  let displayPrice = $derived.by(() => {
    if (currentVariant) {
      return {
        price: currentVariant.price,
        discountPrice: effectiveUnitPrice
      };
    }
    // Min max range if not selected
    if (pVariants.length > 0) {
      const prices = pVariants.map(v => v.price);
      const discountPrices = pVariants.map(v => v.discountPrice || v.discount_price).filter(p => p != null) as number[];
      
      const minPrice = Math.min(...prices);
      const maxPrice = Math.max(...prices);
      
      const minDiscount = discountPrices.length > 0 ? Math.min(...discountPrices) : undefined;
      const maxDiscount = discountPrices.length > 0 ? Math.max(...discountPrices) : undefined;

      const formatRange = (min: number, max: number) => min === max ? min.toLocaleString('vi-VN') : `${min.toLocaleString('vi-VN')} - ${max.toLocaleString('vi-VN')}`;

      return {
        price: formatRange(minPrice, maxPrice),
        discountPrice: minDiscount ? formatRange(minDiscount, maxDiscount) : undefined
      };
    }

    return {
      price: product.price,
      discountPrice: product.discountPrice || product.discount_price
    };
  });
  
  let currentStock = $derived(currentVariant ? currentVariant.stock : product.stock);

  function selectOption(tierIndex: number, optionIndex: number) {
    const newSelected = [...selectedIndices];
    if (newSelected[tierIndex] === optionIndex) {
      newSelected[tierIndex] = -1; // toggle off
    } else {
      newSelected[tierIndex] = optionIndex;
    }
    selectedIndices = newSelected;
    
    // Sync quantity with combo_qty (Elite V2.2)
    const nextVariant = pVariants.find(v => 
      v.tierIndex.length === selectedIndices.length && 
      v.tierIndex.every((val, i) => val === selectedIndices[i])
    );
    if (nextVariant?.attributes?.combo_qty) {
      quantity = Number(nextVariant.attributes.combo_qty);
    } else if (quantity > currentStock) {
      // Reset quantity if it exceeds new stock
      quantity = currentStock > 0 ? 1 : 0;
    }
  }

  function validateSelection(): boolean {
    if (variations.length > 0 && selectedIndices.includes(-1)) {
      clientUi.showToast('Vui lòng chọn phân loại hàng', 'error');
      return false;
    }
    if (quantity < 1 || quantity > currentStock) {
      clientUi.showToast('Số lượng không hợp lệ', 'error');
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
      const matchingVariant = pVariants.find(v => Number(v.attributes?.combo_qty || 0) === quantity);
      if (matchingVariant && matchingVariant.tierIndex) {
        selectedIndices = [...matchingVariant.tierIndex];
      }
    }
  }

  function addToCart() {
    if (!validateSelection()) return;
    cartStore.addItem(product, currentVariant, quantity);
    clientUi.showToast('Đã thêm sản phẩm vào giỏ hàng', 'success');
  }

  // --- SALES ASSASSIN FOMO & VOUCHER LOGIC ---
  // Elite V2.2: Derive countdown from DB (product.metadata.flash_sale_end)
  const flashSaleEnd = $derived(
    product.metadata?.flash_sale_end
      ? new Date(product.metadata.flash_sale_end).getTime()
      : null
  );
  const isFlashSaleActive = $derived(
    flashSaleEnd !== null && flashSaleEnd > Date.now()
  );
  let timeLeft = $state({ hours: 0, minutes: 0, seconds: 0 });
  
  /**
   * Elite V2.2: Theo dõi trạng thái mở khóa Viral để kích hoạt hiệu ứng bay
   */
  let isViralUnlocked = $state(false);
  $effect(() => {
    if (typeof window !== 'undefined') {
       isViralUnlocked = !!localStorage.getItem(`viral_unlocked_${product.id}`);
    }
  });

  // Voucher State
  let selectedVouchers = $state<string[]>([]);
  
  // Use DB vouchers if available
  const productVouchers = $derived.by(() => {
    let vouchers = [];
    
    // 1. Check if product has specific override vouchers in metadata
    if (Array.isArray(product.metadata?.vouchers) && product.metadata.vouchers.length > 0) {
      vouchers = product.metadata.vouchers;
    } else {
      // 2. Fallback to global active vouchers from CartStore (Elite V2.2)
      vouchers = cartStore.vouchers.map(v => ({
        id: v.id,
        label: v.title || v.id,
        sub: v.subtitle || (v.type === 'SHIPPING' ? 'Miễn phí vận chuyển' : `Giảm ${formatCurrency(v.value)}`),
        type: v.type === 'SHIPPING' ? 'ship' : 'discount'
      }));
    }

    /**
     * Elite V2.2: Intelligent Filtering
     * Lọc bỏ các Voucher Viral để tránh hiện ở khối chung khi CHƯA chia sẻ.
     * Nếu ĐÃ mở khóa (isViralUnlocked), mã sẽ được hiển thị như một phần của hệ thống.
     */
    return vouchers.filter((v: { id: string; label?: string }) => {
      const isViral = v.id.includes('VIRAL') || (v.label || '').toUpperCase().includes('VIRAL');
      if (!isViral) return true;
      return isViralUnlocked;
    });
  });

  /**
   * Elite V2.2: Hiệu ứng bay vào Box giảm giá
   */
  function triggerViralFly() {
     isViralUnlocked = true; // Cập nhật state để Svelte render voucher vào box ngay
     // Logic hiệu ứng bay sẽ được component con kích hoạt
  }

  function toggleVoucher(id: string) {
    const voucher = productVouchers.find(v => v.id === id);
    if (!voucher) return;

    if (selectedVouchers.includes(id)) {
      selectedVouchers = selectedVouchers.filter(v => v !== id);
    } else {
      // Group-based exclusive selection
      const groupIds = productVouchers.filter(v => v.type === voucher.type).map(v => v.id);
      selectedVouchers = [...selectedVouchers.filter(v => !groupIds.includes(v)), id];
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

  // Extract product details (Dynamic from DB)
  const pDiscountPrice = $derived(product.discountPrice || product.discount_price);
  
  const productInfo = $derived({
    barcode: (product.sku as string) || 'N/A',
    brand: (product.metadata?.brand as string) || (product.attributes?.brand as string) || (product.attributes?.['Thương hiệu'] as string) || '',
    origin: (product.metadata?.origin as string) || (product.attributes?.origin as string) || (product.attributes?.['Xuất xứ'] as string) || '',
    weight: (product.metadata?.weight as string) || (product.attributes?.weight as string) || (product.attributes?.['Trọng lượng'] as string) || '',
    originalPrice: pDiscountPrice ? (product.price || product.base_price || 0) : (product.price || 0) * 1.55,
    salePrice: (pDiscountPrice as number) || (product.price as number) || 0
  });

  const visibleAttributes = $derived(
    product.attributes ? Object.entries(product.attributes).filter(([key, value]) => {
      const k = key.toLowerCase().replace(/_/g, " ").trim();
      const brand = productInfo.brand;
      const origin = productInfo.origin;
      const weight = productInfo.weight;
      return !( ((k === "xuất xứ" || k === "origin") && origin) || 
                ((k === "trọng lượng" || k === "quy cách" || k === "weight") && weight) || 
                ((k === "mã vạch" || k === "barcode") && productInfo.barcode && productInfo.barcode !== "N/A") || 
                (k === "thương hiệu" || k === "brand") );
    }) : []
  );

  const activePrices = $derived({
    sale: displayPrice.discountPrice || displayPrice.price,
    original: displayPrice.discountPrice ? displayPrice.price : (typeof displayPrice.price === 'number' ? displayPrice.price * 1.55 : displayPrice.price)
  });

  function buyNow() {
    if (!validateSelection()) return;
    cartStore.buyNow(product, currentVariant, quantity);
    goto('/checkout');
  }

  function triggerWriteReview() {
    const el = document.getElementById('product-reviews');
    if (el) {
       el.scrollIntoView({ behavior: 'smooth' });
       setTimeout(() => {
         const btn = document.getElementById('btn-write-review');
         if (btn) btn.click();
       }, 600);
    }
  }

  // --- HELEN AI PRICE INTELLIGENCE (VIRAL 2026) ---
  const helenAdvice = $derived.by(() => {
    const comboVariants = pVariants.filter(cv => cv.attributes && cv.attributes.combo_qty);
    if (comboVariants.length === 0) return "Cơ hội sở hữu liệu trình chuyên sâu với ưu đãi độc quyền. Hãy chọn số lượng phù hợp để tối ưu kết quả.";
    
    const sortedTiers = [...comboVariants].sort((a, b) => Number(a.attributes.combo_qty) - Number(b.attributes.combo_qty));
    const nextTier = sortedTiers.find(t => Number(t.attributes.combo_qty) > quantity);
    
    if (nextTier) {
      const gap = Number(nextTier.attributes.combo_qty) - quantity;
      const nextUnitPrice = nextTier.discountPrice || nextTier.discount_price || nextTier.price;
      const currentUnitPrice = effectiveUnitPrice;
      const savingsPerUnit = currentUnitPrice - nextUnitPrice;
      const tierName = nextTier.tierIndex.map((idx, i) => variations?.[i]?.options?.[idx] || '').filter(Boolean).join(' ') || "Combo tiếp theo";
      
      if (savingsPerUnit > 0) {
        return `Nâng cấp ngay lên bộ "${tierName}" (thêm ${gap} sp) để chạm ngưỡng tiết kiệm ${formatCurrency(nextUnitPrice)}/sp. Bạn sẽ giảm thêm ${formatCurrency(savingsPerUnit)} trên mỗi sản phẩm!`;
      }
      return `Chỉ thêm ${gap} sản phẩm để kích hoạt bộ "${tierName}" và nhận trọn vẹn đặc quyền quà tặng đi kèm!`;
    }
    
    return `Tuyệt vời! Bạn đã sở hữu Liệu Trình Hoàn Mỹ với mức giá tối ưu nhất. ${supportAgent.config.agentName} cam kết bảo vệ quyền lợi và chất lượng sản phẩm cho đơn hàng của bạn.`;
  });

  const activeComboQty = $derived(effectiveTier?.attributes?.combo_qty || effectiveTier?.attributes?.comboQty || 0);
  const activeGifts = $derived(effectiveTier?.attributes?.gifts || []);

  // SGE Shield V1.0: Deterministic DOM Entropy (Product Detail)
  const wrapperTags = ['div', 'article', 'section', 'main'];
  const seedLength = $derived(product?.name ? product.name.length : 10);
  const outerWrapper = $derived(wrapperTags[seedLength % wrapperTags.length]);
  const contentWrapper = $derived(wrapperTags[(seedLength + 3) % wrapperTags.length]);
  const descWrapper = $derived(['div', 'section', 'article'][(seedLength + 5) % 3]);
</script>

<svelte:element this={outerWrapper} class="bg-[#f6f6f6] min-h-screen">
  <!-- VIRAL 2026: PROFESSIONAL BREADCRUMB -->
  <div class="bg-[#f5f5f5] py-4">
  <div class="max-w-[1200px] mx-auto px-4 xl:px-0 flex items-center gap-3 text-[11px] text-gray-500 font-bold uppercase tracking-wider">
    <a href="/" class="flex items-center gap-2 bg-[#ee4d2d] text-white px-2 py-1 hover:brightness-110 transition-all">
      <Diamond size={10} fill="currentColor" />
      <span class="text-[9px] font-black tracking-[0.25em]">OSMO</span>
    </a>
    <span class="opacity-20">/</span>
    <span class="text-gray-400 normal-case tracking-normal font-medium">{product.name}</span>
  </div>
</div>

<svelte:element this={contentWrapper} class="max-w-[1200px] mx-auto bg-white shadow-sm mt-0  rounded-none p-5">
  <div class="flex flex-col md:flex-row gap-8">
    <!-- LEFT: IMAGES & SOCIAL (Viral 2026) -->
    <div class="w-full md:w-[450px] shrink-0">
      <div class="aspect-square w-full rounded-none overflow-hidden relative border border-gray-100 flex items-center justify-center bg-white group">
        {#if isVideoUrl(currentImage)}
          <!-- SHOPEE-STYLE: autoplay muted loop, full-fill -->
          <video
            bind:this={videoEl}
            src={currentImage}
            class="w-full h-full object-cover"
            autoplay
            muted={videoMuted}
            loop={videoEndTime === null}
            playsinline
            preload="auto"
            ontimeupdate={handleTimeUpdate}
          ></video>
          <!-- Mute / Unmute button (Shopee-style, bottom-right) -->
          <button
            onclick={toggleMute}
            class="absolute bottom-3 right-3 z-10 w-9 h-9 rounded-full bg-black/50 backdrop-blur-sm flex items-center justify-center text-white hover:bg-black/70 transition-all border border-white/20"
            title={videoMuted ? 'Bật âm thanh' : 'Tắt âm thanh'}
          >
            {#if videoMuted}
              <VolumeX size={16} />
            {:else}
              <Volume2 size={16} />
            {/if}
          </button>
        {:else}
          <img src={currentImage} alt={product.name} class="w-full h-full object-contain transition-transform duration-700 group-hover:scale-150 bg-white" />
        {/if}
        
        <!-- Flash Sale Label (Conditional: only when active) -->
        {#if isFlashSaleActive}
          <div class="absolute top-0 left-0 bg-[#ee4d2d] text-white px-3 py-1.5 text-[11px] font-black uppercase tracking-widest shadow-lg">
            Flash Sale
          </div>
        {/if}

        {#if !isVideoUrl(currentImage) && productInfo.salePrice < productInfo.originalPrice}
          <div class="absolute top-2 right-2 bg-[#ffe97a] px-2 py-1 text-[12px] font-black text-[#ee4d2d] shadow-sm">
            -{Math.round((1 - productInfo.salePrice / productInfo.originalPrice) * 100)}%
          </div>
        {/if}
      </div>
      
      <!-- Thumbnails -->
      <div class="mt-4 grid grid-cols-5 gap-2 px-1">
        {#each (product.images || []).slice(0, 5) as img, i}
          <button 
            type="button"
            class="aspect-square border-2 cursor-pointer transition-all {activeImageIndex === i ? 'border-[#ee4d2d]' : 'border-transparent hover:border-[#ee4d2d]'} relative overflow-hidden bg-gray-50 p-0"
            onclick={() => activeImageIndex = i}
            aria-label="Xem ảnh {i + 1}"
          >
            {#if isVideoUrl(img)}
              <video
                src={img}
                class="w-full h-full object-cover pointer-events-none"
                muted
                playsinline
                preload="metadata"
              ></video>
              <!-- Play icon mini -->
              <div class="absolute inset-0 flex items-center justify-center bg-black/20">
                <svg class="w-4 h-4 text-white drop-shadow" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
              </div>
            {:else}
              <img src={img} alt="Thumb" class="w-full h-full object-cover" />
            {/if}
          </button>
        {/each}
      </div>

      <!-- Social & Like (Viral 2026 — ViralShareBar) -->
      <div class="mt-8 px-2">
        <ViralShareBarDesktop 
          {product} 
          likeCount={likeCount}
          hideLikes={false}
        />
      </div>
    </div>

    <!-- RIGHT: PRODUCT INFO (Standard Mall UI) -->
    <div class="flex-1 flex flex-col pt-1">
         <div class="flex items-start gap-3 mb-2">
          <div class="flex items-center gap-1.5 bg-[#d0011b] text-white px-1.5 py-0.5 text-[10px] font-black uppercase tracking-widest shadow-sm group relative overflow-hidden mt-1 shrink-0">
            <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
            <span class="relative z-10 whitespace-nowrap">{product.metadata?.is_mall ? 'Mall' : 'Shop'}</span>
          </div>
         <h1 class="text-[20px] font-medium text-gray-900 leading-snug tracking-tight">
            {product.name.replace(/40gr/g, '40g')}
         </h1>
      </div>

      <!-- Stats Row -->
      <div class="flex items-center gap-6 text-[14px] mb-6 mt-1">
        <div class="flex items-center gap-1 text-[#ee4d2d] border-b border-[#ee4d2d]/20 pb-0.5">
          <span class="font-bold border-b border-[#ee4d2d] leading-none mb-[-2px]">{stats?.average_rating || product.metadata?.rating || '5.0'}</span>
          <div class="flex pt-0.5 gap-0.5 ml-1">
             {#each Array(5) as _, i}
                <svg class="w-3 h-3 {i < Math.floor(stats?.average_rating || Number(product.metadata?.rating) || 5) ? 'text-orange-400' : 'text-gray-300'} fill-current" viewBox="0 0 24 24"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>
             {/each}
          </div>
        </div>
        <div class="w-px h-4 bg-gray-200"></div>
        <button 
          onclick={() => document.getElementById('product-reviews')?.scrollIntoView({ behavior: 'smooth' })}
          class="flex items-center gap-1 group cursor-pointer border-none bg-transparent">
          <span class="text-black font-bold border-b border-black leading-none mb-[-2px]">{stats?.total_count ?? (product.metadata?.reviews?.length || 0)}</span>
          <span class="text-gray-500 font-medium">Đánh Giá</span>
        </button>
        <div class="w-px h-4 bg-gray-200"></div>
        <div class="flex items-center gap-1">
          <span class="text-black font-bold">{product.order_count_text || product.orderCount || 0}</span>
          {#if !product.order_count_text}
            <span class="text-gray-500 font-medium">Đã bán</span>
          {/if}
        </div>
        <div class="ml-auto">
           <button onclick={triggerWriteReview} class="text-[13px] text-gray-400 font-medium hover:text-[#ee4d2d] transition-colors">Tố cáo</button>
        </div>
      </div>

      <!-- Price Bar (Soft Luxury FOMO - Vietnamese Edition) -->
      <div class="bg-[#f6f6f6] px-5 py-2.5 flex items-center justify-between mb-3 relative overflow-hidden group border-y border-gray-100/50">
        <div class="flex flex-col">
            <div class="flex items-center gap-3 mb-0.5">
               <span class="text-[14px] text-gray-400 line-through">{formatCurrency(activePrices.original)}</span>
               {#if activePrices.original > activePrices.sale}
                  <span class="text-[11px] font-black text-[#00bfa5] uppercase tracking-widest bg-[#e6f9f6] px-1.5 py-0.5">
                      Tiết kiệm {formatCurrency(Number(activePrices.original) - Number(activePrices.sale))}
                  </span>
               {/if}
            </div>
            <div class="flex items-baseline gap-4">
                <span class="text-[32px] font-black text-[#d0011b] tracking-tighter leading-none">{formatCurrency(activePrices.sale)}</span>
            </div>

            {#if pVariants.some(v => v.attributes?.combo_qty && v.attributes.combo_qty > 1)}
                <div class="mt-1 flex flex-col gap-2">
                    <div class="flex items-center gap-2.5">
                        {#if activeComboQty > 1}
                           <div class="bg-slate-900 text-white text-[8px] font-black px-1.5 py-0.5 rounded-sm uppercase tracking-widest flex items-center gap-1">
                               <Package size={10} class="text-white/70" /> {activeComboQty} SP ĐÃ ÁP DỤNG
                           </div>
                        {/if}
                        <div class="flex items-center gap-1.5 group/ai cursor-default">
                            <HelenIcon size={12} color="#3b82f6" />
                            <span class="text-[8px] text-blue-500 font-mono font-black uppercase tracking-[0.2em]">{supportAgent.config.agentName}</span>
                            <div class="w-0.5 h-0.5 bg-blue-400 rounded-full animate-pulse"></div>
                        </div>
                    </div>
                    <div class="relative pl-4 border-l border-blue-200/40">
                        <p class="text-[12.5px] text-slate-500 font-medium leading-[1.4] max-w-[580px] tracking-tight">
                            {helenAdvice}
                        </p>
                    </div>
                </div>
            {/if}
        </div>

        <!-- Minimalist Timer (Conditional: only when flash sale is active) -->
        {#if isFlashSaleActive}
          <div class="flex flex-col items-end">
             <div class="flex items-center gap-2 mb-1">
                <div class="w-1.5 h-1.5 bg-[#ee4d2d] rounded-full animate-pulse shadow-[0_0_8px_#ee4d2d]"></div>
                <span class="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] opacity-80">Kết thúc sau</span>
             </div>
             <div class="flex gap-1 text-gray-800 font-black text-[17px] font-mono tabular-nums select-none">
                <div class="bg-gray-200/50 px-1.5 py-0.5 min-w-[30px] text-center rounded-sm">{timeLeft.hours < 10 ? '0' + timeLeft.hours : timeLeft.hours}</div>
                <span class="opacity-30 self-center w-1.5 text-center text-[12px]">:</span>
                <div class="bg-gray-200/50 px-1.5 py-0.5 min-w-[30px] text-center rounded-sm">{timeLeft.minutes < 10 ? '0' + timeLeft.minutes : timeLeft.minutes}</div>
                <span class="opacity-30 self-center w-1.5 text-center text-[12px]">:</span>
                <div class="bg-gray-200/50 px-1.5 py-0.5 min-w-[30px] text-center rounded-sm">{timeLeft.seconds < 10 ? '0' + timeLeft.seconds : timeLeft.seconds}</div>
             </div>
          </div>
        {/if}
      </div>

      <!-- Voucher Selection (Interactive FOMO) -->
      <div class="px-5 mb-4">
         <div class="flex items-start">
            <span class="w-[110px] shrink-0 text-[14px] text-gray-500 mt-2">Mã Giảm Giá</span>
            <div class="flex flex-wrap gap-3">
               {#each productVouchers as v}
                 {@const isApplied = selectedVouchers.includes(v.id)}
                 <button 
                  onclick={() => toggleVoucher(v.id)}
                  class="relative flex items-center gap-2 bg-[#fff4f1] border-2 transition-all p-2 pr-4 shadow-sm group {isApplied ? 'border-[#ee4d2d]' : 'border-transparent hover:border-[#ee4d2d]/30'}">
                    <!-- Ticket Edge Effect -->
                    <div class="absolute -left-1 top-1/2 -translate-y-1/2 w-2 h-2 bg-white rounded-full border border-gray-100"></div>
                    <div class="absolute -right-1 top-1/2 -translate-y-1/2 w-2 h-2 bg-white rounded-full border border-gray-100"></div>
                    
                    <div class="w-px h-6 bg-[#ee4d2d]/20 border-dashed border-l mx-1"></div>
                    <div class="flex flex-col items-start translate-x-1">
                       <span class="text-[12px] font-black text-[#ee4d2d] leading-none">{v.label}</span>
                       <span class="text-[9px] text-gray-400 font-bold uppercase mt-1 tracking-tighter">{v.sub || ''}</span>
                    </div>
                    
                    {#if isApplied}
                      <div class="absolute -top-2 -right-2 bg-[#ee4d2d] text-white rounded-full p-0.5 shadow-md">
                        <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
                      </div>
                    {/if}
                 </button>
               {/each}
            </div>
         </div>
      </div>
      
      <!-- Elite V2.2: Share-to-Unlock (Minimalist Placement) -->
      <div class="px-5 mb-4">
        <ShareToUnlockPromoDesktop {product} compact={true} onUnlock={triggerViralFly} />
      </div>

      <!-- Shipping Block -->
      <div class="px-5 space-y-2 mb-4">
         <div class="flex items-start">
            <span class="w-[110px] shrink-0 text-[14px] text-gray-500">Vận Chuyển</span>
            <div class="space-y-2">
               <div class="flex items-center gap-2">
                  <svg class="w-5 h-5 text-[#00bfa5]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                  <span class="text-[14px] font-medium text-gray-800">Nhận hàng nhanh chóng</span>
                  <svg class="w-3.5 h-3.5 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7-7" /></svg>
               </div>
               <div class="text-[14px]">
                  <span class="text-[#00bfa5] font-black">Phí ship 0₫</span>
                  <p class="text-[12px] text-gray-400 mt-1">Giao hàng toàn quốc từ 2-4 ngày làm việc.</p>
               </div>
            </div>
         </div>
      </div>
      <!-- Variations Selection (Standard Mall UI) -->
      {#if variations.length > 0}
        <div class="px-5 space-y-5 mb-5 mt-2">
          {#each variations as tier, tIdx}
            <div class="flex items-start">
              <span class="w-[110px] shrink-0 text-[14px] text-gray-500 mt-2 capitalize">{tier.name}</span>
              <div class="flex flex-wrap gap-2.5">
                {#each tier.options as option, oIdx}
                  {@const isSelected = selectedIndices[tIdx] === oIdx}
                  <button 
                    type="button"
                    onclick={() => selectOption(tIdx, oIdx)}
                    class="relative min-w-[80px] h-10 px-4 border transition-all flex items-center justify-center text-[14px] hover:bg-[#ffeee8]/20 group
                    {isSelected ? 'border-[#ee4d2d] text-[#ee4d2d] bg-white ring-1 ring-[#ee4d2d]/10' : 'border-gray-200 text-gray-800 bg-white'}"
                  >
                    {#if tIdx === 0 && tier.images?.[oIdx]}
                      <img src={tier.images[oIdx]} alt={option} class="w-6 h-6 object-cover mr-2 border border-gray-100" />
                    {/if}
                    <span class="font-medium">{option}</span>
                    
                    {#if isSelected}
                      <!-- Selection Indicator Corner -->
                      <div class="absolute bottom-0 right-0 w-0 h-0 border-t-[12px] border-t-transparent border-r-[12px] border-r-[#ee4d2d]"></div>
                      <svg class="absolute bottom-0 right-0 w-2.5 h-2.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4"><path d="M20 6L9 17l-5-5" /></svg>
                    {/if}
                  </button>
                {/each}
              </div>
            </div>
          {/each}
        </div>
      {/if}

      <!-- Quantity & Luxury Stock Logic (Vietnamese) -->
      <div class="px-5 flex items-center mb-4">
         <span class="w-[110px] shrink-0 text-[12px] font-bold text-gray-400 uppercase tracking-widest">Số Lượng</span>
         <div class="flex items-center gap-8">
            <div class="flex items-center border border-gray-100 rounded-none h-9 group overflow-hidden bg-white shadow-sm">
               <button 
                  type="button"
                  class="w-10 h-full flex items-center justify-center text-gray-300 hover:text-black hover:bg-gray-50 transition-colors disabled:opacity-20 active:bg-gray-100"
                  onclick={() => handleQuantityChange(-1)} disabled={quantity <= 1}>
                  <Minus class="w-3.5 h-3.5" strokeWidth={3} />
               </button>
               <input 
                  type="text" 
                  readonly
                  class="w-12 h-full text-center border-x border-gray-100 text-[15px] font-black outline-none bg-white pointer-events-none text-gray-900"
                  value={quantity} />
               <button 
                  type="button"
                  class="w-10 h-full flex items-center justify-center text-gray-300 hover:text-black hover:bg-gray-50 transition-colors disabled:opacity-20 active:bg-gray-100"
                  onclick={() => handleQuantityChange(1)} disabled={quantity >= (currentStock || 99)}>
                  <Plus class="w-3.5 h-3.5" strokeWidth={3} />
               </button>
            </div>
            
            <div class="flex flex-col gap-0.5">
               <span class="text-[12px] text-gray-900 font-black uppercase tracking-tighter italic">SỐ LƯỢNG CÓ HẠN</span>
               {#if currentStock < 10}
                 <span class="text-[11px] font-bold text-[#ee4d2d] flex items-center gap-1">
                    <span class="w-1 h-1 bg-[#ee4d2d] rounded-full animate-ping"></span>
                    Hàng hiếm, chỉ còn {currentStock} bộ trong kho
                 </span>
               {:else}
                 <span class="text-[11px] text-[#00bfa5] font-black uppercase tracking-tight italic">Đang có sẵn tại kho Mall chính hãng</span>
               {/if}
            </div>
         </div>
      </div>

      <!-- COMBO & GIFTS SECTION (Viral 2026 UI) -->
      {#if activeGifts.length > 0}
        <div class="px-5 mb-6">
          <div class="bg-gradient-to-br from-[#fdf2f2] to-[#fff] border-2 border-[#ee4d2d]/10 p-5 relative overflow-hidden group/combo-box shadow-sm">
              <!-- Background Decorative Elements -->
              <div class="absolute -top-10 -right-10 w-32 h-32 bg-[#ee4d2d]/5 rounded-full blur-3xl group-hover/combo-box:bg-[#ee4d2d]/10 transition-colors"></div>
              
              <div class="flex items-start gap-4 relative z-10">
                <div class="mt-1">
                  <div class="w-10 h-10 rounded-full bg-[#ee4d2d] flex items-center justify-center text-white shadow-lg shadow-[#ee4d2d]/20">
                    <Gift size={20} />
                  </div>
                </div>
                
                <div class="flex-1 space-y-3">
                  <div class="flex items-center justify-between">
                    <h3 class="text-[14px] font-black uppercase tracking-widest text-gray-800">Ưu đãi độc quyền</h3>
                    {#if activeComboQty > 1}
                      <div class="bg-[#d0011b] text-white text-[10px] font-black px-2.5 py-1 rounded-full flex items-center gap-1.5 shadow-md">
                        <Package size={10} /> COMBO X{activeComboQty}
                      </div>
                    {/if}
                  </div>
                  
                  {#if activeGifts.length > 0}
                    <div class="grid grid-cols-1 gap-2.5">
                      {#each activeGifts as gift}
                        <div class="flex items-center gap-3 bg-white/60 backdrop-blur-md p-2 border border-[#ee4d2d]/5 hover:border-[#ee4d2d]/20 transition-all group/gift-item rounded-sm">
                          <div class="w-12 h-12 rounded-sm overflow-hidden bg-gray-50 border border-gray-100 shrink-0 group-hover/gift-item:scale-105 transition-transform shadow-sm">
                            {#if gift.image}
                              <img src={resolveMediaUrl(gift.image)} alt={gift.name} class="w-full h-full object-cover" />
                            {:else}
                              <div class="w-full h-full flex items-center justify-center bg-gray-50 text-gray-300">
                                <Sparkles size={16} />
                              </div>
                            {/if}
                          </div>
                          <div class="flex flex-col">
                            <span class="text-[13px] font-bold text-gray-900 leading-tight">{gift.name}</span>
                            <div class="flex items-center gap-2 mt-0.5">
                              <span class="text-[11px] text-gray-500 font-medium">Số lượng:</span>
                              <span class="text-[11px] text-[#ee4d2d] font-black italic">x{gift.qty}</span>
                            </div>
                          </div>
                        </div>
                      {/each}
                    </div>
                  {/if}
                </div>
              </div>
          </div>
        </div>
      {/if}

      <!-- CTA BUTTONS (Elite V2.2 Sharp) -->
      <div class="px-5 flex gap-4 mt-auto pb-4">
         <button 
            onclick={addToCart}
            class="h-[52px] min-w-[210px] border border-[#d0011b] bg-[#ffeee8]/60 text-[#d0011b] font-medium flex items-center justify-center gap-2.5 hover:bg-[#ffeee8] transition-all rounded-none">
            <ShoppingCart class="w-5 h-5" />
            <span class="text-[14px] font-black uppercase">Thêm Vào Giỏ Hàng</span>
         </button>
         <button 
            onclick={buyNow}
            class="h-[52px] min-w-[180px] bg-[#d0011b] text-white font-black text-[14px] uppercase hover:brightness-110 transition-all rounded-none">
            Mua Ngay
         </button>
      </div>

    </div>
  </div>
</svelte:element>

<!-- Bottom Sections (Professional Layout) -->
<div class="max-w-[1200px] mx-auto flex flex-col gap-[20px] mb-0">
    <!-- CHI TIẾT SẢN PHẨM -->
    <div class="bg-white p-6 shadow-[0_2px_20px_-5px_rgba(0,0,0,0.05)] border border-gray-50 ">
       <div class="flex items-center justify-between mb-8 pb-4 border-b border-gray-50">
          <div class="flex items-center gap-3">
             <div class="w-1.5 h-6 bg-[#ee4d2d]"></div>
             <h2 class="text-[20px] font-black text-gray-900 uppercase tracking-tight">Chi tiết sản phẩm</h2>
          </div>
          <div class="flex items-center gap-4">
             <div class="flex flex-col items-end">
                <span class="text-[9px] font-black text-gray-400 uppercase tracking-widest">Serial / SKU</span>
                <span class="text-[12px] font-black text-black tracking-widest">{product.sku || 'N/A'}</span>
             </div>
          </div>
       </div>

       <!-- Viral 2026: Liquid Spec Bar (Desktop) -->
       <div class="flex items-stretch bg-gray-50/50 border border-gray-100 divide-x divide-gray-100 rounded-none mb-10 overflow-hidden">
          {#if productInfo.brand}
            <div class="flex-1 px-8 py-5 flex flex-col justify-center hover:bg-white transition-all group/spec cursor-default">
              <span class="text-[9px] text-gray-400 font-black uppercase tracking-[0.25em] mb-2 flex items-center gap-2">
                <div class="w-1 h-1 rounded-full bg-amber-400 animate-pulse"></div> Thương hiệu
              </span>
              <a href="/products?brand={encodeURIComponent(productInfo.brand)}" class="text-[14px] font-black text-[#ee4d2d] hover:underline flex items-center gap-1.5 uppercase tracking-tight">
                {productInfo.brand}
                <svg class="w-3.5 h-3.5 opacity-0 group-hover/spec:opacity-100 transition-all translate-x-[-5px] group-hover/spec:translate-x-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M9 5l7 7-7 7" /></svg>
              </a>
            </div>
          {/if}
          {#if productInfo.origin}
            <div class="flex-1 px-8 py-5 flex flex-col justify-center hover:bg-white transition-all">
              <span class="text-[9px] text-gray-400 font-black uppercase tracking-[0.25em] mb-2 flex items-center gap-2">
                <div class="w-1 h-1 rounded-full bg-blue-400"></div> Xuất xứ
              </span>
              <span class="text-[14px] font-black text-gray-800 uppercase tracking-tighter">{productInfo.origin}</span>
            </div>
          {/if}
          {#if productInfo.weight}
            <div class="flex-1 px-8 py-5 flex flex-col justify-center hover:bg-white transition-all">
              <span class="text-[9px] text-gray-400 font-black uppercase tracking-[0.25em] mb-2 flex items-center gap-2">
                <div class="w-1 h-1 rounded-full bg-emerald-400"></div> Quy cách
              </span>
              <span class="text-[14px] font-black text-gray-800">{productInfo.weight}</span>
            </div>
          {/if}
          <div class="flex-[1.5] px-8 py-5 flex flex-col justify-center hover:bg-white transition-all">
            <span class="text-[9px] text-gray-400 font-black uppercase tracking-[0.25em] mb-2 flex items-center gap-2">
               <div class="w-1 h-1 rounded-full bg-indigo-400"></div> Danh mục
            </span>
            <div class="flex items-center gap-2 text-[13px] font-bold uppercase tracking-tighter">
               <a href="/products" class="text-gray-400 hover:text-gray-900 transition-colors">osmo</a>
               <svg class="w-3 h-3 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M9 5l7 7-7 7" /></svg>
               <a href="/{product.categorySlug || 'products'}/" class="text-[#0384ff] hover:underline truncate">
                  {product.category || 'CHĂM SÓC DA'}
               </a>
            </div>
          </div>
       </div>

       <div class="px-0 text-[14px] space-y-10">
          <div class="grid grid-cols-1 gap-6 w-full">
               <!-- Elite V2.2: Featured Ingredients (Viral 2026 UI) -->
               {#if product.metadata?.featured_ingredients && product.metadata.featured_ingredients.length > 0}
               <div class="flex flex-col gap-3 py-2">
                  <div class="flex items-center gap-2 text-[10px] font-black text-gray-400 uppercase tracking-widest">
                    <Sparkles size={12} class="text-amber-500" /> Thành phần nổi bật (Featured)
                  </div>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {#each product.metadata.featured_ingredients as ing}
                      <div class="flex gap-3 bg-[#fdf2f2]/50 border border-[#ee4d2d]/5 p-3 rounded-xl hover:bg-white hover:shadow-xl hover:shadow-[#ee4d2d]/5 transition-all group/ing">
                        <div class="w-10 h-10 shrink-0 bg-white border border-[#ee4d2d]/10 rounded-full flex items-center justify-center text-[18px] group-hover/ing:scale-110 transition-transform shadow-sm">
                          {ing.icon || getIngredientIcon(ing.name)}
                        </div>
                        <div class="flex flex-col">
                          <span class="text-[13px] font-black text-gray-900 leading-none mb-1">{ing.name}</span>
                          <span class="text-[11px] text-gray-500 leading-relaxed font-medium">{ing.benefit}</span>
                        </div>
                      </div>
                    {/each}
                  </div>
               </div>
               {/if}

               <!-- Elite V2.2: Full Ingredients (SGE Shield & Technical Transparency) -->
               {#if product.metadata?.ingredients}
               <div class="flex flex-col gap-2 py-1">
                  <div class="flex items-center gap-2 text-[10px] font-black text-gray-400 uppercase tracking-widest">
                    <Beaker size={12} class="text-teal-500" /> Bảng thành phần (Full INCI)
                  </div>
                  <div class="bg-gray-50/50 border border-gray-100 p-4 rounded-xl relative overflow-hidden group/inci">
                    <div class="absolute top-0 right-0 p-2 opacity-10 group-hover/inci:opacity-30 transition-opacity">
                      <FlaskConical size={40} />
                    </div>
                    <p class="text-[11px] text-gray-600 font-mono leading-relaxed tracking-tight relative z-10">
                      {product.metadata.ingredients}
                    </p>
                    <div class="mt-3 pt-3 border-t border-gray-100 flex items-center gap-2">
                      <Info size={10} class="text-blue-500" />
                      <span class="text-[9px] text-gray-400 font-bold italic">Bảng thành phần công bố</span>
                    </div>
                  </div>
               </div>
               {/if}
{#if visibleAttributes.length > 0}
                  <div class="grid grid-cols-2 gap-4 pt-4 mt-4 border-t border-gray-50">
                    {#each visibleAttributes as [key, value]}
                      <div class="flex items-center justify-between p-3 bg-gray-50/30 rounded-lg">
                        <span class="text-gray-400 font-medium capitalize">{key.replace(/_/g, " ")}</span>
                        <span class="text-gray-900 font-bold">{value}</span>
                      </div>
                    {/each}
                  </div>
                {/if}
          </div>
       </div>
    </div>

     <!-- MÔ TẢ SẢN PHẨM -->
    <div class="bg-white p-6 shadow-[0_2px_20px_-5px_rgba(0,0,0,0.05)] border border-gray-50 ">
       <div class="flex items-center justify-between mb-8 pb-4 border-b border-gray-50">
          <div class="flex items-center gap-3">
             <div class="w-1.5 h-6 bg-[#ee4d2d]"></div>
             <h2 class="text-[20px] font-black text-gray-900 uppercase tracking-tight">Mô tả sản phẩm</h2>
          </div>
       </div>
       <div class="px-0 prose-osmo">
          {#if isJson(product.description)}
             <div class="bg-slate-900 text-white p-4 rounded-none">
               <InteractiveDashboard data={product.description} compact={false} />
             </div>
          {:else}
             {@html product.description || 'Chưa có mô tả chi tiết cho sản phẩm này.'}
          {/if}
       </div>
    </div>

    <!-- GEO 2026: Desktop FAQ Section -->
    {#if product.metadata?.faqs && product.metadata.faqs.length > 0}
    <div class="bg-white p-6 shadow-[0_2px_20px_-5px_rgba(0,0,0,0.05)] border border-gray-50 ">
       <div class="flex items-center justify-between mb-8 pb-4 border-b border-gray-50">
          <div class="flex items-center gap-3">
             <div class="w-1.5 h-6 bg-[#ee4d2d]"></div>
             <h2 class="text-[20px] font-black text-gray-900 uppercase tracking-tight">Câu hỏi thường gặp</h2>
          </div>
       </div>
       <div class="px-0 flex flex-col gap-4">
          {#each product.metadata.faqs as faq}
            <div class="border border-gray-100 p-4 rounded-md bg-gray-50/30">
              <h3 class="text-[15px] font-bold text-gray-900 mb-2">{faq.question}</h3>
              <p class="text-[14px] text-gray-600 leading-relaxed w-full">{faq.answer}</p>
            </div>
          {/each}
       </div>
    </div>
    {/if}

    <!-- ĐÁNH GIÁ SẢN PHẨM -->
    <div id="product-reviews" class="mt-0">
       <ProductDetailReviews {product} />
    </div>

    <!-- SẢN PHẨM LIÊN QUAN (Viral 2026) -->
    <ProductDetailRelated {product} />
  </div>

</svelte:element>
<style>
  /* Elite V2.2: Premium Prose System */
  :global(.prose-osmo) {
    font-family: inherit !important;
    font-size: 16px !important;
    line-height: 1.8 !important;
    color: #374151 !important; /* text-gray-700 */
  }

  :global(.prose-osmo p) {
    margin-bottom: 1rem !important;
    font-family: inherit !important;
  }

  /* Khử margin cho p bên trong li để list items khít nhau */
  :global(.prose-osmo li p) {
    margin-bottom: 0 !important;
  }

  :global(.prose-osmo span) {
    font-family: inherit !important;
    font-size: inherit !important;
    line-height: inherit !important;
  }

  :global(.prose-osmo h2, .prose-osmo h3) {
    color: #111827 !important;
    font-weight: 800 !important;
    margin-top: 2rem !important;
    margin-bottom: 1rem !important;
    font-family: inherit !important;
    text-transform: uppercase;
    letter-spacing: -0.025em;
  }

  :global(.prose-osmo h2) { font-size: 20px !important; }
  :global(.prose-osmo h3) { font-size: 18px !important; }

  :global(.prose-osmo ul, .prose-osmo ol) {
    margin-bottom: 1.5rem !important;
    padding-left: 1.75rem !important;
  }

  /* Aggressive suppression of default bullets */
  :global(.prose-osmo ul),
  :global(.prose-osmo ul li) {
    list-style: none !important;
    list-style-type: none !important;
  }

  :global(.prose-osmo ul li::marker) {
    content: none !important;
  }

  :global(.prose-osmo li) {
    position: relative !important;
    margin-bottom: 0.5rem !important;
  }

  :global(.prose-osmo ul li::before) {
    content: "" !important;
    position: absolute !important;
    left: -0.8rem !important;
    top: 0.75em !important;
    width: 3px !important;
    height: 3px !important;
    background-color: #94a3b8 !important;
    border-radius: 50% !important;
    opacity: 0.5 !important;
  }

  :global(.prose-osmo img) {
    max-width: 100%;
    height: auto !important;
    margin: 1rem auto !important;
    display: block;
  }
</style>
