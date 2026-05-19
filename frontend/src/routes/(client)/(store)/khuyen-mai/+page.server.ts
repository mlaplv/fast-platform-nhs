import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { ServerEnv } from '$lib/server/env';

export const load: PageServerLoad = async ({ fetch }) => {
  const apiUrl = ServerEnv.INTERNAL_API_URL;
  const tenantId = ServerEnv.TENANT_ID;
  const targetUrl = `${apiUrl}/api/v1/client/home`;

  try {
    const res = await fetch(targetUrl, {
      headers: { 'x-tenant': tenantId },
      signal: AbortSignal.timeout(5000)
    });

    if (!res.ok) {
      return {
        products: [],
        banners: [],
        categories: [],
        aiProducts: []
      };
    }

    const homeData = await res.json();
    return {
      products: homeData.products || [],
      banners: homeData.banners || [],
      categories: homeData.categories || [],
      aiProducts: homeData.ai_products || []
    };
  } catch (e) {
    console.error('[PROMOTION PRODUCTS FETCH FAILED]', e);
    return {
      products: [],
      banners: [],
      categories: [],
      aiProducts: []
    };
  }
};
