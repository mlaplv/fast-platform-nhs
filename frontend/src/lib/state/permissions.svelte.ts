import type { JwtPayload } from "$lib/types";

function decodeJwtPayload<T>(token: string): T {
  const base64Url = token.split(".")[1];
  const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
  const jsonPayload = decodeURIComponent(
    atob(base64)
      .split("")
      .map(function (c) {
        return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
      })
      .join(""),
  );
  return JSON.parse(jsonPayload);
}

class PermissionState {
  perms = $state<string[]>([]);
  roles = $state<string[]>([]);
  user = $state<string | null>(null);
  userName = $state<string | null>(null);
  isInitialized = $state(false);
  private watchdogTimer: ReturnType<typeof setInterval> | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      this.handshake();
    }
  }

  public handshake() {
    if (typeof window === "undefined") return;
    
    // 1. Prioritized Capture from URL
    const urlParams = new URLSearchParams(window.location.search);
    const urlToken = urlParams.get("token");
    
    if (urlToken) {
      console.log("🛡️ [RBAC] Capturing administrative token from URL...");
      localStorage.setItem("admin_token", urlToken);
      
      // Elite V2.2: Aggressive Purge of legacy sessions
      localStorage.removeItem("access_token");
      localStorage.removeItem("user_token");
      
      const rootDomain = window.location.hostname.split('.').slice(-2).join('.');
      document.cookie = `admin_token=${urlToken}; path=/; domain=.${rootDomain}; max-age=604800; SameSite=Lax; Secure`;

      // Clean URL WITHOUT triggering a state purge immediately
      const newUrl = window.location.origin + window.location.pathname + window.location.search.replace(/[?&]token=[^&]+/, '').replace(/^&/, '?');
      window.history.replaceState({}, '', newUrl);
    }

    // 2. Immediate Sync from collected sources
    this.syncFromToken();
  }

  private syncFromToken() {
    if (typeof window === "undefined") return;

    // Elite V2.2: Root Cause Fix - Priority Selection
    const token =
      localStorage.getItem("admin_token") ||
      this.getCookie("admin_token") ||
      localStorage.getItem("access_token") ||
      sessionStorage.getItem("admin_token");

    if (token) {
      try {
        const decoded = decodeJwtPayload<JwtPayload>(token);

        // THIẾT QUÂN LUẬT: Kiểm tra hạn sử dụng JWT
        if (decoded.exp && decoded.exp * 1000 < Date.now()) {
          console.warn("[SECURITY] Token expired. Bắt buộc đăng xuất.");
          this.purgeAuth();
          return;
        }

        // Update state properties directly for Svelte 5 tracking
        this.perms = decoded.perms || [];
        this.roles = decoded.roles || [];
        this.user = decoded.sub;
        
        // Elite V2.2: Tiered Identity Resolution
        const storedName = localStorage.getItem("admin_user_name");
        this.userName =
          decoded.name || storedName || decoded.sub?.split("@")[0] || "IDENTITY_V2.2";
          
        this.isInitialized = true;

        if (decoded.exp) {
          this.startWatchdog(decoded.exp * 1000);
        }
      } catch (e) {
        console.error("[RBAC] Token synchronization failure:", e);
        const isLoginPage = window.location.pathname.includes("/login");
        // Elite V2.2: Only purge and redirect on Admin domain
        const host = window.location.hostname;
        const isAdminDomain = host.startsWith("admin.") || host.includes("admin");
        this.purgeAuth(isAdminDomain && !isLoginPage);
      }
    } else {
      const isLoginPage = window.location.pathname.includes("/login");
      // Elite V2.2: Zero-Barrier Storefront fix
      const host = window.location.hostname;
      const isAdminDomain = host.startsWith("admin.") || host.includes("admin");
      this.purgeAuth(isAdminDomain && !isLoginPage);
    }
  }

  private startWatchdog(expTimeMs: number) {
    if (this.watchdogTimer) clearInterval(this.watchdogTimer);
    this.watchdogTimer = setInterval(() => {
      if (Date.now() >= expTimeMs) {
        console.warn("[SECURITY] Watchdog: Token expired. Bắt buộc đăng xuất.");
        this.purgeAuth();
      }
    }, 10000); // Check every 10 seconds
  }

  purgeAuth(redirect = true) {
    if (typeof window === "undefined") return;
    if (this.watchdogTimer) clearInterval(this.watchdogTimer);
    
    // THIẾT QUÂN LUẬT: Xóa sạch dấu vết
    localStorage.removeItem("admin_token");
    localStorage.removeItem("user_token");
    localStorage.removeItem("access_token");
    sessionStorage.clear();
    document.cookie = "admin_token=; path=/; max-age=0; SameSite=Strict";
    document.cookie = "user_token=; path=/; max-age=0; SameSite=Strict";
    
    this.perms = [];
    this.roles = [];
    this.user = null;
    this.userName = null;
    this.isInitialized = false;

    if (redirect && !window.location.pathname.includes("/login")) {
      window.location.href = "/login";
    }
  }

  hasPermission(perm: string) {
    if (this.roles.includes("SUPER_ADMIN")) return true;
    return this.perms.includes(perm);
  }

  hasRole(role: string) {
    return this.roles.includes(role);
  }

  private getCookie(name: string) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop()?.split(";").shift();
    return null;
  }

  getAuthToken(): string | null {
    if (typeof window === "undefined") return null;
    // Elite V2.2: Root Cause Fix - Priority Selection
    const token =
      localStorage.getItem("admin_token") ||
      this.getCookie("admin_token") ||
      localStorage.getItem("access_token") ||
      sessionStorage.getItem("admin_token");
      
    return token || null;
  }
}

export const permissionState = new PermissionState();
export const getAuthToken = () => permissionState.getAuthToken();
