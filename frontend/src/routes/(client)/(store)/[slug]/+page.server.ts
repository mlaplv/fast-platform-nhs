import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { ServerEnv } from '$lib/server/env';
import { isMobileDevice } from '$lib/utils/device';

export const trailingSlash = 'ignore';

export const load: PageServerLoad = async ({ params, fetch, request, url }) => {
  const apiUrl = ServerEnv.INTERNAL_API_URL;
  const tenantId = ServerEnv.TENANT_ID;
  const { slug } = params;
  const hasTrailingSlash = url.pathname.endsWith('/');

  // Rule 2.2: Standardize Structure
  // 1. If it ends with '/', it MUST be a Category
  if (hasTrailingSlash) {
    if (slug === 'tin-tuc') {
       // News list is explicitly NOT allowed with a trailing slash as per Sếp's simplified rule
       throw error(404, { message: "Không tìm thấy nội dung (Dấu '/' không được phép cho tin bài)" });
    }

    const categoryUrl = `${apiUrl}/api/v1/client/categories/slug/${slug}`;
    try {
      const catRes = await fetch(categoryUrl, { headers: { 'x-tenant': tenantId } });
      if (catRes.ok) {
        const data = await catRes.json();
        return {
          type: 'category',
          categoryName: slug.replace(/-/g, ' ').toUpperCase(),
          items: Array.isArray(data) ? data : (data.items || [])
        };
      }
    } catch (e) {
      console.error(`[CATEGORY FETCH FAILED] slug: ${slug}`, e);
    }
    
    throw error(404, { message: `Danh mục không tồn tại: ${slug}/` });
  }

  // 2. If it does NOT end with '/', it's either News List or Product
  if (slug === 'tin-tuc') {
    const newsUrl = `${apiUrl}/api/v1/client/news`;
    try {
      const newsRes = await fetch(newsUrl, { headers: { 'x-tenant': tenantId } });
      if (newsRes.ok) {
        const data = await newsRes.json();
        return {
          type: 'news',
          categoryName: 'GÓC TIN TỨC ELITE',
          items: Array.isArray(data) ? data : (data.data || data.items || [])
        };
      }
    } catch (e) {
      console.error(`[NEWS FETCH FAILED]`, e);
    }
    throw error(404, { message: "Hiện tại chưa có tin tức nào." });
  }

  // 3. Try Product (Standard Slug)
  const productUrl = `${apiUrl}/api/v1/client/products/slug/${slug}`;
  try {
    const prodRes = await fetch(productUrl, { headers: { 'x-tenant': tenantId } });
    if (prodRes.ok) {
      const product = await prodRes.json();
      const userAgent = request.headers.get('user-agent') || '';
      const isMobile = isMobileDevice(userAgent);
      const effectiveIp = request.headers.get('cf-connecting-ip') || '127.0.0.1';

      return {
        type: 'product',
        product,
        isMobile,
        effectiveIp,
        metadata: {
          timestamp: new Date().toISOString(),
          userAgent,
          isMobile
        }
      };
    }
  } catch (e) {
    console.error(`[PRODUCT FETCH FAILED] slug: ${slug}`, e);
    throw error(503, { message: "Dịch vụ tạm thời không khả dụng (Backend Connection Failed)" });
  }

  // Final 404
  throw error(404, { message: `Không tìm thấy nội dung cho: ${slug}` });
};
