<script lang="ts">
  import { slide } from 'svelte/transition';
  import vnDivisions from '$lib/data/vn_divisions.json';
  import SearchableCheckoutSelect from '$lib/components/storefront/ui/SearchableCheckoutSelect.svelte';
  import SimpleTiptap from '$lib/components/storefront/ui/SimpleTiptap.svelte';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import type { ProvinceData } from '$lib/types/commerce/checkout';
  
  interface FormState {
    name: string;
    phone: string;
    province: string;
    ward: string;
    street: string;
  }

  let { 
    form = $bindable(), 
    invalidFields, 
    showNote = $bindable(), 
    orderNote = $bindable(),
    lookupCustomer
  } = $props<{
    form: FormState;
    invalidFields: Set<string>;
    showNote: boolean;
    orderNote: string;
    lookupCustomer: () => void;
  }>();

  const cartStore = getCartStore();
  const validProvinces = (vnDivisions as unknown as ProvinceData[]).filter(p => p.id);

  const normalize = (s: string) => s.normalize('NFC').toLowerCase().trim();

  const currentWards = $derived.by(() => {
    if (!form.province) return [];
    const province = validProvinces.find(p => p.name === form.province);
    if (!province) return [];
    
    const wards = [...(province?.wards || [])];
    if (!province.has_express || !province.express_supported_wards?.length) return wards;
    
    const supported = province.express_supported_wards;
    return wards.sort((a, b) => {
      const aSupported = supported.some(w => normalize(w) === normalize(a));
      const bSupported = supported.some(w => normalize(w) === normalize(b));
      if (aSupported && !bSupported) return -1;
      if (!aSupported && bSupported) return 1;
      return 0;
    });
  });

  const selectedProvinceData = $derived(validProvinces.find(p => p.name === form.province));

  const getWardBadge = (wardName: string) => {
    if (!selectedProvinceData?.has_express || !selectedProvinceData.express_supported_wards) return null;
    const normWard = normalize(wardName);
    const isSupported = selectedProvinceData.express_supported_wards?.some(w => normalize(w) === normWard);
    if (!isSupported) return { text: 'Tiêu chuẩn', type: 'default' };
    return { text: 'Hỏa tốc 2h', type: 'success' };
  };
</script>

<div class="bg-white p-6 md:p-8 shadow-sm">
  <h2 class="text-lg font-black uppercase tracking-tighter flex items-center gap-3 mb-6">
    <span class="w-7 h-7 rounded-full bg-[#ee4d2d] text-white flex items-center justify-center text-xs italic">01</span>
    THÔNG TIN VẬN CHUYỂN
  </h2>

  <!-- Address Matrix -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
    <div class="space-y-1">
      <label class="text-[9px] font-black uppercase text-gray-400 ml-1">Họ và Tên</label>
      <input 
        type="text" 
        bind:value={form.name} 
        placeholder="Nhập họ tên người nhận..." 
        class="w-full bg-gray-50 border {invalidFields.has('name') ? 'border-red-500 ring-2 ring-red-500/10 field-error-shake' : 'border-gray-100'} px-4 py-3 text-sm focus:border-[#ee4d2d] outline-none font-bold text-gray-900" 
      />
    </div>
    <div class="space-y-1">
      <label class="text-[9px] font-black uppercase text-gray-400 ml-1">Số điện thoại</label>
      <input 
        type="tel" 
        bind:value={form.phone} 
        onblur={lookupCustomer} 
        placeholder="Số điện thoại liên hệ..." 
        class="w-full bg-gray-50 border {invalidFields.has('phone') ? 'border-red-500 ring-2 ring-red-500/10 field-error-shake' : 'border-gray-100'} px-4 py-3 text-sm focus:border-[#ee4d2d] outline-none font-bold text-gray-900" 
      />
    </div>
    <div class="space-y-1">
      <label class="text-[9px] font-black uppercase text-gray-400 ml-1">Tỉnh / Thành phố</label>
      <SearchableCheckoutSelect 
        bind:value={form.province} 
        options={validProvinces.map(p => p.name)} 
        placeholder="Chọn Tỉnh/Thành" 
        onChange={() => form.ward = ''}
      />
    </div>
    <div class="space-y-1">
      <label class="text-[9px] font-black uppercase text-gray-400 ml-1">Phường / Xã</label>
      <SearchableCheckoutSelect 
        bind:value={form.ward} 
        options={currentWards} 
        placeholder="Chọn Phường/Xã" 
        disabled={!form.province}
        getBadge={getWardBadge}
      />
    </div>
    <div class="md:col-span-2 space-y-1">
      <label class="text-[9px] font-black uppercase text-gray-400 ml-1">Địa chỉ chi tiết</label>
      <input 
        type="text" 
        bind:value={form.street} 
        placeholder="Số nhà, tên đường..." 
        class="w-full bg-gray-50 border {invalidFields.has('street') ? 'border-red-500 ring-2 ring-red-500/10 field-error-shake' : 'border-gray-100'} px-4 py-3 text-sm focus:border-[#ee4d2d] outline-none font-bold text-gray-900" 
      />
      
      <div class="pt-1">
        <div class="flex gap-4">
          <button
            type="button"
            onclick={() => showNote = !showNote}
            class="text-[9px] font-black uppercase text-[#ee4d2d] hover:underline flex items-center gap-1.5 transition-all"
          >
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
            {showNote ? 'THU GỌN GHI CHÚ' : 'THÊM GHI CHÚ ĐƠN HÀNG'}
          </button>

          <button
            type="button"
            onclick={() => cartStore.toggleGiftModal(true)}
            class="text-[9px] font-black uppercase text-[#ee4d2d] hover:underline flex items-center gap-1.5 transition-all"
          >
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" /></svg>
            {cartStore.giftInfo ? 'ĐÃ CẬP NHẬT QUÀ TẶNG' : 'THÊM QUÀ TẶNG / GÓI QUÀ'}
          </button>
        </div>
        
        {#if showNote}
          <div transition:slide class="mt-4">
            <SimpleTiptap 
              bind:content={orderNote}
              placeholder="Ghi chú về đơn hàng (ví dụ: giao giờ hành chính, gọi điện trước khi giao...)"
              limit={2000}
            />
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>
