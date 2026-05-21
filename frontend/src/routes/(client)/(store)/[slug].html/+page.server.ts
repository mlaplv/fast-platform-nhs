import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { ServerEnv } from '$lib/server/env';

export const trailingSlash = 'ignore';

interface Article {
  id: string;
  title: string;
  slug: string;
  content?: string;
  excerpt?: string;
  featured_image?: string;
  category?: string;
}

export const load: PageServerLoad = async ({ params, fetch }) => {
  const apiUrl = ServerEnv.INTERNAL_API_URL;
  const tenantId = ServerEnv.TENANT_ID;
  const { slug } = params;

  const articleUrl = `${apiUrl}/api/v1/client/news/slug/${slug}`;

  const newsUrl = `${apiUrl}/api/v1/client/news`;

  try {
    const [artRes, newsRes] = await Promise.all([
      fetch(articleUrl, {
        headers: { 'x-tenant': tenantId },
        signal: AbortSignal.timeout(3000)
      }),
      fetch(newsUrl, {
        headers: { 'x-tenant': tenantId },
        signal: AbortSignal.timeout(3000)
      }).catch(e => {
        console.error(`[RELATED NEWS FETCH FAILED] slug: ${slug}`, e);
        return null;
      })
    ]);

    if (artRes.ok) {
      const artData = await artRes.json();
      const article = artData as Article;
      let relatedNews: Article[] = [];

      if (newsRes && newsRes.ok) {
        const newsData = await newsRes.json();
        const allNews = (Array.isArray(newsData) ? newsData : (newsData.data || newsData.items || [])) as Article[];
        relatedNews = allNews
          .filter((n: Article) => n.id !== article.id)
          .slice(0, 3);
      }

      return {
        type: 'article',
        article,
        relatedNews,
        metadata: {
          timestamp: new Date().toISOString()
        }
      };
    }
  } catch (artErr) {
    console.error(`[ARTICLE FETCH SYSTEM ERROR] slug: ${slug}`, artErr);
  }

  throw error(404, { message: `Không tìm thấy bài viết cho: ${slug}.html` });
};
