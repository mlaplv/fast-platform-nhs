<script lang="ts">
  import { onMount, type Snippet } from 'svelte';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { fade } from 'svelte/transition';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import UserLayout from './UserLayout.svelte';
  import UserMenuMobile from './UserMenuMobile.svelte';
  import UserHeaderMobile from './UserHeaderMobile.svelte';
  import SeoHead from '../seo/SeoHead.svelte';

  interface Props {
    title: string;
    mobileTitle?: string;
    description?: string;
    children: Snippet;
    requireAuth?: boolean;
    headerHiddenOnMobile?: boolean;
  }

  let { 
    title, 
    mobileTitle, 
    description = "Quản lý thông tin tài khoản và ưu đãi của bạn.",
    children, 
    requireAuth = true,
    headerHiddenOnMobile = true
  }: Props = $props();

  const ui = getClientUi();
  let isMenuOpen = $state(false);

  // Elite V2.2: Deterministic Layout Management
  onMount(() => {
    if (ui.isMobile) {
      ui.isHeaderHidden = headerHiddenOnMobile;
    } else {
      ui.isHeaderHidden = false;
    }
    ui.isFooterHidden = false;

    return () => {
      ui.isHeaderHidden = false;
      ui.isFooterHidden = false;
    };
  });

  // Security Protocol: Auth Guard
  $effect(() => {
    if (browser && requireAuth && !authStore.isAuthenticated) {
      ui.openLogin();
      goto('/');
    }
  });

  const displayMobileTitle = $derived(mobileTitle || title);
</script>

<SeoHead 
  title="{title} | {ui.settings?.basic_info?.site_name || 'osmo Elite'}" 
  description={description}
  robots="noindex, nofollow"
/>

{#if browser}
  {#if !ui.isMobile}
    <UserLayout>
      <div class="space-y-8" in:fade={{ duration: 400 }}>
        <div class="border-b border-stone-100 pb-5">
          <h1 class="text-xl font-serif italic text-stone-800 tracking-wide">{title}</h1>
          {#if description}
            <p class="text-[13px] text-stone-400 mt-1 tracking-widest">{description}</p>
          {/if}
        </div>
        {@render children()}
      </div>
    </UserLayout>
  {:else}
    <UserMenuMobile bind:active={isMenuOpen} onClose={() => isMenuOpen = false} />
    <UserHeaderMobile title={displayMobileTitle} bind:isMenuOpen />

    <div
      class="pb-20 px-4 space-y-6 bg-[#f9f8f6] min-h-screen"
      style="padding-top: calc(env(safe-area-inset-top) + 80px);"
      in:fade={{ duration: 300 }}
    >
      {@render children()}
    </div>
  {/if}
{/if}
