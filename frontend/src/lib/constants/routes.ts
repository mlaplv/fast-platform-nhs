/**
 * System-wide Route Configuration (Elite V2.2)
 * All protected and special logic routes must be defined here.
 * NO HARDCODING in hooks or components allowed.
 */

/**
 * Admin Paths that require explicit Admin Role and Tenant context.
 * These are relative to the admin domain root.
 */
export const ADMIN_PROTECTED_PATHS = [
    "/chat",
    "/settings",
    "/analytics",
    "/users",
    "/orders",
    "/products",
    "/inventory"
] as const;

/**
 * Public routes that bypass certain security checks if needed (CRO optimization).
 */
export const PUBLIC_CLIENT_ROUTES = [
    "/",
    "/search",
    "/categories",
    "/product"
] as const;
