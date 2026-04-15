<script lang="ts">
  import { apiClient } from '$lib/utils/apiClient';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { onMount } from 'svelte';
  import { Plus, MapPin } from 'lucide-svelte';
  import AddressList from './AddressList.svelte';
  import AddressForm from './AddressForm.svelte';
  import { fade } from 'svelte/transition';

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

  let addresses = $state<Address[]>([]);
  let isLoading = $state(true);
  let showForm = $state(false);

  onMount(async () => {
    try {
      const profile = await apiClient.get<{ extra_metadata?: { addresses?: Address[] } }>('/api/v1/client/user/profile');
      addresses = profile?.extra_metadata?.addresses || [];
    } catch (e) {
      addresses = authStore.user?.extra_metadata?.addresses || [];
    } finally {
      isLoading = false;
    }
  });

  async function handleDelete(id: string) {
    if (!confirm('Xóa địa chỉ này?')) return;
    const updated = addresses.filter(a => a.id !== id);
    await updateApi(updated);
  }

  async function setAsDefault(id: string) {
    const updated = addresses.map(a => ({ ...a, isDefault: a.id === id }));
    await updateApi(updated);
  }

  async function updateApi(updated: Address[]) {
    try {
      await apiClient.patch('/api/v1/client/user/profile', {
        extra_metadata: { ...authStore.user?.extra_metadata, addresses: updated }
      });
      authStore.syncUser({ extra_metadata: { ...(authStore.user?.extra_metadata || {}), addresses: updated } });
      addresses = updated;
      ui.showToast('Cập nhật thành công', 'success');
    } catch (e) {
      ui.showToast('Lỗi cập nhật', 'error');
    }
  }
</script>

<div class="space-y-4" in:fade>
  {#if showForm}
    <AddressForm bind:addresses onUpdate={(updated) => { addresses = updated; showForm = false; }} />
  {:else}
    <button onclick={() => showForm = true} class="w-full flex items-center justify-center gap-2 py-3 bg-stone-900 text-white text-[11px] font-bold uppercase tracking-widest hover:bg-luxury-copper">
      <Plus class="w-4 h-4" /> Thêm địa chỉ mới
    </button>
    {#if isLoading}
        <div class="py-10 text-center text-stone-400 text-[11px]">Đang tải...</div>
    {:else}
        <AddressList {addresses} onEdit={(a) => {}} onDelete={handleDelete} onSetDefault={setAsDefault} />
    {/if}
  {/if}
</div>
