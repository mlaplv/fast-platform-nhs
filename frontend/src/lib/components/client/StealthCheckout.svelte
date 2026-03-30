<script lang="ts">
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { portal } from '$lib/core/actions/portal';
  import { Z_INDEX } from '$lib/core/constants/zIndex.ts';
  import { fade, fly, scale } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import { onMount } from 'svelte';

  const shopStore = getShopStore();

  // Optimized DOM refs (Native! KHÔNG dùng $state)
  let nameRef: HTMLInputElement | undefined;
  let phoneRef: HTMLInputElement | undefined;
  let addressRef: HTMLTextAreaElement | undefined;
  
  let validationError = $state<string | null>(null);
  let reservationTime = $state(501); 

  // Derived (These stay reactive!)
  const totalPrice = $derived(shopStore.totalAmount);
  const isSubmitting = $derived(shopStore.isSubmitting);
  const orderSuccess = $derived(shopStore.orderSuccess);
  const variants = $derived(shopStore.product?.variants || []);
  const hasVariants = $derived(variants.length > 1);

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

  function validateInput() {
    const phone = phoneRef?.value || '';
    const address = addressRef?.value || '';
    
    if (phone && phone.length > 0 && phone.length < 10) {
      validationError = "Số điện thoại cần đủ 10 chữ số";
    } else if (address && address.length > 0 && address.length < 5) {
      validationError = "Vui lòng nhập địa chỉ chi tiết hơn";
    } else {
      validationError = null;
    }
  }

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

  async function handleSubmit() {
    validateInput();
    if (validationError) return;
    
    const name = nameRef?.value || 'Khách lẻ';
    const phone = phoneRef?.value || '';
    const address = addressRef?.value || '';

    if (!phone || !address) {
      validationError = "Vui lòng điền đủ SĐT và Địa chỉ";
      return;
    }

    await shopStore.submitCheckout({ 
      phone, 
      address, 
      name 
    });
  }
</script>

