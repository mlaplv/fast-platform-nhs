import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { ServerEnv } from '$lib/server/env';

export const trailingSlash = 'always';

export const load: PageServerLoad = async ({ fetch, locals }) => {
  const apiUrl = ServerEnv.INTERNAL_API_URL;
  const tenantId = ServerEnv.TENANT_ID; // Elite V2.2: Hard tenant ID for backend queries
  const currentTenant = locals.tenant; // Dynamic context for logic branching

  // Elite V2.2: Bypass storefront fetch for admin tenant
  if (currentTenant === 'admin') {
      return {
          home: null,
          timestamp: new Date().toISOString(),
          tenant: 'admin'
      };
  }

  const targetUrl = `${apiUrl}/api/v1/client/home`;

    let res;
    try {
        res = await fetch(targetUrl, {
            headers: { 'x-tenant': tenantId },
            signal: AbortSignal.timeout(5000) // Rationale: Prevent "Neural Link" hang
        });
    } catch (err: unknown) {
        const e = err as Error;
        const isTimeout = e.name === 'TimeoutError' || e.message?.includes('timeout');
        console.error(`[ROOT FETCH FAILED] ${isTimeout ? 'TIMEOUT' : 'CONNECTION ERROR'}`);
        console.error(`URL: ${targetUrl}`);
        
        throw error(isTimeout ? 504 : 503, {
            message: isTimeout 
                ? "Hệ thống đang phản hồi chậm (Backend Timeout)" 
                : "Dịch vụ tạm thời không khả dụng (Backend Connection Failed)",
            details: isTimeout 
                ? "Vui lòng chờ giây lát và thử lại (Request timed out after 5s)."
                : `Failed to reach API at ${apiUrl}.`
        });
    }

  if (!res.ok) {
    throw error(res.status, {
      message: `API Error: ${res.statusText} (${res.status})`,
      details: `Failed to fetch home data from ${targetUrl}`
    });
  }

  const data = await res.json();
  return data;
};