<script lang="ts">
  import { onMount } from "svelte";
  import { fade, fly } from "svelte/transition";
  import X from "lucide-svelte/icons/x";
  import Package from "lucide-svelte/icons/package";
  import User from "lucide-svelte/icons/user";
  import Calendar from "lucide-svelte/icons/calendar";
  import CreditCard from "lucide-svelte/icons/credit-card";
  import Activity from "lucide-svelte/icons/activity";
  import Clock from "lucide-svelte/icons/clock";
  import CheckCircle from "lucide-svelte/icons/check-circle";
  import Truck from "lucide-svelte/icons/truck";
  import Play from "lucide-svelte/icons/play";
  import ShieldAlert from "lucide-svelte/icons/shield-alert";
  import Phone from "lucide-svelte/icons/phone";
  import MapPin from "lucide-svelte/icons/map-pin";
  import TrendingUp from "lucide-svelte/icons/trending-up";
  import Target from "lucide-svelte/icons/target";
  import History from "lucide-svelte/icons/history";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { portal } from "$lib/actions/portal";
  import { formatCurrency, formatDate } from "$lib/utils/format";
  import type { OrderDetail } from "$lib/types";
  import { ORDER_STATUS_MAP } from "$lib/constants/order";

  let {
    isOpen = $bindable(),
    orderId = "",
    onClose,
    onReload
  } = $props<{
    isOpen: boolean;
    orderId: string;
    onClose: () => void;
    onReload?: () => void;
  }>();

  let orderData = $state<OrderDetail | null>(null);
  let isLoading = $state(false);

  $effect(() => {
    if (isOpen && orderId) {
      loadOrderDetails();
    }
  });

  async function loadOrderDetails() {
    isLoading = true;
    try {
      orderData = await apiClient.get<OrderDetail>(`/api/v1/orders/${orderId}`);
    } catch (err: unknown) {
      console.error("Failed to load order details", err);
    } finally {
      isLoading = false;
    }
  }

  async function handleAction(actionType: string) {
    const label = ORDER_STATUS_MAP[actionType.toLowerCase()]?.label || actionType;

    const confirm = await nanobot.showConfirm({
      title: "XÁC NHẬN CHUYỂN TRẠNG THÁI",
      message: `Đổi trạng thái đơn hàng sang "${label.toUpperCase()}"?\nHành động này sẽ được lưu vào lịch sử hệ thống.`,
      confirmLabel: "XÁC NHẬN",
      cancelLabel: "QUAY LẠI"
    });

    if (confirm) {
      isLoading = true;
      try {
        await apiClient.patch(`/api/v1/orders/${orderId}/status`, { status: actionType });
        nanobot.addLog("Cập nhật trạng thái " + actionType, "Nanobot-System");
        await loadOrderDetails();
        onReload?.();
      } catch (err: unknown) {
        const e = err as Error;
        nanobot.showToast(e.message || "Lỗi cập nhật", "error");
        isLoading = false;
      }
    }
  }

  async function handleCancel() {
    const reason = await nanobot.showConfirm({
      isPrompt: true,
      title: "XÁC NHẬN HUỶ ĐƠN",
      message: "Vui lòng nhập lý do huỷ đơn hàng:",
      defaultValue: "Khách yêu cầu",
      promptPlaceholder: "Lý do huỷ...",
      confirmLabel: "HUỶ ĐƠN",
      cancelLabel: "QUAY LẠI"
    });

    if (reason !== null) {
      isLoading = true;
      try {
        await apiClient.patch(`/api/v1/orders/${orderId}/cancel`, { reason });
        nanobot.addLog("Đã huỷ đơn hàng " + orderId.split('-')[0], "Nanobot-System");
        await loadOrderDetails();
        onReload?.();
      } catch (err: unknown) {
        const e = err as Error;
        nanobot.showToast(e.message || "Lỗi huỷ đơn", "error");
        isLoading = false;
      }
    }
  }

  // Removed local formatters (moved to centralized utils)
</script>