{#if shopStore.isCheckoutOpen}
  <div
    onclick={() => shopStore.closeCheckout()}
    class="fixed inset-0 bg-slate-950/90 backdrop-blur-sm z-[1000]"
    role="button"
    aria-label="Đóng"
    tabindex="-1"
  ></div>

  <div
    class="fixed bottom-0 left-0 right-0 md:top-1/2 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2 md:bottom-auto w-full md:max-w-xl bg-slate-900 border border-white/10 rounded-t-[2.5rem] md:rounded-[2.5rem] p-6 md:p-10 shadow-2xl flex flex-col overflow-hidden max-h-[95vh] z-[1001]"
  >
    <!-- Optimized BG Decorations! -->
    <div class="absolute -top-32 -right-32 w-80 h-80 bg-sky-500/10 rounded-full blur-[100px] pointer-events-none animate-pulse"></div>
    <div class="absolute -bottom-32 -left-32 w-80 h-80 bg-blue-600/10 rounded-full blur-[100px] pointer-events-none animate-pulse"></div>

    <button 
      class="absolute top-6 right-6 text-slate-500 hover:text-white transition-colors p-2 z-20"
      onclick={() => shopStore.closeCheckout()}
    >
      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
    </button>

    <div class="relative z-10 flex flex-col gap-6 overflow-y-auto custom-scrollbar pr-1">
        <header>
          <h2 class="text-4xl font-black text-white tracking-tighter uppercase italic leading-none mb-1">Xác nhận đơn</h2>
          <div class="flex items-center gap-2">
             <span class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
             <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest">Đang kết nối bảo mật (AES-256 SSL)</span>
          </div>
        </header>

        <!-- Variant Selection! -->
        {#if hasVariants}
          <div class="space-y-4">
             <div class="flex items-baseline justify-between mb-1">
                <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest leading-none">Phân loại sản phẩm:</span>
                <span class="bg-sky-500/10 text-sky-400 text-[8px] font-black px-1.5 py-0.5 rounded border border-sky-500/20">ELITE CHOICE</span>
             </div>
             <div class="grid grid-cols-3 gap-3">
                {#each variants as v}
                  <button 
                    onclick={() => shopStore.selectVariant(v)}
                    class="flex flex-col p-2 rounded-[1.5rem] border-2 transition-all group/v {shopStore.variant?.id === v.id ? 'border-sky-500 bg-sky-500/10' : 'border-white/5 bg-white/5 opacity-40 hover:opacity-100'}"
                  >
                    <div class="aspect-square rounded-xl overflow-hidden bg-slate-950 mb-2 border border-white/5 relative">
                       <img src={getVariantImage(v)} alt={getVariantName(v)} class="w-full h-full object-cover group-hover/v:scale-110 transition-transform duration-700" />
                       {#if shopStore.variant?.id === v.id}
                          <div class="absolute inset-0 bg-sky-500/10 flex items-center justify-center">
                            <div class="w-6 h-6 bg-white rounded-full flex items-center justify-center shadow-lg transform scale-110">
                              <svg class="w-4 h-4 text-sky-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M5 13l4 4L19 7" /></svg>
                            </div>
                          </div>
                       {/if}
                    </div>
                    <span class="text-[9px] font-black text-white uppercase text-center line-clamp-1 mb-1 px-1">{getVariantName(v)}</span>
                    <span class="text-[11px] font-black text-sky-400 text-center tabular-nums italic tracking-tighter">{(v.discountPrice || v.price).toLocaleString()}đ</span>
                  </button>
                {/each}
             </div>
          </div>
        {/if}

        <div class="grid grid-cols-2 gap-4">
           <!-- Quantity (Static!) -->
           <div class="bg-white/5 border border-white/5 p-2 rounded-2xl flex items-center justify-between">
              <span class="text-[10px] font-black text-slate-500 uppercase tracking-tight ml-2">Số lượng:</span>
              <div class="flex items-center gap-4 bg-slate-950 px-3 py-1.5 rounded-xl border border-white/5 shadow-inner">
                 <button onclick={() => shopStore.setQuantity(shopStore.quantity - 1)} class="w-6 h-6 text-slate-500 hover:text-white font-black">-</button>
                 <span class="text-sm font-black text-white tabular-nums w-4 text-center">{shopStore.quantity}</span>
                 <button onclick={() => shopStore.setQuantity(shopStore.quantity + 1)} class="w-6 h-6 text-slate-500 hover:text-white font-black">+</button>
              </div>
           </div>
           <!-- Time (Static!) -->
           <div class="bg-white/5 border border-white/5 p-2 rounded-2xl flex items-center justify-between">
              <span class="text-[10px] font-black text-slate-500 uppercase tracking-tight ml-2">Giữ hàng:</span>
              <span class="text-sm font-black text-white tabular-nums mr-2">{formatTime(reservationTime)}</span>
           </div>
        </div>

        <!-- Inputs (NATIVE ONLY!) -->
        <div class="space-y-4">
          <div class="relative group/input">
            <input 
              type="text" 
              bind:this={nameRef}
              placeholder="HỌ TÊN NGƯỜI NHẬN (KHÔNG BẮT BUỘC)" 
              class="w-full px-6 py-4 bg-white/[0.03] border-2 border-white/5 focus:border-sky-500/50 focus:bg-white/[0.05] rounded-[1.5rem] outline-none placeholder:text-slate-600 text-white font-black text-sm shadow-[inset_0_2px_10px_rgba(0,0,0,0.5)] uppercase tracking-wider" 
            />
          </div>

          <div class="relative group/input">
            <input 
              type="tel" 
              bind:this={phoneRef}
              onblur={validateInput}
              placeholder="SĐT NHẬN TƯ VẤN Y KHOA (Bảo mật)" 
              class="w-full px-6 py-5 bg-white/[0.03] border-2 {validationError ? 'border-red-500/30' : 'border-white/5'} focus:border-sky-500/50 focus:bg-white/[0.05] rounded-[1.5rem] outline-none placeholder:text-slate-600 text-white font-black text-xl shadow-[inset_0_2px_10px_rgba(0,0,0,0.5)] uppercase tracking-wider" 
            />
            <div class="absolute right-6 top-1/2 -translate-y-1/2 text-slate-700 text-[10px] font-black pointer-events-none tracking-widest group-focus-within/input:text-sky-500/50 transition-colors">10+ SỐ</div>
          </div>

          <textarea 
            bind:this={addressRef}
            onblur={validateInput}
            rows="2" 
            placeholder="ĐỊA CHỈ GIAO KÍN ĐÁO (Che tên sản phẩm)" 
            class="w-full px-6 py-5 bg-white/[0.03] border-2 {validationError ? 'border-red-500/30' : 'border-white/5'} focus:border-sky-500/50 focus:bg-white/[0.05] rounded-[1.5rem] outline-none placeholder:text-slate-600 text-white font-black text-sm shadow-[inset_0_2px_10px_rgba(0,0,0,0.5)] uppercase resize-none leading-relaxed"
          ></textarea>
          
          {#if validationError}
            <div class="px-2 text-red-500 text-[10px] font-black uppercase tracking-widest">{validationError}</div>
          {/if}
        </div>

        <!-- Promotion (Static!) -->
        {#if shopStore.appliedDeal}
          <div class="flex items-center justify-between bg-sky-500/10 border border-sky-500/20 px-5 py-4 rounded-2xl">
             <div class="flex flex-col">
                <span class="text-[8px] font-black text-sky-400 uppercase tracking-widest">QUÀ TẶNG ELITE ĐÃ ÁP DỤNG:</span>
                <span class="text-sm font-black text-white uppercase italic">{shopStore.appliedDeal.label}</span>
             </div>
             <button type="button" onclick={() => shopStore.setQuantity(1)} class="text-[10px] font-black text-slate-500 hover:text-white uppercase px-3 py-2 border border-white/5 rounded-xl transition-all">Hủy</button>
          </div>
        {:else if shopStore.nextDeal}
          <button 
            type="button" 
            onclick={() => shopStore.setQuantity(shopStore.quantity + shopStore.nextDeal!.missing)}
            class="group flex items-center justify-between bg-amber-500/10 border border-amber-500/30 px-5 py-4 rounded-2xl hover:bg-amber-500/20 transition-all active:scale-[0.98]"
          >
             <div class="flex items-center gap-3">
                <span class="text-2xl">🎁</span>
                <div class="flex flex-col text-left">
                   <span class="text-[8px] font-black text-amber-500 uppercase tracking-widest">SIÊU ƯU ĐÃI:</span>
                   <span class="text-[13px] font-black text-white italic">Thêm {shopStore.nextDeal.missing} hộp nhận <span class="text-amber-400 underline decoration-2">{shopStore.nextDeal.deal.label}</span></span>
                </div>
             </div>
             <div class="bg-amber-500 text-black text-[9px] font-black px-2 py-1.5 rounded-lg uppercase transition-transform group-hover:scale-110">NHẬN NGAY</div>
          </button>
        {/if}

        <footer class="pt-6 border-t border-white/10 space-y-6">
          <div class="flex items-center justify-between">
            <div class="flex flex-col">
               <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Cần thanh toán (Đã gồm ship):</span>
               <div class="flex items-baseline gap-2">
                 <span class="text-4xl font-black text-white tracking-tighter tabular-nums italic">{(totalPrice || 0).toLocaleString()}đ</span>
                 {#if shopStore.originalPrice * shopStore.quantity > totalPrice}
                   <span class="text-sm font-bold text-slate-600 line-through">{(shopStore.originalPrice * shopStore.quantity).toLocaleString()}đ</span>
                 {/if}
               </div>
            </div>
            <div class="p-3 bg-emerald-500/20 rounded-2xl border border-emerald-500/30 rotate-3">
               <span class="text-[11px] font-black text-emerald-400 uppercase tracking-tight">MIỄN PHÍ SHIP 🚚</span>
            </div>
          </div>

          {#if shopStore.error}
            <div class="px-4 py-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-500 text-[10px] font-black text-center uppercase tracking-widest">{shopStore.error}</div>
          {/if}

          <button 
            onclick={handleSubmit}
            disabled={isSubmitting}
            class="w-full py-6 bg-sky-500 hover:bg-sky-400 disabled:bg-slate-800 text-white font-black text-2xl rounded-full flex items-center justify-center gap-4 transition-all hover:scale-[1.03] active:scale-[0.97] shadow-2xl shadow-sky-500/30 group"
          >
            {#if isSubmitting}
              <div class="w-6 h-6 border-4 border-white/30 border-t-white rounded-full animate-spin"></div>
              HỆ THỐNG ĐANG XỬ LÝ...
            {:else}
              <span class="italic tracking-tighter">XÁC NHẬN ĐƠN HÀNG</span>
              <span class="w-10 h-10 bg-white/10 rounded-full flex items-center justify-center group-hover:bg-white/20 transition-all">→</span>
            {/if}
          </button>
          
          <div class="flex justify-center gap-3 opacity-30 grayscale">
             <div class="px-2 py-1 border border-white/20 rounded text-[7px] font-black">PCI DSS</div>
             <div class="px-2 py-1 border border-white/20 rounded text-[7px] font-black">AES-256</div>
             <div class="px-2 py-1 border border-white/20 rounded text-[7px] font-black">2FA PROTECTED</div>
          </div>
        </footer>
      </div>
  </div>
{/if}

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 3px; }
  .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.05); border-radius: 10px; }
  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-2px); }
    20%, 40%, 60%, 80% { transform: translateX(2px); }
  }
  .animate-shake { animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both; }
</style>
