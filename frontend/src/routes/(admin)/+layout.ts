import { redirect } from '@sveltejs/kit';
import type { LayoutLoad } from './$types';
import { permissionState } from '$lib/state/permissions.svelte';

export const load: LayoutLoad = async ({ url }) => {
    if (typeof window === 'undefined') return {};

    // Don't guard the login route
    if (url.pathname === '/login') {
        return {};
    }

    // Sync auth from token cookie or storage
    permissionState.handshake();

    const token = permissionState.getAuthToken();
    if (!token) {
        throw redirect(307, '/login');
    }

    // Phase 2 - Role-Based Access Control (RBAC)
    const authorizedRoles = ['ADMIN', 'SUPER_ADMIN'];
    const isAuthorized = permissionState.roles.some(r => authorizedRoles.includes(r));

    if (!isAuthorized && permissionState.isInitialized) {
        console.error(`[SECURITY] Unauthorized access attempt to Admin Zone by ${permissionState.user}`);
        throw redirect(307, '/login');
    }

    return {};
};
