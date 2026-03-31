<script lang="ts">
  import type { Product } from '$lib/types';
  import { X, ShoppingCart, ShieldCheck, ArrowRight, ArrowLeft, Phone, MapPin, User, Loader2 } from 'lucide-svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/z_index_client';
  import { portal } from '$lib/core/actions/portal';
  import { fade, fly } from 'svelte/transition';

  const shopStore = getShopStore();
  let { active = $bindable(), product }: { active: boolean, product: Product } = $props();

  const metadata = $derived(product?.metadata || {});
  const variants = $derived(product?.variants || []);
  const appliedDeal = $derived(shopStore.appliedDeal);
  const nextDeal = $derived(shopStore.nextDeal);
  const totalSaved = $derived(shopStore.originalPrice * shopStore.quantity - shopStore.totalAmount);
  
  let step = $state<'selection' | 'shipping'>('selection');
  let name = $state('');
  let phone = $state('');
  let address = $state('');
  let validationError = $state<string | null>(null);

  const labels = $derived({
    title_select: (metadata.mobile_bottom_sheet_title as string) || "Lựa chọn liệu trình",
    title_shipping: "Thông tin nhận hàng",
    cta_next: "TIẾP TỤC",
    cta_submit: (metadata.mobile_bottom_sheet_cta as string) || "XÁC NHẬN LIỆU TRÌNH",
    free_shipping: (metadata.mobile_free_shipping_label as string) || "Lightning Free Shipping",
    variant_label: (metadata.mobile_variant_selection_label as string) || "Phân loại đang chọn",
  });

  // Drag-to-Close Logic
  let dragY = $state(0);
  let isDragging = $state(false);
  let startY = 0;

  function onPointerDown(e: PointerEvent) {
    isDragging = true;
    startY = e.clientY;
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }

  function onPointerMove(e: PointerEvent) {
    if (!isDragging) return;
    const delta = e.clientY - startY;
    if (delta > 0) dragY = delta;
    else dragY = delta * 0.2; // Tension when pulling up
  }

  function onPointerUp(e: PointerEvent) {
    if (!isDragging) return;
    isDragging = false;
    if (dragY > 120) {
      close();
    }
    dragY = 0;
  }

  function close() { 
    active = false;
    setTimeout(() => step = 'selection', 300); // Reset after animation
  }
  
  function validate() {
    if (step === 'shipping') {
      if (phone.length < 10) return "Số điện thoại không hợp lệ";
      if (address.length < 5) return "Địa chỉ cần chi tiết hơn";
    }
    return null;
  }

  // Smart Lookup Logic (Elite V2.2)
  let lookupTimer: any;
  function handlePhoneInput() {
    if (phone.length >= 10) {
      if (lookupTimer) clearTimeout(lookupTimer);
      lookupTimer = setTimeout(() => {
        shopStore.lookupCustomer(phone);
      }, 500);
    }
  }


  // Elite Identity Shield v2.2: Masked Auto-fill
  $effect(() => {
    const data = shopStore.customerData;
    if (data?.isRecurring) {
      if (data.nameMasked) name = data.nameMasked;
      if (data.addressMasked) address = data.addressMasked;
    }
  });

  async function handleAction() {
    validationError = null;
    if (step === 'selection') {
      step = 'shipping';
    } else {
      const err = validate();
      if (err) {
        validationError = err;
        return;
      }
      await shopStore.submitCheckout({ name, phone, address });
    }
  }

  function getVariantTitle(variant: any): string {
    if (!product.tierVariations?.length || !variant.tierIndex?.length) return variant.sku || 'Combo';
    return variant.tierIndex.map((optIdx: number, tierIdx: number) => {
      const option = product.tierVariations![tierIdx]?.options[optIdx];
      if (typeof option === 'string') return option;
      return option?.name || option?.label || '';
    }).filter(Boolean).join(' - ') || 'Combo';
  }
</script>

