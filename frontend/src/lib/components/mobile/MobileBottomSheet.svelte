<script lang="ts">
  import type { Product, ProductVariant } from '$lib/types';
  import { X, ShoppingCart, ShieldCheck, ArrowRight, ArrowLeft, Phone, MapPin, User, Loader2 } from 'lucide-svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import type { ShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { portal } from '$lib/core/actions/portal';
  import { fade, fly } from 'svelte/transition';
  import GiftModal from '$lib/components/storefront/ui/GiftModal.svelte';

  let { active = $bindable(), product, shopStore }: { active: boolean, product: Product, shopStore: ShopStore } = $props();

  const metadata = $derived(product?.metadata);
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
    title_select: metadata?.mobile_bottom_sheet_title || "Lựa chọn liệu trình",
    title_shipping: "Thông tin nhận hàng",
    cta_next: "TIẾP TỤC",
    cta_submit: metadata?.mobile_bottom_sheet_cta || "XÁC NHẬN LIỆU TRÌNH",
    free_shipping: metadata?.mobile_free_shipping_label || "Lightning Free Shipping",
    variant_label: metadata?.mobile_variant_selection_label || "Phân loại đang chọn",
  });

  // Memory cleanup for async timers
  let lookupTimer: ReturnType<typeof setTimeout> | undefined;
  $effect(() => {
    return () => {
      if (lookupTimer) clearTimeout(lookupTimer);
    };
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
      if (data.nameMasked && !name) name = data.nameMasked;
      if (data.addressMasked && !address) address = data.addressMasked;
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

  function handleInputChange() {
    if (validationError) {
      const err = validate();
      if (!err) validationError = null;
    }
  }

  function getVariantTitle(variant: ProductVariant): string {
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
    class="mobile-overlay border-none outline-none"
    style:--drag-opacity-reduce={active ? Math.min(dragY / 400, 0.5) : 0}
    class:active
    class:dragging={isDragging}
    onclick={close}
  ></button>

  <div
    class="mobile-modal-base"
    class:active
    class:dragging={isDragging}
    style:--drag-y={active ? dragY + 'px' : '100%'}
    role="dialog"
    aria-modal="true"
  >
    <div 
      class="w-full flex justify-center pt-4 pb-2 relative touch-none cursor-grab active:cursor-grabbing"
      onpointerdown={onPointerDown}
      onpointermove={onPointerMove}
      onpointerup={onPointerUp}
      onpointercancel={onPointerUp}
    >
      <div class="w-12 h-1.5 bg-white/30 rounded-full shadow-[0_0_10px_rgba(255,255,255,0.05)]"></div>
    </div>

    <!-- Close Button: Decoupled from Drag Area with 48px Hitbox -->
    <button
      onclick={close}
      class="absolute right-0 top-0 w-12 h-12 flex items-center justify-center text-white/45 hover:text-white transition-all active:scale-90 active:bg-white/5 rounded-tr-[inherit] z-header"
      aria-label="Đóng"
    >
      <X class="w-5 h-5" strokeWidth={1.5} />
    </button>

    <!-- Header: Optimized Spacing -->
    <div class="relative flex items-center justify-center px-6 pt-2 pb-4 border-b border-white/5">
      {#if step === 'shipping'}
        <button 
          onclick={() => step = 'selection'} 
          class="absolute left-6 text-white/40 hover:text-white transition-colors p-2 active:scale-90"
        >
          <ArrowLeft class="w-5 h-5" strokeWidth={1.5} />
        </button>
      {/if}

      <h2 class="text-[13px] font-black uppercase tracking-[0.25em] italic text-white/90">
        {step === 'selection' ? labels.title_select : labels.title_shipping}
      </h2>
    </div>

    <!-- Scrollable content area -->
    <div class="px-6 py-4 overflow-y-auto custom-scrollbar flex flex-col h-auto max-h-[75dvh] flex-initial">
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
              Vui lòng điền thông tin.
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
                  oninput={() => { handlePhoneInput(); handleInputChange(); }}
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
                  oninput={handleInputChange}
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
                  oninput={handleInputChange}
                  rows="3"
                  placeholder="ĐỊA CHỈ NHẬN HÀNG CHI TIẾT *"
                  class="w-full pl-12 pr-6 py-5 bg-white/[0.03] border-2 {validationError?.includes('Địa chỉ') ? 'border-red-500/30' : 'border-white/5 focus:border-blue-500/30'} rounded-2xl outline-none placeholder:text-white/10 text-white font-bold text-sm uppercase transition-all resize-none"
                ></textarea>
              </div>

              <!-- Viral Gift Modal Trigger (Elite V2.2 Mobile) -->
              <div class="gift-trigger-wrap mt-2">
                <button 
                    type="button"
                    onclick={() => shopStore?.toggleGiftModal(true)}
                    class="gift-trigger-btn flex items-center justify-between w-full group"
                >
                    <div class="flex items-center gap-3">
                        <span class="text-xl group-hover:scale-125 transition-transform">🎁</span>
                        <div class="flex flex-col text-left">
                            <span class="text-[9px] font-black tracking-widest text-pink-400 uppercase">Ưu đãi Elite đặc biệt</span>
                            <span class="text-xs font-bold text-white">Thêm Gói quà & Lời nhắn tặng người thân</span>
                        </div>
                    </div>
                    
                    {#if shopStore?.giftInfo}
                        <div class="flex items-center gap-1.5 text-emerald-400">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
                            <span class="text-[9px] font-black uppercase tracking-tighter">ĐÃ LƯU</span>
                        </div>
                    {:else}
                        <ArrowRight class="w-3.5 h-3.5 text-white/30" />
                    {/if}
                </button>
                
                {#if shopStore?.giftInfo}
                    <div class="gift-summary-mini animate-in fade-in slide-in-from-top-2 ml-12 mt-1">
                        <p class="text-[9px] text-white/60 italic truncate">
                            Quà từ: <span class="text-white font-bold uppercase">{shopStore?.giftInfo.sender_name}</span> 
                            {shopStore?.giftInfo.message ? ` - "${shopStore?.giftInfo.message}"` : ''}
                        </p>
                    </div>
                {/if}
              </div>
            </div>
          </div>
        </div>
      {/if}
    </div>

    {#if validationError || shopStore.error}
      <div class="px-6 py-2 bg-red-500/10 border-t border-red-500/20 text-[10px] text-red-500 font-bold uppercase tracking-widest text-center animate-pulse">
        {validationError || shopStore.error}
      </div>
    {/if}

    <!-- Horizontal Pinned Action Bar: Stick to bottom -->
    <div class="flex items-center gap-3 px-6 py-4 border-t border-white/5 bg-[#0a0a0a]">
      <div class="flex-1 flex flex-col min-w-0">
        <div class="flex items-baseline gap-1 mb-0.5 whitespace-nowrap">
          <span class="text-[8px] font-black text-white/20 uppercase tracking-widest">Tổng giá trị liệu trình</span>
          {#if shopStore.originalPrice * shopStore.quantity > shopStore.totalAmount}
             <div class="px-1 py-0.5 bg-emerald-500/10 rounded-[4px] text-[6px] font-black text-emerald-400">-{totalSaved.toLocaleString()}đ</div>
          {/if}
        </div>
        <span class="text-xl font-black text-white italic tabular-nums leading-none">
          {(shopStore.totalAmount).toLocaleString()}đ
        </span>
      </div>

      <button
        class="flex-[1.2] py-[14px] px-3 text-white font-black text-[12px] leading-none uppercase tracking-wider rounded-full btn-primary-viral active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50 overflow-hidden relative group shrink-0"
        onclick={handleAction}
        disabled={shopStore.isSubmitting}
      >
        <!-- Shimmer Effect -->
        <div class="absolute inset-0 w-1/3 h-full bg-gradient-to-r from-transparent via-white/10 to-transparent -skew-x-12 animate-shimmer pointer-events-none"></div>
        
        {#if shopStore.isSubmitting}
          <Loader2 class="w-4 h-4 animate-spin shrink-0" />
        {:else}
          <div class="flex flex-col items-center leading-none relative z-surface">
            <span class="text-[12px] font-black tracking-widest whitespace-nowrap">{step === 'selection' ? labels.cta_next : labels.cta_submit}</span>
            {#if step === 'shipping' && totalSaved > 0}
              <span class="text-[9px] font-bold text-white/80 tracking-tighter mt-1.5 whitespace-nowrap drop-shadow-sm">
                TIẾT KIỆM {totalSaved.toLocaleString()}đ | FREESHIP
              </span>
            {:else if step === 'selection'}
              <span class="text-[9px] font-bold text-white/70 tracking-tighter mt-1.5 uppercase whitespace-nowrap">Xác nhận thông tin</span>
            {/if}
          </div>
          
          {#if step === 'selection'}
            <ArrowRight class="w-4 h-4 relative z-surface group-hover:translate-x-1 transition-transform shrink-0" />
          {:else}
            <ShoppingCart class="w-4 h-4 relative z-surface group-hover:scale-110 transition-transform shrink-0" />
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
    
    <p class="mt-6 mb-4 text-[9px] text-white/10 text-center uppercase tracking-[0.3em] font-medium italic">
      🔒 Bảo mật AES-256 mã hóa quân sự
    </p>
  </div>

  <GiftModal />
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

  /* ── Viral Gift Trigger ── */
  .gift-trigger-btn {
    background: linear-gradient(135deg, rgba(219, 39, 119, 0.08) 0%, rgba(131, 24, 67, 0.05) 100%);
    border: 1px solid rgba(219, 39, 119, 0.2);
    border-radius: 1rem;
    padding: 14px 18px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  }
  .gift-trigger-btn:active {
    background: rgba(219, 39, 119, 0.15);
    scale: 0.98;
  }
</style>
