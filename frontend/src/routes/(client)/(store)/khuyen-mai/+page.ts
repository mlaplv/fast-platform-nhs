import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
  const targetUrl = `/api/v1/client/home`;

  try {
    const res = await fetch(targetUrl, {
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
