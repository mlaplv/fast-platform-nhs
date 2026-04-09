<script lang="ts">
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import HeaderDesktop from "$lib/components/storefront/layout/HeaderDesktop.svelte";
  import HeaderMobile from "$lib/components/storefront/layout/HeaderMobile.svelte";
  import FooterDesktop from "$lib/components/storefront/layout/FooterDesktop.svelte";
  import BottomNavMobile from "$lib/components/storefront/layout/BottomNavMobile.svelte";
  import type { Snippet } from "svelte";

  let { children }: { children: Snippet } = $props();
  const ui = getClientUi();
</script>

<div class="client-layout min-h-screen flex flex-col">
  {#if ui.isHydrated && !ui.isHeaderHidden}
    {#if ui.isMobile}
      <HeaderMobile />
    {:else}
      <HeaderDesktop />
    {/if}
  {/if}

  <main class="flex-grow">
    {@render children()}
  </main>

  {#if ui.isHydrated && !ui.isFooterHidden}
    {#if ui.isMobile}
      <BottomNavMobile />
    {:else}
      <FooterDesktop />
    {/if}
  {/if}
</div>
