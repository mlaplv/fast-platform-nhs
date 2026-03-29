<script lang="ts">
  import { shopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { portal } from '$lib/core/actions/portal';
  import { Z_INDEX } from '$lib/core/constants/zIndex.ts';
  import { fade, fly, scale } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import { onMount } from 'svelte';

  // State
  let phone = $state('');
  let address = $state('');
  let validationError = $state<string | null>(null);
  let reservationTime = $state(501); // 08:21 = 501s

  // Derived
  const totalPrice = $derived(shopStore.totalAmount);
  const isSubmitting = $derived(shopStore.isSubmitting);
  const orderSuccess = $derived(shopStore.orderSuccess);
  const variants = $derived(shopStore.product?.variants || []);
  const hasVariants = $derived(variants.length > 1);

  // Timer logic
  onMount(() => {
    const timer = setInterval(() => {
      if (reservationTime > 0) reservationTime--;
    }, 1000);
    return () => clearInterval(timer);
  });

  const formatTime = (s: number) => {
    const mins = Math.floor(s / 60).toString().padStart(2, '0');
    const secs = (s % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  function getVariantName(v: any) {
    if (!shopStore.product?.tierVariations) return v.sku || 'Sản phẩm';
    return v.tierIndex.map((idx: number, tierIdx: number) => {
        const tier = shopStore.product!.tierVariations[tierIdx];
        return tier?.options[idx] || '';
    }).filter(Boolean).join(' - ');
  }

  function getVariantImage(v: any) {
    if (!shopStore.product?.tierVariations) return shopStore.product?.images?.[0] || '';
    for (let i = 0; i < v.tierIndex.length; i++) {
        const img = shopStore.product!.tierVariations[i]?.images[v.tierIndex[i]];
        if (img) return img;
    }
    return shopStore.product?.images?.[0] || '';
  }

  async function handleCheckout() {
    validationError = null;
    if (!phone || phone.length < 10) {
      validationError = "Vui lòng nhập số điện thoại chính xác để nhận tư vấn y khoa";
      return;
    }
    if (!address || address.length < 10) {
      validationError = "Vui lòng cung cấp địa chỉ giao hàng chi tiết để đảm bảo nhận hàng kín đáo";
      return;
    }
    await shopStore.submitCheckout({ 
      phone, 
      address, 
      name: "Bệnh nhân" 
    });
  }
</script>

{#if shopStore.isCheckoutOpen}
  <div
    use:portal
    transition:fade={{ duration: 300 }}
    class="fixed inset-0 bg-slate-950/60 backdrop-blur-sm"
    style="z-index: {Z_INDEX.OVERLAY};"
    onclick={() => shopStore.closeCheckout()}
    onkeydown={(e) => e.key === 'Escape' && shopStore.closeCheckout()}
    role="button"
    aria-label="Đóng bảng thanh toán"
    tabindex="-1"
  ></div>

  <div
    use:portal
    transition:fly={{ y: 50, duration: 600, easing: quintOut }}
    class="fixed bottom-0 left-0 right-0 md:top-1/2 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2 md:bottom-auto w-full md:max-w-lg bg-[#020617]/90 backdrop-blur-3xl rounded-t-[2.5rem] md:rounded-[2.5rem] p-6 md:p-10 shadow-[0_45px_150px_-20px_rgba(0,0,0,0.6)] border border-white/10 overflow-hidden group/modal"
    style="z-index: {Z_INDEX.MODAL};"
  >
    <!-- Liquid Gradient Background Decoration (Cinematic thưa sếp!) -->
    <div class="absolute -top-32 -right-32 w-80 h-80 bg-sky-500/10 rounded-full blur-[100px] pointer-events-none transition-all duration-1000 group-hover/modal:bg-sky-500/20"></div>
    <div class="absolute -bottom-32 -left-32 w-80 h-80 bg-blue-600/10 rounded-full blur-[100px] pointer-events-none transition-all duration-1000 group-hover/modal:bg-blue-600/20"></div>

    {#if orderSuccess}
      <div class="text-center py-16" in:scale={{ duration: 500 }}>
        <div class="w-24 h-24 bg-sky-500/20 text-sky-400 rounded-[2rem] flex items-center justify-center mx-auto mb-8 shadow-2xl border border-sky-400/30">
          <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 class="text-3xl font-black text-white mb-3 uppercase tracking-tighter italic">GỬI THÔNG TIN THÀNH CÔNG</h2>
        <p class="text-slate-400 font-medium">Bác sĩ sẽ liên hệ hỗ trợ bạn ngay lập tức.</p>
      </div>
    {:else}
      <!-- Header Section -->
      <div class="mb-6 relative">
        <div class="flex items-center gap-2 mb-2">
            <span class="px-2 py-0.5 bg-sky-500/20 text-sky-400 text-[9px] font-black tracking-widest uppercase rounded-md flex items-center gap-1 border border-sky-400/20">
              🛡️ BẢO MẬT Y KHOA TUYỆT ĐỐI
            </span>
        </div>
        <h2 class="text-3xl font-black text-white leading-none tracking-tighter uppercase mb-2">HOÀN TẤT LIỆU TRÌNH</h2>
        
        <!-- Scarcity FOMO Badge -->
        <div class="flex items-center gap-2 mb-4">
           <span class="inline-flex w-1.5 h-1.5 bg-red-500 rounded-full animate-ping"></span>
           <span class="text-[11px] font-bold text-red-500 uppercase tracking-tight">
             🔥 Kho chỉ còn <span class="bg-red-500 text-white px-1.5 rounded ml-1">02</span> bộ cuối cùng cho khu vực của bạn
           </span>
        </div>

        <!-- Countdown Banner -->
        <div class="py-2.5 px-4 bg-white/5 border border-white/5 rounded-2xl flex items-center justify-between backdrop-blur-md shadow-inner">
          <span class="text-[11px] text-slate-400 font-bold uppercase tracking-wider">Phiên giao dịch sẽ hết hạn sau:</span>
          <span class="text-base font-black text-white tabular-nums font-mono">{formatTime(reservationTime)}</span>
        </div>
      </div>

      <div class="space-y-6">
        <!-- Variant & Quantity Controls -->
        <div class="space-y-4 pt-2 border-t border-white/5">
          {#if hasVariants}
             <div class="grid grid-cols-1 gap-2">
               <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Lựa chọn liệu trình:</span>
               <div class="grid grid-cols-3 gap-2">
                 {#each variants as v}
                    <button 
                      onclick={() => shopStore.selectVariant(v)}
                      class="flex-col p-1.5 rounded-xl border-2 transition-all flex group/variant {shopStore.variant?.id === v.id ? 'border-sky-500 bg-sky-500/10 text-white shadow-[0_0_15px_rgba(14,165,233,0.2)]' : 'border-white/5 bg-white/5 text-slate-500 hover:border-white/10 hover:text-slate-300'}"
                    >
                      <div class="w-full aspect-square rounded-lg overflow-hidden bg-slate-900 border border-white/5 mb-2">
                        <img src={getVariantImage(v)} alt={getVariantName(v)} class="w-full h-full object-cover group-hover/variant:scale-110 transition-transform duration-500" />
                      </div>
                      <div class="flex flex-col gap-0.5 text-center w-full px-0.5">
                        <span class="text-[9px] font-black uppercase tracking-tight line-clamp-1">{getVariantName(v)}</span>
                        <div class="flex items-center justify-center gap-1 mt-0.5">
                           {#if v.discountPrice && v.discountPrice < v.price}
                             <span class="text-[8px] text-slate-500 line-through opacity-70">{v.price.toLocaleString()}đ</span>
                           {/if}
                           <span class="text-base font-black tracking-tighter text-sky-400 leading-none">{v.discountPrice?.toLocaleString() || v.price?.toLocaleString()}đ</span>
                        </div>
                      </div>
                      <div class="mt-1.5 flex justify-center w-full">
                         <div class="w-3.5 h-3.5 rounded-full border-2 flex items-center justify-center transition-all {shopStore.variant?.id === v.id ? 'bg-sky-500 border-sky-500' : 'border-slate-700'}">
                            {#if shopStore.variant?.id === v.id}
                               <svg class="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M5 13l4 4L19 7" /></svg>
                            {/if}
                         </div>
                      </div>
                    </button>
                 {/each}
               </div>
             </div>
          {/if}

          <div class="flex items-center justify-between bg-white/5 border border-white/5 p-2.5 rounded-2xl">
             <span class="text-[11px] font-black text-slate-500 uppercase tracking-widest ml-2">Số lượng đơn vị:</span>
             <div class="flex items-center gap-6 bg-slate-900 shadow-xl border border-white/10 p-1.5 rounded-xl">
               <button 
                 onclick={() => shopStore.setQuantity(shopStore.quantity - 1)}
                 class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-white/5 text-white font-bold transition-all active:scale-90"
               >−</button>
               <span class="font-black text-lg text-white w-4 text-center tabular-nums">{shopStore.quantity}</span>
               <button 
                 onclick={() => shopStore.setQuantity(shopStore.quantity + 1)}
                 class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-white/5 text-white font-bold transition-all active:scale-90"
               >+</button>
             </div>
          </div>
        </div>

        <!-- Input Fields -->
        <div class="space-y-3">
          <div class="group relative">
            <input
              type="tel"
              bind:value={phone}
              placeholder="Số điện thoại nhận tư vấn (Bảo mật 100%)"
              class="w-full px-5 py-5 text-xl bg-white/5 border-2 border-transparent focus:border-sky-500/20 focus:bg-white/10 rounded-[1.25rem] outline-none transition-all placeholder:text-slate-600 text-white font-black shadow-inner"
            />
          </div>
          <div class="group relative">
            <textarea
              bind:value={address}
              rows="2"
              placeholder="Địa chỉ giao hàng (Giao kín đáo, che tên sản phẩm)"
              class="w-full px-5 py-5 text-base bg-white/5 border-2 border-transparent focus:border-sky-500/20 focus:bg-white/10 rounded-[1.25rem] outline-none transition-all placeholder:text-slate-600 text-white font-bold shadow-inner resize-none"
            ></textarea>
          </div>
        </div>

        <!-- Validation Error -->
        {#if validationError}
          <div class="text-[10px] text-red-500 font-bold uppercase tracking-tight flex items-center gap-2 ml-1" in:fade>
            <span class="w-2 h-2 bg-red-500 rounded-full animate-pulse shadow-[0_0_8px_#ef4444]"></span>
            {validationError}
          </div>
        {/if}

        <!-- Shipping Incentive Badge -->
        <div class="flex items-center gap-3 px-5 py-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl">
           <span class="text-lg">🎁</span>
           <div class="flex flex-col">
              <span class="text-[11px] font-black text-emerald-400 uppercase tracking-widest">ƯU ĐÃI VẬN CHUYỂN:</span>
              <span class="text-[13px] font-bold text-white">Miễn phí giao hàng toàn quốc (Tiết kiệm 30.000đ)</span>
           </div>
        </div>

        <!-- Upsell Card -->
        <div 
          class="p-5 bg-sky-500 text-white rounded-[1.5rem] cursor-pointer transition-all hover:scale-[1.02] shadow-2xl shadow-sky-500/20 active:scale-100 relative overflow-hidden"
          onclick={() => shopStore.toggleOrderBump()}
          onkeydown={(e) => e.key === ' ' && shopStore.toggleOrderBump()} 
          role="button"
          tabindex="0"
        >
          <!-- Shine effect (Premium thưa sếp!) -->
          <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent -translate-x-[200%] animate-[shimmer_3s_infinite] pointer-events-none"></div>

          <div class="flex items-start gap-4 relative z-10">
            <div class="w-6 h-6 rounded-lg bg-white shrink-0 flex items-center justify-center {shopStore.hasOrderBump ? '' : 'bg-white/20'} transition-all">
                {#if shopStore.hasOrderBump}
                   <svg class="w-5 h-5 text-sky-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M5 13l4 4L19 7" /></svg>
                {/if}
            </div>
            <div>
              <p class="text-[12px] font-black leading-tight uppercase tracking-tight">
                🎁 DƯỢC SĨ KHUYÊN DÙNG: XỊT KHỬ MÙI GIÀY NANO
              </p>
              <div class="flex items-baseline gap-2 mt-1">
                <span class="text-lg font-black tracking-tight">+99.000đ</span>
                <span class="text-[11px] text-white/60 line-through font-bold">250.000đ</span>
              </div>
              <p class="text-[10px] text-white/80 mt-1 font-medium font-serif italic leading-tight">
                Tiêu diệt 99.9% vi khuẩn sinh mùi cho giày & tất. Tỷ lệ khách hàng mua lại đạt 98%.
              </p>
            </div>
          </div>
        </div>

        <!-- Medical Guarantees -->
        <div class="flex flex-col gap-2 pt-2 px-1">
          <div class="flex items-center gap-3 text-[11px] text-slate-400 font-black uppercase tracking-tight">
            <span class="w-5 h-5 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center shrink-0 border border-emerald-500/20">✔</span> 
            GIAO HÀNG HĐ 0 ĐỒNG - ĐÓNG GÓI BẢO MẬT
          </div>
          <div class="flex items-center gap-3 text-[11px] text-slate-400 font-black uppercase tracking-tight">
            <span class="w-5 h-5 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center shrink-0 border border-emerald-500/20">✔</span> 
            KIỂM TRA HÀNG ƯNG Ý MỚI THANH TOÁN (COD)
          </div>
        </div>

        <!-- CTA Section -->
        <div class="space-y-4 pt-4 border-t border-white/5">
          <div class="flex items-center justify-between px-2">
            <div class="flex flex-col">
               <span class="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Tổng giá trị thanh toán:</span>
               <div class="flex items-baseline gap-2">
                 <span class="text-3xl font-black text-white tracking-tighter tabular-nums">{totalPrice.toLocaleString()}đ</span>
                 {#if shopStore.originalPrice * shopStore.quantity > totalPrice}
                   <span class="text-sm font-bold text-slate-500 line-through opacity-70">{(shopStore.originalPrice * shopStore.quantity).toLocaleString()}đ</span>
                 {/if}
                 <span class="text-[8px] font-medium text-slate-500 tracking-normal italic leading-none">(đã bao gồm tất phí, kiểm hàng & thanh toán)</span>
               </div>
            </div>
            <div class="w-12 h-12 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center text-white text-xl animate-bounce-subtle">
               🛒
            </div>
          </div>

          <button
            onclick={handleCheckout}
            disabled={isSubmitting}
            class="w-full py-6 bg-sky-500 hover:bg-sky-400 text-white rounded-3xl font-black text-xl transition-all active:scale-[0.97] flex items-center justify-center gap-3 shadow-2xl shadow-sky-500/40 group/btn"
          >
            {#if isSubmitting}
              <div class="w-6 h-6 border-4 border-white/20 border-t-white rounded-full animate-spin"></div>
              XỬ LÝ DỮ LIỆU...
            {:else}
              XÁC NHẬN ĐẶT HÀNG KÍN ĐÁO 
              <span class="text-2xl group-hover/btn:translate-x-2 transition-transform duration-300">➔</span>
            {/if}
          </button>

          <p class="text-center text-[9px] text-slate-500 font-bold px-6 leading-relaxed uppercase tracking-widest">
            Thông tin mã hóa 256-bit chuẩn y khoa bởi Nhà Thuốc Hồng Sơn.
          </p>
        </div>
      </div>
    {/if}
    
    <!-- Close Button -->
    <button
      onclick={() => shopStore.closeCheckout()}
      class="absolute top-8 right-8 p-3 text-slate-600 hover:text-white transition-colors hidden md:block"
    >
      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" /></svg>
    </button>
  </div>
{/if}

<style>
  @keyframes shimmer {
    from { transform: translateX(-150%); }
    to { transform: translateX(150%); }
  }

  @keyframes bounce-subtle {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-3px); }
  }

  :global(.animate-bounce-subtle) {
    animation: bounce-subtle 2s ease-in-out infinite;
  }

  /* Base styles for premium feel thưa sếp! */
  :global(body) {
    overflow: hidden;
  }
</style>