<div use:portal class="mobile-bottom-sheet-root">
  <button
    type="button"
    class="mobile-bottom-sheet-bg border-none outline-none"
    style="z-index: {Z_INDEX_CLIENT.OVERLAY}; opacity: {active ? 1 - Math.min(dragY / 400, 0.5) : 0}; transition: {isDragging ? 'none' : 'opacity 0.4s fade'}"
    class:active
    onclick={close}
  ></button>

  <div
    class="mobile-bottom-sheet bg-[#0a0a0a] text-white border-t border-white/10 flex flex-col shadow-[0_-20px_80px_rgba(0,0,0,0.9)]"
    class:active
    style="z-index: {Z_INDEX_CLIENT.MODAL}; padding-bottom: env(safe-area-inset-bottom, 24px); transform: translateY({active ? dragY + 'px' : '100%'}); transition: {isDragging ? 'none' : 'transform 0.4s cubic-bezier(0.23, 1, 0.32, 1)'}"
    role="dialog"
    aria-modal="true"
  >
    <div 
      class="w-full flex justify-center pt-3 pb-2 relative touch-none cursor-grab active:cursor-grabbing"
      onpointerdown={onPointerDown}
      onpointermove={onPointerMove}
      onpointerup={onPointerUp}
      onpointercancel={onPointerUp}
    >
      <div class="w-10 h-1 bg-white/10 rounded-full"></div>
      
      <!-- Close Button: Absolute Top Right -->
      <button 
        onclick={close} 
        class="absolute right-2 top-1 text-white/20 hover:text-white transition-colors p-3 active:scale-90"
      >
        <X class="w-5 h-5" strokeWidth={1} />
      </button>
    </div>

    <div class="relative flex items-center justify-center px-6 pb-4 pt-1">
      {#if step === 'shipping'}
        <button 
          onclick={() => step = 'selection'} 
          class="absolute left-6 text-white/40 hover:text-white transition-colors p-2 active:scale-90"
        >
          <ArrowLeft class="w-5 h-5" strokeWidth={1.5} />
        </button>
      {/if}

      <h2 class="text-[13px] font-black uppercase tracking-[0.2em] italic text-white/90">
        {step === 'selection' ? labels.title_select : labels.title_shipping}
      </h2>
    </div>

    <div class="px-6 pb-6 overflow-y-auto max-h-[70dvh] custom-scrollbar">
      {#if step === 'selection'}
        <div in:fade={{ duration: 200 }}>
          <div class="flex items-center gap-4 mb-6 p-4 bg-white/[0.02] rounded-3xl border border-white/5">
            <div class="w-20 h-20 rounded-2xl overflow-hidden border border-white/5 shrink-0">
               <img src={product.images[0]} alt={product.name} class="w-full h-full object-cover" />
            </div>
            <div class="flex-1">
               <div class="flex items-baseline gap-2 mb-1">
                  <span class="text-xl font-black text-white italic">{(shopStore.totalAmount).toLocaleString()}đ</span>
                  {#if shopStore.originalPrice * shopStore.quantity > shopStore.totalAmount}
                    <span class="text-[10px] text-white/20 line-through">{(shopStore.originalPrice * shopStore.quantity).toLocaleString()}đ</span>
                  {/if}
               </div>
               <div class="inline-flex items-center gap-1.5 text-[8px] font-black text-blue-400 uppercase tracking-[0.2em]">
                  <ShieldCheck class="w-2.5 h-2.5" /> {labels.free_shipping}
               </div>
               
               <!-- Active Deal Placement -->
               {#if shopStore.quantity >= 3}
                  <div class="mt-2 inline-flex items-center gap-2 px-2 py-0.5 bg-red-500/10 border border-red-500/20 rounded text-[7px] font-bold text-red-400 uppercase tracking-tight">
                    <span>🔥 MUA 2 TẶNG 1 ĐÃ KÍCH HOẠT</span>
                  </div>
               {/if}
            </div>
          </div>

          <!-- Compact Variant Chips -->
          <div class="space-y-3 mb-6">
            <span class="text-[9px] font-black text-white/30 uppercase tracking-[0.2em] ml-1">{labels.variant_label}</span>
            <div class="flex flex-wrap gap-2">
              {#each variants as v}
                <button 
                  onclick={() => shopStore.selectVariant(v)}
                  class="px-4 py-2.5 rounded-full border transition-all flex items-center gap-3 {shopStore.variant?.id === v.id ? 'border-blue-500 bg-blue-500/10 shadow-lg' : 'border-white/10 bg-white/5 opacity-60'}"
                >
                  <span class="text-[11px] font-bold {shopStore.variant?.id === v.id ? 'text-white' : 'text-white/60'} uppercase tracking-tight">
                    {getVariantTitle(v).split('-')[0].trim()}
                  </span>
                  <div class="w-px h-3 bg-white/10"></div>
                  <span class="text-[11px] font-black italic">{(v.discountPrice || v.price).toLocaleString()}đ</span>
                </button>
              {/each}
            </div>
          </div>
          

          <!-- Streamlined Quantity -->
          <div class="flex justify-between items-center mb-6">
            <span class="text-[9px] font-black text-white/30 uppercase tracking-[0.2em] ml-1">Số lượng mua</span>
            <div class="flex items-center bg-white/5 rounded-full p-1 border border-white/5">
              <button onclick={() => shopStore.setQuantity(shopStore.quantity - 1)} class="w-8 h-8 flex items-center justify-center rounded-full text-white/40 active:bg-white/10 active:text-white transition-all">-</button>
              <span class="px-4 text-[13px] font-black italic tabular-nums">{shopStore.quantity}</span>
              <button onclick={() => shopStore.setQuantity(shopStore.quantity + 1)} class="w-8 h-8 flex items-center justify-center rounded-full text-white/40 active:bg-white/10 active:text-white transition-all">+</button>
            </div>
          </div>

          <!-- Streamlined Upsell -->
          {#if nextDeal && !appliedDeal}
            <button 
              onclick={() => shopStore.setQuantity(shopStore.quantity + nextDeal.missing)}
              class="w-full p-3 bg-amber-500/5 border border-amber-500/20 rounded-xl flex items-center justify-between group active:scale-[0.98] transition-all"
            >
              <div class="flex items-center gap-3">
                <span class="text-base">🎁</span>
                <span class="text-[10px] font-bold text-amber-500/80 uppercase tracking-tight">Thêm {nextDeal.missing} hộp để nhận {nextDeal.deal.label}</span>
              </div>
              <ArrowRight class="w-3.5 h-3.5 text-amber-500/50 group-hover:translate-x-1 transition-transform" />
            </button>
          {/if}
        </div>
      {:else}
        <div in:fly={{ x: 20, duration: 300 }}>
          <!-- Applied Deal & Savings for Step 2 -->
          {#if appliedDeal || totalSaved > 0}
            <div class="mb-6 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center justify-between">
              <div class="flex flex-col">
                <span class="text-[8px] font-black text-emerald-400 uppercase tracking-widest">ƯU ĐÃI ĐÃ ÁP DỤNG</span>
                <span class="text-xs font-bold text-white uppercase italic">{appliedDeal?.label || 'GIÁ KHUYẾN MÃI'}</span>
              </div>
              <div class="text-right">
                <span class="text-[8px] font-black text-emerald-400 uppercase tracking-widest block">BẠN TIẾT KIỆM</span>
                <span class="text-lg font-black text-emerald-400 italic">-{totalSaved.toLocaleString()}đ</span>
              </div>
            </div>
          {/if}
          <!-- Shipping & Trust Info! -->
          <div class="mb-4 space-y-2">
            <div class="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-white/40 border-b border-white/5 pb-2">
              <span>Phương thức vận chuyển</span>
              <span class="text-emerald-400">Miễn phí (Tiết kiệm 30k)</span>
            </div>
            <div class="flex items-center gap-2 text-[9px] font-medium text-white/20 italic">
               <ShieldCheck class="w-3 h-3" /> Kiểm tra và nhận hàng tận nơi
            </div>
          </div>

          <div class="mb-6">
            <p class="text-[10px] text-white/30 uppercase tracking-[0.2em] font-medium leading-relaxed mb-6">
              Vui lòng cung cấp danh tính và địa chỉ. Hệ thống Elite sẽ bảo mật 100%.
            </p>
            
            <div class="space-y-4">
              <!-- 1. Phone FIRST (Mobile) -->
              <div class="relative group">
                <div class="absolute inset-y-0 left-5 flex items-center pointer-events-none text-white/20 group-focus-within:text-blue-500 transition-colors">
                  <Phone class="w-4 h-4" />
                </div>
                <input 
                  type="tel"
                  bind:value={phone}
                  oninput={handlePhoneInput}
                  placeholder="SỐ ĐIỆN THOẠI *"
                  class="w-full pl-12 pr-6 py-5 bg-white/[0.03] border-2 {validationError?.includes('thoại') ? 'border-red-500/30' : 'border-white/5 focus:border-blue-500/30'} rounded-2xl outline-none placeholder:text-white/10 text-white font-bold text-lg uppercase transition-all"
                />
                
                {#if shopStore.customerData?.isRecurring}
                   <div class="absolute -bottom-5 left-2 flex items-center gap-1.5 text-[8px] font-black text-blue-400 uppercase tracking-widest animate-in fade-in slide-in-from-top-1">
                      <div class="w-1.5 h-1.5 {shopStore.customerData.isTrustedDevice ? 'bg-emerald-500' : 'bg-amber-500'} rounded-full animate-pulse"></div>
                      CHÀO MỪNG {shopStore.customerData.nameMasked || 'QUÝ KHÁCH'} QUAY TRỞ LẠI!
                      <span class="ml-1 px-1 py-0.5 bg-sky-500/10 text-sky-500 text-[6px] rounded italic">BẢO MẬT (***)</span>
                   </div>
                {/if}
              </div>

              <!-- 2. Name -->
              <div class="relative group {shopStore.customerData?.isRecurring ? 'mt-3' : ''}">
                <div class="absolute inset-y-0 left-5 flex items-center pointer-events-none text-white/20 group-focus-within:text-blue-500 transition-colors">
                  <User class="w-4 h-4" />
                </div>
                <input 
                  bind:value={name}
                  placeholder="HỌ VÀ TÊN *"
                  class="w-full pl-12 pr-12 py-5 bg-white/[0.03] border-2 border-white/5 focus:border-blue-500/30 rounded-2xl outline-none placeholder:text-white/10 text-white font-bold text-sm uppercase transition-all"
                />
                
                {#if shopStore.customerData?.isRecurring && name === shopStore.customerData.nameMasked}
                   <div class="absolute right-5 inset-y-0 flex items-center text-emerald-400 animate-in zoom-in">
                      <ShieldCheck class="w-5 h-5" />
                   </div>
                {/if}
              </div>

              <!-- 3. Address -->
              <div class="relative group">
                <div class="absolute top-5 left-5 pointer-events-none text-white/20 group-focus-within:text-blue-500 transition-colors">
                  <MapPin class="w-4 h-4" />
                </div>
                <textarea 
                  bind:value={address}
                  rows="3"
                  placeholder="ĐỊA CHỈ NHẬN HÀNG CHI TIẾT *"
                  class="w-full pl-12 pr-6 py-5 bg-white/[0.03] border-2 {validationError?.includes('Địa chỉ') ? 'border-red-500/30' : 'border-white/5 focus:border-blue-500/30'} rounded-2xl outline-none placeholder:text-white/10 text-white font-bold text-sm uppercase transition-all resize-none"
                ></textarea>
              </div>

              {#if validationError}
                <p class="text-[10px] text-red-500 font-bold uppercase tracking-widest text-center animate-pulse">{validationError}</p>
              {/if}
              
              {#if shopStore.error}
                 <p class="text-[10px] text-red-500 font-bold uppercase tracking-widest text-center">{shopStore.error}</p>
              {/if}
            </div>
          </div>
        </div>
      {/if}

      <!-- Horizontal Pinned Action Bar -->
      <div class="flex items-center gap-4 mt-auto pt-4 border-t border-white/5">
        <div class="flex-1 flex flex-col">
          <div class="flex items-center gap-2 mb-0.5">
            <span class="text-[8px] font-black text-white/20 uppercase tracking-widest">Tổng giá trị liệu trình</span>
            {#if shopStore.originalPrice * shopStore.quantity > shopStore.totalAmount}
               <div class="px-1.5 py-0.5 bg-emerald-500/10 rounded text-[7px] font-black text-emerald-400">-{totalSaved.toLocaleString()}đ</div>
            {/if}
          </div>
          <span class="text-2xl font-black text-white italic tabular-nums leading-none">
            {(shopStore.totalAmount).toLocaleString()}đ
          </span>
        </div>

        <button
          class="flex-1 py-4 text-white font-black text-[13px] uppercase tracking-wider rounded-full shadow-[0_10px_30px_rgba(254,44,85,0.3)] active:scale-[0.98] transition-all flex items-center justify-center gap-2 disabled:opacity-50 overflow-hidden relative group"
          style="background: linear-gradient(90deg, #fe2c55 0%, #ff4b6b 100%);"
          onclick={handleAction}
          disabled={shopStore.isSubmitting}
        >
          <!-- Shimmer Effect -->
          <div class="absolute inset-0 w-1/3 h-full bg-gradient-to-r from-transparent via-white/10 to-transparent -skew-x-12 animate-shimmer pointer-events-none"></div>
          
          {#if shopStore.isSubmitting}
            <Loader2 class="w-4 h-4 animate-spin" />
          {:else}
            <span class="relative z-10">{step === 'selection' ? labels.cta_next : labels.cta_submit}</span>
            {#if step === 'selection'}
              <ArrowRight class="w-4 h-4 relative z-10 group-hover:translate-x-1 transition-transform" />
            {:else}
              <ShoppingCart class="w-4 h-4 relative z-10 group-hover:scale-110 transition-transform" />
            {/if}
          {/if}
        </button>
      </div>

      <!-- FOMO Indicator -->
      <div class="mt-4 flex items-center justify-center gap-2">
        <div class="flex -space-x-1.5">
          {#each Array(3) as _, i}
            <div class="w-4 h-4 rounded-full border border-black bg-gray-800 flex items-center justify-center overflow-hidden">
               <div class="w-full h-full bg-gradient-to-br from-gray-600 to-gray-800"></div>
            </div>
          {/each}
        </div>
        <p class="text-[8px] font-bold text-white/20 uppercase tracking-widest">
           🔥 <span class="text-amber-500/50">32 người</span> đang chọn phân loại này
        </p>
      </div>
      
      <p class="mt-6 text-[9px] text-white/10 text-center uppercase tracking-[0.3em] font-medium italic">
        🔒 Bảo mật AES-256 mã hóa quân sự
      </p>
    </div>
  </div>
</div>

<style lang="postcss">
  @keyframes shimmer {
    0% { transform: translateX(-200%); }
    100% { transform: translateX(300%); }
  }
  .animate-shimmer {
    animation: shimmer 3s infinite cubic-bezier(0.4, 0, 0.2, 1);
  }

  /* ── Autofill Correction (Elite V2.2) ───────── */
  input:-webkit-autofill,
  input:-webkit-autofill:hover, 
  input:-webkit-autofill:focus,
  textarea:-webkit-autofill,
  textarea:-webkit-autofill:hover,
  textarea:-webkit-autofill:focus {
    -webkit-text-fill-color: white !important;
    -webkit-box-shadow: 0 0 0px 1000px #0a0a0a inset !important;
    transition: background-color 5000s ease-in-out 0s;
    caret-color: white;
  }
</style>
