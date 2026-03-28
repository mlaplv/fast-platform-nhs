<script lang="ts">
  import { shopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { portal } from '$lib/actions/portal.ts';
  import { Z_INDEX } from '$lib/core/constants/zIndex.ts';
  import { fade, fly, scale } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import { SHOP_CONFIG } from '$lib/constants/shop';
  import { onMount } from 'svelte';
  import "./slug/LiquidEffects.css";

  interface CustomerInfo {
    phone: string;
    address: string;
  }

  let customer = $state<CustomerInfo>({
    phone: '',
    address: ''
  });

  let validationError = $state<string | null>(null);
  let reservationTime = $state(SHOP_CONFIG.checkout.reservation_time);

  const product = $derived(shopStore.product);
  const mainImage = $derived(resolveMediaUrl(product?.images?.[0] || ''));

  const zIndexStyle = `--z-index: ${Z_INDEX.MODAL}`;

  // ELITE V2.2: Reservation Timer (Rule III.3) thưa sếp!
  onMount(() => {
    const timer = setInterval(() => {
      if (reservationTime > 0) reservationTime--;
    }, 1000);
    return () => clearInterval(timer);
  });

  const formatTime = (s: number) => {
    const mins = Math.floor(s / 60);
    const secs = (s % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  async function handleCheckout() {
    validationError = null;
    if (!customer.phone || customer.phone.length < 10) {
      validationError = "Vui lòng nhập số điện thoại chính xác của Sếp";
      return;
    }
    if (!customer.address || customer.address.length < 10) {
      validationError = "Sếp vui lòng cho em biết địa chỉ nhận hàng chi tiết ạ";
      return;
    }
    await shopStore.submitCheckout({ ...customer, name: 'Khách hàng Elite' });
  }
</script>

{#if shopStore.isCheckoutOpen}
  <div
    use:portal
    transition:fade={{ duration: 400 }}
    class="fixed inset-0 bg-[#020617]/80 backdrop-blur-sm transition-opacity duration-300"
    style="z-index: {Z_INDEX.OVERLAY};"
    onclick={() => shopStore.closeCheckout()}
    onkeydown={(e) => e.key === 'Escape' && shopStore.closeCheckout()}
    role="button"
    aria-label="Close checkout overlay"
    tabindex="-1"
  ></div>

  <div
    use:portal
    transition:fly={{ y: 30, duration: 800, easing: quintOut }}
    class="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[calc(100%-2rem)] max-w-lg glass-liquid text-white rounded-[4rem] p-10 md:p-14 transition-all shadow-[0_80px_250px_rgba(0,0,0,0.9)] border border-white/5"
    style="z-index: var(--z-index); {zIndexStyle}"
  >
    <!-- Header with Trust Indicator -->
    <div class="header flex justify-between items-start mb-10">
      <div in:fly={{ x: -20, duration: 800, easing: quintOut }}>
        <div class="flex items-center gap-3 mb-2">
          <span class="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_12px_#10b981] animate-pulse"></span>
          <span class="text-emerald-500/80 text-[10px] font-black uppercase tracking-[0.4em]">{SHOP_CONFIG.checkout.trust_active}</span>
        </div>
        <h2 class="text-4xl font-black text-white tracking-tighter uppercase leading-none mb-4">{SHOP_CONFIG.checkout.title}</h2>
        
        <!-- Reservation Timer Badge thưa sếp! -->
        <div class="flex items-center gap-2 px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full w-fit backdrop-blur-md">
          <span class="text-[8px] font-bold text-blue-400 uppercase tracking-widest">{SHOP_CONFIG.checkout.reservation_msg}</span>
          <span class="text-[10px] font-black text-white tabular-nums">{formatTime(reservationTime)}</span>
        </div>
      </div>
      <button 
        onclick={() => shopStore.closeCheckout()} 
        class="p-4 bg-white/5 text-white/20 hover:text-white hover:bg-white/10 rounded-full transition-all border border-white/5 active:scale-90"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    {#if shopStore.orderSuccess}
      <div class="success-message text-center py-20" in:scale={{ duration: 800, easing: quintOut }}>
        <div class="inline-flex items-center justify-center w-32 h-32 glass-liquid rounded-[3rem] mb-10 border-blue-500/20 shadow-[0_0_50px_rgba(59,130,246,0.3)]">
          <svg class="w-16 h-16 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" in:fly={{ y: 20, duration: 500, delay: 300 }}>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 class="text-5xl font-black text-white mb-6 uppercase tracking-tighter">{SHOP_CONFIG.checkout.labels.success_title}</h3>
        <p class="text-white/40 leading-relaxed font-medium text-lg max-w-sm mx-auto">{SHOP_CONFIG.checkout.labels.success_msg}</p>
      </div>
    {:else}
      <div class="form-container space-y-8">
        
        <!-- Product Quick Summary thưa sếp! -->
        <div class="product-mini-card flex items-center gap-6 p-5 rounded-[2rem] bg-white/5 border border-white/10 mb-2 relative overflow-hidden group" in:fly={{ y: 20, duration: 800, delay: 200, easing: quintOut }}>
          <div class="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          
          <!-- Neural Scan Line thưa sếp! -->
          <div class="absolute left-0 top-0 w-full h-[1px] bg-gradient-to-r from-transparent via-blue-400/40 to-transparent animate-scan z-20"></div>

          <div class="w-20 h-20 rounded-2xl overflow-hidden bg-white/5 shrink-0 border border-white/5 relative">
             <img src="{mainImage}" alt="{product?.name}" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" />
             <div class="absolute inset-0 bg-blue-500/10 mix-blend-overlay"></div>
          </div>
          <div class="relative z-10 flex-grow">
            <span class="text-[8px] font-bold text-blue-400 uppercase tracking-widest mb-1 block">{SHOP_CONFIG.checkout.labels.summary}</span>
            <h4 class="font-black text-lg uppercase tracking-tight text-white/90 leading-tight mb-2">{product?.name}</h4>
            
            <div class="flex items-center justify-between">
               <div class="flex items-center gap-2">
                 <span class="text-white/30 text-[9px] font-bold uppercase tracking-widest">Elite Delivery</span>
                 <span class="w-1 h-1 rounded-full bg-emerald-500/40"></span>
                 <span class="text-emerald-400/80 text-[8px] font-black uppercase tracking-tighter tabular-nums">ID: {product?.id?.slice(0,8)}</span>
               </div>

               <!-- ELITE QUANTITY SELECTOR thưa sếp! -->
               <div class="flex items-center bg-black/40 border border-white/5 p-1 rounded-xl gap-2 h-8">
                 <button 
                   onclick={() => shopStore.setQuantity(shopStore.quantity - 1)}
                   class="w-6 h-6 flex items-center justify-center rounded-lg hover:bg-white/10 text-white/40 hover:text-white transition-all active:scale-90"
                 >−</button>
                 <span class="text-xs font-black text-blue-400 w-4 text-center tabular-nums">{shopStore.quantity}</span>
                 <button 
                   onclick={() => shopStore.setQuantity(shopStore.quantity + 1)}
                   class="w-6 h-6 flex items-center justify-center rounded-lg hover:bg-white/10 text-white/40 hover:text-white transition-all active:scale-90"
                 >+</button>
               </div>
            </div>
          </div>
        </div>

        <!-- Solidified Inputs thưa sếp! -->
        <div class="input-group group" in:fly={{ y: 20, duration: 800, delay: 300, easing: quintOut }}>
          <label class="block text-[9px] font-black text-white/40 uppercase tracking-[0.3em] mb-4 ml-4" for="phone">{SHOP_CONFIG.checkout.labels.phone} <span class="text-blue-500">*</span></label>
          <div class="relative">
            <input
              type="tel"
              id="phone"
              bind:value={customer.phone}
              placeholder="{SHOP_CONFIG.checkout.placeholders.phone}"
              class="w-full p-6 bg-slate-900/40 border border-white/10 rounded-[1.75rem] outline-none focus:border-blue-500/60 focus:bg-blue-500/5 text-2xl font-black text-white placeholder:text-white/5 transition-all shadow-inner"
            />
            <div class="absolute right-6 top-1/2 -translate-y-1/2 opacity-20">📱</div>
          </div>
        </div>

        <div class="input-group group" in:fly={{ y: 20, duration: 800, delay: 400, easing: quintOut }}>
          <label class="block text-[9px] font-black text-white/40 uppercase tracking-[0.3em] mb-4 ml-4" for="address">{SHOP_CONFIG.checkout.labels.address} <span class="text-blue-500">*</span></label>
          <div class="relative">
            <textarea
              id="address"
              bind:value={customer.address}
              rows="2"
              placeholder="{SHOP_CONFIG.checkout.placeholders.address}"
              class="w-full p-6 bg-slate-900/40 border border-white/10 rounded-[1.75rem] outline-none focus:border-blue-500/60 focus:bg-blue-500/5 text-lg font-bold text-white placeholder:text-white/5 transition-all resize-none shadow-inner"
            ></textarea>
            <div class="absolute right-6 top-6 opacity-20">📍</div>
          </div>
        </div>

        {#if validationError}
          <div class="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-[10px] text-red-400 font-bold uppercase tracking-widest flex items-center gap-3 animate-shake" in:fly={{ y: -10 }}>
            <span class="w-1.5 h-1.5 bg-red-400 rounded-full animate-ping"></span>
            {validationError}
          </div>
        {/if}

        <!-- Conversion Badges thưa sếp! -->
        <div class="flex items-center justify-between gap-2 px-1" in:fly={{ y: 20, duration: 800, delay: 500, easing: quintOut }}>
           {#each SHOP_CONFIG.checkout.trust_badges as badge}
             <div class="flex items-center gap-2.5 px-4 py-3 bg-white/5 rounded-2xl border border-white/10 flex-1 justify-center group/badge hover:bg-white/10 transition-colors">
                <span class="text-lg group-hover/badge:scale-125 transition-transform">{badge.icon}</span>
                <span class="text-[8px] font-black uppercase {badge.color} tracking-tighter opacity-70 group-hover/badge:opacity-100">{badge.label}</span>
             </div>
           {/each}
        </div>

        <div class="summary pt-8 border-t border-white/5" in:fly={{ y: 20, duration: 800, delay: 600, easing: quintOut }}>
          <div class="flex justify-between items-end mb-8 px-4">
            <span class="text-white/20 font-black uppercase tracking-[0.4em] text-[10px] mb-2">{SHOP_CONFIG.checkout.labels.total}</span>
            <div class="text-right">
              <span class="block text-5xl font-black text-white drop-shadow-[0_10px_20px_rgba(255,255,255,0.1)]">{shopStore.totalAmount.toLocaleString()}đ</span>
            </div>
          </div>

          <button
            onclick={handleCheckout}
            disabled={shopStore.isSubmitting}
            class="group relative w-full py-7 bg-blue-600 text-white rounded-[2rem] font-black text-3xl shadow-[0_30px_80px_-15px_rgba(37,99,235,0.5)] overflow-hidden active:scale-[0.98] transition-all flex items-center justify-center gap-4 hover:bg-blue-500"
          >
            <!-- Liquid Shine Effect thưa sếp! -->
            <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-[1500ms] ease-in-out pointer-events-none"></div>

            {#if shopStore.isSubmitting}
               <span class="animate-pulse flex items-center gap-3">
                 <svg class="w-6 h-6 animate-spin" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                 {SHOP_CONFIG.checkout.labels.processing}
               </span>
            {:else}
              <span class="relative z-10">{SHOP_CONFIG.checkout.labels.cta}</span>
              <svg class="w-8 h-8 relative z-10 group-hover:translate-x-2 transition-transform h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            {/if}
          </button>
          <p class="text-center text-[10px] font-black text-white/10 uppercase tracking-[0.5em] mt-8">Secure by Elite Labs AI</p>
        </div>
      </div>
    {/if}
  </div>
{/if}

<style>
  :global(.glass-liquid) {
    transition: all 0.6s cubic-bezier(0.23, 1, 0.32, 1);
  }

  @keyframes scan {
    0% { transform: translateY(-100%); opacity: 0; }
    50% { opacity: 1; }
    100% { transform: translateY(500%); opacity: 0; }
  }

  :global(.animate-scan) {
    animation: scan 4s linear infinite;
  }

  /* Shaking error for emphasis */
  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-5px); }
    75% { transform: translateX(5px); }
  }
  :global(.animate-shake) {
    animation: shake 0.4s ease-in-out;
  }
</style>


