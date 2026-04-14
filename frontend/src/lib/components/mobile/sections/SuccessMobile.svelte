<script lang="ts">
  import { fade, fly, scale } from 'svelte/transition';
  import { FileText, ShieldCheck, Copy, ShoppingCart, MessageSquare, CheckCircle2, Package, Truck, Award, Sparkles, Phone, Gift, Home } from 'lucide-svelte';
  import { formatCurrency, formatDate } from '$lib/utils/format.ts';
  import { goto } from '$app/navigation';
  import { SHOP_CONFIG } from '$lib/constants/shop';

  import { page } from '$app/state';

  import type { OrderDetail } from '$lib/types';
  let { order, orderId, isLookup } = $props<{ order: OrderDetail, orderId: string, isLookup: boolean }>();

  const STATUS_STEPS = [
    { key: 'PENDING', label: 'Tiếp nhận', icon: FileText },
    { key: 'PACKED', label: 'Bảo mật', icon: ShieldCheck },
    { key: 'SHIPPING', label: 'Vận chuyển', icon: Truck },
    { key: 'DELIVERED', label: 'Thành công', icon: Gift }
  ];

  function getStepIndex(status: string) {
    const idx = STATUS_STEPS.findIndex(s => s.key === status);
    return idx === -1 ? 0 : idx;
  }

  const currentStepIdx = $derived(getStepIndex(order?.status || 'PENDING'));


  let copied = $state(false);
  let copyTimer: ReturnType<typeof setTimeout> | undefined;

  $effect(() => {
    return () => {
      if (copyTimer) clearTimeout(copyTimer);
    };
  });

  function copyOrderId() {
    if (typeof navigator !== 'undefined') {
        const shortId = orderId.slice(-6).toUpperCase();
        navigator.clipboard.writeText(shortId);
        copied = true;
        if (copyTimer) clearTimeout(copyTimer);
        copyTimer = setTimeout(() => copied = false, 2000);
    }
  }

  const items = $derived(order?.items || []);
  const customerName = $derived(order?.customerName || order?.name_masked || 'Khách hàng');
  const customerAddress = $derived(order?.customerAddress || order?.address_masked || 'Địa chỉ bảo mật');
</script>

