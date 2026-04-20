<script lang="ts">
  import { fade, fly, scale, slide } from 'svelte/transition';
  import { FileText, ShieldCheck, ShoppingCart, MessageSquare, Package, Truck, Phone, Gift, Home, Sparkles, Edit3 } from 'lucide-svelte';
  import { formatCurrency, formatDate } from '$lib/utils/format.ts';
  import { goto } from '$app/navigation';
  import { SHOP_CONFIG } from '$lib/constants/shop';
  import { apiClient } from '$lib/utils/apiClient';
  import { page } from '$app/state';
  import vnDivisions from '$lib/data/vn_divisions.json';
  import SearchableCheckoutSelect from '$lib/components/storefront/ui/SearchableCheckoutSelect.svelte';

  import type { OrderDetail } from '$lib/types/commerce/order';
  let { order, orderId, isLookup } = $props<{ order: OrderDetail, orderId: string, isLookup: boolean }>();

  // --- Elite V2.2: Edit Logic ---
  let isEditing = $state(false);
  let isSubmittingAction = $state(false);
  let editForm = $state({
    name: '',
    phone: '',
    province: '',
    ward: '',
    street: ''
  });

  interface VnDivision {
    id: string;
    name: string;
    code: string;
    wards: string[];
  }

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

  function startEditing() {
    const addrParts = parseAddress(order.customer_address || '');
    editForm = {
        name: order.customer_name || '',
        phone: order.customer_phone || '',
        province: addrParts.province,
        ward: addrParts.ward,
        street: addrParts.street
    };
    isEditing = true;
  }

  // Local Elite Toast System
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

  async function handleSaveEdit() {
    isSubmittingAction = true;
    try {
        const phoneParam = page.url.searchParams.get('phone') || (typeof localStorage !== 'undefined' ? localStorage.getItem(`order_verify_${orderId}`) : null);
        
        await apiClient.patch(`/api/v1/client/orders/${orderId}`, {
            customer_name: editForm.name,
            customer_phone: editForm.phone,
            customer_address: `${editForm.street}, ${editForm.ward}, ${editForm.province}`
        }, { params: { phone: phoneParam } });
        
        // Refresh local data
        order.customer_name = editForm.name;
        order.customer_phone = editForm.phone;
        order.customer_address = `${editForm.street}, ${editForm.ward}, ${editForm.province}`;
        
        showToast("Đã cập nhật thông tin thành công");
        isEditing = false;
    } catch (err) {
        console.error("Failed to save", err);
        showToast((err as Error).message || "Lỗi cập nhật dữ liệu", "error");
    } finally {
        isSubmittingAction = false;
    }
  }

  const STATUS_STEPS = [
    { key: 'PENDING', label: 'Tiếp nhận', icon: FileText },
    { key: 'PACKED', label: 'Bảo mật', icon: ShieldCheck },
    { key: 'SHIPPING', label: 'Vận chuyển', icon: Truck },
    { key: 'DELIVERED', label: 'Thành công', icon: Gift }
  ];

  function getStepIndex(status: string) {
    if (status === 'CANCELLED') return -1;
    const idx = STATUS_STEPS.findIndex(s => s.key === status);
    return idx === -1 ? 0 : idx;
  }

  const currentStepIdx = $derived(getStepIndex(order?.status || 'PENDING'));

  let copied = $state(false);
  let copyTimer: ReturnType<typeof setTimeout> | undefined;

  function copyOrderId() {
    if (typeof navigator !== 'undefined') {
        const shortId = orderId.slice(-6).toUpperCase();
        navigator.clipboard.writeText(shortId);
        copied = true;
        if (copyTimer) clearTimeout(copyTimer);
        copyTimer = setTimeout(() => copied = false, 2000);
    }
  }

  const items = $derived(order?.items || []);
  const customerNameDisplay = $derived(order?.name_masked || order?.customer_name || 'Khách hàng');
  const customerAddressDisplay = $derived(order?.address_masked || order?.customer_address || 'Địa chỉ bảo mật');

  // Elite V2.2: Reactive Financial Breakdown
  const voucherDiscount = $derived(Number(order?.order_metadata?.voucher_discount || 0));
  const comboDiscount = $derived(Number(order?.order_metadata?.combo_discount || 0));
  const totalSavings = $derived(voucherDiscount + comboDiscount);
