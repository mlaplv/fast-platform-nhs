import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const trailingSlash = 'always';

export const load: PageLoad = async ({ fetch }) => {
  let tenant = 'storefront';
  if (typeof window !== 'undefined') {
      if (window.location.hostname.startsWith('admin.') || window.location.search.includes('admin')) {
          tenant = 'admin';
      }
  }

  // Elite V2.2: Bypass storefront fetch for admin tenant
  if (tenant === 'admin') {
      return {
          home: null,
          timestamp: new Date().toISOString(),
          tenant: 'admin'
      };
  }

  const targetUrl = '/api/v1/client/home';

  let res;
  try {
      res = await fetch(targetUrl, {
          signal: AbortSignal.timeout(5000) // Prevent hangs
      });
  } catch (err: unknown) {
      console.error(`[ROOT FETCH FAILED] CONNECTION ERROR`);
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
  return {
      ...data,
      tenant: 'storefront'
  };
};
