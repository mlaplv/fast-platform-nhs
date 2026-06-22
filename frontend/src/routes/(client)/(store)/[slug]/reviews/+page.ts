import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, fetch }) => {
  const { slug } = params;

  // Only products can have reviews pages
  const productUrl = `/api/v1/client/products/slug/${slug}`;
  const res = await fetch(productUrl, {
    signal: AbortSignal.timeout(5000)
  });
  
  if (!res.ok) {
    throw error(404, 'Không tìm thấy nội dung yêu cầu');
  }

  const entity = await res.json();

  return {
    entity,
    entityType: 'PRODUCT'
  };
};
