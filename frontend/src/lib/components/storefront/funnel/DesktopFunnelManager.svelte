<script lang="ts">
  import { onMount } from "svelte";
  import { setShopStore } from "$lib/state/commerce/shop.svelte";
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import { browser } from "$app/environment";

  import SeoHead from "$lib/components/storefront/seo/SeoHead.svelte";
  import X from "@lucide/svelte/icons/x";
  import { portal } from "$lib/core/actions/portal";
  import { Z_INDEX_CLIENT } from "$lib/core/constants/zIndex";
  import { fade, scale } from "svelte/transition";

  import type { Product, ReviewStats } from "$lib/types";

  interface FunnelData {
    product: Product;
    shopInfo?: any;
    reviewStats?: ReviewStats | null;
    reviews?: any[];
    relatedProducts?: any[];
    unlockedVoucherIds?: string[];
    isMobile?: boolean;
  }

  let isAdminSession = $state(false);

  let { data }: { data: FunnelData } = $props();
  let isMounted = $state(false);
  let loadJIT = $state(false);

  import type { Component } from "svelte";
  let LiquidHeaderComponent = $state<Component<any> | null>(null);
  let HeroBannerComponent = $state<Component<any> | null>(null);

  // Desktop Dynamic JIT Components
  let DiagnosticsSectionComponent = $state<Component<any> | null>(null);
  let ScienceBentoComponent = $state<Component<any> | null>(null);
  let VerifiedReviewsComponent = $state<Component<any> | null>(null);
  let OfferGridComponent = $state<Component<any> | null>(null);
  let EliteLandingFooterComponent = $state<Component<any> | null>(null);

  // Lazy-loaded heavy modal components
  let ScannerHUDComponent = $state<Component<any> | null>(null);
  let VerificationCenterComponent = $state<Component<any> | null>(null);

  async function loadScannerHUD() {
    if (!ScannerHUDComponent) {
      const mod = await import("$lib/components/storefront/product-detail/shared/ScannerHUD.svelte");
      ScannerHUDComponent = mod.default;
    }
  }

  async function loadVerificationCenter() {
    if (!VerificationCenterComponent) {
      const mod = await import("$lib/components/storefront/product-detail/shared/VerificationCenter.svelte");
      VerificationCenterComponent = mod.default;
    }
  }

  // Load core above-fold components on mount
  onMount(() => {
    Promise.all([
      import("$lib/components/client/LiquidHeader.svelte"),
      import("$lib/components/client/HeroBanner.svelte")
    ]).then(([headerMod, heroMod]) => {
      LiquidHeaderComponent = headerMod.default;
      HeroBannerComponent = heroMod.default;
    });
  });

  $effect(() => {
    if (loadJIT) {
      Promise.all([
        import("./desktop/sections/DiagnosticsSection.svelte"),
        import("./desktop/sections/ScienceBento.svelte"),
        import("./desktop/sections/VerifiedReviews.svelte"),
        import("./desktop/sections/OfferGrid.svelte"),
        import("./desktop/sections/EliteLandingFooter.svelte")
      ]).then(([diagMod, sciMod, revMod, offMod, footMod]) => {
        DiagnosticsSectionComponent = diagMod.default;
        ScienceBentoComponent = sciMod.default;
        VerifiedReviewsComponent = revMod.default;
        OfferGridComponent = offMod.default;
        EliteLandingFooterComponent = footMod.default;
      });
    }
  });

  const shopStore = setShopStore();
  const product = $derived(data?.product);
  const metadata = $derived(product?.metadata || {});
  const seoMeta = $derived(product?.seoMeta || product?.seo_meta || null);

  const loadingText = $derived(
    metadata.sync_loading_text || "SYNCHRONIZING ELITE ASSETS..."
  );

  const clientUi = getClientUi();

  let isInitialized = false;
  if (product?.id && !isInitialized) {
    shopStore.init(product);
    if (data.unlockedVoucherIds) {
      shopStore.setUnlockedVouchers(data.unlockedVoucherIds);
    }
    isInitialized = true;
  }

  $effect.pre(() => {
    if (clientUi && data.shopInfo) {
      clientUi.settings = data.shopInfo;
      if (typeof sessionStorage !== 'undefined') {
        sessionStorage.setItem('primary_config', JSON.stringify(data.shopInfo));
      }
    }
  });

  onMount(() => {
    if (!browser) return;
    const timer = setTimeout(() => {
      isMounted = true;
    }, 150);

    if (product) {
      const urlParams = new URLSearchParams(window.location.search);
      const isLiveEditUrl = urlParams.get("live_edit") === "true";
      const hasLiveEditSession = isLiveEditUrl || sessionStorage.getItem('live_edit') === 'true';

      if (hasLiveEditSession) {
        Promise.all([
          import("$lib/state/commerce/liveEdit.svelte"),
          import("$lib/state/permissions.svelte")
        ]).then(([{ liveEditStore }, { permissionState }]) => {
          liveEditStore.init(product);
          if (isLiveEditUrl) {
            if (
              permissionState.hasRole("SUPER_ADMIN") ||
              permissionState.hasRole("ADMIN")
            ) {
              liveEditStore.isEditMode = true;
              isAdminSession = true;
            } else {
              window.location.replace(
                window.location.origin + window.location.pathname,
              );
            }
          } else {
            isAdminSession = liveEditStore.isAdmin;
          }
        });
      }
    }

    if (clientUi) {
      clientUi.isHeaderHidden = false;
      clientUi.isFooterHidden = false;
    }

    const cleanupObservers = clientUi.initObservers();

    return () => {
      clearTimeout(timer);
      shopStore.dispose();
      if (cleanupObservers) cleanupObservers();
    };
  });

  $effect(() => {
    if (!browser) return;

    const jitObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            loadJIT = true;
            jitObserver.disconnect();
          }
        });
      },
      { rootMargin: "1200px", threshold: 0.01 },
    );

    const sessionObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const idx = sectionIds.indexOf(entry.target.id);
            if (idx !== -1) currentSessionIdx = idx;
          }
        });
      },
      {
        rootMargin: "-50% 0px -50% 0px",
        threshold: 0,
      },
    );

    let active = true;
    Promise.resolve().then(() => {
      if (!active) return;
      const trigger = document.getElementById("jit-trigger");
      if (trigger) jitObserver.observe(trigger);

      sectionIds.forEach((id) => {
        const el = document.getElementById(id);
        if (el) sessionObserver.observe(el);
      });
    });

    return () => {
      active = false;
      jitObserver.disconnect();
      sessionObserver.disconnect();
    };
  });

  const scrollToQuiz = () => {
    const el = document.getElementById("diagnostics");
    if (el) {
      currentSessionIdx = 1;
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const hasQuiz = $derived(metadata?.quiz_questions?.length > 0);
  const sectionIds = $derived(
    hasQuiz
      ? ["hero", "diagnostics", "science", "reviews", "offers"]
      : ["hero", "science", "reviews", "offers"],
  );
  let currentSessionIdx = $state(0);
  const activeId = $derived(sectionIds[currentSessionIdx]);

  let isScanning = $state(false);
  let showVerification = $state(false);
  let verificationData = $state<any>(null);

  async function triggerScan() {
    await loadScannerHUD();
    isScanning = true;
    showVerification = false;
  }

  async function handleScanComplete(event: { verificationData: any }) {
    isScanning = false;
    verificationData = event.verificationData;
    await loadVerificationCenter();
    showVerification = true;
  }

  const normalizedFaqs = $derived(product?.metadata?.faqs || []);

  const siteNavigationLd = $derived.by(() => {
    const sections = [
      { name: "Đầu trang", url: "#hero" },
      { name: "Chẩn đoán AI", url: "#diagnostics" },
      { name: "Cơ chế Khoa học", url: "#science" },
      { name: "Đánh giá thực tế", url: "#reviews" },
      { name: "Ưu đãi Đặc biệt", url: "#offers" },
    ];

    return JSON.stringify({
      "@context": "https://schema.org",
      "@type": "ItemList",
      name: "Mục lục nội dung",
      itemListElement: sections.map((s, i) => ({
        "@type": "ListItem",
        position: i + 1,
        name: s.name,
        url: s.url,
      })),
    });
  });
</script>

<SeoHead
  pageType="product"
  title={seoMeta?.title || product?.name || "osmo Elite"}
  description={seoMeta?.description ||
    product?.shortDescription ||
    product?.short_description ||
    product?.description ||
    ""}
  image={product?.images?.[0] || ""}
  keywords={seoMeta?.keywords || ""}
  siteName={seoMeta?.site_name || product?.metadata?.seo_site_name || "osmo"}
  productData={{
    name: product?.name || "",
    price: product?.price || 0,
    discountPrice: product?.discountPrice ?? product?.discount_price,
    currency: "đ",
    availability: product?.stock > 0 ? "InStock" : "OutOfStock",
    brand: product?.metadata?.brand || "Osmo",
    sku: product?.sku || product?.id,
    images: Array.from(new Set([
      ...(product?.images || []),
      ...(product?.tierVariations?.[0]?.images || [])
    ])).filter(Boolean),
    ratingValue: data?.reviewStats?.average_rating || 5,
    reviewCount: data?.reviewStats?.total_count || 1,
  }}
  jsonLdScripts={[
    seoMeta?.json_ld_string,
    seoMeta?.breadcrumb_ld_string,
    seoMeta?.faq_ld_string,
    siteNavigationLd,
  ]}
  faqs={normalizedFaqs}
/>

<div
  class="client-page-root selection:bg-blue-600 selection:text-white min-h-screen"
  translate="no"
>
  {#if product?.id}
    {#if LiquidHeaderComponent}
      {@const LiquidHeader = LiquidHeaderComponent}
      <LiquidHeader
        {product}
        {scrollToQuiz}
        {activeId}
      />
    {/if}
    {#if HeroBannerComponent}
      {@const HeroBanner = HeroBannerComponent}
      <HeroBanner {scrollToQuiz} {triggerScan} />
    {/if}
    <div id="jit-trigger"></div>

    <!-- SECTIONS WITH DYNAMIC JIT RENDERING -->
    {#if hasQuiz}
      <section id="diagnostics" class="snap-session">
        {#if DiagnosticsSectionComponent}
          {@const Diagnostics = DiagnosticsSectionComponent}
          <Diagnostics {product} />
        {:else}
          <div class="w-full min-h-[400px] flex items-center justify-center bg-[#010101]">
            <div class="w-10 h-10 border border-[#C5A25D]/10 border-t-[#C5A25D] rounded-full animate-spin"></div>
          </div>
        {/if}
      </section>
    {/if}

    <section id="science" class="snap-session">
      {#if ScienceBentoComponent}
        {@const Science = ScienceBentoComponent}
        <Science />
      {:else}
        <div class="w-full min-h-[400px] flex items-center justify-center bg-[#010101]">
          <div class="w-10 h-10 border border-[#C5A25D]/10 border-t-[#C5A25D] rounded-full animate-spin"></div>
        </div>
      {/if}
    </section>

    <section id="reviews" class="snap-session">
      {#if VerifiedReviewsComponent}
        {@const VerifiedReviews = VerifiedReviewsComponent}
        <VerifiedReviews initialReviews={data.reviews} />
      {:else}
        <div class="w-full min-h-[400px] flex items-center justify-center bg-[#010101]">
          <div class="w-10 h-10 border border-[#C5A25D]/10 border-t-[#C5A25D] rounded-full animate-spin"></div>
        </div>
      {/if}
    </section>

    <section id="offers" class="snap-session">
      {#if OfferGridComponent}
        {@const OfferGrid = OfferGridComponent}
        <OfferGrid onTriggerScan={triggerScan} />
      {:else}
        <div class="w-full min-h-[400px] flex items-center justify-center bg-[#010101]">
          <div class="w-10 h-10 border border-[#C5A25D]/10 border-t-[#C5A25D] rounded-full animate-spin"></div>
        </div>
      {/if}
    </section>

    {#if EliteLandingFooterComponent}
      {@const EliteLandingFooter = EliteLandingFooterComponent}
      <EliteLandingFooter {product} onTriggerScan={triggerScan} />
    {:else}
      <div class="w-full min-h-[200px] bg-[#010101]"></div>
    {/if}
  {:else}
    <div
      class="flex flex-col items-center justify-center min-h-screen bg-[#050505] text-white"
    >
      <div
        class="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"
      ></div>
      <p
        class="text-sm tracking-[0.2em] font-light animate-pulse text-blue-400"
      >
        {loadingText}
      </p>
    </div>
  {/if}

  {#if isScanning && ScannerHUDComponent}
    {@const ScannerHUD = ScannerHUDComponent}
    <ScannerHUD
      barcode={product?.sku || (product?.metadata?.["barcode"] as string)}
      oncomplete={handleScanComplete}
    />
  {/if}

  {#if showVerification && VerificationCenterComponent}
    {@const VerificationCenter = VerificationCenterComponent}
    <div
      use:portal
      transition:fade={{ duration: 200 }}
      class="fixed inset-0 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xl"
      style:z-index={Z_INDEX_CLIENT.MODAL + 100}
      onclick={() => (showVerification = false)}
    >
      <div
        transition:scale={{ duration: 300, start: 0.95 }}
        class="bg-[#0a0a0a]/90 backdrop-blur-3xl w-full max-w-5xl p-0 shadow-[0_20px_100px_rgba(0,0,0,1)] border border-white/10 rounded-[5px] overflow-hidden relative"
        onclick={(e) => e.stopPropagation()}
      >
        <button
          class="absolute top-0 right-0 text-white/40 hover:text-white z-20 transition-all w-8 h-8 flex items-center justify-center hover:bg-white/10 rounded-bl-[5px]"
          onclick={() => (showVerification = false)}
        >
          <X size={18} />
        </button>

        <div
          class="relative z-10 pt-10 px-10 pb-2 max-h-[90vh] overflow-y-auto custom-scrollbar"
        >
          <VerificationCenter {product} {verificationData} />
        </div>
      </div>
    </div>
  {/if}
</div>

{#if isMounted && isAdminSession}
  {#await import("$lib/components/admin/AdminActionBar.svelte") then { default: AdminActionBar }}
    <AdminActionBar />
  {/await}
  {#await import("$lib/components/admin/LiveEditorOverlay.svelte") then { default: LiveEditorOverlay }}
    <LiveEditorOverlay />
  {/await}
  {#await import("$lib/components/admin/LiveEditNotification.svelte") then { default: LiveEditNotification }}
    <LiveEditNotification />
  {/await}
{/if}

<style lang="postcss">
  .client-page-root {
    antialiased: true;
    overflow-x: hidden;
    min-height: 100vh;
    font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background-color: #010101;
    color: var(--text-base);
  }

  :global(.snap-session) {
    min-height: auto;
    height: auto;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    position: relative;
    padding: 1.5rem 0;
    transform: translateZ(0);
    will-change: transform;
  }

  /* Ensure smooth transitions inside snap sessions */
  :global(section) {
    transition: opacity 0.8s ease;
  }
</style>
