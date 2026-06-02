<script lang="ts">
  import type { Product, Category, ReviewStats } from '$lib/types';
  import type { Component } from 'svelte';

  import SeoHead from '$lib/components/storefront/seo/SeoHead.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { onMount, untrack } from 'svelte';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte';
  import { afterNavigate } from '$app/navigation';
  import { page } from '$app/stores';
  import type { PageData } from './$types';
  import type { PageData as FunnelPageData } from '../../[slug]-funnel/$types';
  import { resolveOptimizedImageUrl } from '$lib/state/utils';


  // ── Dynamic Component State (Zero Bundle Overlap) ──────────────────────────
  // Each component is isolated in its own Vite chunk.
  // A mobile user NEVER downloads desktop code, and vice versa.
  // Funnel/Landing is completely separate from product-detail bundles.
  let activeComponent = $state<Component<any> | null>(null);
  let activeProps = $state<Record<string, unknown>>({});

  let { data }: { data: PageData } = $props();
  const ui = getClientUi();
  const siteUrl = $derived($page.url.origin);
  const siteName = $derived(ui.settings?.basic_info?.site_name || ui.settings?.name || 'SmartShop');

  interface NewsItem {
    id: string;
    slug: string;
    title: string;
    excerpt?: string;
    featuredImage: string;
    category?: string;
    createdAt?: string;
  }

  // Route Navigation Scroll Restoration Shield
  afterNavigate(() => {
    if (typeof window !== 'undefined') {
      window.scrollTo({ top: 0, behavior: 'instant' });
      setTimeout(() => {
        window.scrollTo({ top: 0, behavior: 'instant' });
      }, 50);
    }
  });

  // Reactive Funnel Detection
  const landingType = $derived(data.product?.metadata?.landing_type || 'standard');
  const isFunnel = $derived(landingType !== 'standard');

  // Dynamic Layout Sync — pre-paint synchronization
  $effect.pre(() => {
    if (isFunnel || ui.isMobile) {
      ui.isHeaderHidden = true;
      ui.isFooterHidden = true;
    } else {
      ui.isHeaderHidden = false;
      ui.isFooterHidden = false;
    }
    return () => {
      ui.isHeaderHidden = false;
      ui.isFooterHidden = false;
    };
  });

  // Neural Product Sync (Reactive Name Only)
  $effect(() => {
    const pName = data.product?.name || '';
    untrack(() => { supportAgent.currentProductName = pName; });
    return () => { untrack(() => { supportAgent.currentProductName = ''; }); };
  });

  // SEO Derived State
  const productSeoMeta = $derived(data.product?.seoMeta || data.product?.seo_meta || null);
  const categorySeoMeta = $derived(data.category?.seoMeta || data.category?.seo_meta || null);

  // Semantic Breadcrumb Logic
  const breadcrumbItems = $derived.by(() => {
    const items = [{ name: 'Trang chủ', url: '/' }];
    if (data.type === 'category') {
      items.push({ name: data.categoryName, url: `/${data.categorySlug}/` });
    } else if (data.type === 'product' && data.product) {
      if (data.product.category_name && data.product.category_slug) {
        items.push({ name: data.product.category_name, url: `/${data.product.category_slug}/` });
      }
      items.push({ name: data.product.name, url: `/${data.product.slug}` });
    }
    return items;
  });

  const pageFaqs = $derived(data.product?.metadata?.faqs || []);

  interface CategoryPageData {
    type: 'category';
    categoryName: string;
    categorySlug: string;
    category: Category | null;
    serverTotal: number;
    items: Product[];
    facets?: Record<string, unknown> | null;
  }
  interface ProductPageData {
    type: 'product';
    product: Product;
    reviewStats: ReviewStats | null;
    relatedProducts: Product[];
  }
  interface NewsPageData {
    type: 'news';
    categoryName: string;
    items: NewsItem[];
  }

  const categoryData = $derived(data.type === 'category' ? (data as unknown as CategoryPageData) : null);
  const productData = $derived(data.type === 'product' ? (data as unknown as ProductPageData) : null);
  const newsData = $derived(data.type === 'news' ? (data as unknown as NewsPageData) : null);
  const funnelPageData = $derived(isFunnel && productData ? (productData as unknown as FunnelPageData) : null);

  // ── Elite Code Splitting: Load exactly ONE bundle per user session ──────────
  // Vite creates separate async chunks for each branch:
  //   chunk-funnel        → Landing/Viral pages
  //   chunk-product-desk  → Desktop product detail
  //   chunk-product-mob   → Mobile product detail
  //   chunk-list-desk     → Desktop category/search list
  //   chunk-list-mob      → Mobile category list
  //   chunk-news-desk     → Desktop news list
  //   chunk-news-mob      → Mobile news list
  $effect(() => {
    // Reactively track pathname, type, and device state
    const type = data.type;
    const isMobile = ui.isMobile;
    const path = $page.url.pathname;

    untrack(async () => {
      try {
        if (type === 'product' && productData) {
          if (isFunnel && funnelPageData) {
            // ── Funnel / Landing (isolated chunk) ─────────────────────────────
            const { default: FunnelPage } = await import('../../[slug]-funnel/+page.svelte');
            activeComponent = FunnelPage;
            activeProps = { data: funnelPageData };
          } else if (isMobile) {
            // ── Mobile Product Detail (isolated chunk) ─────────────────────────
            const { default: ProductDetailMobile } = await import(
              '$lib/components/storefront/product-detail/MainDetail/Mobile.svelte'
            );
            activeComponent = ProductDetailMobile;
            activeProps = {
              product: productData.product,
              relatedProducts: productData.relatedProducts,
              reviewStats: productData.reviewStats
            };
          } else {
            // ── Desktop Product Detail (isolated chunk) ─────────────────────────
            const { default: ProductDetailDesktop } = await import(
              '$lib/components/storefront/product-detail/MainDetail/Desktop.svelte'
            );
            activeComponent = ProductDetailDesktop;
            activeProps = {
              product: productData.product,
              relatedProducts: productData.relatedProducts,
              reviewStats: productData.reviewStats
            };
          }
        } else if (type === 'news' && newsData) {
          if (isMobile) {
            const { default: NewsListMobile } = await import(
              '$lib/components/storefront/news/NewsListMobile.svelte'
            );
            activeComponent = NewsListMobile;
            activeProps = { newsList: newsData.items, categoryName: newsData.categoryName };
          } else {
            const { default: NewsListDesktop } = await import(
              '$lib/components/storefront/news/NewsListDesktop.svelte'
            );
            activeComponent = NewsListDesktop;
            activeProps = { newsList: newsData.items, categoryName: newsData.categoryName };
          }
        } else if (type === 'category' && categoryData) {
          if (isMobile) {
            const { default: ProductListMobile } = await import(
              '$lib/components/storefront/product/ProductListMobile.svelte'
            );
            activeComponent = ProductListMobile;
            activeProps = {
              products: categoryData.items,
              categoryName: categoryData.categoryName,
              categorySlug: categoryData.categorySlug,
              serverTotal: categoryData.serverTotal,
              facets: categoryData.facets,
              category: categoryData.category
            };
          } else {
            const { default: ProductListDesktop } = await import(
              '$lib/components/storefront/product/ProductListDesktop.svelte'
            );
            activeComponent = ProductListDesktop;
            activeProps = {
              products: categoryData.items,
              categoryName: categoryData.categoryName,
              categorySlug: categoryData.categorySlug,
              serverTotal: categoryData.serverTotal,
              facets: categoryData.facets,
              category: categoryData.category
            };
          }
        }
      } catch (e) {
        console.error('[PageRouter] Dynamic component import failed:', e);
      }
    });
  });