{#if isOpen}
  <div use:portal class="relative" style="z-index: var(--z-modal);">
    <!-- Backdrop -->
    <div
      class="fixed inset-0 bg-black/95 md:bg-black/90 md:backdrop-blur-sm"
      style="z-index: var(--z-overlay);"
      transition:fade={{ duration: 200 }}
      onclick={onClose}
      aria-label="Close drawer"
      role="button"
      tabindex="0"
      onkeydown={(e) => e.key === 'Escape' && onClose()}
    ></div>

    <!-- Drawer Panel -->
    <div
      class="fixed top-0 right-0 h-full w-[500px] max-w-full bg-[#050505] border-l border-white/10 shadow-[-30px_0_50px_rgba(0,0,0,0.8)] flex flex-col overflow-hidden"
      style="z-index: calc(var(--z-modal) + 10);"
      transition:fly={{ x: 500, duration: 300, opacity: 1 }}
    >
      <!-- Header -->
      <div class="h-16 flex items-center justify-between px-6 border-b border-white/10 relative bg-black/40">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded bg-neon-cyan/10 border border-neon-cyan/20 flex items-center justify-center">
            <Activity size={14} class="text-neon-cyan animate-pulse" />
          </div>
          <div>
            <h2 class="text-sm font-bold text-white tracking-widest uppercase">Order Details</h2>
            {#if orderId}
              <div class="text-[9px] font-mono text-gray-500 uppercase">SYS_ID: {orderId}</div>
            {/if}
          </div>
        </div>
        <button 
          onclick={onClose}
          class="w-8 h-8 flex items-center justify-center text-gray-500 hover:text-white hover:bg-white/10 rounded-lg transition-colors border border-transparent hover:border-white/10"
        >
          <X size={16} />
        </button>

        <!-- Decorative bottom line -->
        <div class="absolute bottom-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent"></div>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto custom-scrollbar p-6">
        {#if isLoading}
          <div class="h-full flex flex-col items-center justify-center gap-4">
            <div class="w-8 h-8 border-2 border-neon-cyan/20 border-t-neon-cyan rounded-full animate-spin"></div>
            <p class="text-[10px] font-mono text-neon-cyan/50 tracking-[0.2em] uppercase pulse">Decrypting data...</p>
          </div>
        {:else if orderData}
          {@const statusInfo = ORDER_STATUS_MAP[orderData.status.toLowerCase()] || { label: orderData.status, color: "text-gray-400", border: "border-gray-400" }}
          
          <!-- Status Banner -->
          <div class="mb-8 relative overflow-hidden rounded-xl border {statusInfo.border}/30 bg-black p-5 flex items-center justify-between">
            <div class="relative z-10">
              <div class="text-[9px] font-mono text-gray-500 mb-1 tracking-widest uppercase">Current Status</div>
              <div class="text-lg font-bold {statusInfo.color} tracking-wider">{statusInfo.label}</div>
            </div>
            <div class="w-12 h-12 rounded-full border {statusInfo.border}/20 flex items-center justify-center relative z-10 bg-white/5">
              <Package size={20} class={statusInfo.color} />
            </div>
            <div class="absolute inset-0 opacity-10" style:background="linear-gradient(45deg, transparent, currentColor)" style:color={statusInfo.color.replace('text-', '')}></div>
          </div>

          <!-- Customer 360 Insights (Viral 2026 Dashboard) -->
          <div class="mb-8">
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center gap-2">
                <Target size={12} class="text-neon-cyan" />
                <h3 class="text-[10px] font-mono text-white/80 uppercase tracking-widest font-bold">Customer 360 Insights</h3>
              </div>
              {#if orderData.insight && orderData.insight.trust_score >= 80}
                <span class="text-[8px] bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded-sm border border-emerald-500/30 uppercase font-black tracking-tighter">High Trust</span>
              {/if}
            </div>
            
            <div class="bg-white/[0.02] border border-white/5 rounded-xl p-5 flex flex-col gap-6">
              <!-- Grid Statistics -->
              <div class="grid grid-cols-2 gap-x-8 gap-y-6">
                <!-- Row 1: Identity -->
                <div class="col-span-2 flex items-center justify-between border-b border-white/5 pb-4">
                  <div>
                    <span class="block text-[8px] font-mono text-gray-500 mb-1 uppercase tracking-wider">Identified Persona</span>
                    <span class="text-sm font-bold text-white">{orderData.customerName}</span>
                  </div>
                  <div class="text-right">
                     <span class="block text-[8px] font-mono text-gray-500 mb-1 uppercase tracking-wider">Contact Trace</span>
                     <div class="flex items-center gap-2 text-neon-cyan font-mono text-[11px]">
                        <Phone size={10} class="opacity-50" />
                        {orderData.customerPhone || "UNREGISTERED"}
                     </div>
                  </div>
                </div>

                <!-- Row 2: Financials & History -->
                <div>
                  <div class="flex items-center gap-2 mb-1.5">
                    <TrendingUp size={10} class="text-emerald-400" />
                    <span class="text-[8px] font-mono text-gray-500 uppercase">Lifetime Value (LTV)</span>
                  </div>
                  <span class="text-base font-bold text-emerald-400 font-mono tracking-wider">
                    {formatCurrency(orderData.insight?.ltv || 0)}
                  </span>
                </div>

                <div>
                   <div class="flex items-center gap-2 mb-1.5">
                    <Package size={10} class="text-blue-400" />
                    <span class="text-[8px] font-mono text-gray-500 uppercase">Order Frequency</span>
                  </div>
                  <div class="flex items-baseline gap-1">
                    <span class="text-sm font-bold text-white font-mono">{orderData.insight?.total_orders || 1}</span>
                    <span class="text-[8px] text-gray-500 uppercase font-bold">Deployments</span>
                  </div>
                </div>

                <!-- Row 3: Trust Radar -->
                <div class="col-span-2 pt-2">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-[8px] font-mono text-gray-500 uppercase">Trust Radar Intelligence</span>
                    <span class="text-[10px] font-mono font-bold {orderData.insight?.trust_score ?? 0 >= 70 ? 'text-emerald-400' : 'text-rose-400'}">
                      {(orderData.insight?.trust_score ?? 0).toFixed(1)}% SUCCESS
                    </span>
                  </div>
                  <div class="h-1.5 w-full bg-white/5 rounded-full overflow-hidden flex">
                    <div 
                      class="h-full {orderData.insight?.trust_score ?? 0 >= 70 ? 'bg-emerald-500' : 'bg-rose-500'} shadow-[0_0_10px_rgba(16,185,129,0.3)] transition-all duration-1000" 
                      style="width: {orderData.insight?.trust_score ?? 0}%"
                    ></div>
                  </div>
                </div>

                <!-- Row 4: Timeline Trace -->
                {#if orderData.insight?.first_order}
                  <div class="col-span-2 bg-black/40 border border-white/5 rounded-lg p-3 flex items-center justify-between mt-2">
                    <div class="flex flex-col gap-1">
                       <span class="text-[7px] text-gray-500 uppercase font-bold">First Extraction</span>
                       <span class="text-[9px] font-mono text-gray-400">{formatDate(orderData.insight.first_order)}</span>
                    </div>
                    <div class="w-px h-6 bg-white/10 mx-4"></div>
                    <div class="flex flex-col gap-1 text-right">
                       <span class="text-[7px] text-gray-500 uppercase font-bold">Last Active</span>
                       <span class="text-[9px] font-mono text-neon-cyan">{formatDate(orderData.insight.last_order || orderData.createdAt)}</span>
                    </div>
                  </div>
                {/if}
              </div>

              {#if orderData.customerAddress}
                <div class="flex items-start gap-2 pt-4 border-t border-white/5">
                   <MapPin size={12} class="text-gray-500 mt-0.5" />
                   <span class="text-[10px] text-gray-400 italic leading-relaxed">{orderData.customerAddress}</span>
                </div>
              {/if}

              {#if orderData.cancellationReason}
                <div class="bg-rose-500/10 border border-rose-500/20 rounded-lg p-3 flex items-start gap-3 mt-2">
                  <ShieldAlert size={14} class="text-rose-400 shrink-0" />
                  <div>
                    <div class="text-[8px] text-rose-400 font-mono uppercase font-bold mb-0.5">Termination Reason</div>
                    <div class="text-[10px] text-rose-300 italic">"{orderData.cancellationReason}"</div>
                  </div>
                </div>
              {/if}
            </div>
          </div>

          <!-- Historical Purchase Timeline (Phase 4) -->
          {#if orderData.insight?.previous_orders && orderData.insight.previous_orders.length > 0}
            <div class="mb-8 p-1 border border-neon-cyan/10 rounded-2xl bg-neon-cyan/[0.01]">
              <div class="flex items-center gap-2 mb-4 px-3 pt-3">
                <History size={12} class="text-neon-cyan" />
                <h3 class="text-[10px] font-mono text-white/80 uppercase tracking-widest font-bold">Historical Purchase Timeline</h3>
              </div>
              
              <div class="bg-black/40 border border-white/5 rounded-xl overflow-hidden shadow-2xl">
                <div class="max-h-[320px] overflow-y-auto custom-scrollbar">
                  {#each orderData.insight.previous_orders as prev}
                    <div class="group border-b border-white/5 last:border-0 p-4 hover:bg-white/[0.03] transition-all">
                      <div class="flex items-center justify-between mb-2">
                        <div class="flex items-center gap-2">
                           <span class="text-[8px] font-mono text-gray-500 uppercase px-1 bg-white/5 rounded-sm">#{prev.id.slice(0,8)}</span>
                           <span class="text-[9px] font-mono text-gray-400">{formatDate(prev.created_at)}</span>
                        </div>
                        <span class="text-[7px] px-1.5 py-0.5 rounded-sm font-black uppercase tracking-tighter
                          {prev.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}">
                          {prev.status}
                        </span>
                      </div>
                      
                      <div class="flex items-center justify-between">
                         <div class="flex items-center gap-3">
                            <div class="flex items-baseline gap-1">
                               <span class="text-[10px] text-white font-bold">{prev.item_count}</span>
                               <span class="text-[7px] text-gray-500 uppercase font-black">Quantity</span>
                            </div>
                            <div class="w-1 h-1 bg-white/10 rounded-full"></div>
                            <span class="text-[10px] text-white/90 font-mono font-bold">{formatCurrency(prev.total)}</span>
                         </div>
                         <button 
                           class="text-[8px] text-neon-cyan hover:text-white bg-neon-cyan/10 hover:bg-neon-cyan px-2 py-0.5 rounded-full uppercase font-black tracking-tighter transition-all opacity-0 group-hover:opacity-100"
                         >
                           Analyze →
                         </button>
                      </div>
                    </div>
                  {/each}
                </div>
              </div>
              <div class="mt-2 pb-2 text-center text-[7px] text-gray-600 font-mono uppercase tracking-[0.2em] font-bold">
                Dữ liệu truy xuất từ 10 năm lịch sử
              </div>
            </div>
          {/if}

          <!-- Order Items -->
          <div class="mb-8">
            <div class="flex items-center gap-2 mb-4">
              <Package size={12} class="text-fuchsia-400" />
              <h3 class="text-[10px] font-mono text-white/80 uppercase tracking-widest font-bold">Cargo Manifest ({Array.isArray(orderData?.items) ? orderData.items.length : (orderData?.items ?? 0)})</h3>
            </div>
            <div class="bg-white/[0.02] border border-white/5 rounded-xl border-l-2 border-l-fuchsia-400/50 p-4">
              {#if Array.isArray(orderData?.items) && orderData.items.length > 0}
                <div class="flex flex-col gap-3">
                  {#each orderData.items as item}
                    <div class="flex items-center justify-between border-b border-white/5 last:border-0 pb-3 last:pb-0">
                      <div class="flex-1">
                        <div class="text-xs text-white font-medium mb-1">{item.name || 'Unknown Item'}</div>
                        <div class="text-[9px] font-mono text-gray-500">QTY: <span class="text-neon-cyan">{item.quantity || 1}</span></div>
                      </div>
                      <div class="text-xs font-mono text-white">
                        {formatCurrency(item.price || 0)}
                      </div>
                    </div>
                  {/each}
                </div>
              {:else}
                <div class="text-xs text-gray-400 font-mono text-center py-4 opacity-50">
                  [ No Items Data Found ]
                </div>
              {/if}
            </div>
          </div>

          <!-- Timeline / Audit History -->
          {#if orderData.history && orderData.history.length > 0}
          <div class="mb-8">
            <div class="flex items-center gap-2 mb-4">
              <Clock size={12} class="text-blue-400" />
              <h3 class="text-[10px] font-mono text-white/80 uppercase tracking-widest font-bold">Audit History</h3>
            </div>
            <div class="bg-white/[0.02] border border-white/5 rounded-xl p-4 space-y-4">
              {#each orderData.history as event, i}
                <div class="flex gap-3 {i !== orderData.history.length - 1 ? 'border-b border-white/5 pb-4' : ''}">
                  <div class="w-1.5 h-1.5 mt-1.5 rounded-full bg-blue-500/50 shadow-[0_0_8px_rgba(59,130,246,0.5)]"></div>
                  <div class="flex-1">
                    <div class="flex justify-between items-start mb-1">
                      <span class="text-xs font-bold text-white uppercase tracking-wider">{event.status}</span>
                      <span class="text-[9px] font-mono text-gray-500">{formatDate(event.timestamp)}</span>
                    </div>
                    <div class="text-[10px] text-gray-400 mb-1">By: {event.actor}</div>
                    {#if event.note}
                      <div class="text-[10px] text-gray-500 italic">Note: {event.note}</div>
                    {/if}
                  </div>
                </div>
              {/each}
            </div>
          </div>
          {/if}

          <!-- Financial Summary -->
          <div>
            <div class="flex items-center gap-2 mb-4">
              <CreditCard size={12} class="text-green-400" />
              <h3 class="text-[10px] font-mono text-white/80 uppercase tracking-widest font-bold">Financial Summary</h3>
            </div>
            <div class="bg-white/[0.02] border border-white/5 rounded-xl p-4">
              <div class="flex items-center justify-between border-b border-white/5 pb-3 mb-3">
                <span class="text-xs text-gray-400">Subtotal</span>
                <span class="text-xs font-mono text-white">{formatCurrency(orderData.total)}</span>
              </div>
              <div class="flex items-center justify-between pb-3 mb-3 border-b border-white/5">
                <span class="text-xs text-gray-400">Tax & Fees</span>
                <span class="text-xs font-mono text-white">0đ</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm font-bold text-white">Net Total</span>
                <span class="text-lg font-bold text-green-400 font-mono tracking-wider">{formatCurrency(orderData.total)}</span>
              </div>
            </div>
          </div>

        {:else}
          <div class="text-center text-gray-500 mt-20 font-mono text-sm">Failed to decrypt data.</div>
        {/if}
      </div>

      <!-- Action Bar (Sticky Bottom) -->
      {#if orderData && !isLoading}
        <div class="p-4 sm:p-6 border-t border-white/10 bg-[#050505] shrink-0">
          <div class="flex flex-col sm:flex-row sm:items-center gap-3">
            {#if orderData.status === 'pending' || orderData.status === 'paid'}
              <button onclick={handleCancel} class="w-full sm:w-auto px-4 py-2.5 rounded-lg border border-red-500/30 text-red-400 hover:bg-red-500/10 text-[10px] font-mono uppercase tracking-widest transition-all text-center flex items-center justify-center gap-2">
                <ShieldAlert size={14} /> Huỷ đơn
              </button>
            {/if}
            
            <div class="flex-1 flex flex-col sm:flex-row justify-end gap-3 w-full sm:w-auto">
              {#if orderData.status === 'pending'}
                <button onclick={() => handleAction('PAID')} class="w-full sm:w-auto justify-center px-6 py-2.5 rounded-lg bg-green-600 hover:bg-green-500 text-white text-[10px] font-mono uppercase tracking-widest transition-all shadow-[0_0_15px_rgba(22,163,74,0.3)] hover:shadow-[0_0_20px_rgba(22,163,74,0.5)] flex items-center gap-2">
                  <CheckCircle size={14} /> Đã thanh toán
                </button>
              {:else if orderData.status === 'paid'}
                <button onclick={() => handleAction('PROCESSING')} class="w-full sm:w-auto justify-center px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-mono uppercase tracking-widest transition-all shadow-[0_0_15px_rgba(37,99,235,0.3)] hover:shadow-[0_0_20px_rgba(37,99,235,0.5)] flex items-center gap-2">
                  <Play size={14} /> Chuẩn bị hàng
                </button>
              {:else if orderData.status === 'processing'}
                <button onclick={() => handleAction('SHIPPED')} class="w-full sm:w-auto justify-center px-6 py-2.5 rounded-lg bg-fuchsia-600 hover:bg-fuchsia-500 text-white text-[10px] font-mono uppercase tracking-widest transition-all shadow-[0_0_15px_rgba(192,38,211,0.3)] hover:shadow-[0_0_20px_rgba(192,38,211,0.5)] flex items-center gap-2">
                  <Truck size={14} /> Giao hàng
                </button>
              {:else if orderData.status === 'shipped'}
                <button onclick={() => handleAction('DELIVERED')} class="w-full sm:w-auto justify-center px-6 py-2.5 rounded-lg bg-green-600 hover:bg-green-500 text-white text-[10px] font-mono uppercase tracking-widest transition-all shadow-[0_0_15px_rgba(22,163,74,0.3)] hover:shadow-[0_0_20px_rgba(22,163,74,0.5)] flex items-center gap-2">
                  <CheckCircle size={14} /> Đã nhận hàng
                </button>
              {:else if orderData.status === 'delivered'}
                <button onclick={() => handleAction('COMPLETED')} class="w-full sm:w-auto justify-center px-6 py-2.5 rounded-lg bg-neon-cyan/20 border border-neon-cyan/50 text-neon-cyan hover:bg-neon-cyan hover:text-black text-[10px] font-mono uppercase tracking-widest transition-all shadow-[0_0_15px_rgba(0,255,255,0.2)] flex items-center gap-2">
                  <CheckCircle size={14} /> Hoàn thành
                </button>
              {/if}
            </div>
          </div>
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 4px; }
  .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 4px; }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(0, 255, 255, 0.3); }
</style>
