import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';
import { normalizeSeoMeta, type NormalizedSeoMeta } from '$lib/utils/seo';
import { browser } from '$app/environment';
import { resolveOptimizedImageUrl, extractIdFromUrl } from '$lib/state/utils';

export const trailingSlash = 'ignore';

const resolvedCache = new Map<string, string>();

async function resolveDirectCacheUrl(fetchFn: typeof fetch, originalUrl: string, width: number): Promise<string> {
  const isVideo = /\.(mp4|webm|mov|ogg|ogv|avi|mkv)$/.test(originalUrl.split('?')[0].toLowerCase());
  if (isVideo) return originalUrl;

  const optUrl = resolveOptimizedImageUrl(originalUrl, width);
  const id = extractIdFromUrl(originalUrl);
  if (id) {
    const fname = originalUrl.split('?')[0].split('/').pop() || '';
    const suffix = fname.endsWith('.webp') ? fname : fname + '.webp';
    return `/v65_assets/cache/t_${width}_75_${suffix}`;
  }
  return optUrl;
}

interface ArticleFaq {
  question: string;
  answer: string;
}

interface Article {
  id: string;
  title: string;
  slug: string;
  content?: string;
  excerpt?: string;
  featured_image?: string;
  featuredImage?: string;
  category?: string;
  author?: string;
  author_name?: string;
  created_at?: string;
  published_at?: string;
  publishedAt?: string;
  metadata?: { faqs?: ArticleFaq[] };
  seoMeta?: NormalizedSeoMeta | null;
}

export const load: PageLoad = async ({ params, fetch }) => {
  const { slug } = params;

  const [artRes, newsRes] = await Promise.all([
    fetch(`/api/v1/client/news/slug/${slug}`, { signal: AbortSignal.timeout(3000) }),
    fetch(`/api/v1/client/news`, { signal: AbortSignal.timeout(3000) }).catch(() => null)
  ]);

  if (!artRes.ok) {
    throw error(404, { message: `Không tìm thấy bài viết: ${slug}.html` });
  }

  const artData = await artRes.json() as Record<string, unknown>;
  const rawSeo = (artData.seoMeta ?? artData.seo_meta) as Record<string, unknown> | null;

  const article: Article = {
    ...(artData as Omit<Article, 'seoMeta'>),
    seoMeta: normalizeSeoMeta(rawSeo, String(artData.title ?? ''))
  };

  const featuredImg = article.featuredImage || article.featured_image || '';

  const [resolvedMobileLcpUrl, resolvedDesktopLcpUrl] = await Promise.all([
    featuredImg ? resolveDirectCacheUrl(fetch, featuredImg, 600) : Promise.resolve(''),
    featuredImg ? resolveDirectCacheUrl(fetch, featuredImg, 1000) : Promise.resolve('')
  ]);

  let relatedNews: Article[] = [];
  if (newsRes?.ok) {
    const newsData = await newsRes.json() as Record<string, unknown>;
    const allNews = (Array.isArray(newsData)
      ? newsData
      : ((newsData.data ?? newsData.items ?? []) as unknown[])
    ) as Article[];
    relatedNews = allNews.filter(n => n.id !== article.id).slice(0, 3);
  }

  return {
    type: 'article' as const,
    article,
    relatedNews,
    resolvedMobileLcpUrl,
    resolvedDesktopLcpUrl
  };
};
