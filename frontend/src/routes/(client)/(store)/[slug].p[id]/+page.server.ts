import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { ServerEnv } from '$lib/server/env';

export const load: PageServerLoad = async ({ params, fetch }) => {
  const apiUrl = ServerEnv.INTERNAL_API_URL;
  const tenantId = ServerEnv.TENANT_ID;
  const { id } = params;

  try {
    const res = await fetch(`${apiUrl}/api/v1/client/news/${id}`, {
      headers: { 'x-tenant': tenantId },
      signal: AbortSignal.timeout(5000)
    });

    if (!res.ok) {
      throw error(res.status, { message: `Không tìm thấy bài viết: ${id}` });
    }

    const article = await res.json();
    return {
      article
    };
  } catch (e) {
    if ((e as any).status) throw e;
    console.error(`[NEWS DETAIL FETCH FAILED] id: ${id}`, e);
    throw error(503, { message: "Dịch vụ tạm thời không khả dụng" });
  }
};