<script lang="ts">
  import Package from "lucide-svelte/icons/package";
  import Clock from "lucide-svelte/icons/clock";
  import CheckCircle from "lucide-svelte/icons/check-circle";
  import Truck from "lucide-svelte/icons/truck";
  import XCircle from "lucide-svelte/icons/x-circle";
  import Play from "lucide-svelte/icons/play";
  import Shield from "lucide-svelte/icons/shield";
  import Phone from "lucide-svelte/icons/phone";
  import MapPin from "lucide-svelte/icons/map-pin";
  import { formatCurrency, timeAgo } from "$lib/utils/format";
  import type { Order } from "$lib/types";

  let { order, status, onOpenDetail, onAction } = $props<{
    order: Order;
    status: { label: string; color: string; border: string };
    onOpenDetail: (id: string) => void;
    onAction: (id: string, action: string) => void;
  }>();

  function handleAction(e: Event, actionType: string) {
    e.stopPropagation();
    onAction(order.id, actionType);
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
  class="order-item group flex flex-col sm:flex-row items-stretch sm:items-center gap-4 sm:gap-6 w-full {order.isSpam
    ? 'border-red-500/50 bg-red-500/[0.02]'
    : ''}"
>
  <div class="flex items-start sm:items-center gap-4 w-full">
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
          {#if order.fingerprint}
            <div class="flex items-center gap-1 bg-fuchsia-500/10 border border-fuchsia-500/30 px-1.5 py-0.5 rounded-sm">
              <span class="text-[7px] text-fuchsia-400/60 uppercase font-bold">FP</span>
              <span class="text-[8px] text-fuchsia-400 font-mono">{order.fingerprint.substring(0, 8)}...</span>
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
      class="flex items-center gap-2 shrink-0 mt-1 sm:mt-0 sm:ml-auto xl:ml-0"
    >
      {#if order.isSpam}
        <div class="relative group/spam">
          <div
            class="px-2 py-1 rounded bg-red-500/20 border border-red-500/50 flex items-center gap-1.5 animate-pulse cursor-help"
          >
            <span class="w-1.5 h-1.5 rounded-full bg-red-500"></span>
            <span
              class="text-[8px] sm:text-[9px] font-mono font-bold tracking-widest uppercase text-red-400"
              >SPAM ALERT</span
            >
          </div>

          <!-- Viral 2026 Security Tooltip (Horizontal Scanner Design to avoid clipping) -->
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
                  {order.fingerprint
                    ? order.fingerprint.substring(0, 12)
                    : "UNKNOWN"}
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
      <div
        class="px-2 py-1 sm:px-3 sm:py-1.5 rounded bg-black border {status.border}/30 flex items-center gap-1.5 sm:gap-2 whitespace-nowrap"
      >
        <span
          class="w-1.5 h-1.5 rounded-full"
          style:background-color={status.color.replace("text-", "")}
        ></span>
        <span
          class="text-[8px] sm:text-[9px] font-mono font-bold tracking-widest uppercase {status.color}"
          >{status.label}</span
        >
      </div>
    </div>
  </div>

  <div
    class="flex items-center justify-between sm:contents mt-2 sm:mt-0 pt-3 sm:pt-0 border-t border-white/5 sm:border-0 w-full sm:w-auto"
  >
    <!-- Quick Actions (Mobile: bottom left, Desktop: inline right) -->
    <div class="flex items-center gap-1.5 sm:gap-2 shrink-0">
      {#if order.status === "pending"}
        <button
          onclick={(e) => handleAction(e, "PAID")}
          class="action-btn bg-green-500/10 hover:bg-green-500/20 text-green-400 border-green-500/30"
          title="Xác nhận thanh toán"
        >
          <CheckCircle size={18} />
        </button>
        <button
          onclick={(e) => handleAction(e, "CANCELLED")}
          class="action-btn bg-red-500/10 hover:bg-red-500/20 text-red-400 border-red-500/30"
          title="Huỷ đơn"
        >
          <XCircle size={18} />
        </button>
      {:else if order.status === "paid"}
        <button
          onclick={(e) => handleAction(e, "PROCESSING")}
          class="action-btn bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border-blue-500/30"
          title="Chuẩn bị hàng"
        >
          <Play size={18} />
        </button>
        <button
          onclick={(e) => handleAction(e, "CANCELLED")}
          class="action-btn bg-red-500/10 hover:bg-red-500/20 text-red-400 border-red-500/30"
          title="Huỷ đơn"
        >
          <XCircle size={18} />
        </button>
      {:else if order.status === "processing"}
        <button
          onclick={(e) => handleAction(e, "SHIPPED")}
          class="action-btn bg-fuchsia-500/10 hover:bg-fuchsia-500/20 text-fuchsia-400 border-fuchsia-500/30"
          title="Giao hàng"
        >
          <Truck size={18} />
        </button>
      {:else if order.status === "shipped"}
        <button
          onclick={(e) => handleAction(e, "DELIVERED")}
          class="action-btn bg-green-500/10 hover:bg-green-500/20 text-green-400 border-green-500/30"
          title="Đã nhận hàng"
        >
          <CheckCircle size={18} />
        </button>
      {:else if order.status === "delivered"}
        <button
          onclick={(e) => handleAction(e, "COMPLETED")}
          class="action-btn bg-neon-cyan/10 hover:bg-neon-cyan/20 text-neon-cyan border-neon-cyan/30"
          title="Hoàn thành đơn"
        >
          <CheckCircle size={18} />
        </button>
      {/if}

      <!-- Manual Spam Toggle (Shield) -->
      <button
        onclick={(e) => handleAction(e, "TOGGLE_SPAM")}
        class="action-btn {order.isSpam
          ? 'bg-red-500/10 hover:bg-gray-500/20 text-red-500 border-red-500/30'
          : 'bg-gray-500/10 hover:bg-red-500/20 text-gray-400 border-gray-500/20 hover:border-red-500/30'}"
        title={order.isSpam
          ? "Gỡ bỏ Spam (Whitelist)"
          : "Đánh dấu là Spam (Blacklist)"}
      >
        <Shield size={18} fill={order.isSpam ? "currentColor" : "none"} />
      </button>
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
  }
  @media (min-width: 640px) {
    .order-item {
      padding: 1.25rem;
    }
  }
  .order-item:hover {
    background: rgba(255, 255, 255, 0.03);
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
