<script lang="ts">
  import { apiClient } from '$lib/utils/apiClient';
  import { authStore, type UserAddress } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import Plus from "@lucide/svelte/icons/plus";
  import MapPin from "@lucide/svelte/icons/map-pin";
  import Phone from "@lucide/svelte/icons/phone";
  import User from "@lucide/svelte/icons/user";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Edit3 from "@lucide/svelte/icons/edit-3";
  import CheckCircle2 from "@lucide/svelte/icons/check-circle-2";
  import divisionsRaw from '$lib/data/vn_divisions.json';
  import type { ProvinceData } from '$lib/types/commerce/checkout';
  import SearchableDropdown from './SearchableDropdown.svelte';
  import { fade, fly, slide } from 'svelte/transition';

  const ui = getClientUi();
  const divisions = divisionsRaw as unknown as ProvinceData[];

  interface Props {
    addresses: UserAddress[];
    initialData?: UserAddress | null;
    onUpdate: (updatedAddresses: UserAddress[]) => void;
    onCancel: () => void;
  }

  let { addresses = $bindable(), initialData = null, onUpdate, onCancel }: Props = $props();

  let isSaving = $state(false);
  let editingId = $state<string | null>(initialData?.id || null);

  // Form states
  let name = $state(initialData?.name || '');
  let phone = $state(initialData?.phone || '');
  let address = $state(initialData?.address || '');
  let city = $state(initialData?.city || '');
  let district = $state(initialData?.district || '');
  let ward = $state(initialData?.ward || '');
  let isDefault = $state(initialData?.isDefault || false);

  const selectedProvinceData = $derived(divisions.find(d => d.name === city));
  const normalize = (s: string) => s.normalize('NFC').toLowerCase().trim();

  const getWardBadge = (wardName: string) => {
    if (!selectedProvinceData?.has_express) return null;
    const normWard = normalize(wardName);
    const isSupported = selectedProvinceData.express_supported_wards?.some(w => normalize(w) === normWard);
    if (!isSupported) return { text: 'Tiêu chuẩn', type: 'default' } as const;
    return { text: 'Hỏa tốc 2h', type: 'success' } as const;
  };

  const currentWards = $derived.by(() => {
    const wards = [...(selectedProvinceData?.wards || [])];
    if (!selectedProvinceData?.has_express || !selectedProvinceData.express_supported_wards?.length) return wards;

    const supported = selectedProvinceData.express_supported_wards;
    return wards.sort((a, b) => {
      const aSupported = supported.some(w => normalize(w) === normalize(a));
      const bSupported = supported.some(w => normalize(w) === normalize(b));
      if (aSupported && !bSupported) return -1;
      if (!aSupported && bSupported) return 1;
      return 0;
    });
  });

  async function handleSave() {
    if (!name || !phone || !address || !city || !ward) {
      ui.showToast('Vui lòng điền đầy đủ thông tin địa chỉ.', 'warning');
      return;
    }

    isSaving = true;
    try {
      let updatedAddresses = [...addresses];

      if (isDefault) {
        updatedAddresses = updatedAddresses.map(a => ({ ...a, isDefault: false }));
      } else if (updatedAddresses.length === 0) {
        isDefault = true;
      }

      const newAddr: UserAddress = {
        id: editingId || crypto.randomUUID(),
        name,
        phone,
        address,
        city,
        ward,
        isDefault
      };

      if (editingId) {
        updatedAddresses = updatedAddresses.map(a => a.id === editingId ? newAddr : a);
      } else {
        updatedAddresses.push(newAddr);
      }

      await apiClient.patch('/api/v1/client/user/profile', {
        extra_metadata: {
          ...authStore.user?.extra_metadata,
          addresses: updatedAddresses
        }
      });

      authStore.syncUser({
        extra_metadata: {
          ...(authStore.user?.extra_metadata || {}),
          addresses: updatedAddresses
        }
      });

      onUpdate(updatedAddresses);
      ui.showToast('Địa chỉ đã được cập nhật thành công! ✨', 'success');
    } catch (e: unknown) {
      ui.showToast('Lỗi khi lưu địa chỉ.', 'error');
    } finally {
      isSaving = false;
    }
  }
</script>

