import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ locals, url }) => {
    // Không chặn nếu đang ở trang login
    if (url.pathname === '/login') {
        return { user: locals.user };
    }

    // Military-Grade Guard: Phase 1 - Session Presence
    if (!locals.user) {
        // Redirection with 303 (See Other) to ensure no POST data leakage
        throw redirect(303, '/login');
    }

    // Phase 2 - Role-Based Access Control (RBAC)
    // Only ADMIN and SUPER_ADMIN are authorized for the (admin) route group perimeter
    const authorizedRoles = ['ADMIN', 'SUPER_ADMIN'];
    const userRole = locals.user.role || '';
    const userRoles = locals.user.roles || [];
    
    const isAuthorized = authorizedRoles.includes(userRole) || 
                         userRoles.some(r => authorizedRoles.includes(r));

    if (!isAuthorized) {
        console.error(`[SECURITY] Unauthorized access attempt to Admin Zone by ${locals.user.email} (Role: ${userRole})`);
        throw redirect(303, '/login');
    }

    return {
        user: locals.user
    };
};
