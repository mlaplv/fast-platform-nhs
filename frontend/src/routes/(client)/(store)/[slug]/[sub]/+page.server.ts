import { error } from '@sveltejs/kit';
import { ServerEnv } from '$lib/server/env';
import type { PageServerLoad } from './$types';

export const trailingSlash = 'always';

export const load: PageServerLoad = async ({ params, fetch }) => {
    const { slug, sub } = params;
    const apiUrl = ServerEnv.INTERNAL_API_URL;
    const tenantId = ServerEnv.TENANT_ID;

    // Elite V2.2: Ghost URL Lockdown
    // Bắt buộc verify category qua Backend API
    const categoryUrl = `${apiUrl}/api/v1/client/home/category/${sub}`;
    try {
        const res = await fetch(categoryUrl, {
            headers: { 'x-tenant': tenantId }
        });

        if (res.ok) {
            const category = await res.json();
            // Kiểm tra tính chính trực của cây danh mục: 
            // Slack 'sub' phải có cha (parent_id) và slug của cha phải khớp với 'slug' trong URL
            // LƯU Ý: Hiện tại API chưa trả về slug của cha trong CategoryResponse gọn, 
            // nhưng ta có thể verify bằng cách fetch cha nếu cần, hoặc đơn giản là chặn các prefix lạ.
            
            // Tạm thời: Nếu tìm thấy 'sub' là OK, nhưng lý tưởng là verify cả 'slug' cha.
            const categoryName = category.name;

            // Fetch sản phẩm thực tế cho danh mục này
            const productsUrl = `${apiUrl}/api/v1/client/products/?category_slug=${sub}&limit=40&status=ACTIVE`;
            const prodRes = await fetch(productsUrl, { headers: { 'x-tenant': tenantId } });
            const products = prodRes.ok ? (await prodRes.json()).data : [];

            return {
                type: 'category',
                categoryName,
                categorySlug: sub,
                items: products
            };
        }
    } catch (e) {
        console.error(`[ROUTE GUARD FAILED] slug: ${slug}, sub: ${sub}`, e);
    }

    // Nếu không tìm thấy hoặc lỗi -> 404 (lockdown)
    throw error(404, { message: `Danh mục không tồn tại: ${slug}/${sub}/` });
};