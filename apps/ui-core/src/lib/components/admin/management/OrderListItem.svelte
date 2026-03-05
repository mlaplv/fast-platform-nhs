<script lang="ts">
  import Package from "lucide-svelte/icons/package";
  import Clock from "lucide-svelte/icons/clock";
  import CheckCircle from "lucide-svelte/icons/check-circle";
  import Truck from "lucide-svelte/icons/truck";
  import XCircle from "lucide-svelte/icons/x-circle";
  import Play from "lucide-svelte/icons/play";
  import type { Order } from "$lib/types";

  let { order, status, onClick, onAction } = $props<{
    order: Order;
    status: { label: string; color: string; border: string };
    onClick: (id: string) => void;
    onAction: (id: string, action: string) => void;
  }>();

  function handleAction(e: Event, actionType: string) {
    e.stopPropagation();
    onAction(order.id, actionType);
  }

  function formatCurrency(n: number): string {
    return new Intl.NumberFormat("vi-VN").format(n) + "đ";
  }

  function timeAgo(iso: string): string {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m trước`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h trước`;
    return `${Math.floor(hrs / 24)}d trước`;
  }
</script>

<div
  role="button"
  tabindex="0"
  onclick={() => onClick(order.id)}
  onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(order.id); } }}
  class="order-item group flex flex-col sm:flex-row items-stretch sm:items-center gap-4 sm:gap-6 w-full"
