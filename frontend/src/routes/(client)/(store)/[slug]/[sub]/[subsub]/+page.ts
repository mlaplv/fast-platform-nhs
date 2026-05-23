import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const trailingSlash = 'always';

export const load: PageLoad = async ({ params, fetch }) => {
    const { slug, sub, subsub } = params;

    const categoryUrl = `/api/v1/client/home/category/${subsub}`;
    try {
        const res = await fetch(categoryUrl);

        if (res.ok) {
            const category = await res.json();
            const categoryName = category.name;

            const productsUrl = `/api/v1/client/products/?category_slug=${subsub}&limit=40&status=ACTIVE`;
            const prodRes = await fetch(productsUrl);
            const products = prodRes.ok ? (await prodRes.json()).data : [];

            return {
                type: 'category',
                categoryName,
                categorySlug: subsub,
                items: products
            };
        }
    } catch (e) {
        console.error(`[ROUTE GUARD FAILED] subsub: ${subsub}`, e);
    }

    throw error(404, { message: `Danh mục không tồn tại: ${slug}/${sub}/${subsub}/` });
};
