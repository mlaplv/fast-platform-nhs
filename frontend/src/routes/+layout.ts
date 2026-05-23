import type { LayoutLoad } from './$types';

export const ssr = false;
export const prerender = false;

interface RootLayoutData {
    user: string | null;
    tenant: string;
    isMobile: boolean;
    agentName: string;
}

export const load: LayoutLoad = async (): Promise<RootLayoutData> => {
    let isMobile = false;
    if (typeof window !== 'undefined') {
        isMobile = window.innerWidth <= 768 || /Mobi|Android|iPhone/i.test(navigator.userAgent);
    }
    
    let tenant = 'storefront';
    if (typeof window !== 'undefined') {
        if (window.location.hostname.startsWith('admin.') || window.location.search.includes('admin')) {
            tenant = 'admin';
        }
    }

    return {
        user: null, // PermissionState will handle user state reactively
        tenant,
        isMobile,
        agentName: 'Helen',
    };
};