>
  <div class="flex items-start sm:items-center gap-4 w-full">
    <!-- Avatar / Icon -->
    <div class="w-10 h-10 sm:w-12 sm:h-12 rounded bg-black border {status.border}/20 flex items-center justify-center shrink-0">
      <Package size={18} class="{status.color} opacity-80" />
    </div>
    
    <!-- Core Data -->
    <div class="flex-1 min-w-0 flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 xl:gap-8">
      <!-- ID & Customer -->
      <div class="min-w-[120px]">
        <div class="text-[9px] font-mono text-gray-500 uppercase tracking-widest mb-0.5 flex items-center gap-1.5">
          ID: {order.id.split('-')[0]}
          {#if order.status === 'pending'}
            <span class="w-1 h-1 rounded-full bg-[#FFB800] animate-pulse"></span>
          {/if}
        </div>
        <div class="text-[13px] sm:text-sm font-bold text-white truncate max-w-[180px]">{order.customerName}</div>
      </div>
      
      <!-- Mobile-only quick stats row -->
      <div class="flex sm:hidden items-center justify-between mt-1">
        <div class="text-[11px] font-mono font-bold text-green-400">
          {formatCurrency(order.total)}
        </div>
        <div class="text-[9px] font-mono text-gray-400">
          {timeAgo(order.createdAt)}
        </div>
      </div>

      <!-- Desktop Items Count -->
      <div class="hidden sm:block min-w-[60px]">
        <div class="text-[9px] font-mono text-gray-500 uppercase tracking-widest mb-1">Payload</div>
        <div class="text-xs font-mono text-gray-300">
          <span class="font-bold text-white">{order.items}</span>
          <span class="text-[9px] text-gray-600 ml-1">UNITS</span>
        </div>
      </div>

      <!-- Desktop Financials -->
      <div class="hidden sm:block min-w-[120px]">
        <div class="text-[9px] font-mono text-gray-500 uppercase tracking-widest mb-1">Capital Transfer</div>
        <div class="text-sm font-bold font-mono text-green-400 tracking-wider">
          {formatCurrency(order.total)}
        </div>
      </div>
    </div>

    <!-- Status Badge (Mobile Top Right, Desktop inline) -->
    <div class="flex items-center shrink-0 mt-1 sm:mt-0 sm:ml-auto xl:ml-0">
      <div class="px-2 py-1 sm:px-3 sm:py-1.5 rounded bg-black border {status.border}/30 flex items-center gap-1.5 sm:gap-2 whitespace-nowrap">
        <span class="w-1.5 h-1.5 rounded-full" style:background-color={status.color.replace('text-', '')}></span>
        <span class="text-[8px] sm:text-[9px] font-mono font-bold tracking-widest uppercase {status.color}">{status.label}</span>
      </div>
    </div>
  </div>

  <div class="flex items-center justify-between sm:contents mt-2 sm:mt-0 pt-3 sm:pt-0 border-t border-white/5 sm:border-0 w-full sm:w-auto">
    <!-- Quick Actions (Mobile: bottom left, Desktop: inline right) -->
    <div class="flex items-center gap-1.5 sm:gap-2 shrink-0">
      {#if order.status === 'pending'}
        <button onclick={(e) => handleAction(e, 'PAID')} class="action-btn bg-green-500/10 hover:bg-green-500/20 text-green-400 border-green-500/30" title="Xác nhận thanh toán">
          <CheckCircle size={18} />
        </button>
        <button onclick={(e) => handleAction(e, 'CANCELLED')} class="action-btn bg-red-500/10 hover:bg-red-500/20 text-red-400 border-red-500/30" title="Huỷ đơn">
          <XCircle size={18} />
        </button>
      {:else if order.status === 'paid'}
        <button onclick={(e) => handleAction(e, 'PROCESSING')} class="action-btn bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border-blue-500/30" title="Chuẩn bị hàng">
          <Play size={18} />
        </button>
        <button onclick={(e) => handleAction(e, 'CANCELLED')} class="action-btn bg-red-500/10 hover:bg-red-500/20 text-red-400 border-red-500/30" title="Huỷ đơn">
          <XCircle size={18} />
        </button>
      {:else if order.status === 'processing'}
        <button onclick={(e) => handleAction(e, 'SHIPPED')} class="action-btn bg-fuchsia-500/10 hover:bg-fuchsia-500/20 text-fuchsia-400 border-fuchsia-500/30" title="Giao hàng">
          <Truck size={18} />
        </button>
      {:else if order.status === 'shipped'}
        <button onclick={(e) => handleAction(e, 'DELIVERED')} class="action-btn bg-green-500/10 hover:bg-green-500/20 text-green-400 border-green-500/30" title="Đã nhận hàng">
          <CheckCircle size={18} />
        </button>
      {:else if order.status === 'delivered'}
        <button onclick={(e) => handleAction(e, 'COMPLETED')} class="action-btn bg-neon-cyan/10 hover:bg-neon-cyan/20 text-neon-cyan border-neon-cyan/30" title="Hoàn thành đơn">
          <CheckCircle size={18} />
        </button>
      {/if}
    </div>

    <!-- Desktop Timestamp -->
    <div class="hidden xl:flex flex-col items-end shrink-0 pl-6 border-l border-white/5 min-w-[80px]">
      <Clock size={12} class="text-neon-cyan mb-1.5 opacity-60" />
      <span class="text-[10px] font-mono text-gray-500 uppercase text-right w-full">{timeAgo(order.createdAt)}</span>
    </div>
  </div>
</div>

<style>
  /* ZERO-REFLOW hover: only background-color changes, no border/size/shadow changes */
  .order-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem;
    background: #0a0a0a;
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 0.75rem;
    text-align: left;
    width: 100%;
    cursor: pointer;
    will-change: background-color;
    contain: layout style;
  }
  @media (min-width: 640px) {
    .order-item {
      padding: 1.25rem;
    }
  }
  .order-item:hover {
    background: rgba(255, 255, 255, 0.03);
  }
  .action-btn {
    width: 40px;
    height: 40px;
    display: flex;
    items-center: center;
    justify-content: center;
    border-width: 1px;
    border-style: solid;
    border-radius: 0.75rem;
    transition: all 0.2s;
  }
  .action-btn:active {
    scale: 0.9;
  }
</style>
