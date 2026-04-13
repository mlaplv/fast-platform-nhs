<script lang="ts">
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { goto } from '$app/navigation';
  import { formatCurrency } from '$lib/utils/format';
  import { onMount } from 'svelte';
  import { apiClient } from '$lib/utils/apiClient';

  const cartStore = getCartStore();
  const clientUi = getClientUi();

  let form = $state({
    name: '',
    phone: '',
    address: ''
  });

  let isSubmitting = $state(false);
  let errorMsg = $state('');

  // Quản lý trạng thái trống của giỏ hàng
  const isEmpty = $derived(cartStore.selectedItemsCount === 0);

  onMount(() => {
    if (isEmpty) goto('/');
  });

  async function handleSubmit(e: Event) {
    e.preventDefault();
    if (!form.name || !form.phone || !form.address) {
      errorMsg = 'Vui lòng điền đầy đủ thông tin nhận hàng.';
      return;
    }

    if (cartStore.items.length === 0) return;

    isSubmitting = true;
    errorMsg = '';

    try {
      // Gọi API thực tế để tạo đơn hàng đa sản phẩm
      const res = await apiClient.post('/api/v1/client/checkout/stealth', {
        customer_name: form.name,
        customer_phone: form.phone,
        customer_address: form.address,
        items: cartStore.items.filter(i => i.selected).map(item => ({
          product_id: item.product.id,
          variant_id: item.variant?.id,
          quantity: item.quantity,
          price: item.variant?.discountPrice ?? item.variant?.price ?? item.product.discountPrice ?? item.product.price ?? 0
        })),
        total_amount: cartStore.totalAmount,
        voucher_id: cartStore.selectedVoucherId
      });

      if (res && (res.ok || res.status === 'success' || res.id)) {
        const orderId = res.id || 'ORD-' + Math.floor(Math.random() * 1000000);
        cartStore.clearCart();
        clientUi.showToast('Đặt hàng thành công!', 'success');
        goto(`/checkout/success/${orderId}?phone=${encodeURIComponent(form.phone)}`);
      } else {
        const msg = res?.message || 'Có lỗi xảy ra khi xử lý đơn hàng.';
        errorMsg = msg;
        clientUi.showToast(msg, 'error');
      }
    } catch (err: unknown) {
      console.error("[CHECKOUT ERROR] Dạ vâng thưa Sếp, lỗi gọi API:", err);
      const msg = err instanceof Error ? err.message : 'Có lỗi xảy ra khi xử lý đơn hàng.';
      errorMsg = msg;
      clientUi.showToast(msg, 'error');
    } finally {
      isSubmitting = false;
    }
  }
</script>

<svelte:head>
  <title>Thanh toán An toàn | Micsmo Elite</title>
</svelte:head>

