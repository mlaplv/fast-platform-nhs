import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params }) => {
  const { slug } = params;
  
  // Elite V2.2: SEO Friendly URL Consolidation (R00: War Room Protocol)
  // Toàn bộ request có đuôi .p[id] sẽ được redirect 301 về đường dẫn rút gọn.
  throw redirect(301, `/${slug}`);
};