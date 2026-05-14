/**
 * Global API Client (The Definitive Fix)
 * Bọc lại window.fetch để an toàn tuyệt đối trước các lỗi 502/503 HTML từ Gateway.
 */

// V45.0: Passive Telemetry — import reactive state from .svelte.ts (runes require Svelte compilation)
import { globalLatency } from "./telemetry.svelte";
// export { globalLatency } from "./telemetry.svelte";

// Define the global ApiError so components can catch it easily
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface ApiOptions extends RequestInit {
  params?: Record<string, string>;
}

function getTenantIdFromHost(): string {
  if (typeof window === "undefined") return "default";
  const hostname = window.location.hostname;
  
  // Handle local development
  if (hostname === "localhost" || hostname === "127.0.0.1") return "osmo.vn";
  
  const parts = hostname.split(".");
  const systemSubdomains = new Set(["admin", "api", "www", "portal"]);
  const relevantParts = parts.filter((p) => !systemSubdomains.has(p));
  
  // Elite V2.2: If we have a clear tenant part (e.g. shopname.osmo.vn), use it.
  // Otherwise, default to osmo.vn if we are on the main domain or admin domain.
  if (relevantParts.length > 0) {
    const tenant = relevantParts.join(".");
    // If it's just "osmo.vn" or similar, that's our primary tenant
    return tenant;
  }
  
  return "osmo.vn"; // Default to primary tenant
}

/**
 * R00: Territory-Isolated Token Resolution.
 * Admin domain → chỉ đọc admin_token.
 * Storefront → chỉ đọc access_token (HttpOnly Cookie xử lý tự động qua credentials:include).
 * CẤM lằn lộn giữa 2 territory.
 */
function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  const isAdmin = window.location.hostname.split(".")[0] === "admin";
  if (isAdmin) {
    return (
      localStorage.getItem("admin_token") ||
      sessionStorage.getItem("admin_token") ||
      null
    );
  }
  // Storefront: access_token chỉ dùng làm fallback cho máy chưa migrate sang HttpOnly Cookie.
  // HttpOnly Cookie được gửi tự động qua credentials: "include".
  return localStorage.getItem("access_token") || null;
}

/**
 * Elite V2.2: Device Fingerprinting Strategy.
 * Tránh logout hàng loạt do thiếu header định danh thiết bị.
 */
function getDeviceFingerprint(): string {
  if (typeof window === "undefined") return "server-node";
  let fp = localStorage.getItem("xohi_device_fingerprint");
  if (!fp) {
    // Tạo vân tay ngẫu nhiên nhưng ổn định cho trình duyệt này
    const randomPart = Math.random().toString(36).substring(2, 15);
    const timePart = Date.now().toString(36);
    fp = `fp_${timePart}_${randomPart}`;
    localStorage.setItem("xohi_device_fingerprint", fp);
  }
  return fp;
}

