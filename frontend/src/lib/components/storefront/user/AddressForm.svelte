<script lang="ts">
  import { apiClient } from '$lib/utils/apiClient';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { Plus, MapPin, Phone, User, Trash2, Edit3, CheckCircle2 } from 'lucide-svelte';
  import divisions from '$lib/data/vn_divisions.json';
  import SearchableDropdown from './SearchableDropdown.svelte';
  import { fade, fly, slide } from 'svelte/transition';

  const ui = getClientUi();

  interface Address {
    id: string;
    name: string;
    phone: string;
    address: string;
    city: string;
    district?: string;
    ward: string;
    isDefault: boolean;
  }

  interface Props {
    addresses: Address[];
    onUpdate: (updatedAddresses: Address[]) => void;
  }

  let { addresses = $bindable(), onUpdate }: Props = $props();

  let showForm = $state(false);
  let isSaving = $state(false);
  let editingId = $state<string | null>(null);

  // Form states
  let name = $state('');
  let phone = $state('');
  let address = $state('');
  let city = $state('');
  let district = $state('');
  let ward = $state('');
  let isDefault = $state(false);

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

  function resetForm() {
    name = '';
    phone = '';
    address = '';
    city = '';
    district = '';
    ward = '';
    isDefault = false;
    editingId = null;
    showForm = false;
  }

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

      const newAddr: Address = {
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
      resetForm();
    } catch (e) {
      ui.showToast('Lỗi khi lưu địa chỉ.', 'error');
    } finally {
      isSaving = false;
    }
  }
</script>

<div class="space-y-4">
    {#if !showForm}
        <button
        onclick={() => showForm = true}
        class="w-full flex items-center justify-center gap-2 px-6 py-3 bg-stone-900 text-white hover:bg-luxury-copper transition-all duration-500 shadow-sm"
        >
        <Plus class="w-4 h-4" />
        <span class="text-[11px] font-bold uppercase tracking-widest">Thêm địa chỉ mới</span>
        </button>
    {:else}
        <div class="bg-stone-50/50 p-6 border border-stone-100 rounded-sm space-y-6" in:fly={{ y: 20 }}>
            <h2 class="text-sm font-bold uppercase tracking-[2px] text-stone-600">
                {editingId ? 'Chỉnh sửa địa chỉ' : 'Địa chỉ mới'}
            </h2>

            <div class="space-y-4">
                <input type="text" bind:value={name} placeholder="Họ và tên" class="w-full h-11 border-b border-stone-200 bg-transparent outline-none focus:border-luxury-copper" />
                <input type="text" bind:value={phone} placeholder="Số điện thoại" class="w-full h-11 border-b border-stone-200 bg-transparent outline-none focus:border-luxury-copper" />
                <input type="text" bind:value={address} placeholder="Địa chỉ cụ thể" class="w-full h-11 border-b border-stone-200 bg-transparent outline-none focus:border-luxury-copper" />
                <SearchableDropdown bind:value={city} options={divisions.map(d => d.name)} placeholder="Chọn tỉnh/thành" />
                <SearchableDropdown bind:value={ward} options={currentWards} placeholder="Chọn phường/xã" disabled={!city} />
            </div>

            <button onclick={handleSave} class="w-full py-3 bg-stone-900 text-white text-[11px] font-bold uppercase tracking-widest">
                {isSaving ? 'Đang lưu...' : 'Hoàn thành'}
            </button>
        </div>
    {/if}
</div>