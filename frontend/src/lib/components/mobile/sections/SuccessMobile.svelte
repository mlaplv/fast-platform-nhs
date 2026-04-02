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
  function copyOrderId() {
    if (typeof navigator !== 'undefined') {
        const shortId = orderId.slice(-6).toUpperCase();
        navigator.clipboard.writeText(shortId);
        copied = true;
        setTimeout(() => copied = false, 2000);
    }
  }

  const items = $derived(order?.items || []);
  const customerName = $derived(order?.customerName || order?.name_masked || 'Khách hàng');
  const customerAddress = $derived(order?.customerAddress || order?.address_masked || 'Địa chỉ bảo mật');
</script>

<div class="fixed inset-0 bg-[#0a0a0a] text-white overflow-y-auto custom-scrollbar flex flex-col">
  <!-- Top Navigation -->
  <button
    onclick={() => goto('/')}
    class="fixed top-4 right-6 w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center backdrop-blur-xl active:scale-95 transition-all text-white/40 ring-1 ring-white/5 shadow-2xl z-[2000]"
    aria-label="Home"
  >
    <Home class="w-4 h-4" />
  </button>

  <!-- Celebration Glow -->
  <div class="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[300px] {isLookup ? 'bg-sky-500/10' : 'bg-emerald-500/10'} blur-[100px] pointer-events-none"></div>

  <div class="relative px-6 pt-[10px] flex flex-col items-center text-center">
    <!-- Status Badge (Ultra-Refined) -->
    <div in:scale={{ duration: 600, delay: 200, start: 0.9 }} 
         class="px-4 py-1 rounded-full border border-white/5 bg-white/5 backdrop-blur-2xl mb-6 flex items-center gap-2 relative shadow-2xl">
      <div class="absolute inset-0 {isLookup ? 'bg-sky-400/5' : 'bg-emerald-400/5'} rounded-full blur-2xl"></div>
      {#if isLookup}
        <ShieldCheck class="w-3 h-3 text-sky-400 relative z-10" strokeWidth={2.5} />
        <span class="text-[9px] font-bold text-white/60 uppercase tracking-[0.2em] relative z-10">Status: Tracking</span>
      {:else}
        <CheckCircle2 class="w-3 h-3 text-emerald-400 relative z-10" strokeWidth={2.5} />
        <span class="text-[9px] font-bold text-white/60 uppercase tracking-[0.2em] relative z-10">Status: Success</span>
      {/if}
    </div>

    <h1 in:fly={{ y: 20, duration: 600, delay: 400 }} 
        class="text-3xl font-black italic tracking-tight uppercase mb-2 text-white/90 drop-shadow-[0_0_15px_rgba(255,255,255,0.1)]">
      {isLookup ? 'Chi tiết liệu trình' : 'Đặt liệu trình thành công'}
    </h1>
    
    <p in:fade={{ delay: 600 }} class="text-white/30 text-[10px] uppercase tracking-[0.3em] font-medium mb-12">
      {isLookup ? 'Cập nhật trạng thái xử lý mới nhất' : 'Cảm ơn Quý khách đã tin tưởng Elite'}
    </p>

    <!-- Status Timeline (Elite — Segmented Connectors) -->
    <div in:fly={{ y: 20, duration: 800, delay: 500 }} class="w-full mb-10 px-2">
      <div class="stepper-row">
        {#each STATUS_STEPS as step, i}
          <!-- Node -->
          <div class="stepper-node">
            {#if i === currentStepIdx}
              <div class="node-halo {isLookup ? 'halo-sky' : 'halo-emerald'}"></div>
            {/if}
            <div class="node-circle {
              i < currentStepIdx  ? (isLookup ? 'done-sky'   : 'done-emerald')   :
              i === currentStepIdx? (isLookup ? 'active-sky' : 'active-emerald') :
              'node-idle'}">
              <step.icon class="w-3.5 h-3.5" />
            </div>
            <span class="node-label {i <= currentStepIdx ? (isLookup ? 'label-sky' : 'label-emerald') : 'label-idle'}">
              {step.label}
            </span>
          </div>

          <!-- Connector segment (between nodes, not through them) -->
          {#if i < STATUS_STEPS.length - 1}
            <div class="connector">
              <div class="connector-track"></div>
              {#if i < currentStepIdx}
                <div class="connector-fill {isLookup ? 'fill-sky' : 'fill-emerald'}"></div>
              {:else if i === currentStepIdx}
                <div class="connector-fill connector-fill-half {isLookup ? 'fill-sky' : 'fill-emerald'}"></div>
              {/if}
            </div>
          {/if}
        {/each}
      </div>
    </div>


    <!-- Main Order Card -->
    <div in:fly={{ y: 30, duration: 800, delay: 600 }} class="w-full bg-white/[0.03] border border-white/10 backdrop-blur-xl rounded-[2.5rem] p-6 mb-6 text-left shadow-2xl">
      <div class="flex justify-between items-start mb-6 border-b border-white/5 pb-4">
        <div>
           <span class="text-[9px] font-black text-white/30 uppercase tracking-widest block mb-1">Mã liệu trình</span>
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
            <span class="text-[9px] font-black text-white/30 uppercase tracking-widest block mb-1">Chi tiết liệu trình</span>
            <p class="text-[11px] font-bold text-white/80 leading-snug">
              {items.map((i: { quantity: number, name: string }) => `${i.quantity}x ${i.name}`).join(', ') || 'Đang cập nhật...'}
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
    <div in:fly={{ y: 30, duration: 800, delay: 800 }} class="w-full bg-white/[0.02] border border-white/5 rounded-[2.5rem] p-8 text-center relative overflow-hidden group shadow-xl">
       <div class="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-transparent to-purple-500/10 opacity-50"></div>
       <div class="relative z-10">
         <span class="text-[10px] font-black text-blue-400 uppercase tracking-[0.4em] block mb-4 italic flex items-center justify-center gap-2">
           <Sparkles class="w-3 h-3" /> TIẾP THEO LÀ GÌ?
         </span>
         <p class="text-[12px] font-medium text-white/70 leading-relaxed max-w-[260px] mx-auto mb-6">
           Hệ thống đang xử lý liệu trình. Chuyên gia sẽ gọi điện xác nhận cho Quý khách trong vòng **15 phút** tới!
         </p>
         <div class="flex items-center justify-center gap-3 py-3 px-4 bg-white/5 rounded-2xl border border-white/5 mx-auto w-fit">
            <div class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>
            <span class="text-[9px] font-black text-white/40 uppercase tracking-widest">Đội ngũ Elite đã sẵn sàng</span>
         </div>
       </div>
    </div>

    <!-- Spacer to ensure content clears the fixed Action Stack -->
    <div class="h-40 shrink-0 pointer-events-none"></div>
  </div>

  <!-- Action Stack (Elite 1-Row Compact) -->
  <div class="fixed bottom-0 left-0 w-full p-6 bg-gradient-to-t from-[#0a0a0a] via-[#0a0a0a]/95 to-transparent flex flex-row gap-3 items-center">
    <a 
      href="tel:{SHOP_CONFIG.pharmacy.phone.replace(/\s+/g, '')}"
      class="flex-[1.5] py-4 text-white font-black text-[12px] uppercase tracking-wider rounded-full btn-primary-viral active:scale-95 transition-all overflow-hidden relative group text-center"
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

  /* ── Stepper Row (interleaved: node · connector · node) ── */
  .stepper-row {
    display: flex;
    align-items: center;          /* vertically center icons + connectors */
    justify-content: space-between;
    padding: 16px 4px 44px;       /* bottom space for labels */
  }

  /* Connector lives BETWEEN two node circles */
  .connector {
    flex: 1;
    position: relative;
    height: 2px;
    margin: 0 2px;                /* tiny gap so line doesn't touch icon border */
  }
  .connector-track {
    position: absolute;
    inset: 0;
    background: rgba(255,255,255,0.07);
    border-radius: 99px;
  }
  .connector-fill {
    position: absolute;
    top: 0; left: 0; bottom: 0;
    width: 100%;
    border-radius: 99px;
    transition: width 0.9s cubic-bezier(0.4,0,0.2,1);
  }
  .connector-fill-half { width: 50%; }
  .fill-emerald { background: linear-gradient(90deg, #10b981, #34d399); box-shadow: 0 0 10px rgba(16,185,129,0.5); }
  .fill-sky     { background: linear-gradient(90deg, #0ea5e9, #38bdf8); box-shadow: 0 0 10px rgba(14,165,233,0.5); }


  /* ── Individual Node ─────────────────────────── */
  .stepper-node {
    position: relative;
    z-index: 10;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  /* Glow halo behind active node */
  .node-halo {
    position: absolute;
    top: -8px; left: -8px; right: -8px; bottom: -8px;
    border-radius: 50%;
    filter: blur(14px);
    pointer-events: none;
    animation: halo-pulse 2.2s ease-in-out infinite;
  }
  .halo-emerald { background: rgba(16,185,129,0.4); }
  .halo-sky     { background: rgba(14,165,233,0.4); }

  /* Node circle 32×32 */
  .node-circle {
    position: relative;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid transparent;
    transition: all 0.5s cubic-bezier(0.4,0,0.2,1);
  }
  .node-idle {
    background: rgba(255,255,255,0.03);
    border-color: rgba(255,255,255,0.08);
    color: rgba(255,255,255,0.2);
  }
  .done-emerald { background: rgba(16,185,129,0.15); border-color: rgba(16,185,129,0.7); color: #34d399; }
  .done-sky     { background: rgba(14,165,233,0.15); border-color: rgba(14,165,233,0.7); color: #38bdf8; }
  .active-emerald {
    background: rgba(16,185,129,0.18);
    border-color: #10b981;
    color: #fff;
    transform: scale(1.22);
    box-shadow: 0 0 0 5px rgba(16,185,129,0.1), 0 0 28px rgba(16,185,129,0.38);
  }
  .active-sky {
    background: rgba(14,165,233,0.18);
    border-color: #0ea5e9;
    color: #fff;
    transform: scale(1.22);
    box-shadow: 0 0 0 5px rgba(14,165,233,0.1), 0 0 28px rgba(14,165,233,0.38);
  }

  /* Labels — absolutely positioned under each node */
  .node-label {
    position: absolute;
    top: 40px;
    font-size: 7.5px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    white-space: nowrap;
    transition: color 0.5s ease;
  }
  .label-idle    { color: rgba(255,255,255,0.2); }
  .label-emerald { color: rgba(52,211,153,0.82); }
  .label-sky     { color: rgba(56,189,248,0.82); }

  @keyframes halo-pulse {
    0%, 100% { opacity: 0.45; transform: scale(1); }
    50%       { opacity: 0.9;  transform: scale(1.35); }
  }
</style>

