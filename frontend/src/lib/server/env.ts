import { dev } from '$app/environment';
import { env } from '$env/dynamic/private';

const APP_DOMAIN = env.APP_DOMAIN || 'osmo';
const ADMIN_DOMAIN = env.ADMIN_DOMAIN || 'admin.osmo';

/**
 * ServerEnv (Elite V2.2)
 * Centralized, type-safe environment configuration for server-side logic.
 * Consolidated from $env/dynamic/private with sensible infrastructure defaults.
 */
export const ServerEnv = {
    /** environment: development | production */
    isDev: dev,

    /** Domain for Admin Portal detection (e.g. admin.osmo) */
    ADMIN_DOMAIN,

    /** Internal URL for Backend API communication (Container-to-Container) */
    INTERNAL_API_URL: env.INTERNAL_API_URL || 'http://api:8000',

    /** Main App Domain for tenant resolution */
    APP_DOMAIN,

    /** Pre-calculated Tenant ID for performance (Elite V2.2: Full domain SSOT) */
    TENANT_ID: APP_DOMAIN || 'default',

    /** Base domain logic for strict matching + Docker container name whitelist */
    isLocal: (hostname: string) =>
        hostname === 'localhost' ||
        hostname === '127.0.0.1' ||
        hostname.startsWith('192.168.') ||
        // Docker-internal container names: nếu SvelteKit nhận hostname = container name thì coi là local
        ['ui', 'api', 'caddy', 'db', 'redis'].includes(hostname),
} as const;