<div class="space-y-10 py-6" in:fade={{ duration: 400 }}>
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 rounded-full bg-luxury-copper/10 flex items-center justify-center">
        <MapPin class="w-4 h-4 text-luxury-copper" />
      </div>
      <h3 class="text-xl font-serif italic text-stone-800 leading-none">
        {editingId ? 'Chỉnh sửa địa chỉ' : 'Địa chỉ mới'}
      </h3>
    </div>
    <p class="text-[9px] tracking-widest text-stone-400 font-bold">Shipping Address</p>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-10">
    <!-- Identity Group -->
    <div class="space-y-8">
      <div class="space-y-1.5 group">
        <label for="name" class="text-[10px] tracking-widest text-stone-400 font-bold group-focus-within:text-luxury-copper transition-colors">Họ và tên người nhận</label>
        <div class="relative">
          <input
            id="name"
            type="text"
            bind:value={name}
            placeholder="Nhập họ tên đầy đủ..."
            class="w-full h-12 bg-transparent border-b border-stone-200 outline-none focus:border-luxury-copper transition-all text-stone-800 font-medium placeholder:text-stone-200"
          />
          <User class="absolute right-0 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-stone-200" />
        </div>
      </div>

      <div class="space-y-1.5 group">
        <label for="phone" class="text-[10px] tracking-widest text-stone-400 font-bold group-focus-within:text-luxury-copper transition-colors">Số điện thoại liên hệ</label>
        <div class="relative">
          <input
            id="phone"
            type="tel"
            bind:value={phone}
            placeholder="0xx xxxx xxx"
            class="w-full h-12 bg-transparent border-b border-stone-200 outline-none focus:border-luxury-copper transition-all text-stone-800 font-medium placeholder:text-stone-200"
          />
          <Phone class="absolute right-0 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-stone-200" />
        </div>
      </div>
    </div>

    <!-- Location Group -->
    <div class="space-y-8">
      <div class="space-y-4">
        <div class="space-y-1.5 group">
           <label for="addr-city" class="text-[10px] tracking-widest text-stone-400 font-bold">Tỉnh / Thành phố</label>
           <SearchableDropdown id="addr-city" bind:value={city} options={divisions.map(d => d.name)} placeholder="Chọn tỉnh/thành..." />
        </div>

        <div class="space-y-1.5 group">
           <label for="addr-ward" class="text-[10px] tracking-widest text-stone-400 font-bold">Quận / Huyện / Phường / Xã</label>
           <SearchableDropdown id="addr-ward" bind:value={ward} options={currentWards} placeholder="Chọn khu vực..." disabled={!city} />
        </div>
      </div>

      <div class="space-y-1.5 group">
        <label for="address" class="text-[10px] tracking-widest text-stone-400 font-bold group-focus-within:text-luxury-copper transition-colors">Địa chỉ cụ thể (Số nhà, Tên đường)</label>
        <input
          id="address"
          type="text"
          bind:value={address}
          placeholder="Nhập địa chỉ của Quý khách..."
          class="w-full h-12 bg-transparent border-b border-stone-200 outline-none focus:border-luxury-copper transition-all text-stone-800 font-medium placeholder:text-stone-200"
        />
      </div>
    </div>
  </div>

  <div class="pt-4">
    <label for="addr-default" class="flex items-center gap-3 cursor-pointer group/check w-fit">
      <div class="w-5 h-5 rounded-md border border-stone-200 flex items-center justify-center transition-all group-hover/check:border-luxury-copper {isDefault ? 'bg-stone-800 border-stone-800 shadow-sm' : ''}">
        {#if isDefault}
          <div in:fade>
            <CheckCircle2 class="w-3.5 h-3.5 text-white" />
          </div>
        {/if}
      </div>
      <input id="addr-default" type="checkbox" bind:checked={isDefault} class="hidden" />
      <span class="text-[12px] font-bold text-stone-600 tracking-widest group-hover/check:text-stone-800 transition-colors">Đặt làm địa chỉ mặc định</span>
    </label>
  </div>

  <div class="pt-10 flex flex-col md:flex-row items-center gap-4">
    <button
      onclick={handleSave}
      disabled={isSaving}
      class="w-full md:w-auto md:px-16 py-4 bg-stone-800 text-white relative group overflow-hidden transition-all duration-700 hover:shadow-[0_20px_40px_rgba(0,0,0,0.2)] disabled:opacity-50"
    >
      <div class="absolute inset-0 bg-luxury-copper translate-x-[-100%] group-hover:translate-x-0 transition-transform duration-700 ease-out"></div>
      <span class="relative z-10 text-[11px] tracking-[5px] font-black">
        {isSaving ? 'Đang lưu...' : 'Lưu địa chỉ'}
      </span>
    </button>

    <button
      onclick={onCancel}
      class="w-full md:w-auto px-10 py-4 text-[11px] tracking-[3px] font-bold text-stone-400 hover:text-stone-800 transition-colors"
    >
      Hủy bỏ
    </button>
  </div>
</div>
