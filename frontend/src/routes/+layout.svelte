<script lang="ts">
  import "./layout.css";
  import { setClientUi } from "$lib/state/commerce/ui.svelte";
  import QuickLoginModal from "$lib/components/storefront/auth/QuickLoginModal.svelte";
  import MobileAccountModal from "$lib/components/mobile/MobileAccountModal.svelte";
  import { setNanobotContext } from "$lib/state/nanobot.svelte";
  import { setCartStore } from "$lib/state/commerce/cart.svelte";
  import { navigating } from "$app/stores";
  import { onMount, type Snippet } from "svelte";
  import { Z_INDEX_CLIENT } from "$lib/core/constants/zIndex";
  import ToastProvider from "$lib/components/storefront/ui/ToastProvider.svelte";
  import GlobalConfirmModal from "$lib/components/storefront/ui/GlobalConfirmModal.svelte";

  // Elite V2.2: Context initialization gated by tenant
  let { children, data } = $props();

  const isAdmin = $derived(data.tenant === 'admin');
  const ui = isAdmin ? null : setClientUi();
  
  setNanobotContext();
  
  if (!isAdmin) {
    setCartStore();
  }

  onMount(() => {
    if (ui) return ui.initObservers();
  });

  const siteName = $derived(
    isAdmin 
    ? "Xohi Admin Dashboard" 
    : (ui?.settings?.basic_info?.site_name || ui?.settings?.site_name || "Micsmo Elite")
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
  <title>{siteName}</title>
  <meta name="description" content={metaDescription} />
  <meta name="theme-color" content="#020202" />

  <!-- OpenGraph -->
  <meta property="og:title" content={siteName} />
  <meta property="og:description" content={metaDescription} />
  <meta property="og:type" content="website" />

  <link rel="icon" href="/favicon.svg" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800;900&family=Outfit:wght@400;700;800;900&display=swap" rel="stylesheet" />
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
      {#if ui.isMobile}
        <MobileAccountModal />
      {:else}
        <QuickLoginModal />
      {/if}
    {/if}

    <ToastProvider />
    <GlobalConfirmModal />
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
