<script lang="ts">
  import { Camera } from 'lucide-svelte';
  import { apiClient } from '$lib/utils/apiClient';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';

  interface Props {
    src?: string;
    name?: string;
    size?: 'xs' | 'sm' | 'lg';
    editable?: boolean;
    class?: string;
  }

  let {
    src = '',
    name = 'U',
    size = 'sm',
    editable = false,
    class: className = ''
  }: Props = $props();

  const ui = getClientUi();
  let fileInput: HTMLInputElement;
  let isUploading = $state(false);

  async function handleUpload(e: Event) {
    const target = e.target as HTMLInputElement;
    if (!target.files || target.files.length === 0) return;

    const file = target.files[0];
    const formData = new FormData();
    formData.append('file', file);

    isUploading = true;
    try {
      const res = await apiClient.upload<{ data: { avatar_url: string } }>('/api/v1/client/user/avatar', formData);
      authStore.syncUser({ avatar_url: res.data.avatar_url });
      ui.showToast('Cập nhật ảnh đại diện thành công! ✨', 'success');
    } catch (error) {
      ui.showToast('Lỗi khi cập nhật ảnh đại diện.', 'error');
      console.error(error);
    } finally {
      isUploading = false;
      target.value = '';
    }
  }

  const sizes = {
    xs: 'w-4 h-4 text-[6px]',
    sm: 'w-8 h-8 text-xs',
    lg: 'w-24 h-24 text-3xl'
  };
</script>

<div class="relative group {sizes[size]} {className}">
  <div class="w-full h-full rounded-full overflow-hidden border border-stone-100 bg-stone-50 shrink-0 {size === 'lg' ? 'border-2 shadow-sm transition-transform duration-700 group-hover:scale-105' : ''}">
    {#if src}
      <img {src} alt="Avatar" class="w-full h-full object-cover" />
    {:else}
      <div class="w-full h-full flex items-center justify-center font-serif italic text-luxury-copper uppercase {size === 'lg' ? 'bg-stone-50' : ''}">
        {name?.charAt(0) || 'U'}
      </div>
    {/if}
  </div>

  {#if editable && size !== 'xs'}
    <input
      type="file"
      accept="image/*"
      class="hidden"
      bind:this={fileInput}
      onchange={handleUpload}
    />

    {#if size === 'sm'}
      <button
        type="button"
        class="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 hover:opacity-100 transition-opacity rounded-full"
        onclick={() => fileInput.click()}
        disabled={isUploading}
      >
        <Camera class="w-3 h-3 text-white" />
      </button>
    {:else}
      <button
        type="button"
        class="absolute bottom-0 right-0 w-8 h-8 bg-stone-900 rounded-full flex items-center justify-center text-white border-2 border-white shadow-md hover:bg-luxury-copper transition-colors z-10"
        onclick={() => fileInput.click()}
        disabled={isUploading}
      >
        <Camera class="w-4 h-4" />
      </button>
    {/if}
  {/if}

  {#if isUploading}
    <div class="absolute inset-0 flex items-center justify-center bg-white/50 rounded-full">
      <div class="w-4 h-4 border-2 border-luxury-copper border-t-transparent animate-spin rounded-full"></div>
    </div>
  {/if}
</div>

<style>
  .text-luxury-copper {
    color: #c5a059;
  }
  .bg-luxury-copper {
    background-color: #c5a059;
  }
  .hover\:bg-luxury-copper:hover {
    background-color: #c5a059;
  }
</style>
