<script lang="ts">
  import { apiClient } from '$lib/utils/apiClient';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { fade, fly, scale } from 'svelte/transition';
  import { untrack } from 'svelte';
  import { formatCurrency, formatDate } from '$lib/utils/format';
  import Package from "@lucide/svelte/icons/package";
  import Truck from "@lucide/svelte/icons/truck";
  import CheckCircle from "@lucide/svelte/icons/check-circle";
  import XCircle from "@lucide/svelte/icons/x-circle";
  import Clock from "@lucide/svelte/icons/clock";
  import ShoppingBag from "@lucide/svelte/icons/shopping-bag";
  import Search from "@lucide/svelte/icons/search";
  import MessageSquare from "@lucide/svelte/icons/message-square";
  import FileText from "@lucide/svelte/icons/file-text";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Gift from "@lucide/svelte/icons/gift";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import AlertCircle from "@lucide/svelte/icons/alert-circle";
  import LayoutGrid from "@lucide/svelte/icons/layout-grid";
  import X from "@lucide/svelte/icons/x";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import type { Order, OrderStatus } from '$lib/types/commerce/order';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import type { Product } from '$lib/types';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { authStore } from '$lib/state/authStore.svelte';

  const ui = getClientUi();
  const cartStore = getCartStore();

  let activeTab = $state('all');
  let orders = $state<Order[]>([]);
  let isLoading = $state(true);
  let isReordering = $state(false);
  let searchQuery = $state('');

  // Infinite Scroll State
  let offset = $state(0);
  let isLoadingMore = $state(false);
  let hasMore = $state(true);
  const LIMIT = 3;

  const tabs = [
    { id: 'all', label: 'Tất cả', icon: LayoutGrid },
    { id: 'pending', label: 'Tiếp nhận', icon: FileText },
    { id: 'packed', label: 'Bảo mật', icon: ShieldCheck },
    { id: 'shipping', label: 'Vận chuyển', icon: Truck },
    { id: 'delivered', label: 'Thành công', icon: Gift },
    { id: 'cancelled', label: 'Đã hủy', icon: XCircle }
  ];

  async function fetchOrders(isLoadMore = false, tab = activeTab) {
    if (!authStore.isAuthenticated) {
      isLoading = false;
      orders = [];
      return;
    }

    if (isLoadMore) {
      isLoadingMore = true;
    } else {
      isLoading = true;
      offset = 0;
      hasMore = true;
      orders = [];
    }

    try {
      const params: Record<string, unknown> = { limit: LIMIT, offset };
      if (tab && tab !== 'all') {
        params.status = tab;
      }
      
      const res = await apiClient.get<{ data: Order[] }>('/api/v1/client/user/orders', { params });
      const fetched = res.data || [];
      
      if (isLoadMore) {
        orders = [...orders, ...fetched];
      } else {
        orders = fetched;
      }

      if (fetched.length < LIMIT) {
        hasMore = false;
      }
    } catch (e: unknown) {
      console.error('Fetch orders failed', e);
      if (!isLoadMore) ui.showToast('Không thể tải lịch sử đơn hàng.', 'error');
    } finally {
      isLoading = false;
      isLoadingMore = false;
    }
  }

  function handleScroll() {
    if (typeof window === 'undefined') return;
    
    // Cross-browser resilient scrolling metrics for Safari/Mobile
    const scrollTop = window.scrollY || document.documentElement.scrollTop || document.body.scrollTop || 0;
    const scrollHeight = document.documentElement.scrollHeight || document.body.scrollHeight || 0;
    const clientHeight = window.innerHeight || document.documentElement.clientHeight || 0;

    // Check if we are near the bottom of the page (within 800px for early triggering)
    if (scrollTop + clientHeight >= scrollHeight - 800) {
      if (!isLoading && !isLoadingMore && hasMore && orders.length > 0) {
        offset += LIMIT;
        fetchOrders(true, activeTab);
      }
    }
  }

  function getStatusStyle(status: OrderStatus | string) {
    switch (status) {
      case 'PENDING': return { color: 'text-[#fe2c55]', icon: Clock, label: 'Chờ xác nhận', bg: 'bg-[#fe2c55]/5' };
      case 'PACKED': return { color: 'text-blue-500', icon: Package, label: 'Đang xử lý', bg: 'bg-blue-500/5' };
      case 'SHIPPING': return { color: 'text-indigo-500', icon: Truck, label: 'Đang giao hàng', bg: 'bg-indigo-500/5' };
      case 'DELIVERED': return { color: 'text-[#00b5ad]', icon: CheckCircle, label: 'Hoàn thành', bg: 'bg-[#00b5ad]/5' };
      case 'CANCELLED': return { color: 'text-stone-400', icon: XCircle, label: 'Đã hủy', bg: 'bg-stone-100' };
      default: return { color: 'text-stone-500', icon: Package, label: status, bg: 'bg-stone-50' };
    }
  }

  $effect(() => {
    const currentTab = activeTab; // Track activeTab
    untrack(() => {
      fetchOrders(false, currentTab); // Run untracked
    });
  });

  async function handleReorder(order: Order) {
    if (isReordering || !order.items?.length) return;
    
    isReordering = true;
    let addedCount = 0;
    
    ui.showToast('🚀 Đang chuẩn bị giỏ hàng của Bạn...', 'info');
    
    try {
      for (const item of order.items) {
        const productId = item.id;
        if (!productId) continue;

        try {
          const product = await apiClient.get<Product>(`/api/v1/client/products/${productId}`);
          const variant = product.variants?.find(v => v.id === item.variant_id);
          const qty = Number(item.qty || item.quantity || 1);
          cartStore.addItem(product, variant, qty);
          addedCount++;
        } catch (itemErr: unknown) {
          console.warn(`Product ${productId} likely no longer exists or is inactive.`, itemErr);
        }
      }
      
      if (addedCount > 0) {
        if (addedCount < order.items.length) {
          ui.showToast(`✨ Đã thêm ${addedCount}/${order.items.length} món. Một số món không còn khả dụng.`, 'info');
        } else {
          ui.showToast('✨ Giỏ hàng đã sẵn sàng!', 'success');
        }
        window.location.href = '/checkout';
      } else {
        ui.showToast('⚠️ Rất tiếc, các sản phẩm trong đơn này hiện không còn khả dụng.', 'error');
      }
    } catch (err: unknown) {
      console.error('Reorder process failed', err);
      ui.showToast('Có lỗi xảy ra khi chuẩn bị giỏ hàng.', 'error');
    } finally {
      isReordering = false;
    }
  }

  async function handleCancelOrder(orderId: string) {
    const isConfirmed = await ui.openConfirm({
      title: 'Xác nhận hủy đơn hàng',
      message: 'Bạn có chắc chắn muốn hủy đơn hàng này không? 😢',
      confirmLabel: 'ĐỒNG Ý HỦY',
      cancelLabel: 'Quay lại'
    });
    
    if (!isConfirmed) return;
    
    try {
      await apiClient.post(`/api/v1/client/user/orders/${orderId}/cancel`, {
          reason: "Khách hàng tự hủy qua trang Đơn Mua"
      });
      ui.showToast('✅ Đã hủy đơn hàng thành công.', 'success');
      fetchOrders();
    } catch (err: unknown) {
      console.error('Cancel order failed', err);
      ui.showToast(err.response?.data?.detail || 'Không thể hủy đơn hàng. Vui lòng liên hệ shop.', 'error');
    }
  }

  function getOrderSavings(order: Order) {
    const meta = order.order_metadata || {};
    const voucher = Number(meta.voucher_discount || 0);
    const combo = Number(meta.combo_discount || 0);
    return voucher + combo;
  }

  function getVariantName(item: { variant_name?: string; name?: string; variant_id?: string }) {
    let name = item.variant_name;
    
    // 🔥 Chiến dịch làm sạch (Sanitize) rác mã hoá từ phiên bản cũ 🔥
    if (name) {
      name = name.replace(/\[\s*\]\s*-\s*/g, ''); // Xóa "[] - "
      name = name.replace(/\[|\]|'|"/g, ''); // Xóa ngoặc vuông và dấu nháy
      name = name.trim();
      
      // Nếu sau khi bóc tách, thẻ phân loại lại trùng hoàn toàn với tên sản phẩm 
      // (Chứng tỏ bản thân nó là sản phẩm đơn - Mặc định) -> Ẩn luôn!
      if (name.toLowerCase() === (item.name || '').toLowerCase()) {
         return '';
      }
      if (name) return name;
    }

    if (!item.variant_id) return '';
    const split = item.variant_id.split('_');
    const suffix = split.pop() || '';
    // Xóa các ID hex 12 ký tự rác tạo bởi UUID (Vd: ea1b5d6f82ea)
    if (/^[0-9a-f]{12}$/i.test(suffix)) {
      return '';
    }
    return suffix;
  }

  // Status Tracker Steps Definition
  const trackerSteps = [
    { id: 'PENDING', label: 'Tiếp nhận', icon: FileText },
    { id: 'PACKED', label: 'Bảo mật', icon: ShieldCheck },
    { id: 'SHIPPING', label: 'Vận chuyển', icon: Truck },
    { id: 'DELIVERED', label: 'Thành công', icon: Gift }
  ];

  function getActiveStepIndex(status: string) {
    const idx = trackerSteps.findIndex(s => s.id === status);
    return idx === -1 ? 0 : idx;
  }
  // Filter orders by search query
  const filteredOrders = $derived(

    orders.filter(o => {
      const idMatch = o.id?.toLowerCase().includes(searchQuery.toLowerCase());
      const itemMatch = o.items?.some(item => 
        item.name?.toLowerCase().includes(searchQuery.toLowerCase())
      );
      return idMatch || itemMatch;
    })
  );
</script>


<svelte:window onscroll={handleScroll} />

<div class="space-y-0" in:fade>
  <!-- 🛰️ Integrated Icon-Tabs Command Center -->
  <div 
    class="bg-white/95 backdrop-blur-3xl sticky z-[40] border-b border-stone-100 transition-all duration-300"
    style={ui.isMobile ? `top: calc(52px + env(safe-area-inset-top));` : 'top: 0;'}
  >
    <!-- Icon Navigation Rack (Ultra-Compact Horizontal Scroller) -->
    <div class="relative pt-4 pb-3 overflow-x-auto no-scrollbar scroll-smooth bg-white/40 backdrop-blur-3xl border-b border-stone-100/30">
      <div class="flex items-center justify-start px-5 gap-6 relative z-10">
        {#each tabs as tab}
          {@const isActive = activeTab === tab.id}
          <button
            onclick={() => activeTab = tab.id}
            class="group relative flex flex-col items-center gap-2 transition-all duration-700 outline-none shrink-0"
          >
            <!-- 🪐 Compact Icon Portal -->
            <div class="relative h-10 w-10 md:h-11 md:w-11 flex items-center justify-center transition-all duration-1000
              {isActive ? 'scale-105' : 'scale-90 opacity-20 grayscale hover:opacity-100 hover:grayscale-0'}">
              
              <!-- Active Halo (Subtle) -->
              {#if isActive}
                <div 
                  class="absolute inset-0 bg-luxury-copper/5 rounded-full animate-pulse"
                  in:fade
                ></div>
              {/if}

              <div class="relative z-10 w-full h-full rounded-full border flex items-center justify-center transition-all duration-700
                {isActive 
                  ? 'border-luxury-copper/50 bg-white text-luxury-copper shadow-[0_10px_25px_-10px_rgba(193,143,126,0.3)]' 
                  : 'border-stone-50 bg-stone-50/20 text-stone-400'}">
                  
                  <div class="transition-transform duration-700 {isActive ? 'scale-105' : 'group-hover:rotate-6'}">
                     <tab.icon size={isActive ? 16 : 14} strokeWidth={isActive ? 2.5 : 1.5} />
                  </div>
              </div>
            </div>
            
            <!-- 🏷️ Label (Nano Typography) -->
            <div class="relative flex flex-col items-center">
              <span class="text-[7px] md:text-[8px] font-black tracking-[0.2em] transition-all duration-700
                {isActive ? 'text-stone-800' : 'text-stone-300'}">
                {tab.label}
              </span>
              
              {#if isActive}
                <div 
                  class="mt-1 w-1 h-1 bg-luxury-copper rounded-full"
                  in:fade
                ></div>
              {/if}
            </div>
          </button>
        {/each}
      </div>
    </div>

    <!-- Nano-Search Rack -->
    <div class="relative group h-11 bg-white">
      <div class="absolute left-4 top-1/2 -translate-y-1/2 z-10 pointer-events-none">
         <Search class="w-3.5 h-3.5 text-stone-300 group-focus-within:text-luxury-copper transition-colors" />
      </div>
      <input
        type="text"
        bind:value={searchQuery}
        placeholder="Tìm kiếm nhanh đơn hàng..."
        class="w-full h-full pl-10 pr-4 bg-transparent outline-none text-[12px] text-stone-800 transition-all placeholder:text-stone-300 font-bold"
      />
      <!-- Specular Highlight -->
      <div class="absolute bottom-0 left-0 w-full h-[0.5px] bg-stone-200/40"></div>
    </div>

  </div>

  <!-- 📦 Order Content Stream (Full Width) -->
  <div class="divide-y divide-stone-100 bg-[#fbfbfb]">
    {#if isLoading}
      <div class="py-32 flex flex-col items-center justify-center space-y-5 bg-[#fbfbfb]">
        <div class="w-10 h-10 border-[3px] border-luxury-copper/10 border-t-luxury-copper animate-spin rounded-full"></div>
        <p class="text-[10px] text-stone-400 font-black tracking-[0.4em] animate-pulse">Syncing Records...</p>
      </div>
    {:else if filteredOrders.length === 0}
      <div class="py-32 text-center bg-[#fbfbfb]" in:fade>
        <div class="w-20 h-20 bg-white rounded-full shadow-inner flex items-center justify-center mx-auto mb-8 opacity-40">
          <ShoppingBag class="w-10 h-10 text-stone-200" strokeWidth={1} />
        </div>
        <p class="text-stone-400 text-[13px] font-bold tracking-widest">Lịch sử trống</p>
        {#if !searchQuery && activeTab === 'all'}
          <a href="/" class="inline-block mt-10 px-12 py-4 bg-luxury-copper text-white text-[10px] tracking-[0.3em] font-black rounded-full hover:scale-105 transition-all shadow-2xl shadow-stone-800/20 active:scale-95">
            Mua sắm ngay
          </a>
        {/if}
      </div>
    {:else}
      {#each filteredOrders as order (order.id)}
        {@const status = getStatusStyle(order.status)}
        {@const activeStep = getActiveStepIndex(order.status)}
        
        <div
          class="bg-white overflow-hidden transition-all duration-500 group border-b border-stone-50 {ui.isMobile ? 'pb-10 pt-10' : 'hover:bg-stone-50/30 pt-14 pb-14 px-10'}"
          in:fly={{ y: 0, duration: 600 }}
        >
          <!-- 🔝 Order Meta Header -->
          <div class="px-5 md:px-0 mb-8 flex items-center justify-between">
             <div class="flex items-center gap-4">
               <div class="w-10 h-10 bg-luxury-copper rounded-2xl flex items-center justify-center shadow-xl shadow-luxury-copper/20 group-hover:scale-110 transition-transform">
                  <span class="text-[14px] text-white font-black italic">M</span>
               </div>
               <a href={`/checkout/success/${order.id}${authStore.user?.phone ? `?phone=${authStore.user.phone}` : ''}`} class="flex flex-col">
                 <span class="text-[12px] font-black text-stone-800 tracking-[0.1em]">osmo Official</span>
                 <span class="text-[9px] font-bold text-stone-300 tracking-tighter italic">#{order.id.slice(-8).toUpperCase()}</span>
               </a>
             </div>
             <div class="flex items-center gap-2 px-4 py-2 rounded-full {status.bg} border border-current/5">
                <span class="text-[9px] font-black {status.color} tracking-[0.2em]">{status.label}</span>
             </div>
          </div>

          <!-- 🛰️ Status Tracker (Progress Bar) -->
          {#if order.status !== 'CANCELLED'}
            <div class="px-5 md:px-0 mb-10">
              <div class="relative flex justify-between">
                <!-- Progress Line Background -->
                <div class="absolute top-4 left-4 right-4 h-[2px] bg-stone-100 z-0"></div>
                <!-- Progress Line Active -->
                <div 
                  class="absolute top-4 left-4 h-[2px] bg-luxury-copper z-0 transition-all duration-1000"
                  style="width: calc((100% - 2rem) * {activeStep / (trackerSteps.length - 1)})"
                ></div>

                {#each trackerSteps as step, idx}
                  <div class="relative z-10 flex flex-col items-center gap-3">
                    <div class="w-8 h-8 rounded-full border-2 flex items-center justify-center bg-white transition-all duration-700
                      {idx <= activeStep ? 'border-luxury-copper text-luxury-copper scale-110 shadow-lg shadow-luxury-copper/20' : 'border-stone-100 text-stone-200'}">
                      <step.icon size={14} strokeWidth={idx <= activeStep ? 2.5 : 1.5} />
                    </div>
                    <span class="text-[7px] md:text-[8px] font-black tracking-widest
                      {idx <= activeStep ? 'text-stone-800' : 'text-stone-300'}">
                      {step.label}
                    </span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}

          <!-- 👕 Order Items Stream (Full Width Scan) -->
          <div class="space-y-px bg-stone-50/30 rounded-2xl overflow-hidden border border-stone-100/50">
            {#if order.items && Array.isArray(order.items)}
              {#each order.items as item}
                {@const itemImage = item.image || item.image_url}
                <div class="flex gap-5 items-center bg-white px-5 py-6 group/item transition-all hover:bg-stone-50/50">
                  <div class="w-20 h-20 bg-stone-50 border border-stone-100 shrink-0 p-1.5 rounded-xl overflow-hidden relative shadow-sm transition-all group-hover/item:shadow-xl group-hover/item:-translate-y-1">
                    {#if itemImage}
                      <img src={resolveMediaUrl(itemImage)} alt={item.name} class="w-full h-full object-cover rounded-lg group-hover/item:scale-110 transition-transform duration-700" />
                    {:else}
                      <div class="w-full h-full flex items-center justify-center text-stone-200">
                         <ShoppingBag class="w-8 h-8" strokeWidth={1} />
                      </div>
                    {/if}
                    <div class="absolute bottom-2 right-2 bg-luxury-copper/95 text-white text-[9px] px-2 py-0.5 rounded-lg font-black backdrop-blur-md shadow-lg border border-white/10">x{item.qty || item.quantity}</div>
                  </div>
                  <div class="flex-1 min-w-0">
                    <h3 class="text-[13px] md:text-[16px] font-serif italic text-stone-800 leading-snug mb-2 line-clamp-2">{item.name}</h3>
                    {#if getVariantName(item)}
                      <span class="text-[8px] font-black text-stone-400 tracking-widest bg-stone-50/80 px-2 py-1 rounded-md border border-stone-100">{getVariantName(item)}</span>
                    {/if}
                  </div>
                  <div class="text-right shrink-0">
                     <span class="text-[12px] md:text-[15px] font-black text-stone-500 tabular-nums italic tracking-tighter">{formatCurrency(item.unit_price || (item as unknown as { price: number }).price || 0)}</span>
                  </div>
                </div>
              {/each}
            {/if}
          </div>

          <!-- 💎 Final Calculation Surface (Dramatic Lean) -->
          <div class="px-5 md:px-0 mt-8 flex flex-col items-end gap-6">
            <div class="w-full flex items-center justify-between border-t border-stone-50 pt-6">
               {#if getOrderSavings(order) > 0}
                  <div class="flex items-center gap-2 text-luxury-copper bg-luxury-copper/5 px-3 py-1.5 rounded-lg border border-luxury-copper/10 animate-bounce">
                    <Sparkles size={10} />
                    <span class="text-[9px] font-black tracking-widest">Tiết kiệm {formatCurrency(getOrderSavings(order))}</span>
                  </div>
               {:else}
                  <div></div>
               {/if}

               <div class="flex flex-col items-end gap-1">
                  <span class="text-[9px] text-stone-300 font-black tracking-[0.3em] italic">Total Amount</span>
                  <span class="text-3xl md:text-5xl font-bold text-stone-700 tracking-tighter tabular-nums">
                    {formatCurrency(order.total || order.total_amount || 0).replace('₫', '')}<span class="text-[0.5em] align-top md:mt-2 inline-block opacity-60">₫</span>
                  </span>
               </div>
            </div>


            <!-- Agentic Actions (Elite Tactical Viral - Ultra Lean) -->
            <div class="grid grid-cols-3 gap-3 w-full mt-2">

              {#if order.status === 'PENDING' || order.status === 'PACKED'}
                 <button
                    onclick={() => handleCancelOrder(order.id)}
                    class="h-11 bg-white border border-stone-100 rounded-2xl text-[9px] font-black text-red-500/60 hover:text-red-600 hover:bg-red-50/50 transition-all tracking-[0.2em] flex items-center justify-center gap-2 group/btn"
                  >
                    <X size={12} strokeWidth={3} class="group-hover/btn:rotate-90 transition-transform" />
                    HỦY ĐƠN
                  </button>
              {/if}

              <a
                href="/checkout/success/{order.id}{authStore.user?.phone ? '?phone=' + authStore.user.phone : ''}"
                class="col-span-{ (order.status === 'PENDING' || order.status === 'PACKED') ? '1' : '2' } h-11 flex items-center justify-center bg-stone-50/80 backdrop-blur-md border border-stone-100/50 rounded-2xl text-[9px] font-black text-stone-500 hover:bg-white hover:text-stone-800 hover:shadow-lg transition-all tracking-[0.2em] active:scale-95 gap-2"
              >
                XEM CHI TIẾT
                <ChevronRight size={12} />
              </a>

              <button
                onclick={() => handleReorder(order)}
                disabled={isReordering}
                class="h-11 bg-luxury-copper text-white text-[10px] font-black tracking-[0.3em] rounded-2xl hover:shadow-2xl hover:shadow-luxury-copper/40 transition-all active:scale-95 disabled:opacity-50 overflow-hidden relative flex items-center justify-center gap-2 group/reorder"
              >
                 <div class="w-1.5 h-1.5 bg-luxury-copper rounded-full animate-pulse group-hover/reorder:scale-150 transition-transform"></div>
                 MUA LẠI
              </button>
            </div>


          </div>
        </div>
      {/each}


      {#if orders.length > 0}
        <div class="h-20 w-full flex items-center justify-center pt-4 pb-8">
          {#if isLoadingMore}
            <div class="flex items-center gap-2 text-[#fe2c55]/80">
              <div class="w-5 h-5 border-2 border-[#fe2c55]/30 border-t-[#fe2c55] animate-spin rounded-full"></div>
              <span class="text-[12px] font-bold tracking-wider">Đang tải thêm...</span>
            </div>
          {:else if !hasMore}
            <div class="flex items-center gap-2 text-stone-300">
              <div class="w-8 h-px bg-stone-200"></div>
              <Sparkles size={14} />
              <span class="text-[11px] font-medium tracking-widest ">Bạn đã xem hết đơn hàng</span>
              <div class="w-8 h-px bg-stone-200"></div>
            </div>
          {/if}
        </div>
      {/if}
    {/if}
  </div>

  <!-- 🔱 Cinematic Branding -->
  <div class="pt-20 text-center pb-12">
      <div class="mt-32 pb-20 flex flex-col items-center gap-4 opacity-30">
        <div class="flex items-center gap-6">
           <div class="h-[0.5px] w-24 bg-luxury-copper/30"></div>
           <span class="text-[11px] font-serif italic tracking-[0.6em] text-luxury-copper/20">VIRAL 2026</span>
           <div class="h-[0.5px] w-24 bg-luxury-copper/30"></div>
        </div>
        <p class="text-[8px] font-black tracking-[0.4em] text-stone-400">osmo Member Exclusive</p>
      </div>
  </div>
</div>

<style>
  .no-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .no-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
  @keyframes shimmer {
    100% {
      transform: translateX(100%);
    }
  }
</style>
