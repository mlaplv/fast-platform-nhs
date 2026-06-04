<script lang="ts">
  import { page } from '$app/state';
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import HeaderDesktop from "$lib/components/storefront/layout/HeaderDesktop.svelte";
  import FooterDesktop from "$lib/components/storefront/layout/FooterDesktop.svelte";
  import { getCartStore } from "$lib/state/commerce/cart.svelte";
  import { getSearchStore } from "$lib/state/commerce/search.svelte";
  import SmartSearch from "$lib/components/storefront/product/SmartSearch.svelte";
  import { fomoStore } from "$lib/state/commerce/fomo.svelte";
  import { onMount, type Snippet, type Component } from "svelte";
  import SeoHead from "$lib/components/storefront/seo/SeoHead.svelte";
  import type { LayoutData } from './$types';

  let { data, children }: { data: LayoutData, children: Snippet } = $props();
  const isAdmin = $derived(data.tenant === 'admin');
  const ui = getClientUi();
  const cart = getCartStore();
  const searchStore = getSearchStore();

  let NeuralBarComponent = $state<Component<any> | null>(null);

  // Elite V2.2: Zero-Latency State Sync (Sync before mount to prevent CLS)
  if (data.isMobile !== undefined) {
    ui.forceMobile(data.isMobile);
  }

  if (data.shopInfo) {
    ui.settings = data.shopInfo;
    if (typeof sessionStorage !== 'undefined') {
      sessionStorage.setItem('primary_config', JSON.stringify(data.shopInfo));
    }
  }
  
  if (data.vouchers) {
    cart.setVouchers(data.vouchers);
  }

  onMount(() => {
    // Elite V2.2: Independent Fomo Initialization (Zero-Latency)
    if (!isAdmin && ui.isMobile && ui.settings?.conversions?.fomo_enabled) {
        fomoStore.init('smartshop-elite');
    }



    return ui.initObservers();
  });

  // Re-check initialization if settings update
  // Elite V2.2: Unitary State Sync (Prop-driven reactivity) - pre-paint synchronization
  $effect.pre(() => {
    if (data.shopInfo) {
        ui.settings = data.shopInfo;
        if (typeof sessionStorage !== 'undefined') {
          sessionStorage.setItem('primary_config', JSON.stringify(data.shopInfo));
        }
    }
    if (data.vouchers) {
        cart.setVouchers(data.vouchers);
    }
    
    // Fomo State Machine (Elite V2.6)
    const fomoEnabled = !isAdmin && ui.isMobile && ui.settings?.conversions?.fomo_enabled;
    if (fomoEnabled) {
        if (!fomoStore.isInitialized) {
            fomoStore.init('smartshop-elite');
        }
        if (!NeuralBarComponent) {
            import('$lib/components/client/common/NeuralActivityBar.svelte').then(m => {
                NeuralBarComponent = m.default;
            });
        }
    } else if (fomoStore.isInitialized) {
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
      name: data.shopInfo?.basic_info?.site_name || data.shopInfo?.site_name || "SmartShop ELITE",
      companyName: data.shopInfo?.contact_info?.company_name || data.shopInfo?.contact?.name || data.shopInfo?.basic_info?.site_name || "Hệ thống SmartShop",
      slogan: data.shopInfo?.basic_info?.slogan || data.shopInfo?.slogan || "Mua sắm thông minh",
      description: data.shopInfo?.basic_info?.description || data.shopInfo?.description || "Hệ thống thương mại điện tử Elite 2026.",
      hotline: data.shopInfo?.contact_info?.hotline || data.shopInfo?.contact?.hotline || "1900-SMART",
      email: data.shopInfo?.contact_info?.email || data.shopInfo?.contact?.email || "contact@smartshop.test",
      address: data.shopInfo?.contact_info?.address || data.shopInfo?.contact?.address || "Hà Nội, Việt Nam",
      taxId: data.shopInfo?.contact_info?.tax_id || data.shopInfo?.tax_id || "",
      businessLicense: data.shopInfo?.contact_info?.business_license || data.shopInfo?.business_license || ""
  });
  // Elite V2.2: Intelligent SSR SEO Guard
  // Suppress layout fallback if the page already has product/article/category data OR is the homepage
  const hasPageSeo = $derived(
    !!data.product || 
    !!data.article || 
    !!data.category || 
    data.type === 'category' || 
    data.type === 'product' ||
    data.type === 'article' ||
    data.type === 'news' ||
    page.url.pathname === '/' ||
    page.url.pathname === '/home'
  );
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

  {#if !isAdmin && ui.isMobile && ui.settings?.conversions?.fomo_enabled && NeuralBarComponent}
    {@const DynamicBar = NeuralBarComponent}
    <DynamicBar />
  {/if}

  {#if searchStore.isOverlayOpen}
    <SmartSearch variant="mobile-overlay" />
  {/if}

</div>
