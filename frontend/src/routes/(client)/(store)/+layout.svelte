<script lang="ts">
  import { page } from '$app/stores';
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import HeaderDesktop from "$lib/components/storefront/layout/HeaderDesktop.svelte";
  import HeaderMobile from "$lib/components/storefront/layout/HeaderMobile.svelte";
  import FooterDesktop from "$lib/components/storefront/layout/FooterDesktop.svelte";
  import BottomNavMobile from "$lib/components/storefront/layout/BottomNavMobile.svelte";
  import type { Snippet } from "svelte";

  let { data, children }: { data: any, children: Snippet } = $props();
  const ui = getClientUi();

  // Trang home mobile tự quản lý header/bottomnav riêng (TikTok Shop style)
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

  // Map backend settings to UI structure
  const footerShopInfo = $derived({
      name: data.shopInfo?.site_name || "MICSMO ELITE",
      slogan: data.shopInfo?.slogan || "Bật tông trắng sáng",
      description: data.shopInfo?.description || "Hệ thống mỹ phẩm Elite 2026.",
      hotline: data.shopInfo?.contact?.hotline || "1800-MICSMO",
      email: data.shopInfo?.contact?.email || "legal@micsmo.com",
      address: data.shopInfo?.contact?.address || "Bitexco Financial Tower, Quận 1, TP. HCM"
  });
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
      <FooterDesktop shopInfo={footerShopInfo} />
    {/if}
  {/if}
</div>
