<script lang="ts">
  import { browser } from '$app/environment';
  import { authStore } from '$lib/state/authStore.svelte';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { fade } from 'svelte/transition';

  let { children } = $props();
  let isChecking = $state(true);

  $effect(() => {
    if (browser) {
      if (!authStore.isAuthenticated) {
        goto('/');
      } else {
        isChecking = false;
      }
    }
  });

  onMount(() => {
    // Final safety check after hydration
    if (!authStore.isAuthenticated) {
      goto('/');
    } else {
      isChecking = false;
    }
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
    <p class="text-[10px] font-black uppercase tracking-[0.3em] text-stone-400 animate-pulse">Đang xác thực bảo mật...</p>
  </div>
{/if}
