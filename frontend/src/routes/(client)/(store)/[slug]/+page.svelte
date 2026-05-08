<script lang="ts">
  import ProductDetailDesktop from '$lib/components/storefront/product-detail/MainDetail/Desktop.svelte';
  import ProductDetailMobile from '$lib/components/storefront/product-detail/MainDetail/Mobile.svelte';
  import ProductListDesktop from '$lib/components/storefront/product/ProductListDesktop.svelte';
  import ProductListMobile from '$lib/components/storefront/product/ProductListMobile.svelte';
  import NewsListDesktop from '$lib/components/storefront/news/NewsListDesktop.svelte';
  import NewsListMobile from '$lib/components/storefront/news/NewsListMobile.svelte';
  import NewsDetailDesktop from '$lib/components/storefront/news-detail/NewsDetailDesktop.svelte';
  import NewsDetailMobile from '$lib/components/storefront/news-detail/NewsDetailMobile.svelte';
  import FunnelPage from '../../[slug]-funnel/+page.svelte';
  import SeoHead from '$lib/components/storefront/seo/SeoHead.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { onMount, untrack } from 'svelte';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();
  const ui = getClientUi();
  const siteUrl = "https://osmo.vn";

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

  onMount(() => {
    return ui.initObservers();
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
  const articleSeoMeta = $derived(data.article?.seoMeta || data.article?.seo_meta || null);
  const categorySeoMeta = $derived(data.category?.seoMeta || data.category?.seo_meta || null);
</script>

<!-- SEO HEAD (SGE & AI SEARCH COMPLIANT) -->
{#if data.type === 'category' || data.type === 'news'}
  <SeoHead
    pageType="category"
    title={categorySeoMeta?.title || `${data.categoryName} | osmo Elite`}
    description={categorySeoMeta?.description || `${data.categoryName} - Sản phẩm chính hãng.`}
    canonical={categorySeoMeta?.canonical_url || `${siteUrl}/${data.categorySlug}/`}
    jsonLdScripts={[categorySeoMeta?.json_ld_string].filter(Boolean)}
  />
{:else if data.type === 'article' && data.article}
  <SeoHead
    pageType="article"
    title={articleSeoMeta?.title || `${data.article.title} | osmo Elite`}
    description={articleSeoMeta?.description || data.article.excerpt}
    canonical={articleSeoMeta?.canonical_url || `${siteUrl}/${data.article.slug}`}
    articleData={{
      headline: data.article.title,
      author: data.article.author_name || "osmo Elite",
      datePublished: data.article.created_at,
      image: data.article.featured_image
    }}
    jsonLdScripts={[articleSeoMeta?.json_ld_string].filter(Boolean)}
  />
{:else if data.type === 'product' && !isFunnel}
  <SeoHead
    pageType="product"
    title={productSeoMeta?.title || `${data.product.name} | osmo Elite`}
    description={productSeoMeta?.description || data.product.short_description}
    canonical={productSeoMeta?.canonical_url || `${siteUrl}/${data.product.slug}`}
    image={data.product.images?.[0]}
    productData={{
      name: data.product.name,
      images: data.product.images,
      description: data.product.short_description,
      brand: (data.product.attributes?.brand as string) || "osmo Elite",
      sku: data.product.sku,
      price: data.product.price,
      currency: "VND",
      availability: data.product.stock > 0 ? 'InStock' : 'OutOfStock'
    }}
    jsonLdScripts={[productSeoMeta?.json_ld_string].filter(Boolean)}
  />
{/if}

{#if data.type === 'category' || data.type === 'news'}
  <!-- CATEGORY/NEWS VIEW -->
  {#if data.type === 'news'}
    {#if ui.isMobile}
      <NewsListMobile newsList={data.items} />
    {:else}
      <NewsListDesktop newsList={data.items} categoryName={data.categoryName} />
    {/if}
  {:else}
    {#if ui.isMobile}
      <ProductListMobile products={data.items} categoryName={data.categoryName} facets={data.facets} category={data.category} />
    {:else}
      <ProductListDesktop products={data.items} categoryName={data.categoryName} categorySlug={data.categorySlug} serverTotal={data.serverTotal} facets={data.facets} category={data.category} />
    {/if}
  {/if}
{:else if data.type === 'article'}
  <!-- ARTICLE VIEW -->
  <div class="news-detail-wrapper bg-[#F5F5F5] pb-8">
    {#if ui.isMobile}
      <NewsDetailMobile article={data.article} />
    {:else}
      <NewsDetailDesktop article={data.article} />
    {/if}
  </div>
{:else}
  <!-- PRODUCT DETAIL / FUNNEL VIEW -->
  {#if isFunnel}
    <FunnelPage {data} />
  {:else}
    {#if ui.isMobile}
      <ProductDetailMobile product={data.product} relatedProducts={data.relatedProducts} />
    {:else}
      <ProductDetailDesktop product={data.product} relatedProducts={data.relatedProducts} />
    {/if}
    
    {#if import.meta.env.DEV}
      <div class="fixed bottom-0 left-0 bg-black/80 text-green-400 p-2 text-xs z-50">
        [DEBUG] Landing Type: {landingType}
      </div>
    {/if}
  {/if}
{/if}
