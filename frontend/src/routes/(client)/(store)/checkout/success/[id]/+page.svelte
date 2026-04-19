<script lang="ts">
  import { page } from '$app/state';
  import { fade, fly, scale, slide } from 'svelte/transition';
  import { Gift, MessageSquare, Sparkles } from 'lucide-svelte';
  import { Z_INDEX_CLIENT } from "$lib/core/constants/zIndex";
  import { onMount, tick } from 'svelte';
  import { apiClient } from '$lib/utils/apiClient';
  import { formatCurrency, formatDate } from '$lib/utils/format.ts';
  import SuccessMobile from '$lib/components/mobile/sections/SuccessMobile.svelte';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import vnDivisions from '$lib/data/vn_divisions.json';
  import SearchableCheckoutSelect from '$lib/components/storefront/ui/SearchableCheckoutSelect.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { browser } from '$app/environment';

  let { data } = $props<{ data: { isMobile: boolean } }>();
  const ui = getClientUi();

  // Standardize Layout: Sync header/footer with Elite V3.2 Protocol
  $effect.pre(() => {
    if (ui.isMobile) {
      ui.isHeaderHidden = true;
      ui.isFooterHidden = true;
    } else {
      ui.isHeaderHidden = false;
      ui.isFooterHidden = false;
    }
    return () => {
      ui.isHeaderHidden = false;
      ui.isFooterHidden = false;
    };
  });

  const orderId = page.params.id;
  const cartStore = getCartStore();

  // Elite V2.2: Order Status Roadmap
  import type { OrderDetail } from '$lib/types/commerce/order';

  interface VnDivision {
    id: string;
    name: string;
    code: string;
    wards: string[];
    has_express?: boolean;
    express_fee?: number;
    express_supported_wards?: string[];
  }

  const STATUS_STEPS = [
    { key: 'PENDING', label: 'Tiếp nhận', icon: '📝' },
    { key: 'PACKED', label: 'Bảo mật', icon: '🛡️' },
    { key: 'SHIPPING', label: 'Vận chuyển', icon: '🚚' },
    { key: 'DELIVERED', label: 'Thành công', icon: '🎁' }
  ];

  function getStepIndex(status: string) {
    if (status === 'CANCELLED') return -1;
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

  const validProvinces = (vnDivisions as unknown as VnDivision[]).filter(p => p.id);
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

  onMount(async () => {
    cartStore.clearCart();
    await fetchOrder();
  });

  async function fetchOrder(overridePhone?: string) {
    isLoading = true;
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
        const addrParts = parseAddress(order.customer_address || '');
        editForm = {
            name: order.customer_name || '',
            phone: order.customer_phone || '',
            province: addrParts.province,
            ward: addrParts.ward,
            street: addrParts.street
        };
      }
    } catch (err: unknown) {
      const e = err as { status?: number; message?: string };
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
  let isConfirmCancelOpen = $state(false);
</script>

<svelte:head>
  <title>{isTrackingMode ? 'Tra cứu đơn hàng' : 'Đặt hàng thành công'} | Micsmo.com</title>
</svelte:head>

{#if browser}
  {#if data.isMobile && order}
    <SuccessMobile {order} {orderId} isLookup={isTrackingMode} />
  {:else}
    <div class="min-h-screen bg-[#fafafa] text-slate-900 pb-20 pt-4 md:pt-10">
      <div class="max-w-[1240px] mx-auto px-4">
        
        {#if isLoading}
          <div class="py-20 flex flex-col items-center gap-6" in:fade>
            <div class="w-16 h-16 border-4 border-slate-100 border-t-[#ee4d2d] rounded-full animate-spin"></div>
            <h1 class="text-xl font-black text-slate-900 uppercase italic tracking-widest">Đang kết nối hệ thống...</h1>
          </div>
        {:else if isLocked}
          <div class="max-w-md mx-auto" in:fly={{ y: 20, duration: 800 }}>
            <div class="bg-white p-10 shadow-2xl border-t-4 border-amber-500 text-center space-y-8">
              <div class="w-20 h-20 bg-amber-50 text-amber-500 rounded-full flex items-center justify-center mx-auto border border-amber-100">
                <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
              </div>
              <h2 class="text-2xl font-black text-slate-900 italic uppercase">Cửa Ngõ Bảo Mật</h2>
              <div class="space-y-4">
                <input type="tel" bind:value={verificationPhone} placeholder="Nhập Số điện thoại..." class="w-full px-6 py-4 bg-slate-50 border-2 border-slate-100 focus:border-amber-500 outline-none text-center text-lg font-black" onkeydown={(e) => e.key === 'Enter' && handleVerify()} />
                <button onclick={handleVerify} class="w-full py-4 bg-slate-900 text-white font-black uppercase italic tracking-widest">XÁC THỰC →</button>
              </div>
            </div>
          </div>
        {:else if order}
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div class="lg:col-span-7 space-y-6">
              <div class="flex items-center justify-between mb-2">
                <h1 class="text-2xl font-black italic text-slate-900 uppercase">
                  {isTrackingMode ? 'TRA CỨU ĐƠN HÀNG' : 'ĐẶT HÀNG THÀNH CÔNG'}
                </h1>
                <div class="flex items-center gap-2 cursor-pointer" onclick={copyOrderId}>
                  <span class="text-[10px] font-black text-slate-400 uppercase">MÃ ĐƠN:</span>
                  <span class="text-xs font-black text-slate-900 bg-white px-2 py-1 border border-slate-100 uppercase italic">#{orderId.slice(-6)}</span>
                </div>
              </div>

              <!-- Timeline -->
              <div class="bg-white p-8 shadow-sm border-t-4 border-sky-500">
                <div class="max-w-md mx-auto flex flex-col gap-6">
                  <div class="flex items-center">
                    {#each STATUS_STEPS as step, i}
                       <div class="relative w-12 h-12">
                          <div class="w-full h-full rounded-full flex items-center justify-center text-xl border-2 transition-all duration-500
                            {stepIdx > i ? 'bg-emerald-50 border-emerald-500 text-emerald-600' : 
                             stepIdx === i ? 'bg-sky-50 border-sky-500 text-sky-600 scale-110 shadow-lg' : 
                             'bg-slate-50 border-slate-100 text-slate-300'}">
                             {step.icon}
                          </div>
                       </div>
                       {#if i < STATUS_STEPS.length - 1}
                         <div class="flex-1 h-1 mx-2 bg-slate-100 rounded-full overflow-hidden">
                           <div class="h-full bg-emerald-500 transition-all duration-1000" style:width={stepIdx > i ? '100%' : stepIdx === i ? '50%' : '0%'}></div>
                         </div>
                       {/if}
                    {/each}
                  </div>
                  <div class="flex justify-between items-start px-1">
                    {#each STATUS_STEPS as step, i}
                       <span class="text-[9px] font-black uppercase tracking-widest {stepIdx >= i ? 'text-slate-900' : 'text-slate-300'}">{step.label}</span>
                    {/each}
                  </div>
                </div>
                {#if !isTrackingMode}
                  <div class="mt-8 p-4 bg-sky-50 border border-sky-100 text-center">
                    <p class="text-[10px] text-sky-700 font-bold uppercase italic">Tài khoản tự động: <span class="font-black">{order.customer_phone}</span></p>
                  </div>
                {/if}
              </div>

              <!-- Info -->
              <div class="bg-white p-8 shadow-sm border-t-4 border-slate-900">
                <div class="flex items-center justify-between mb-8 border-b border-slate-50 pb-4">
                   <h3 class="text-sm font-black text-slate-900 uppercase italic">THÔNG TIN NHẬN HÀNG</h3>
                   {#if !isEditing}
                     <button onclick={() => isEditing = true} class="text-[10px] font-black text-sky-600 uppercase italic">CHỈNH SỬA</button>
                   {/if}
                </div>
                {#if !isEditing}
                  <div class="grid md:grid-cols-2 gap-8">
                    <div class="space-y-4">
                      <div>
                        <span class="text-[9px] font-black text-slate-400 uppercase block mb-1">Họ tên:</span>
                        <span class="text-sm font-bold uppercase">{order.name_masked || order.customer_name || 'Khách hàng'}</span>
                      </div>
                      <div>
                        <span class="text-[9px] font-black text-slate-400 uppercase block mb-1">Số điện thoại:</span>
                        <span class="text-sm font-bold">{order.customer_phone}</span>
                      </div>
                    </div>
                    <div>
                      <span class="text-[9px] font-black text-slate-400 uppercase block mb-1">Địa chỉ:</span>
                      <span class="text-xs font-bold text-slate-600 leading-snug uppercase">{order.address_masked || order.customer_address}</span>
                    </div>
                  </div>
                {:else}
                  <div class="space-y-6">
                    <div class="grid md:grid-cols-2 gap-4">
                      <input type="text" bind:value={editForm.name} class="px-4 py-3 bg-slate-50 border border-slate-100 font-bold text-sm uppercase" />
                      <input type="tel" bind:value={editForm.phone} class="px-4 py-3 bg-slate-50 border border-slate-100 font-bold text-sm" />
                    </div>
                    <div class="flex gap-4">
                      <button onclick={() => isEditing = false} class="px-6 py-2 text-[10px] font-black text-slate-400 uppercase">HỦY BỎ</button>
                      <button onclick={handleSaveEdit} class="px-8 py-3 bg-slate-900 text-white text-[10px] font-black uppercase">LƯU THÔNG TIN</button>
                    </div>
                  </div>
                {/if}
              </div>
            </div>

            <!-- RIGHT -->
            <div class="lg:col-span-5 space-y-6">
              <div class="bg-white p-6 shadow-sm border-t-4 border-[#ee4d2d] sticky top-20">
                <div class="flex justify-between items-center mb-6 pb-4 border-b border-slate-50">
                   <h3 class="text-sm font-black text-slate-900 uppercase italic">GIỎ HÀNG</h3>
                   <span class="text-[10px] font-black text-[#ee4d2d]">SL: {order.items.length}</span>
                </div>
                <div class="space-y-4 max-h-[400px] overflow-y-auto pr-2">
                   {#each order.items as item}
                     <div class="flex items-center gap-4">
                        <div class="w-14 h-14 bg-slate-50 border border-slate-100 rounded-sm flex items-center justify-center overflow-hidden italic">
                          {#if item.image_url}<img src={item.image_url} alt={item.name} class="w-full h-full object-cover" />{:else}📦{/if}
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="text-xs font-black text-slate-900 uppercase truncate mb-1">{item.name}</p>
                          <p class="text-[9px] text-slate-400 font-bold uppercase italic">SL: {item.quantity} × {formatCurrency(item.unit_price)}</p>
                        </div>
                        <div class="text-right">
                          <span class="text-sm font-black italic">{formatCurrency(item.total_price)}</span>
                        </div>
                     </div>
                   {/each}
                </div>

                {#if order.order_metadata?.custom_requests && order.order_metadata.custom_requests.length > 0}
                  <div class="pt-6 mt-6 border-t border-dashed border-slate-100">
                    <p class="text-[9px] font-black text-slate-500 uppercase italic mb-4">Yêu cầu bổ sung</p>
                    {#each order.order_metadata.custom_requests as c_item}
                       <div class="bg-amber-50/20 p-3 border border-amber-100/50 flex items-center gap-3 mb-2">
                         <div class="w-10 h-10 bg-white border border-amber-100 flex items-center justify-center text-lg">{#if c_item.image_url}<img src={c_item.image_url} alt={c_item.name} class="w-full h-full object-cover" />{:else}🧪{/if}</div>
                         <div class="flex-1 min-w-0">
                           <p class="text-[10px] font-black uppercase truncate">{c_item.name}</p>
                           <p class="text-[8px] font-bold text-slate-500 italic uppercase">Đang chờ báo giá</p>
                         </div>
                       </div>
                    {/each}
                  </div>
                {/if}

                <div class="mt-6 pt-6 border-t border-slate-100 space-y-3">
                   {@const subtotal = order.items.reduce((acc, it) => acc + (it.total_price || 0), 0)}
                   {@const voucherDiscount = Number(order.order_metadata?.voucher_discount || 0)}
                   {@const comboDiscount = Number(order.order_metadata?.combo_discount || 0)}
                   {@const totalSavings = voucherDiscount + comboDiscount}

                   <div class="flex justify-between text-[11px] font-black text-slate-400 uppercase italic">
                      <span>Tạm tính:</span>
                      <span>{formatCurrency(subtotal)}</span>
                   </div>
                   
                   {#if comboDiscount > 0}
                     <div class="flex justify-between text-[11px] font-black text-emerald-500 uppercase italic">
                        <span>Ưu đãi Combo:</span>
                        <span>-{formatCurrency(comboDiscount)}</span>
                     </div>
                   {/if}
                   
                   {#if voucherDiscount > 0}
                     <div class="flex justify-between text-[11px] font-black text-pink-500 uppercase italic">
                        <span>Voucher giảm giá:</span>
                        <span>-{formatCurrency(voucherDiscount)}</span>
                     </div>
                   {/if}

                   <div class="flex justify-between text-[11px] font-black text-emerald-500 uppercase italic">
                      <span>Vận chuyển:</span>
                      <span>MIỄN PHÍ</span>
                   </div>

                   <!-- 🧧 VIRAL SAVINGS BADGE -->
                   {#if totalSavings > 0}
                     <div 
                       class="relative py-3 px-4 bg-gradient-to-r from-emerald-500/10 to-transparent border-l-2 border-emerald-500 mt-4 overflow-hidden group"
                       in:fly={{ x: -20, delay: 600 }}
                     >
                        <div class="flex items-center gap-2">
                           <div class="p-1 bg-emerald-500 text-white rounded-full">
                              <Sparkles size={10} class="animate-pulse" />
                           </div>
                           <span class="text-[10px] font-black text-emerald-600 uppercase italic tracking-wider">
                              YAY! BẠN ĐÃ TIẾT KIỆM ĐƯỢC {formatCurrency(totalSavings)}
                           </span>
                        </div>
                        <div class="absolute inset-0 bg-gradient-to-r from-white/0 via-white/30 to-white/0 -translate-x-full animate-[shimmer_2s_infinite]"></div>
                     </div>
                   {/if}

                   <div class="flex justify-between items-end pt-4">
                      <span class="text-[10px] font-black text-slate-900 uppercase italic">TỔNG THANH TOÁN:</span>
                      <span class="text-3xl font-black text-[#ee4d2d] italic tabular-nums">{formatCurrency(order.total_amount)}</span>
                   </div>
                </div>

                {#if order.order_metadata?.gift_info || order.order_metadata?.customer_note}
                  <div class="pt-6 mt-6 border-t border-slate-100 space-y-4">
                    {#if order.order_metadata?.gift_info}
                       <div class="bg-pink-50/50 p-4 border border-pink-100/50 italic space-y-1">
                         <p class="text-[9px] font-black text-pink-500 uppercase mb-2">QUÀ TẶNG ELITE</p>
                         <p class="text-[11px] font-bold text-slate-600">"{order.order_metadata.gift_info.message}"</p>
                         <p class="text-[8px] font-black text-pink-400 uppercase">Từ: {order.order_metadata.gift_info.sender_name}</p>
                       </div>
                    {/if}
                    {#if order.order_metadata?.customer_note || order.order_metadata?.note}
                       <div class="bg-slate-50 p-4 border border-slate-100 italic space-y-1">
                         <p class="text-[9px] font-black text-slate-400 uppercase mb-2">GHI CHÚ ĐƠN HÀNG</p>
                         <p class="text-[11px] font-bold text-slate-600 leading-relaxed">{@html order.order_metadata.customer_note || order.order_metadata.note}</p>
                       </div>
                    {/if}
                  </div>
                {/if}

                <div class="pt-8 space-y-3">
                   <a href="/" class="block w-full py-4 bg-slate-900 text-white text-center text-xs font-black uppercase italic tracking-widest">TIẾP TỤC MUA SẮM →</a>
                   {#if order.status !== 'CANCELLED'}
                      <button onclick={() => isConfirmCancelOpen = true} class="block w-full py-2 text-[10px] font-black text-slate-300 uppercase italic text-center">Hủy đơn hàng</button>
                   {/if}
                </div>
              </div>
            </div>
          </div>
        {/if}
      </div>
    </div>
  {/if}
{/if}

{#if isConfirmCancelOpen}
  <div class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-6 z-[2000]" transition:fade>
    <div class="w-full max-w-sm bg-white shadow-2xl border-t-4 border-red-500 p-10 text-center space-y-6" in:scale>
      <h3 class="text-xl font-black uppercase italic">Xác nhận hủy đơn?</h3>
      <div class="flex flex-col gap-3">
        <button onclick={handleCancel} class="py-4 bg-red-500 text-white font-black uppercase italic tracking-widest">HỦY ĐƠN HÀNG</button>
        <button onclick={() => isConfirmCancelOpen = false} class="py-2 text-[10px] font-black text-slate-400 uppercase tracking-widest">QUAY LẠI</button>
      </div>
    </div>
  </div>
{/if}

<div class="fixed bottom-8 right-8 flex flex-col gap-4 pointer-events-none" style:z-index={Z_INDEX_CLIENT.TOAST}>
  {#each toasts as toast (toast.id)}
    <div in:fly={{ x: 50 }} out:fade class="px-8 py-4 bg-white shadow-2xl border-l-4 {toast.type === 'success' ? 'border-emerald-500' : 'border-red-500'} flex items-center gap-4 pointer-events-auto">
      <span class="text-[10px] font-black text-slate-900 uppercase italic">{toast.message}</span>
    </div>
  {/each}
</div>
