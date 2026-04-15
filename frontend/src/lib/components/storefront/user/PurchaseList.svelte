<script lang="ts">
  import { apiClient } from '$lib/utils/apiClient';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { fade, fly } from 'svelte/transition';
  import { onMount } from 'svelte';
  import { formatCurrency, formatDate } from '$lib/utils/format';
  import { Package, Truck, CheckCircle, XCircle, Clock, ShoppingBag, Search } from 'lucide-svelte';
  import type { Order, OrderStatus } from '$lib/types/commerce/order';

  const ui = getClientUi();

  let activeTab = $state('all');
  let orders = $state<Order[]>([]);
  let isLoading = $state(true);

  const tabs = [
    { id: 'all', label: 'Tất cả' },
    { id: 'pending', label: 'Chờ xác nhận' },
    { id: 'packed', label: 'Đang xử lý' },
    { id: 'shipping', label: 'Đang giao' },
    { id: 'delivered', label: 'Hoàn thành' },
    { id: 'cancelled', label: 'Đã hủy' }
  ];

  async function fetchOrders() {
    isLoading = true;
    try {
      const res = await apiClient.get<{ data: Order[] }>('/api/v1/client/user/orders', {
        params: {
          status: activeTab === 'all' ? undefined : activeTab,
          limit: 50
        }
      });
      orders = res.data;
    } catch (e: unknown) {
      ui.showToast('Không thể tải lịch sử đơn hàng.', 'error');
    } finally {
      isLoading = false;
    }
  }

  function getStatusStyle(status: OrderStatus | string) {
    switch (status) {
      case 'PENDING': return { color: 'text-amber-500', icon: Clock, label: 'Chờ xác nhận' };
      case 'PACKED': return { color: 'text-blue-500', icon: Package, label: 'Đang đóng gói' };
      case 'SHIPPING': return { color: 'text-indigo-500', icon: Truck, label: 'Đang giao hàng' };
      case 'DELIVERED': return { color: 'text-emerald-500', icon: CheckCircle, label: 'Đã hoàn thành' };
      case 'CANCELLED': return { color: 'text-stone-400', icon: XCircle, label: 'Đã hủy' };
      default: return { color: 'text-stone-500', icon: Package, label: status };
    }
  }

  onMount(() => {
    fetchOrders();
  });

  $effect(() => {
    if (activeTab) {
      fetchOrders();
    }
  });

  function handleReorder(order: Order) {
    ui.showToast('Tính năng mua lại đang được xử lý, vui lòng chờ trong giây lát! ✨', 'info');
  }
</script>

<div class="space-y-6" in:fade>
  <!-- Navigation Tabs -->
  <div class="flex border-b border-stone-100 gap-4 overflow-x-auto no-scrollbar">
    {#each tabs as tab}
      <button
        onclick={() => activeTab = tab.id}
        class="pb-3 text-[11px] uppercase tracking-widest font-bold whitespace-nowrap transition-all relative {activeTab === tab.id ? 'text-stone-800' : 'text-stone-400'}"
      >
        {tab.label}
        {#if activeTab === tab.id}
          <div class="absolute bottom-0 left-0 w-full h-0.5 bg-luxury-copper" in:fly={{ y: 2 }}></div>
        {/if}
      </button>
    {/each}
  </div>

  <!-- Order List -->
  <div class="space-y-4">
    {#if isLoading}
      <div class="py-10 text-center text-stone-400 text-[11px] uppercase tracking-widest animate-pulse">Đang truy xuất...</div>
    {:else if orders.length === 0}
      <div class="py-10 text-center text-stone-400 italic text-sm">Chưa có đơn hàng.</div>
    {:else}
      {#each orders as order (order.id)}
        {@const status = getStatusStyle(order.status)}
        <div class="bg-white p-4 border border-stone-100 rounded-sm">
          <div class="flex justify-between items-center mb-3">
             <span class="text-[10px] font-bold text-stone-500">#{order.id.slice(-8).toUpperCase()}</span>
             <span class="text-[10px] font-black {status.color}">{status.label}</span>
          </div>
          <div class="text-sm font-bold text-stone-800 mb-2">{formatCurrency(order.total_amount || 0)}</div>
          <button onclick={() => ui.closeModal()} class="w-full py-2 border border-stone-200 text-[10px] font-bold uppercase tracking-widest text-stone-600">
             Xem chi tiết
          </button>
        </div>
      {/each}
    {/if}
  </div>
</div>
