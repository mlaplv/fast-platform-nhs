import { error, redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

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

export const load: PageLoad = async ({ params, fetch, url }) => {
  const { slug } = params;
  const hasTrailingSlash = url.pathname.endsWith('/');

  // Rule 2.2: Standardize Structure
  // 1. If it ends with '/', it MUST be a Category
  if (hasTrailingSlash) {
    if (slug === 'bai-viet') {
      throw error(404, { message: "Không tìm thấy nội dung (Dấu '/' không được phép cho tin bài)" });
    }

    const productsUrl = `/api/v1/client/products/?category_slug=${slug}&limit=49&status=ACTIVE`;
    const categoryDetailUrl = `/api/v1/client/categories/slug/${slug}`;

    try {
      const [prodRes, catDetailRes] = await Promise.all([
        fetch(productsUrl, {
          signal: AbortSignal.timeout(3000)
        }),
        fetch(categoryDetailUrl, {
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

        let category = null;
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
    const newsUrl = `/api/v1/client/news`;
    try {
      const newsRes = await fetch(newsUrl, {
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
  const productUrl = `/api/v1/client/products/slug/${slug}`;
  const relatedUrl = `/api/v1/client/products/?limit=9`;

  try {
    const prodRes = await fetch(productUrl, {
      signal: AbortSignal.timeout(3000)
    });
    if (prodRes.ok) {
      const product = await prodRes.json();
      
      if (product?.name) {
        product.name = product.name.replace(/40gr/g, '40g');
      }

      let userAgent = '';
      let isMobile = false;
      if (typeof navigator !== 'undefined') {
        userAgent = navigator.userAgent;
        isMobile = window.innerWidth <= 768 || /Mobi|Android|iPhone/i.test(userAgent);
      }

      // Parallel fetch for related products and reviews stats
      const [relRes, statsRes] = await Promise.all([
        fetch(relatedUrl, {
          signal: AbortSignal.timeout(2000)
        }).catch((relErr) => {
          console.error(`[RELATED PRODUCTS FETCH FAILED]`, relErr);
          return null;
        }),
        fetch(`/api/v1/client/reviews/stats?entity_type=PRODUCT&entity_id=${product.id}`, {
          signal: AbortSignal.timeout(2000)
        }).catch((e) => {
          console.warn(`[REVIEW STATS FETCH FAILED] id: ${product.id}`, e);
          return null;
        })
      ]);

      // Parse related products
      let relatedProducts: { id: string }[] = [];
      if (relRes && relRes.ok) {
        try {
          const relData = await relRes.json();
          relatedProducts = (relData.data || [])
            .filter((p: { id: string }) => p.id !== product.id)
            .slice(0, 8);
        } catch (e) {
          console.error(`[RELATED PRODUCTS PARSE FAILED]`, e);
        }
      }

      // Parse review stats
      let reviewStats = null;
      if (statsRes && statsRes.ok) {
        try {
          reviewStats = await statsRes.json();
        } catch (e) {
          console.warn(`[REVIEW STATS PARSE FAILED] id: ${product.id}`);
        }
      }

      return {
        type: 'product',
        product,
        reviewStats,
        relatedProducts,
        isMobile,
        effectiveIp: '127.0.0.1',
        metadata: {
          timestamp: new Date().toISOString(),
          userAgent,
          isMobile
        }
      };
    }

    if (prodRes.status !== 404) {
      const errorData = await prodRes.text();
      console.error(`[PRODUCT FETCH ERROR] status: ${prodRes.status}, slug: ${slug}, data: ${errorData}`);
      throw error(prodRes.status, { 
        message: `Lỗi hệ thống khi tải sản phẩm: ${slug} (${prodRes.status})` 
      });
    }

  } catch (e: unknown) {
    const err = e as { status?: number };
    if (err.status) throw e;
    console.error(`[PRODUCT FETCH SYSTEM ERROR] slug: ${slug}`, e);
  }

  // Phase 2026: Redirect old article link structure to professional `[slug].html`
  const articleUrl = `/api/v1/client/news/slug/${slug}`;
  try {
    const artRes = await fetch(articleUrl, {
      method: 'HEAD',
      signal: AbortSignal.timeout(1500)
    });
    if (artRes.ok) {
      throw redirect(301, `/${slug}.html`);
    }
  } catch (artErr: unknown) {
    if (artErr && typeof artErr === 'object' && 'status' in artErr && (artErr as { status: number }).status === 301) {
      throw artErr;
    }
    console.error(`[FRIENDLY URL FALLBACK CHECK FAILED] slug: ${slug}`, artErr);
  }

  throw error(404, { message: `Không tìm thấy sản phẩm hoặc trang cho: ${slug}` });
};
