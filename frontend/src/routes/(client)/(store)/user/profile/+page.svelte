<script lang="ts">
  import UserLayout from '$lib/components/storefront/user/UserLayout.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { fade } from 'svelte/transition';
  import UserProfileForm from '$lib/components/storefront/user/UserProfileForm.svelte';
  import UserMenuMobile from '$lib/components/storefront/user/UserMenuMobile.svelte';
  import UserHeaderMobile from '$lib/components/storefront/user/UserHeaderMobile.svelte';

  const ui = getClientUi();
  let isMenuOpen = $state(false);

  // Quản lý layout: Ẩn Header mặc định trên mobile, hiển thị trên desktop
  $effect(() => {
    if (ui.isMobile) {
      ui.isHeaderHidden = true;
    } else {
      ui.isHeaderHidden = false;
    }
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
  {#if !ui.isMobile}
    <UserLayout>
      <div class="space-y-8" in:fade>
        <div class="border-b border-stone-100 pb-5">
          <h1 class="text-xl font-serif italic text-stone-800 tracking-wide">Hồ Sơ Của Tôi</h1>
          <p class="text-[13px] text-stone-400 mt-1 uppercase tracking-widest">Quản lý thông tin tài khoản</p>
        </div>
        <UserProfileForm />
      </div>
    </UserLayout>
  {:else}
    <UserMenuMobile bind:active={isMenuOpen} onClose={() => isMenuOpen = false} />
    <UserHeaderMobile title="Hồ sơ" bind:isMenuOpen />

    <div class="pt-16 pb-20 px-4 space-y-6">
      <UserProfileForm />
    </div>
  {/if}
{/if}
