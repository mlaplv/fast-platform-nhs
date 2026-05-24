import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';
import { normalizeSeoMeta, type NormalizedSeoMeta } from '$lib/utils/seo';

export const trailingSlash = 'ignore';

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

  let relatedNews: Article[] = [];
  if (newsRes?.ok) {
    const newsData = await newsRes.json() as Record<string, unknown>;
    const allNews = (Array.isArray(newsData)
      ? newsData
      : ((newsData.data ?? newsData.items ?? []) as unknown[])
    ) as Article[];
    relatedNews = allNews.filter(n => n.id !== article.id).slice(0, 3);
  }

  return { type: 'article' as const, article, relatedNews };
};
