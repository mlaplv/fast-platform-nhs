<script lang="ts">
  import Package from "@lucide/svelte/icons/package";
  import Clock from "@lucide/svelte/icons/clock";
  import Check from "@lucide/svelte/icons/check";
  import Truck from "@lucide/svelte/icons/truck";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import PackageCheck from "@lucide/svelte/icons/package-check";
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import Phone from "@lucide/svelte/icons/phone";
  import MapPin from "@lucide/svelte/icons/map-pin";
  import User from "@lucide/svelte/icons/user";
  import Calendar from "@lucide/svelte/icons/calendar";
  import Shield from "@lucide/svelte/icons/shield";
  import XCircle from "@lucide/svelte/icons/x-circle";
  import MessageSquare from "@lucide/svelte/icons/message-square";
  import StatusDropdown from "./StatusDropdown.svelte";
  import { ORDER_TRANSITIONS } from "$lib/constants/order";
  import { SHOP_CONFIG } from "$lib/constants/shop";
  import { formatCurrency, formatDate, timeAgo } from "$lib/utils/format";
  import type { Order } from "$lib/types";

  let { order, status, isSelected = false, onOpenDetail, onAction, onToggleSelect } = $props<{
    order: Order;
    status: { label: string; color: string; border: string };
    isSelected?: boolean;
    onOpenDetail: (id: string) => void;
    onAction: (id: string, action: string) => void;
    onToggleSelect: (id: string) => void;
  }>();

  function handleAction(e: Event, actionType: string) {
    e.stopPropagation();
    onAction(order.id, actionType);
  }

  async function openZalo(e: Event) {
    e.stopPropagation();
    if (!order.customerPhone) return;
    
    const phone = order.customerPhone.replace(/\D/g, '');
    const shopName = SHOP_CONFIG.pharmacy.name;
    const orderIdShort = order.id.split('-')[0].toUpperCase();
    const total = formatCurrency(order.total);

    const message = `Chào bạn ${order.finalCustomerName}, ${shopName} xác nhận đơn hàng #${orderIdShort} của bạn. Tổng thanh toán: ${total}. Shop sẽ sớm giao hàng cho bạn nhé!`;
    
    try {
      // Elite Clipboard Integration
      await navigator.clipboard.writeText(message);
      nanobot.showToast("Đã copy tin nhắn mẫu! Hãy Dán (Paste) vào Zalo.", "success");
      
      // Delay slightly to ensure toast is seen before tab switch
      setTimeout(() => {
        window.open(`https://zalo.me/${phone}`, '_blank');
      }, 300);
    } catch (err) {
      // Fallback if clipboard fails
      window.open(`https://zalo.me/${phone}?text=${encodeURIComponent(message)}`, '_blank');
    }
  }
</script>

<div
  role="button"
  tabindex="0"
  onclick={() => onOpenDetail(order.id)}
  onkeydown={(e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onOpenDetail(order.id);
    }
  }}
  class="order-item group flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4 w-full {isSelected ? 'border-neon-cyan/30 bg-neon-cyan/[0.02]' : ''} {order.isSpam
    ? 'border-red-500/30 bg-red-500/[0.01]'
    : ''}"
