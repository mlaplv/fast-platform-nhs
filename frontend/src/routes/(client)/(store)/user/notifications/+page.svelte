<script lang="ts">
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import UserLayout from '$lib/components/storefront/user/UserLayout.svelte';
  import NotificationList from '$lib/components/storefront/user/NotificationList.svelte';
  import UserMenuMobile from '$lib/components/storefront/user/UserMenuMobile.svelte';
  import BottomNavMobile from '$lib/components/storefront/layout/BottomNavMobile.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { fade } from 'svelte/transition';
  import { Menu } from 'lucide-svelte';

  const ui = getClientUi();
  let isMenuOpen = $state(false);

  // Immersive layout management: Hide global header, show global footer (BottomNav)
  $effect(() => {
    ui.isHeaderHidden = true;
    ui.isFooterHidden = false;

    return () => {
      ui.isHeaderHidden = false;
      ui.isFooterHidden = false;
    };
  });
</script>

{#if browser}
  {#if !ui.isMobile}
    <UserLayout>
      <div class="space-y-8" in:fade>
        <div class="border-b border-stone-100 pb-5">
          <h1 class="text-xl font-serif italic text-stone-800 tracking-wide">Thông Báo</h1>
          <p class="text-[13px] text-stone-400 mt-1 uppercase tracking-widest">Cập nhật tin tức mới nhất từ hệ thống</p>
        </div>
        <NotificationList />
      </div>
    </UserLayout>
  {:else}
    <UserMenuMobile bind:active={isMenuOpen} onClose={() => isMenuOpen = false} />
    <!-- Immersive Header Mobile -->
    <header class="fixed top-0 left-0 w-full z-[var(--z-header)] flex items-center justify-between p-6 bg-white/90 backdrop-blur-md border-b border-gray-100">
        <button onclick={() => history.back()} class="w-10 h-10 flex items-center justify-center">
            <svg class="w-6 h-6 text-gray-900" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" /></svg>
        </button>
        <h1 class="text-sm font-black text-gray-900 uppercase italic tracking-widest">Thông Báo</h1>
        <!-- Menu Button -->
        <button onclick={() => isMenuOpen = true} class="w-10 h-10 flex items-center justify-center">
            <Menu class="w-6 h-6 text-gray-900" />
        </button>
    </header>

    <div class="pt-24 pb-20 px-4">
        <NotificationList />
    </div>

    <BottomNavMobile />
  {/if}
{/if}