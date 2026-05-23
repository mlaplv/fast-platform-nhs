import type { PageLoad } from './$types';

export const load: PageLoad = async () => {
    let isMobile = false;
    if (typeof window !== 'undefined') {
        isMobile = window.innerWidth <= 768 || /Mobi|Android|iPhone/i.test(navigator.userAgent);
    }
    return {
        isMobile
    };
};
