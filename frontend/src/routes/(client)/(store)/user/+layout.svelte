<script lang="ts">
  import { authStore } from '$lib/state/authStore.svelte';
  import { goto } from '$app/navigation';
  import { fade } from 'svelte/transition';

  let { children } = $props();
  let isChecking = $state(true);

  // SSR đã chặn pre-render trong hooks.server.ts.
  // Guard này xử lý SPA navigation (khi user logout trong lúc đang ở /user/*)
  $effect(() => {
    if (!authStore.isAuthenticated) {
      goto('/');
    } else {
      isChecking = false;
    }
  });

  // R00: Lắng nghe sự kiện auth:logout từ authStore để navigate.
  // Store không được tự navigate (Zero-Hydration principle).
  // Dùng $effect để đảm bảo chỉ chạy ở Client và tự động cleanup.
  $effect(() => {
    const handleLogout = () => goto('/');
    window.addEventListener('auth:logout', handleLogout);
    return () => window.removeEventListener('auth:logout', handleLogout);
  });
</script>

{#if !isChecking && authStore.isAuthenticated}
  <div in:fade={{ duration: 400 }}>
    {@render children()}
  </div>
{:else}
  <!-- Global Loading State for Auth Verification -->
  <div class="fixed inset-0 bg-white z-[9999] flex flex-col items-center justify-center gap-6">
    <div class="w-12 h-12 border-2 border-stone-100 border-t-luxury-copper rounded-full animate-spin"></div>
    <p class="text-[10px] font-black tracking-[0.3em] text-stone-400 animate-pulse">Đang xác thực bảo mật...</p>
  </div>
{/if}
