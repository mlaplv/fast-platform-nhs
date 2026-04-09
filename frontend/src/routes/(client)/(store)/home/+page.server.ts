import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { ServerEnv } from '$lib/server/env';

export const trailingSlash = 'always';

export const load: PageServerLoad = async ({ fetch }) => {
  const apiUrl = ServerEnv.INTERNAL_API_URL;
  const tenantId = ServerEnv.TENANT_ID;
  const targetUrl = `${apiUrl}/api/v1/client/home`;

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
    // If backend doesn't have this endpoint yet, it will throw 404 which is correct per R00
    throw error(res.status, {
      message: `API Error: ${res.statusText} (${res.status})`,
      details: `Failed to fetch home data from ${targetUrl}`
    });
  }

  const data = await res.json();
  return data;
};
