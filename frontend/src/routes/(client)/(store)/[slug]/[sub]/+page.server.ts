import type { PageServerLoad } from './$types';

export const trailingSlash = 'always';

export const load: PageServerLoad = async ({ params }) => {
    const { slug, sub } = params;
    const categoryName = `${slug} / ${sub}`.replace(/-/g, ' ').toUpperCase();

    return {
        type: 'category',
        categoryName,
        items: []
    };
};