<script lang="ts">
  import { onMount } from 'svelte';
  import { Music } from 'lucide-svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import MobileActionStack from './MobileActionStack.svelte';
  import MobileBottomSheet from './MobileBottomSheet.svelte';
  import MobileVariantTabs from './MobileVariantTabs.svelte';

  // Dedicated Mobile Sections
  import MobileVideoBanner from './sections/MobileVideoBanner.svelte';
  import MobileHero from './sections/MobileHero.svelte';
  import MobileDiagnostics from './sections/MobileDiagnostics.svelte';
  import MobileScience from './sections/MobileScience.svelte';
  import MobileReviews from './sections/MobileReviews.svelte';
  import MobileOffer from './sections/MobileOffer.svelte';
  import MobileProductDetailsModal from './MobileProductDetailsModal.svelte';

  // Support Agent
  import SupportChatMobile from '$lib/components/client/support/SupportChatMobile.svelte';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte.ts';

  import './mobile.css';

  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  const shopStore = getShopStore();
  const isEditMode = $derived(liveEditStore.isEditMode);

  // Elite V2.2: Reactive switching between live data and edited data
  const product = $derived(isEditMode && liveEditStore.dirtyProduct ? liveEditStore.dirtyProduct : shopStore.product);

  // ── SEO Derived State (Elite V2.2 – Mobile Parity) ──────────────────────────
  const seoMeta = $derived(product?.seoMeta ?? product?.seo_meta ?? null);
  const siteName = $derived(product?.metadata?.seo_site_name ?? 'Elite Storefront');
  const ogImage = $derived(product?.images?.[0] ?? '');

  // Active section index tracked via IntersectionObserver (O(1) – no scroll listeners)
  let activeSectionIndex = $state(0);
  let isDetailsModalOpen = $state(false);

  // Variant tabs should be hidden when user is on the video banner (section 0)
  // Check both `video_url` (admin field) and `hero_video_url` (desktop fallback) for compatibility
  const hasVideo = $derived(
    !!(product?.metadata?.video_url || product?.metadata?.hero_video_url || product?.metadata?.hero_video)
  );

  const isTikTokVideo = $derived.by((): boolean => {
    const url = product?.metadata?.video_url || product?.metadata?.hero_video_url || product?.metadata?.hero_video || '';
    return typeof url === 'string' && url.includes('tiktok.com');
  });

  const isTikTokActive = $derived(activeSectionIndex === 0 && isTikTokVideo);

  const heroIndex = $derived(hasVideo ? 1 : 0);
  const tabsHidden = $derived(activeSectionIndex !== heroIndex);

  // 🚀 ELITE MOBILE SCROLL COORDINATOR (O(1))
  let isScrollingDown = $state(false);
  let lastScrollTop = 0;
  let scrollTicking = false;

  function handleScroll(e: Event): void {
    if (scrollTicking) return;
    scrollTicking = true;
    
    requestAnimationFrame(() => {
      const container = e.target as HTMLElement;
      if (!container) return;
      
      const currentScroll = container.scrollTop;
      if (Math.abs(currentScroll - lastScrollTop) >= 10) {
        isScrollingDown = currentScroll > lastScrollTop;
        lastScrollTop = currentScroll;
      }
      scrollTicking = false;
    });
  }

  onMount(() => {
    const sections = document.querySelectorAll<HTMLElement>('.mobile-snap-section');
    if (sections.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            const idx = Number((entry.target as HTMLElement).dataset.sectionIdx ?? 0);
            activeSectionIndex = idx;
            break;
          }
        }
      },
      { threshold: 0.6 }
    );

    sections.forEach((el, idx) => {
      el.dataset.sectionIdx = String(idx);
      observer.observe(el);
    });

    return () => observer.disconnect();
  });
</script>

<svelte:head>
  {#if seoMeta}
    <title>{seoMeta.title} | {siteName}</title>
    <meta name="description" content={seoMeta.description} />
    <meta name="keywords" content={seoMeta.keywords} />
    <meta name="robots" content="index, follow, max-image-preview:large" />
    <link rel="canonical" href={seoMeta.canonical_url} />

    <!-- Open Graph (Facebook, Threads, Telegram) -->
    <meta property="og:type" content="product" />
    <meta property="og:title" content={seoMeta.title} />
    <meta property="og:description" content={seoMeta.description} />
    <meta property="og:url" content={seoMeta.canonical_url} />
    {#if ogImage}
      <meta property="og:image" content={ogImage} />
      <meta property="og:image:width" content="1200" />
      <meta property="og:image:height" content="630" />
      <meta property="og:image:alt" content={seoMeta.title} />
    {/if}
    <meta property="og:site_name" content={siteName} />
    <meta property="og:locale" content="vi_VN" />

    <!-- Twitter / X Card -->
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content={seoMeta.title} />
    <meta name="twitter:description" content={seoMeta.description} />
    {#if ogImage}<meta name="twitter:image" content={ogImage} />{/if}

    <!-- JSON-LD Structured Data -->
    {#if seoMeta.json_ld_string}
      <!-- eslint-disable-next-line svelte/no-at-html-tags -->
      {@html `<script type="application/ld+json">${seoMeta.json_ld_string}</script>`}
    {/if}
  {:else if product}
    <title>{product.name} | {siteName}</title>
    <meta name="robots" content="noindex" />
  {/if}
</svelte:head>

<div class="mobile-snap-container relative h-screen overflow-y-auto" onscroll={handleScroll}>
  <!-- PERSISTENT OVERLAYS -->
  <MobileVariantTabs hidden={tabsHidden} />
  <MobileActionStack 
    {product} 
    {isTikTokActive}
    {isScrollingDown}
    onPurchase={() => shopStore.openCheckout()} 
    onOpenDetails={() => isDetailsModalOpen = true}
    onChat={() => supportAgent.toggle()}
  />
  {#if hasVideo}
    <section class="mobile-snap-section video-section" data-section-idx="0">
      <MobileVideoBanner {product} />
    </section>
  {/if}

  <!-- SECTION 1 (or 0 if no video): NATIVE HERO (variant slider) -->
  <section class="mobile-snap-section" data-section-idx={hasVideo ? 1 : 0}>
    <MobileHero {product} />
  </section>

  <!-- SECTION 2: NATIVE DIAGNOSTICS -->
  <section id="diagnostics-section" class="mobile-snap-section" data-section-idx={hasVideo ? 2 : 1}>
    <MobileDiagnostics {product} />
  </section>

  <!-- SECTION 3: NATIVE SCIENCE -->
  <section class="mobile-snap-section" data-section-idx={hasVideo ? 3 : 2}>
    <MobileScience {product} />
  </section>

  <!-- SECTION 4: NATIVE REVIEWS -->
  <section class="mobile-snap-section" data-section-idx={hasVideo ? 4 : 3}>
    <MobileReviews {product} />
  </section>

  <!-- SECTION 5: NATIVE OFFER -->
  <section id="offer-section" class="mobile-snap-section" data-section-idx={hasVideo ? 5 : 4}>
    <MobileOffer {product} />
  </section>

  <MobileBottomSheet bind:active={shopStore.isCheckoutOpen} {product} />
  <MobileProductDetailsModal bind:active={isDetailsModalOpen} {product} />
</div>
