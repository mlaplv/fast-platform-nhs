import { error, redirect } from '@sveltejs/kit';
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

interface ProductMetadata {
  landing_type?: string;
  mobile_images?: string[];
}

interface TierVariation {
  mobile_images?: string[];
  mobileImages?: string[];
  images?: string[];
}

interface ProductDetails {
  id?: string | number;
  name?: string;
  seoMeta?: NormalizedSeoMeta | null;
  metadata?: ProductMetadata | null;
  tierVariations?: TierVariation[];
  tier_variations?: TierVariation[];
  attributes?: {
    tier_variations?: TierVariation[];
  } & Record<string, unknown>;
  mobileImages?: string[];
  images?: string[];
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

    if (!prodRes.ok || !catRes || !catRes.ok) throw error(404, { message: `Danh mục không tồn tại: ${slug}/` });

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
    const newsRes = await fetch(`/api/v1/client/news?limit=25`, {
      signal: AbortSignal.timeout(3000)
    }).catch(e => { console.error('[NEWS FETCH FAILED]', e); return null; });

    if (!newsRes?.ok) throw error(404, { message: 'Hiện tại chưa có bài viết nào.' });

    const data = await newsRes.json() as Record<string, unknown>;
    const items = (Array.isArray(data) ? data : ((data.data ?? data.items ?? []) as unknown[])) as NewsItem[];
    const total = typeof data.total === 'number' ? data.total : (Array.isArray(data) ? data.length : items.length);

    return {
      type: 'news' as const,
      categoryName: 'Hướng dẫn - kiến thức',
      items,
      serverTotal: total
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
    } as ProductDetails & Record<string, unknown>;

    const metadata = product.metadata || {};
    const landingType = metadata.landing_type || 'standard';
    const isFunnel = landingType !== 'standard';

    // Fetch related products & review stats in parallel
    const promises: Promise<Response | null>[] = [
      fetch(`/api/v1/client/products/?limit=9`, { signal: AbortSignal.timeout(2000) })
        .catch(e => { console.error('[RELATED PRODUCTS FETCH FAILED]', e); return null; }),
      fetch(`/api/v1/client/reviews/stats?entity_type=PRODUCT&entity_id=${String(product.id)}`, {
        signal: AbortSignal.timeout(2000)
      }).catch(e => { console.warn('[REVIEW STATS FETCH FAILED]', e); return null; })
    ];

    if (isFunnel) {
      promises.push(
        fetch(`/api/v1/client/reviews?entity_type=PRODUCT&entity_id=${product.id}&status=APPROVED&limit=20`, {
          signal: AbortSignal.timeout(2000)
        }).catch(() => null),
        fetch(`/api/v1/client/settings/primary`, {
          signal: AbortSignal.timeout(3000)
        }).catch(() => null)
      );
    }

    const [relRes, statsRes, reviewsRes, settingsRes] = await Promise.all(promises);

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

    let reviews: unknown[] = [];
    if (reviewsRes && reviewsRes.ok) {
      const revData = await reviewsRes.json() as Record<string, unknown>;
      reviews = (revData.items || []) as unknown[];
    }

    let shopInfo: unknown = null;
    if (settingsRes && settingsRes.ok) {
      shopInfo = await settingsRes.json();
    }

    let unlockedVoucherIds: string[] = [];
    if (browser) {
      unlockedVoucherIds = document.cookie.split(';')
        .map(c => c.trim())
        .filter(c => c.startsWith('elite_viral_') && c.includes('='))
        .filter(c => {
          const parts = c.split('=');
          return parts[1] === '1';
        })
        .map(c => c.split('=')[0].replace('elite_viral_', ''));
    }

    // Derive LCP hero images for mobile and desktop
    const mobileHeroImage = (() => {
      const p = product;
      const mobVideo = p.metadata?.mobile_video_url || p.metadata?.video_url;
      if (mobVideo) return mobVideo;

      const tierVar = p.tierVariations?.[0] || p.tier_variations?.[0] || p.attributes?.tier_variations?.[0];
      if (tierVar) {
        const mobImgs = (tierVar.mobile_images || tierVar.mobileImages || []).filter(Boolean);
        if (mobImgs.length > 0) return mobImgs[0];
        const deskImgs = (tierVar.images || []).filter(Boolean);
        if (deskImgs.length > 0) return deskImgs[0];
      }
      if (p.mobileImages && p.mobileImages.length > 0) return p.mobileImages[0];
      if (p.metadata?.mobile_images && p.metadata.mobile_images.length > 0) return p.metadata.mobile_images[0];
      return p.images?.[0];
    })();

    const desktopHeroImage = (() => {
      const p = product;
      const deskVideo = p.metadata?.video_url;
      if (deskVideo) return deskVideo;

      const tierVar = p.tierVariations?.[0] || p.tier_variations?.[0] || p.attributes?.tier_variations?.[0];
      if (tierVar) {
        const deskImgs = (tierVar.images || []).filter(Boolean);
        if (deskImgs.length > 0) return deskImgs[0];
      }
      return p.images?.[0];
    })();

    const [resolvedMobileLcpUrl, resolvedDesktopLcpUrl] = await Promise.all([
      mobileHeroImage ? resolveDirectCacheUrl(fetch, mobileHeroImage, 600) : Promise.resolve(''),
      desktopHeroImage ? resolveDirectCacheUrl(fetch, desktopHeroImage, 800) : Promise.resolve('')
    ]);

    // NOTE: isMobile intentionally NOT set here.
    // It is resolved server-side in hooks.server.ts (User-Agent) and passed through layout data.
    // Setting it here via window.innerWidth would cause SSR/Hydration mismatch.
    return {
      type: 'product' as const,
      product,
      reviewStats,
      relatedProducts,
      reviews,
      shopInfo,
      unlockedVoucherIds,
      mobileHeroImage,
      desktopHeroImage,
      resolvedMobileLcpUrl,
      resolvedDesktopLcpUrl
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