<div class="min-h-screen bg-[#010101] text-white pt-24 pb-16 px-6 md:px-8">
  <div class="max-w-6xl mx-auto">
    {#if isEmpty}
      <div class="flex flex-col items-center justify-center py-20 text-center space-y-8" in:fade>
        <div class="w-32 h-32 bg-white/5 rounded-full flex items-center justify-center border border-white/10">
          <svg class="w-16 h-16 text-slate-700" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
        </div>
        <div class="space-y-3">
          <h2 class="text-3xl font-black uppercase tracking-tighter italic">Giỏ hàng đã được dọn sạch</h2>
          <p class="text-slate-400 text-sm max-w-sm mx-auto">Có vẻ như bạn đã xóa hết mọi thứ. Hãy quay lại khám phá thêm các sản phẩm tuyệt vời của Micsmo nhé.</p>
        </div>
        <a href="/" class="px-10 py-4 bg-white text-black font-black rounded-2xl uppercase tracking-widest text-xs hover:bg-red-500 hover:text-white transition-all shadow-xl shadow-white/5 active:scale-95">
          Tiếp tục mua sắm
        </a>
      </div>
    {:else}
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16" in:fade>
        <!-- LEFT: CHECKOUT FORM (as before) -->
        <div class="lg:col-span-7 space-y-10">
          <!-- ... (chế độ ẩn code cũ để tiết kiệm token) ... -->
          <div class="space-y-4">
            <span class="bg-red-600 text-white px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest shadow-lg shadow-red-600/20">
              Stealth Checkout
            </span>
            <h1 class="text-4xl md:text-5xl font-black uppercase tracking-tighter italic drop-shadow-lg">Thông tin nhận hàng</h1>
            <p class="text-slate-400 text-sm font-medium">Hoàn tất đặt hàng cực nhanh, không cần tạo tài khoản.</p>
          </div>

          {#if errorMsg}
            <div class="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm font-bold flex items-center gap-3">
              <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
              {errorMsg}
            </div>
          {/if}

          <form onsubmit={handleSubmit} class="space-y-6">
            <div class="space-y-2">
              <label for="name" class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-4">Họ và tên người nhận</label>
              <input
                id="name"
                type="text"
                bind:value={form.name}
                placeholder="Ví dụ: Nguyễn Văn A"
                class="w-full px-6 py-4 bg-white/5 border border-white/10 focus:border-red-500/50 rounded-2xl outline-none text-white font-bold transition-all focus:bg-white/10"
                required
              />
            </div>

            <div class="space-y-2">
              <label for="phone" class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-4">Số điện thoại liên hệ</label>
              <input
                id="phone"
                type="tel"
                bind:value={form.phone}
                placeholder="Ví dụ: 0987654321"
                class="w-full px-6 py-4 bg-white/5 border border-white/10 focus:border-red-500/50 rounded-2xl outline-none text-white font-bold transition-all focus:bg-white/10"
                required
              />
            </div>

            <div class="space-y-2">
              <label for="address" class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-4">Địa chỉ giao hàng chi tiết</label>
              <textarea
                id="address"
                bind:value={form.address}
                placeholder="Số nhà, Tên đường, Phường/Xã, Quận/Huyện, Tỉnh/Thành phố..."
                rows="3"
                class="w-full px-6 py-4 bg-white/5 border border-white/10 focus:border-red-500/50 rounded-2xl outline-none text-white font-bold transition-all focus:bg-white/10 resize-none"
                required
              ></textarea>
            </div>

            <div class="flex items-center gap-3 p-4 rounded-2xl bg-emerald-500/5 border border-emerald-500/10 text-emerald-400/80 text-xs font-bold">
              <svg class="w-5 h-5 shrink-0 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
              Mọi thông tin của bạn đều được mã hóa nội bộ và bảo mật tuyệt đối.
            </div>

            <button
              type="submit"
              disabled={isSubmitting || cartStore.items.length === 0}
              class="w-full mt-8 py-5 bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 text-white font-black rounded-2xl transition-all active:scale-[0.98] shadow-[0_15px_30px_rgba(220,38,38,0.2)] uppercase tracking-widest italic flex items-center justify-center gap-3 disabled:opacity-50"
            >
              {#if isSubmitting}
                <div class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                <span>Đang xử lý đơn hàng...</span>
              {:else}
                <span>Xác nhận Đặt hàng</span>
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
              {/if}
            </button>
          </form>
        </div>

        <!-- RIGHT: ORDER SUMMARY (Interactive) -->
        <div class="lg:col-span-5">
          <div class="bg-white/[0.02] border border-white/10 p-6 md:p-8 rounded-[2.5rem] sticky top-28 shadow-2xl backdrop-blur-xl">
            <h2 class="text-lg font-black uppercase tracking-widest text-white mb-8 flex items-center justify-between">
              <span>Sản phẩm ({cartStore.selectedItemsCount})</span>
            </h2>

            <!-- Items Scroll Area -->
            <div class="max-h-[50vh] overflow-y-auto space-y-4 mb-8 pr-2 custom-scrollbar">
              {#each cartStore.items.filter(i => i.selected) as item (item.id)}
                <div class="flex gap-4 items-center group bg-white/[0.03] p-3 rounded-2xl border border-white/5 hover:border-white/10 transition-all">
                  <div class="w-20 h-20 bg-black/50 rounded-xl overflow-hidden shrink-0 border border-white/5 relative">
                    <img src={item.product.image || item.product.images?.[0] || '/uploads/img/micsmo/sp1.png'} alt={item.product.name} class="w-full h-full object-cover group-hover:scale-110 transition-transform" />
                  </div>

                  <div class="flex-1 min-w-0 flex flex-col justify-between self-stretch py-1">
                    <div>
                      <h4 class="text-xs font-bold text-white leading-snug line-clamp-1">{item.product.name}</h4>
                      {#if item.variant}
                        <p class="text-[9px] text-slate-500 font-black uppercase tracking-widest mt-1">{item.variant.sku}</p>
                      {/if}
                    </div>

                    <div class="flex items-center justify-between mt-auto">
                      <div class="flex items-center gap-2 bg-black/40 rounded-lg p-1 border border-white/5 scale-90 origin-left">
                        <button onclick={() => cartStore.updateQuantity(item.id, item.quantity - 1)} class="w-6 h-6 rounded flex items-center justify-center text-slate-400 hover:text-white transition-colors font-black">-</button>
                        <span class="text-xs font-black w-6 text-center text-white">{item.quantity}</span>
                        <button onclick={() => cartStore.updateQuantity(item.id, item.quantity + 1)} class="w-6 h-6 rounded flex items-center justify-center text-slate-400 hover:text-white transition-colors font-black">+</button>
                      </div>
                      <span class="text-sm font-black text-red-500">{formatCurrency((item.variant?.discountPrice ?? item.variant?.price ?? item.product.discountPrice ?? item.product.price ?? 0) * item.quantity)}</span>
                    </div>
                  </div>

                  <button onclick={() => cartStore.removeItem(item.id)} class="w-8 h-8 rounded-full bg-red-600/10 flex items-center justify-center text-red-500 hover:bg-red-600 hover:text-white transition-all opacity-0 group-hover:opacity-100">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </button>
                </div>
              {/each}
            </div>

            <!-- Totals -->
            <div class="space-y-4 border-t border-white/10 pt-6">
              <div class="flex justify-between items-center text-slate-400 text-sm font-medium">
                <span>Tạm tính</span>
                <span class="text-white">{formatCurrency(cartStore.totalAmount)}</span>
              </div>
              <div class="flex justify-between items-center text-slate-400 text-sm font-medium">
                <span>Phí vận chuyển</span>
                <span class="text-emerald-400 font-bold uppercase tracking-widest text-[10px]">Miễn phí</span>
              </div>
              <div class="pt-6 border-t border-white/10 flex justify-between items-end mt-4">
                <span class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Tổng thanh toán</span>
                <span class="text-4xl font-black text-red-500 italic tracking-tighter drop-shadow-[0_0_15px_rgba(239,68,68,0.4)]">
                  {formatCurrency(cartStore.totalAmount)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
  }
</style>