<script>
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import UserDashboardContent from '$lib/components/storefront/user/UserDashboardContent.svelte';

  const ui = getClientUi();

<script>
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import UserDashboardContent from '$lib/components/storefront/user/UserDashboardContent.svelte';
  import { onMount } from 'svelte';

  const ui = getClientUi();

  onMount(() => {
    if (ui.isMobile) {
      // Hide global header/footer for immersive view on mobile
      ui.isHeaderHidden = true;
      ui.isFooterHidden = true;
    }

    return () => {
        ui.isHeaderHidden = false;
        ui.isFooterHidden = false;
    };
  });

  $effect(() => {
    if (browser && !authStore.isAuthenticated) {
      ui.openLogin();
      goto('/');
    }
  });
</script>

{#if browser}
  {#if ui.isMobile}
    <!-- Immersive Header (Mobile Only) -->
    <div class="bg-white border-b border-gray-100 sticky top-0 z-30">
      <div class="flex items-center gap-4 px-6 py-4">
          <button onclick={() => history.back()} class="w-8 h-8 flex items-center justify-center text-gray-900">
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" /></svg>
          </button>
          <h1 class="text-lg font-black text-gray-900 uppercase italic tracking-tight truncate flex-1">
            TÀI KHOẢN CỦA TÔI
          </h1>
      </div>
    </div>

    <div class="pt-4 pb-20">
      <UserDashboardContent />
    </div>
  {:else}
    <!-- Desktop Layout -->
    <div class="py-4 px-2">
      <UserDashboardContent />
    </div>
  {/if}
{/if}
