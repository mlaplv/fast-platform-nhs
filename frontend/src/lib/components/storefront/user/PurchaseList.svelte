<script lang="ts">
  import { apiClient } from '$lib/utils/apiClient';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { fade, fly } from 'svelte/transition';
  import { untrack } from 'svelte';
  import { formatCurrency, formatDate } from '$lib/utils/format';
  import { Package, Truck, CheckCircle, XCircle, Clock, ShoppingBag, Search, MessageSquare } from 'lucide-svelte';
  import type { Order, OrderStatus } from '$lib/types/commerce/order';

  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import type { Product } from '$lib/types';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { Sparkles, AlertCircle } from 'lucide-svelte';

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
    { id: 'all', label: 'Tất cả' },
    { id: 'pending', label: 'Chờ xác nhận' },
    { id: 'packed', label: 'Luồng vận chuyển' },
    { id: 'shipping', label: 'Đang giao' },
    { id: 'delivered', label: 'Hoàn thành' },
    { id: 'cancelled', label: 'Đã hủy' }
  ];

  async function fetchOrders(isLoadMore = false, tab = activeTab) {
    if (isLoadMore) {
      isLoadingMore = true;
    } else {
      isLoading = true;
      offset = 0;
      hasMore = true;
      orders = [];
    }

    try {
      const params: any = { limit: LIMIT, offset };
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
    
    ui.showToast('🚀 Đang chuẩn bị giỏ hàng của Sếp...', 'info');
    
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
        } catch (itemErr: any) {
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
    } catch (err: any) {
      console.error('Reorder process failed', err);
      ui.showToast('Có lỗi xảy ra khi chuẩn bị giỏ hàng.', 'error');
    } finally {
      isReordering = false;
    }
  }

  async function handleCancelOrder(orderId: string) {
    const isConfirmed = await ui.openConfirm({
      title: 'Xác nhận hủy đơn hàng',
      message: 'Sếp có chắc chắn muốn hủy đơn hàng này không? 😢',
      confirmLabel: 'ĐỒNG Ý HỦY',
      cancelLabel: 'QUAY LẠI'
    });
    
    if (!isConfirmed) return;
    
    try {
      await apiClient.post(`/api/v1/client/user/orders/${orderId}/cancel`, {
          reason: "Khách hàng tự hủy qua trang Đơn Mua"
      });
      ui.showToast('✅ Đã hủy đơn hàng thành công.', 'success');
      fetchOrders();
    } catch (err: any) {
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

  function getVariantName(item: any) {
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

<div class="space-y-6" in:fade>
  <!-- Navigation Tabs: Shopee Style -->
  <div class="bg-white sticky top-0 z-[40] border-b border-stone-100 -mx-4 md:mx-0 px-4 md:px-0">
    <div class="flex gap-4 md:gap-0 overflow-x-auto no-scrollbar scroll-smooth">
      {#each tabs as tab}
        <button
          onclick={() => activeTab = tab.id}
          class="flex-1 min-w-fit md:min-w-0 pt-4 pb-4 text-[13px] md:text-[14px] font-medium whitespace-nowrap transition-all relative px-4 text-center {activeTab === tab.id ? 'text-[#fe2c55]' : 'text-stone-500 hover:text-stone-800'}"
        >
          {tab.label}
          {#if activeTab === tab.id}
            <div 
               class="absolute bottom-0 left-0 w-full h-[2.5px] bg-[#fe2c55]" 
               in:fade={{ duration: 200 }}
            ></div>
          {/if}
        </button>
      {/each}
    </div>
  </div>

  <!-- Search / Filter: TikTok Minimal -->
  <div class="relative group mt-4">
    <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-300 group-focus-within:text-[#fe2c55] transition-colors" />
    <input
      type="text"
      bind:value={searchQuery}
      placeholder="Tìm kiếm theo Mã đơn hàng hoặc Tên sản phẩm..."
      class="w-full h-11 pl-11 pr-4 bg-stone-100/50 border border-transparent focus:border-[#fe2c55]/20 focus:bg-white outline-none text-[13px] text-stone-800 transition-all rounded-xl placeholder:text-stone-400"
    />
  </div>

  <!-- Order List -->
  <div class="space-y-4 md:space-y-6">
    {#if isLoading}
      <div class="py-20 flex flex-col items-center justify-center space-y-4">
        <div class="w-8 h-8 border-[3px] border-[#fe2c55]/20 border-t-[#fe2c55] animate-spin rounded-full"></div>
        <p class="text-[11px] text-stone-400 font-bold uppercase tracking-[0.2em] animate-pulse">Synchronizing Data...</p>
      </div>
    {:else if filteredOrders.length === 0}
      <div class="py-24 text-center bg-white border border-stone-100 rounded-3xl" in:fade>
        <div class="w-24 h-24 bg-stone-50 rounded-full flex items-center justify-center mx-auto mb-6">
          <ShoppingBag class="w-12 h-12 text-stone-200" />
        </div>
        <p class="text-stone-400 text-sm font-medium">Chưa có đơn hàng nào trong mục này.</p>
        {#if !searchQuery && activeTab === 'all'}
          <a href="/" class="inline-block mt-8 px-10 py-3.5 bg-[#fe2c55] text-white text-[12px] uppercase tracking-widest font-black rounded-full hover:scale-105 transition-all shadow-xl shadow-[#fe2c55]/20">
            Khám phá ngay
          </a>
        {/if}
      </div>
    {:else}
      {#each filteredOrders as order (order.id)}
        {@const status = getStatusStyle(order.status)}
        <div
          class="bg-white/80 backdrop-blur-xl md:border md:border-stone-100 overflow-hidden md:rounded-[32px] transition-all duration-500 group {ui.isMobile ? 'rounded-[32px] mx-2 mb-6 shadow-[0_10px_30px_rgba(0,0,0,0.03)] border border-stone-100' : 'hover:shadow-[0_40px_100px_rgba(0,0,0,0.1)] hover:-translate-y-1 mb-10 shadow-sm'}"
          in:fly={{ y: 20, duration: 400 }}
        >
          <!-- 📦 Order Header: Shopee Style -->
          {#if !ui.isMobile}
            <div class="px-6 py-4 border-b border-stone-50 flex items-center justify-between bg-white relative">
              <div class="flex items-center gap-4">
                <span class="flex items-center gap-2 text-[12px] font-bold text-stone-800">
                  <span class="px-2 py-0.5 bg-black text-white text-[9px] font-black rounded">ELITE</span>
                  Micsmo Official Store
                </span>
                <button class="bg-stone-100 hover:bg-stone-200 px-3 py-1 rounded text-[11px] font-bold transition-all flex items-center gap-1.5">
                   <MessageSquare size={12} /> Chat
                </button>
                <div class="w-px h-4 bg-stone-100 mx-1"></div>
                <button class="text-stone-500 hover:text-stone-800 text-[11px] font-medium transition-all">Xem Shop</button>
              </div>
              <div class="flex items-center gap-2 {status.color}">
                <span class="text-[12px] font-bold uppercase tracking-wider">{status.label}</span>
              </div>
            </div>
          {:else}
            <!-- 📱 Mobile Header: Viral Elite Style -->
            <div class="px-6 py-4 flex items-center justify-between border-b border-stone-50">
               <div class="flex items-center gap-2">
                 <div class="w-6 h-6 bg-stone-900 rounded-lg flex items-center justify-center shadow-lg shadow-stone-900/20">
                    <span class="text-[9px] text-white font-black italic">M</span>
                 </div>
                 <span class="text-[12px] font-black text-stone-800 uppercase tracking-widest">Micsmo Official</span>
               </div>
               <span class="text-[9px] font-black {status.color} uppercase tracking-[2px] px-3 py-1.5 rounded-full {status.bg} border border-current/10">{status.label}</span>
            </div>
          {/if}

          <!-- 🛍️ Order Items: High Density -->
          <div class="{ui.isMobile ? 'px-6 py-6' : 'p-8'} space-y-5">
            {#if order.items && Array.isArray(order.items)}
              {#each order.items as item}
                {@const itemImage = item.image || item.image_url}
                <div class="flex gap-4 items-start md:items-center">
                  <div class="w-24 h-24 bg-stone-50 border border-stone-100 shrink-0 p-1 rounded-2xl overflow-hidden relative shadow-sm transition-all group-hover:scale-[1.02]">
                    {#if itemImage}
                      <img src={resolveMediaUrl(itemImage)} alt={item.name} class="w-full h-full object-cover rounded-xl" />
                    {:else}
                      <div class="w-full h-full flex items-center justify-center text-stone-200">
                         <ShoppingBag class="w-10 h-10" strokeWidth={1} />
                      </div>
                    {/if}
                    <div class="absolute bottom-1 right-1 bg-stone-900/90 text-white text-[9px] px-2 py-0.5 rounded-lg font-black backdrop-blur-md">x{item.qty || item.quantity}</div>
                  </div>
                  <div class="flex-1 min-w-0 py-1">
                    <h3 class="text-[14px] font-serif italic text-stone-800 leading-snug mb-1.5 group-hover:text-luxury-copper transition-colors line-clamp-2">{item.name}</h3>
                    {#if getVariantName(item)}
                      <div class="flex items-center gap-2">
                        <span class="px-2 py-0.5 bg-stone-50 text-stone-400 text-[9px] font-black uppercase tracking-widest rounded-md border border-stone-100">{getVariantName(item)}</span>
                      </div>
                    {/if}
                  </div>
                  <div class="text-right flex flex-col justify-center">
                     <span class="text-[15px] font-black text-stone-800 tabular-nums italic tracking-tighter">{formatCurrency(item.unit_price || (item as any).price || 0)}</span>
                  </div>
                </div>
              {/each}
            {/if}
          </div>

          <!-- 💰 Order Footer: Viral 2026 Style -->
          <div class="{ui.isMobile ? 'px-4 py-5' : 'px-8 py-6'} border-t border-white/20 bg-gradient-to-br from-stone-50/10 to-stone-100/5 backdrop-blur-sm flex flex-col items-end gap-6">
            
            <div class="w-full flex flex-col gap-2.5 items-end">
              {#if getOrderSavings(order) > 0}
                <div class="flex items-center gap-2 text-[#ee4d2d] bg-[#ee4d2d]/5 px-3 py-1.5 rounded-2xl border border-[#ee4d2d]/10">
                  <Sparkles size={14} class="animate-pulse" />
                  <span class="text-[12px] font-black italic tracking-tight">SIÊU ƯU ĐÃI: -{formatCurrency(getOrderSavings(order))}</span>
                </div>
              {/if}
              
              <div class="flex items-end gap-3 translate-y-1">
                <span class="text-[11px] text-stone-400 font-bold uppercase tracking-[0.1em] italic">Thành tiền</span>
                <span class="text-3xl font-black text-[#fe2c55] tracking-tighter tabular-nums drop-shadow-sm">{formatCurrency(order.total || order.total_amount || 0)}</span>
              </div>
            </div>

            <div class="flex items-center gap-3 w-full md:w-auto">
              {#if order.status === 'PENDING' || order.status === 'PACKED'}
                 <button
                    onclick={() => handleCancelOrder(order.id)}
                    class="flex-1 md:flex-none h-11 px-6 border border-stone-100 rounded-full text-[10px] font-black text-stone-400 hover:text-red-500 hover:border-red-200 hover:bg-red-50 transition-all flex items-center justify-center gap-2 uppercase tracking-widest"
                  >
                    Hủy Đơn
                  </button>
              {/if}

              <a
                href="/checkout/success/{order.id}"
                class="flex-1 md:flex-none h-11 flex items-center justify-center px-8 border border-stone-100 rounded-full text-[10px] font-black text-stone-800 hover:bg-stone-50 transition-all uppercase tracking-widest whitespace-nowrap"
              >
                Chi tiết
              </a>

              <button
                onclick={() => handleReorder(order)}
                disabled={isReordering}
                class="flex-1 md:flex-none h-11 min-w-[130px] px-8 bg-stone-900 text-white text-[10px] font-black uppercase tracking-[0.2em] rounded-full hover:bg-luxury-copper transition-all shadow-[0_15px_30px_rgba(0,0,0,0.1)] active:scale-95 disabled:opacity-50 disabled:grayscale disabled:cursor-not-allowed group overflow-hidden relative"
              >
                <div class="relative z-10 flex items-center justify-center gap-2">
                  {#if isReordering}
                    <div class="w-3.5 h-3.5 border-2 border-white/20 border-t-white animate-spin rounded-full"></div>
                    <span class="animate-pulse">PROCESSING...</span>
                  {:else}
                    MUA LẠI
                  {/if}
                </div>
                <div class="absolute inset-0 bg-white/10 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000 skew-x-[-20deg]"></div>
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
              <span class="text-[12px] font-bold uppercase tracking-wider">Đang tải thêm...</span>
            </div>
          {:else if !hasMore}
            <div class="flex items-center gap-2 text-stone-300">
              <div class="w-8 h-px bg-stone-200"></div>
              <Sparkles size={14} />
              <span class="text-[11px] font-medium tracking-widest uppercase">Bạn đã xem hết đơn hàng</span>
              <div class="w-8 h-px bg-stone-200"></div>
            </div>
          {/if}
        </div>
      {/if}
    {/if}
  </div>

  <!-- 🔱 Cinematic Branding -->
  <div class="pt-20 text-center pb-12">
     <div class="flex items-center justify-center gap-5 mb-3 opacity-10">
        <div class="h-[0.5px] w-24 bg-stone-800"></div>
        <span class="text-[11px] font-serif italic uppercase tracking-[0.6em] text-stone-800">VIRAL 2026</span>
        <div class="h-[0.5px] w-24 bg-stone-800"></div>
     </div>
     <p class="text-[9px] text-stone-300 font-black uppercase tracking-[0.4em] opacity-40">Elite Transaction Shield • AES-256</p>
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
</style>
