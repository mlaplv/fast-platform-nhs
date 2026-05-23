import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, url }) => {
  const query = url.searchParams.get('q') ?? '';

  if (!query) {
    return {
      products: [],
      total: 0,
      searchQuery: '',
      facets: null,
      articles: []
    };
  }

  const params = new URLSearchParams();
  params.set('search', query);

  const targetUrl = `/api/v1/client/products?${params.toString()}`;
  const articleUrl = `/api/v1/client/news/search?q=${encodeURIComponent(query)}&limit=6`;

  try {
    const [prodRes, artRes] = await Promise.all([
      fetch(targetUrl),
      fetch(articleUrl).catch(e => {
        console.error("[ARTICLE SEARCH FAILED]", e);
        return null;
      })
    ]);

    if (!prodRes.ok) {
      throw error(prodRes.status, {
        message: `API Error: ${prodRes.statusText} (${prodRes.status})`,
        details: `Failed to fetch products`
      });
    }

    const prodData = await prodRes.json();
    let articles = [];
    if (artRes && artRes.ok) {
      try {
        articles = await artRes.json();
      } catch (e) {
        console.error("Failed to parse article search JSON", e);
      }
    }

    return { 
      products: prodData.data ?? (Array.isArray(prodData) ? prodData : (prodData.items || prodData.products || [])),
      total: prodData.total ?? 0,
      searchQuery: query,
      facets: prodData.facets ?? null,
      articles: articles
    };
  } catch (e: unknown) {
    if (e && typeof e === 'object' && 'status' in e) {
      throw e;
    }
    const err = e as Error;
    console.error(`[FETCH FAILED], không thể kết nối tới Backend!`);
    console.error(`Error: ${err.message}`);
    throw error(503, {
      message: "Dịch vụ tạm thời không khả dụng (Backend Connection Failed)"
    });
  }
};
