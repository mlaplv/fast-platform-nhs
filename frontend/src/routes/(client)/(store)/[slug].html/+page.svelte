<script lang="ts">
  import NewsDetailDesktop from '$lib/components/storefront/news-detail/NewsDetailDesktop.svelte';
  import NewsDetailMobile from '$lib/components/storefront/news-detail/NewsDetailMobile.svelte';
  import SeoHead from '$lib/components/storefront/seo/SeoHead.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { afterNavigate } from '$app/navigation';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();
  const ui = getClientUi();

  afterNavigate(() => {
    if (typeof window !== 'undefined') {
      window.scrollTo({ top: 0, behavior: 'instant' });
    }
  });

  const seo = $derived(data.article?.seoMeta ?? null);

  const breadcrumbItems = $derived([
    { name: 'Trang chủ', url: '/' },
    { name: 'Bài viết', url: '/bai-viet' },
    ...(data.article ? [{ name: data.article.title, url: `/${data.article.slug}.html` }] : [])
  ]);

  const pageFaqs = $derived(data.article?.metadata?.faqs ?? []);
</script>

{#if data.article}
  <SeoHead
    pageType="article"
    title={seo?.title || data.article.title}
    description={seo?.description || data.article.excerpt || ''}
    canonical={seo?.canonical_url || ''}
    keywords={seo?.keywords || ''}
    image={data.article.featuredImage || data.article.featured_image || ''}
    {breadcrumbItems}
    faqs={pageFaqs}
    articleData={{
      headline: data.article.title,
      author: data.article.author || data.article.author_name || '',
      datePublished: data.article.publishedAt || data.article.published_at || data.article.created_at || '',
      image: data.article.featuredImage || data.article.featured_image || ''
    }}
    jsonLdScripts={[seo?.json_ld_string, seo?.breadcrumb_ld_string, seo?.faq_ld_string].filter(Boolean)}
  />
{/if}

<div class="news-detail-wrapper bg-[#F5F5F5] pb-8">
  {#if ui.isMobile}
    <NewsDetailMobile article={data.article} />
  {:else}
    <NewsDetailDesktop article={data.article} relatedNews={data.relatedNews} />
  {/if}
</div>
