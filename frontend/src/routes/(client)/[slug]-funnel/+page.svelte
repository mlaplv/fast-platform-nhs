<script lang="ts">
  import "../client.css";
  import { onMount } from "svelte";
  import { setShopStore } from "$lib/state/commerce/shop.svelte";
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import HeroBanner from "$lib/components/client/HeroBanner.svelte";
  import LiquidHeader from "$lib/components/client/LiquidHeader.svelte";
  import { browser } from "$app/environment";
  import type { Action } from "svelte/action";

  // JIT Component Flags
  let loadJIT = $state(false);

  import type { Component } from "svelte";
  let DiagnosticsSection = $state<Component<any> | null>(null);
  let ScienceBento = $state<Component<any> | null>(null);
  let VerifiedReviews = $state<Component<any> | null>(null);
  let OfferGrid = $state<Component<any> | null>(null);

  $effect(() => {
    if (loadJIT) {
      import("$lib/components/client/slug/DiagnosticsSection.svelte").then((m) => {
        DiagnosticsSection = m.default as Component<any>;
      });
      import("$lib/components/client/slug/ScienceBento.svelte").then((m) => {
        ScienceBento = m.default as Component<any>;
      });
      import("$lib/components/client/slug/VerifiedReviews.svelte").then((m) => {
        VerifiedReviews = m.default as Component<any>;
      });
      import("$lib/components/client/slug/OfferGrid.svelte").then((m) => {
        OfferGrid = m.default as Component<any>;
      });
    }
  });

  import MobileLandingLayout from "$lib/components/mobile/MobileLandingLayout.svelte";
  import SeoHead from "$lib/components/storefront/seo/SeoHead.svelte";
  import ScannerHUD from "$lib/components/storefront/product-detail/shared/ScannerHUD.svelte";
  import VerificationCenter from "$lib/components/storefront/product-detail/shared/VerificationCenter.svelte";
  import X from "@lucide/svelte/icons/x";
  import { portal } from "$lib/core/actions/portal";
  import { Z_INDEX_CLIENT } from "$lib/core/constants/zIndex";
  import { fade, scale } from "svelte/transition";

  import type { PageData } from "./$types";

  // Admin Live Editor (Elite V2.2)
  import { liveEditStore } from "$lib/state/commerce/liveEdit.svelte";
  import { permissionState } from "$lib/state/permissions.svelte";

  let { data }: { data: PageData } = $props();
  let themeMode = $state<"system" | "light" | "dark">("system");
  let isMounted = $state(false);

  // 🚀 ELITE CONTEXT INJECTION (Elite V2.2)
  const shopStore = setShopStore();

  // Protection & Derived State
  const product = $derived(data?.product);
  const metadata = $derived(product?.metadata || {});
  const seoMeta = $derived(product?.seoMeta || product?.seo_meta || null);
  const isMobile = $derived(data?.isMobile || false);

  const loadingText = $derived(
    metadata.sync_loading_text || "SYNCHRONIZING ELITE ASSETS...",
  );
  const siteName = $derived(metadata.seo_site_name || "osmo Elite");

  // Elite Smart-Adaptive: Reactive Layout Switching
  const clientUi = getClientUi();
  const useMobileLayout = $derived(
    clientUi?.isHydrated ? clientUi.isMobile : isMobile,
  );

  // 🚀 QUANTUM SYNC (Elite V2.2 Protocol)
  // Inline init ensures SSR stability; Guarded initialization for client-side
  let isInitialized = false;

  if (product?.id && !isInitialized) {
    shopStore.init(product);
    if (data.unlockedVoucherIds) {
      shopStore.setUnlockedVouchers(data.unlockedVoucherIds);
    }
    isInitialized = true;
  }

  const updateDOM = (theme: "light" | "dark"): void => {
    if (!browser) return;
    document.documentElement.setAttribute("data-theme", theme);
    document.body.setAttribute("data-theme", theme);
  };

  const applyTheme = (mode: "system" | "light" | "dark") => {
    themeMode = mode;
    if (!browser) return;
    localStorage.setItem("hero-theme-mode", mode);
    if (mode === "system") {
      const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      updateDOM(isDark ? "dark" : "light");
    } else {
      updateDOM(mode as "light" | "dark");
    }
  };

  // Shop Settings Sync (Elite V2.2)
  $effect.pre(() => {
    if (clientUi) {
      // Inject global shop settings into the UI state for sub-components (OfferGrid, etc.)
      if (data.shopInfo) {
        clientUi.settings = data.shopInfo;
      }
    }
  });

  // 🚀 ELITE QUANTUM COORDINATOR (Elite V2.2)
  onMount(() => {
    if (!browser) return;
    const timer = setTimeout(() => {
      isMounted = true;
    }, 150);

    const savedTheme = localStorage.getItem("hero-theme-mode");
    applyTheme(
      savedTheme === "light" || savedTheme === "dark" || savedTheme === "system"
        ? savedTheme
        : "system",
    );

    if (product) {
      liveEditStore.init(product);
      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.get("live_edit") === "true") {
        if (
          permissionState.hasRole("SUPER_ADMIN") ||
          permissionState.hasRole("ADMIN")
        ) {
          liveEditStore.isEditMode = true;
        } else {
          window.location.replace(
            window.location.origin + window.location.pathname,
          );
        }
      }
    }

    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const h = (e: MediaQueryListEvent): void => {
      if (themeMode === "system") updateDOM(e.matches ? "dark" : "light");
    };
    mq.addEventListener("change", h);

    // JIT ASSET LOADER (Elite V2.2 Protocol) - FIRE EARLY
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

    // SESSION COORDINATOR (Elite V2.2 HUD Sync) - FIRE AT CENTER
    const sessionObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !isWheelLocked) {
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

    // Register Assets
    const trigger = document.getElementById("jit-trigger");
    if (trigger) jitObserver.observe(trigger);

    sectionIds.forEach((id) => {
      const el = document.getElementById(id);
      if (el) sessionObserver.observe(el);
    });

    // Elite V2.2: Instant UI Recovery Protocol
    if (clientUi) {
      clientUi.isHeaderHidden = false;
      clientUi.isFooterHidden = false;
    }

    const cleanupObservers = clientUi.initObservers();

    return () => {
      clearTimeout(timer);
      shopStore.dispose();
      mq.removeEventListener("change", h);
      jitObserver.disconnect();
      sessionObserver.disconnect();
      if (cleanupObservers) cleanupObservers();
    };
  });

  const scrollToQuiz = () => {
    const el = document.getElementById("diagnostics");
    if (el) {
      currentSessionIdx = 1; // Sync programmatic tracker
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  // Elite 2026 Programmatic Scroll Coordinator (O(1) Speed/Memory)
  const hasQuiz = $derived((metadata?.quiz_questions?.length || 0) > 0);
  const sectionIds = $derived(
    hasQuiz
      ? ["hero", "diagnostics", "science", "reviews", "offers"]
      : ["hero", "science", "reviews", "offers"],
  );
  let currentSessionIdx = $state(0);
  const activeId = $derived(sectionIds[currentSessionIdx]);
  let isWheelLocked = false;

  // Verification System (Elite V2.2)
  let isScanning = $state(false);
  let showVerification = $state(false);
  let verificationData = $state<any>(null);

  function triggerScan() {
    isScanning = true;
    showVerification = false;
  }

  function handleScanComplete(event: { verificationData: any }) {
    isScanning = false;
    verificationData = event.verificationData;
    showVerification = true;
  }

  const onWheelObserver = (e: WheelEvent) => {
    // Escape limiters: Mobile layout, Server, or interacting with Checkout
    if (useMobileLayout || !browser) return;

    // Viral 2026: Neural Activity Interception? (Optional)
    const target = e.target as HTMLElement;

    // Elite V2.2 Escape: Don't hijack scroll if we are in Edit Mode and hovering over an editor
    if (
      liveEditStore.isEditMode &&
      (target?.closest(".edit-mode-container") ||
        target?.closest(".editor-box"))
    )
      return;

    // Ignore micro-scrolls (e.g., trackpad resting)
    if (Math.abs(e.deltaY) < 15) return;

    // 100% Native Intercept - Bypass default DOM scrolling
    e.preventDefault();
    if (isWheelLocked) return;

    const direction = e.deltaY > 0 ? 1 : -1;
    let nextIdx = currentSessionIdx + direction;

    // Clamp boundaries
    if (nextIdx >= 0 && nextIdx < sectionIds.length) {
      isWheelLocked = true;
      currentSessionIdx = nextIdx;

      // O(1) Native C++ lookup
      const target = document.getElementById(sectionIds[currentSessionIdx]);
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      }

      // Memory-efficient cooling lock to prevent scroll-looping (450ms for ultra-fast snap)
      setTimeout(() => {
        isWheelLocked = false;
      }, 450);
    }
  };

  // Svelte 5 Native Action: Forced non-passive listener
  const initScrollObserver: Action<HTMLElement> = (node) => {
    node.addEventListener("wheel", onWheelObserver, { passive: false });
    return {
      destroy() {
        node.removeEventListener("wheel", onWheelObserver);
      },
    };
  };

  // ── ELITE V2.2: SEO FAQ Extraction ───────────────────────────────────────
  const normalizedFaqs = $derived(product?.metadata?.faqs || []);

  // ── SITE NAVIGATION LD (Google Sitelinks Support) ──────────────────────────
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
    images: product?.images || [],
  }}
  jsonLdScripts={[
    seoMeta?.json_ld_string,
    seoMeta?.breadcrumb_ld_string,
    seoMeta?.faq_ld_string,
    siteNavigationLd,
  ]}
  faqs={normalizedFaqs}
