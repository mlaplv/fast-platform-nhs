import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, fetch }) => {
  const { slug } = params;

  // 1. Try product first
  const productUrl = `/api/v1/client/products/slug/${slug}`;
  let res = await fetch(productUrl, {
    signal: AbortSignal.timeout(5000)
  });
  
  let entityType = 'PRODUCT';

  if (!res.ok) {
    // 2. Try category second
    const categoryUrl = `/api/v1/client/categories/slug/${slug}`;
    res = await fetch(categoryUrl, {
      signal: AbortSignal.timeout(5000)
    });
    
    if (!res.ok) {
      // 3. Try News/Article as final fallback
      const articleUrl = `/api/v1/client/news/slug/${slug}`;
      res = await fetch(articleUrl, {
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
