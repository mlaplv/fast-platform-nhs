<script lang="ts">
  import { page } from '$app/stores';
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import HeaderDesktop from "$lib/components/storefront/layout/HeaderDesktop.svelte";
  import HeaderMobile from "$lib/components/storefront/layout/HeaderMobile.svelte";
  import FooterDesktop from "$lib/components/storefront/layout/FooterDesktop.svelte";
  import BottomNavMobile from "$lib/components/storefront/layout/BottomNavMobile.svelte";
  import type { Snippet } from "svelte";

  let { children }: { children: Snippet } = $props();
  const ui = getClientUi();

  // Trang home mobile tự quản lý header/bottomnav riêng (TikTok Shop style)
  // Dùng $page.url.pathname để tránh timing race condition với ui state
  const isHomePage = $derived(
    $page.url.pathname === '/home' || $page.url.pathname === '/'
  );

  // Global header chỉ hiện khi: đã hydrate + không bị ẩn + không phải trang home mobile
  const showGlobalHeader = $derived(
    ui.isHydrated && !ui.isHeaderHidden && !(isHomePage && ui.isMobile)
  );

  // Global bottom nav: tương tự, ẩn trên home mobile
  const showGlobalFooter = $derived(
    ui.isHydrated && !ui.isFooterHidden && !(isHomePage && ui.isMobile)
  );
</script>

<div class="client-layout min-h-screen flex flex-col">
  {#if showGlobalHeader}
    {#if ui.isMobile}
      <HeaderMobile />
    {:else}
      <HeaderDesktop />
    {/if}
  {/if}

  <main class="flex-grow">
    {@render children()}
  </main>

  {#if showGlobalFooter}
    {#if ui.isMobile}
      <BottomNavMobile />
    {:else}
      <FooterDesktop />
    {/if}
  {/if}
</div>