/>

{#if useMobileLayout}
  {#if product}
    <MobileLandingLayout
      {product}
      reviewStats={data.reviewStats}
      reviews={data.reviews}
      relatedProducts={data.relatedProducts}
    />
  {/if}
{:else}
  <div
    class="client-page-root selection:bg-blue-600 selection:text-white h-screen overflow-y-scroll"
    translate="no"
    use:initScrollObserver
  >
    {#if product?.id}
      <LiquidHeader
        {product}
        {themeMode}
        {applyTheme}
        {scrollToQuiz}
        {activeId}
      />
      <HeroBanner {scrollToQuiz} {triggerScan} />

      <!-- SECTIONS WITH INDEPENDENT JIT LOADING (Elite V2.2 Optimization) -->
      <!-- This preserves snap points while components are loading -->

      <div id="jit-trigger"></div>

      {#if hasQuiz}
        <section id="diagnostics" class="snap-session">
          {#if DiagnosticsSection}
            <DiagnosticsSection {product} />
          {:else}
            <div
              class="w-full h-full bg-[#010101] animate-pulse rounded-t-3xl border-t border-[#111]"
            ></div>
          {/if}
        </section>
      {/if}

      <section id="science" class="snap-session">
        {#if ScienceBento}
          <ScienceBento />
        {:else}
          <div class="w-full h-full bg-[#010101] animate-pulse"></div>
        {/if}
      </section>

      <section id="reviews" class="snap-session">
        {#if VerifiedReviews}
          <VerifiedReviews initialReviews={data.reviews} />
        {:else}
          <div class="w-full h-full bg-[#010101] animate-pulse"></div>
        {/if}
      </section>

      <section id="offers" class="snap-session">
        {#if OfferGrid}
          <OfferGrid onTriggerScan={triggerScan} />
        {:else}
          <div class="w-full h-full bg-[#010101] animate-pulse"></div>
        {/if}
      </section>
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

    {#if isScanning}
      <ScannerHUD
        barcode={product?.sku || (product?.metadata?.["barcode"] as string)}
        oncomplete={handleScanComplete}
      />
    {/if}

    {#if showVerification}
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
{/if}

<!-- Administrative HUD (Elite V2.2 Overlay Layer - Severely Protected) -->
{#if isMounted && liveEditStore.isAdmin}
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
    height: 100vh;
    font-family: "Be Vietnam Pro", sans-serif;
    background-color: #010101; /* Viral 2026: Luxury Black foundation */
    color: var(--text-base);
  }

  :root {
    --z-sticky-header: 100;
  }

  :global(.snap-session) {
    min-height: 100dvh;
    height: auto;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    position: relative;
    transform: translateZ(0); /* Hardware Acceleration */
    will-change: transform;
  }

  /* ELITE V2.2: Final section isolation - no forced min-height to prevent gaps */
  #offers.snap-session {
    min-height: auto;
  }

  /* Ensure smooth transitions inside snap sessions */
  :global(section) {
    transition: opacity 0.8s ease;
  }

  /* Elite V2.2: Floating Verify Button Styles (Liquid Viral - Minimalist) */
  .verify-floating-btn {
    position: relative;
    width: 40px;
    height: 40px;
    background: transparent;
    color: #00bfa5;
    border: none;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: none;
    transition: all 0.5s cubic-bezier(0.19, 1, 0.22, 1);
    overflow: visible;
  }

  .verify-floating-btn:hover {
    transform: scale(1.2);
    color: #00d1b2;
  }

  .btn-inner {
    position: relative;
    z-index: 2;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
  }

  .icon-scanner .scan-line {
    stroke-dasharray: 12;
    animation: scan-move 2s infinite ease-in-out;
    opacity: 0.8;
  }

  .icon-scanner .check-mark {
    opacity: 0;
    transition: all 0.3s;
    transform: scale(0.5);
  }

  .verify-floating-btn:hover .icon-scanner .check-mark {
    opacity: 1;
    transform: scale(1);
    stroke: #ffffff;
  }

  .verify-floating-btn:hover .icon-scanner .scan-line,
  .verify-floating-btn:hover .icon-scanner .corner {
    opacity: 0.3;
  }

  @keyframes scan-move {
    0%,
    100% {
      transform: translateY(-4px);
    }
    50% {
      transform: translateY(4px);
    }
  }

  .pulse-ring {
    position: absolute;
    inset: 4px;
    border: 1px solid #00bfa5;
    border-radius: 50%;
    opacity: 0;
  }

  .ring-1 {
    animation: verify-pulse 3s infinite;
  }
  .ring-2 {
    animation: verify-pulse 3s infinite 1.5s;
  }

  @keyframes verify-pulse {
    0% {
      transform: scale(1);
      opacity: 0.6;
    }
    100% {
      transform: scale(1.6);
      opacity: 0;
    }
  }

  .glow-effect {
    position: absolute;
    inset: 0;
    background: radial-gradient(
      circle at center,
      rgba(255, 255, 255, 0.4) 0%,
      transparent 70%
    );
    opacity: 0;
    transition: opacity 0.3s;
    border-radius: inherit;
  }

  .verify-floating-btn:hover .glow-effect {
    opacity: 1;
  }

  .btn-tooltip-left {
    position: absolute;
    right: 80px;
    background: rgba(10, 10, 10, 0.9);
    backdrop-filter: blur(12px);
    color: white;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 800;
    white-space: nowrap;
    opacity: 0;
    pointer-events: none;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    transform: translateX(20px) scale(0.8);
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
  }

  .verify-floating-btn:hover .btn-tooltip-left {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
</style>
