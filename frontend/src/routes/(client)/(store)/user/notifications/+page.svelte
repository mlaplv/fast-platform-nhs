<script lang="ts">
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import UserLayout from '$lib/components/storefront/user/UserLayout.svelte';
  import NotificationList from '$lib/components/storefront/user/NotificationList.svelte';
  import UserMenuMobile from '$lib/components/storefront/user/UserMenuMobile.svelte';
  import UserHeaderMobile from '$lib/components/storefront/user/UserHeaderMobile.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';

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
          <h1 class="text-xl font-serif italic text-stone-800 tracking-wide">Thông Báo</h1>
          <p class="text-[13px] text-stone-400 mt-1 uppercase tracking-widest">Cập nhật tin tức mới nhất từ hệ thống</p>
        </div>
        <NotificationList />
      </div>
    </UserLayout>
  {:else}
    <UserMenuMobile bind:active={isMenuOpen} onClose={() => isMenuOpen = false} />
    <UserHeaderMobile title="Thông Báo" bind:isMenuOpen />

    <div class="pt-12 pb-20 px-4">
        <NotificationList />
    </div>
  {/if}
{/if}