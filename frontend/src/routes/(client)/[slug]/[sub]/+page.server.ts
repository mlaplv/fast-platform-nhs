import type { PageServerLoad } from './$types';

export const trailingSlash = 'always';

export const load: PageServerLoad = async ({ params }) => {
    const { slug, sub } = params;
    const categoryName = `${slug} / ${sub}`.replace(/-/g, ' ').toUpperCase();

    const mockProducts = Array.from({ length: 10 }).map((_, i) => ({
        id: `sp-elite-${sub}-${i}`,
        name: `Siêu phẩm ${categoryName} ${i + 1}`,
        price: 399000 + (i * 50000),
        image: `/uploads/img/micsmo/-MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-CREAM-60g-Kem-Duong-Nhau-Thai-Lam-Sang-amp-Cap-Am-Diu-Nhe_33.1.png`
    }));

    return {
        type: 'category',
        categoryName,
        items: mockProducts
    };
};