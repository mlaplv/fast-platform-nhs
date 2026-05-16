<script lang="ts">
  import UserLayout from '$lib/components/storefront/user/UserLayout.svelte';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { fade, slide } from 'svelte/transition';
  import Eye from "@lucide/svelte/icons/eye";
  import EyeOff from "@lucide/svelte/icons/eye-off";
  import { apiClient } from '$lib/utils/apiClient';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import { fallbackSha256 } from '$lib/utils/cryptoFallback';
  import UserMenuMobile from '$lib/components/storefront/user/UserMenuMobile.svelte';
  import UserHeaderMobile from '$lib/components/storefront/user/UserHeaderMobile.svelte';
  import PasswordForm from '$lib/components/storefront/user/PasswordForm.svelte';
  import SeoHead from '$lib/components/storefront/seo/SeoHead.svelte';


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

<SeoHead title="Đổi mật khẩu | {ui.settings?.basic_info?.site_name || 'osmo Elite'}" />


{#if browser}
  {#if !ui.isMobile}
    <UserLayout>
      <div class="space-y-8" in:fade>
        <div class="border-b border-stone-100 pb-5">
          <h1 class="text-xl font-serif italic text-stone-800 tracking-wide">Đổi mật khẩu</h1>
          <p class="text-[13px] text-stone-400 mt-1 tracking-widest">Để bảo mật tài khoản, vui lòng không chia sẻ mật khẩu cho người khác</p>
        </div>


        <div class="max-w-md">
          <PasswordForm />
        </div>
      </div>
    </UserLayout>
  {:else}
    <UserMenuMobile bind:active={isMenuOpen} onClose={() => isMenuOpen = false} />
    <UserHeaderMobile title="Đổi mật khẩu" bind:isMenuOpen />


    <div
      class="pb-20 px-4 space-y-6"
      style="padding-top: calc(env(safe-area-inset-top) + 80px);"
    >
      <PasswordForm />
    </div>
  {/if}
{/if}