<script lang="ts">
  import { onMount } from "svelte";
  import { setShopStore } from "$lib/state/commerce/shop.svelte";
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import { browser } from "$app/environment";

  import SeoHead from "$lib/components/storefront/seo/SeoHead.svelte";

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

  let { data }: { data: FunnelData } = $props();

  import type { Component } from "svelte";
  let MobileLandingLayoutComponent = $state<Component<any> | null>(null);

  // Elite V2.6: Use onMount instead of $effect to prevent re-triggering on reactivity changes
  onMount(() => {
    import("./mobile/MobileFunnelLayout.svelte").then((mod) => {
      MobileLandingLayoutComponent = mod.default;
    });
  });

  const shopStore = setShopStore();
  const product = $derived(data?.product);
  const metadata = $derived(product?.metadata || {});
  const seoMeta = $derived(product?.seoMeta || product?.seo_meta || null);
  const loadingText = $derived(metadata.sync_loading_text || "SYNCHRONIZING ELITE ASSETS...");

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

    if (clientUi) {
      clientUi.isHeaderHidden = true;
      clientUi.isFooterHidden = true;
    }

    const cleanupObservers = clientUi.initObservers();

    return () => {
      shopStore.dispose();
      if (cleanupObservers) cleanupObservers();
    };
  });

  const normalizedFaqs = $derived(product?.metadata?.faqs || []);
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
  ]}
  faqs={normalizedFaqs}
/>

{#if product}
  {#if MobileLandingLayoutComponent}
    {@const MobileLandingLayout = MobileLandingLayoutComponent}
    <MobileLandingLayout
      {product}
      reviewStats={data.reviewStats}
      reviews={data.reviews}
      relatedProducts={data.relatedProducts}
    />
  {:else}
    <div class="flex flex-col items-center justify-center min-h-screen bg-[#050505] text-white">
      <div class="w-16 h-16 border-4 border-luxury-copper border-t-transparent rounded-full animate-spin mb-4"></div>
      <p class="text-sm tracking-[0.2em] font-light animate-pulse text-luxury-copper">
        {loadingText}
      </p>
    </div>
  {/if}
{/if}
