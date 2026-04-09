import type { PageServerLoad } from './$types';

// ELITE V2.2: Tắt tính năng tự động chuyển hướng slash của SvelteKit
export const trailingSlash = 'ignore';

export const load: PageServerLoad = async ({ params, url }) => {
  // XỬ LÝ THEO CHUẨN URL KIẾN TRÚC: CÓ "/" Ở CUỐI LÀ DANH MỤC
  if (url.pathname.endsWith('/')) {

    // Nếu slug là tin tức
    if (params.slug === 'tin-tuc') {
        const mockNews = Array.from({ length: 6 }).map((_, i) => ({
            id: `${i}`,
            slug: `blog-elite-${i}`,
            title: i === 0 ? "Bí quyết trẻ hóa làn da Agentic AI 2026" : `Cẩm nang chăm sóc sắc đẹp Elite Vol.${i + 1}`,
            summary: 'Khám phá công nghệ mỹ phẩm hàng đầu giúp bạn lưu giữ thanh xuân và tự tin tỏa sáng mỗi ngày...',
            image: '/uploads/img/micsmo/20250729_Clo7Mql2nt.jpeg'
        }));

        return {
            type: 'news',
            categoryName: 'GÓC TIN TỨC ELITE',
            items: mockNews
        };
    }

    const categoryName = params.slug.replace(/-/g, ' ').toUpperCase();
    const mockProducts = Array.from({ length: 10 }).map((_, i) => ({
        id: `sp-elite-${params.slug}-${i}`,
        name: i === 0 ? `Serum Nhau Thai White Label Premium` : `${categoryName.charAt(0) + categoryName.slice(1).toLowerCase()} Cao Cấp Phiên Bản ${i + 1}`,
        price: 399000 + (i * 50000),
        image: `/uploads/img/micsmo/-MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-CREAM-60g-Kem-Duong-Nhau-Thai-Lam-Sang-amp-Cap-Am-Diu-Nhe_33.1.png`
    }));

    return {
        type: 'category',
        categoryName,
        items: mockProducts
    };
  }

  // KHÔNG CÓ "/" Ở CUỐI CHẮC CHẮN LÀ CHI TIẾT SẢN PHẨM
  return {
    type: 'product',
    product: {
      id: params.slug,
      name: 'Hurry Harry Wrinkle Serum Rich (Dữ liệu thực từ ' + params.slug + ')',
      price: 350000,
      description: 'Serum chuyên sâu giúp xóa mờ nếp nhăn vùng mắt, miệng, trán với công thức collagen đậm đặc.',
      image: '/uploads/img/micsmo/Hurry-Harry-Medicated-Beauty-Wrinkle-Serum-Rich-jpeg.jpg',
      images: [
        '/uploads/img/micsmo/Hurry-Harry-Medicated-Beauty-Wrinkle-Serum-Rich-jpeg.jpg',
        '/uploads/img/micsmo/-MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-CREAM-60g-Kem-Duong-Nhau-Thai-Lam-Sang-amp-Cap-Am-Diu-Nhe_33.1.png'
      ]
    }
  };
};