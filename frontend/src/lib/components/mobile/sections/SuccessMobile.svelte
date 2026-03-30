<script lang="ts">
  import { fade, fly, scale } from 'svelte/transition';
  import { ShieldCheck, Copy, ShoppingCart, MessageSquare, CheckCircle2, Package, Truck, Award, Sparkles, Phone } from 'lucide-svelte';
  import { formatCurrency, formatDate } from '$lib/utils/format.ts';
  import { goto } from '$app/navigation';
  import { SHOP_CONFIG } from '$lib/constants/shop.ts';
  import { onMount } from 'svelte';
  import { nanobot } from '$lib/state/nanobot.svelte';

  import { page } from '$app/state';

  let { order, orderId, isLookup } = $props<{ order: any, orderId: string, isLookup: boolean }>();

  const STATUS_STEPS = [
    { key: 'PENDING', label: 'Chờ duyệt', icon: CheckCircle2 },
    { key: 'PAID', label: 'Đã thanh toán', icon: Award },
    { key: 'PROCESSING', label: 'Đang xử lý', icon: Package },
    { key: 'SHIPPED', label: 'Đang giao', icon: Truck },
    { key: 'COMPLETED', label: 'Thành công', icon: ShieldCheck }
  ];

  function getStepIndex(status: string) {
    const idx = STATUS_STEPS.findIndex(s => s.key === status);
    return idx === -1 ? 0 : idx;
  }

  const currentStepIdx = $derived(getStepIndex(order?.status || 'PENDING'));

  onMount(() => {
    const originalHideFooter = nanobot.ui.hideFooter;
    nanobot.ui.hideFooter = true;
    return () => {
      nanobot.ui.hideFooter = originalHideFooter;
    };
  });

  let copied = $state(false);
  function copyOrderId() {
    if (typeof navigator !== 'undefined') {
        const shortId = orderId.slice(-6).toUpperCase();
        navigator.clipboard.writeText(shortId);
        copied = true;
        setTimeout(() => copied = false, 2000);
    }
  }

  const items = $derived(order?.items || []);
  const customerName = $derived(order?.customerName || order?.customer_name || 'Khách hàng');
  const customerAddress = $derived(order?.customerAddress || order?.customer_address || 'Địa chỉ bảo mật');
</script>

