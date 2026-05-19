import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { ServerEnv } from '$lib/server/env';

export const load: PageServerLoad = async ({ fetch, url }) => {
  const apiUrl = ServerEnv.INTERNAL_API_URL;
  const tenantId = ServerEnv.TENANT_ID;
  const query = url.searchParams.get('q') ?? '';
  const brand = url.searchParams.get('brand') ?? '';
  const origin = url.searchParams.get('origin') ?? '';

  const params = new URLSearchParams();
  if (query) params.set('search', query);
  if (brand) params.set('brand', brand);
  if (origin) params.set('origin', origin);

  const targetUrl = `${apiUrl}/api/v1/client/products?${params.toString()}`;

  let res;
  try {
    res = await fetch(targetUrl, {
      headers: { 'x-tenant': tenantId }
    });
  } catch (e: unknown) {
    const err = e as Error;
    console.error(`[FETCH FAILED], không thể kết nối tới Backend!`);
    console.error(`URL: ${targetUrl}`);
    console.error(`Error: ${err.message}`);
    throw error(503, {
      message: "Dịch vụ tạm thời không khả dụng (Backend Connection Failed)",
      details: `Failed to reach API at ${apiUrl}.`
    });
  }

  if (!res.ok) {
    throw error(res.status, {
      message: `API Error: ${res.statusText} (${res.status})`,
      details: `Failed to fetch products from ${targetUrl}`
    });
  }

  const data = await res.json();
  return { 
    products: data.data ?? (Array.isArray(data) ? data : (data.items || data.products || [])),
    total: data.total ?? 0,
    searchQuery: query,
    brand: brand,
    origin: origin,
    facets: data.facets ?? null,
  };
};