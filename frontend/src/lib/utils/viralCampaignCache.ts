/**
 * Elite V2.2 — Viral Campaign Singleton Cache
 * Deduplicate ALL `/api/v1/client/viral/campaign/{id}` calls at module level.
 * Survives component unmount/remount — no 429 loop possible.
 */

type CampaignResult = {
  exists: boolean;
  enabled: boolean;
  data: Record<string, unknown> | null;
};

// Module-level cache: persists for entire browser session
const _cache = new Map<string, CampaignResult>();
// In-flight promises: prevents duplicate concurrent requests for same id
const _inflight = new Map<string, Promise<CampaignResult>>();

export async function fetchViralCampaign(voucher_id: string): Promise<CampaignResult> {
  // 1. Return cached result immediately (hit)
  const cached = _cache.get(voucher_id);
  if (cached !== undefined) return cached;

  // 2. Return in-flight promise if already fetching (dedup concurrent calls)
  const inflight = _inflight.get(voucher_id);
  if (inflight) return inflight;

  // 3. Fire new request and cache the promise immediately to block duplicates
  const promise = fetch(`/api/v1/client/viral/campaign/${voucher_id}`)
    .then(async (res) => {
      if (!res.ok) {
        const result: CampaignResult = { exists: false, enabled: false, data: null };
        _cache.set(voucher_id, result);
        return result;
      }
      const json = await res.json();
      const result: CampaignResult = {
        exists: json.exists !== false,
        enabled: json.enabled !== false,
        data: json,
      };
      _cache.set(voucher_id, result);
      return result;
    })
    .catch((): CampaignResult => {
      const result: CampaignResult = { exists: false, enabled: false, data: null };
      _cache.set(voucher_id, result);
      return result;
    })
    .finally(() => {
      _inflight.delete(voucher_id);
    });

  _inflight.set(voucher_id, promise);
  return promise;
}
