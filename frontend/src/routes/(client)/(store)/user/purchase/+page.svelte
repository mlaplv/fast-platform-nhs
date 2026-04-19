<script lang="ts">
  import { browser } from '$app/environment';
  import UserLayout from '$lib/components/storefront/user/UserLayout.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { fade } from 'svelte/transition';
  import UserMenuMobile from '$lib/components/storefront/user/UserMenuMobile.svelte';
  import UserHeaderMobile from '$lib/components/storefront/user/UserHeaderMobile.svelte';
  import PurchaseList from '$lib/components/storefront/user/PurchaseList.svelte';

  const ui = getClientUi();
  let isMenuOpen = $state(false);

  // Quản lý layout: Ẩn Header mặc định trên mobile, hiển thị trên desktop
  $effect.pre(() => {
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
        <!-- Header -->
        <div class="border-b border-stone-100 pb-5">
          <h1 class="text-xl font-serif italic text-stone-800 tracking-wide">Đơn Mua</h1>
          <p class="text-[13px] text-stone-400 mt-1 uppercase tracking-widest">Danh sách giao dịch</p>
        </div>

        <PurchaseList />
      </div>
    </UserLayout>
  {:else}
    <UserMenuMobile bind:active={isMenuOpen} onClose={() => isMenuOpen = false} />
    <UserHeaderMobile title="Đơn Mua" bind:isMenuOpen />

    <div
      class="pb-20 px-4 space-y-6"
      style="padding-top: calc(env(safe-area-inset-top) + 80px);"
    >
      <PurchaseList />
    </div>
  {/if}
{/if}