>
  <div class="flex items-start sm:items-center gap-3 w-full">
    <!-- Selection Checkbox (Elite V2.2) -->
    <div 
      class="shrink-0 flex items-center justify-center w-6 h-6 grayscale hover:grayscale-0 transition-all"
      onclick={(e) => { e.stopPropagation(); onToggleSelect(order.id); }}
      onkeydown={(e) => { if (e.key === ' ') { e.stopPropagation(); onToggleSelect(order.id); } }}
      role="checkbox"
      aria-checked={isSelected}
      tabindex="0"
    >
      <div class="w-4 h-4 rounded border-2 transition-all flex items-center justify-center
        {isSelected ? 'bg-neon-cyan border-neon-cyan' : 'bg-transparent border-white/20 group-hover:border-white/40'}">
        {#if isSelected}
          <Check size={12} strokeWidth={4} class="text-black" />
        {/if}
      </div>
    </div>

    <!-- Avatar / Icon -->
    <div
      class="w-10 h-10 sm:w-12 sm:h-12 rounded bg-black border {status.border}/20 flex items-center justify-center shrink-0"
    >
      <Package size={18} class="{status.color} opacity-80" />
    </div>

    <!-- Core Data -->
    <div
      class="flex-1 min-w-0 flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 xl:gap-8"
    >
      <!-- Identity & Contact Block -->
      <div class="min-w-[200px] flex flex-col gap-1">
        <div
          class="text-[9px] font-mono text-gray-500 uppercase tracking-widest flex items-center gap-2"
        >
          <span>ID: {order.id.split("-")[0]}</span>
          {#if order.customerIp}
            <div class="flex items-center gap-1 bg-neon-cyan/10 border border-neon-cyan/30 px-1.5 py-0.5 rounded-sm">
              <span class="text-[7px] text-neon-cyan/60 uppercase font-bold">IP</span>
              <span class="text-[8px] text-neon-cyan font-mono">{order.customerIp}</span>
            </div>
          {/if}

          {#if order.status === "pending"}
            <span class="w-1.5 h-1.5 rounded-full bg-[#FFB800] animate-pulse ml-auto"
            ></span>
          {/if}
        </div>
        <div class="flex flex-col gap-1.5">
          <div class="flex items-center gap-2">
            <div class="text-[13px] sm:text-sm font-bold {order.successfulOrdersCount >= 3 ? 'text-emerald-400 bg-emerald-400/10 px-1.5 rounded-sm' : 'text-white'} truncate max-w-[180px]">
              {order.finalCustomerName}
            </div>
            {#if order.successfulOrdersCount >= 5}
              <span class="text-[8px] bg-amber-400/20 text-amber-400 px-1 rounded-sm border border-amber-400/30 uppercase font-black tracking-tighter">VIP Elite</span>
            {:else if order.successfulOrdersCount === 0 && order.cancelledOrdersCount === 0}
              <span class="text-[8px] bg-blue-500/20 text-blue-400 px-1 rounded-sm border border-blue-400/30 uppercase font-bold tracking-tighter">New</span>
            {/if}
          </div>
          
          <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
            {#if order.customerPhone}
              <div class="text-[10px] font-mono text-neon-cyan/80 flex items-center gap-1">
                <Phone size={10} class="opacity-60" />
                {order.customerPhone}
                {#if order.order_metadata?.zalo_status === 'ACTIVE'}
                  <div class="flex items-center gap-0.5 text-blue-400 bg-blue-400/10 px-1 rounded-[2px] ml-1">
                    <MessageSquare size={8} />
                    <span class="text-[7px] font-black tracking-tighter">ZALO</span>
                  </div>
                {/if}
              </div>
            {/if}
            
            <!-- Trust Radar -->
            <div class="flex items-center gap-1.5 min-h-[16px]">
              {#if order.successfulOrdersCount > 0}
                <div class="flex items-center gap-1 text-[9px] text-emerald-500 bg-emerald-500/5 px-1 rounded-sm border border-emerald-500/10">
                  <span class="font-bold">{order.successfulOrdersCount}</span>
                  <span class="opacity-50 text-[7px] uppercase font-bold">Done</span>
                </div>
              {/if}
              {#if order.cancelledOrdersCount > 0}
                <div class="flex items-center gap-1 text-[9px] text-rose-500 bg-rose-500/5 px-1 rounded-sm border border-rose-500/10">
                  <span class="font-bold">{order.cancelledOrdersCount}</span>
                  <span class="opacity-50 text-[7px] uppercase font-bold">Burn</span>
                </div>
              {/if}
            </div>
          </div>

          {#if order.customerAddress}
            <div class="text-[10px] text-gray-500 italic truncate max-w-[220px] flex items-center gap-1" title={order.customerAddress}>
              <MapPin size={10} class="shrink-0 opacity-40" />
              {order.customerAddress}
            </div>
          {/if}
        </div>
      </div>

      <!-- Mobile-only quick stats row -->
      <div class="flex sm:hidden items-center gap-3 mt-1">
        <div class="text-[11px] font-mono font-bold text-green-400">
          {formatCurrency(order.total)}
        </div>
        <div class="text-[10px] font-mono text-gray-500 flex items-center gap-1">
          <span class="text-white font-bold">{order.itemCount}</span>
          <span class="text-[8px]">UNITS</span>
        </div>
        <div class="text-[9px] font-mono text-gray-400 ml-auto">
          {timeAgo(order.createdAt)}
        </div>
      </div>

      <!-- Desktop Items Count -->
      <div class="hidden sm:block min-w-[60px]">
        <div
          class="text-[9px] font-mono text-gray-500 uppercase tracking-widest mb-1"
        >
          Payload
        </div>
        <div class="text-xs font-mono text-gray-300">
          <span class="font-bold text-white">{order.itemCount}</span>
          <span class="text-[9px] text-gray-600 ml-1">UNITS</span>
        </div>
      </div>

      <!-- Desktop Planning (Elite V2.2) -->
      <div class="hidden xl:flex flex-col gap-1.5 min-w-[150px] border-l border-white/5 pl-6">
        {#if order.planning?.assigned_to}
          <div class="flex items-center gap-2 text-[10px] text-white/90 font-mono">
            <User size={10} class="text-orange-400" />
            <span class="truncate max-w-[120px]">{order.planning.assigned_to}</span>
          </div>
        {:else}
          <div class="flex items-center gap-2 text-[9px] text-gray-600 font-mono italic">
            <User size={10} /> Unassigned
          </div>
        {/if}

        {#if order.planning?.scheduled_at}
          <div class="flex items-center gap-2 text-[9px] text-gray-500 font-mono">
            <Calendar size={10} class="text-blue-400" />
            <span>{formatDate(order.planning.scheduled_at)}</span>
          </div>
        {/if}

        {#if order.planning?.priority && order.planning.priority !== 'NORMAL'}
          <div class="flex items-center gap-1.5 mt-0.5">
            <span class="text-[7px] px-1.5 py-0.5 rounded-full font-black uppercase tracking-widest border
              {order.planning.priority === 'URGENT' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' : 
               'bg-orange-500/10 text-orange-400 border-orange-500/20'}">
              {order.planning.priority}
            </span>
          </div>
        {/if}
      </div>

      <!-- Desktop Financials -->
      <div class="hidden sm:block min-w-[120px]">
        <div
          class="text-[9px] font-mono text-gray-500 uppercase tracking-widest mb-1"
        >
          Capital Transfer
        </div>
        <div class="text-sm font-bold font-mono text-green-400 tracking-wider">
          {formatCurrency(order.total)}
        </div>
      </div>
    </div>

    <!-- Status Badge (Mobile Top Right, Desktop inline) -->
    <div
      class="flex items-center gap-2 shrink-0 mt-1 sm:mt-0 sm:ml-auto xl:ml-0 relative"
    >
      {#if order.isSpam}
        <div class="relative group/spam">
          <!-- Primary Spam Indicator -->
          <div
            class="px-2 py-1 rounded bg-red-500/20 border border-red-500/50 flex items-center gap-1.5 animate-pulse cursor-help relative"
          >
            <span class="w-1.5 h-1.5 rounded-full bg-red-500 shrink-0"></span>
            <span
              class="text-[8px] sm:text-[9px] font-mono font-bold tracking-widest uppercase text-red-400"
              >SPAM ALERT</span
            >
            
            <!-- Mini Shield Indicator (Pinned stably to the badge) -->
            <div class="absolute -top-1.5 -right-1.5 bg-red-500 rounded-full p-0.5 shadow-[0_0_10px_rgba(239,68,68,0.5)] border border-black/20 z-10">
              <Shield size={8} class="text-white" fill="currentColor" />
            </div>
          </div>

          <!-- Viral 2026 Security Tooltip (Horizontal Scanner Design) -->
          <div
            class="absolute top-1/2 -translate-y-1/2 right-full mr-4 w-[450px] h-[48px] bg-black/95 border border-red-500/40 rounded-lg backdrop-blur-xl opacity-0 invisible group-hover/spam:opacity-100 group-hover/spam:visible transition-all duration-300 pointer-events-none shadow-[0_0_30px_rgba(239,68,68,0.2)] flex items-center px-4 gap-6 overflow-hidden"
            style="z-index: var(--z-popover);"
          >
            <div class="flex flex-col shrink-0">
              <span
                class="text-[7px] font-mono text-red-500/60 uppercase tracking-tighter"
                >Trace Mode</span
              >
              <span
                class="text-[10px] font-mono font-bold text-red-500 animate-pulse"
                >VIRAL_2026</span
              >
            </div>

            <div class="h-6 w-px bg-red-500/20"></div>

            <div class="flex-1 flex items-center gap-4">
              <!-- Score -->
              <div class="flex flex-col gap-1 w-20">
                <span class="text-[7px] font-mono text-gray-500 uppercase"
                  >Suspicion</span
                >
                <div class="flex items-center gap-1.5">
                  <div
                    class="h-1 flex-1 bg-red-900/40 rounded-full overflow-hidden"
                  >
                    <div
                      class="h-full bg-red-500 shadow-[0_0_5px_rgba(239,68,68,1)]"
                      style="width: {order.spamScore ?? 0}%"
                    ></div>
                  </div>
                  <span class="text-[9px] font-mono text-red-400"
                    >{(order.spamScore ?? 0).toFixed(0)}%</span
                  >
                </div>
              </div>

              <!-- Target -->
              <div class="flex flex-col gap-0.5 min-w-[100px]">
                <span class="text-[7px] font-mono text-gray-500 uppercase"
                  >Target_Lock</span
                >
                <span class="text-[9px] font-mono text-gray-300 truncate">
                  {order.id.split('-')[0]}
                </span>
              </div>

              <!-- Reason -->
              <div class="flex flex-col gap-0.5 flex-1">
                <span class="text-[7px] font-mono text-gray-500 uppercase"
                  >Heuristics</span
                >
                <span
                  class="text-[9px] text-white italic truncate max-w-[140px]"
                >
                  "{order.spamReason || "Anomaly detected"}"
                </span>
              </div>
            </div>

            <!-- Scanner Decoration -->
            <div
              class="absolute inset-y-0 right-0 w-24 bg-gradient-to-l from-red-500/10 to-transparent pointer-events-none"
            ></div>
          </div>
        </div>
      {/if}

      <!-- Status Hub -->
      <div class="flex items-center gap-1.5 p-1 bg-white/[0.02] border border-white/5 rounded-lg shadow-inner group/hub">
        <StatusDropdown 
          variant="badge"
          currentStatus={order.status}
          label={status.label}
          color={status.color}
          border={status.border}
          options={ORDER_TRANSITIONS[order.status.toLowerCase()] || []}
          onSelect={(val) => onAction(order.id, val)}
          actions={[
            ...(order.status === 'pending' ? [
              { label: 'XÁC NHẬN & ĐÓNG GÓI', value: 'PACKED', icon: ShieldCheck, color: 'text-cyan-400' },
              { label: 'HỦY ĐƠN HÀNG', value: 'CANCELLED', icon: XCircle, color: 'text-red-400' }
            ] : []),
            ...(order.status === 'packed' ? [
              { label: 'BÀN GIAO VẬN CHUYỂN', value: 'SHIPPING', icon: Truck, color: 'text-lime-400' },
              { label: 'HỦY ĐƠN HÀNG', value: 'CANCELLED', icon: XCircle, color: 'text-red-400' }
            ] : []),
            ...(order.status === 'shipping' ? [
              { label: 'XÁC NHẬN GIAO HÀNG', value: 'DELIVERED', icon: PackageCheck, color: 'text-emerald-400' }
            ] : []),
            { label: 'ĐÁNH DẤU SPAM', value: 'TOGGLE_SPAM', icon: ShieldAlert, color: order.isSpam ? 'text-red-500' : 'text-gray-500' }
          ]}
        />

        <!-- High-Priority Quick-Fire Actions (V4 Elite) -->
        <div class="flex items-center gap-1 opacity-0 group-hover/hub:opacity-100 transition-opacity border-l border-white/10 ml-1 pl-1">
          {#if order.customerPhone}
            <button
              onclick={openZalo}
              class="w-7 h-7 rounded {order.order_metadata?.zalo_status === 'ACTIVE' ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' : 'bg-white/5 text-white/40 border-white/10'} border flex items-center justify-center hover:bg-blue-500 hover:text-black transition-all group/zalo"
              title="Zalo Chat Elite"
            >
              <MessageSquare size={12} class="group-hover/zalo:scale-110 transition-transform" />
            </button>
          {/if}

          {#if order.status === 'pending'}
             <button 
              onclick={(e) => { e.stopPropagation(); onAction(order.id, 'PACKED') }}
              class="w-7 h-7 rounded bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center hover:bg-cyan-500 hover:text-black transition-all group/btn"
              title="Confirm & Pack"
             >
               <ShieldCheck size={14} class="group-hover/btn:scale-110 transition-transform" />
             </button>
          {:else if order.status === 'packed'}
             <button 
              onclick={(e) => { e.stopPropagation(); onAction(order.id, 'SHIPPING') }}
              class="w-7 h-7 rounded bg-lime-500/10 border border-lime-500/20 text-lime-400 flex items-center justify-center hover:bg-lime-500 hover:text-black transition-all group/btn"
              title="Ship Order"
             >
               <Truck size={14} class="group-hover/btn:scale-110 transition-transform" />
             </button>
          {:else if order.status === 'shipping'}
             <button 
              onclick={(e) => { e.stopPropagation(); onAction(order.id, 'DELIVERED') }}
              class="w-7 h-7 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center hover:bg-emerald-500 hover:text-black transition-all group/btn"
              title="Mark Delivered"
             >
               <PackageCheck size={14} class="group-hover/btn:scale-110 transition-transform" />
             </button>
          {/if}
        </div>
      </div>
    </div>

    <!-- Desktop Timestamp -->
    <div
      class="hidden xl:flex flex-col items-end shrink-0 pl-6 border-l border-white/5 min-w-[80px]"
    >
      <Clock size={12} class="text-neon-cyan mb-1.5 opacity-60" />
      <span
        class="text-[10px] font-mono text-gray-500 uppercase text-right w-full"
        >{timeAgo(order.createdAt)}</span
      >
    </div>
  </div>
</div>

<style>
  /* ZERO-REFLOW hover: only background-color changes, no border/size/shadow changes */
  .order-item {
    position: relative;
    background-color: #050505;
    border-bottom: 1px solid rgba(255, 255, 255, 0.03);
    border-radius: 0;
    padding: 0.5rem 1rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    width: 100%;
    cursor: pointer;
  }
  @media (min-width: 640px) {
    .order-item {
      padding: 0.5rem 1rem;
    }
  }
  .order-item:hover {
    background: rgba(255, 255, 255, 0.02);
    z-index: var(--z-surface);
    position: relative;
  }
  .action-btn {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
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
