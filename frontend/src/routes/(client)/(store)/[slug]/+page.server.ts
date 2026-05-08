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
    if (slug === 'bai-viet') {
      // News list is explicitly NOT allowed with a trailing slash as per Sếp's simplified rule
      throw error(404, { message: "Không tìm thấy nội dung (Dấu '/' không được phép cho tin bài)" });
    }

    // TĂNG GIỚI HẠN LÊN 49: 1 sp cho banner + 48 sp cho grid (4 cột x 12 hàng)
    const productsUrl = `${apiUrl}/api/v1/client/products/?category_slug=${slug}&limit=49&status=ACTIVE`;
    const categoryDetailUrl = `${apiUrl}/api/v1/client/categories/slug/${slug}`;

    try {
      const [prodRes, catDetailRes] = await Promise.all([
        fetch(productsUrl, {
          headers: { 'x-tenant': tenantId },
          signal: AbortSignal.timeout(3000)
        }),
        fetch(categoryDetailUrl, {
          headers: { 'x-tenant': tenantId },
          signal: AbortSignal.timeout(3000)
        }).catch(e => {
          console.error(`[CATEGORY DETAIL FETCH FAILED] slug: ${slug}`, e);
          return null;
        })
      ]);

      if (prodRes.ok) {
        const prodData = await prodRes.json();
        const items = (prodData.data || []) as unknown[];
        const total = prodData.total || items.length;

        let category: Category | null = null;
        if (catDetailRes && catDetailRes.ok) {
          category = await catDetailRes.json();
        }

        return {
          type: 'category',
          categoryName: category?.name || slug.replace(/-/g, ' ').toUpperCase(),
          categorySlug: slug,
          category,
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
  if (slug === 'bai-viet') {
    const newsUrl = `${apiUrl}/api/v1/client/news`;
    try {
      const newsRes = await fetch(newsUrl, {
        headers: { 'x-tenant': tenantId },
        signal: AbortSignal.timeout(3000)
      });
      if (newsRes.ok) {
        const data = await newsRes.json();
        return {
          type: 'news',
          categoryName: 'Hướng dẫn - kiến thức',
          items: (Array.isArray(data) ? data : (data.data || data.items || [])) as Article[]
        };
      }
    } catch (e) {
      console.error(`[NEWS FETCH FAILED]`, e);
    }
    throw error(404, { message: "Hiện tại chưa có bài viết nào." });
  }

  // 3. Try Product (Standard Slug)
  const productUrl = `${apiUrl}/api/v1/client/products/slug/${slug}`;
  const relatedUrl = `${apiUrl}/api/v1/client/products/?limit=9`; // Fetch 9 to safely exclude current product and keep 8

  try {
    const prodRes = await fetch(productUrl, {
      headers: { 'x-tenant': tenantId },
      signal: AbortSignal.timeout(3000)
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
          signal: AbortSignal.timeout(3000)
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

      // Elite V2.2: Fetch Authentic Review Stats for Server-side SEO
      let reviewStats = null;
      try {
        const statsRes = await fetch(`${apiUrl}/api/v1/client/reviews/stats?entity_type=PRODUCT&entity_id=${product.id}`, {
          headers: { 'x-tenant': tenantId },
          signal: AbortSignal.timeout(3000)
        });
        if (statsRes.ok) reviewStats = await statsRes.json();
      } catch (e) {
        console.warn(`[REVIEW STATS FETCH FAILED] id: ${product.id}`);
      }

      return {
        type: 'product',
        product,
        reviewStats,
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

    // Rule 2.2: Only fallback to Articles if Product is definitively NOT found (404)
    // If it's a 500/403/etc, we should report the actual error or proceed to article ONLY if 404.
    if (prodRes.status !== 404) {
      const errorData = await prodRes.text();
      console.error(`[PRODUCT FETCH ERROR] status: ${prodRes.status}, slug: ${slug}, data: ${errorData}`);
      throw error(prodRes.status, { 
        message: `Lỗi hệ thống khi tải sản phẩm: ${slug} (${prodRes.status})` 
      });
    }

  } catch (e: unknown) {
    const err = e as { status?: number };
    if (err.status) throw e; // Re-throw SvelteKit errors
    console.error(`[PRODUCT FETCH SYSTEM ERROR] slug: ${slug}`, e);
  }

  // Phase 2026: Friendly URL Fallback - If not a product (404), try fetching as News/Article
  const articleUrl = `${apiUrl}/api/v1/client/news/slug/${slug}`;
  try {
    const artRes = await fetch(articleUrl, {
      headers: { 'x-tenant': tenantId },
      signal: AbortSignal.timeout(3000)
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
