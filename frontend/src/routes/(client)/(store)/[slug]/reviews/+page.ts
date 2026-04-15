import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, fetch }) => {
  const { slug } = params;

  // Fetch product to get ID and basic info
  const res = await fetch(`/api/v1/client/products/slug/${slug}`);
  if (!res.ok) {
    throw error(404, 'Không tìm thấy sản phẩm');
  }

  const product = await res.json();

  return {
    product
  };
};
