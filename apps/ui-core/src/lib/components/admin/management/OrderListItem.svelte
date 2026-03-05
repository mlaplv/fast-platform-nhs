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
  class="group relative flex items-center justify-between p-5 bg-[#0a0a0a] border border-white/5 rounded-xl hover:border-white/20 hover:bg-white/[0.02] transition-all text-left overflow-hidden shadow-sm hover:shadow-[0_4px_20px_rgba(0,0,0,0.5)] w-full cursor-pointer"
>
  <!-- Hover Scan Line -->
  <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent w-full h-full -translate-x-full group-hover:translate-x-full transition-transform duration-1000 ease-in-out"></div>
  
  <div class="flex items-center gap-6 relative z-10 w-full">
    <!-- Avatar / Icon -->
    <div class="w-12 h-12 rounded bg-black border {status.border}/20 flex items-center justify-center shrink-0 relative overflow-hidden">
      <Package size={18} class="{status.color} opacity-80" />
      {#if order.status === 'pending' || order.status === 'processing'}
        <div class="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,currentColor,transparent_70%)] opacity-10" style:color={status.color.replace('text-', '')}></div>
      {/if}
    </div>
    
    <!-- Core Data -->
    <div class="flex-1 min-w-0 flex flex-wrap gap-4 sm:gap-8 items-center justify-between xl:justify-start">
      <!-- ID & Customer -->
      <div class="min-w-[150px]">
        <div class="text-[9px] font-mono text-gray-500 uppercase tracking-widest mb-1 flex items-center gap-2">
          ID: {order.id.split('-')[0]}...
          {#if order.status === 'pending'}
            <span class="w-1.5 h-1.5 rounded-full bg-[#FFB800] animate-pulse"></span>
          {/if}
        </div>
        <div class="text-sm font-bold text-white truncate max-w-[200px]">{order.customerName}</div>
      </div>
      
      <!-- Items Count -->
      <div class="hidden sm:block min-w-[60px]">
        <div class="text-[9px] font-mono text-gray-500 uppercase tracking-widest mb-1">Payload</div>
        <div class="text-xs font-mono text-gray-300">
          <span class="font-bold text-white">{order.items}</span>
          <span class="text-[9px] text-gray-600 ml-1">UNITS</span>
        </div>
      </div>

      <!-- Financials -->
      <div class="min-w-[120px]">
        <div class="text-[9px] font-mono text-gray-500 uppercase tracking-widest mb-1">Capital Transfer</div>
        <div class="text-sm font-bold font-mono text-green-400 tracking-wider">
          {formatCurrency(order.total)}
        </div>
      </div>
      
      <!-- Status Badge -->
      <div class="flex justify-start items-center ml-auto xl:ml-0">
        <div class="px-3 py-1.5 rounded bg-black border {status.border}/30 flex items-center gap-2 shadow-inner group-hover:bg-white/[0.02] transition-colors whitespace-nowrap">
          <span class="w-1.5 h-1.5 rounded-full" style:background-color={status.color.replace('text-', '')} style:box-shadow={`0 0 8px ${status.color.replace('text-', '')}`}></span>
          <span class="text-[9px] font-mono font-bold tracking-widest uppercase {status.color}">{status.label}</span>
        </div>
      </div>
    </div>
    
    <!-- Quick Actions (Shows on hover/large screens) -->
    <div class="hidden md:flex items-center gap-2 shrink-0">
      {#if order.status === 'pending'}
        <button onclick={(e) => handleAction(e, 'PAID')} class="p-2 bg-green-500/10 hover:bg-green-500/20 text-green-400 border border-green-500/30 rounded-lg transition-all" title="Xác nhận thanh toán">
          <CheckCircle size={16} />
        </button>
        <button onclick={(e) => handleAction(e, 'CANCELLED')} class="p-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 rounded-lg transition-all" title="Huỷ đơn">
          <XCircle size={16} />
        </button>
      {:else if order.status === 'paid'}
        <button onclick={(e) => handleAction(e, 'PROCESSING')} class="p-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded-lg transition-all" title="Chuẩn bị hàng">
          <Play size={16} />
        </button>
        <button onclick={(e) => handleAction(e, 'CANCELLED')} class="p-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 rounded-lg transition-all" title="Huỷ đơn">
          <XCircle size={16} />
        </button>
      {:else if order.status === 'processing'}
        <button onclick={(e) => handleAction(e, 'SHIPPED')} class="p-2 bg-fuchsia-500/10 hover:bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30 rounded-lg transition-all" title="Giao hàng">
          <Truck size={16} />
        </button>
      {:else if order.status === 'shipped'}
        <button onclick={(e) => handleAction(e, 'DELIVERED')} class="p-2 bg-green-500/10 hover:bg-green-500/20 text-green-400 border border-green-500/30 rounded-lg transition-all" title="Đã nhận hàng">
          <CheckCircle size={16} />
        </button>
      {:else if order.status === 'delivered'}
        <button onclick={(e) => handleAction(e, 'COMPLETED')} class="p-2 bg-neon-cyan/10 hover:bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/30 rounded-lg transition-all" title="Hoàn thành đơn">
          <CheckCircle size={16} />
        </button>
      {/if}
    </div>
    
    <!-- Timestamp (Right aligned on large screens) -->
    <div class="hidden xl:flex flex-col items-end shrink-0 pl-6 border-l border-white/5 opacity-60 group-hover:opacity-100 transition-opacity min-w-[80px]">
      <Clock size={12} class="text-neon-cyan mb-1.5" />
      <span class="text-[10px] font-mono text-gray-400 uppercase text-right w-full">{timeAgo(order.createdAt)}</span>
    </div>
  </div>
</div>
