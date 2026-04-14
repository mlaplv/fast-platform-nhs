<script lang="ts">
  import UserLayout from '$lib/components/storefront/user/UserLayout.svelte';
  import { apiClient } from '$lib/utils/apiClient';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { fade, fly, slide } from 'svelte/transition';
  import { onMount } from 'svelte';
  import { Plus, MapPin, Phone, User, Trash2, Edit3, CheckCircle2 } from 'lucide-svelte';
  import divisions from '$lib/data/vn_divisions.json';
  import SearchableDropdown from '$lib/components/storefront/user/SearchableDropdown.svelte';

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

  // Elite V3.1: Khởi đầu rỗng, load từ API trong onMount — đảm bảo fresh data sau mọi lần F5.
  // Không dùng authStore trực tiếp vì localStorage có thể stale.
  let addresses = $state<Address[]>([]);
  let isLoading = $state(true);
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

  // Elite V3.1: Fetch fresh profile from API on mount — bảo đảm data đúng sau mọi lần F5
  onMount(async () => {
    try {
      const profile = await apiClient.get<{ extra_metadata?: { addresses?: Address[] } }>('/api/v1/client/user/profile');
      const fresh = profile?.extra_metadata?.addresses;
      if (Array.isArray(fresh)) {
        addresses = fresh;
        // Sync vào authStore để đồng bộ localStorage
        authStore.syncUser({ extra_metadata: { ...(authStore.user?.extra_metadata || {}), addresses: fresh } });
      }
    } catch (e) {
      // Fallback an toàn: dùng data trong authStore nếu API thất bại
      addresses = authStore.user?.extra_metadata?.addresses || [];
      console.warn('[Address] API fetch failed, falling back to local cache:', e);
    } finally {
      isLoading = false;
    }
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

  function handleEdit(addr: Address) {
    name = addr.name;
    phone = addr.phone;
    address = addr.address;
    city = addr.city;
    district = addr.district;
    ward = addr.ward;
    isDefault = addr.isDefault;
    editingId = addr.id;
    showForm = true;
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
        // Reset other defaults
        updatedAddresses = updatedAddresses.map(a => ({ ...a, isDefault: false }));
      } else if (updatedAddresses.length === 0) {
        // First address is always default
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

      // Elite V3.1: Sync authStore → cập nhật localStorage để lần F5 tiếp theo không stale
      authStore.syncUser({
        extra_metadata: {
          ...(authStore.user?.extra_metadata || {}),
          addresses: updatedAddresses
        }
      });

      addresses = updatedAddresses;
      ui.showToast('Địa chỉ đã được cập nhật thành công! ✨', 'success');
      resetForm();
    } catch (e) {
      ui.showToast('Lỗi khi lưu địa chỉ.', 'error');
    } finally {
      isSaving = false;
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Bạn có chắc chắn muốn xóa địa chỉ này không?')) return;

    try {
      const updatedAddresses = addresses.filter(a => a.id !== id);

      // If we deleted a default address, set another one as default if exists
      if (addresses.find(a => a.id === id)?.isDefault && updatedAddresses.length > 0) {
        updatedAddresses[0].isDefault = true;
      }

      await apiClient.patch('/api/v1/client/user/profile', {
        extra_metadata: {
          ...authStore.user?.extra_metadata,
          addresses: updatedAddresses
        }
      });

      // Elite V3.1: Sync authStore sau delete
      authStore.syncUser({
        extra_metadata: {
          ...(authStore.user?.extra_metadata || {}),
          addresses: updatedAddresses
        }
      });

      addresses = updatedAddresses;
      ui.showToast('Đã xóa địa chỉ.', 'info');
    } catch (e) {
      ui.showToast('Lỗi khi xóa địa chỉ.', 'error');
    }
  }

  async function setAsDefault(id: string) {
    try {
      const updatedAddresses = addresses.map(a => ({
        ...a,
        isDefault: a.id === id
      }));

      await apiClient.patch('/api/v1/client/user/profile', {
        extra_metadata: {
          ...authStore.user?.extra_metadata,
          addresses: updatedAddresses
        }
      });

      // Elite V3.1: Sync authStore sau set default
      authStore.syncUser({
        extra_metadata: {
          ...(authStore.user?.extra_metadata || {}),
          addresses: updatedAddresses
        }
      });

      addresses = updatedAddresses;
      ui.showToast('Đã thiết lập địa chỉ mặc định.', 'success');
    } catch (e) {
      ui.showToast('Lỗi khi thiết lập địa chỉ.', 'error');
    }
  }
</script>

<UserLayout>
  <div class="space-y-8" in:fade>
    <div class="flex items-center justify-between border-b border-stone-100 pb-5">
      <div>
        <h1 class="text-xl font-serif italic text-stone-800 tracking-wide">Địa chỉ của tôi</h1>
        <p class="text-[13px] text-stone-400 mt-1 uppercase tracking-widest">Quản lý địa chỉ nhận hàng của bạn</p>
      </div>

      {#if !showForm}
        <button
          onclick={() => showForm = true}
          class="flex items-center gap-2 px-6 py-2.5 bg-stone-900 text-white hover:bg-luxury-copper transition-all duration-500 shadow-sm"
        >
          <Plus class="w-4 h-4" />
          <span class="text-[11px] font-bold uppercase tracking-widest">Thêm địa chỉ mới</span>
        </button>
      {/if}
    </div>

    {#if showForm}
      <div class="bg-stone-50/50 p-8 border border-stone-100 rounded-sm space-y-8" in:fly={{ y: 20 }}>
        <div class="flex items-center justify-between">
          <h2 class="text-sm font-bold uppercase tracking-[2px] text-stone-600">
            {editingId ? 'Chỉnh sửa địa chỉ' : 'Địa chỉ mới'}
          </h2>
          <button onclick={resetForm} class="text-stone-400 hover:text-stone-600 transition-colors">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div class="space-y-2">
            <label class="text-[10px] uppercase tracking-widest text-stone-400 font-bold">Họ và tên</label>
            <input
              type="text"
              bind:value={name}
              placeholder="Nhập họ tên người nhận"
              class="w-full h-11 border-b border-stone-200 bg-transparent outline-none focus:border-luxury-copper transition-colors text-stone-800 placeholder:text-stone-300"
            />
          </div>
          <div class="space-y-2">
            <label class="text-[10px] uppercase tracking-widest text-stone-400 font-bold">Số điện thoại</label>
            <input
              type="text"
              bind:value={phone}
              placeholder="Nhập số điện thoại"
              class="w-full h-11 border-b border-stone-200 bg-transparent outline-none focus:border-luxury-copper transition-colors text-stone-800 placeholder:text-stone-300"
            />
          </div>
        </div>

        <div class="space-y-2">
          <label class="text-[10px] uppercase tracking-widest text-stone-400 font-bold">Địa chỉ cụ thể</label>
          <input
            type="text"
            bind:value={address}
            placeholder="Số nhà, tên đường..."
            class="w-full h-11 border-b border-stone-200 bg-transparent outline-none focus:border-luxury-copper transition-colors text-stone-800 placeholder:text-stone-300"
          />
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div class="space-y-2">
            <label class="text-[10px] uppercase tracking-widest text-stone-400 font-bold">Tỉnh / Thành phố</label>
            <SearchableDropdown
              bind:value={city}
              options={divisions.filter(d => d.name).map(d => d.name)}
              placeholder="Chọn tỉnh/thành"
              onChange={() => ward = ''}
            />
          </div>
          <div class="space-y-2">
            <label class="text-[10px] uppercase tracking-widest text-stone-400 font-bold">Phường / Xã</label>
            <SearchableDropdown
              bind:value={ward}
              options={currentWards}
              placeholder="Chọn phường/xã"
              disabled={!city}
              getBadge={getWardBadge}
            />
          </div>
        </div>

        <div class="flex items-center gap-3">
          <label class="flex items-center gap-3 cursor-pointer group">
            <div class="w-5 h-5 border border-stone-300 flex items-center justify-center transition-all group-hover:border-luxury-copper {isDefault ? 'border-luxury-copper bg-luxury-copper text-white' : ''}">
              {#if isDefault}
                <CheckCircle2 class="w-3.5 h-3.5" />
              {/if}
            </div>
            <input type="checkbox" bind:checked={isDefault} class="hidden" />
            <span class="text-[12px] text-stone-500 uppercase tracking-widest">Đặt làm địa chỉ mặc định</span>
          </label>
        </div>

        <div class="pt-4 flex justify-end gap-4">
          <button
            onclick={resetForm}
            class="px-8 py-2.5 border border-stone-200 text-stone-500 hover:bg-stone-50 transition-colors text-[11px] font-bold uppercase tracking-widest"
          >
            Trở lại
          </button>
          <button
            onclick={handleSave}
            disabled={isSaving}
            class="px-10 py-2.5 bg-stone-900 text-white hover:bg-luxury-copper transition-all duration-500 shadow-lg disabled:opacity-50 text-[11px] font-bold uppercase tracking-widest"
          >
            {isSaving ? 'Đang lưu...' : 'Hoàn thành'}
          </button>
        </div>
      </div>
    {:else}
      <div class="space-y-4">
        {#if isLoading}
          <!-- Elite V3.1: Skeleton loading — tránh flash "rỗng" trong khi API fetch -->
          <div class="space-y-4" in:fade>
            {#each [1, 2] as _}
              <div class="bg-white p-6 border border-stone-100 animate-pulse">
                <div class="h-4 bg-stone-100 rounded w-1/3 mb-3"></div>
                <div class="h-3 bg-stone-100 rounded w-2/3 mb-2"></div>
                <div class="h-3 bg-stone-100 rounded w-1/2"></div>
              </div>
            {/each}
          </div>
        {:else if addresses.length === 0}
          <div class="py-20 text-center border-2 border-dashed border-stone-100 rounded-lg">
            <div class="w-16 h-16 bg-stone-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <MapPin class="w-8 h-8 text-stone-200" />
            </div>
            <p class="text-stone-400 text-sm italic font-serif">Bạn chưa có địa chỉ nào được lưu.</p>
          </div>
        {:else}
          {#each addresses as addr (addr.id)}
            <div
              class="group relative bg-white p-6 border border-stone-100 hover:border-stone-200 transition-all duration-500 hover:shadow-[0_10px_30px_rgba(0,0,0,0.03)]"
              in:fade
            >
              <div class="flex flex-col md:flex-row md:items-start justify-between gap-6">
                <div class="flex-1 space-y-4">
                  <div class="flex items-center gap-3">
                    <span class="text-[14px] font-bold text-stone-800 uppercase tracking-wider">{addr.name}</span>
                    <div class="w-px h-3 bg-stone-200"></div>
                    <span class="text-[13px] text-stone-500">{addr.phone}</span>
                    {#if addr.isDefault}
                      <span class="px-2 py-0.5 border border-luxury-copper text-luxury-copper text-[9px] font-black uppercase tracking-widest ml-2">Mặc định</span>
                    {/if}
                  </div>

                  <div class="space-y-1 text-[13px] text-stone-600 leading-relaxed">
                    <p>{addr.address}</p>
                    <p>{addr.ward}, {addr.city}</p>
                  </div>
                </div>

                <div class="flex flex-col items-end gap-3">
                  <div class="flex items-center gap-4">
                    <button
                      onclick={() => handleEdit(addr)}
                      class="text-[11px] text-stone-400 hover:text-luxury-copper transition-colors uppercase tracking-widest font-bold flex items-center gap-1.5"
                    >
                      <Edit3 class="w-3 h-3" /> Sửa
                    </button>
                    {#if !addr.isDefault}
                      <button
                        onclick={() => handleDelete(addr.id)}
                        class="text-[11px] text-stone-400 hover:text-red-400 transition-colors uppercase tracking-widest font-bold flex items-center gap-1.5"
                      >
                        <Trash2 class="w-3 h-3" /> Xóa
                      </button>
                    {/if}
                  </div>

                  {#if !addr.isDefault}
                    <button
                      onclick={() => setAsDefault(addr.id)}
                      class="px-4 py-1.5 border border-stone-200 text-[10px] text-stone-500 hover:border-stone-800 hover:text-stone-800 transition-all uppercase tracking-widest font-bold"
                    >
                      Thiết lập mặc định
                    </button>
                  {/if}
                </div>
              </div>
            </div>
          {/each}
        {/if}
      </div>
    {/if}

    <!-- Aesthetic Footer Note -->
    <div class="pt-12 text-center">
       <div class="inline-flex items-center gap-4 text-stone-300">
          <div class="h-px w-12 bg-stone-100"></div>
          <span class="text-[10px] uppercase tracking-[4px] italic font-serif">Micsmo Zen Living</span>
          <div class="h-px w-12 bg-stone-100"></div>
       </div>
    </div>
  </div>
</UserLayout>
