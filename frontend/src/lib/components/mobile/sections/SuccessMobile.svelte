<script lang="ts">
  import { fade, fly, scale, slide } from 'svelte/transition';
  import { FileText, ShieldCheck, Copy, ShoppingCart, MessageSquare, CheckCircle2, Package, Truck, Award, Sparkles, Phone, Gift, Home, XCircle, Edit3 } from 'lucide-svelte';
  import { formatCurrency, formatDate } from '$lib/utils/format.ts';
  import { goto } from '$app/navigation';
  import { SHOP_CONFIG } from '$lib/constants/shop';
  import { apiClient } from '$lib/utils/apiClient';
  import vnDivisions from '$lib/data/vn_divisions.json';
  import SearchableCheckoutSelect from '$lib/components/storefront/ui/SearchableCheckoutSelect.svelte';

  import { page } from '$app/state';

  import type { OrderDetail } from '$lib/types';
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
    const addrParts = parseAddress(order.customerAddress || order.customer_address || '');
    editForm = {
        name: order.customerName || order.customer_name || '',
        phone: order.customerPhone || order.customer_phone || '',
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
        order.customerName = editForm.name;
        order.customerPhone = editForm.phone;
        order.customerAddress = `${editForm.street}, ${editForm.ward}, ${editForm.province}`;
        
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

  function symbolizeMask(text: string | null | undefined) {
    if (!text) return '';
    return text.replace(/\*{2,}/g, '***');
  }

  const currentStepIdx = $derived(getStepIndex(order?.status || 'PENDING'));


  let copied = $state(false);
  let copyTimer: ReturnType<typeof setTimeout> | undefined;

  $effect(() => {
    return () => {
      if (copyTimer) clearTimeout(copyTimer);
    };
  });

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
  const customerName = $derived(symbolizeMask(order?.customerName || order?.name_masked) || 'Khách hàng');
  const customerAddress = $derived(symbolizeMask(order?.customerAddress || order?.address_masked) || 'Địa chỉ bảo mật');
</script>

<div class="fixed inset-0 bg-[#fafafa] text-slate-900 overflow-y-auto custom-scrollbar flex flex-col">
  <!-- Top Navigation (Standard 48px Header) -->
  <header class="fixed top-0 left-0 w-full h-[48px] bg-white border-b border-slate-100 flex items-center justify-between px-4 z-[1000]">
     <button
       onclick={() => goto('/')}
       class="p-2 text-slate-900 active:scale-90 transition-transform"
       aria-label="Back"
     >
       <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" /></svg>
     </button>

     <h1 class="text-sm font-black text-slate-900 uppercase italic tracking-tight">
        {isLookup ? 'CHI TIẾT ĐƠN HÀNG' : 'ĐẶT HÀNG THÀNH CÔNG'}
     </h1>

     <div class="w-9"></div>
  </header>

  <!-- Celebration Glow (Subtle for Light Mode) -->
  <div class="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[300px] {isLookup ? 'bg-sky-500/5' : 'bg-emerald-500/5'} blur-[80px] pointer-events-none"></div>

  <div class="relative px-4 pt-[72px] flex flex-col items-center text-center">
    
    <p in:fade={{ delay: 200 }} class="text-slate-400 text-[11px] uppercase tracking-[0.25em] font-black mb-10 italic">
      {#if order?.status === 'CANCELLED'}
        RẤT TIẾC VÌ LIỆU TRÌNH KHÔNG ĐƯỢC TIẾP TỤC
      {:else}
        {isLookup ? 'CẬP NHẬT TRẠNG THÁI MỚI NHẤT' : 'CẢM ƠN QUÝ KHÁCH ĐÃ TIN TƯỞNG'}
      {/if}
    </p>

    <!-- Status Timeline (White Mode) -->
    <div in:fly={{ y: 20, duration: 800, delay: 500 }} class="w-full mb-10 px-2">
      <div class="stepper-row">
        {#each STATUS_STEPS as step, i}
          <div class="stepper-node">
            {#if i === currentStepIdx}
              <div class="node-halo absolute -inset-2 bg-sky-500/5 rounded-full blur-xl animate-pulse"></div>
            {/if}
            <div class="node-circle {
              i < currentStepIdx  ? 'bg-emerald-50 border-emerald-500 text-emerald-600' :
              i === currentStepIdx? 'bg-sky-50 border-sky-500 text-sky-600 scale-110 shadow-lg shadow-sky-100' :
              'bg-slate-50 border-slate-100 text-slate-300'}">
              <step.icon class="w-4 h-4" />
            </div>
            <span class="node-label {i <= currentStepIdx ? 'text-slate-900' : 'text-slate-300'}">
              {step.label}
            </span>
          </div>

          {#if i < STATUS_STEPS.length - 1}
            <div class="connector">
              <div class="connector-track bg-slate-100"></div>
              {#if i < currentStepIdx}
                <div class="connector-fill bg-emerald-500 shadow-sm"></div>
              {:else if i === currentStepIdx}
                <div class="connector-fill w-1/2 bg-sky-400"></div>
              {/if}
            </div>
          {/if}
        {/each}
      </div>
    </div>


    <!-- Main Order Card (Checkout Style) -->
    <div in:fly={{ y: 30, duration: 800, delay: 600 }} class="w-full bg-white shadow-sm border-t-4 border-[#ee4d2d] p-6 mb-6 text-left relative overflow-hidden">
      <div class="flex justify-between items-start mb-8 border-b border-slate-50 pb-6">
        <div>
           <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest block mb-2">Mã liệu trình</span>
           <div class="flex items-center gap-2 active:opacity-60 transition-opacity" onclick={copyOrderId} role="button" tabindex="0">
             <span class="text-base font-black text-slate-900 tracking-widest uppercase italic bg-slate-50/50 px-3 py-1.5 border border-slate-100 shadow-sm">{copied ? 'ĐÃ SAO CHÉP!' : `#${orderId.slice(-6).toUpperCase()}`}</span>
           </div>
        </div>
        <div class="text-right">
           <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">Tổng (Freeship)</span>
           <span class="text-2xl font-black text-[#ee4d2d] italic tabular-nums">{(order?.total || 0).toLocaleString()}đ</span>
        </div>
      </div>

      <div class="space-y-8">
        <div class="flex items-start gap-4">
          <div class="w-12 h-12 rounded-lg bg-slate-50/50 border border-slate-100 flex items-center justify-center shrink-0 shadow-sm">
             <Package class="w-6 h-6 text-slate-300" strokeWidth={1.5} />
          </div>
          <div class="flex-1 pt-0.5">
            <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest block mb-2">Sản phẩm trong đơn</span>
            <div class="space-y-2">
              {#each items as item}
                <p class="text-[11.5px] font-black text-[#0f172a] leading-relaxed uppercase">
                  {item.quantity || item.qty || 1}X {item.name}
                </p>
              {/each}
            </div>
          </div>
        </div>

        <div class="flex items-start gap-4">
          <div class="w-12 h-12 rounded-lg bg-slate-50/50 border border-slate-100 flex items-center justify-center shrink-0 shadow-sm">
             <Truck class="w-6 h-6 text-slate-400" strokeWidth={1.5} />
          </div>
          <div class="flex-1 pt-0.5">
            <div class="flex items-center justify-between mb-2">
              <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest block">Giao đến</span>
              {#if !isEditing}
                <button 
                  onclick={startEditing}
                  class="flex items-center gap-1.5 text-[10px] font-black text-[#1e88e5] uppercase tracking-widest hover:opacity-70 transition-opacity"
                >
                  <Edit3 class="w-3 h-3" /> CHỈNH SỬA
                </button>
              {/if}
            </div>

            <div in:fade>
              <p class="text-[12.5px] font-black text-[#0f172a] leading-tight uppercase italic mb-1.5">{customerName}</p>
              <p class="text-[11px] font-bold text-slate-500 leading-relaxed uppercase">{customerAddress}</p>
            </div>
          </div>
        </div>

        <!-- Elite V2.2: Mobile Metadata Sections -->
        {#if order?.order_metadata?.gift_info || order?.orderMetadata?.gift_info}
          {@const gift = order?.order_metadata?.gift_info || order?.orderMetadata?.gift_info}
          <div class="p-4 bg-pink-50/40 border border-pink-100/50 rounded-sm space-y-3">
             <div class="flex items-center gap-2 text-pink-600">
                <Gift class="w-4 h-4" />
                <span class="text-[9px] font-black uppercase tracking-widest italic">QUÀ TẶNG ELITE</span>
             </div>
             <p class="text-[10px] font-bold text-slate-600 leading-snug italic">"{gift.message || 'Chúc mừng ngày đặc biệt'}"</p>
             <div class="text-[8px] font-black text-pink-400 uppercase tracking-tighter">Từ: {gift.sender_name}</div>
          </div>
        {/if}

        {#if order?.order_metadata?.customer_note || order?.orderMetadata?.customer_note}
          <div class="p-4 bg-slate-50 border border-slate-100 rounded-sm space-y-2">
             <div class="flex items-center gap-2 text-slate-500">
                <MessageSquare class="w-4 h-4" />
                <span class="text-[9px] font-black uppercase tracking-widest italic">GHI CHÚ ĐƠN HÀNG</span>
             </div>
             <div class="text-[10px] font-bold text-slate-600 leading-relaxed italic prose-p:my-0">
                {@html order?.order_metadata?.customer_note || order?.orderMetadata?.customer_note}
             </div>
          </div>
        {/if}

        {#if (order?.order_metadata?.custom_requests || order?.orderMetadata?.custom_requests || order?.order_metadata?.customRequests || order?.orderMetadata?.customRequests || order?.order_metadata?.custom_items) && (order?.order_metadata?.custom_requests || order?.orderMetadata?.custom_requests || order?.order_metadata?.customRequests || order?.orderMetadata?.customRequests || order?.order_metadata?.custom_items).length > 0}
          <div class="space-y-4 pt-2">
            <div class="flex items-center gap-2 border-b border-amber-100/50 pb-2">
              <Sparkles class="w-3.5 h-3.5 text-amber-500" />
              <span class="text-[9px] font-black text-slate-500 uppercase tracking-widest italic">SẢN PHẨM YÊU CẦU BỔ SUNG</span>
            </div>
            <div class="space-y-2">
              {#each (order?.order_metadata?.custom_requests || order?.orderMetadata?.custom_requests || order?.order_metadata?.customRequests || order?.orderMetadata?.customRequests || order?.order_metadata?.custom_items) as c_item}
                <div class="flex items-center gap-4 bg-amber-50/20 p-3 border border-amber-100/50 rounded-sm">
                   <div class="w-12 h-12 bg-white border border-amber-100/30 flex items-center justify-center text-xl overflow-hidden shrink-0">
                      {#if c_item.image || c_item.image_url}<img src={c_item.image || c_item.image_url} alt={c_item.name} class="w-full h-full object-cover" />{:else}🧪{/if}
                   </div>
                   <div class="flex-1 min-w-0">
                     <div class="text-[10px] font-black text-slate-800 uppercase truncate mb-0.5">{c_item.name}</div>
                     <div class="text-[8px] text-slate-500 font-bold uppercase tracking-tighter italic">SL: {c_item.qty || c_item.quantity || 1} · Đang chờ báo giá</div>
                   </div>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    </div>

    {#if order?.status !== 'CANCELLED'}
      <!-- What's Next Card (White Mode) -->
      <div in:fly={{ y: 30, duration: 800, delay: 800 }} class="w-full bg-white shadow-sm mb-6 pb-8 relative">
         <div class="p-8 text-center border-b-0">
           <span class="text-[11px] font-black text-[#1e88e5] uppercase tracking-[0.3em] block mb-4 italic flex items-center justify-center gap-2">
             <Sparkles class="w-4 h-4" strokeWidth={2.5} /> TIẾP THEO LÀ GÌ?
           </span>
           <p class="text-[13px] font-bold text-slate-600 leading-relaxed max-w-[260px] mx-auto uppercase">
             Hệ thống đang xử lý. Chuyên gia sẽ xác nhận đơn trong vòng 15 phút tới!
           </p>
         </div>
         
         <div class="relative px-6">
            <a 
              href="tel:{SHOP_CONFIG.pharmacy.phone.replace(/\s+/g, '')}"
              class="w-full h-[60px] bg-[#111827] text-white font-black text-[14px] uppercase tracking-[0.2em] active:scale-95 transition-all text-center flex items-center justify-center gap-3 italic mb-2 shadow-xl"
            >
                GỌI XÁC NHẬN NGAY <Phone class="w-5 h-5 fill-white" />
            </a>
            
            <div class="absolute -bottom-4 left-1/2 -translate-x-1/2 flex items-center justify-center gap-2 py-2 px-6 bg-white rounded-full border border-slate-100 shadow-md whitespace-nowrap z-10 w-auto">
               <div class="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
               <span class="text-[9px] font-black text-slate-400 uppercase tracking-widest pt-[2px]">Hệ thống đã sẵn sàng</span>
            </div>
         </div>
      </div>
    {:else}
      <div class="w-full bg-white shadow-sm p-6 mb-6">
         <button
            onclick={() => goto('/')}
            class="w-full h-[60px] bg-[#111827] text-white font-black text-[14px] uppercase tracking-[0.2em] active:scale-95 transition-all text-center flex items-center justify-center gap-3 italic shadow-xl"
          >
              QUAY LẠI CỬA HÀNG <Home class="w-5 h-5 fill-white" />
          </button>
      </div>
    {/if}

    <!-- Spacer -->
    <div class="h-10 shrink-0 pointer-events-none"></div>
  </div>

  <!-- Elite Mobile Toasts -->
  <div class="fixed bottom-24 left-4 right-4 flex flex-col gap-3 pointer-events-none z-[3000]">
    {#each toasts as toast (toast.id)}
       <div 
         in:fly={{ y: 20, duration: 400 }}
         out:fade
         class="px-6 py-4 bg-white shadow-2xl border-l-[4px] {toast.type === 'success' ? 'border-emerald-500' : 'border-red-500'} flex items-center gap-4 pointer-events-auto"
       >
         <div class="text-xl">{toast.type === 'success' ? '✅' : '❌'}</div>
         <span class="text-[10px] font-black text-slate-900 uppercase tracking-widest italic">{toast.message}</span>
       </div>
    {/each}
  </div>

  <!-- Global Edit Modal (Elite Style) -->
  {#if isEditing}
    <div class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-6 z-[2000]" transition:fade>
      <div 
        in:scale={{ duration: 450, start: 0.9, opacity: 0 }} 
        class="w-full max-w-sm bg-white shadow-[0_20px_50px_rgba(0,0,0,0.3)] border-t-4 border-[#1e88e5] overflow-hidden flex flex-col"
      >
         <div class="p-8 pb-4 text-center">
            <h2 class="text-2xl font-black text-slate-900 uppercase italic tracking-tighter leading-tight mb-1">CHỈNH SỬA THÔNG TIN</h2>
            <p class="text-[9px] text-slate-400 font-bold uppercase tracking-widest">Cập nhật thông tin nhận hàng</p>
         </div>

         <div class="px-8 pb-8 space-y-5">
            <div class="space-y-1">
              <label class="text-[9px] font-black text-slate-500 uppercase tracking-widest ml-1">Họ tên người nhận:</label>
              <input type="text" bind:value={editForm.name} class="w-full h-12 px-4 bg-slate-50 border border-slate-100 font-bold text-sm uppercase focus:border-[#ee4d2d] outline-none text-slate-900 shadow-sm" />
            </div>
            <div class="space-y-1">
              <label class="text-[9px] font-black text-slate-500 uppercase tracking-widest ml-1">Số điện thoại:</label>
              <input type="tel" bind:value={editForm.phone} class="w-full h-12 px-4 bg-slate-50 border border-slate-100 font-bold text-sm focus:border-[#ee4d2d] outline-none text-slate-900 shadow-sm" />
            </div>
            
            <div class="space-y-4">
               <div class="space-y-1">
                 <label class="text-[9px] font-black text-slate-500 uppercase tracking-widest ml-1">Tỉnh/Thành:</label>
                 <SearchableCheckoutSelect 
                   bind:value={editForm.province} 
                   options={validProvinces.map(p => p.name)} 
                   placeholder="Chọn Tỉnh" 
                   onChange={() => editForm.ward = ''}
                 />
               </div>
               <div class="space-y-1">
                 <label class="text-[9px] font-black text-slate-500 uppercase tracking-widest ml-1">Phường/Xã:</label>
                 <SearchableCheckoutSelect 
                   bind:value={editForm.ward} 
                   options={currentWards} 
                   placeholder="Chọn Phường" 
                   disabled={!editForm.province}
                 />
               </div>
            </div>

            <div class="space-y-1">
               <label class="text-[9px] font-black text-slate-500 uppercase tracking-widest ml-1">Địa chỉ (Số nhà, đường):</label>
               <input type="text" bind:value={editForm.street} class="w-full h-12 px-4 bg-slate-50 border border-slate-100 font-bold text-sm uppercase focus:border-[#ee4d2d] outline-none text-slate-900 shadow-sm" />
            </div>

            <div class="flex flex-col gap-3 pt-4">
               <button 
                 onclick={handleSaveEdit} 
                 disabled={isSubmittingAction} 
                 class="w-full h-[52px] bg-[#111827] text-white text-[13px] font-black uppercase tracking-[0.2em] italic flex items-center justify-center gap-2 shadow-xl active:scale-95 transition-all"
               >
                 {isSubmittingAction ? 'ĐANG LƯU HỆ THỐNG...' : 'XÁC NHẬN CẬP NHẬT'}
               </button>
               <button 
                 onclick={() => isEditing = false} 
                 class="w-full h-10 text-slate-400 text-[10px] font-black uppercase tracking-widest hover:text-slate-600 transition-colors"
               >
                 QUAY LẠI
               </button>
            </div>
         </div>
      </div>
    </div>
  {/if}
</div>


<style lang="postcss">
  :global(body) {
    background-color: #fafafa;
  }

  .stepper-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 4px 44px;
  }

  .connector {
    flex: 1;
    position: relative;
    height: 2px;
    margin: 0 4px;
  }
  
  .connector-track {
    position: absolute;
    inset: 0;
    border-radius: 99px;
    background: #f1f5f9;
  }
  
  .connector-fill {
    position: absolute;
    top: 0; left: 0; bottom: 0;
    width: 100%;
    border-radius: 99px;
    transition: width 0.9s cubic-bezier(0.4,0,0.2,1);
  }

  .stepper-node {
    position: relative;
    z-index: 10;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .node-circle {
    position: relative;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid;
    transition: all 0.5s cubic-bezier(0.4,0,0.2,1);
  }

  .node-label {
    position: absolute;
    top: 44px;
    font-size: 8px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    white-space: nowrap;
    transition: color 0.5s ease;
  }

  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(0,0,0,0.05);
    border-radius: 10px;
  }

  @keyframes halo-pulse {
    0%, 100% { opacity: 0.45; transform: scale(1); }
    50%       { opacity: 0.9;  transform: scale(1.35); }
  }
</style>
