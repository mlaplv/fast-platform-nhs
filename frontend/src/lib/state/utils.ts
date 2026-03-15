export function safeRandomUUID(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Robust Fallback (RFC 4122)
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * CNS V75: Extracts the real DB ID (UUID) from a media URL.
 * Supports /api/v1/media/{uuid} and /uploads/.../{uuid}.webp formats.
 */
export function extractIdFromUrl(url: string | null): string | null {
  if (!url) return null;
  
  // 1. Try to find UUID pattern in the URL
  const uuidRegex = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;
  const match = url.match(uuidRegex);
  if (match) return match[0];

  // 2. Fallback: Parse the last segment before extension if it looks like an ID
  try {
    const parts = url.split('/');
    const lastPart = parts[parts.length - 1].split('?')[0].split('.')[0];
    
    // IDs in our system are usually UUIDs, but could be alphanumeric
    // If it's not a generic name like 'placeholder', 'logo', 'image', it might be our ID
    const genericNames = ['placeholder', 'logo', 'image', 'avatar', 'default', 'thumb'];
    if (lastPart.length > 20 && !genericNames.some(name => lastPart.toLowerCase().includes(name))) {
        return lastPart;
    }
  } catch (e) {
    // Silent fail
  }

  return null;
}
