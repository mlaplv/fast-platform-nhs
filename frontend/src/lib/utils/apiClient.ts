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
  const parts = window.location.hostname.split(".");
  const systemSubdomains = new Set(["admin", "api", "www", "portal"]);
  const relevantParts = parts.filter((p) => !systemSubdomains.has(p));
  return relevantParts.length > 0 ? relevantParts.join(".") : "default";
}

export const apiClient = {
  /**
   * Core request handler
   */
  async request<T>(endpoint: string, options: ApiOptions = {}): Promise<T> {
    const { params, ...customConfig } = options;

    // 1. Build URL with query params
    const apiBase = typeof window !== 'undefined' ? (window.location.origin + '/api/v1') : 'http://api:8000/api/v1';
    
    // Normalize endpoint: if it starts with /api/v1, remove it if we are using apiBase
    let cleanEndpoint = endpoint;
    if (cleanEndpoint.startsWith('/api/v1')) {
        cleanEndpoint = cleanEndpoint.substring(7);
    } else if (cleanEndpoint.startsWith('api/v1')) {
        cleanEndpoint = cleanEndpoint.substring(6);
    }
    
    // Ensure cleanEndpoint starts with /
    if (!cleanEndpoint.startsWith('/')) cleanEndpoint = '/' + cleanEndpoint;

    const url = new URL(apiBase + cleanEndpoint);
    if (params) {
      Object.entries(params).forEach(([k, v]) => url.searchParams.append(k, v));
    }

    // Add robust Bearer token fallback (CNS V2 - Resilient Auth)
    const token = typeof window !== "undefined" ? (localStorage.getItem("admin_token") || localStorage.getItem("access_token") || sessionStorage.getItem("admin_token")) : null;

    // 2. Set default headers (JSON)
    const config: RequestInit = {
      credentials: "include", // R2: Bắt buộc gửi cookie cho cross-origin
      ...customConfig,
      headers: {
        "Content-Type": "application/json",
        "x-tenant": getTenantIdFromHost(),
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

    const apiBase = typeof window !== 'undefined' ? (window.location.origin + '/api/v1') : 'http://api:8000/api/v1';
    
    let cleanEndpoint = endpoint;
    if (cleanEndpoint.startsWith('/api/v1')) cleanEndpoint = cleanEndpoint.substring(7);
    else if (cleanEndpoint.startsWith('api/v1')) cleanEndpoint = cleanEndpoint.substring(6);
    if (!cleanEndpoint.startsWith('/')) cleanEndpoint = '/' + cleanEndpoint;

    const url = new URL(apiBase + cleanEndpoint);
    if (params) {
      Object.entries(params).forEach(([k, v]) => url.searchParams.append(k, v));
    }

    const token = typeof window !== "undefined" ? (localStorage.getItem("admin_token") || localStorage.getItem("access_token") || sessionStorage.getItem("admin_token")) : null;

    // Explicitly exclude Content-Type so browser sets multipart boundary
    const config: RequestInit = {
      method: "POST",
      credentials: "include",
      body: formData,
      headers: {
        "x-tenant": getTenantIdFromHost(),
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
