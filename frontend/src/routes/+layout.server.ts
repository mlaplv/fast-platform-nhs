import type { LayoutServerLoad } from './$types';

import { env } from '$env/dynamic/private';

/**
 * Elite V2.2: Mandatory interface for LayoutData to ensure 100% static typing.
 * CẤM: Sử dụng 'any' hoặc trả về object không có kiểu.
 */
interface RootLayoutData {
    user: App.Locals['user'];
    tenant: App.Locals['tenant'];
    isMobile: boolean;
    agentName: string;
}

export const load: LayoutServerLoad = async ({ locals }): Promise<RootLayoutData> => {
    return {
        user: locals.user,
        tenant: locals.tenant,
        isMobile: locals.isMobile ?? false,
        agentName: env.SUPPORT_NAME_CLIENT || 'Helen',
    };
};
