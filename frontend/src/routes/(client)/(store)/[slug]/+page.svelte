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
  import { afterNavigate } from '$app/navigation';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();
  const ui = getClientUi();
  const siteUrl = "https://osmo.vn";

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
  const articleSeoMeta = $derived(data.article?.seoMeta || data.article?.seo_meta || null);
  const categorySeoMeta = $derived(data.category?.seoMeta || data.category?.seo_meta || null);

  // Elite V2.2: Semantic Breadcrumb Logic (GEO 2026)
  const breadcrumbItems = $derived.by(() => {
    const items = [{ name: 'Trang chủ', url: '/' }];
    
    if (data.type === 'category') {
      items.push({ name: data.categoryName, url: `/${data.categorySlug}/` });
    } else if (data.type === 'article' && data.article) {
      items.push({ name: 'Bài viết', url: '/bai-viet' });
      items.push({ name: data.article.title, url: `/${data.article.slug}` });
    } else if (data.type === 'product' && data.product) {
      // If product has a primary category, we could inject it here
      if (data.product.category_name && data.product.category_slug) {
        items.push({ name: data.product.category_name, url: `/${data.product.category_slug}/` });
      }
      items.push({ name: data.product.name, url: `/${data.product.slug}` });
    }
    return items;
  });

  // Elite V2.2: FAQ Extraction for SGE
  const pageFaqs = $derived(data.article?.metadata?.faqs || data.product?.metadata?.faqs || []);
</script>

<!-- SEO HEAD (SGE & AI SEARCH COMPLIANT) -->
{#if data.type === 'category' || data.type === 'news'}
  <SeoHead
    pageType="category"
    title={categorySeoMeta?.title || `${data.categoryName} | osmo Elite`}
    description={categorySeoMeta?.description || `${data.categoryName} - Sản phẩm chính hãng.`}
    canonical={categorySeoMeta?.canonical_url || `${siteUrl}/${data.categorySlug}/`}
    {breadcrumbItems}
    categoryData={{
      name: data.categoryName,
      items: data.items?.map((it: any) => ({ name: it.name, url: `/${it.slug}` }))
    }}
    jsonLdScripts={[categorySeoMeta?.json_ld_string].filter(Boolean)}
  />
{:else if data.type === 'article' && data.article}
  <SeoHead
    pageType="article"
    title={articleSeoMeta?.title || `${data.article.title} | osmo Elite`}
    description={articleSeoMeta?.description || data.article.excerpt}
    canonical={articleSeoMeta?.canonical_url || `${siteUrl}/${data.article.slug}`}
    {breadcrumbItems}
    faqs={pageFaqs}
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
    description={productSeoMeta?.description || data.product.short_description || data.product.shortDescription || data.product.description || ""}
    canonical={productSeoMeta?.canonical_url || `${siteUrl}/${data.product.slug}`}
    image={data.product.images?.[0]}
    {breadcrumbItems}
    faqs={pageFaqs}
    productData={{
      name: data.product.name,
      images: data.product.images,
      description: productSeoMeta?.description || data.product.short_description || data.product.shortDescription || "",
      brand: (data.product.attributes?.brand as string) || (data.product.attributes?.['Thương hiệu'] as string) || "osmo Elite",
      sku: data.product.sku,
      price: data.product.price,
      discountPrice: data.product.discountPrice || data.product.discount_price,
      variants: data.product.variants?.map((v: any) => ({
          name: v.sku || data.product.name,
          price: v.price,
          discountPrice: v.discountPrice || v.discount_price,
          sku: v.sku,
          availability: v.stock > 0 ? "InStock" : "OutOfStock"
      })),
      currency: "VND",
      availability: data.product.stock > 0 ? 'InStock' : 'OutOfStock',
      ratingValue: data.reviewStats?.average_rating || 5,
      reviewCount: data.reviewStats?.total_reviews || 1
    }}
    jsonLdScripts={[productSeoMeta?.json_ld_string, productSeoMeta?.breadcrumb_ld_string, productSeoMeta?.faq_ld_string].filter(Boolean)}
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
      <NewsDetailDesktop article={data.article} relatedNews={data.relatedNews} />
    {/if}
  </div>
{:else}
  <!-- PRODUCT DETAIL / FUNNEL VIEW -->
  {#if isFunnel}
    <FunnelPage {data} />
  {:else}
    {#if ui.isMobile}
      <ProductDetailMobile product={data.product} relatedProducts={data.relatedProducts} reviewStats={data.reviewStats} />
    {:else}
      <ProductDetailDesktop product={data.product} relatedProducts={data.relatedProducts} reviewStats={data.reviewStats} />
    {/if}
    

  {/if}
{/if}