</script>

<!-- Elite LCP Optimization: Preload hero product image with precise device-optimized resolution to avoid double downloads and maximize LCP -->
<svelte:head>
  {#if productData?.product}
    {@const heroImage = (() => {
      const p = productData.product;
      const tierVar = p.tierVariations?.[0] || p.tier_variations?.[0] || p.attributes?.tier_variations?.[0];
      if (data.isMobile) {
        if (tierVar) {
          const mobImgs = (tierVar.mobile_images || tierVar.mobileImages || []).filter(Boolean);
          if (mobImgs.length > 0) return mobImgs[0];
          const deskImgs = (tierVar.images || []).filter(Boolean);
          if (deskImgs.length > 0) return deskImgs[0];
        }
      } else {
        if (tierVar) {
          const deskImgs = (tierVar.images || []).filter(Boolean);
          if (deskImgs.length > 0) return deskImgs[0];
        }
      }
      return p.images?.[0];
    })()}
    {#if heroImage}
      {@const isVideo = /\.(mp4|webm|mov|ogg|ogv|avi|mkv)$/.test(heroImage.split('?')[0].toLowerCase())}
      {#if isVideo}
        <link rel="preload" as="video" type="video/mp4" href={heroImage} fetchpriority="high" />
      {:else}
        {@const preloadUrl = resolveOptimizedImageUrl(heroImage, data.isMobile ? 600 : 800)}
        <link rel="preload" as="image" href={preloadUrl} fetchpriority="high" />
      {/if}
    {/if}
  {/if}
</svelte:head>


<!-- SEO HEAD (SGE & AI SEARCH COMPLIANT) -->
{#if data.type === 'category' || data.type === 'news'}
  <SeoHead
    pageType="category"
    title={categorySeoMeta?.title || `${data.categoryName} | ${siteName}`}
    description={categorySeoMeta?.description || `${data.categoryName} - Sản phẩm chính hãng.`}
    canonical={categorySeoMeta?.canonical_url || `${siteUrl}/${data.categorySlug}/`}
    keywords={categorySeoMeta?.keywords || ""}
    {breadcrumbItems}
    categoryData={{
      name: data.categoryName,
      items: categoryData?.items?.map((it) => ({ name: it.name, url: `/${it.slug}` }))
    }}
    jsonLdScripts={[categorySeoMeta?.json_ld_string, categorySeoMeta?.breadcrumb_ld_string, categorySeoMeta?.faq_ld_string].filter(Boolean)}
  />

{:else if data.type === 'product' && !isFunnel && productData}
  <SeoHead
    pageType="product"
    title={productSeoMeta?.title || `${productData.product.name} | ${siteName}`}
    description={productSeoMeta?.description || productData.product.short_description || productData.product.shortDescription || productData.product.description || ""}
    canonical={productSeoMeta?.canonical_url || `${siteUrl}/${productData.product.slug}`}
    image={productData.product.images?.[0]}
    {breadcrumbItems}
    faqs={pageFaqs}
    productData={{
      name: productData.product.name,
      images: Array.from(new Set([
        ...(productData.product.images || []),
        ...(productData.product.tierVariations?.[0]?.images || [])
      ])).filter(Boolean),
      description: productSeoMeta?.description || productData.product.short_description || productData.product.shortDescription || "",
      brand: (productData.product.attributes?.brand as string) || (productData.product.attributes?.['Thương hiệu'] as string) || siteName,
      sku: productData.product.sku,
      price: productData.product.price,
      discountPrice: productData.product.discountPrice || productData.product.discount_price,
      variants: productData.product.variants?.map((v: {sku?: string, price: number, discountPrice?: number, discount_price?: number, stock: number}) => ({
          name: v.sku || productData.product.name,
          price: v.price,
          discountPrice: v.discountPrice || v.discount_price,
          sku: v.sku,
          availability: v.stock > 0 ? "InStock" : "OutOfStock"
      })),
      currency: "VND",
      availability: productData.product.stock > 0 ? 'InStock' : 'OutOfStock',
      ratingValue: productData.reviewStats?.average_rating || 5,
      reviewCount: productData.reviewStats?.total_count || 1
    }}
    jsonLdScripts={[productSeoMeta?.json_ld_string, productSeoMeta?.breadcrumb_ld_string, productSeoMeta?.faq_ld_string].filter(Boolean)}
  />
{/if}

{#if activeComponent}
  {@const DynamicComponent = activeComponent}
  <DynamicComponent {...activeProps} />
{:else}
  <!-- Elite 2026: Zero-CLS Luxury Skeleton Placeholders to prevent UI flashes during lazy bundle load -->
  <div class="flex flex-col items-center justify-center gap-3 transition-colors duration-300 {isFunnel ? 'min-h-screen bg-[#020202] text-stone-400' : 'min-h-[88vh] bg-gradient-to-br from-[#faf8f5] to-[#f2e6d8] text-stone-600'}" style="width: 100%;">
    <div class="w-8 h-8 rounded-full border-2 animate-spin {isFunnel ? 'border-stone-800' : 'border-stone-200'}" style="border-top-color: var(--color-luxury-copper, #C18F7E);"></div>
    <span class="text-[9px] font-black tracking-widest uppercase {isFunnel ? 'text-stone-500/80' : 'text-stone-600/70'}">Đang tải giao diện...</span>
  </div>
{/if}
