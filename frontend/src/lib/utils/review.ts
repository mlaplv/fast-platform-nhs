import type { Review } from '$lib/types';

export interface RawReview {
  id: string | number;
  name?: string;
  customer_name?: string;
  phone?: string;
  customer_phone?: string;
  location?: string;
  customer_location?: string;
  rating?: number;
  content?: string;
  created_at?: string;
  attributes?: Record<string, string>;
  attachments?: Array<{ url: string; type: 'image' | 'video' }>;
  likes_count?: number;
}

/**
 * Normalizes raw review payloads from the server (both SSR and dynamic API responses)
 * into the standardized frontend UI Review model.
 */
export function mapRawReview(r: RawReview): Review {
  // Ensure paragraphs/HTML tags from Rich Text Editor are normalized properly
  const cleanContent = r.content
    ? r.content.trim().replace(/^<p[^>]*>/i, '').replace(/<\/p>$/i, '').trim()
    : '';

  // Extract real name, stripping phone numbers/metadata appended in legacy seeding tools
  const rawName = r.name || r.customer_name || 'Ẩn danh';
  const cleanName = rawName.split('(')[0].split('-')[0].trim() || 'Ẩn danh';

  // Obfuscate / Mask customer phone numbers to protect PII
  const rawPhone = r.phone || r.customer_phone;
  const maskedPhone = rawPhone
    ? (rawPhone.startsWith('0') ? '0' + rawPhone.slice(-9, -3) + '***' : rawPhone.slice(0, 3) + '****' + rawPhone.slice(-3))
    : '09x****xxx';

  return {
    id: r.id,
    name: cleanName,
    phone: maskedPhone,
    location: r.location || r.customer_location || 'Việt Nam',
    rating: r.rating || 5,
    content: cleanContent,
    initial: cleanName.charAt(0).toUpperCase(),
    created_at: r.created_at,
    attributes: r.attributes,
    attachments: r.attachments,
    likes_count: r.likes_count || 0
  };
}
