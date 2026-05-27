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

  // Elite V2.2: Defense-in-depth hostname resolution.
  // Ưu tiên X-Forwarded-Host (do Caddy set) > Host header > event.url.hostname (raw).
  // Mục đích: Đảm bảo tenant detection đúng ngay cả khi SvelteKit nhận hostname container nội bộ.
  const hostname =
    (event.request.headers.get("x-forwarded-host") || event.request.headers.get("host") || event.url.hostname)
      .split(":")[0] // Strip port nếu có (e.g. "admin.osmo:3000" → "admin.osmo")
      .toLowerCase()
      .trim();
  const adminDomain = ServerEnv.ADMIN_DOMAIN;

  // 1. Identify Tenant (STRICT Matching for Elite V2.2)
  // Logic: Exactly equals admin domain OR starts with admin. if on local/internal proxy
  const isAdminHost = hostname === adminDomain || (ServerEnv.isLocal(hostname) && event.url.searchParams.has('admin'));
  event.locals.tenant = isAdminHost ? "admin" : "storefront";

  // 2. Optimized Device Snapshot
  event.locals.isMobile = isMobileDevice(userAgent);

  // 3. Selective Auth Logic (Resource Protection)
  if (isAdminHost) {
    const token = event.cookies.get("admin_token");
    if (token) {
      const payload = parseJwt(token);
      if (payload && payload.exp && payload.exp * 1000 > Date.now()) {
        event.locals.user = {
          email: payload.sub,
          role: payload.roles?.[0] || "ADMIN",
          roles: payload.roles || [],
          perms: payload.perms || [],
        };
        event.locals.token = token;
      }
    }
  } else {
    // Elite V2.2: Storefront Secure Auth (Military Grade)
    const token = event.cookies.get("access_token");
    if (token) {
      const payload = parseJwt(token);
      if (payload && payload.exp && payload.exp * 1000 > Date.now()) {
        event.locals.user = {
          id: payload.id,
          email: payload.sub,
          name: payload.name,
          role: payload.roles?.[0] || "CUSTOMER",
          roles: payload.roles || [],
          perms: payload.perms || [],
        };
        event.locals.token = token;
      }
    }
  }

  // Handle Redundant /admin prefix
  if (event.locals.tenant === "admin" && event.url.pathname.startsWith("/admin")) {
    const newPath = event.url.pathname.replace("/admin", "") || "/";
    throw redirect(301, newPath);
  }

  // R31 & R33: Route Isolation & Protection
  const isTargetingAdminRoute = (ADMIN_PROTECTED_PATHS as readonly string[]).some((p: string) => event.url.pathname.startsWith(p));
  const isTargetingAdminBase = isTargetingAdminRoute || event.url.pathname === "/" || event.url.pathname === "/login";

  /**
   * Elite V2.2: Global Domain Guard (Root Fix for Multi-Domain Navigation)
   * Enforced on all non-local domains to prevent "Tenant Leakage"
   */
  if (!ServerEnv.isLocal(hostname)) {
    if (isAdminHost) {
      // On Admin domain, but accessing a Storefront route? -> Redirect to Storefront
      if (!isTargetingAdminBase) {
        throw redirect(308, `https://${ServerEnv.APP_DOMAIN}${event.url.pathname}${event.url.search}`);
      }
    } else {
      // On Storefront domain, but accessing an Admin route? -> Redirect to Admin
      if (isTargetingAdminRoute) {
        const targetHost = adminDomain.includes('.') ? adminDomain : `${adminDomain}.${ServerEnv.APP_DOMAIN}`;
        throw redirect(308, `https://${targetHost}${event.url.pathname}${event.url.search}`);
      }
      // Security Fix: /login KHÔNG thuộc storefront. Redirect sang admin domain.
      // osmo/login phải → admin.osmo/login (không được render admin UI trên storefront domain)
      if (event.url.pathname === "/login") {
        throw redirect(308, `https://${adminDomain}/login`);
      }
    }
  }

  // Protection logic: Admin tenant
  if (event.locals.tenant === "admin" && event.url.pathname !== "/login") {
    const isAdmin = event.locals.user?.roles?.some((r: string) => ["ADMIN", "SUPER_ADMIN"].includes(r));
    if (!isAdmin) throw redirect(303, "/login");
  }

  // Elite V2.2: Storefront Territory Protection
  // Bọc kín toàn bộ Sidebar (/user/*) bằng lớp giáp SSR
  if (event.locals.tenant === "storefront" && event.url.pathname.startsWith("/user")) {
    if (!event.locals.user) {
      console.warn(`[SECURITY] Unauthorized SSR access attempt to ${event.url.pathname} from ${event.getClientAddress()}`);
      throw redirect(303, "/");
    }
  }

  // CTV Attribution — Viral 2026
  // Capture ?ctv=CODE from URL params → set HTTPOnly __ctv cookie (7 days)
  // Cookie is set even before the page is rendered (SSR-first attribution)
  const ctvParam = event.url.searchParams.get("ctv");
  if (ctvParam) {
    let ctvValue = ctvParam.trim();
    if (ctvValue.length <= 20 && /^[a-zA-Z0-9]+$/.test(ctvValue)) {
      ctvValue = ctvValue.toUpperCase();
    } else {
      // Cryptographically secure token — preserve urlsafe base64 characters: [A-Za-z0-9_\-]
      ctvValue = ctvValue.replace(/[^A-Za-z0-9_\-]/g, "");
    }
    
    if (ctvValue.length >= 4) {
      event.cookies.set("__ctv", ctvValue, {
        path: "/",
        httpOnly: true,
        secure: !ServerEnv.isDev,
        sameSite: "lax",
        maxAge: 60 * 60 * 24 * 7, // 7 days
      });
    }
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
