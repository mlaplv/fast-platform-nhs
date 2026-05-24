<script lang="ts">
  import type { Component } from 'svelte';
  import type { Product, Category, ReviewStats, Article } from '$lib/types';

  import FunnelPage from '../../[slug]-funnel/+page.svelte';
  import SeoHead from '$lib/components/storefront/seo/SeoHead.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { onMount, untrack } from 'svelte';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte';
  import { afterNavigate } from '$app/navigation';
  import { page } from '$app/stores';
  import type { PageData } from './$types';

  import type { PageData as FunnelPageData } from '../../[slug]-funnel/$types';

  let { data }: { data: PageData } = $props();
  const ui = getClientUi();
  const siteUrl = $derived($page.url.origin);
  const siteName = $derived(ui.settings?.basic_info?.site_name || ui.settings?.name || "SmartShop");

  // Elite V2.2: Dynamic components to prevent overlapping loading
  let activeDetailComponent = $state<Component<{
    product: Product;
    relatedProducts?: Product[];
    reviewStats?: ReviewStats | null;
  }> | null>(null);

  interface NewsItem {
    id: string;
    slug: string;
    title: string;
    excerpt?: string;
    featuredImage: string;
    category?: string;
    createdAt?: string;
  }

  let activeListComponent = $state<Component<{
    products: Product[];
    categoryName: string;
    categorySlug: string;
    serverTotal: number;
    facets?: Record<string, unknown> | null;
    category: Category | null;
  }> | null>(null);

  let activeNewsComponent = $state<Component<{
    newsList: NewsItem[];
    categoryName?: string;
  }> | null>(null);

  // Elite V2.2: Parallel JIT dynamic imports on mount
  onMount(async () => {
    try {
      if (data.isMobile) {
        const [detailMod, listMod, newsMod] = await Promise.all([
          import('$lib/components/storefront/product-detail/MainDetail/Mobile.svelte'),
          import('$lib/components/storefront/product/ProductListMobile.svelte'),
          import('$lib/components/storefront/news/NewsListMobile.svelte')
        ]);
        activeDetailComponent = detailMod.default;
        activeListComponent = listMod.default;
        activeNewsComponent = newsMod.default;
      } else {
        const [detailMod, listMod, newsMod] = await Promise.all([
          import('$lib/components/storefront/product-detail/MainDetail/Desktop.svelte'),
          import('$lib/components/storefront/product/ProductListDesktop.svelte'),
          import('$lib/components/storefront/news/NewsListDesktop.svelte')
        ]);
        activeDetailComponent = detailMod.default;
        activeListComponent = listMod.default;
        activeNewsComponent = newsMod.default;
      }
    } catch (e) {
      console.error("[SYSTEM FAULT] Dynamic storefront page components failed to load:", e);
    }
  });

  // Elite V2.2: Route Navigation Scroll Restoration Shield
  afterNavigate(() => {
    if (typeof window !== 'undefined') {
      window.scrollTo({ top: 0, behavior: 'instant' });
      setTimeout(() => {
        window.scrollTo({ top: 0, behavior: 'instant' });
      }, 50);
    }
  });

  // Elite V2.2: Reactive Funnel Detection (Zero-Latency Sync)
  const landingType = $derived(data.product?.metadata?.landing_type || 'standard');
  const isFunnel = $derived(landingType !== 'standard');

  // Elite V2.2: Dynamic Layout Sync (Viral 2026 Protocol)
  $effect(() => {
    if (isFunnel || ui.isMobile) {
      ui.isHeaderHidden = true;
      ui.isFooterHidden = true;
    } else {
      ui.isHeaderHidden = false;
      ui.isFooterHidden = false;
    }

    return () => {
      // Auto-restore on unmount
      ui.isHeaderHidden = false;
      ui.isFooterHidden = false;
    };
  });

  // Elite V6.3: Neural Product Sync (Reactive Name Only)
  $effect(() => {
    const pName = data.product?.name || "";
    untrack(() => {
        supportAgent.currentProductName = pName;
    });
    return () => {
        untrack(() => {
            supportAgent.currentProductName = "";
        });
    };
  });

  // SEO Derived State (Elite V2.2)
  const productSeoMeta = $derived(data.product?.seoMeta || data.product?.seo_meta || null);
  const categorySeoMeta = $derived(data.category?.seoMeta || data.category?.seo_meta || null);

  // Elite V2.2: Semantic Breadcrumb Logic (GEO 2026)
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

  // Elite V2.2: FAQ Extraction for SGE
  const pageFaqs = $derived(data.product?.metadata?.faqs || []);

  // Elite V2.2: Define precise PageData subsets to resolve Svelte-check compiler issues
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

  // Cast page data securely for FunnelPage component
  const funnelPageData = $derived(isFunnel && productData ? (productData as unknown as FunnelPageData) : null);
</script>

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
      images: productData.product.images,
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

{#if data.type === 'category' || data.type === 'news'}
  <!-- CATEGORY/NEWS VIEW -->
  {#if data.type === 'news' && newsData}
    {#if activeNewsComponent}
      {@const NewsComponent = activeNewsComponent}
      <NewsComponent newsList={newsData.items} categoryName={newsData.categoryName} />
    {/if}
  {:else if categoryData}
    {#if activeListComponent}
      {@const ListComponent = activeListComponent}
      <ListComponent 
        products={categoryData.items} 
        categoryName={categoryData.categoryName} 
        categorySlug={categoryData.categorySlug} 
        serverTotal={categoryData.serverTotal} 
        facets={categoryData.facets} 
        category={categoryData.category} 
      />
    {/if}
  {/if}

{:else if productData}
  <!-- PRODUCT DETAIL / FUNNEL VIEW -->
  {#if isFunnel && funnelPageData}
    <FunnelPage data={funnelPageData} />
  {:else}
    {#if activeDetailComponent}
      {@const DetailComponent = activeDetailComponent}
      <DetailComponent 
        product={productData.product} 
        relatedProducts={productData.relatedProducts as Product[] | undefined} 
        reviewStats={productData.reviewStats} 
      />
    {/if}
  {/if}
{/if}
