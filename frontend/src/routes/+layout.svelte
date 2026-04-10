<script lang="ts">
  import "./layout.css";
  import { setNanobotContext } from "$lib/state/nanobot.svelte";
  import { setCartStore } from "$lib/state/commerce/cart.svelte";
  import CartDrawer from "$lib/components/storefront/cart/CartDrawer.svelte";
  import { navigating } from "$app/stores";
  import { Z_INDEX_CLIENT } from "$lib/core/constants/zIndex";

  // Elite V2.2: Ensure root initialization of context
  setNanobotContext();
  setCartStore();

  let { children } = $props();

  // Elite V2.2: Global Z-Index Injection
  const zIndexStyles = Object.entries(Z_INDEX_CLIENT)
    .map(([key, value]) => `--z-${key.toLowerCase().replace(/_/g, '-')}: ${value};`)
    .join(' ');
</script>

<svelte:head>
  <!-- SEO & Viral Meta (Elite V2.2) -->
  <title>SmartShop Elite | AI-Driven Commerce 2026</title>
  <meta name="description" content="Hệ thống quản trị kinh doanh thông minh tích hợp Agentic AI thế hệ mới (Viral 2026 Design)." />
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0, viewport-fit=cover" />
  <meta name="theme-color" content="#020202" />

  <!-- OpenGraph -->
  <meta property="og:title" content="SmartShop Elite" />
  <meta property="og:description" content="AI-Driven Commerce Platform" />
  <meta property="og:type" content="website" />

  <link rel="icon" href="/favicon.svg" />
</svelte:head>

<!-- Premium Navigation Progress Bar (Liquid Glass) -->
{#if $navigating}
    <div class="fixed top-0 left-0 right-0 h-[2px] z-[9999] pointer-events-none">
        <div class="h-full bg-gradient-to-r from-transparent via-[#00FFFF] to-transparent shadow-[0_0_10px_#00FFFF] animate-nav-progress"></div>
    </div>
{/if}

<div class="min-h-screen bg-[#020202] text-gray-100 selection:bg-[#00FFFF]/20" style={zIndexStyles}>
  <main class="relative z-10">
    {@render children()}
  </main>

  <CartDrawer />
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
