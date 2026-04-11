import type { Handle, HandleServerError } from "@sveltejs/kit";
import type { JwtPayload } from "$lib/types";
import { redirect } from "@sveltejs/kit";
import { ServerEnv } from "$lib/server/env";
import { isMobileDevice } from "$lib/utils/device";
import { ADMIN_PROTECTED_PATHS } from "$lib/constants/routes";

export const handleError: HandleServerError = ({ error }) => {
  const isDev = ServerEnv.isDev;
  const err = error instanceof Error ? error : new Error(String(error));
  console.error('[SERVER HTTP ERROR]', err);

  return {
    message: isDev ? err.message : "Lỗi hệ thống (Internal Error)",
    stack: isDev ? err.stack : undefined
  };
};

function parseJwt(token: string): JwtPayload | null {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c: string) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join(""),
    );
    return JSON.parse(jsonPayload) as JwtPayload;
  } catch (err: unknown) {
    console.error("JWT Parse Error:", err);
    return null;
  }
}

export const handle: Handle = async ({ event, resolve }) => {
  const userAgent = event.request.headers.get("user-agent") || "";
  const host = event.request.headers.get("host") || "";
  const adminDomain = ServerEnv.ADMIN_DOMAIN;
  const isAdminHost = host.includes(adminDomain);

  // 1. Identify Tenant (Atomic Early-Exit for Elite V2.2)
  event.locals.tenant = isAdminHost ? "admin" : "storefront";

  // 2. Optimized Device Snapshot (R00: Zero-Patch Policy)
  // Only detect at start or use cached value if possible (TBD Phase 2)
  event.locals.isMobile = isMobileDevice(userAgent);

  // 3. Selective Auth Logic (Resource Protection)
  // Storefront visitors NEVER need admin_token parsing (CPU/RAM Save)
  if (isAdminHost) {
    const token = event.cookies.get("admin_token");
    if (token) {
      const payload = parseJwt(token);
      if (payload && payload.exp * 1000 > Date.now()) {
        event.locals.user = {
          email: payload.sub,
          role: payload.role || (payload.roles ? payload.roles[0] : null),
          roles: payload.roles || [],
          perms: payload.perms || [],
        };
        event.locals.token = token;
      }
    }
  }

  // Handle Redundant /admin prefix (Phase Clean URLs)
  if (event.locals.tenant === "admin" && event.url.pathname.startsWith("/admin")) {
    const newPath = event.url.pathname.replace("/admin", "") || "/";
    throw redirect(301, newPath);
  }

  // R31 & R33: Route Isolation & Protection (Single Source of Truth)
  const isTargetingAdminRoute = (ADMIN_PROTECTED_PATHS as readonly string[]).some((p: string) => event.url.pathname.startsWith(p));
  const isTargetingAdminBase = isTargetingAdminRoute || event.url.pathname === "/" || event.url.pathname === "/login";

  // Elite V2.2: Global Domain Guard (Root Fix for Multi-Domain Navigation)
  if (!ServerEnv.isDev) {
    if (isAdminHost) {
      // On Admin domain, but accessing a Storefront route? -> Redirect to Storefront
      if (!isTargetingAdminBase) {
        throw redirect(308, `https://${ServerEnv.APP_DOMAIN}${event.url.pathname}${event.url.search}`);
      }
    } else {
      // On Storefront domain, but accessing an Admin route? -> Redirect to Admin
      if (isTargetingAdminRoute) {
        throw redirect(308, `https://${adminDomain}${event.url.pathname}${event.url.search}`);
      }
    }
  }

  // Protection logic: Admin tenant ONLY (Storefront is ALWAYS PUBLIC)
  if (event.locals.tenant === "admin" && event.url.pathname !== "/login") {
    const isAdmin = event.locals.user?.roles?.some((r: string) => ["ADMIN", "SUPER_ADMIN"].includes(r)) || 
                    event.locals.user?.role === "ADMIN";
    if (!isAdmin) throw redirect(303, "/login");
  }

  // Process the request
  const response = await resolve(event);

  // R12 - Security & Protocol Defaults
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("X-Frame-Options", "DENY");
  
  // Elite V2.2: Vary cache by User-Agent for Adaptive Layouts
  response.headers.set("Vary", "Origin, User-Agent");

  return response;
};
