<script>
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import UserProfileForm from '$lib/components/storefront/user/UserProfileForm.svelte';
  import UserMenuMobile from '$lib/components/storefront/user/UserMenuMobile.svelte';
  import BottomNavMobile from '$lib/components/storefront/layout/BottomNavMobile.svelte';
  import { Menu } from 'lucide-svelte';

  const ui = getClientUi();
  let isMenuOpen = $state(false);

  // Ẩn Header mặc định của Layout, hiển thị Footer (BottomNav)
  $effect(() => {
    ui.isHeaderHidden = true;
    ui.isFooterHidden = false;

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
  <UserMenuMobile bind:active={isMenuOpen} onClose={() => isMenuOpen = false} />

  <!-- Header Immersive -->
  <header class="fixed top-0 left-0 w-full z-[var(--z-header)] flex items-center justify-between p-6 bg-white/90 backdrop-blur-md border-b border-gray-100">
      <button onclick={() => history.back()} class="w-10 h-10 flex items-center justify-center">
          <svg class="w-6 h-6 text-gray-900" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" /></svg>
      </button>
      <h1 class="text-sm font-black text-gray-900 uppercase italic tracking-widest">Hồ sơ</h1>
      <!-- Menu Button -->
      <button onclick={() => isMenuOpen = true} class="w-10 h-10 flex items-center justify-center">
        <Menu class="w-6 h-6 text-gray-900" />
      </button>
  </header>

  <div class="pt-24 pb-8 px-4">
    <UserProfileForm />
  </div>

  {#if ui.isMobile}
    <BottomNavMobile />
  {/if}
{/if}