</script>

<div class="fixed inset-0 bg-[#fafafa] text-slate-900 overflow-y-auto flex flex-col">
  <header class="fixed top-0 left-0 w-full h-[48px] bg-white border-b border-slate-100 flex items-center justify-between px-4 z-[1000]">
     <button onclick={() => goto('/')} class="p-2 text-slate-900 active:scale-90 transition-transform">
       <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" /></svg>
     </button>
     <h1 class="text-sm font-black text-slate-900 uppercase italic tracking-tight">
        {isLookup ? 'CHI TIẾT ĐƠN HÀNG' : 'ĐẶT HÀNG THÀNH CÔNG'}
     </h1>
     <div class="w-9"></div>
  </header>

  <div class="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[250px] {isLookup ? 'bg-sky-500/5' : 'bg-emerald-500/5'} blur-[60px] pointer-events-none"></div>

  <div class="relative px-4 pt-[72px] flex flex-col items-center text-center">
    <p class="text-slate-400 text-[10px] uppercase tracking-[0.2em] font-black mb-8 italic">
      {order?.status === 'CANCELLED' ? 'RẤT TIẾC VÌ LIỆU TRÌNH KHÔNG ĐƯỢC TIẾP TỤC' : isLookup ? 'CẬP NHẬT TRẠNG THÁI MỚI NHẤT' : 'CẢM ƠN QUÝ KHÁCH ĐÃ TIN TƯỞNG'}
    </p>

    <div class="w-full mb-10 px-2">
      <div class="stepper-row flex items-center justify-between pb-8">
        {#each STATUS_STEPS as step, i}
          <div class="relative flex flex-col items-center gap-2">
            <div class="w-9 h-9 rounded-full flex items-center justify-center text-xl border-2 transition-all duration-500
              {i < currentStepIdx ? 'bg-emerald-50 border-emerald-500 text-emerald-600' : 
               i === currentStepIdx ? 'bg-sky-50 border-sky-500 text-sky-600 scale-110 shadow-lg' : 
               'bg-slate-50 border-slate-100 text-slate-300'}">
              <step.icon class="w-4 h-4" />
            </div>
            <span class="text-[8px] font-black uppercase tracking-widest {i <= currentStepIdx ? 'text-slate-900' : 'text-slate-300'}">{step.label}</span>
          </div>
          {#if i < STATUS_STEPS.length - 1}
            <div class="flex-1 h-[2px] mx-1 bg-slate-100 relative">
               <div class="absolute inset-y-0 left-0 bg-emerald-500 transition-all duration-1000" style:width={i < currentStepIdx ? '100%' : i === currentStepIdx ? '50%' : '0%'}></div>
            </div>
          {/if}
        {/each}
      </div>
    </div>

    <div class="w-full bg-white shadow-sm border-t-4 border-[#ee4d2d] p-6 mb-6 text-left space-y-8">
      <div class="flex flex-col gap-6 pb-6 border-b border-slate-50">
        <div class="flex justify-between items-start">
           <div>
              <span class="text-[9px] font-black text-slate-500 uppercase block mb-1">Mã liệu trình</span>
              <div class="bg-slate-50 px-2 py-1 border border-slate-100" onclick={copyOrderId} role="button" tabindex="0">
                <span class="text-xs font-black text-slate-900 tracking-widest uppercase italic">{copied ? 'COPIED!' : `#${orderId.slice(-6).toUpperCase()}`}</span>
              </div>
           </div>
           <div class="text-right">
              <span class="text-[9px] font-black text-slate-400 uppercase block mb-1">Tổng thanh toán</span>
              <span class="text-xl font-black text-[#ee4d2d] italic tabular-nums">{formatCurrency(order?.total_amount || 0)}</span>
           </div>
        </div>

        <!-- 🚀 [ELITE V2.2] Viral Savings Breakdown -->

        {#if totalSavings > 0}
          <div 
            class="py-4 px-4 bg-emerald-500/5 border-l-2 border-emerald-500 rounded-r-lg group relative overflow-hidden"
            in:fly={{ x: -20, delay: 400 }}
          >
             <div class="flex items-center gap-3">
                <div class="w-7 h-7 bg-emerald-500 text-white rounded-full flex items-center justify-center shadow-lg shadow-emerald-500/20">
                   <Sparkles size={14} class="animate-pulse" />
                </div>
                <div class="flex flex-col">
                   <span class="text-[8px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">SIÊU ƯU ĐÃI</span>
                   <span class="text-[10px] font-black text-emerald-600 uppercase italic">TIẾT KIỆM {formatCurrency(totalSavings)}</span>
                </div>
             </div>
             <div class="absolute inset-0 bg-gradient-to-r from-white/0 via-white/40 to-white/0 -translate-x-full animate-[shimmer_2.5s_infinite]"></div>
          </div>
        {/if}
      </div>

      <div class="space-y-6">
        <div class="flex items-start gap-3">
          <Package class="w-5 h-5 text-slate-300 mt-0.5 shrink-0" />
          <div class="flex-1 min-w-0">
            <span class="text-[9px] font-black text-slate-500 uppercase block mb-1">Sản phẩm chi tiết</span>
            <div class="space-y-1">
              {#each items as item}
                <p class="text-[11px] font-black text-slate-900 uppercase truncate">{item.quantity}X {item.name}</p>
              {/each}
            </div>
          </div>
        </div>

        <div class="flex items-start gap-3">
          <Truck class="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between mb-1">
              <span class="text-[9px] font-black text-slate-500 uppercase">Địa chỉ nhận hàng</span>
              <button onclick={startEditing} class="text-[9px] font-black text-sky-600 italic uppercase">CHỈNH SỬA</button>
            </div>
            <p class="text-[12px] font-black text-slate-900 uppercase italic leading-tight mb-1">{customerNameDisplay}</p>
            <p class="text-[10px] font-bold text-slate-500 uppercase leading-relaxed">{customerAddressDisplay}</p>
          </div>
        </div>
      </div>
    </div>
    
    <div class="w-full space-y-4 mb-20 px-4">
       <a href="tel:{SHOP_CONFIG.pharmacy.phone.replace(/\s+/g, '')}" class="block w-full py-4 bg-slate-900 text-white font-black uppercase italic tracking-widest text-center shadow-xl">GỌI XÁC NHẬN NGAY →</a>
       <p class="text-[10px] font-bold text-slate-400 uppercase italic">Hệ thống Micsmo Elite đang xử lý yêu cầu...</p>
    </div>
  </div>
</div>

{#if isEditing}
  <div class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[2000] flex items-center justify-center p-4">
     <div class="w-full max-w-sm bg-white p-8 space-y-6 border-t-4 border-sky-500 shadow-2xl">
        <h2 class="text-xl font-black text-slate-900 uppercase italic text-center">Cập nhật thông tin</h2>
        <div class="space-y-3">
           <input type="text" bind:value={editForm.name} class="w-full p-4 bg-slate-50 border border-slate-100 font-bold text-sm uppercase" />
           <input type="tel" bind:value={editForm.phone} class="w-full p-4 bg-slate-50 border border-slate-100 font-bold text-sm" />
           <button onclick={handleSaveEdit} class="w-full py-4 bg-slate-900 text-white font-black uppercase italic">LƯU THÔNG TIN</button>
           <button onclick={() => isEditing = false} class="w-full py-2 text-[10px] font-black text-slate-400 uppercase">QUAY LẠI</button>
        </div>
     </div>
  </div>
{/if}
