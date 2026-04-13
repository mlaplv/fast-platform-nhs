<script lang="ts">
  import UserLayout from '$lib/components/storefront/user/UserLayout.svelte';
  import { apiClient } from '$lib/utils/apiClient';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { fade, fly } from 'svelte/transition';
  import { onMount } from 'svelte';
  import { formatCurrency, formatDate } from '$lib/utils/format';
  import { Package, Truck, CheckCircle, XCircle, Clock, ShoppingBag, ChevronRight, Search } from 'lucide-svelte';

  const ui = getClientUi();

  let activeTab = $state('all');
  let orders = $state<any[]>([]);
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
      const res = await apiClient.get<any>('/api/v1/client/user/orders', {
        params: {
          status: activeTab === 'all' ? undefined : activeTab,
          limit: 50
        }
      });
      orders = res.data;
    } catch (e) {
      ui.showToast('Không thể tải lịch sử đơn hàng.', 'error');
    } finally {
      isLoading = false;
    }
  }

  function getStatusStyle(status: string) {
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

  function handleReorder(order: any) {
    ui.showToast('Tính năng mua lại đang được xử lý, Sếp chờ em chút nhé! ✨', 'info');
  }
</script>

<UserLayout>
  <div class="space-y-8" in:fade>
    <!-- Header -->
    <div class="border-b border-stone-100 pb-5">
      <h1 class="text-xl font-serif italic text-stone-800 tracking-wide">Đơn Mua</h1>
      <p class="text-[13px] text-stone-400 mt-1 uppercase tracking-widest">Danh sách giao dịch</p>
    </div>

    <!-- Navigation Tabs -->
    <div class="flex border-b border-stone-100 gap-6 md:gap-10 overflow-x-auto no-scrollbar">
      {#each tabs as tab}
        <button
          onclick={() => activeTab = tab.id}
          class="pb-4 text-[12px] uppercase tracking-widest font-bold whitespace-nowrap transition-all relative {activeTab === tab.id ? 'text-stone-800' : 'text-stone-400 hover:text-stone-600'}"
        >
          {tab.label}
          {#if activeTab === tab.id}
            <div class="absolute bottom-0 left-0 w-full h-0.5 bg-luxury-copper" in:fly={{ y: 2 }}></div>
          {/if}
        </button>
      {/each}
    </div>

    <!-- Search / Filter Placeholder -->
    <div class="relative group">
      <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-300 group-focus-within:text-luxury-copper transition-colors" />
      <input
        type="text"
        placeholder="Tìm kiếm theo Mã đơn hàng hoặc Tên sản phẩm..."
        class="w-full h-12 pl-12 pr-4 bg-stone-50 border border-transparent focus:border-stone-200 focus:bg-white outline-none text-[13px] text-stone-800 transition-all rounded-sm placeholder:italic"
      />
    </div>

    <!-- Order List -->
    <div class="space-y-6">
      {#if isLoading}
        <div class="py-20 flex flex-col items-center justify-center space-y-4">
          <div class="w-8 h-8 border-2 border-luxury-copper border-t-transparent animate-spin rounded-full"></div>
          <p class="text-[11px] text-stone-400 uppercase tracking-widest animate-pulse">Đang truy xuất dữ liệu...</p>
        </div>
      {:else if orders.length === 0}
        <div class="py-24 text-center border-2 border-dashed border-stone-50 rounded-lg" in:fade>
          <div class="w-20 h-20 bg-stone-50 rounded-full flex items-center justify-center mx-auto mb-6">
            <ShoppingBag class="w-10 h-10 text-stone-200" />
          </div>
          <p class="text-stone-400 font-serif italic">Bạn chưa có đơn hàng nào trong mục này.</p>
          <a href="/" class="inline-block mt-8 px-10 py-3 bg-stone-900 text-white text-[11px] uppercase tracking-[3px] font-bold hover:bg-luxury-copper transition-all duration-500 shadow-lg">
            Khám phá bộ sưu tập
          </a>
        </div>
      {:else}
        {#each orders as order (order.id)}
          {@const status = getStatusStyle(order.status)}
          <div
            class="bg-white border border-stone-100 overflow-hidden hover:shadow-[0_15px_40px_rgba(0,0,0,0.04)] transition-all duration-700 group"
            in:fly={{ y: 10 }}
          >
            <!-- Order Header -->
            <div class="px-6 py-4 border-b border-stone-50 flex items-center justify-between bg-stone-50/30">
              <div class="flex items-center gap-4">
                <span class="text-[11px] font-black uppercase tracking-widest text-stone-400">Đơn hàng</span>
                <span class="text-[13px] font-bold text-stone-800">#{order.id.slice(-8).toUpperCase()}</span>
                <span class="text-[11px] text-stone-300">|</span>
                <span class="text-[12px] text-stone-500 font-medium italic font-serif">{formatDate(order.created_at)}</span>
              </div>
              <div class="flex items-center gap-2 {status.color}">
                <status.icon class="w-4 h-4" />
                <span class="text-[11px] font-black uppercase tracking-widest">{status.label}</span>
              </div>
            </div>

            <!-- Order Items -->
            <div class="p-6 space-y-6">
              {#if order.items && Array.isArray(order.items)}
                {#each order.items as item}
                  <div class="flex gap-6 items-center">
                    <div class="w-20 h-20 bg-stone-50 border border-stone-100 shrink-0 p-1 rounded-sm overflow-hidden group-hover:scale-105 transition-transform duration-700">
                      {#if item.image}
                        <img src={item.image} alt={item.name} class="w-full h-full object-cover" />
                      {:else}
                        <div class="w-full h-full flex items-center justify-center text-stone-200">
                           <ShoppingBag class="w-6 h-6" />
                        </div>
                      {/if}
                    </div>
                    <div class="flex-1 min-w-0">
                      <h3 class="text-[14px] font-medium text-stone-800 truncate mb-1">{item.name || 'Sản phẩm cao cấp'}</h3>
                      <div class="flex items-center gap-4 text-[12px] text-stone-400 uppercase tracking-widest">
                        <span>Số lượng: {item.quantity || item.qty || 1}</span>
                        {#if item.variant}
                          <span class="w-px h-3 bg-stone-100"></span>
                          <span>Phân loại: {item.variant}</span>
                        {/if}
                      </div>
                    </div>
                    <div class="text-right">
                       <span class="text-[14px] font-bold text-stone-800">{formatCurrency(item.price || item.unit_price || 0)}</span>
                    </div>
                  </div>
                {/each}
              {/if}
            </div>

            <!-- Order Footer -->
            <div class="px-6 py-5 bg-stone-50/30 border-t border-stone-50 flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div class="flex items-center gap-2">
                <span class="text-[12px] text-stone-400 uppercase tracking-widest">Thành tiền:</span>
                <span class="text-xl font-bold text-luxury-copper tabular-nums">{formatCurrency(order.total_amount || order.total || 0)}</span>
              </div>

              <div class="flex items-center gap-4">
                <a
                  href="/checkout/success/{order.id}"
                  class="px-6 py-2 border border-stone-200 text-[11px] font-bold uppercase tracking-widest text-stone-600 hover:border-stone-800 hover:text-stone-800 transition-all"
                >
                  Xem chi tiết
                </a>
                <button
                  onclick={() => handleReorder(order)}
                  class="px-8 py-2 bg-stone-900 text-white text-[11px] font-bold uppercase tracking-widest hover:bg-luxury-copper transition-all duration-500 shadow-md"
                >
                  Mua lại
                </button>
              </div>
            </div>
          </div>
        {/each}
      {/if}
    </div>

    <!-- Aesthetic Branding -->
    <div class="pt-16 text-center opacity-30">
       <div class="flex items-center justify-center gap-4 mb-2">
          <div class="h-[1px] w-20 bg-stone-200"></div>
          <span class="text-[10px] font-serif italic uppercase tracking-[5px] text-stone-800">Micsmo Elite Experience</span>
          <div class="h-[1px] w-20 bg-stone-200"></div>
       </div>
       <p class="text-[9px] text-stone-400 uppercase tracking-[2px]">Bản quyền thuộc về Micsmo.com • 2026</p>
    </div>
  </div>
</UserLayout>

<style>
  .no-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .no-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
</style>