<div class="fixed inset-0 bg-[#fafafa] text-slate-900 overflow-y-auto custom-scrollbar flex flex-col">
  <!-- Top Navigation -->
  <button
    onclick={() => goto('/')}
    class="fixed top-4 right-6 w-10 h-10 rounded-full bg-white border border-slate-200 flex items-center justify-center shadow-lg active:scale-95 transition-all text-slate-400 z-toast"
    aria-label="Home"
  >
    <Home class="w-4 h-4" />
  </button>

  <!-- Celebration Glow (Subtle for Light Mode) -->
  <div class="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[300px] {isLookup ? 'bg-sky-500/5' : 'bg-emerald-500/5'} blur-[80px] pointer-events-none"></div>

  <div class="relative px-6 pt-12 flex flex-col items-center text-center">
    <!-- Status Badge (White Mode) -->
    <div in:scale={{ duration: 600, delay: 200, start: 0.9 }} 
         class="px-5 py-1.5 rounded-full border border-slate-200 bg-white shadow-sm mb-8 flex items-center gap-2 relative">
      {#if isLookup}
        <ShieldCheck class="w-3.5 h-3.5 text-sky-500" strokeWidth={2.5} />
        <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest">STATUS: TRACKING</span>
      {:else}
        <CheckCircle2 class="w-3.5 h-3.5 text-emerald-500" strokeWidth={2.5} />
        <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest">STATUS: SUCCESS</span>
      {/if}
    </div>

    <h1 in:fly={{ y: 20, duration: 600, delay: 400 }} 
        class="text-2xl font-black italic tracking-tighter uppercase mb-2 text-slate-900">
      {isLookup ? 'CHI TIẾT ĐƠN HÀNG' : 'ĐẶT HÀNG THÀNH CÔNG'}
    </h1>
    
    <p in:fade={{ delay: 600 }} class="text-slate-400 text-[10px] uppercase tracking-[0.3em] font-black mb-12 italic">
      {isLookup ? 'CẬP NHẬT TRẠNG THÁI MỚI NHẤT' : 'CẢM ƠN QUÝ KHÁCH ĐÃ TIN TƯỞNG'}
    </p>

    <!-- Status Timeline (White Mode) -->
    <div in:fly={{ y: 20, duration: 800, delay: 500 }} class="w-full mb-10 px-2">
      <div class="stepper-row">
        {#each STATUS_STEPS as step, i}
          <div class="stepper-node">
            {#if i === currentStepIdx}
              <div class="node-halo absolute -inset-2 bg-sky-500/5 rounded-full blur-xl animate-pulse"></div>
            {/if}
            <div class="node-circle {
              i < currentStepIdx  ? 'bg-emerald-50 border-emerald-500 text-emerald-600' :
              i === currentStepIdx? 'bg-sky-50 border-sky-500 text-sky-600 scale-110 shadow-lg shadow-sky-100' :
              'bg-slate-50 border-slate-100 text-slate-300'}">
              <step.icon class="w-4 h-4" />
            </div>
            <span class="node-label {i <= currentStepIdx ? 'text-slate-900' : 'text-slate-300'}">
              {step.label}
            </span>
          </div>

          {#if i < STATUS_STEPS.length - 1}
            <div class="connector">
              <div class="connector-track bg-slate-100"></div>
              {#if i < currentStepIdx}
                <div class="connector-fill bg-emerald-500 shadow-sm"></div>
              {:else if i === currentStepIdx}
                <div class="connector-fill w-1/2 bg-sky-400"></div>
              {/if}
            </div>
          {/if}
        {/each}
      </div>
    </div>


    <!-- Main Order Card (Checkout Style) -->
    <div in:fly={{ y: 30, duration: 800, delay: 600 }} class="w-full bg-white shadow-sm border-t-4 border-[#ee4d2d] p-7 mb-6 text-left relative overflow-hidden">
      <div class="flex justify-between items-start mb-8 border-b border-slate-50 pb-5">
        <div>
           <span class="text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-1">Mã liệu trình</span>
           <div class="flex items-center gap-2 active:opacity-60 transition-opacity" onclick={copyOrderId} role="button" tabindex="0">
             <span class="text-sm font-black text-slate-900 tracking-widest uppercase italic bg-slate-50 px-2 py-1 border border-slate-100">{copied ? 'ĐÃ SAO CHÉP!' : `#${orderId.slice(-6).toUpperCase()}`}</span>
           </div>
        </div>
        <div class="text-right">
           <span class="text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-1">Tổng tiền</span>
           <span class="text-xl font-black text-[#ee4d2d] italic">{(order?.total || 0).toLocaleString()}đ</span>
        </div>
      </div>

      <div class="space-y-6">
        <div class="flex items-start gap-4">
          <div class="w-10 h-10 rounded-sm bg-slate-50 border border-slate-50 flex items-center justify-center shrink-0">
             <Package class="w-5 h-5 text-slate-300" />
          </div>
          <div class="flex-1">
            <span class="text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-1">Sản phẩm trong đơn</span>
            <div class="space-y-1">
              {#each items as item}
                <p class="text-[11px] font-bold text-slate-800 leading-snug uppercase mb-1">
                  {item.quantity}x {item.name}
                </p>
              {/each}
            </div>
          </div>
        </div>

        <div class="flex items-start gap-4">
          <div class="w-10 h-10 rounded-sm bg-slate-50 border border-slate-50 flex items-center justify-center shrink-0">
             <Truck class="w-5 h-5 text-slate-300" />
          </div>
          <div class="flex-1">
            <span class="text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-1">Giao đến</span>
            <p class="text-[11px] font-bold text-slate-900 leading-tight uppercase italic">{customerName}</p>
            <p class="text-[10px] font-bold text-slate-400 leading-snug uppercase mt-1">{customerAddress}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- What's Next Card (White Mode) -->
    <div in:fly={{ y: 30, duration: 800, delay: 800 }} class="w-full bg-white border border-slate-100 rounded-none p-8 text-center relative overflow-hidden group shadow-sm">
       <div class="relative z-10">
         <span class="text-[10px] font-black text-sky-600 uppercase tracking-[0.4em] block mb-4 italic flex items-center justify-center gap-2">
           <Sparkles class="w-3.5 h-3.5" /> TIẾP THEO LÀ GÌ?
         </span>
         <p class="text-[12px] font-bold text-slate-500 leading-relaxed max-w-[260px] mx-auto mb-6 uppercase">
           Hệ thống đang xử lý. Chuyên gia sẽ xác nhận đơn trong vòng **15 phút** tới!
         </p>
         <div class="flex items-center justify-center gap-3 py-3 px-6 bg-slate-50 rounded-full border border-slate-100 mx-auto w-fit">
            <div class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
            <span class="text-[9px] font-black text-slate-400 uppercase tracking-widest">Hệ thống đã sẵn sàng</span>
         </div>
       </div>
    </div>

    <!-- Spacer -->
    <div class="h-40 shrink-0 pointer-events-none"></div>
  </div>

  <!-- Action Stack (White Mode) -->
  <div class="fixed bottom-0 left-0 w-full p-6 bg-gradient-to-t from-white via-white/95 to-transparent flex flex-row gap-3 items-center">
    <a 
      href="tel:{SHOP_CONFIG.pharmacy.phone.replace(/\s+/g, '')}"
      class="w-full py-5 bg-slate-900 text-white font-black text-[14px] uppercase tracking-[0.2em] active:scale-95 transition-all relative overflow-hidden text-center shadow-2xl flex items-center justify-center gap-3 italic"
    >
        GỌI XÁC NHẬN NGAY <Phone class="w-4 h-4 fill-white" />
    </a>
  </div>
</div>


<style lang="postcss">
  :global(body) {
    background-color: #fafafa;
  }

  .stepper-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 4px 44px;
  }

  .connector {
    flex: 1;
    position: relative;
    height: 2px;
    margin: 0 4px;
  }
  
  .connector-track {
    position: absolute;
    inset: 0;
    border-radius: 99px;
    background: #f1f5f9;
  }
  
  .connector-fill {
    position: absolute;
    top: 0; left: 0; bottom: 0;
    width: 100%;
    border-radius: 99px;
    transition: width 0.9s cubic-bezier(0.4,0,0.2,1);
  }

  .stepper-node {
    position: relative;
    z-index: 10;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .node-circle {
    position: relative;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid;
    transition: all 0.5s cubic-bezier(0.4,0,0.2,1);
  }

  .node-label {
    position: absolute;
    top: 44px;
    font-size: 8px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    white-space: nowrap;
    transition: color 0.5s ease;
  }

  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(0,0,0,0.05);
    border-radius: 10px;
  }

  @keyframes halo-pulse {
    0%, 100% { opacity: 0.45; transform: scale(1); }
    50%       { opacity: 0.9;  transform: scale(1.35); }
  }
</style>
