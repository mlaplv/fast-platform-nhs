import { logger } from "$lib/utils/logger";

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
    logger.warn('Failed to extract ID from URL', url, e);
  }

  return null;
}

/**
 * R105: Sanitizes user/tenant IDs to prevent "undefined" string leakage.
 */
export function sanitizeId(id: string | null | undefined): string | null {
  if (!id) return null;
  const s = String(id).trim();
  if (s.toLowerCase() === "undefined" || !s) return null;
  return s;
}

import { purifyAIContent } from "$lib/utils/purify";
import type { MediaAsset } from "./types";

/**
 * CNS V80: Polymorphic Media Resolver.
 * Ensures consistent URL for local files and external (Google/AI) links.
 */
export function resolveMediaUrl(url: string | null | undefined): string {
    if (!url) return '';

    // 1. Absolute URLs (http, https, //, blob, data)
    if (url.startsWith('http') || url.startsWith('//') || url.startsWith('blob:') || url.startsWith('data:')) {
        return url;
    }

    // 2. Clean up leading slashes and legacy prefixes
    let path = url.trim();
    if (path.startsWith('/')) path = path.slice(1);

    // Legacy support: remove redundant 'static/uploads' or 'uploads' if they exist twice
    if (path.startsWith('static/uploads/')) path = path.slice(15);
    if (path.startsWith('uploads/')) path = path.slice(8);

    // 3. Construct final path (default to /uploads/ prefix for internal files)
    return `/uploads/${path}`;
}

/**
 * Elite V2.6: Dynamic WebP Resizer Resolver.
 * Extracts UUID from path to leverage public dynamic resizing API when width is specified.
 */
export function resolveOptimizedImageUrl(url: string | null | undefined, width?: number): string {
    if (!url) return '';
    const base = resolveMediaUrl(url);
    if (!width) return base;

    const id = extractIdFromUrl(url);
    if (id) {
        return `/api/v1/media/${id}/thumb?w=${width}`;
    }
    return base;
}


/**
 * CNS V110: Standardized Unit Formatting.
 */
export function formatBytes(bytes: number = 0): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

/**
 * CNS V110: Standardized Date Formatting.
 */
export function formatDate(dateStr?: string | Date, includeTime: boolean = false): string {
    if (!dateStr) return 'N/A';
    const date = typeof dateStr === 'string' ? new Date(dateStr) : dateStr;

    if (includeTime) {
        return date.toLocaleString('vi-VN', {
            hour: '2-digit',
            minute: '2-digit',
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    }

    return date.toLocaleDateString('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

/**
 * CNS V105: Unified Thumbnail/Preview URL Resolver.
 * Handles both API-based thumbnails and full resolution previews with cache busting.
 */
export function resolveThumbnailUrl(asset: MediaAsset, width?: number): string {
    if (!asset) return '';
    if (asset.id?.startsWith('tmp_')) return asset.file_path || '';

    // If width is provided, use the thumbnail API
    if (width) {
        const base = `/api/v1/media/${asset.id}/thumb?w=${width}`;
        return asset._updatedAt ? `${base}&t=${asset._updatedAt}` : base;
    }

    // Otherwise use the full media resolution helper
    const url = asset.file_path || asset.url || '';
    const base = resolveMediaUrl(url);
    return asset._updatedAt ? `${base}?t=${asset._updatedAt}` : base;
}

/**
 * Elite V2.2: Unified HTML Media Processor.
 * Standardizes [IMAGE_n] replacement and external-to-local link mapping.
 */
export function processContentImages(html: string | null | undefined, assets: (MediaAsset | string)[]): string {
    let base = html || "";
    if (!base) return "";

    const assetList = Array.isArray(assets) ? assets : [];

    // 1. Resolve [IMAGE_n] placeholders
    if (base.includes("[IMAGE_")) {
        assetList.forEach((asset, i) => {
            const url = typeof asset === 'string' ? asset : (asset.file_path || asset.url || '');
            const local = resolveMediaUrl(url);
            const placeholder = `[IMAGE_${i + 1}]`;

            // Surgical replacement: Handle markers inside src first
            const srcPattern = new RegExp(`(src|href)=["']\\s*${placeholder.replace('[', '\\[').replace(']', '\\]')}\\s*["']`, 'g');
            base = base.replace(srcPattern, `$1="${local}"`);

            // Then handle standalone markers (even if wrapped in figure by AI)
            const figurePattern = new RegExp(`(<figure[^>]*>\\s*)?${placeholder.replace('[', '\\[').replace(']', '\\]')}(\\s*<\\/figure>)?`, 'g');
            base = base.replace(figurePattern, `<figure class="image-figure"><img src="${local}" alt="content image" loading="lazy" /></figure>`);
        });
        // Cleanup leftover placeholders
        base = base.replace(/\[IMAGE_\d+\]/g, "");
    }

    // 2. Replace external links with local assets in sequence (Viral 2026 Engine)
    if (base.includes("<img") && assetList.length > 0) {
        let idx = 0;
        const locals = assetList.map(a => resolveMediaUrl(typeof a === 'string' ? a : (a.file_path || a.url || '')));
        base = base.replace(/<img([^>]+)src=["']([^"']+)["']([^>]*)>/gi, (full, pre, src, post) => {
            if (src.includes('/api/v1/media/') || src.includes('/uploads/') || src.startsWith('data:')) {
                if (!full.includes('alt=') || full.includes('alt=""') || full.includes("alt=''")) {
                    let cleaned = full.replace('alt=""', '').replace("alt=''", '');
                    return cleaned.replace('<img', '<img alt="product content image" ');
                }
                return full;
            }
            const newSrc = idx < locals.length ? locals[idx++] : src;
            let result = `<img${pre}src="${newSrc}"${post}>`;
            if (!result.includes('alt=') || result.includes('alt=""') || result.includes("alt=''")) {
                result = result.replace('alt=""', '').replace("alt=''", '');
                result = result.replace('<img', '<img alt="product detail image" ');
            }
            return result;
        });
    }

    return purifyAIContent(base);
}
