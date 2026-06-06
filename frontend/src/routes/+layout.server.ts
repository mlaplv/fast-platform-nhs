import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = ({ locals }) => {
    return {
        user: locals.user ?? null,
        tenant: locals.tenant ?? 'storefront',
        isMobile: locals.isMobile ?? false,
        agentName: 'Helen',
    };
};
