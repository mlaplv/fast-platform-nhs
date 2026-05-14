<script lang="ts">
  import "./layout.css";
  import "$lib/styles/fonts.css";
  import { setClientUi } from "$lib/state/commerce/ui.svelte";
  import QuickLoginModal from "$lib/components/storefront/auth/QuickLoginModal.svelte";
  import { setNanobotContext } from "$lib/state/nanobot.svelte";
  import { setCartStore } from "$lib/state/commerce/cart.svelte";
  import { navigating, page } from "$app/stores";
  import { onMount, onDestroy, type Snippet } from "svelte";
  import { Z_INDEX_CLIENT } from "$lib/core/constants/zIndex";
  import ToastProvider from "$lib/components/storefront/ui/ToastProvider.svelte";
  import GlobalConfirmModal from "$lib/components/storefront/ui/GlobalConfirmModal.svelte";
  import ReportReviewModal from "$lib/components/storefront/reviews/ReportReviewModal.svelte";
  import { permissionState } from "$lib/state/permissions.svelte";
  import { supportAgent } from "$lib/state/commerce/supportAgent.svelte";
  import SupportAgentFAB from "$lib/components/client/support/SupportAgentFAB.svelte";
  import SupportChatDesktop from "$lib/components/client/support/SupportChatDesktop.svelte";
  import SupportChatMobile from "$lib/components/client/support/SupportChatMobile.svelte";
  import { untrack } from "svelte";
  import { getSearchStore } from "$lib/state/commerce/search.svelte";
  import SmartSearch from "$lib/components/storefront/product/SmartSearch.svelte";

  // Elite V2.2: Context initialization gated by tenant
  let { children, data } = $props();

  // Elite V6.3: Neural Path Synchronization
  $effect(() => {
    const path = $page.url.pathname;
    untrack(() => {
        supportAgent.setPath(path);
        
        // Elite V2.2: Global Navigation Guard (Scroll-Lock & Overlay Reset)
        if (typeof document !== 'undefined') {
            document.body.style.overflow = '';
            document.documentElement.style.overflow = '';
        }
        
        if (ui) {
            ui.authModal.isOpen = false;
        }
        
        try {
            const searchStore = getSearchStore();
            searchStore.isOverlayOpen = false;
        } catch (e) {}
    });
  });

  const isAdmin = $derived(data?.tenant === 'admin');
  const ui = isAdmin ? null : setClientUi();

  setNanobotContext();

  if (!isAdmin) {
    setCartStore();
  }

  onMount(async () => {
    // Elite V2.2: Global Identity Handshake
    await permissionState.handshake();

    // Elite V2.2: Neural Advisor Persona Initialization
    if (!isAdmin) {
      await supportAgent.init(data.agentName);
    }

    if (ui) {
      return ui.initObservers();
    }
  });

  onDestroy(() => {
    // Elite V2.2: Resource Discipline
    permissionState.dispose();
    supportAgent.dispose();
  });

  const siteName = $derived(
    isAdmin 
    ? "Xohi Admin Dashboard" 
    : (ui?.settings?.basic_info?.site_name || ui?.settings?.site_name || "osmo Elite")
  );
  const metaDescription = $derived(
    isAdmin
    ? "Hệ thống quản trị Elite V2.2"
    : `${siteName} - Hệ thống phân phối sản phẩm chăm sóc sức khỏe Elite V2.2`
  );

  // Elite V2.2: Global Z-Index Injection (Client Only)
  const zIndexStyles = $derived(!isAdmin ? Object.entries(Z_INDEX_CLIENT)
    .map(([key, value]) => `--z-${key.toLowerCase().replace(/_/g, '-')}: ${value};`)
    .join(' ') : '');
</script>

<svelte:head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0, viewport-fit=cover" />
  
  {#if isAdmin}
    <title>{siteName}</title>
    <meta name="description" content={metaDescription} />
    <meta name="theme-color" content="#020202" />
    <meta name="robots" content="noindex, nofollow" />
    
    <meta property="og:title" content={siteName} />
    <meta property="og:description" content={metaDescription} />
    <meta property="og:type" content="website" />
    <meta property="og:site_name" content={siteName} />
    <meta property="og:locale" content="vi_VN" />
  {:else}
    <meta name="theme-color" content="#f5f5f5" />
  {/if}

  <link rel="icon" href="/favicon.svg" />
</svelte:head>

<!-- Premium Navigation Progress Bar (Liquid Glass) -->
{#if $navigating}
    <div class="fixed top-0 left-0 right-0 h-[2px] z-[var(--z-admin-action-bar-progress)] pointer-events-none">
        <div class="h-full bg-gradient-to-r from-transparent via-[#00FFFF] to-transparent shadow-[0_0_10px_#00FFFF] animate-nav-progress"></div>
    </div>
{/if}

<div class="min-h-screen bg-[#020202] text-gray-100 selection:bg-[#00FFFF]/20" style={zIndexStyles}>
  <main class="relative z-10">
    {@render children()}
  </main>

  {#if !isAdmin}
    
    {#if ui?.authModal?.isOpen}
      <QuickLoginModal />
    {/if}

    <ToastProvider />
    <GlobalConfirmModal />
    <ReportReviewModal />

    <SupportAgentFAB isMobile={ui.isMobile} />
    {#if ui.isMobile}
      <SupportChatMobile productSlug={$page.params.slug} />
      <SmartSearch variant="mobile-overlay" />
    {:else}
      <SupportChatDesktop productSlug={$page.params.slug} />
    {/if}
  {/if}
</div>

<style>
    @keyframes nav-progress {
        0% { transform: translateX(-100%); }
        50% { transform: translateX(0); }
        100% { transform: translateX(100%); }
    }
    .animate-nav-progress {
        animation: nav-progress 1.5s infinite ease-in-out;
    }
</style>
