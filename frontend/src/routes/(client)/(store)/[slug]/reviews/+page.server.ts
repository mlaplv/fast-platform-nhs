import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { ServerEnv } from '$lib/server/env';

export const load: PageServerLoad = async ({ params, fetch }) => {
  const { slug } = params;
  const apiUrl = ServerEnv.INTERNAL_API_URL;
  const tenantId = ServerEnv.TENANT_ID;

  // Elite V2.2: Polymorphic Resolver (Server-side to hide 404 logs from browser console)
  // We check Product -> Category -> News sequentially
  
  // 1. Try product first
  const productUrl = `${apiUrl}/api/v1/client/products/slug/${slug}`;
  let res = await fetch(productUrl, {
    headers: { 'x-tenant': tenantId },
    signal: AbortSignal.timeout(5000)
  });
  
  let entityType = 'PRODUCT';

  if (!res.ok) {
    // 2. Try category second
    const categoryUrl = `${apiUrl}/api/v1/client/categories/slug/${slug}`;
    res = await fetch(categoryUrl, {
      headers: { 'x-tenant': tenantId },
      signal: AbortSignal.timeout(5000)
    });
    
    if (!res.ok) {
      // 3. Try News/Article as final fallback
      const articleUrl = `${apiUrl}/api/v1/client/news/slug/${slug}`;
      res = await fetch(articleUrl, {
        headers: { 'x-tenant': tenantId },
        signal: AbortSignal.timeout(5000)
      });
      
      if (!res.ok) {
        throw error(404, 'Không tìm thấy nội dung yêu cầu');
      }
      entityType = 'NEWS';
    } else {
      entityType = 'CATEGORY';
    }
  }

  const entity = await res.json();

  return {
    entity,
    entityType
  };
};
