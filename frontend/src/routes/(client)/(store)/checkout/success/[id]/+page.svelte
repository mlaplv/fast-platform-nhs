<script lang="ts">
  import { page } from '$app/state';
  import { fade, fly, scale, slide } from 'svelte/transition';
  import { Z_INDEX_CLIENT } from "$lib/core/constants/zIndex";
  import { onMount } from 'svelte';
  import { apiClient } from '$lib/utils/apiClient';
  import { formatCurrency, formatDate } from '$lib/utils/format.ts';
  import SuccessMobile from '$lib/components/mobile/sections/SuccessMobile.svelte';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import vnDivisions from '$lib/data/vn_divisions.json';
  import SearchableCheckoutSelect from '$lib/components/storefront/ui/SearchableCheckoutSelect.svelte';

  let { data } = $props<{ data: { isMobile: boolean } }>();

  const orderId = page.params.id;
  const cartStore = getCartStore();

  // Elite V2.2: Order Status Roadmap
  import type { OrderDetail } from '$lib/types';
  const STATUS_STEPS = [
    { key: 'PENDING', label: 'Tiếp nhận', icon: '📝' },
    { key: 'PACKED', label: 'Bảo mật', icon: '🛡️' },
    { key: 'SHIPPING', label: 'Vận chuyển', icon: '🚚' },
    { key: 'DELIVERED', label: 'Thành công', icon: '🎁' }
  ];

  function getStepIndex(status: string) {
    const idx = STATUS_STEPS.findIndex(s => s.key === status);
    return idx === -1 ? 0 : idx;
  }

  // Elite V2.2: Retrieve phone from URL or LocalStorage to persist unlock!
  const phoneParam = page.url.searchParams.get('phone') || (typeof localStorage !== 'undefined' ? localStorage.getItem(`order_verify_${orderId}`) : null);
  const isTrackingMode = !!phoneParam;

  let order = $state<OrderDetail | null>(null);
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
    province: '',
    ward: '',
    street: ''
  });

  const validProvinces = (vnDivisions as any[]).filter(p => p.id);
  const currentWards = $derived.by(() => {
    if (!editForm.province) return [];
    const province = validProvinces.find(p => p.name === editForm.province);
    return province?.wards || [];
  });

  function parseAddress(fullAddress: string) {
    if (!fullAddress) return { province: '', ward: '', street: '' };
    const parts = fullAddress.split(',').map(p => p.trim());
    if (parts.length >= 3) {
      return {
        province: parts[parts.length - 1],
        ward: parts[parts.length - 2],
        street: parts.slice(0, parts.length - 2).join(', ')
      };
    }
    return { province: '', ward: '', street: fullAddress };
  }

  // Confirm Cancel State
  let isConfirmCancelOpen = $state(false);

  onMount(async () => {
    cartStore.clearCart();
    await fetchOrder();
  });

  async function fetchOrder(overridePhone?: string) {
    isLoading = true;
    authError = '';
    const phoneToUse = overridePhone || phoneParam;
    
    try {
      const res = await apiClient.get<OrderDetail>(`/api/v1/client/orders/${orderId}`, {
        params: phoneToUse ? { phone: phoneToUse } : undefined
      });
      if (res) {
        order = res;
        isLocked = false;
        // Persist the unlock!
        if (phoneToUse && typeof localStorage !== 'undefined') {
          localStorage.setItem(`order_verify_${orderId}`, phoneToUse);
        }
        const addrParts = parseAddress(order.customerAddress || order.customer_address || '');
        editForm = {
            name: order.customerName || order.customer_name || '',
            phone: order.customerPhone || order.customer_phone || '',
            province: addrParts.province,
            ward: addrParts.ward,
            street: addrParts.street
        };
      }
    } catch (err: unknown) {
      const e = err as { status?: number; message?: string };
      console.error("Failed to load order", e);
      // R2026: If it's a 400 validation error regarding phone, it's a "Lock"!
      if (e.status === 400 && e.message?.toLowerCase().includes('số điện thoại')) {
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
    } catch (err: unknown) {
      const e = err as { message?: string };
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
            customer_address: `${editForm.street}, ${editForm.ward}, ${editForm.province}`
        }, { params: { phone: phoneParam || verificationPhone } });
        showToast("Đã cập nhật thông tin thành công");
        isEditing = false;
        await fetchOrder();
    } catch (err: unknown) {
      const e = err as { message?: string };
        showToast(e.message || "Lỗi cập nhật dữ liệu", "error");
    } finally {
        isSubmittingAction = false;
    }
  }

  const stepIdx = $derived(getStepIndex(order?.status ?? ''));
