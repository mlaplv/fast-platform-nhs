<script lang="ts">
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { goto } from '$app/navigation';
  import type { Product, ProductVariant } from '$lib/types';
  import { ShoppingCart, Minus, Plus, Star } from 'lucide-svelte';
  import { Volume2, VolumeX } from 'lucide-svelte';
  import ProductDetailReviews from './ProductDetailReviews.svelte';

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
    typeof (product.metadata as any)?.video_start_time === 'number'
      ? (product.metadata as any).video_start_time as number
      : 0
  );
  const videoEndTime = $derived(
    typeof (product.metadata as any)?.video_end_time === 'number'
      ? (product.metadata as any).video_end_time as number
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

  interface Props {
    product: Product;
  }
  let { product }: Props = $props();

  let selectedIndices = $state<number[]>(product.tierVariations?.map(() => -1) ?? []);
  let quantity = $state(1);
  let activeImageIndex = $state(0);

  let currentVariant = $derived<ProductVariant | undefined>(
    product.variants?.find(v => 
      v.tierIndex.length === selectedIndices.length && 
      v.tierIndex.every((val, i) => val === selectedIndices[i])
    )
  );

  let currentImage = $derived.by(() => {
    if (selectedIndices[0] >= 0 && product.tierVariations?.[0]?.images?.[selectedIndices[0]]) {
      return product.tierVariations[0].images[selectedIndices[0]];
    }
    return product.images?.[activeImageIndex] || product.images?.[0] || '/placeholder.png';
  });

  let displayPrice = $derived.by(() => {
    if (currentVariant) {
      return {
        price: currentVariant.price,
        discountPrice: currentVariant.discountPrice
      };
    }
    // Min max range if not selected
    if (product.variants?.length > 0) {
      const prices = product.variants.map(v => v.price);
      const discountPrices = product.variants.map(v => v.discountPrice).filter(p => p != null) as number[];
      
      const minPrice = Math.min(...prices);
      const maxPrice = Math.max(...prices);
      
      const minDiscount = discountPrices.length > 0 ? Math.min(...discountPrices) : undefined;
      const maxDiscount = discountPrices.length > 0 ? Math.max(...discountPrices) : undefined;

      return {
        price: minPrice === maxPrice ? minPrice : `${minPrice.toLocaleString('vi-VN')} - ${maxPrice.toLocaleString('vi-VN')}`,
        discountPrice: minDiscount ? (minDiscount === maxDiscount ? minDiscount : `${minDiscount.toLocaleString('vi-VN')} - ${maxDiscount.toLocaleString('vi-VN')}`) : undefined
      };
    }

    return {
      price: product.price,
      discountPrice: product.discountPrice
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
    
    // Reset quantity if it exceeds new stock
    if (quantity > currentStock) {
      quantity = currentStock > 0 ? 1 : 0;
    }
  }

  function validateSelection(): boolean {
    if (product.tierVariations?.length > 0 && selectedIndices.includes(-1)) {
      alert('Vui lòng chọn phân loại hàng');
      return false;
    }
    if (quantity < 1 || quantity > currentStock) {
      alert('Số lượng không hợp lệ');
      return false;
    }
    return true;
  }

  function handleQuantityChange(delta: number) {
    const newVal = quantity + delta;
    const maxStock = currentStock || 99; // Fallback to 99 for Transino single variant
    if (newVal >= 1 && newVal <= maxStock) {
      quantity = newVal;
    }
  }

  function addToCart() {
    if (!validateSelection()) return;
    cartStore.addItem(product, currentVariant, quantity);
  }

  // --- SALES ASSASSIN FOMO & VOUCHER LOGIC ---
  let timeLeft = $state({ hours: 0, minutes: 43, seconds: 33 });
  
  // Voucher State
  let selectedVouchers = $state<string[]>([]);
  
  // Use DB vouchers if available, otherwise show global system promos
  const productVouchers = $derived(
    Array.isArray((product.metadata as any)?.vouchers) && (product.metadata as any).vouchers.length > 0
      ? (product.metadata as any).vouchers 
        : [
            { id: 'freeship_30k', label: 'Miễn Phí Vận Chuyển', sub: 'Giảm tối đa 30,000đ', type: 'ship' },
            { id: 'freeship_60k', label: 'Miễn Phí Vận Chuyển', sub: 'Giảm tối đa 60,000đ', type: 'ship' },
            { id: 'disc_30k', label: 'Giảm ₫30k', sub: 'Đơn từ 150k', type: 'discount' },
            { id: 'disc_60k', label: 'Giảm ₫60k', sub: 'Đơn từ 300k', type: 'discount' }
          ]
  );

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
    const timer = setInterval(() => {
      if (timeLeft.seconds > 0) timeLeft.seconds--;
      else if (timeLeft.minutes > 0) { timeLeft.minutes--; timeLeft.seconds = 59; }
      else if (timeLeft.hours > 0) { timeLeft.hours--; timeLeft.minutes = 59; timeLeft.seconds = 59; }
    }, 1000);

    return () => clearInterval(timer);
  });

  // Viral 2026: Format currency standard
  const formatVnd = (val: number | string) => {
    if (typeof val === 'string') return val;
    return val.toLocaleString('vi-VN');
  };

  // Extract product details (Dynamic from DB)
  const pDiscountPrice = $derived(product.discountPrice || product.discount_price);
  
  const productInfo = $derived({
    barcode: product.sku || 'N/A',
    brand: (product.metadata as any)?.brand || '',
    origin: (product.metadata as any)?.origin || '',
    weight: (product.metadata as any)?.weight || '',
    originalPrice: pDiscountPrice ? product.price : product.price * 1.55,
    salePrice: pDiscountPrice || product.price
  });

  function buyNow() {
    if (!validateSelection()) return;
    cartStore.addItem(product, currentVariant, quantity);
    goto('/checkout');
  }
</script>

<div class="bg-[#f6f6f6] min-h-screen">
  <!-- VIRAL 2026: PROFESSIONAL BREADCRUMB -->
  <div class="bg-[#f5f5f5] py-4">
  <div class="max-w-[1200px] mx-auto px-4 xl:px-0 flex items-center gap-2 text-[13px] text-gray-600 font-medium">
    <a href="/" class="hover:text-[#ee4d2d]">Micsmo</a>
    <svg class="w-3 h-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7" /></svg>
    <span class="truncate max-w-[400px] text-gray-400">{product.name}</span>
  </div>
</div>

<div class="max-w-[1200px] mx-auto bg-white shadow-sm my-4 rounded-none p-5">
  <div class="flex flex-col md:flex-row gap-8">
    <!-- LEFT: IMAGES & SOCIAL (Viral 2026) -->
    <div class="w-full md:w-[450px] shrink-0">
      <div class="aspect-square w-full rounded-none overflow-hidden relative border border-gray-50 flex items-center justify-center bg-black group">
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
          />
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
        
        <!-- Flash Sale Label -->
        <div class="absolute top-0 left-0 bg-[#ee4d2d] text-white px-3 py-1.5 text-[11px] font-black uppercase tracking-widest shadow-lg">
          Flash Sale
        </div>

        {#if !isVideoUrl(currentImage) && productInfo.salePrice < productInfo.originalPrice}
          <div class="absolute top-2 right-2 bg-[#ffe97a] px-2 py-1 text-[12px] font-black text-[#ee4d2d] shadow-sm">
            -{Math.round((1 - productInfo.salePrice / productInfo.originalPrice) * 100)}%
          </div>
        {/if}
      </div>
      
      <!-- Thumbnails -->
      <div class="mt-4 grid grid-cols-5 gap-2 px-1">
        {#each (product.images || []).slice(0, 5) as img, i}
          <div 
            class="aspect-square border-2 cursor-pointer transition-all {activeImageIndex === i ? 'border-[#ee4d2d]' : 'border-transparent hover:border-[#ee4d2d]'} relative overflow-hidden bg-gray-50"
            onclick={() => activeImageIndex = i}
          >
            {#if isVideoUrl(img)}
              <video
                src={img}
                class="w-full h-full object-cover pointer-events-none"
                muted
                playsinline
                preload="metadata"
              />
              <!-- Play icon mini -->
              <div class="absolute inset-0 flex items-center justify-center bg-black/20">
                <svg class="w-4 h-4 text-white drop-shadow" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
              </div>
            {:else}
              <img src={img} alt="Thumb" class="w-full h-full object-cover" />
            {/if}
          </div>
        {/each}
      </div>

      <!-- Social & Like -->
      <div class="mt-8 flex items-center justify-between px-2">
        <div class="flex items-center gap-3">
          <span class="text-sm font-medium text-gray-800">Chia sẻ:</span>
          <div class="flex gap-1.5 font-bold">
            <button class="w-6 h-6 rounded-full bg-[#0384ff] text-white text-[10px] flex items-center justify-center">f</button>
            <button class="w-6 h-6 rounded-full bg-[#38adff] text-white text-[10px] flex items-center justify-center">z</button>
            <button class="w-6 h-6 rounded-full bg-[#ff4500] text-white text-[10px] flex items-center justify-center">p</button>
            <button class="w-6 h-6 rounded-full bg-black text-white text-[10px] flex items-center justify-center">𝕏</button>
          </div>
        </div>
        <div class="w-px h-5 bg-gray-100"></div>
        <div class="flex items-center gap-2">
           <svg class="w-6 h-6 text-[#ff424f] fill-current" viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
           <span class="text-sm font-medium text-gray-700">Đã thích (1,7k)</span>
        </div>
      </div>
    </div>

    <!-- RIGHT: PRODUCT INFO (Standard Mall UI) -->
    <div class="flex-1 flex flex-col pt-1">
      <div class="flex items-start gap-3 mb-2">
         <div class="flex items-center gap-1.5 bg-[#d0011b] text-white px-1.5 py-0.5 text-[10px] font-black uppercase tracking-widest shadow-sm group relative overflow-hidden mt-1 shrink-0">
            <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
            <span class="relative z-10 whitespace-nowrap">{(product.metadata as any)?.is_mall ? 'Mall' : 'Shop'}</span>
         </div>
         <h1 class="text-[20px] font-medium text-gray-900 leading-snug tracking-tight">
            {product.name}
         </h1>
      </div>

      <!-- Stats Row -->
      <div class="flex items-center gap-6 text-[14px] mb-6 mt-1">
        <div class="flex items-center gap-1 text-[#ee4d2d] border-b border-[#ee4d2d]/20 pb-0.5">
          <span class="font-bold border-b border-[#ee4d2d] leading-none mb-[-2px]">{(product.metadata as any)?.rating || '5.0'}</span>
          <div class="flex pt-0.5 gap-0.5 ml-1">
             {#each Array(5) as _, i}
                <svg class="w-3 h-3 {i < ((product.metadata as any)?.rating || 5) ? 'text-orange-400' : 'text-gray-300'} fill-current" viewBox="0 0 24 24"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>
             {/each}
          </div>
        </div>
        <div class="w-px h-4 bg-gray-200"></div>
        <button 
          onclick={() => document.getElementById('product-reviews')?.scrollIntoView({ behavior: 'smooth' })}
          class="flex items-center gap-1 group cursor-pointer border-none bg-transparent">
          <span class="text-black font-bold border-b border-black leading-none mb-[-2px]">{(product.metadata as any)?.reviews?.length || 0}</span>
          <span class="text-gray-500 font-medium">Đánh Giá</span>
        </button>
        <div class="w-px h-4 bg-gray-200"></div>
        <div class="flex items-center gap-1">
          <span class="text-black font-bold">{(product as any).order_count_text || product.order_count || 0}</span>
          {#if !(product as any).order_count_text}
            <span class="text-gray-500 font-medium">Đã Bán</span>
          {/if}
          <svg class="w-3.5 h-3.5 opacity-30 cursor-help" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        </div>
        <div class="ml-auto">
           <button class="text-[13px] text-gray-400 font-medium hover:text-[#ee4d2d] transition-colors">Tố cáo</button>
        </div>
      </div>

      <!-- Price Bar (Soft Luxury FOMO - Vietnamese Edition) -->
      <div class="bg-[#f6f6f6] px-5 py-3 flex items-center justify-between mb-3 relative overflow-hidden group border-y border-gray-100/50">
        <div class="flex flex-col">
            <div class="flex items-center gap-3 mb-1">
               <span class="text-[16px] text-gray-400 line-through">₫{formatVnd(productInfo.originalPrice)}</span>
               <div class="bg-[#ee4d2d] text-white text-[10px] font-black px-1.5 py-0.5 uppercase tracking-tighter">Giảm 55%</div>
            </div>
            <div class="flex items-baseline gap-4">
               <span class="text-[36px] font-black text-[#d0011b] tracking-tighter">₫{formatVnd(productInfo.salePrice)}</span>
               <span class="text-[13px] font-black text-[#00bfa5] uppercase tracking-widest bg-[#e6f9f6] px-2 py-1">Tiết kiệm {formatVnd(productInfo.originalPrice - productInfo.salePrice)}₫</span>
            </div>
        </div>

        <!-- Minimalist Timer (Soft Version) -->
        <div class="flex flex-col items-end">
           <div class="flex items-center gap-2 mb-2">
              <div class="w-1.5 h-1.5 bg-[#ee4d2d] rounded-full animate-pulse shadow-[0_0_8px_#ee4d2d]"></div>
              <span class="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] opacity-80">Kết thúc sau</span>
           </div>
           <div class="flex gap-2 text-gray-800 font-black text-[18px]">
              <div class="bg-gray-200/50 px-2 py-0.5 min-w-[32px] text-center">0</div>
              <span class="opacity-30">:</span>
              <div class="bg-gray-200/50 px-2 py-0.5 min-w-[32px] text-center">{timeLeft.minutes < 10 ? '0' + timeLeft.minutes : timeLeft.minutes}</div>
              <span class="opacity-30">:</span>
              <div class="bg-gray-200/50 px-2 py-0.5 min-w-[32px] text-center">{timeLeft.seconds < 10 ? '0' + timeLeft.seconds : timeLeft.seconds}</div>
           </div>
        </div>
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
                  <span class="text-[#00bfa5] font-black">Phí ship ₫0</span>
                  <p class="text-[12px] text-gray-400 mt-1">Giao hàng toàn quốc từ 2-4 ngày làm việc.</p>
               </div>
            </div>
         </div>
      </div>



      <!-- Product Specifications (Dynamic) -->
      <div class="px-5 space-y-2.5 mb-4 border-t border-gray-50 pt-4">
         {#if productInfo.barcode && productInfo.barcode !== 'N/A'}
         <div class="flex items-center">
            <span class="w-[110px] shrink-0 text-[14px] text-gray-400 font-medium">Mã vạch</span>
            <span class="text-[14px] font-black text-gray-900 tracking-widest bg-gray-50 px-2 py-0.5">{productInfo.barcode}</span>
         </div>
         {/if}
         {#if productInfo.brand}
         <div class="flex items-center">
            <span class="w-[110px] shrink-0 text-[14px] text-gray-400 font-medium">Thương hiệu</span>
            <span class="text-[14px] font-black text-[#ee4d2d]">{productInfo.brand}</span>
         </div>
         {/if}
         {#if productInfo.origin}
         <div class="flex items-center">
            <span class="w-[110px] shrink-0 text-[14px] text-gray-400 font-medium">Xuất xứ</span>
            <span class="text-[14px] font-black text-gray-900">{productInfo.origin}</span>
         </div>
         {/if}
         {#if productInfo.weight}
         <div class="flex items-center">
            <span class="w-[110px] shrink-0 text-[14px] text-gray-400 font-medium">Trọng Lượng</span>
            <span class="text-[14px] font-black text-gray-900">{productInfo.weight}</span>
         </div>
         {/if}
         {#if product.attributes}
           {#each Object.entries(product.attributes) as [key, value]}
             <div class="flex items-center">
                <span class="w-[110px] shrink-0 text-[14px] text-gray-400 font-medium capitalize">{key.replace(/_/g, ' ')}</span>
                <span class="text-[14px] font-black text-gray-900">{value}</span>
             </div>
           {/each}
         {/if}
      </div>

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
</div>

<!-- Bottom Sections (Professional Layout) -->
<div class="max-w-[1200px] mx-auto flex flex-col gap-4 mb-0">
    <!-- CHI TIẾT SẢN PHẨM -->
    <div class="bg-white p-5 shadow-sm">
       <div class="bg-gray-50/50 px-0 py-4 border-b border-gray-100 mb-6 flex items-center justify-between">
          <h2 class="text-[18px] font-black text-gray-800 uppercase tracking-tight">Chi tiết sản phẩm</h2>
          <div class="flex items-center gap-2">
             <span class="text-[11px] font-bold text-gray-400 uppercase tracking-widest">Mã vạch:</span>
             <span class="text-[11px] font-black text-black tracking-widest bg-gray-100 px-2 py-0.5">{productInfo.barcode}</span>
          </div>
       </div>
       <div class="px-0 text-[14px] space-y-6">
          <div class="grid grid-cols-1 gap-4 max-w-4xl">
              {#if productInfo.brand}
              <div class="flex items-center">
                 <span class="w-[180px] shrink-0 text-gray-400 font-medium">Thương hiệu</span>
                 <span class="text-[#ee4d2d] font-black">{productInfo.brand}</span>
              </div>
              {/if}
              {#if productInfo.origin}
              <div class="flex items-center">
                 <span class="w-[180px] shrink-0 text-gray-400 font-medium">Xuất xứ</span>
                 <span class="text-gray-900 font-bold">{productInfo.origin}</span>
              </div>
              {/if}
              {#if productInfo.weight}
              <div class="flex items-center">
                 <span class="w-[180px] shrink-0 text-gray-400 font-medium">Trọng Lượng</span>
                 <span class="text-gray-900 font-bold">{productInfo.weight}</span>
              </div>
              {/if}
              <div class="flex items-center">
                 <span class="w-[180px] shrink-0 text-gray-400 font-medium tracking-tight">Danh Mục</span>
                 <div class="flex items-center gap-2 text-[#0384ff] font-black uppercase text-[12px] tracking-tighter">
                    <a href="/" class="hover:underline">Micsmo</a> 
                    <svg class="w-2.5 h-2.5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7" /></svg>
                    <a href="/" class="hover:underline">{product.category || 'CHĂM SÓC DA'}</a>
                 </div>
              </div>
             {#if product.attributes}
               {#each Object.entries(product.attributes) as [key, value]}
                 <div class="flex items-center">
                    <span class="w-[180px] shrink-0 text-gray-400 font-medium capitalize">{key.replace(/_/g, ' ')}</span>
                    <span class="text-gray-900 font-medium">{value}</span>
                 </div>
               {/each}
             {/if}
          </div>
       </div>
    </div>

     <!-- MÔ TẢ SẢN PHẨM -->
    <div class="bg-white p-5 shadow-sm">
       <div class="bg-gray-50/50 px-0 py-4 border-b border-gray-100 mb-6">
          <h2 class="text-[18px] font-black text-gray-800 uppercase tracking-tight">Mô tả sản phẩm</h2>
       </div>
       <div class="px-0 prose-micsmo">
          {@html product.description || 'Chưa có mô tả chi tiết cho sản phẩm này.'}
       </div>
    </div>

    <!-- ĐÁNH GIÁ SẢN PHẨM -->
    <div id="product-reviews">
       <ProductDetailReviews {product} />
    </div>
  </div>
</div>
<style>
  /* Elite V2.2: Premium Prose System */
  :global(.prose-micsmo) {
    font-family: inherit !important;
    font-size: 16px !important;
    line-height: 1.8 !important;
    color: #374151 !important; /* text-gray-700 */
  }

  :global(.prose-micsmo p) {
    margin-bottom: 1rem !important;
    font-family: inherit !important;
  }

  /* Khử margin cho p bên trong li để list items khít nhau */
  :global(.prose-micsmo li p) {
    margin-bottom: 0 !important;
  }

  :global(.prose-micsmo span) {
    font-family: inherit !important;
    font-size: inherit !important;
    line-height: inherit !important;
  }

  :global(.prose-micsmo h2, .prose-micsmo h3) {
    color: #111827 !important;
    font-weight: 800 !important;
    margin-top: 2rem !important;
    margin-bottom: 1rem !important;
    font-family: inherit !important;
    text-transform: uppercase;
    letter-spacing: -0.025em;
  }

  :global(.prose-micsmo h2) { font-size: 20px !important; }
  :global(.prose-micsmo h3) { font-size: 18px !important; }

  :global(.prose-micsmo ul, .prose-micsmo ol) {
    margin-bottom: 1rem !important;
    padding-left: 1.5rem !important;
  }

  :global(.prose-micsmo li) {
    margin-bottom: 0.25rem !important;
    list-style-type: disc;
  }

  :global(.prose-micsmo img) {
    border-radius: 8px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    margin: 2rem auto !important;
    display: block;
  }
</style>
