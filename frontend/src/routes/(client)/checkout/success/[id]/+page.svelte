<script lang="ts">
  import { page } from '$app/state';
  import { fade, fly, scale } from 'svelte/transition';
  import { Z_INDEX } from '$lib/core/constants/zIndex.ts';
  import { onMount } from 'svelte';
  import { apiClient } from '$lib/utils/apiClient';

  const orderId = page.params.id;
  let order = $state<any>(null);
  let isLoading = $state(true);

  onMount(async () => {
    try {
      // Fetch order details for the professional success page thưa sếp!
      const res = await apiClient.get<any>(`/api/v1/client/orders/${orderId}`);
      if (res) order = res;
    } catch (e) {
      console.error("Failed to load order thưa sếp", e);
    } finally {
      isLoading = false;
    }
  });
</script>

<svelte:head>
  <title>Đặt hàng thành công | Nhà Thuốc Hồng Sơn</title>
</svelte:head>

<div class="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center p-6 relative overflow-hidden">
  <!-- Elite Glass Background thưa sếp! -->
  <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-sky-500/10 rounded-full blur-[120px] pointer-events-none"></div>
  
  {#if isLoading}
    <div class="flex flex-col items-center gap-4">
      <div class="w-12 h-12 border-4 border-sky-500/20 border-t-sky-500 rounded-full animate-spin"></div>
      <p class="text-slate-500 font-bold uppercase tracking-widest text-[10px]">Đang tải dữ liệu đơn hàng...</p>
    </div>
  {:else}
    <div 
      in:fly={{ y: 30, duration: 800 }}
      class="w-full max-w-2xl bg-white/5 border border-white/10 backdrop-blur-2xl rounded-[3rem] p-8 md:p-12 shadow-2xl relative z-10"
    >
      <!-- Success Icon thưa sếp! -->
      <div class="w-24 h-24 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-8 border border-emerald-500/30 animate-in zoom-in duration-500 shadow-[0_0_40px_rgba(16,185,129,0.2)]">
        <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
      </div>

      <div class="text-center mb-12">
        <h1 class="text-4xl md:text-5xl font-black tracking-tight mb-4 uppercase">ĐẶT HÀNG THÀNH CÔNG!</h1>
        <p class="text-slate-400 text-lg max-w-md mx-auto leading-relaxed">
          Đơn hàng <span class="text-white font-bold">#{orderId.slice(-6).toUpperCase()}</span> đã được ghi nhận. 
          Hệ thống đã tự động tạo tài khoản cho Quý khách bằng số điện thoại <span class="text-sky-400 font-bold">{order?.customer_phone || ''}</span> để tiện theo dõi đơn hàng.
        </p>
      </div>

      <!-- Order Details Summary thưa sếp! -->
      <div class="grid md:grid-cols-2 gap-6 p-6 bg-white/5 border border-white/10 rounded-[2rem] mb-12">
        <div class="space-y-4">
          <div class="flex flex-col">
            <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest">Người nhận:</span>
            <span class="text-lg font-bold">{order?.customer_name || 'Khách hàng'}</span>
          </div>
          <div class="flex flex-col">
            <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest">Địa chỉ:</span>
            <span class="text-sm text-slate-300 leading-snug">{order?.customer_address || 'Địa chỉ bảo mật'}</span>
          </div>
        </div>
        <div class="space-y-4 border-t md:border-t-0 md:border-l border-white/10 pt-4 md:pt-0 md:pl-6 text-right">
          <div class="flex flex-col">
            <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest">Tổng thanh toán:</span>
            <span class="text-3xl font-black text-sky-400 tabular-nums">{order?.total_amount?.toLocaleString() || '---'}đ</span>
          </div>
          <div class="flex flex-col">
            <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest">Trạng thái:</span>
            <span class="text-xs font-bold text-amber-500 uppercase">Đang chờ xác nhận ⏱</span>
          </div>
        </div>
      </div>

      <!-- Welcome Message for New Users thưa sếp! -->
      <div class="p-6 bg-sky-500/10 border border-sky-500/20 rounded-[2rem] text-center mb-12">
        <h3 class="text-sky-400 font-black text-sm uppercase tracking-widest mb-2">🎁 ƯU ĐÃI THÀNH VIÊN MỚI</h3>
        <p class="text-slate-400 text-xs leading-relaxed">
          Quý khách có thể đăng nhập bằng Số điện thoại để theo dõi đơn hàng và nhận quà tặng cho lần mua sau. 
          Hệ thống sẽ gửi mã xác thực qua điện thoại khi Quý khách đăng nhập lần đầu.
        </p>
      </div>

      <div class="flex flex-col md:flex-row gap-4">
        <a 
          href="/"
          class="flex-1 py-4 bg-white text-black font-black text-center rounded-full hover:bg-slate-200 transition-all active:scale-95 uppercase tracking-tight"
        >
          Tiếp tục mua sắm
        </a>
        <a 
          href="/account/orders"
          class="flex-1 py-4 bg-white/5 border border-white/10 text-white font-black text-center rounded-full hover:bg-white/10 transition-all active:scale-95 uppercase tracking-tight"
        >
          Theo dõi đơn hàng
        </a>
      </div>
    </div>
  {/if}

  <p class="mt-12 text-[10px] text-slate-700 font-black uppercase tracking-[0.3em]">Nhà Thuốc Hồng Sơn - Tận Tâm 2026</p>
</div>
