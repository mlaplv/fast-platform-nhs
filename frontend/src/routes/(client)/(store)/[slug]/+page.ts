import { error, redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';
import { normalizeSeoMeta, type NormalizedSeoMeta } from '$lib/utils/seo';

export const trailingSlash = 'ignore';

// ── Shared local types ────────────────────────────────────────────────────────
interface NewsItem {
  id: string;
  title: string;
  slug: string;
  excerpt?: string;
  featured_image?: string;
  category?: string;
}

interface ReviewStats {
  average_rating: number;
  total_count: number;
}

// ── Loader ────────────────────────────────────────────────────────────────────
export const load: PageLoad = async ({ params, fetch, url }) => {
  const { slug } = params;

  // ── 1. Category (trailing slash) ─────────────────────────────────────────
  if (url.pathname.endsWith('/')) {
    if (slug === 'bai-viet') {
      throw error(404, { message: "Dấu '/' không được phép cho trang bài viết." });
    }

    const [prodRes, catRes] = await Promise.all([
      fetch(`/api/v1/client/products/?category_slug=${slug}&limit=49&status=ACTIVE`, {
        signal: AbortSignal.timeout(3000)
      }),
      fetch(`/api/v1/client/categories/slug/${slug}`, {
        signal: AbortSignal.timeout(3000)
      }).catch(e => {
        console.error(`[CATEGORY DETAIL FETCH FAILED] ${slug}`, e);
        return null;
      })
    ]);

    if (!prodRes.ok) throw error(404, { message: `Danh mục không tồn tại: ${slug}/` });

    const prodData = await prodRes.json() as Record<string, unknown>;
    const items = (prodData.data ?? []) as unknown[];
    const total = (prodData.total as number) || items.length;

    let category: Record<string, unknown> | null = null;
    if (catRes?.ok) {
      const catData = await catRes.json() as Record<string, unknown>;
      const rawSeo = (catData.seoMeta ?? catData.seo_meta) as Record<string, unknown> | null;
      category = {
        ...catData,
        seoMeta: normalizeSeoMeta(rawSeo, String(catData.name ?? ''))
      };
    }

    return {
      type: 'category' as const,
      categoryName: (category?.name as string) || slug.replace(/-/g, ' ').toUpperCase(),
      categorySlug: slug,
      category,
      serverTotal: total,
      items
    };
  }

  // ── 2. News list ─────────────────────────────────────────────────────────
  if (slug === 'bai-viet') {
    const newsRes = await fetch(`/api/v1/client/news`, {
      signal: AbortSignal.timeout(3000)
    }).catch(e => { console.error('[NEWS FETCH FAILED]', e); return null; });

    if (!newsRes?.ok) throw error(404, { message: 'Hiện tại chưa có bài viết nào.' });

    const data = await newsRes.json() as Record<string, unknown>;
    return {
      type: 'news' as const,
      categoryName: 'Hướng dẫn - kiến thức',
      items: (Array.isArray(data) ? data : ((data.data ?? data.items ?? []) as unknown[])) as NewsItem[]
    };
  }

  // ── 3. Product ────────────────────────────────────────────────────────────
  const prodRes = await fetch(`/api/v1/client/products/slug/${slug}`, {
    signal: AbortSignal.timeout(3000)
  }).catch(e => { console.error(`[PRODUCT FETCH FAILED] ${slug}`, e); return null; });

  if (prodRes?.ok) {
    const prodData = await prodRes.json() as Record<string, unknown>;
    const rawSeo = (prodData.seoMeta ?? prodData.seo_meta) as Record<string, unknown> | null;
    const seoMeta: NormalizedSeoMeta | null = normalizeSeoMeta(rawSeo, String(prodData.name ?? ''));

    const product = {
      ...prodData,
      seoMeta,
      // Normalize legacy weight notation
      name: typeof prodData.name === 'string' ? prodData.name.replace(/40gr/g, '40g') : prodData.name
    };

    // Fetch related products & review stats in parallel (does NOT block product render)
    const [relRes, statsRes] = await Promise.all([
      fetch(`/api/v1/client/products/?limit=9`, { signal: AbortSignal.timeout(2000) })
        .catch(e => { console.error('[RELATED PRODUCTS FETCH FAILED]', e); return null; }),
      fetch(`/api/v1/client/reviews/stats?entity_type=PRODUCT&entity_id=${String(product.id)}`, {
        signal: AbortSignal.timeout(2000)
      }).catch(e => { console.warn('[REVIEW STATS FETCH FAILED]', e); return null; })
    ]);

    let relatedProducts: { id: string }[] = [];
    if (relRes?.ok) {
      const relData = await relRes.json() as Record<string, unknown>;
      relatedProducts = ((relData.data ?? []) as { id: string }[])
        .filter(p => p.id !== String(product.id))
        .slice(0, 8);
    }

    let reviewStats: ReviewStats | null = null;
    if (statsRes?.ok) {
      reviewStats = await statsRes.json() as ReviewStats;
    }

    // NOTE: isMobile intentionally NOT set here.
    // It is resolved server-side in hooks.server.ts (User-Agent) and passed through layout data.
    // Setting it here via window.innerWidth would cause SSR/Hydration mismatch.
    return {
      type: 'product' as const,
      product,
      reviewStats,
      relatedProducts
    };
  }

  if (prodRes && prodRes.status !== 404) {
    throw error(prodRes.status, { message: `Lỗi hệ thống: ${slug} (${prodRes.status})` });
  }

  // ── 4. Article redirect (old URL → [slug].html) ───────────────────────────
  const artRes = await fetch(`/api/v1/client/news/slug/${slug}`, {
    method: 'HEAD',
    signal: AbortSignal.timeout(1500)
  }).catch(() => null);

  if (artRes?.ok) throw redirect(301, `/${slug}.html`);

  throw error(404, { message: `Không tìm thấy: ${slug}` });
};
