import { dev } from '$app/environment';
import { env } from '$env/dynamic/private';

const APP_DOMAIN = env.APP_DOMAIN || 'micsmo.com';
const ADMIN_DOMAIN = env.ADMIN_DOMAIN || 'admin.micsmo.com';

/**
 * ServerEnv (Elite V2.2)
 * Centralized, type-safe environment configuration for server-side logic.
 * Consolidated from $env/dynamic/private with sensible infrastructure defaults.
 */
export const ServerEnv = {
    /** environment: development | production */
    isDev: dev,

    /** Domain for Admin Portal detection (e.g. admin.micsmo.com) */
    ADMIN_DOMAIN,

    /** Internal URL for Backend API communication (Container-to-Container) */
    INTERNAL_API_URL: env.INTERNAL_API_URL || 'http://api:8000',

    /** Main App Domain for tenant resolution */
    APP_DOMAIN,

    /** Pre-calculated Tenant ID for performance (Elite V2.2: Full domain SSOT) */
    TENANT_ID: APP_DOMAIN || 'default',

    /** Base domain logic for strict matching */
    isLocal: (hostname: string) => hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.'),
} as const;
