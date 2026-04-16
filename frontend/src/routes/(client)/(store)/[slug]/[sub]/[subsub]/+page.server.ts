import type { PageServerLoad } from './$types';

export const trailingSlash = 'always';

export const load: PageServerLoad = async ({ params }) => {
    const { slug, sub, subsub } = params;
    const categoryName = `${slug} / ${sub} / ${subsub}`.replace(/-/g, ' ').toUpperCase();

    return {
        type: 'category',
        categoryName,
        items: []
    };
};