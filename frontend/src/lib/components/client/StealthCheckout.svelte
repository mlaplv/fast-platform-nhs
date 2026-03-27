<script lang="ts">
  import { shopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { portal } from '$lib/actions/portal.ts';
  import { Z_INDEX } from '$lib/core/constants/zIndex.ts';
  import { fade, fly } from 'svelte/transition';

  let customer = $state({
    phone: '',
    address: ''
  });

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
    transition:fade={{ duration: 300 }}
    class="fixed inset-0 bg-slate-950/80 backdrop-blur-xl transition-opacity duration-300"
    style="z-index: ${Z_INDEX.OVERLAY};"
    onclick={() => shopStore.closeCheckout()}
    role="button"
    tabindex="-1"
  ></div>

  <div
    use:portal
    transition:fly={{ y: 100, duration: 500, opacity: 1 }}
    class="fixed bottom-0 left-0 right-0 max-w-lg mx-auto glass-dark text-white rounded-t-[3rem] p-10 transition-all"
    style="z-index: var(--z-index); {zIndexStyle}"
  >
    <!-- Premium Handle -->
    <div class="w-16 h-1 bg-white/10 rounded-full mx-auto mb-10"></div>

    <div class="header flex justify-between items-start mb-10">
      <div>
        <h2 class="text-4xl font-black text-white tracking-tighter leading-none mb-2">XÁC NHẬN</h2>
        <p class="text-blue-400 text-sm font-bold uppercase tracking-widest">Elite Order Fulfillment</p>
      </div>
      <button onclick={() => shopStore.closeCheckout()} class="p-3 bg-white/5 text-white/40 hover:text-white rounded-full transition-all hover:bg-white/10">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    {#if shopStore.orderSuccess}
      <div class="success-message text-center py-16" in:fade={{ duration: 500 }}>
        <div class="inline-flex items-center justify-center w-24 h-24 bg-blue-600 rounded-[2.5rem] mb-8 shadow-[0_0_50px_rgba(37,99,235,0.4)] animate-float">
          <svg class="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 class="text-4xl font-black text-white mb-4 tracking-tighter">SUCCESS!</h3>
        <p class="text-white/60 leading-relaxed font-medium">Đơn hàng đã được chuyển tới trung tâm xử lý ưu tiên. Chúng tôi sẽ liên hệ trong tích tắc.</p>
      </div>
    {:else}
      <div class="form-container space-y-8">
        <div class="input-group">
          <label class="block text-xs font-black text-blue-400 uppercase tracking-[0.2em] mb-3" for="phone">Hỗ trợ nhận dạng (SĐT) <span class="text-red-500">*</span></label>
          <input
            type="tel"
            id="phone"
            bind:value={customer.phone}
            placeholder="09xx xxx xxx"
            class="w-full p-5 bg-white/5 border border-white/10 rounded-2xl focus:ring-2 focus:ring-blue-600 focus:bg-white/10 outline-none transition-all text-xl font-bold placeholder:text-white/20"
          />
        </div>

        <div class="input-group">
          <label class="block text-xs font-black text-blue-400 uppercase tracking-[0.2em] mb-3" for="address">Tọa độ giao hàng <span class="text-red-500">*</span></label>
          <textarea
            id="address"
            bind:value={customer.address}
            rows="2"
            placeholder="Số nhà, khu vực..."
            class="w-full p-5 bg-white/5 border border-white/10 rounded-2xl focus:ring-2 focus:ring-blue-600 focus:bg-white/10 outline-none transition-all text-xl font-bold placeholder:text-white/20"
          ></textarea>
        </div>

        <!-- Order Bump (Elite Design) -->
        <div
          class="order-bump p-6 bg-gradient-to-r from-blue-600/20 to-transparent border border-blue-500/30 rounded-3xl flex items-center gap-5 cursor-pointer hover:from-blue-600/30 transition-all group relative overflow-hidden"
          onclick={() => shopStore.toggleOrderBump()}
          role="button"
          tabindex="0"
        >
          <div class="relative w-8 h-8 shrink-0">
            <input
              type="checkbox"
              checked={shopStore.hasOrderBump}
              class="peer absolute inset-0 opacity-0 cursor-pointer"
              readonly
            />
            <div class="w-8 h-8 border-2 border-white/20 rounded-xl bg-white/5 peer-checked:bg-blue-600 peer-checked:border-blue-600 transition-all flex items-center justify-center shadow-lg">
              <svg class="w-5 h-5 text-white opacity-0 peer-checked:opacity-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
          <div class="content flex-1">
            <div class="flex items-center gap-3 mb-1">
              <span class="font-black text-white uppercase tracking-tighter">Gói Quà Tặng (Add-on)</span>
              <span class="bg-blue-600 text-[10px] font-black px-2 py-0.5 rounded-full">+99K</span>
            </div>
            <p class="text-xs text-white/40 font-medium">Bổ sung Nano Silver Spray cho giày - Tự tin 360 độ.</p>
          </div>
          <div class="absolute inset-0 animate-shimmer opacity-30"></div>
        </div>

        <div class="summary pt-10 border-t border-white/5">
          <div class="flex justify-between items-end mb-10">
            <span class="text-white/40 font-bold uppercase tracking-widest text-xs">Total Investment:</span>
            <div class="text-right">
              <span class="block text-5xl font-black text-white tracking-tighter drop-shadow-[0_0_20px_rgba(255,255,255,0.3)]">{shopStore.totalAmount.toLocaleString()}đ</span>
              <span class="text-[10px] text-blue-400 font-bold uppercase tracking-[0.3em]">Neural Delivery Active</span>
            </div>
          </div>

          <button
            onclick={handleCheckout}
            disabled={shopStore.isSubmitting}
            class="group relative w-full py-6 bg-blue-600 text-white rounded-3xl font-black text-2xl shadow-[0_20px_40px_-10px_rgba(37,99,235,0.5)] overflow-hidden active:scale-95 transition-all flex items-center justify-center gap-4"
          >
            {#if shopStore.isSubmitting}
              <svg class="animate-spin h-8 w-8 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              SYSTEM BUSY...
            {:else}
              <span class="relative z-10">CONFIRM ORDER</span>
              <svg class="w-8 h-8 relative z-10 group-hover:translate-x-2 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
              <div class="absolute inset-0 animate-shimmer"></div>
            {/if}
          </button>
        </div>
      </div>
    {/if}
  </div>
{/if}

<style>
  /* No extra colors needed, using Elite V2.2 globals */
</style>


