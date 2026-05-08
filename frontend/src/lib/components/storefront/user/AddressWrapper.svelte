<script lang="ts">
  import { apiClient } from '$lib/utils/apiClient';
  import type UserAddress } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { onMount } from 'svelte';
  import Plus from "@lucide/svelte/icons/plus";
  import MapPin from "@lucide/svelte/icons/map-pin";
  import AddressList from './AddressList.svelte';
  import AddressForm from './AddressForm.svelte';
  import { fade } from 'svelte/transition';

  const ui = getClientUi();

  let addresses = $state<UserAddress[]>([]);
  let isLoading = $state(true);
  let showForm = $state(false);
  let selectedAddress = $state<UserAddress | null>(null);

  onMount(async () => {
    try {
      const profile = await apiClient.get<{ extra_metadata?: { addresses?: UserAddress[] } }>('/api/v1/client/user/profile');
      addresses = profile?.extra_metadata?.addresses || [];
    } catch (e: unknown) {
      addresses = authStore.user?.extra_metadata?.addresses || [];
    } finally {
      isLoading = false;
    }
  });

  function handleEdit(addr: UserAddress) {
    selectedAddress = addr;
    showForm = true;
  }

  function handleAddNew() {
    selectedAddress = null;
    showForm = true;
  }

  async function handleDelete(id: string) {
    if (!confirm('Xóa địa chỉ này?')) return;
    const updated = addresses.filter(a => a.id !== id);
    await updateApi(updated);
  }

  async function setAsDefault(id: string) {
    const updated = addresses.map(a => ({ ...a, isDefault: a.id === id }));
    await updateApi(updated);
  }

  async function updateApi(updated: UserAddress[]) {
    try {
      await apiClient.patch('/api/v1/client/user/profile', {
        extra_metadata: { ...authStore.user?.extra_metadata, addresses: updated }
      });
      authStore.syncUser({ extra_metadata: { ...(authStore.user?.extra_metadata || {}), addresses: updated } });
      addresses = updated;
      ui.showToast('Cập nhật thành công', 'success');
    } catch (e: unknown) {
      ui.showToast('Lỗi cập nhật', 'error');
    }
  }
</script>

<div class="space-y-8" in:fade>
  {#if showForm}
    <AddressForm
      bind:addresses
      initialData={selectedAddress}
      onUpdate={(updated) => { addresses = updated; showForm = false; selectedAddress = null; }}
      onCancel={() => { showForm = false; selectedAddress = null; }}
    />
  {:else}
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-stone-100 pb-6">
      <div class="space-y-1">
        <h2 class="text-[12px] font-black uppercase tracking-[3px] text-stone-800">Sổ địa chỉ</h2>
        <p class="text-[10px] text-stone-400 uppercase tracking-widest">Lưu tối đa 10 địa chỉ nhận hàng</p>
      </div>
      <button
        onclick={handleAddNew}
        class="group relative px-8 py-3 bg-stone-900 text-white overflow-hidden transition-all duration-500 hover:shadow-lg"
      >
        <div class="absolute inset-0 bg-luxury-copper translate-y-full group-hover:translate-y-0 transition-transform duration-500"></div>
        <div class="relative z-10 flex items-center gap-2">
          <Plus class="w-3.5 h-3.5" />
          <span class="text-[10px] font-bold uppercase tracking-widest">Thêm địa chỉ</span>
        </div>
      </button>
    </div>

    {#if isLoading}
        <div class="py-20 flex flex-col items-center justify-center space-y-4">
          <div class="w-8 h-8 border-2 border-luxury-copper border-t-transparent animate-spin rounded-full"></div>
          <p class="text-[10px] text-stone-400 uppercase tracking-widest animate-pulse">Đang tải dữ liệu...</p>
        </div>
    {:else}
        <AddressList
          {addresses}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onSetDefault={setAsDefault}
        />
    {/if}

    <div class="pt-10 flex items-center justify-center gap-4 opacity-20">
       <div class="h-px w-12 bg-stone-300"></div>
       <MapPin class="w-4 h-4 text-stone-800" />
       <div class="h-px w-12 bg-stone-300"></div>
    </div>
  {/if}
</div>
