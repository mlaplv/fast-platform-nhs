<script lang="ts">
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { fade } from 'svelte/transition';
  import UserLayout from '$lib/components/storefront/user/UserLayout.svelte';
  import NotificationList from '$lib/components/storefront/user/NotificationList.svelte';
  import UserMenuMobile from '$lib/components/storefront/user/UserMenuMobile.svelte';
  import UserHeaderMobile from '$lib/components/storefront/user/UserHeaderMobile.svelte';
  import SeoHead from '$lib/components/storefront/seo/SeoHead.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';


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

<SeoHead 
  title="Thông báo | {ui.settings?.basic_info?.site_name || 'osmo Elite'}" 
  robots="noindex, nofollow"
/>



{#if browser}
  {#if !ui.isMobile}
    <UserLayout>
      <div class="space-y-8" in:fade>
        <div class="border-b border-stone-100 pb-5">
          <h1 class="text-xl font-serif italic text-stone-800 tracking-wide">Thông báo</h1>
          <p class="text-[13px] text-stone-400 mt-1 tracking-widest">Cập nhật tin tức mới nhất từ hệ thống</p>
        </div>

        <NotificationList />
      </div>
    </UserLayout>
  {:else}
    <UserMenuMobile bind:active={isMenuOpen} onClose={() => isMenuOpen = false} />
    <UserHeaderMobile title="Thông báo" bind:isMenuOpen />


    <div
      class="pb-20 px-4 space-y-6"
      style="padding-top: calc(env(safe-area-inset-top) + 80px);"
    >
        <NotificationList />
    </div>
  {/if}
{/if}