</script>

<svelte:head>
  <title>{isTrackingMode ? 'Tra cứu đơn hàng' : 'Đặt hàng thành công'} | Micsmo.com</title>
</svelte:head>

{#if data.isMobile && order}
  <SuccessMobile {order} {orderId} isLookup={isTrackingMode} />
{:else}
  <div class="min-h-screen bg-[#fafafa] text-slate-900 pb-20 pt-4 md:pt-10 transition-colors duration-500">
    <div class="max-w-[1240px] mx-auto px-4">
      
      {#if isLoading}
        <div class="py-20 flex flex-col items-center gap-6" in:fade>
          <div class="w-16 h-16 border-4 border-slate-100 border-t-[#ee4d2d] rounded-full animate-spin"></div>
          <h1 class="text-xl font-black text-slate-900 uppercase italic tracking-widest">Đang kết nối hệ thống...</h1>
          <p class="text-[10px] text-slate-400 font-bold uppercase tracking-[0.3em]">Micsmo Elite Core Engine V2.2</p>
        </div>
      {:else if isLocked}
        <!-- Elite Security Gate (White Mode) -->
        <div class="max-w-md mx-auto" in:fly={{ y: 20, duration: 800 }}>
          <div class="bg-white p-10 shadow-2xl border-t-4 border-amber-500 text-center space-y-8">
            <div class="w-20 h-20 bg-amber-50 text-amber-500 rounded-full flex items-center justify-center mx-auto border border-amber-100">
              <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
            </div>
            
            <div class="space-y-2">
              <h2 class="text-2xl font-black text-slate-900 italic tracking-tighter uppercase leading-tight">Cửa Ngõ Bảo Mật</h2>
              <p class="text-slate-400 text-[10px] uppercase tracking-widest font-bold">Xác minh Số điện thoại để tiếp tục</p>
            </div>

            <div class="space-y-4">
              <input 
                type="tel" 
                bind:value={verificationPhone}
                placeholder="Nhập Số điện thoại..."
                class="w-full px-6 py-4 bg-slate-50 border-2 border-slate-100 focus:border-amber-500 focus:bg-white outline-none text-slate-900 font-black text-center text-lg placeholder:text-slate-300 transition-all rounded-none"
                onkeydown={(e) => e.key === 'Enter' && handleVerify()}
              />
              <button 
                onclick={handleVerify}
                class="w-full py-4 bg-slate-900 hover:bg-[#ee4d2d] text-white font-black transition-all active:scale-95 uppercase text-xs tracking-[0.3em] italic"
              >
                XÁC THỰC QUYỀN TRUY CẬP →
              </button>
            </div>
            
            <p class="text-[9px] text-slate-400 font-bold uppercase tracking-widest italic pt-4">An toàn • Bảo mật • Riêng tư</p>
          </div>
        </div>
      {:else}
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          <!-- LEFT: Order Status & Details -->
          <div class="lg:col-span-7 space-y-6">
            <div class="flex items-center justify-between mb-2">
              <h1 class="text-2xl font-black italic text-slate-900 tracking-tighter uppercase">
                {isTrackingMode ? 'TRA CỨU ĐƠN HÀNG' : 'ĐẶT HÀNG THÀNH CÔNG'}
              </h1>
              <div class="flex items-center gap-2 group cursor-pointer" onclick={copyOrderId}>
                <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">MÃ ĐƠN:</span>
                <span class="text-xs font-black text-slate-900 bg-white px-2 py-1 shadow-sm border border-slate-100 group-hover:text-[#ee4d2d] transition-colors">#{orderId.slice(-6).toUpperCase()}</span>
              </div>
            </div>

            <!-- Status Timeline Card -->
            <div class="bg-white p-8 shadow-sm border-t-4 border-sky-500 relative overflow-hidden">
               <!-- Subtle background glow -->
               <div class="absolute top-0 right-0 w-32 h-32 bg-sky-50 opacity-[0.03] rounded-full blur-3xl pointer-events-none"></div>

               <div class="max-w-md mx-auto flex flex-col gap-6 relative z-10">
                  <!-- Row 1: Icons + Connectors -->
                  <div class="flex items-center">
                    {#each STATUS_STEPS as step, i}
                       <div class="relative shrink-0 w-12 h-12">
                          {#if stepIdx === i}
                             <div class="node-halo absolute inset-0 bg-sky-500/10 rounded-full blur-xl animate-pulse"></div>
                          {/if}
                          <div class="w-full h-full rounded-full flex items-center justify-center text-xl transition-all duration-500 border-2 relative
                            {stepIdx > i ? 'bg-emerald-50 border-emerald-500 text-emerald-600' : 
                             stepIdx === i ? 'bg-sky-50 border-sky-500 text-sky-600 scale-110 shadow-lg shadow-sky-100' : 
                             'bg-slate-50 border-slate-100 text-slate-300'}">
                             {step.icon}
                          </div>
                       </div>
                       {#if i < STATUS_STEPS.length - 1}
                         <div class="flex-1 relative h-1 mx-2">
                           <div class="absolute inset-0 bg-slate-100 rounded-full"></div>
                           {#if stepIdx > i}
                             <div class="absolute inset-0 bg-gradient-to-r from-emerald-400 to-emerald-500 rounded-full shadow-sm transition-all duration-1000"></div>
                           {:else if stepIdx === i}
                             <div class="absolute inset-y-0 left-0 w-1/2 bg-sky-400 rounded-full transition-all duration-1000"></div>
                           {/if}
                         </div>
                       {/if}
                    {/each}
                  </div>

                  <!-- Row 2: Labels -->
                  <div class="flex items-start">
                    {#each STATUS_STEPS as step, i}
                       <div class="shrink-0 w-12 flex flex-col items-center">
                         <span class="text-[9px] font-black uppercase tracking-widest text-center transition-colors duration-500 
                           {stepIdx >= i ? 'text-slate-900' : 'text-slate-300'}">
                           {step.label}
                         </span>
                       </div>
                       {#if i < STATUS_STEPS.length - 1}
                         <div class="flex-1 mx-2"></div>
                       {/if}
                    {/each}
                  </div>
               </div>

               {#if !isTrackingMode}
                  <div class="mt-10 p-4 bg-sky-50 border border-sky-100 text-center">
                    <p class="text-[10px] text-sky-700 font-bold uppercase leading-relaxed uppercase italic">
                      Đã tự động tạo tài khoản: <span class="text-sky-900 font-black">{order?.customerPhone || ''}</span>
                    </p>
                  </div>
               {/if}
            </div>

            <!-- Customer Info Card -->
            <div class="bg-white p-8 shadow-sm border-t-4 border-slate-900">
               <div class="flex items-center justify-between mb-8 border-b border-slate-50 pb-4">
                  <h3 class="text-sm font-black text-slate-900 uppercase italic tracking-widest">THÔNG TIN NHẬN HÀNG</h3>
                  {#if !isEditing}
                    <button 
                      onclick={() => isEditing = true}
                      disabled={order?.status === 'CANCELLED' || !order?.is_trusted_device}
                      class="text-[10px] font-black text-sky-600 hover:text-sky-800 uppercase tracking-widest disabled:opacity-30"
                    >
                      CHỈNH SỬA
                    </button>
                  {/if}
               </div>

               {#if !isEditing}
                 <div class="grid md:grid-cols-2 gap-8" in:fade>
                   <div class="space-y-6">
                     <div class="flex flex-col">
                       <span class="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Họ tên:</span>
                       <span class="text-sm font-bold text-slate-900 uppercase">{order?.customerName || order?.name_masked || 'Khách hàng'}</span>
                     </div>
                     <div class="flex flex-col">
                       <span class="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Số điện thoại:</span>
                       <span class="text-sm font-bold text-slate-900 tracking-wider">{order?.customerPhone || order?.customer_phone || '---'}</span>
                     </div>
                   </div>
                   <div class="flex flex-col">
                     <span class="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Địa chỉ giao hàng:</span>
                     <span class="text-xs font-bold text-slate-600 leading-snug uppercase">{order?.customerAddress || order?.address_masked || 'Địa chỉ bảo mật'}</span>
                   </div>
                 </div>
               {:else}
                 <div class="space-y-6" in:slide>
                    <div class="grid md:grid-cols-2 gap-6">
                      <div class="space-y-1">
                        <label class="text-[8px] font-black text-slate-400 uppercase tracking-widest ml-1">Họ tên người nhận:</label>
                        <input type="text" bind:value={editForm.name} class="w-full px-4 py-3 bg-slate-50 border border-slate-100 font-bold text-sm uppercase focus:border-sky-500 outline-none text-slate-900" />
                      </div>
                      <div class="space-y-1">
                        <label class="text-[8px] font-black text-slate-400 uppercase tracking-widest ml-1">Số điện thoại:</label>
                        <input type="tel" bind:value={editForm.phone} class="w-full px-4 py-3 bg-slate-50 border border-slate-100 font-bold text-sm focus:border-sky-500 outline-none text-slate-900" />
                      </div>
                    </div>
                    <div class="grid md:grid-cols-2 gap-6">
                      <div class="space-y-1">
                        <label class="text-[8px] font-black text-slate-400 uppercase tracking-widest ml-1">Tỉnh / Thành phố:</label>
                        <SearchableCheckoutSelect 
                          bind:value={editForm.province} 
                          options={validProvinces.map(p => p.name)} 
                          placeholder="Chọn Tỉnh/Thành" 
                          onChange={() => editForm.ward = ''}
                        />
                      </div>
                      <div class="space-y-1">
                        <label class="text-[8px] font-black text-slate-400 uppercase tracking-widest ml-1">Phường / Xã:</label>
                        <SearchableCheckoutSelect 
                          bind:value={editForm.ward} 
                          options={currentWards} 
                          placeholder="Chọn Phường/Xã" 
                          disabled={!editForm.province}
                        />
                      </div>
                    </div>
                    <div class="space-y-1">
                      <label class="text-[8px] font-black text-slate-400 uppercase tracking-widest ml-1">Địa chỉ chi tiết (Số nhà, tên đường):</label>
                      <input type="text" bind:value={editForm.street} class="w-full px-4 py-3 bg-slate-50 border border-slate-100 font-bold text-sm uppercase focus:border-sky-500 outline-none text-slate-900" />
                    </div>
                    <div class="flex gap-3 justify-end pt-2">
                       <button onclick={() => isEditing = false} class="px-6 py-2 text-[10px] font-black text-slate-400 uppercase tracking-widest">HỦY BỎ</button>
                       <button onclick={handleSaveEdit} disabled={isSubmittingAction} class="px-8 py-3 bg-slate-900 text-white text-[10px] font-black uppercase tracking-widest hover:bg-sky-600 transition-colors">
                         {isSubmittingAction ? 'ĐANG LƯU...' : 'LƯU THÔNG TIN'}
                       </button>
                    </div>
                 </div>
               {/if}

               {#if order?.is_trusted_device === false}
                  <div class="mt-8 p-4 bg-amber-50 border border-amber-100 flex items-center gap-3">
                    <svg class="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                    <p class="text-[9px] text-amber-700 font-bold uppercase italic tracking-wider">Thiết bị không tin cậy - Vui lòng không thực hiện chỉnh sửa nhạy cảm.</p>
                  </div>
               {/if}
            </div>

            <!-- Welcome Benefits (if success) -->
            {#if !isTrackingMode}
              <div class="bg-gradient-to-br from-emerald-500 to-emerald-600 p-8 shadow-sm flex items-center justify-between group overflow-hidden relative">
                <div class="relative z-10 space-y-2">
                  <h4 class="text-white font-black text-lg italic uppercase tracking-tighter">ĐẶC QUYỀN ELITE ACTIVATED!</h4>
                  <p class="text-emerald-100 text-[10px] font-bold uppercase tracking-widest max-w-sm">Hệ thống đã ưu tiên xử lý đơn hàng của Quý khách. Theo dõi tiến độ thời gian thực ngay tại trang này.</p>
                </div>
                <div class="text-6xl group-hover:scale-125 transition-transform duration-700 opacity-20 relative z-0">🎁</div>
                <div class="absolute -right-10 -bottom-10 w-40 h-40 bg-white/10 rounded-full blur-3xl group-hover:bg-white/20 transition-all duration-700"></div>
              </div>
            {/if}
          </div>

          <!-- RIGHT: Order Items & Actions -->
          <div class="lg:col-span-5 space-y-6">
            
             <!-- Order Items Box -->
             <div class="bg-white p-6 shadow-sm border-t-4 border-[#ee4d2d] space-y-6 sticky top-20">
                <div class="flex items-center justify-between border-b border-slate-50 pb-4">
                  <h3 class="text-sm font-black text-slate-900 uppercase italic tracking-widest">SẢN PHẨM TRONG ĐƠN</h3>
                  <span class="text-[10px] font-black text-[#ee4d2d] uppercase">SL: {order?.itemCount || order?.items?.length || 0}</span>
                </div>

                <div class="space-y-4 max-h-[400px] overflow-y-auto pr-2 scrollbar-thin">
                  {#if order?.items && Array.isArray(order.items)}
                    {#each order.items as item}
                      <div class="flex items-center gap-4 group">
                        <div class="w-16 h-16 bg-slate-50 border border-slate-100 rounded-sm flex items-center justify-center text-2xl group-hover:bg-slate-100 transition-colors">📦</div>
                        <div class="flex-1 flex flex-col justify-center">
                          <span class="text-xs font-black text-slate-900 uppercase leading-tight mb-2 group-hover:text-[#ee4d2d] transition-colors">{item.name || 'Sản phẩm'}</span>
                          <span class="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Số lượng: {item.quantity || item.qty || 1}</span>
                        </div>
                        <div class="text-right">
                          <span class="text-sm font-black text-slate-900 italic">{formatCurrency(item.totalPrice || item.total_price || ((item.price || item.unit_price || 0) * (item.quantity || item.qty || 1)))}</span>
                        </div>
                      </div>
                    {/each}
                  {/if}
                </div>

                <!-- Financial Summary -->
                <div class="border-t border-slate-100 pt-6 space-y-4">
                   <div class="flex justify-between items-center text-[11px] font-bold text-slate-500 uppercase tracking-widest">
                      <span>TỔNG TIỀN HÀNG:</span>
                      <span>{formatCurrency(order?.total || order?.total_amount || 0)}</span>
                   </div>
                   <div class="flex justify-between items-center text-[11px] font-bold text-emerald-500 uppercase tracking-widest">
                      <span>PHÍ VẬN CHUYỂN:</span>
                      <span>MIỄN PHÍ</span>
                   </div>
                   <div class="flex justify-between items-end pt-2">
                      <div class="flex flex-col">
                        <span class="text-[10px] font-black text-slate-900 uppercase tracking-widest">TỔNG THANH TOÁN:</span>
                        <span class="text-[10px] font-bold text-slate-400 uppercase italic">Thanh toán khi nhận hàng (COD)</span>
                      </div>
                      <span class="text-3xl font-black text-[#ee4d2d] italic tracking-tighter tabular-nums">{formatCurrency(order?.total || order?.total_amount || 0)}</span>
                   </div>
                   
                   <div class="flex flex-col gap-1 pt-4 border-t border-slate-50">
                      <span class="text-[9px] font-black text-slate-400 uppercase tracking-widest">Trạng thái hiện tại:</span>
                      <div class="flex items-center gap-2">
                        <div class="w-2 h-2 rounded-full {order?.status === 'CANCELLED' ? 'bg-red-500' : 'bg-amber-500'} animate-pulse"></div>
                        <span class="text-xs font-black uppercase italic {order?.status === 'CANCELLED' ? 'text-red-500' : 'text-amber-500'}">
                            {order?.status === 'CANCELLED' ? 'Đã hủy đơn hàng' : (STATUS_STEPS.find(s => s.key === order?.status)?.label || 'Đang xử lý')}
                        </span>
                      </div>
                   </div>
                </div>

                <!-- Footer Actions -->
                <div class="space-y-3 pt-6 border-t border-slate-100">
                   <a 
                     href="/" 
                     class="block w-full py-4 bg-slate-900 text-white text-center text-xs font-black uppercase tracking-[0.3em] italic hover:bg-[#ee4d2d] transition-all active:scale-[0.98] shadow-lg shadow-slate-200"
                   >
                     TIẾP TỤC MUA SẮM →
                   </a>
                   
                   {#if order?.status !== 'CANCELLED'}
                      <button 
                        onclick={() => isConfirmCancelOpen = true}
                        class="block w-full py-3 text-center text-[10px] font-black text-slate-300 hover:text-red-500 uppercase tracking-[0.2em] transition-colors"
                      >
                        HỦY ĐƠN HÀNG NẾU MUỐN
                      </button>
                   {/if}
                </div>
             </div>

          </div>
        </div>
      {/if}
      
      <p class="mt-20 text-center text-[10px] text-slate-300 font-black uppercase tracking-[0.5em] italic">Micsmo.com - Bật tông trắng sáng</p>
    </div>
  </div>
{/if}

<!-- Elite Toast System (White/Elite Style) -->
<div class="fixed bottom-8 right-8 flex flex-col gap-4 pointer-events-none" style:z-index={Z_INDEX_CLIENT.TOAST}>
  {#each toasts as toast (toast.id)}
    <div 
      in:fly={{ x: 50, duration: 400 }}
      out:fade
      class="px-8 py-4 bg-white shadow-2xl border-l-4 {toast.type === 'success' ? 'border-emerald-500' : 'border-red-500'} flex items-center gap-4 pointer-events-auto"
    >
      <div class="text-xl">{toast.type === 'success' ? '✅' : '❌'}</div>
      <span class="text-[10px] font-black text-slate-900 uppercase tracking-widest italic">{toast.message}</span>
    </div>
  {/each}
</div>

<!-- Confirm Cancel Modal (Elite White Style) -->
{#if isConfirmCancelOpen}
  <div class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-6" style:z-index={Z_INDEX_CLIENT.TOAST + 100} transition:fade>
    <div class="w-full max-w-sm bg-white shadow-2xl border-t-4 border-red-500 p-10 text-center space-y-6" in:scale={{ duration: 400, start: 0.9 }}>
      <div class="w-20 h-20 bg-red-50 text-red-500 rounded-full flex items-center justify-center mx-auto border border-red-100">
        <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
      </div>
      <div class="space-y-2">
        <h2 class="text-2xl font-black text-slate-900 uppercase italic tracking-tighter">Xác nhận hủy đơn?</h2>
        <p class="text-slate-400 text-xs font-bold uppercase leading-relaxed tracking-wider px-2">Hành động này không thể hoàn tác. Sếp chắc chắn chứ ạ?</p>
      </div>
      
      <div class="flex flex-col gap-3 pt-4">
        <button onclick={handleCancel} class="w-full py-4 bg-red-500 hover:bg-red-600 text-white font-black uppercase tracking-widest text-xs italic shadow-lg shadow-red-100">
          XÁC NHẬN HỦY ĐƠN
        </button>
        <button onclick={() => isConfirmCancelOpen = false} class="w-full py-4 text-slate-400 font-black text-[10px] uppercase tracking-widest">
          QUAY LẠI
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  /* Shimmer for progress lines on white theme */
  @keyframes shimmer-flow {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  .scrollbar-thin::-webkit-scrollbar {
    width: 4px;
  }
  .scrollbar-thin::-webkit-scrollbar-track {
    background: #f8fafc;
  }
  .scrollbar-thin::-webkit-scrollbar-thumb {
    background: #e2e8f0;
    border-radius: 10px;
  }
  .scrollbar-thin::-webkit-scrollbar-thumb:hover {
    background: #cbd5e1;
  }
</style>

