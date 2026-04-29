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
  import XCircle from "lucide-svelte/icons/x-circle";
  import ShieldCheck from "lucide-svelte/icons/shield-check";
  import PackageCheck from "lucide-svelte/icons/package-check";
  import ShieldAlert from "lucide-svelte/icons/shield-alert";
  import Phone from "lucide-svelte/icons/phone";
  import MapPin from "lucide-svelte/icons/map-pin";
  import TrendingUp from "lucide-svelte/icons/trending-up";
  import Target from "lucide-svelte/icons/target";
  import ChevronDown from "lucide-svelte/icons/chevron-down";
  import HistoryIcon from "lucide-svelte/icons/history";
  import MessageSquareIcon from "lucide-svelte/icons/message-square";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import Gift from "lucide-svelte/icons/gift";
  import Coins from "lucide-svelte/icons/coins";
  import StatusDropdown from "./StatusDropdown.svelte";
  import StatusStepper from "./StatusStepper.svelte";
  import { ORDER_STATUS_MAP, ORDER_TRANSITIONS } from "$lib/constants/order";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { portal } from "$lib/core/actions/portal";
  import { formatCurrency, formatDate } from "$lib/utils/format";
  import type { OrderDetail, User as UserType } from "$lib/types";
  import { SHOP_CONFIG } from "$lib/constants/shop";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";

  const nanobot = useNanobot();

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
  let isSavingPlanning = $state(false);
  let staffList = $state<UserType[]>([]);

  // Planning form state
  let planningForm = $state({
    assigned_to: "",
    scheduled_at: "",
    priority: "NORMAL",
    planning_notes: ""
  });

  $effect(() => {
    if (isOpen && orderId) {
      loadOrderDetails();
      loadStaff();
    }
  });

  async function loadStaff() {
    try {
      const res = await apiClient.get<{ data: UserType[] }>("/api/v1/users?limit=100");
      staffList = res.data.filter(u => u.status === "ACTIVE");
    } catch (err) {
      console.error("Failed to load staff", err);
    }
  }

  async function loadOrderDetails() {
    isLoading = true;
    try {
      orderData = await apiClient.get<OrderDetail>(`/api/v1/orders/${orderId}`);
      if (orderData?.planning) {
        planningForm = {
          assigned_to: orderData.planning.assigned_to || "",
          scheduled_at: orderData.planning.scheduled_at?.split('.')[0].slice(0, 16) || "",
          priority: orderData.planning.priority || "NORMAL",
          planning_notes: orderData.planning.planning_notes || ""
        };
      }
    } catch (err: unknown) {
      console.error("Failed to load order details", err);
    } finally {
      isLoading = false;
    }
  }

  async function savePlanning() {
    isSavingPlanning = true;
    try {
      await apiClient.patch(`/api/v1/orders/${orderId}/planning`, {
        assigned_to: planningForm.assigned_to,
        scheduled_at: planningForm.scheduled_at ? new Date(planningForm.scheduled_at).toISOString() : null,
        priority: planningForm.priority,
        planning_notes: planningForm.planning_notes
      });
      nanobot.showToast("Cập nhật kế hoạch thành công", "success");
      await loadOrderDetails();
      onReload?.();
    } catch (err: unknown) {
      const e = err as Error;
      nanobot.showToast(e.message || "Lỗi cập nhật kế hoạch", "error");
    } finally {
      isSavingPlanning = false;
    }
  }

  async function handleAction(actionType: string) {
    const statusType = actionType.toUpperCase();
    const label = ORDER_STATUS_MAP[statusType.toLowerCase()]?.label || actionType;

    const confirm = await nanobot.showConfirm({
      title: "XÁC NHẬN CHUYỂN TRẠNG THÁI",
      message: `Đổi trạng thái đơn hàng sang "${label.toUpperCase()}"?\nHành động này sẽ được lưu vào lịch sử hệ thống.`,
      confirmLabel: "XÁC NHẬN",
      cancelLabel: "QUAY LẠI"
    });

    if (confirm) {
      isLoading = true;
      try {
        await apiClient.patch(`/api/v1/orders/${orderId}/status`, { status: statusType });
        nanobot.addLog("Cập nhật trạng thái " + statusType, "Nanobot-System");
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

  function openZalo() {
    if (!orderData?.customerPhone) return;
    const phone = orderData.customerPhone.replace(/\D/g, '');
    const shopName = SHOP_CONFIG.pharmacy.name;
    const orderIdShort = orderId.split('-')[0].toUpperCase();
    const total = formatCurrency(orderData.total);

    const message = `Chào bạn ${orderData.finalCustomerName}, ${shopName} xác nhận đơn hàng #${orderIdShort} của bạn. Tổng thanh toán: ${total}. Shop sẽ sớm giao hàng cho bạn nhé!`;
    const encodedMsg = encodeURIComponent(message);
    window.open(`https://zalo.me/${phone}?text=${encodedMsg}`, '_blank');
  }
</script>

{#if isOpen}
  <div use:portal class="relative" style="z-index: {Z_INDEX_ADMIN.MODAL};">
    <!-- Backdrop -->
    <div
      class="fixed inset-0 bg-black/95 md:bg-black/90 md:backdrop-blur-sm"
      style="z-index: {Z_INDEX_ADMIN.OVERLAY};"
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
      style="z-index: {Z_INDEX_ADMIN.MODAL + 10};"
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
          
          <!-- V4 Status LifeCycle Stepper (Micsmo-Elite Integrated) -->
          <div class="mb-10" in:fly={{ y: -20, duration: 600 }}>
            <StatusStepper 
              currentStatus={orderData.status} 
              onStatusChange={(newStatus) => handleAction(newStatus)}
            />
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
                     {#if orderData.customerPhone}
                        {@const isZalo = orderData.order_metadata?.zalo_status === 'ACTIVE' || orderData.orderMetadata?.zalo_status === 'ACTIVE'}
                        <button
                          onclick={openZalo}
                          class="flex items-center gap-1 px-1.5 py-0.5 rounded border {isZalo ? 'bg-blue-500/20 border-blue-400 text-blue-400' : 'bg-gray-500/10 border-white/10 text-gray-500'} hover:scale-105 transition-transform"
                          title={isZalo ? "Phát hiện có Zalo - Bấm để nhắn tin" : "Chưa xác định Zalo - Bấm để thử nhắn"}
                        >
                          <span class="text-[8px] font-black tracking-tighter uppercase">ZALO</span>
                          <MessageSquareIcon size={10} />
                        </button>
                     {/if}
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

          <!-- Elite V2.2: Customer Directive (Rich Notes) -->
          {#if (orderData.order_metadata?.customer_note || orderData.orderMetadata?.customer_note || orderData.order_metadata?.note || orderData.orderMetadata?.note)}
            <div class="mb-8 p-1 border border-cyan-500/10 rounded-2xl bg-cyan-500/[0.01]" in:fly={{ y: 20, duration: 600, delay: 100 }}>
              <div class="flex items-center gap-2 mb-4 px-3 pt-3">
                <MessageSquareIcon size={12} class="text-cyan-400" />
                <h3 class="text-[10px] font-mono text-white/80 uppercase tracking-widest font-bold">Customer Directive</h3>
              </div>
              <div class="bg-black/40 border border-white/5 rounded-xl p-4">
                <div class="text-[11px] text-gray-300 leading-relaxed italic prose-invert prose-sm max-w-none">
                  {@html orderData.order_metadata?.customer_note || orderData.orderMetadata?.customer_note || orderData.order_metadata?.note || orderData.orderMetadata?.note}
                </div>
              </div>
            </div>
          {/if}

          <!-- Historical Purchase Timeline (Phase 4) -->
          {#if orderData.insight?.previous_orders && orderData.insight.previous_orders.length > 0}
            <div class="mb-8 p-1 border border-neon-cyan/10 rounded-2xl bg-neon-cyan/[0.01]">
              <div class="flex items-center gap-2 mb-4 px-3 pt-3">
                <HistoryIcon size={12} class="text-neon-cyan" />
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
                          {prev.status === 'DELIVERED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}">
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

          <!-- Logistics & Planning (Elite V2.2) -->
          <div class="mb-8 p-1 border border-orange-500/10 rounded-2xl bg-orange-500/[0.01]">
            <div class="flex items-center justify-between mb-4 px-3 pt-3">
              <div class="flex items-center gap-2">
                <Truck size={12} class="text-orange-400" />
                <h3 class="text-[10px] font-mono text-white/80 uppercase tracking-widest font-bold">Logistics & Planning</h3>
              </div>
              <span class="text-[7px] font-mono text-orange-500/50 uppercase tracking-widest animate-pulse">Live Tracking Enabled</span>
            </div>

            <div class="bg-black/40 border border-white/5 rounded-xl p-5 space-y-5">
              <!-- Grid Layout for Inputs -->
              <div class="grid grid-cols-2 gap-4">
                <!-- Assigned To -->
                <div class="col-span-2 sm:col-span-1">
                  <label for="assigned" class="flex items-center gap-2 text-[8px] font-mono text-gray-500 uppercase mb-1.5 focus-within:text-orange-400 transition-colors">
                    <User size={10} /> Responsible Personnel
                  </label>
                  <select 
                    id="assigned"
                    bind:value={planningForm.assigned_to}
                    class="w-full bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-orange-500/50 transition-all font-mono"
                  >
                    <option value="" class="bg-[#111]">-- UNASSIGNED --</option>
                    {#each staffList as staff}
                      <option value={staff.name} class="bg-[#111]">{staff.name}</option>
                    {/each}
                  </select>
                </div>

                <!-- Priority -->
                <div class="col-span-2 sm:col-span-1">
                  <label for="priority" class="flex items-center gap-2 text-[8px] font-mono text-gray-500 uppercase mb-1.5 focus-within:text-orange-400 transition-colors">
                    <TrendingUp size={10} /> Priority Scale
                  </label>
                  <select 
                    id="priority"
                    bind:value={planningForm.priority}
                    class="w-full bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2 text-xs focus:outline-none transition-all font-mono
                      {planningForm.priority === 'URGENT' ? 'text-rose-400 border-rose-500/30' : 
                       planningForm.priority === 'HIGH' ? 'text-orange-400 border-orange-500/30' : 
                       'text-white'}"
                  >
                    <option value="LOW" class="bg-[#111] text-gray-400">LOW</option>
                    <option value="NORMAL" class="bg-[#111] text-white">NORMAL</option>
                    <option value="HIGH" class="bg-[#111] text-orange-400">HIGH</option>
                    <option value="URGENT" class="bg-[#111] text-rose-400">URGENT</option>
                  </select>
                </div>

                <!-- Scheduled At -->
                <div class="col-span-2">
                  <label for="scheduled" class="flex items-center gap-2 text-[8px] font-mono text-gray-500 uppercase mb-1.5 focus-within:text-orange-400 transition-colors">
                    <Calendar size={10} /> Deployment Schedule
                  </label>
                  <input 
                    type="datetime-local"
                    id="scheduled"
                    bind:value={planningForm.scheduled_at}
                    class="w-full bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-orange-500/50 transition-all font-mono"
                  />
                </div>

                <!-- Planning Notes -->
                <div class="col-span-2">
                  <label for="notes" class="flex items-center gap-2 text-[8px] font-mono text-gray-500 uppercase mb-1.5 focus-within:text-orange-400 transition-colors">
                    <MessageSquareIcon size={10} /> Logistics Intelligence Notes
                  </label>
                  <textarea 
                    id="notes"
                    bind:value={planningForm.planning_notes}
                    rows="3"
                    placeholder="Enter strategic notes for deployment team..."
                    class="w-full bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-orange-500/50 transition-all font-mono resize-none placeholder:text-gray-700"
                  ></textarea>
                </div>
              </div>

              <!-- Save Action -->
              <button 
                onclick={savePlanning}
                disabled={isSavingPlanning}
                class="w-full py-2.5 rounded-lg bg-orange-500/10 hover:bg-orange-500 border border-orange-500/30 text-orange-400 hover:text-black text-[10px] font-mono uppercase tracking-[0.2em] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {#if isSavingPlanning}
                  <div class="w-3 h-3 border-2 border-black/20 border-t-black rounded-full animate-spin"></div>
                  Syncing Tactics...
                {:else}
                  <Target size={14} /> Update Logistics Plan
                {/if}
              </button>
            </div>
          </div>

          <!-- Elite V2.2: Gift Intelligence -->
          {#if (orderData.order_metadata?.gift_info || orderData.orderMetadata?.gift_info)}
            {@const gift = orderData.order_metadata?.gift_info || orderData.orderMetadata?.gift_info}
            <div class="mb-8 p-1 border border-pink-500/10 rounded-2xl bg-pink-500/[0.01]" in:fly={{ y: 20, duration: 600, delay: 200 }}>
              <div class="flex items-center gap-2 mb-4 px-3 pt-3">
                <Gift size={12} class="text-pink-400" />
                <h3 class="text-[10px] font-mono text-white/80 uppercase tracking-widest font-bold">Gift Intelligence</h3>
              </div>
              <div class="bg-black/40 border border-white/5 rounded-xl p-5 space-y-4">
                <div class="flex items-center justify-between border-b border-white/5 pb-4">
                  <div>
                    <span class="block text-[8px] font-mono text-gray-500 uppercase mb-1">Sender Trace</span>
                    <span class="text-sm font-bold text-pink-400">{gift.sender_name}</span>
                  </div>
                  <div class="text-right">
                     <span class="block text-[8px] font-mono text-gray-500 uppercase mb-1">Contact</span>
                     <span class="text-[10px] font-mono text-gray-400">{gift.sender_phone}</span>
                  </div>
                </div>
                
                <div class="grid grid-cols-2 gap-4 pt-2">
                   <div>
                      <span class="block text-[8px] font-mono text-gray-500 uppercase mb-1">Packaging Manifest</span>
                      <span class="text-[9px] bg-pink-500/10 text-pink-400 px-1.5 py-0.5 rounded border border-pink-500/20 uppercase font-black tracking-tighter">
                        {gift.packaging || 'ELITE LUXURY'}
                      </span>
                   </div>
                   {#if gift.scheduled_at}
                     <div class="text-right">
                        <span class="block text-[8px] font-mono text-gray-500 uppercase mb-1">Delivery Priority</span>
                        <span class="text-[9px] text-cyan-400 font-mono italic">{formatDate(gift.scheduled_at)}</span>
                     </div>
                   {/if}
                </div>

                <div class="pt-4 border-t border-white/5 relative">
                  <div class="absolute -top-2 left-3 bg-black px-2 text-[7px] text-gray-600 uppercase font-black">Encoded Content</div>
                  <div class="p-3 bg-white/[0.02] border border-white/5 rounded-lg">
                    <p class="text-[11px] text-gray-300 italic leading-relaxed">"{gift.message || 'No custom message provided.'}"</p>
                  </div>
                </div>
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

          <!-- Elite V2.2: Augmented Request Manifest (Custom Items Awaiting Quote) -->
          {#if (orderData.order_metadata?.custom_requests || orderData.orderMetadata?.custom_requests || orderData.order_metadata?.custom_items || orderData.orderMetadata?.custom_items) && (orderData.order_metadata?.custom_requests || orderData.orderMetadata?.custom_requests || orderData.order_metadata?.custom_items || orderData.orderMetadata?.custom_items).length > 0}
            <div class="mb-8 p-1 border border-amber-500/10 rounded-2xl bg-amber-500/[0.01]" in:fly={{ y: 20, duration: 600, delay: 300 }}>
              <div class="flex items-center gap-2 mb-4 px-3 pt-3">
                <Sparkles size={12} class="text-amber-400" />
                <h3 class="text-[10px] font-mono text-white/80 uppercase tracking-widest font-bold">Augmented Request Manifest</h3>
              </div>
              <div class="bg-black/40 border border-white/5 rounded-xl border-l-2 border-l-amber-500/50 p-4 space-y-3">
                {#each (orderData.order_metadata?.custom_requests || orderData.orderMetadata?.custom_requests || orderData.order_metadata?.custom_items || orderData.orderMetadata?.custom_items) as c_item}
                  <div class="flex items-center gap-4 group hover:bg-white/[0.02] p-2 rounded-lg transition-all border border-transparent hover:border-white/5">
                    <div class="w-14 h-14 bg-white/5 border border-white/10 rounded flex items-center justify-center overflow-hidden shrink-0 shadow-lg">
                      {#if c_item.image || c_item.image_url}
                        <img src={c_item.image || c_item.image_url} alt={c_item.name} class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
                      {:else}
                        <span class="text-2xl animate-pulse">🧪</span>
                      {/if}
                    </div>
                    <div class="flex-1 min-w-0">
                      <div class="text-[11px] font-bold text-white uppercase truncate tracking-tight">{c_item.name}</div>
                      <div class="flex items-center gap-2 mt-1">
                        <span class="text-[8px] font-mono text-gray-500 uppercase">QTY: <span class="text-white">{c_item.qty || c_item.quantity || 1}</span></span>
                        <div class="w-1 h-1 rounded-full bg-white/10"></div>
                        <span class="text-[8px] font-black text-amber-500 uppercase tracking-widest animate-pulse">Status: Awaiting Quote</span>
                      </div>
                    </div>
                  </div>
                {/each}
              </div>
              <div class="mt-2 text-center">
                 <p class="text-[7px] text-gray-600 font-mono uppercase tracking-[0.3em]">Requires manual price adjustment in v2.3</p>
              </div>
            </div>
          {/if}

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
                <span class="text-xs font-mono text-white">đ0</span>
              </div>

              {#if orderData.points_earned > 0 || orderData.points_redeemed > 0}
              <div class="flex flex-col gap-2 pb-3 mb-3 border-b border-white/5 bg-amber-500/[0.03] p-2 rounded-lg">
                <div class="flex items-center gap-1.5 mb-1">
                  <Coins size={12} class="text-amber-400" />
                  <span class="text-[9px] font-mono text-amber-400/80 uppercase tracking-widest font-bold">Loyalty Rewards</span>
                </div>
                {#if orderData.points_earned > 0}
                <div class="flex items-center justify-between">
                  <span class="text-[10px] text-gray-400">Points Earned</span>
                  <span class="text-[10px] font-mono text-amber-400">+{orderData.points_earned} PTS</span>
                </div>
                {/if}
                {#if orderData.points_redeemed > 0}
                <div class="flex items-center justify-between">
                  <span class="text-[10px] text-gray-400">Points Redeemed</span>
                  <span class="text-[10px] font-mono text-red-400">-{orderData.points_redeemed} PTS</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-[10px] text-gray-400">Point Discount</span>
                  <span class="text-[10px] font-mono text-red-400">-{formatCurrency(orderData.point_discount_amount)}</span>
                </div>
                {/if}
              </div>
              {/if}
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
            {#if orderData.status === 'pending' || orderData.status === 'packed'}
              <button onclick={handleCancel} class="w-full sm:w-auto px-4 py-2.5 rounded-lg border border-red-500/30 text-red-400 hover:bg-red-500/10 text-[10px] font-mono uppercase tracking-widest transition-all text-center flex items-center justify-center gap-2">
                <XCircle size={14} /> Huỷ đơn
              </button>
            {/if}
            
            <div class="flex-1 flex flex-col sm:flex-row justify-end gap-3 w-full sm:w-auto">
              <div class="w-px h-8 bg-white/10 hidden sm:block mx-1"></div>

              {#if orderData.status === 'pending'}
                <button onclick={() => handleAction('PACKED')} class="w-full sm:w-auto justify-center px-6 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-[10px] font-mono uppercase tracking-widest transition-all shadow-[0_0_15px_rgba(6,182,212,0.3)] hover:shadow-[0_0_20px_rgba(6,182,212,0.5)] flex items-center gap-2">
                  <ShieldCheck size={14} /> Xác nhận & Đóng gói
                </button>
              {:else if orderData.status === 'packed'}
                <button onclick={() => handleAction('SHIPPING')} class="w-full sm:w-auto justify-center px-6 py-2.5 rounded-lg bg-lime-600 hover:bg-lime-500 text-white text-[10px] font-mono uppercase tracking-widest transition-all shadow-[0_0_15px_rgba(132,204,22,0.3)] hover:shadow-[0_0_20px_rgba(132,204,22,0.5)] flex items-center gap-2">
                  <Truck size={14} /> Bàn giao vận tải
                </button>
              {:else if orderData.status === 'shipping'}
                <button onclick={() => handleAction('DELIVERED')} class="w-full sm:w-auto justify-center px-6 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-mono uppercase tracking-widest transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)] hover:shadow-[0_0_20px_rgba(16,185,129,0.5)] flex items-center gap-2">
                  <PackageCheck size={14} /> Giao hàng thành công
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
