<script lang="ts">
  import NewsDetailDesktop from '$lib/components/storefront/news-detail/NewsDetailDesktop.svelte';
  import NewsDetailMobile from '$lib/components/storefront/news-detail/NewsDetailMobile.svelte';
  import SeoHead from '$lib/components/storefront/seo/SeoHead.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { afterNavigate } from '$app/navigation';
  import { page } from '$app/stores';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();
  const ui = getClientUi();
  const siteUrl = $derived($page.url.origin);
  const siteName = $derived(ui.settings?.basic_info?.site_name || ui.settings?.site_name || "SmartShop");

  // Elite V2.2: Route Navigation Scroll Restoration Shield
  afterNavigate(() => {
    if (typeof window !== 'undefined') {
      window.scrollTo({ top: 0, behavior: 'instant' });
      setTimeout(() => {
        window.scrollTo({ top: 0, behavior: 'instant' });
      }, 50);
    }
  });

  // SEO Derived State (Elite V2.2)
  const articleSeoMeta = $derived(data.article?.seoMeta || data.article?.seo_meta || null);

  // Elite V2.2: Semantic Breadcrumb Logic (GEO 2026)
  const breadcrumbItems = $derived.by(() => {
    const items = [{ name: 'Trang chủ', url: '/' }];
    if (data.article) {
      items.push({ name: 'Bài viết', url: '/bai-viet' });
      items.push({ name: data.article.title, url: `/${data.article.slug}.html` });
    }
    return items;
  });

  // Elite V2.2: FAQ Extraction for SGE
  const pageFaqs = $derived(data.article?.metadata?.faqs || []);
</script>

<!-- SEO HEAD (SGE & AI SEARCH COMPLIANT) -->
{#if data.article}
  <SeoHead
    pageType="article"
    title={articleSeoMeta?.title || `${data.article.title} | ${siteName}`}
    description={articleSeoMeta?.description || data.article.excerpt || ""}
    canonical={articleSeoMeta?.canonical_url || `${siteUrl}/${data.article.slug}.html`}
    {breadcrumbItems}
    faqs={pageFaqs}
    articleData={{
      headline: data.article.title,
      author: data.article.author_name || siteName,
      datePublished: data.article.created_at,
      image: data.article.featured_image
    }}
    jsonLdScripts={[articleSeoMeta?.json_ld_string].filter(Boolean)}
  />
{/if}

<div class="news-detail-wrapper bg-[#F5F5F5] pb-8">
  {#if ui.isMobile}
    <NewsDetailMobile article={data.article} />
  {:else}
    <NewsDetailDesktop article={data.article} relatedNews={data.relatedNews} />
  {/if}
</div>
