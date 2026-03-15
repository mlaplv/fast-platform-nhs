import type { MediaAsset } from "../types";

export const SIGNAL_THROTTLE_MS = 5000;
export const THINKING_TIMEOUT_MS = 30_000;

export const normalizeAssets = (data: unknown): MediaAsset[] => {
  if (!data) return [];
  if (Array.isArray(data)) return data as MediaAsset[];

  if (typeof data === 'object' && data !== null) {
    const obj = data as Record<string, unknown>;
    if (obj.raw && Array.isArray(obj.raw)) return obj.raw as MediaAsset[];
    if (obj.assets && Array.isArray(obj.assets)) return obj.assets as MediaAsset[];

    // Fallback for asset objects that might be nested or have different keys
    const possibleList = Object.values(obj).find(v => Array.isArray(v));
    if (possibleList) return possibleList as MediaAsset[];
  }
  return [];
};
