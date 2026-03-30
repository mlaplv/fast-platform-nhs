<script lang="ts">
  import { page } from '$app/state';
  import { fade, fly, scale } from 'svelte/transition';
  import { Z_INDEX } from '$lib/core/constants/zIndex.ts';
  import { onMount } from 'svelte';
  import { apiClient } from '$lib/utils/apiClient';
  import { formatCurrency, formatDate } from '$lib/utils/format.ts';
  import SuccessMobile from '$lib/components/mobile/sections/SuccessMobile.svelte';

  let { data } = $props<{ data: { isMobile: boolean } }>();

  const orderId = page.params.id;

  // Elite V2.2: Order Status Roadmap!
  const STATUS_STEPS = [
    { key: 'PENDING', label: 'Chờ duyệt', icon: '⏱' },
    { key: 'PAID', label: 'Đã thanh toán', icon: '💳' },
    { key: 'PROCESSING', label: 'Đang xử lý', icon: '⚙️' },
    { key: 'SHIPPED', label: 'Đang giao', icon: '🚚' },
    { key: 'COMPLETED', label: 'Thành công', icon: '🏆' }
  ];

  function getStepIndex(status: string) {
    const idx = STATUS_STEPS.findIndex(s => s.key === status);
    return idx === -1 ? 0 : idx;
  }

  // Elite V2.2: Retrieve phone from URL or LocalStorage to persist unlock!
  const phoneParam = page.url.searchParams.get('phone') || (typeof localStorage !== 'undefined' ? localStorage.getItem(`order_verify_${orderId}`) : null);
  const isTrackingMode = !!phoneParam;

  let order = $state<any>(null);
  let isLoading = $state(true);
  let isSubmittingAction = $state(false);

  // Security Gate State!
  let isLocked = $state(false);
  let verificationPhone = $state('');
  let authError = $state('');

  // Elite V2.2 Toast System!
  let toasts = $state<{id: number, type: 'success' | 'error', message: string}[]>([]);
  let toastId = 0;

  function showToast(message: string, type: 'success' | 'error' = 'success') {
    const id = toastId++;
    toasts.push({ id, type, message });
    setTimeout(() => {
        const idx = toasts.findIndex(t => t.id === id);
        if (idx !== -1) toasts.splice(idx, 1);
    }, 4000);
  }

  function copyOrderId() {
    if (typeof navigator !== 'undefined') {
        navigator.clipboard.writeText(orderId);
        showToast("Đã sao chép mã đơn hàng");
    }
  }

  // Edit State
  let isEditing = $state(false);
  let editForm = $state({
    name: '',
    phone: '',
    address: ''
  });

  // Confirm Cancel State
  let isConfirmCancelOpen = $state(false);

  onMount(async () => {
    await fetchOrder();
  });

  async function fetchOrder(overridePhone?: string) {
    isLoading = true;
    authError = '';
    const phoneToUse = overridePhone || phoneParam;
    
    try {
      const res = await apiClient.get<any>(`/api/v1/client/orders/${orderId}`, {
        params: phoneToUse ? { phone: phoneToUse } : {}
      });
      if (res) {
        order = res;
        isLocked = false;
        // Persist the unlock!
        if (phoneToUse && typeof localStorage !== 'undefined') {
          localStorage.setItem(`order_verify_${orderId}`, phoneToUse);
        }
        editForm = {
            name: order.customerName || order.customer_name || '',
            phone: order.customerPhone || order.customer_phone || '',
            address: order.customerAddress || order.customer_address || ''
        };
      }
    } catch (e: any) {
      console.error("Failed to load order", e);
      // R2026: If it's a 400 validation error regarding phone, it's a "Lock"!
      if (e.status === 400 && e.message.toLowerCase().includes('số điện thoại')) {
        isLocked = true;
      } else {
        showToast(e.message || "Lỗi tải dữ liệu", "error");
      }
    } finally {
      isLoading = false;
    }
  }

  async function handleVerify() {
    if (!verificationPhone) return;
    await fetchOrder(verificationPhone);
  }

  async function handleCancel() {
    isConfirmCancelOpen = false;
    isSubmittingAction = true;
    try {
        await apiClient.post(`/api/v1/client/orders/${orderId}/cancel`, {}, { params: { phone: phoneParam || verificationPhone } });
        showToast("Đã hủy đơn hàng thành công");
        await fetchOrder();
    } catch (e: any) {
        showToast(e.message || "Không thể hủy đơn hàng", "error");
    } finally {
        isSubmittingAction = false;
    }
  }

  async function handleSaveEdit() {
    isSubmittingAction = true;
    try {
        await apiClient.patch(`/api/v1/client/orders/${orderId}`, {
            customer_name: editForm.name,
            customer_phone: editForm.phone,
            customer_address: editForm.address
        }, { params: { phone: phoneParam || verificationPhone } });
        showToast("Đã cập nhật thông tin thành công");
        isEditing = false;
        await fetchOrder();
    } catch (e: any) {
        showToast(e.message || "Lỗi cập nhật dữ liệu", "error");
    } finally {
        isSubmittingAction = false;
    }
  }