<div class="fixed inset-0 bg-[#0a0a0a] text-white overflow-y-auto custom-scrollbar flex flex-col">
  <!-- Celebration Glow -->
  <div class="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[300px] {isLookup ? 'bg-sky-500/10' : 'bg-emerald-500/10'} blur-[100px] pointer-events-none"></div>

  <div class="relative px-6 pt-16 flex flex-col items-center text-center">
    <!-- Animated Icon -->
    <div in:scale={{ duration: 600, delay: 200, start: 0.5 }} class="w-24 h-24 {isLookup ? 'bg-sky-500/20 text-sky-400 border-sky-500/30' : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'} rounded-full flex items-center justify-center mb-8 border relative">
      <div class="absolute inset-0 {isLookup ? 'bg-sky-400/20' : 'bg-emerald-400/20'} rounded-full blur-2xl {isLookup ? '' : 'animate-pulse'}"></div>
      {#if isLookup}
        <ShieldCheck class="w-12 h-12 relative z-10" strokeWidth={2.5} />
      {:else}
        <CheckCircle2 class="w-12 h-12 relative z-10" strokeWidth={2.5} />
      {/if}
    </div>

    <h1 in:fly={{ y: 20, duration: 600, delay: 400 }} class="text-3xl font-black italic tracking-widest uppercase mb-2">
      {isLookup ? 'CHI TIẾT ĐƠN HÀNG' : 'ĐẶT HÀNG THÀNH CÔNG!'}
    </h1>
    <p in:fade={{ delay: 600 }} class="text-white/40 text-[10px] uppercase tracking-[0.3em] font-bold italic mb-10">
      {isLookup ? 'Thông tin trạng thái xử lý đơn hàng' : 'Cảm ơn Quý khách đã tin tưởng lựa chọn'}
    </p>

    <!-- Status Timeline -->
    <div in:fly={{ y: 20, duration: 800, delay: 500 }} class="w-full mb-8 px-4">
      <div class="flex justify-between items-center relative">
        <!-- Connecting Line -->
        <div class="absolute top-1/2 left-0 w-full h-[2px] bg-white/5 -translate-y-1/2"></div>
        <div 
          class="absolute top-1/2 left-0 h-[2px] bg-emerald-500 transition-all duration-1000 -translate-y-1/2" 
          style="width: {(currentStepIdx / (STATUS_STEPS.length - 1)) * 100}%"
        ></div>

        {#each STATUS_STEPS as step, i}
          <div class="relative z-10 flex flex-col items-center">
            <div 
              class="w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all duration-500 
              {i <= currentStepIdx ? 'bg-emerald-500 border-emerald-500 text-white scale-110 shadow-[0_0_15px_rgba(16,185,129,0.3)]' : 'bg-[#0a0a0a] border-white/10 text-white/20'}"
            >
              <step.icon class="w-4 h-4" />
            </div>
            <span class="text-[8px] font-black uppercase mt-2 tracking-tighter {i <= currentStepIdx ? 'text-emerald-400' : 'text-white/20'}">
              {step.label}
            </span>
          </div>
        {/each}
      </div>
    </div>

    <!-- Main Order Card -->
    <div in:fly={{ y: 30, duration: 800, delay: 600 }} class="w-full bg-white/[0.03] border border-white/10 backdrop-blur-xl rounded-[2.5rem] p-6 mb-6 text-left">
      <div class="flex justify-between items-start mb-6 border-b border-white/5 pb-4">
        <div>
           <span class="text-[9px] font-black text-white/30 uppercase tracking-widest block mb-1">Mã đơn hàng</span>
           <div class="flex items-center gap-2 group active:opacity-60 transition-opacity" onclick={copyOrderId} role="button" tabindex="0">
             <span class="text-sm font-black text-white tracking-widest uppercase italic">{copied ? 'ĐÃ COPPY!' : `#${orderId.slice(-6).toUpperCase()}`}</span>
             <Copy class="w-3 h-3 {copied ? 'text-emerald-400' : 'text-white/20'}" />
           </div>
        </div>
        <div class="text-right">
           <span class="text-[9px] font-black text-white/30 uppercase tracking-widest block mb-1">Tổng tiền</span>
           <span class="text-xl font-black text-emerald-400 italic">{(order?.total || 0).toLocaleString()}đ</span>
        </div>
      </div>

      <div class="space-y-4">
        <div class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center shrink-0">
             <Package class="w-4 h-4 text-white/40" />
          </div>
          <div>
            <span class="text-[9px] font-black text-white/30 uppercase tracking-widest block mb-1">Sản phẩm chi tiết</span>
            <p class="text-[11px] font-bold text-white/80 leading-snug">
              {items.map((i: any) => `${i.quantity}x ${i.name}`).join(', ') || 'Đang cập nhật...'}
            </p>
          </div>
        </div>

        <div class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center shrink-0">
             <Truck class="w-4 h-4 text-white/40" />
          </div>
          <div>
            <span class="text-[9px] font-black text-white/30 uppercase tracking-widest block mb-1">Giao đến</span>
            <p class="text-[11px] font-bold text-white/80 leading-tight uppercase italic">{customerName}</p>
            <p class="text-[10px] text-white/40 leading-snug uppercase mt-0.5">{customerAddress}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- What's Next Card (Elite V2.2 Refined) -->
    <div in:fly={{ y: 30, duration: 800, delay: 800 }} class="w-full bg-white/[0.02] border border-white/5 rounded-[2.5rem] p-8 text-center relative overflow-hidden group">
       <div class="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-transparent to-purple-500/10 opacity-50"></div>
       <div class="relative z-10">
         <span class="text-[10px] font-black text-blue-400 uppercase tracking-[0.4em] block mb-4 italic flex items-center justify-center gap-2">
           <Sparkles class="w-3 h-3" /> TIẾP THEO LÀ GÌ?
         </span>
         <p class="text-[12px] font-medium text-white/70 leading-relaxed max-w-[260px] mx-auto mb-6">
           Hệ thống đang xử lý đơn hàng. Chuyên gia sẽ gọi điện xác nhận cho Quý khách trong vòng **15 phút** tới!
         </p>
         <div class="flex items-center justify-center gap-3 py-3 px-4 bg-white/5 rounded-2xl border border-white/5 mx-auto w-fit">
            <div class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>
            <span class="text-[9px] font-black text-white/40 uppercase tracking-widest">Đội ngũ Elite đã sẵn sàng</span>
         </div>
       </div>
    </div>

    <!-- Spacer to ensure content clears the fixed Action Stack thưa sếp! -->
    <div class="h-80 shrink-0 pointer-events-none"></div>
  </div>

  <!-- Action Stack (Elite 1-Row Compact thưa sếp!) -->
  <div class="fixed bottom-0 left-0 w-full p-6 bg-gradient-to-t from-[#0a0a0a] via-[#0a0a0a]/95 to-transparent flex flex-row gap-3 items-center">
    <a 
      href="tel:{SHOP_CONFIG.pharmacy.phone.replace(/\s+/g, '')}"
      class="flex-[1.5] py-4 text-white font-black text-[12px] uppercase tracking-wider rounded-full shadow-[0_10px_30px_rgba(254,44,85,0.2)] active:scale-95 transition-all overflow-hidden relative group text-center"
      style="background: linear-gradient(90deg, #fe2c55 0%, #ff4b6b 100%) !important;"
    >
        <span class="relative z-10 flex items-center justify-center gap-1.5">GỌI TƯ VẤN <Phone class="w-3.5 h-3.5" /></span>
        <div class="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
    </a>
    
    <a 
      href="https://zalo.me/{SHOP_CONFIG.pharmacy.phone.replace(/\s+/g, '')}"
      target="_blank"
      class="flex-1 py-4 bg-white/5 border border-white/10 text-white/70 font-black text-[10px] uppercase tracking-widest rounded-full active:bg-white/10 transition-all flex items-center justify-center gap-1.5 text-center"
    >
       <svg class="w-4 h-4 fill-current" viewBox="0 0 24 24">
         <path d="M12.003 2c-5.523 0-10 4.03-10 9 0 2.877 1.517 5.414 3.864 7.073l-.49 2.508c-.06.31.28.528.535.357l3.074-2.049A11.02 11.02 0 0 0 12.003 20c5.522 0 10-4.03 10-9s-4.478-9-10-9zM15.534 15.11H8.468v-1.12l2.67-3.328H8.468V9.167h6.732v1.12l-2.67 3.328h2.67v1.495z"/>
       </svg>
       CHAT ZALO
    </a>
  </div>
</div>

<style lang="postcss">
  :global(body) {
    background-color: #0a0a0a;
  }
</style>
