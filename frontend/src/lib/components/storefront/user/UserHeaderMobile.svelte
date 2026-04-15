<script lang="ts">
  import { Menu, Camera } from 'lucide-svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import { apiClient } from '$lib/utils/apiClient';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';

  interface Props {
    title: string;
    isMenuOpen: boolean;
  }
  let { title, isMenuOpen = $bindable() }: Props = $props();
  const ui = getClientUi();
  let fileInput: HTMLInputElement;

  // Handle avatar upload on mobile menu
  async function handleAvatarUpload(e: Event) {
    const target = e.target as HTMLInputElement;
    if (!target.files || target.files.length === 0) return;

    const file = target.files[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await apiClient.upload<{ data: { avatar_url: string } }>('/api/v1/client/user/avatar', formData);
      authStore.syncUser({ avatar_url: res.data.avatar_url });
      ui.showToast('Cập nhật ảnh đại diện thành công! ✨', 'success');
    } catch (e) {
      ui.showToast('Lỗi khi cập nhật ảnh đại diện.', 'error');
      console.error(e);
    } finally {
      target.value = '';
    }
  }
</script>

<header class="fixed top-0 left-0 w-full z-[var(--z-header)] flex items-center justify-between p-2 bg-white/90 backdrop-blur-md border-b border-gray-100 h-[48px]">
    <button onclick={() => history.back()} class="w-10 h-10 flex items-center justify-center">
        <svg class="w-6 h-6 text-gray-900" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" /></svg>
    </button>

    <div class="flex items-center gap-3">
        <!-- Avatar + Name -->
        <div class="flex items-center gap-2">
            <div class="relative w-8 h-8 rounded-full overflow-hidden border border-stone-100 bg-stone-50 shrink-0">
                {#if authStore.user?.avatar_url}
                    <img src={authStore.user.avatar_url} alt="Avatar" class="w-full h-full object-cover" />
                {:else}
                    <div class="w-full h-full flex items-center justify-center text-xs font-serif italic text-luxury-copper uppercase">
                        {authStore.user?.name?.charAt(0) || 'U'}
                    </div>
                {/if}
                <button
                    type="button"
                    class="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 hover:opacity-100 transition-opacity"
                    onclick={() => fileInput.click()}
                >
                    <Camera class="w-3 h-3 text-white" />
                </button>
            </div>
            <span class="text-xs font-black text-gray-900 uppercase tracking-tight truncate max-w-[80px]">
                {authStore.user?.name || 'Quý khách'}
            </span>
        </div>
    </div>

    <input
        type="file"
        accept="image/*"
        class="hidden"
        bind:this={fileInput}
        onchange={handleAvatarUpload}
    />

    <!-- Menu Button -->
    <button onclick={() => isMenuOpen = true} class="w-10 h-10 flex items-center justify-center">
        <Menu class="w-6 h-6 text-gray-900" />
    </button>
</header>
