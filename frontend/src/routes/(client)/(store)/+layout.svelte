<script lang="ts">
  import { page } from '$app/stores';
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import HeaderDesktop from "$lib/components/storefront/layout/HeaderDesktop.svelte";
  import HeaderMobile from "$lib/components/storefront/layout/HeaderMobile.svelte";
  import FooterDesktop from "$lib/components/storefront/layout/FooterDesktop.svelte";
  import BottomNavMobile from "$lib/components/storefront/layout/BottomNavMobile.svelte";
  import type { Snippet } from "svelte";
  import type { LayoutData } from './$types';
  import "../client.css";

  let { data, children }: { data: LayoutData, children: Snippet } = $props();
  const ui = getClientUi();

  // Elite V2.2: Global Settings Sync
  $effect(() => {
    if (data.shopInfo) ui.settings = data.shopInfo;
  });

  // Trang home/search mobile tự quản lý header riêng (Marketplace style)
  const isSpecializedPage = $derived(
    $page.url.pathname === '/home' || 
    $page.url.pathname === '/' || 
    $page.url.pathname === '/products'
  );

  // Global header chỉ hiện khi: đã hydrate + không bị ẩn + không phải trang chuyên biệt trên mobile
  const showGlobalHeader = $derived(
    ui.isHydrated && !ui.isHeaderHidden && !(isSpecializedPage && ui.isMobile)
  );

  // Global bottom nav: tương tự, ẩn trên home/search mobile
  const showGlobalFooter = $derived(
    ui.isHydrated && !ui.isFooterHidden && !(isSpecializedPage && ui.isMobile)
  );

  // Map backend settings to UI structure (Elite V2.2: Deep Mapping)
  const footerShopInfo = $derived({
      name: data.shopInfo?.basic_info?.site_name || data.shopInfo?.site_name || "MICSMO ELITE",
      companyName: data.shopInfo?.contact_info?.company_name || data.shopInfo?.contact?.name || data.shopInfo?.basic_info?.site_name || "Hệ thống Micsmo",
      slogan: data.shopInfo?.basic_info?.slogan || data.shopInfo?.slogan || "Bật tông trắng sáng",
      description: data.shopInfo?.basic_info?.description || data.shopInfo?.description || "Hệ thống mỹ phẩm Elite 2026.",
      hotline: data.shopInfo?.contact_info?.hotline || data.shopInfo?.contact?.hotline || "1800-MICSMO",
      email: data.shopInfo?.contact_info?.email || data.shopInfo?.contact?.email || "legal@micsmo.com",
      address: data.shopInfo?.contact_info?.address || data.shopInfo?.contact?.address || "Bitexco Financial Tower, Quận 1, TP. HCM",
      taxId: data.shopInfo?.contact_info?.tax_id || data.shopInfo?.tax_id || "",
      businessLicense: data.shopInfo?.contact_info?.business_license || data.shopInfo?.business_license || ""
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
