import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';
import { resolveOptimizedImageUrl, extractIdFromUrl } from '$lib/state/utils';
import { browser } from '$app/environment';

export const trailingSlash = 'always';

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

export const load: PageLoad = async ({ fetch, parent }) => {
  const parentData = await parent();
  const tenant = parentData.tenant || 'storefront';

  // Elite V2.2: Bypass storefront fetch for admin tenant
  if (tenant === 'admin') {
      return {
          home: null,
          timestamp: new Date().toISOString(),
          tenant: 'admin',
          resolvedMobileLcpUrl: '',
          resolvedDesktopLcpUrl: ''
      };
  }

  const targetUrl = '/api/v1/client/home';

  let res;
  try {
      res = await fetch(targetUrl, {
          signal: AbortSignal.timeout(5000) // Prevent hangs
      });
  } catch (err: unknown) {
      console.error(`[ROOT FETCH FAILED] CONNECTION ERROR`, err);

      // Fire-and-forget report to SOC
      const errorMsg = err instanceof Error ? err.message : String(err);
      const reportPayload = {
          error: "CONNECTION_ERROR",
          url: targetUrl,
          timestamp: new Date().toISOString(),
          details: `Error in storefront root load: ${errorMsg}`
      };

      if (browser) {
          if (navigator.sendBeacon) {
              navigator.sendBeacon('/api/v1/client/home/report-error', JSON.stringify(reportPayload));
          } else {
              fetch('/api/v1/client/home/report-error', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(reportPayload)
              }).catch(() => {});
          }
      } else {
          fetch('/api/v1/client/home/report-error', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(reportPayload)
          }).catch(() => {});
      }

      throw error(503, {
          message: "Dịch vụ tạm thời không khả dụng (Backend Connection Failed)",
          details: "Vui lòng chờ giây lát và thử lại."
      });
  }

  if (!res.ok) {
    throw error(res.status, {
      message: `API Error: ${res.statusText} (${res.status})`,
      details: `Failed to fetch home data`
    });
  }

  const data = await res.json();
  const banners = (data.banners || []) as any[];
  const mainBanners = banners.filter(b => b.position === 'home_main');

  let resolvedMobileLcpUrl = '';
  let resolvedDesktopLcpUrl = '';

  if (mainBanners.length > 0) {
    const firstBanner = mainBanners[0];
    const mobileImg = firstBanner.mobile_image_url || firstBanner.image_url;
    const desktopImg = firstBanner.image_url;

    const [mobUrl, deskUrl] = await Promise.all([
      mobileImg ? resolveDirectCacheUrl(fetch, mobileImg, 800) : Promise.resolve(''),
      desktopImg ? resolveDirectCacheUrl(fetch, desktopImg, 800) : Promise.resolve('')
    ]);
    resolvedMobileLcpUrl = mobUrl;
    resolvedDesktopLcpUrl = deskUrl;
  }

  return {
      ...data,
      tenant,
      resolvedMobileLcpUrl,
      resolvedDesktopLcpUrl
  };
};
