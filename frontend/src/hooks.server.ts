import type { Handle } from "@sveltejs/kit";
import { redirect } from "@sveltejs/kit";
import { env } from "$env/dynamic/private";

function parseJwt(token: string) {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join(""),
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

export const handle: Handle = async ({ event, resolve }) => {
  const host = event.request.headers.get("host") || "";
  const userAgent = event.request.headers.get("user-agent") || "";
  const token = event.cookies.get("admin_token");

  // Determine the tenant based on the requested subdomain (Rules map)
  // R32: Admin domain separately. Minimal, hardened detection via ENV.
  const adminDomain = env.ADMIN_DOMAIN || "admin.smartshop.test";
  const isAdminHost = host.includes(adminDomain);

  if (isAdminHost) {
    event.locals.tenant = "admin";
  } else {
    event.locals.tenant = "storefront";
  }

  // Auth logic: Validate JWT
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

  // Handle Redundant /admin prefix (Phase Clean URLs)
  if (
    event.locals.tenant === "admin" &&
    event.url.pathname.startsWith("/admin")
  ) {
    const newPath = event.url.pathname.replace("/admin", "") || "/";
    throw redirect(301, newPath);
  }

  // R31 & R33: Route Isolation & Protection
  const adminOnlyPaths = ["/chat", "/settings", "/analytics"];
  const isTargetingAdminRoute = adminOnlyPaths.some((p) =>
    event.url.pathname.startsWith(p),
  );

  // If trying to access admin route from storefront domain -> 404 or Redirect to Admin
  if (isTargetingAdminRoute && event.locals.tenant !== "admin") {
    const adminDomain = env.ADMIN_DOMAIN || "admin.smartshop.test";
    throw redirect(303, `https://${adminDomain}` + event.url.pathname);
  }

  // Protection logic: Admin tenant requires authenticated ADMIN or SUPER_ADMIN (EXCEPT /login)
  if (event.locals.tenant === "admin" && event.url.pathname !== "/login") {
    const isAdmin =
      event.locals.user?.roles?.some((r) =>
        ["ADMIN", "SUPER_ADMIN"].includes(r),
      ) || event.locals.user?.role === "ADMIN";

    if (!isAdmin) {
      throw redirect(303, "/login");
    }
  }

  // Detect device for initial layout resolution
  // Minimal detection for <1s load target
  event.locals.isMobile = /mobile|android|iphone|ipad|phone/i.test(userAgent);

  // Process the request
  const response = await resolve(event);

  // R12 - Security defaults
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("X-Frame-Options", "DENY");

  return response;
};
