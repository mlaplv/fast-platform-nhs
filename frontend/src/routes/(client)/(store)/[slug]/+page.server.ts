import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { ServerEnv } from '$lib/server/env';
import { isMobileDevice } from '$lib/utils/device';

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

export const load: PageServerLoad = async ({ params, fetch, request, url }) => {
  const apiUrl = ServerEnv.INTERNAL_API_URL;
  const tenantId = ServerEnv.TENANT_ID;
  const { slug } = params;
  const hasTrailingSlash = url.pathname.endsWith('/');

  // Rule 2.2: Standardize Structure
  // 1. If it ends with '/', it MUST be a Category
  if (hasTrailingSlash) {
    if (slug === 'tin-tuc') {
       // News list is explicitly NOT allowed with a trailing slash as per Sếp's simplified rule
       throw error(404, { message: "Không tìm thấy nội dung (Dấu '/' không được phép cho tin bài)" });
    }

    // TĂNG GIỚI HẠN LÊN 49: 1 sp cho banner + 48 sp cho grid (4 cột x 12 hàng)
    const productsUrl = `${apiUrl}/api/v1/client/products/?category_slug=${slug}&limit=49&status=ACTIVE`;
    try {
      const catRes = await fetch(productsUrl, { 
        headers: { 'x-tenant': tenantId },
        signal: AbortSignal.timeout(5000)
      });
      if (catRes.ok) {
        const data = await catRes.json();
        const items = (data.data || []) as unknown[];
        const total = data.total || items.length;

        return {
          type: 'category',
          categoryName: slug.replace(/-/g, ' ').toUpperCase(),
          categorySlug: slug,
          serverTotal: total,
          items
        };
      }
    } catch (e) {
      console.error(`[CATEGORY FETCH FAILED] slug: ${slug}`, e);
    }
    
    throw error(404, { message: `Danh mục không tồn tại: ${slug}/` });
  }

  // 2. If it does NOT end with '/', it's either News List or Product
  if (slug === 'tin-tuc') {
    const newsUrl = `${apiUrl}/api/v1/client/news`;
    try {
      const newsRes = await fetch(newsUrl, { 
        headers: { 'x-tenant': tenantId },
        signal: AbortSignal.timeout(5000)
      });
      if (newsRes.ok) {
        const data = await newsRes.json();
        return {
          type: 'news',
          categoryName: 'GÓC TIN TỨC ELITE',
          items: (Array.isArray(data) ? data : (data.data || data.items || [])) as Article[]
        };
      }
    } catch (e) {
      console.error(`[NEWS FETCH FAILED]`, e);
    }
    throw error(404, { message: "Hiện tại chưa có tin tức nào." });
  }

  // 3. Try Product (Standard Slug)
  const productUrl = `${apiUrl}/api/v1/client/products/slug/${slug}`;
  const relatedUrl = `${apiUrl}/api/v1/client/products/?limit=9`; // Fetch 9 to safely exclude current product and keep 8

  try {
    const prodRes = await fetch(productUrl, { 
      headers: { 'x-tenant': tenantId },
      signal: AbortSignal.timeout(5000)
    });
    if (prodRes.ok) {
      const product = await prodRes.json();
      const userAgent = request.headers.get('user-agent') || '';
      const isMobile = isMobileDevice(userAgent);
      const effectiveIp = request.headers.get('cf-connecting-ip') || '127.0.0.1';

      // Load newest products for recommendation section
      let relatedProducts = [];
      try {
        const relRes = await fetch(relatedUrl, { 
          headers: { 'x-tenant': tenantId },
          signal: AbortSignal.timeout(5000)
        });
        if (relRes.ok) {
          const relData = await relRes.json();
          // Remove current product and take exact 8 items
          relatedProducts = (relData.data || [])
            .filter((p: { id: string }) => p.id !== product.id)
            .slice(0, 8);
        }
      } catch (relErr) {
        console.error(`[RELATED PRODUCTS FETCH FAILED]`, relErr);
      }

      return {
        type: 'product',
        product,
        relatedProducts,
        isMobile,
        effectiveIp,
        metadata: {
          timestamp: new Date().toISOString(),
          userAgent,
          isMobile
        }
      };
    }
  } catch (e) {
    console.error(`[PRODUCT FETCH SYSTEM ERROR] slug: ${slug}`, e);
  }

  // Phase 2026: Friendly URL Fallback - If not a product, try fetching as News/Article
  const articleUrl = `${apiUrl}/api/v1/client/news/slug/${slug}`;
  try {
    const artRes = await fetch(articleUrl, { 
      headers: { 'x-tenant': tenantId },
      signal: AbortSignal.timeout(5000)
    });
    if (artRes.ok) {
      const article = (await artRes.json()) as Article;
      return {
        type: 'article',
        article,
        metadata: {
          timestamp: new Date().toISOString()
        }
      };
    }
  } catch (artErr) {
    console.error(`[FRIENDLY URL FALLBACK FAILED] slug: ${slug}`, artErr);
  }

  // Final 404
  throw error(404, { message: `Không tìm thấy nội dung cho: ${slug}` });
};
