<script lang="ts">
  import { page } from '$app/state';
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import HeaderDesktop from "$lib/components/storefront/layout/HeaderDesktop.svelte";
  import FooterDesktop from "$lib/components/storefront/layout/FooterDesktop.svelte";
  import { getCartStore } from "$lib/state/commerce/cart.svelte";
  import { getSearchStore } from "$lib/state/commerce/search.svelte";
  import SmartSearch from "$lib/components/storefront/product/SmartSearch.svelte";
  import { fomoStore } from "$lib/state/commerce/fomo.svelte";
  import NeuralActivityBar from "$lib/components/client/common/NeuralActivityBar.svelte";
  import { onMount, type Snippet } from "svelte";
  import type { LayoutData } from './$types';
  import "../client.css";

  let { data, children }: { data: LayoutData, children: Snippet } = $props();
  const isAdmin = $derived(data.tenant === 'admin');
  const ui = getClientUi();
  const cart = getCartStore();
  const searchStore = getSearchStore();

  // Elite V2.2: Zero-Latency State Sync (Sync before mount to prevent CLS)
  if (data.isMobile !== undefined) {
    ui.forceMobile(data.isMobile);
  }

  if (data.shopInfo) {
    ui.settings = data.shopInfo;
  }
  
  if (data.vouchers) {
    cart.setVouchers(data.vouchers);
  }

  onMount(() => {
    // Elite V2.2: Independent Fomo Initialization (Zero-Latency)
    if (!isAdmin && ui.settings?.conversions?.fomo_enabled) {
        fomoStore.init('osmo-elite');
    }
    return ui.initObservers();
  });

  // Re-check initialization if settings update
  // Elite V2.2: Unitary State Sync (Prop-driven reactivity)
  $effect(() => {
    if (data.shopInfo) {
        ui.settings = data.shopInfo;
    }
    if (data.vouchers) {
        cart.setVouchers(data.vouchers);
    }
    
    // Fomo State Machine (Elite V2.6)
    const fomoEnabled = !isAdmin && ui.settings?.conversions?.fomo_enabled;
    if (fomoEnabled && !fomoStore.isInitialized) {
        fomoStore.init('osmo-elite');
    } else if (!fomoEnabled && fomoStore.isInitialized) {
        fomoStore.dispose();
    }
  });
  
  const isAccountPage = $derived(page.url.pathname.startsWith('/user/'));

  // Global header: chỉ hiện trên DESKTOP (Hydrated + Not Hidden)
  const showGlobalHeader = $derived(
    !ui.isHeaderHidden && !ui.isMobile && !isFunnelPage
  );

  const isFunnelPage = $derived(
    page.data.product?.metadata?.landing_type && 
    page.data.product.metadata.landing_type !== 'standard'
  );

  // Global footer: chỉ hiện trên DESKTOP + không phải funnel
  const showGlobalFooter = $derived(
    !ui.isFooterHidden && !isFunnelPage && !ui.isMobile
  );

  // Map backend settings to UI structure (Elite V2.2: Deep Mapping)
  const footerShopInfo = $derived({
      name: data.shopInfo?.basic_info?.site_name || data.shopInfo?.site_name || "osmo ELITE",
      companyName: data.shopInfo?.contact_info?.company_name || data.shopInfo?.contact?.name || data.shopInfo?.basic_info?.site_name || "Hệ thống osmo",
      slogan: data.shopInfo?.basic_info?.slogan || data.shopInfo?.slogan || "Bật tông trắng sáng",
      description: data.shopInfo?.basic_info?.description || data.shopInfo?.description || "Hệ thống mỹ phẩm Elite 2026.",
      hotline: data.shopInfo?.contact_info?.hotline || data.shopInfo?.contact?.hotline || "1800-osmo",
      email: data.shopInfo?.contact_info?.email || data.shopInfo?.contact?.email || "legal@osmo",
      address: data.shopInfo?.contact_info?.address || data.shopInfo?.contact?.address || "Bitexco Financial Tower, Quận 1, TP. HCM",
      taxId: data.shopInfo?.contact_info?.tax_id || data.shopInfo?.tax_id || "",
      businessLicense: data.shopInfo?.contact_info?.business_license || data.shopInfo?.business_license || ""
  });
</script>

<div class="client-layout min-h-screen flex flex-col {ui.isMobile && isAccountPage ? '!bg-white' : ''}" translate="no">
  {#if showGlobalHeader}
    <HeaderDesktop />
  {/if}

  <main class="flex-grow">
    {@render children()}
  </main>

  {#if showGlobalFooter}
    {#if !ui.isMobile}
      <FooterDesktop shopInfo={footerShopInfo} />
    {/if}
  {/if}

  {#if !isAdmin && ui.settings?.conversions?.fomo_enabled}
    <NeuralActivityBar />
  {/if}

  {#if searchStore.isOverlayOpen}
    <SmartSearch variant="mobile-overlay" />
  {/if}
</div>
