<script lang="ts">
  import { setShopStore } from "$lib/state/commerce/shop.svelte";
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import { browser } from "$app/environment";

  import SeoHead from "$lib/components/storefront/seo/SeoHead.svelte";
  import MobileFunnelLayout from "./mobile/MobileFunnelLayout.svelte";

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



  const shopStore = setShopStore();
  const product = $derived(data?.product);
  const metadata = $derived(product?.metadata || {});
  const seoMeta = $derived(product?.seoMeta || product?.seo_meta || null);
  const loadingText = $derived(metadata.sync_loading_text || "Loading...");

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

  import { onMount } from "svelte";

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
  title={seoMeta?.title || product?.name || (clientUi.settings?.basic_info?.site_name || "osmo.vn")}
  description={seoMeta?.description ||
    product?.shortDescription ||
    product?.short_description ||
    product?.description ||
    ""}
  image={product?.images?.[0] || ""}
  keywords={seoMeta?.keywords || ""}
  siteName={seoMeta?.site_name || product?.metadata?.seo_site_name || (clientUi.settings?.basic_info?.site_name || "osmo.vn")}
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
    ratingValue: data?.reviewStats?.average_rating || undefined,
    reviewCount: data?.reviewStats?.total_count || undefined,
  }}
  jsonLdScripts={[
    seoMeta?.json_ld_string,
    seoMeta?.breadcrumb_ld_string,
    seoMeta?.faq_ld_string,
  ]}
  faqs={normalizedFaqs}
/>

{#if product}
  <MobileFunnelLayout
    {product}
    reviewStats={data.reviewStats}
    reviews={data.reviews}
    relatedProducts={data.relatedProducts}
    resolvedLcpUrl={data.resolvedMobileLcpUrl}
  />
{/if}
