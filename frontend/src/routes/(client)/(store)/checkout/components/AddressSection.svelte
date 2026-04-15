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

<div class="bg-white p-4 shadow-sm border border-gray-100 rounded-lg">
  <h2 class="text-sm font-bold uppercase text-gray-800 flex items-center gap-2 mb-4">
    <svg class="w-4 h-4 text-[#fe2c55]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
    Thông tin vận chuyển
  </h2>

  <!-- Address Matrix (Compact) -->
  <div class="space-y-3">
    <div class="grid grid-cols-2 gap-3">
      <div class="space-y-1">
        <label class="text-[9px] font-bold uppercase text-gray-500 ml-1">Họ và Tên</label>
        <input 
          type="text" 
          bind:value={form.name} 
          placeholder="Tên người nhận" 
          class="w-full bg-gray-50 border {invalidFields.has('name') ? 'border-red-500 ring-1 ring-red-500/20' : 'border-gray-200'} px-3 py-2 text-[13px] focus:border-[#fe2c55] focus:bg-white outline-none font-medium text-gray-900 rounded" 
        />
      </div>
      <div class="space-y-1">
        <label class="text-[9px] font-bold uppercase text-gray-500 ml-1">Số điện thoại</label>
        <input 
          type="tel" 
          bind:value={form.phone} 
          onblur={lookupCustomer} 
          placeholder="Số điện thoại" 
          class="w-full bg-gray-50 border {invalidFields.has('phone') ? 'border-red-500 ring-1 ring-red-500/20' : 'border-gray-200'} px-3 py-2 text-[13px] focus:border-[#fe2c55] focus:bg-white outline-none font-medium text-gray-900 rounded" 
        />
      </div>
    </div>
    
    <div class="space-y-3">
      <div class="space-y-1">
        <label class="text-[9px] font-bold uppercase text-gray-500 ml-1">Tỉnh / Thành phố</label>
        <SearchableCheckoutSelect 
          bind:value={form.province} 
          options={validProvinces.map(p => p.name)} 
          placeholder="Chọn tỉnh/thành..." 
          onChange={() => form.ward = ''}
        />
      </div>
      <div class="space-y-1">
        <label class="text-[9px] font-bold uppercase text-gray-500 ml-1">Phường / Quận / Xã</label>
        <SearchableCheckoutSelect 
          bind:value={form.ward} 
          options={currentWards} 
          placeholder="Chọn phường/xã..." 
          disabled={!form.province}
          getBadge={getWardBadge}
        />
      </div>
    </div>

    <div class="space-y-1">
      <label class="text-[9px] font-bold uppercase text-gray-500 ml-1">Địa chỉ chi tiết</label>
      <input 
        type="text" 
        bind:value={form.street} 
        placeholder="Số nhà, tên đường..." 
        class="w-full bg-gray-50 border {invalidFields.has('street') ? 'border-red-500 ring-1 ring-red-500/20' : 'border-gray-200'} px-3 py-2 text-[13px] focus:border-[#fe2c55] focus:bg-white outline-none font-medium text-gray-900 rounded" 
      />
      
      <div class="pt-2">
        <div class="flex gap-4">
          <button
            type="button"
            onclick={() => showNote = !showNote}
            class="text-[10px] font-bold uppercase text-gray-500 hover:text-[#fe2c55] flex items-center gap-1 transition-colors"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
            {showNote ? 'Thu gọn ghi chú' : 'Thêm ghi chú'}
          </button>

          <button
            type="button"
            onclick={() => cartStore.toggleGiftModal(true)}
            class="text-[10px] font-bold uppercase text-gray-500 hover:text-[#fe2c55] flex items-center gap-1 transition-colors"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" /></svg>
            {cartStore.giftInfo ? 'Đã cập nhật quà' : 'Tặng / Gói quà'}
          </button>
        </div>
        
        {#if showNote}
          <div transition:slide class="mt-3">
             <input type="text" bind:value={orderNote} placeholder="VD: Giao trong giờ hành chính..." class="w-full bg-gray-50 border border-gray-200 px-3 py-2 text-[12px] focus:border-[#fe2c55] focus:bg-white outline-none font-medium text-gray-800 rounded" />
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>