export const apiClient = {
  /**
   * Core request handler
   */
  async request<T>(endpoint: string, options: ApiOptions = {}): Promise<T> {
    const { params, ...customConfig } = options;

    // 1. Build URL with query params
    const isAbsolute = endpoint.startsWith('http://') || endpoint.startsWith('https://');
    let url: URL;

    if (isAbsolute) {
        url = new URL(endpoint);
    } else {
        const apiBase = typeof window !== 'undefined' ? (window.location.origin + '/api/v1') : 'http://api:8000/api/v1';
        
        // Normalize endpoint
        let cleanEndpoint = endpoint;
        if (cleanEndpoint.startsWith('/api/v1')) {
            cleanEndpoint = cleanEndpoint.substring(7);
        } else if (cleanEndpoint.startsWith('api/v1')) {
            cleanEndpoint = cleanEndpoint.substring(6);
        }
        
        if (!cleanEndpoint.startsWith('/')) cleanEndpoint = '/' + cleanEndpoint;
        url = new URL(apiBase + cleanEndpoint);
    }
    if (params) {
      Object.entries(params).forEach(([k, v]) => url.searchParams.append(k, v));
    }

    // R00: Territory-isolated token. getAuthToken() KHÔNG bao giờ trả về admin_token trên storefront.
    const token = getAuthToken();

    // 2. Set default headers (JSON)
    const config: RequestInit = {
      credentials: "include", // R2: Bắt buộc gửi cookie cho cross-origin
      ...customConfig,
      headers: {
        "Content-Type": "application/json",
        "x-tenant": getTenantIdFromHost(),
        "x-device-fingerprint": getDeviceFingerprint(),
        ...(token ? { "Authorization": `Bearer ${token}` } : {}),
        ...customConfig.headers,
      },
    };

    try {
      const t0 = performance.now();
      const response = await fetch(url.toString(), config);
      globalLatency.set(Math.round(performance.now() - t0));

      // 3. SECURE JSON PARSING (The core fix for "Unexpected end of JSON input")
      let data: unknown = null;
      const contentType = response.headers.get("content-type");

      if (contentType && contentType.includes("application/json")) {
        try {
          data = await response.json();
        } catch (e) {
          console.warn(`[SafeFetch] Could not parse JSON from ${endpoint}`, e);
          data = {};
        }
      } else {
        // If Caddy returns 502 HTML, or it's a 204 No Content
        const text = await response.text();
        data = text ? { detail: text.substring(0, 150) } : {};
      }

      // 4. Handle HTTP Status Errors
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          // Elite V2.2 Domain Guard: Chỉ purge session và redirect /login khi đang ở Admin domain.
          // Tuyệt đối không redirect storefront user sang /login của admin.
          const isAdminDomain = typeof window !== "undefined" &&
            window.location.hostname.startsWith("admin.");
          if (isAdminDomain && !window.location.pathname.includes("/login")) {
            const hasToken = localStorage.getItem("admin_token") || document.cookie.includes("admin_token");
            if (hasToken) {
              console.warn("[SafeFetch] Admin auth failed, purging session...");
              localStorage.removeItem("admin_token");
              localStorage.removeItem("user_token");
              localStorage.removeItem("access_token");
              sessionStorage.clear();
              document.cookie = "admin_token=; path=/; max-age=0; SameSite=Strict";
              document.cookie = "user_token=; path=/; max-age=0; SameSite=Strict";
              window.location.href = "/login";
            }
          }
        }

        const errorData = data as { detail?: unknown; message?: string } | null;
        let errorMessage = errorData?.message || `Lỗi máy chủ (${response.status} ${response.statusText})`;

        // Handle Pydantic V2 Validation Errors (loc)
        if (Array.isArray(errorData?.detail)) {
          const detail = errorData.detail as { loc: (string | number)[]; msg: string; type: string }[];
          errorMessage = detail.map(err => {
            const field = err.loc[err.loc.length - 1];
            // Simple mapping for common fields
            const fieldNames: Record<string, string> = {
              'phone': 'Số điện thoại',
              'name': 'Họ tên',
              'address': 'Địa chỉ',
              'province': 'Tỉnh/Thành',
              'ward': 'Phường/Xã',
              'street': 'Địa chỉ chi tiết'
            };
            const friendlyField = fieldNames[field as string] || field;
            return `${friendlyField}: ${err.msg}`;
          }).join('; ');
        } else if (typeof errorData?.detail === 'string') {
          errorMessage = errorData.detail;
        }

        throw new ApiError(
          response.status,
          errorMessage,
          data,
        );
      }

      // 5. Success
      return data as T;
    } catch (error: unknown) {
      // Catch pure network failures (e.g. docker container down completely)
      if (error instanceof TypeError && error.message.includes("fetch")) {
        throw new ApiError(
          0,
          "Mất kết nối đến máy chủ. Vui lòng kiểm tra mạng.",
          null,
        );
      }
      // Re-throw if it's already an ApiError
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(500, "Lỗi không xác định", error instanceof Error ? error.message : String(error));
    }
  },

  // Convenience methods
  get<T>(url: string, options?: ApiOptions) {
    return this.request<T>(url, { method: "GET", ...options });
  },
  post<T>(url: string, payload: unknown, options?: ApiOptions) {
    return this.request<T>(url, {
      method: "POST",
      body: JSON.stringify(payload),
      ...options,
    });
  },
  put<T>(url: string, payload: unknown, options?: ApiOptions) {
    return this.request<T>(url, {
      method: "PUT",
      body: JSON.stringify(payload),
      ...options,
    });
  },
  patch<T>(url: string, payload: unknown, options?: ApiOptions) {
    return this.request<T>(url, {
      method: "PATCH",
      body: JSON.stringify(payload),
      ...options,
    });
  },
  delete<T>(url: string, options?: ApiOptions) {
    return this.request<T>(url, { method: "DELETE", ...options });
  },
  /**
   * Upload FormData (e.g., audio files). Does NOT set Content-Type header
   * so the browser can set the correct multipart boundary automatically.
   */
  async upload<T>(
    endpoint: string,
    formData: FormData,
    options: ApiOptions = {},
  ): Promise<T> {
    const { params, headers: customHeaders, ...rest } = options;

    const isAbsolute = endpoint.startsWith('http://') || endpoint.startsWith('https://');
    let url: URL;

    if (isAbsolute) {
        url = new URL(endpoint);
    } else {
        const apiBase = typeof window !== 'undefined' ? (window.location.origin + '/api/v1') : 'http://api:8000/api/v1';
        
        let cleanEndpoint = endpoint;
        if (cleanEndpoint.startsWith('/api/v1')) cleanEndpoint = cleanEndpoint.substring(7);
        else if (cleanEndpoint.startsWith('api/v1')) cleanEndpoint = cleanEndpoint.substring(6);
        if (!cleanEndpoint.startsWith('/')) cleanEndpoint = '/' + cleanEndpoint;

        url = new URL(apiBase + cleanEndpoint);
    }
    if (params) {
      Object.entries(params).forEach(([k, v]) => url.searchParams.append(k, v));
    }

    // R00: Territory-isolated token.
    const token = getAuthToken();

    // Explicitly exclude Content-Type so browser sets multipart boundary
    const config: RequestInit = {
      method: "POST",
      credentials: "include",
      body: formData,
      headers: {
        "x-tenant": getTenantIdFromHost(),
        "x-device-fingerprint": getDeviceFingerprint(),
        ...(token ? { "Authorization": `Bearer ${token}` } : {}),
        ...customHeaders,
      },
      ...rest,
    };

    try {
      const t0 = performance.now();
      const response = await fetch(url.toString(), config);
      globalLatency.set(Math.round(performance.now() - t0));

      let data: unknown = null;
      const contentType = response.headers.get("content-type");

      if (contentType && contentType.includes("application/json")) {
        try {
          data = await response.json();
        } catch (e) {
          data = {};
        }
      } else {
        const text = await response.text();
        data = text ? { detail: text.substring(0, 150) } : {};
      }

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          // Elite V2.2 Domain Guard: Đồng bộ với request() — chỉ redirect trên Admin domain.
          const isAdminDomain = typeof window !== "undefined" &&
            window.location.hostname.startsWith("admin.");
          const hasToken = typeof window !== "undefined" &&
            (!!localStorage.getItem("admin_token") || document.cookie.includes("admin_token"));
          if (isAdminDomain && hasToken && !window.location.pathname.includes("/login")) {
            localStorage.removeItem("admin_token");
            localStorage.removeItem("user_token");
            localStorage.removeItem("access_token");
            sessionStorage.clear();
            document.cookie = "admin_token=; path=/; max-age=0; SameSite=Strict";
            document.cookie = "user_token=; path=/; max-age=0; SameSite=Strict";
            window.location.href = "/login";
          }
        }

        throw new ApiError(
          response.status,
          (data as { detail?: string; message?: string })?.detail || (data as { detail?: string; message?: string })?.message || `Upload Error (${response.status})`,
          data,
        );
      }

      return data as T;
    } catch (error) {
      if (error instanceof TypeError && error.message.includes("fetch")) {
        throw new ApiError(0, "Mất kết nối đến máy chủ.", null);
      }
      throw error;
    }
  },
};
