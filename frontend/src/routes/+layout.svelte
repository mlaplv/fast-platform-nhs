<script lang="ts">
  import "./layout.css";
  import "$lib/styles/fonts.css";
  import { setClientUi } from "$lib/state/commerce/ui.svelte";
  import QuickLoginModal from "$lib/components/storefront/auth/QuickLoginModal.svelte";
  import { setNanobotContext } from "$lib/state/nanobot.svelte";
  import { setCartStore } from "$lib/state/commerce/cart.svelte";
  import { navigating, page } from "$app/state";
  import { onMount, onDestroy, type Snippet, type Component } from "svelte";
  import { Z_INDEX_CLIENT } from "$lib/core/constants/zIndex";
  import ToastProvider from "$lib/components/storefront/ui/ToastProvider.svelte";
  import GlobalConfirmModal from "$lib/components/storefront/ui/GlobalConfirmModal.svelte";
  import ReportReviewModal from "$lib/components/storefront/reviews/ReportReviewModal.svelte";
  import { permissionState } from "$lib/state/permissions.svelte";
  import { supportAgent } from "$lib/state/commerce/supportAgent.svelte";
  import SupportAgentFAB from "$lib/components/client/support/SupportAgentFAB.svelte";
  import { untrack } from "svelte";
  import { getSearchStore } from "$lib/state/commerce/search.svelte";

  // Elite V2.2: Context initialization gated by tenant
  let { children, data } = $props();

  // Elite V2.2: Global Navigation Guard & State Reset Protocol
  $effect(() => {
    const path = page.url.pathname;
    const isNavigating = !!navigating;

    untrack(() => {
        supportAgent.setPath(path);
        
        // Elite V2.2: Instant UI Recovery Protocol
        // We force reset these states immediately on ANY navigation to prevent black screens
        if (ui) {
            ui.isHeaderHidden = false;
            ui.isFooterHidden = false;
            ui.authModal.isOpen = false;
        }

        // Reset scroll locks and overlays
        if (typeof document !== 'undefined') {
            document.body.style.overflow = '';
            document.documentElement.style.overflow = '';
        }
        
        try {
            const searchStore = getSearchStore();
            searchStore.isOverlayOpen = false;
        } catch (e) {}
    });
  });

  // Elite V2.2: Stable Admin Tenant Detection (SvelteKit-Native $app/state Page Rune)
  const isAdmin = $derived(
    data?.tenant === 'admin' || 
    page.url.hostname.startsWith('admin.') || 
    page.url.searchParams.has('admin')
  );
  
  // Safe fallback to prevent undefined UI state during hydration mismatch
  const ui = setClientUi(); 

  // Elite V2.2: Zero-Latency State Sync (Sync before template hydration to prevent DOM mismatch crashes)
  if (data?.isMobile !== undefined) {
    ui.forceMobile(data.isMobile);
  }

  // Elite V2.2: Hydration Isolation Gate
  let isMounted = $state(false);

  // Elite V2.2: Dynamic Component State (Post-Mount Resolution & Non-Overlapping Imports)
  let chatComponent = $state<Component<{ productSlug?: string }> | null>(null);
  let searchComponent = $state<Component<{ variant: string }> | null>(null);

  setNanobotContext();

  if (!isAdmin) {
    setCartStore();
  }

  // Elite V2.2: Svelte 5 Navigation Traffic Cop & Dynamic Imports
  let navigationEpoch = $state(0);

  $effect(() => {
    // Reactively track pathname changes
    const path = page.url.pathname;
    
    // Increment Epoch on each navigation
    navigationEpoch++;
    const myEpoch = navigationEpoch;

    untrack(async () => {
      if (isAdmin) return;

      try {
        let chatMod, searchMod;

        if (ui?.isMobile) {
          [chatMod, searchMod] = await Promise.all([
            import("$lib/components/client/support/SupportChatMobile.svelte"),
            import("$lib/components/storefront/product/SmartSearch.svelte")
          ]);
        } else {
          chatMod = await import("$lib/components/client/support/SupportChatDesktop.svelte");
        }

        // CHỐT CHẶN TRAFFIC COP: Bỏ qua render nếu người dùng đã chuyển trang khác
        if (myEpoch !== navigationEpoch) return;

        chatComponent = chatMod?.default || null;
        searchComponent = searchMod?.default || null;
      } catch (e) {
        console.warn("[Traffic-Cop Component Load Interrupted]", e);
      }
    });
  });

  // Elite V2.2: Neural Advisor Persona Initialization (Svelte 5 Runes-based Auto-cleanup)
  $effect(() => {
    const agentName = data.agentName;
    const path = page.url.pathname; // Reactively track navigation to reset timer
    if (isAdmin) return;

    const myEpoch = navigationEpoch;
    const timer = setTimeout(() => {
      if (myEpoch !== navigationEpoch) return;
      supportAgent.init(agentName);
    }, 3000);

    return () => clearTimeout(timer);
  });

  onMount(() => {
    isMounted = true;

    // Self-healing: Reload page on dynamic asset preload failures (common after new builds)
    if (typeof window !== 'undefined') {
      window.addEventListener('vite:preloadError', (event) => {
        console.warn("[SYSTEM] Vite preload error detected. Auto-healing by reloading page...", event);
        window.location.reload();
      });

      // bfcache (Back-Forward Cache) Auto-Healing: Auto-refresh page on browser back/forward to ensure fresh state
      window.addEventListener('pageshow', (event) => {
        if (event.persisted) {
          console.warn("[SYSTEM] Page restored from back-forward cache (bfcache). Auto-refreshing to guarantee fresh state...");
          window.location.reload();
        }
      });
    }

    // Elite V2.2: Global Identity Handshake
    permissionState.handshake();

    // Elite V3.5: Google Ads Click Protection (Real-time biometric & Canary detection)
    let adsCleanup: (() => void) | null = null;
    if (!isAdmin && typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search);
      
      // Capture CTV affiliate tracking parameter client-side for SPA routing
      const ctv = urlParams.get('ctv');
      if (ctv) {
        let ctvValue = ctv.trim();
        if (ctvValue.length <= 20) {
          ctvValue = ctvValue.toUpperCase();
        } else {
          ctvValue = ctvValue.replace(/[^A-Za-z0-9_\-=]/g, "");
        }
        if (ctvValue.length >= 4) {
          const secure = window.location.protocol === 'https:' ? '; Secure' : '';
          document.cookie = `__ctv=${ctvValue}; path=/; max-age=${7 * 24 * 60 * 60}; SameSite=Lax${secure}`;
        }
      }

      const gclid = urlParams.get('gclid');
      if (gclid) {
        let mouseEventsCount = 0;
        let touchEventsCount = 0;
        let keyEventsCount = 0;
        let maxScrollY = 0;
        let mouseAcceleration = 0;
        let interactionRhythm = 0;
        let honeypotTriggered = false;
        
        let lastMouseX = 0, lastMouseY = 0, lastMouseTime = 0;
        let clickTimes: number[] = [];
        const startTime = Date.now();

        const onMouseMove = (e: MouseEvent) => {
          mouseEventsCount++;
          const now = Date.now();
          if (lastMouseTime > 0) {
            const dt = (now - lastMouseTime) / 1000;
            if (dt > 0) {
              const dx = e.clientX - lastMouseX;
              const dy = e.clientY - lastMouseY;
              const v = Math.sqrt(dx*dx + dy*dy) / dt;
              if (v > mouseAcceleration) mouseAcceleration = v;
            }
          }
          lastMouseX = e.clientX;
          lastMouseY = e.clientY;
          lastMouseTime = now;
        };

        const onTouchMove = (e: TouchEvent) => {
          touchEventsCount++;
          const touch = e.touches[0];
          if (!touch) return;
          const now = Date.now();
          if (lastMouseTime > 0) {
            const dt = (now - lastMouseTime) / 1000;
            if (dt > 0) {
              const dx = touch.clientX - lastMouseX;
              const dy = touch.clientY - lastMouseY;
              const v = Math.sqrt(dx*dx + dy*dy) / dt;
              if (v > mouseAcceleration) mouseAcceleration = v;
            }
          }
          lastMouseX = touch.clientX;
          lastMouseY = touch.clientY;
          lastMouseTime = now;
        };

        const onClick = () => {
          clickTimes.push(Date.now());
          if (clickTimes.length > 2) {
            const diffs = clickTimes.slice(1).map((t, i) => t - clickTimes[i]);
            const mean = diffs.reduce((a,b) => a+b, 0) / diffs.length;
            interactionRhythm = diffs.reduce((a,b) => a + Math.pow(b - mean, 2), 0) / diffs.length;
          }
        };

        const onScroll = () => {
          const scrolled = window.scrollY;
          if (scrolled > maxScrollY) maxScrollY = scrolled;
        };

        const onKeyPress = () => {
          keyEventsCount++;
        };

        // Listen to honeypot
        const honeypotInput = document.getElementById('ads_honeypot_hidden') as HTMLInputElement | null;
        const triggerHoneypot = () => { honeypotTriggered = true; };

        // Bind events
        window.addEventListener('mousemove', onMouseMove, { passive: true });
        window.addEventListener('touchmove', onTouchMove, { passive: true });
        window.addEventListener('click', onClick, { passive: true });
        window.addEventListener('scroll', onScroll, { passive: true });
        window.addEventListener('keypress', onKeyPress, { passive: true });
        if (honeypotInput) {
          honeypotInput.addEventListener('focus', triggerHoneypot);
          honeypotInput.addEventListener('input', triggerHoneypot);
        }

        let reported = false;
        const sendTelemetry = async () => {
          if (reported) return;
          reported = true;

          const docHeight = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, 1);
          const winHeight = window.innerHeight;
          const scrollDepthPct = Math.min((maxScrollY / (docHeight - winHeight)) * 100, 100);

          const payload = {
            gclid: gclid,
            campaign_id: urlParams.get('utm_campaign') || null,
            ad_group_id: urlParams.get('utm_adgroup') || null,
            keyword: urlParams.get('utm_term') || null,
            ip_address: '0.0.0.0', // backend overrides this
            user_agent: navigator.userAgent,
            referrer: document.referrer || null,
            landing_url: window.location.href,
            session_duration_ms: Math.round(Date.now() - startTime),
            scroll_depth_percent: Math.round(scrollDepthPct || 0),
            mouse_events_count: mouseEventsCount,
            touch_events_count: touchEventsCount,
            key_events_count: keyEventsCount,
            screen_width: window.screen.width,
            screen_height: window.screen.height,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            language: navigator.language,
            plugins_count: navigator.plugins.length,
            webdriver_detected: navigator.webdriver || false,
            cookie_enabled: navigator.cookieEnabled,
            mouse_acceleration: mouseAcceleration,
            interaction_rhythm: interactionRhythm,
            honeypot_triggered: honeypotTriggered,
            is_high_intent: false
          };

          try {
            await fetch('/api/v1/ads-protection/validate-click', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(payload)
            });
          } catch (e) {
            console.error('[Ads-Protection] Telemetry failed:', e);
          }
        };

        const timeoutId = setTimeout(sendTelemetry, 5000);
        window.addEventListener('beforeunload', sendTelemetry);
        const visibilityHandler = () => {
          if (document.hidden) sendTelemetry();
        };
        document.addEventListener('visibilitychange', visibilityHandler);

        adsCleanup = () => {
          clearTimeout(timeoutId);
          window.removeEventListener('mousemove', onMouseMove);
          window.removeEventListener('touchmove', onTouchMove);
          window.removeEventListener('click', onClick);
          window.removeEventListener('scroll', onScroll);
          window.removeEventListener('keypress', onKeyPress);
          window.removeEventListener('beforeunload', sendTelemetry);
          document.removeEventListener('visibilitychange', visibilityHandler);
          if (honeypotInput) {
            honeypotInput.removeEventListener('focus', triggerHoneypot);
            honeypotInput.removeEventListener('input', triggerHoneypot);
          }
        };
      }
    }

    if (ui) {
      const observerCleanup = ui.initObservers();
      return () => {
        if (adsCleanup) adsCleanup();
        if (observerCleanup) observerCleanup();
      };
    }

    return () => {
      if (adsCleanup) adsCleanup();
    };
  });

  onDestroy(() => {
    // Elite V2.2: Resource Discipline
    permissionState.dispose();
    supportAgent.dispose();
  });

  const siteName = $derived(
    isAdmin 
    ? "Xohi Admin Dashboard" 
    : (ui?.settings?.basic_info?.site_name || ui?.settings?.site_name || "osmo Elite")
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

  const isFunnel = $derived(
    page.data?.product?.metadata?.landing_type && 
    page.data.product.metadata.landing_type !== 'standard'
  );
</script>

<svelte:head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0, viewport-fit=cover" />
  
  {#if isAdmin}
    <title>{siteName}</title>
    <meta name="description" content={metaDescription} />
    <meta name="theme-color" content="#020202" />
    <meta name="robots" content="noindex, nofollow" />
    
    <meta property="og:title" content={siteName} />
    <meta property="og:description" content={metaDescription} />
    <meta property="og:type" content="website" />
    <meta property="og:site_name" content={siteName} />
    <meta property="og:locale" content="vi_VN" />
  {:else}
    <meta name="theme-color" content={isFunnel ? '#020202' : '#f5f5f5'} />
  {/if}

  <link rel="icon" href="/favicon.svg" />
</svelte:head>

<!-- Premium Navigation Progress Bar (Liquid Glass) -->
{#if navigating}
    <div class="fixed top-0 left-0 right-0 h-[2px] z-[var(--z-admin-action-bar-progress)] pointer-events-none">
        <div class="h-full bg-gradient-to-r from-transparent via-[#00FFFF] to-transparent shadow-[0_0_10px_#00FFFF] animate-nav-progress"></div>
    </div>
{/if}

<div 
  class="min-h-screen {isAdmin ? 'bg-[#020202] text-gray-100 selection:bg-[#00FFFF]/20' : (isFunnel ? 'bg-[#020202] text-gray-100 selection:bg-luxury-copper/20' : 'bg-[#fafafa] text-gray-900 selection:bg-luxury-copper/20')}" 
  style="{zIndexStyles} --bg-canvas: {isAdmin ? '#010101' : (isFunnel ? '#020202' : '#fafafa')}; --text-base: {isAdmin || isFunnel ? '#ffffff' : '#111827'};"
>
  <main class="relative z-10">
    {@render children()}
  </main>

  {#if isMounted && !isAdmin}
    <!-- Elite V3.5: Honeypot / Canary Trap for Ad-fraud Bot Isolation -->
    <input type="text" id="ads_honeypot_hidden" style="opacity: 0.01; position: absolute; left: -9999px; top: -9999px; height: 1px; width: 1px; z-index: -999;" tabindex="-1" autocomplete="off" aria-hidden="true" />

    {#if ui?.authModal?.isOpen}
      <QuickLoginModal />
    {/if}

    <ToastProvider />
    <GlobalConfirmModal />
    <ReportReviewModal />

    <SupportAgentFAB isMobile={ui?.isMobile || false} />
    {#if ui?.isMobile}
      {#if chatComponent}
        {@const Chat = chatComponent}
        <Chat productSlug={page.params.slug} />
      {/if}
      {#if searchComponent}
        {@const Search = searchComponent}
        <Search variant="mobile-overlay" />
      {/if}
    {:else}
      {#if chatComponent}
        {@const Chat = chatComponent}
        <Chat productSlug={page.params.slug} />
      {/if}
    {/if}
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
