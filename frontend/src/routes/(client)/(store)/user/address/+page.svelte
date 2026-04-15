<script lang="ts">
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import UserLayout from '$lib/components/storefront/user/UserLayout.svelte';
  import AddressWrapper from '$lib/components/storefront/user/AddressWrapper.svelte';
  import UserMenuMobile from '$lib/components/storefront/user/UserMenuMobile.svelte';
  import UserHeaderMobile from '$lib/components/storefront/user/UserHeaderMobile.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { fade } from 'svelte/transition';

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
</script>

{#if browser}
  {#if !ui.isMobile}
    <UserLayout>
      <div class="space-y-8" in:fade>
        <div class="border-b border-stone-100 pb-5">
          <h1 class="text-xl font-serif italic text-stone-800 tracking-wide">Địa Chỉ</h1>
          <p class="text-[13px] text-stone-400 mt-1 uppercase tracking-widest">Quản lý các địa chỉ nhận hàng của bạn</p>
        </div>
        <AddressWrapper />
      </div>
    </UserLayout>
  {:else}
    <UserMenuMobile bind:active={isMenuOpen} onClose={() => isMenuOpen = false} />
    <UserHeaderMobile title="Địa Chỉ" bind:isMenuOpen />

    <div class="pt-16 pb-20 px-4 space-y-6">
        <AddressWrapper />
    </div>
  {/if}
{/if}