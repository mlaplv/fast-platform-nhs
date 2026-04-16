import { error } from '@sveltejs/kit';
import { ServerEnv } from '$lib/server/env';
import type { PageServerLoad } from './$types';

export const trailingSlash = 'always';

export const load: PageServerLoad = async ({ params, fetch }) => {
    const { slug, sub, subsub } = params;
    const apiUrl = ServerEnv.INTERNAL_API_URL;
    const tenantId = ServerEnv.TENANT_ID;

    // Elite V2.2: Ghost URL Lockdown
    const categoryUrl = `${apiUrl}/api/v1/client/home/category/${subsub}`;
    try {
        const res = await fetch(categoryUrl, {
            headers: { 'x-tenant': tenantId }
        });

        if (res.ok) {
            const category = await res.json();
            const categoryName = category.name;

            // Fetch sản phẩm thực tế
            const productsUrl = `${apiUrl}/api/v1/client/products/?category_slug=${subsub}&limit=40&status=ACTIVE`;
            const prodRes = await fetch(productsUrl, { headers: { 'x-tenant': tenantId } });
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