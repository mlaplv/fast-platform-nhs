export const SIGNAL_THROTTLE_MS = 5000;
export const THINKING_TIMEOUT_MS = 30_000;

export const normalizeAssets = (data: any): any[] => {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  if (typeof data === 'object' && data.raw && Array.isArray(data.raw)) return data.raw;
  if (typeof data === 'object' && data.assets && Array.isArray(data.assets)) return data.assets;
  // Fallback for asset objects that might be nested or have different keys
  if (typeof data === 'object') {
     const possibleList = Object.values(data).find(v => Array.isArray(v));
     if (possibleList) return possibleList as any[];
  }
  return [];
};
