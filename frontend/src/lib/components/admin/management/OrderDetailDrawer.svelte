<script lang="ts">
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
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { portal } from "$lib/actions/portal";
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
    } catch (err) {
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

  function formatCurrency(n: number): string {
    return new Intl.NumberFormat("vi-VN").format(n) + "đ";
  }

  function formatDate(iso: string): string {
    return new Intl.DateTimeFormat("vi-VN", {
      year: "numeric", month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit"
    }).format(new Date(iso));
  }
</script>

{#if isOpen}
  <div use:portal class="relative z-[9999]">
    <!-- Backdrop -->
    <div 
      class="fixed inset-0 bg-black/95 md:bg-black/90 md:backdrop-blur-sm z-[200]"
      transition:fade={{ duration: 200 }}
      onclick={onClose}
      aria-label="Close drawer"
      role="button"
      tabindex="0"
      onkeydown={(e) => e.key === 'Escape' && onClose()}
    ></div>

    <!-- Drawer Panel -->
    <div 
      class="fixed top-0 right-0 h-full w-[500px] max-w-full bg-[#050505] border-l border-white/10 z-[210] shadow-[-30px_0_50px_rgba(0,0,0,0.8)] flex flex-col overflow-hidden"
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

          <!-- Customer Info -->
          <div class="mb-8">
            <div class="flex items-center gap-2 mb-4">
              <User size={12} class="text-neon-cyan" />
              <h3 class="text-[10px] font-mono text-white/80 uppercase tracking-widest font-bold">Customer Profile</h3>
            </div>
            <div class="bg-white/[0.02] border border-white/5 rounded-xl p-4 flex flex-col gap-3">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <span class="block text-[9px] font-mono text-gray-500 mb-1">Name</span>
                  <span class="text-xs text-white font-medium">{orderData.customerName}</span>
                </div>
                <div>
                  <span class="block text-[9px] font-mono text-gray-500 mb-1">Timestamp</span>
                  <span class="text-xs text-white font-mono">{formatDate(orderData.createdAt)}</span>
                </div>
              </div>
            </div>
          </div>

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