</script>

<svelte:head>
  <title>{isTrackingMode ? 'Tra cứu đơn hàng' : 'Đặt hàng thành công'} | Nhà Thuốc Hồng Sơn</title>
</svelte:head>

{#if data.isMobile && order}
  <SuccessMobile {order} {orderId} isLookup={isTrackingMode} />
{:else}
  <div class="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center p-6 relative overflow-hidden">
    <!-- Rest of existing desktop code... -->
  <!-- Elite Glass Background! -->
  <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-sky-500/10 rounded-full blur-[120px] pointer-events-none"></div>
  
  {#if isLoading}
    <div class="flex flex-col items-center gap-4">
      <div class="w-12 h-12 border-4 border-sky-500/20 border-t-sky-500 rounded-full animate-spin"></div>
      <p class="text-slate-500 font-bold uppercase tracking-widest text-[10px]">Đang tải dữ liệu đơn hàng...</p>
    </div>
  {:else if isLocked}
    <!-- Elite Security Gate (Soft Wall!) -->
    <div 
      in:fly={{ y: 20, duration: 800 }}
      class="w-full max-w-md bg-white/5 border border-white/10 backdrop-blur-3xl rounded-[3rem] p-12 shadow-2xl relative z-10 text-center"
    >
      <div class="w-20 h-20 bg-amber-500/10 text-amber-500 rounded-full flex items-center justify-center mx-auto mb-8 border border-amber-500/20 shadow-[0_0_30px_rgba(245,158,11,0.1)]">
        <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
      </div>
      <h2 class="text-3xl font-black text-white italic tracking-tighter uppercase mb-4 leading-none">Cửa Ngõ Bảo Mật</h2>
      <p class="text-slate-400 text-xs mb-8 uppercase tracking-widest font-bold">Xác minh Số điện thoại để tiếp tục</p>
      
      <div class="space-y-6">
        <input 
          type="tel" 
          bind:value={verificationPhone}
          placeholder="Nhập Số điện thoại..."
          class="w-full px-8 py-4 bg-white/[0.03] border-2 border-white/5 focus:border-amber-500/50 focus:bg-white/[0.05] rounded-full outline-none text-white font-black text-center text-lg placeholder:text-slate-700 transition-all"
          onkeydown={(e) => e.key === 'Enter' && handleVerify()}
        />
        <button 
          onclick={handleVerify}
          class="w-full py-4 bg-amber-500 hover:bg-amber-400 text-slate-950 font-black rounded-full transition-all active:scale-95 shadow-xl shadow-amber-500/20 uppercase text-sm tracking-tighter italic"
        >
          XÁC THỰC QUYỀN TRUY CẬP →
        </button>
      </div>
      
      <p class="mt-8 text-[9px] text-slate-600 font-bold uppercase tracking-widest italic">An toàn • Bảo mật • Riêng tư</p>
    </div>
  {:else}
    <div 
      in:fly={{ y: 30, duration: 800 }}
      class="w-full max-w-2xl bg-white/5 border border-white/10 backdrop-blur-2xl rounded-[3rem] p-8 md:p-12 shadow-2xl relative z-10"
    >
      <!-- Status Icon! -->
      {#if isTrackingMode}
        <div class="w-24 h-24 bg-sky-500/10 text-sky-400 rounded-full flex items-center justify-center mx-auto mb-10 border border-sky-500/30 relative group">
          <div class="absolute inset-0 bg-sky-400/20 rounded-full blur-2xl animate-pulse group-hover:blur-3xl transition-all duration-700"></div>
          <svg class="w-12 h-12 relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
        </div>
      {:else}
        <div class="w-24 h-24 bg-emerald-500/10 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-10 border border-emerald-500/30 relative group">
          <div class="absolute inset-0 bg-emerald-400/20 rounded-full blur-2xl animate-pulse group-hover:blur-3xl transition-all duration-700"></div>
          <svg class="w-12 h-12 relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
        </div>
      {/if}

      <div class="text-center mb-12">
        <h1 class="text-4xl md:text-5xl font-black tracking-tight mb-4 uppercase">
          {isTrackingMode ? 'TRẠNG THÁI ĐƠN HÀNG' : 'ĐẶT HÀNG THÀNH CÔNG!'}
        </h1>
        <div class="flex items-center justify-center gap-2 group cursor-pointer mb-6" onclick={copyOrderId}>
          <p class="text-slate-400 text-lg leading-relaxed">
            Đơn hàng <span class="text-white font-bold tracking-widest">#{orderId.slice(-6).toUpperCase()}</span>
          </p>
          <svg class="w-4 h-4 text-slate-600 group-hover:text-sky-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" /></svg>
        </div>

        {#if order?.status !== 'CANCELLED'}
          <!-- Elite Status Timeline! -->
          <div class="max-w-md mx-auto mb-12 px-4 relative">
             <div class="absolute top-1/2 left-0 w-full h-0.5 bg-white/5 -translate-y-1/2 rounded-full overflow-hidden">
                <div
                    class="h-full bg-gradient-to-r from-sky-500 to-emerald-500 transition-all duration-1000 ease-out shadow-[0_0_15px_rgba(14,165,233,0.5)]"
                    style="width: {(getStepIndex(order?.status) / (STATUS_STEPS.length - 1)) * 100}%"
                ></div>
             </div>
             <div class="flex justify-between relative z-10">
                {#each STATUS_STEPS as step, i}
                   {@const isActive = getStepIndex(order?.status) >= i}
                   <div class="flex flex-col items-center gap-3">
                      <div
                        class="w-10 h-10 rounded-full flex items-center justify-center text-xs transition-all duration-500 border-2
                        {isActive ? 'bg-slate-900 border-sky-500 text-sky-400 scale-110 shadow-[0_0_15px_rgba(14,165,233,0.3)]' : 'bg-slate-950 border-white/10 text-slate-600'}"
                      >
                         {step.icon}
                      </div>
                      <span class="text-[8px] font-black uppercase tracking-tighter {isActive ? 'text-white' : 'text-slate-700'}">
                        {step.label}
                      </span>
                   </div>
                {/each}
             </div>
          </div>
        {/if}

        {#if !isTrackingMode}
          <p class="text-slate-500 text-sm italic mt-2">
            Hệ thống đã tự động tạo tài khoản cho Quý khách bằng số điện thoại <span class="text-sky-400 font-bold">{order?.customerPhone || ''}</span> để tiện theo dõi đơn hàng.
          </p>
        {/if}
      </div>

      <!-- Order Details Summary! -->
      <div class="grid md:grid-cols-2 gap-6 p-6 bg-white/5 border border-white/10 rounded-[2rem] mb-8 relative group">
        {#if !isEditing}
          <div class="space-y-4" in:fade>
            <div class="flex flex-col">
              <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest">Người nhận:</span>
              <span class="text-lg font-bold uppercase">{order?.customerName || order?.customer_name || 'Khách hàng'}</span>
            </div>
            <div class="flex flex-col">
              <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest">Địa chỉ:</span>
              <span class="text-xs text-slate-300 leading-snug uppercase">{order?.customerAddress || order?.customer_address || 'Địa chỉ bảo mật'}</span>
            </div>
            <div class="flex flex-col">
              <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest">Số điện thoại:</span>
              <span class="text-sm text-sky-400 font-bold">{order?.customerPhone || order?.customer_phone || '---'}</span>
            </div>
          </div>
        {:else}
          <div class="space-y-4" in:fly={{ y: 10 }}>
            <div class="space-y-1">
              <span class="text-[8px] font-black text-sky-500 uppercase tracking-widest ml-2">Họ tên:</span>
              <input 
                type="text" 
                bind:value={editForm.name}
                class="w-full px-4 py-2 bg-white/[0.03] border border-white/10 rounded-xl outline-none text-white font-bold text-sm uppercase focus:border-sky-500/50"
              />
            </div>
            <div class="space-y-1">
              <span class="text-[8px] font-black text-sky-500 uppercase tracking-widest ml-2">Số điện thoại:</span>
              <input 
                type="tel" 
                bind:value={editForm.phone}
                class="w-full px-4 py-2 bg-white/[0.03] border border-white/10 rounded-xl outline-none text-white font-bold text-sm focus:border-sky-500/50"
              />
            </div>
            <div class="space-y-1">
              <span class="text-[8px] font-black text-sky-500 uppercase tracking-widest ml-2">Địa chỉ:</span>
              <textarea 
                bind:value={editForm.address}
                rows="2"
                class="w-full px-4 py-2 bg-white/[0.03] border border-white/10 rounded-xl outline-none text-white font-bold text-xs uppercase focus:border-sky-500/50 resize-none"
              ></textarea>
            </div>
          </div>
        {/if}

        <div class="space-y-4 border-t md:border-t-0 md:border-l border-white/10 pt-4 md:pt-0 md:pl-6 text-right flex flex-col justify-between">
          <div class="flex flex-col">
            <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest">Tổng thanh toán:</span>
            <span class="text-3xl font-black text-sky-400 tabular-nums">{formatCurrency(order?.total || order?.total_amount || 0)}</span>
          </div>
          <div class="flex flex-col">
            <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest">Trạng thái:</span>
            <span class="text-xs font-bold uppercase {order?.status === 'CANCELLED' ? 'text-red-500' : 'text-amber-500'}">
                {order?.status === 'CANCELLED' ? 'Đã hủy ❌' : (STATUS_STEPS.find(s => s.key === order?.status)?.label || 'Đang xử lý') + ' ⏱'}
            </span>
          </div>
          {#if !isEditing && (order?.insight?.total_orders || order?.successfulOrdersCount)}
            <div class="flex flex-col pt-2 border-t border-white/5 mt-2" in:fade>
              <span class="text-[8px] font-black text-emerald-500 uppercase tracking-widest italic">THÀNH VIÊN ELITE V2.2:</span>
              <span class="text-[10px] font-bold text-white uppercase italic tracking-tighter">Hệ thống ghi nhận {order?.insight?.total_orders || order?.successfulOrdersCount} đơn hàng thành công 🌟</span>
            </div>
          {/if}
          {#if isEditing}
            <div class="flex gap-2 justify-end mt-4" in:scale>
              <button 
                onclick={() => isEditing = false}
                class="px-4 py-2 bg-white/5 text-slate-400 font-black rounded-lg text-[10px] uppercase hover:bg-white/10 transition-all"
              >
                Hủy
              </button>
              <button 
                onclick={handleSaveEdit}
                disabled={isSubmittingAction}
                class="px-4 py-2 bg-sky-500 text-white font-black rounded-lg text-[10px] uppercase hover:bg-sky-400 transition-all shadow-lg shadow-sky-500/20"
              >
                {isSubmittingAction ? 'Đang lưu...' : 'Lưu'}
              </button>
            </div>
          {/if}
        </div>
      </div>

      <!-- Cargo Manifest (Danh sách hàng!) -->
      <div class="bg-white/[0.03] border border-white/5 rounded-[2rem] p-6 mb-8">
        <h3 class="text-xs font-black text-white uppercase tracking-widest mb-6 border-b border-white/5 pb-3 flex justify-between">
          <span>HÀNG HÓA TRONG ĐƠN</span>
          <span class="text-sky-500">SỐ LƯỢNG: {order?.itemCount || order?.items?.length || 0}</span>
        </h3>
        <div class="space-y-4">
          {#if order?.items && Array.isArray(order.items)}
            {#each order.items as item}
              <div class="flex items-center justify-between gap-4 p-3 bg-white/[0.02] rounded-xl border border-white/5">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 bg-white/5 rounded-lg flex items-center justify-center text-xl border border-white/5">📦</div>
                  <div class="flex flex-col">
                    <span class="text-xs font-bold text-white uppercase tracking-tight">{item.name || 'Sản phẩm'}</span>
                    <span class="text-[10px] text-slate-500 font-black uppercase tracking-widest">x{item.quantity || item.qty || 1} • {formatCurrency(item.price || item.unit_price || 0)}</span>
                  </div>
                </div>
                <div class="text-right">
                  <span class="text-sm font-black text-white italic">{formatCurrency(item.totalPrice || item.total_price || ((item.price || item.unit_price || 0) * (item.quantity || item.qty || 1)))}</span>
                </div>
              </div>
            {/each}
          {/if}
        </div>
      </div>

      {#if !isTrackingMode}
        <!-- Welcome Message for New Users! -->
        <div class="p-8 bg-sky-500/5 border border-sky-500/10 rounded-[2.5rem] text-center mb-8 relative overflow-hidden group" in:fade>
          <div class="absolute -right-4 -top-4 w-24 h-24 bg-sky-500/10 rounded-full blur-2xl group-hover:bg-sky-500/20 transition-all duration-1000"></div>
          <h3 class="text-sky-400 font-black text-[11px] uppercase tracking-[0.3em] mb-3 italic">🎁 ĐẶC QUYỀN THÀNH VIÊN</h3>
          <p class="text-slate-400 text-xs leading-relaxed max-w-sm mx-auto">
            Hệ thống đã tự động kích hoạt chế độ **Theo dõi ưu tiên** cho Quý khách. Hãy lưu lại mã đơn hàng hoặc dùng SĐT để tra cứu bất cứ lúc nào!
          </p>
        </div>
      {/if}

      <div class="flex flex-col md:flex-row gap-4 mb-4">
        <button
          onclick={() => isEditing = true}
          disabled={order?.status === 'CANCELLED' || isSubmittingAction || isEditing}
          class="flex-1 py-4 bg-white/[0.03] border border-white/10 text-slate-300 font-black text-center rounded-full hover:bg-white/[0.08] hover:text-white transition-all active:scale-95 uppercase tracking-widest text-[10px] italic disabled:opacity-20"
        >
          {isEditing ? 'ĐANG CHỈNH SỬA...' : 'CHỈNH SỬA ĐƠN'}
        </button>
        <button
          onclick={() => isConfirmCancelOpen = true}
          disabled={order?.status === 'CANCELLED' || isSubmittingAction}
          class="flex-1 py-4 bg-red-500/5 border border-red-500/10 text-red-500/70 font-black text-center rounded-full hover:bg-red-500/10 hover:text-red-500 transition-all active:scale-95 uppercase tracking-widest text-[10px] italic disabled:opacity-20"
        >
          {order?.status === 'CANCELLED' ? 'ĐÃ HỦY ❌' : 'HỦY ĐƠN HÀNG'}
        </button>
      </div>
      <a
        href="/"
        class="group block w-full py-6 bg-sky-500 text-slate-950 font-black text-center rounded-full hover:bg-sky-400 transition-all hover:scale-[1.02] active:scale-[0.98] shadow-2xl shadow-sky-500/20 uppercase tracking-[0.2em] italic text-xl relative overflow-hidden"
      >
        <span class="relative z-10">TIẾP TỤC MUA SẮM →</span>
        <div class="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
      </a>
    </div>
  {/if}

  <p class="mt-12 text-[10px] text-slate-700 font-black uppercase tracking-[0.3em]">Nhà Thuốc Hồng Sơn - Tận Tâm 2026</p>
</div>

<!-- Elite Toast System! -->
<div class="fixed bottom-8 right-8 z-[2000] flex flex-col gap-3 pointer-events-none">
  {#each toasts as toast (toast.id)}
    <div 
      in:fly={{ x: 50, duration: 400 }}
      out:fade
      class="px-6 py-4 rounded-2xl shadow-2xl backdrop-blur-xl border {toast.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-red-500/10 border-red-500/30 text-red-400'} flex items-center gap-3 pointer-events-auto"
    >
      <div class="w-2 h-2 rounded-full {toast.type === 'success' ? 'bg-emerald-400' : 'bg-red-400'} animate-pulse"></div>
      <span class="text-xs font-black uppercase tracking-widest italic">{toast.message}</span>
    </div>
  {/each}
</div>


<!-- Confirm Cancel Modal! -->
{#if isConfirmCancelOpen}
  <div 
    class="fixed inset-0 bg-slate-950/90 backdrop-blur-sm z-[2100] flex items-center justify-center p-6"
    transition:fade
  >
    <div 
      class="w-full max-w-sm bg-slate-900 border border-red-500/20 rounded-[3rem] p-10 text-center shadow-2xl"
      in:scale={{ duration: 400, start: 0.9 }}
    >
      <div class="w-20 h-20 bg-red-500/10 text-red-500 rounded-full flex items-center justify-center mx-auto mb-6 border border-red-500/20">
        <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
      </div>
      <h2 class="text-2xl font-black text-white uppercase italic mb-4">Xác nhận hủy đơn?</h2>
      <p class="text-slate-400 text-sm leading-relaxed mb-8">Quý khách có chắc chắn muốn hủy đơn hàng này không ạ? Hành động này không thể hoàn tác.</p>
      
      <div class="flex flex-col gap-3">
        <button 
          onclick={handleCancel}
          class="w-full py-4 bg-red-500 hover:bg-red-400 text-white font-black rounded-full transition-all active:scale-95 shadow-xl shadow-red-500/20 uppercase tracking-widest text-xs"
        >
          XÁC NHẬN HỦY ĐƠN
        </button>
        <button 
          onclick={() => isConfirmCancelOpen = false}
          class="w-full py-4 bg-white/5 text-slate-400 font-bold rounded-full hover:bg-white/10 transition-all uppercase tracking-widest text-[10px]"
        >
          QUAY LẠI
        </button>
      </div>
    </div>
  </div>
{/if}
{/if}
