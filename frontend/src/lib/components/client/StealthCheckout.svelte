<script lang="ts">
  import { shopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { portal } from '$lib/actions/portal.ts';
  import { Z_INDEX } from '$lib/core/constants/zIndex.ts';
  import { fade, fly, scale } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import "./slug/LiquidEffects.css";

  interface CustomerInfo {
    phone: string;
    address: string;
  }

  let customer = $state<CustomerInfo>({
    phone: '',
    address: ''
  });

  const product = $derived(shopStore.product);
  const mainImage = $derived(resolveMediaUrl(product?.images?.[0] || ''));

  const zIndexStyle = `--z-index: ${Z_INDEX.MODAL}`;

  async function handleCheckout() {
    if (!customer.phone || !customer.address) {
      alert("Vui lòng điền đủ Số điện thoại và Địa chỉ để nhận hàng");
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
    <div class="header flex justify-between items-center mb-12">
      <div in:fly={{ x: -20, duration: 800, easing: quintOut }}>
        <div class="flex items-center gap-3 mb-1">
          <span class="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_10px_#10b981]"></span>
          <span class="text-emerald-500/80 text-[10px] font-black uppercase tracking-[0.3em]">Neural Encryption Active</span>
        </div>
        <h2 class="text-4xl font-black text-white tracking-tighter uppercase leading-none">CHECKOUT</h2>
      </div>
      <button 
        onclick={() => shopStore.closeCheckout()} 
        class="p-4 bg-white/5 text-white/20 hover:text-white rounded-full transition-all border border-white/5"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    {#if shopStore.orderSuccess}
      <div class="success-message text-center py-20" in:scale={{ duration: 800, easing: quintOut }}>
        <div class="inline-flex items-center justify-center w-32 h-32 glass-liquid rounded-[3rem] mb-10 border-blue-500/20">
          <svg class="w-16 h-16 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 class="text-5xl font-black text-white mb-6 uppercase tracking-tighter">SUCCESS</h3>
        <p class="text-white/40 leading-relaxed font-medium text-lg max-w-sm mx-auto">Đơn hàng đã được chuyển tới trung tâm hậu cần. Nhân viên hỗ trợ sẽ gọi tới Sếp ngay.</p>
      </div>
    {:else}
      <div class="form-container space-y-10">
        
        <!-- Product Quick Summary -->
        <div class="product-mini-card flex items-center gap-6 p-4 rounded-3xl bg-white/5 border border-white/5 mb-4" in:fly={{ y: 20, duration: 800, delay: 200, easing: quintOut }}>
          <div class="w-20 h-20 rounded-2xl overflow-hidden bg-white/5 shrink-0">
             <img src="{mainImage}" alt="{product?.name}" class="w-full h-full object-cover" />
          </div>
          <div>
            <h4 class="font-black text-lg uppercase tracking-tight text-white/90">{product?.name}</h4>
            <div class="flex items-center gap-2 mt-1">
               <span class="text-blue-500 font-black text-xs">Quantity: {shopStore.quantity}</span>
               <span class="w-1 h-1 rounded-full bg-white/10"></span>
               <span class="text-white/30 text-[10px] font-bold uppercase tracking-widest">COD Delivery</span>
            </div>
          </div>
        </div>

        <!-- Solidified Inputs -->
        <div class="input-group group" in:fly={{ y: 20, duration: 800, delay: 300, easing: quintOut }}>
          <label class="block text-[10px] font-black text-white/30 uppercase tracking-[0.2em] mb-3 ml-2" for="phone">Số điện thoại <span class="text-red-500/50">*</span></label>
          <input
            type="tel"
            id="phone"
            bind:value={customer.phone}
            placeholder="09xx xxx xxx"
            class="w-full p-6 bg-white/5 border border-white/10 rounded-3xl outline-none focus:border-blue-500/40 text-2xl font-black text-white placeholder:text-white/5 transition-all"
          />
        </div>

        <div class="input-group group" in:fly={{ y: 20, duration: 800, delay: 400, easing: quintOut }}>
          <label class="block text-[10px] font-black text-white/30 uppercase tracking-[0.2em] mb-3 ml-2" for="address">Địa chỉ giao hàng <span class="text-red-500/50">*</span></label>
          <textarea
            id="address"
            bind:value={customer.address}
            rows="1"
            placeholder="Số nhà, tên đường, khu vực..."
            class="w-full p-6 bg-white/5 border border-white/10 rounded-3xl outline-none focus:border-blue-500/40 text-xl font-bold text-white placeholder:text-white/5 transition-all resize-none"
          ></textarea>
        </div>

        <!-- Conversion Badges -->
        <div class="flex items-center justify-between gap-4 px-2" in:fly={{ y: 20, duration: 800, delay: 500, easing: quintOut }}>
           <div class="flex items-center gap-2">
              <span class="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-xs">📦</span>
              <span class="text-[9px] font-black uppercase text-white/40 tracking-wider">Free Shipping</span>
           </div>
           <div class="flex items-center gap-2">
              <span class="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-xs">🛡️</span>
              <span class="text-[9px] font-black uppercase text-white/40 tracking-wider">Elite Privacy</span>
           </div>
           <div class="flex items-center gap-2">
              <span class="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-xs">🚚</span>
              <span class="text-[9px] font-black uppercase text-white/40 tracking-wider">COD Payment</span>
           </div>
        </div>

        <div class="summary pt-10 border-t border-white/5" in:fly={{ y: 20, duration: 800, delay: 600, easing: quintOut }}>
          <div class="flex justify-between items-center mb-10">
            <span class="text-white/20 font-black uppercase tracking-[0.4em] text-[10px]">Grand Total</span>
            <div class="text-right">
              <span class="block text-5xl font-black text-white">{shopStore.totalAmount.toLocaleString()}đ</span>
            </div>
          </div>

          <button
            onclick={handleCheckout}
            disabled={shopStore.isSubmitting}
            class="group relative w-full py-8 bg-blue-600 text-white rounded-[2.5rem] font-black text-3xl shadow-[0_40px_100px_-20px_rgba(37,99,235,0.4)] overflow-hidden active:scale-[0.98] transition-all flex items-center justify-center gap-4 transition-all hover:bg-blue-500"
          >
            {#if shopStore.isSubmitting}
               <span class="animate-pulse">PROCESSING...</span>
            {:else}
              <span class="relative z-10">CHỐT ĐƠN NGAY</span>
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
</style>


