import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { ServerEnv } from '$lib/server/env';
import { isMobileDevice } from '$lib/utils/device';

export const trailingSlash = 'ignore';

export const load: PageServerLoad = async ({ params, url, fetch, request }) => {
  if (url.pathname.endsWith('/')) {
    // Keep category logic as-is to obey "Cấm sửa tính năng cũ"
    if (params.slug === 'tin-tuc') {
        const mockNews = Array.from({ length: 6 }).map((_, i) => ({
            id: `${i}`,
            slug: `blog-elite-${i}`,
            title: i === 0 ? "Bí quyết trẻ hóa làn da Agentic AI 2026" : `Cẩm nang chăm sóc sắc đẹp Elite Vol.${i + 1}`,
            summary: '...',
            image: '/uploads/img/micsmo/20250729_Clo7Mql2nt.jpeg'
        }));
        return { type: 'news', categoryName: 'GÓC TIN TỨC ELITE', items: mockNews };
    }
    const categoryName = params.slug.replace(/-/g, ' ').toUpperCase();
    const mockProducts = Array.from({ length: 10 }).map((_, i) => ({
        id: `sp-elite-${params.slug}-${i}`,
        name: i === 0 ? `Serum Nhau Thai White Label Premium` : `${categoryName.charAt(0) + categoryName.slice(1).toLowerCase()} Cao Cấp Phiên Bản ${i + 1}`,
        price: 399000 + (i * 50000),
        image: `/uploads/img/micsmo/-MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-CREAM-60g-Kem-Duong-Nhau-Thai-Lam-Sang-amp-Cap-Am-Diu-Nhe_33.1.png`
    }));
    return { type: 'category', categoryName, items: mockProducts };
  }

  const apiUrl = ServerEnv.INTERNAL_API_URL || 'http://127.0.0.1:8000';
  const tenantId = ServerEnv.TENANT_ID;
  const targetUrl = `${apiUrl}/api/v1/client/products/slug/${params.slug}`;
  
  try {
      const res = await fetch(targetUrl, { headers: { 'x-tenant': tenantId } });
      if (!res.ok) {
          throw new Error(`API Error: ${res.status}`);
      }
      const product = await res.json();
      
      const effectiveIp = request.headers.get('cf-connecting-ip') || '127.0.0.1';
      const userAgent = request.headers.get('user-agent') || '';
      const isMobile = isMobileDevice(userAgent);
      
      // LOG DEBUGS TO SERVER CONSOLE
      console.log(`[SLUG PAGE] Fetched product: ${product.name}`);
      console.log(`[SLUG PAGE] Landing Type: ${product.metadata?.landing_type}`);

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
  } catch (err) {
      console.error(`[SLUG PAGE] Fallback triggered due to API error:`, err);
      // Fallback for development if API is down
      return {
          type: 'product',
          product: {
              id: params.slug,
              name: '[API FALLBACK] Lỗi kết nối Backend: ' + params.slug,
              price: 350000,
              description: 'Sản phẩm này đang được hiển thị ở chế độ Offline (Mock Data) do mất kết nối tới Backend.',
              image: '/uploads/img/micsmo/Hurry-Harry-Medicated-Beauty-Wrinkle-Serum-Rich-jpeg.jpg',
              images: [],
              metadata: { landing_type: 'standard' }
          },
          isMobile: false
      };
  }
};
