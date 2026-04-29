export type ReviewEntityType = 'PRODUCT' | 'CATEGORY' | 'NEWS' | 'SHOP';

export interface ReviewAttachment {
  url: string;
  type: 'image' | 'video';
}

export interface Review {
  id: string;
  entity_type: ReviewEntityType;
  entity_id: string;
  customer_name: string;
  customer_phone?: string;
  customer_location?: string;
  rating: number;
  content: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  attachments?: ReviewAttachment[];
  likes_count: number;
  attributes?: Record<string, string>;
  created_at: string;
  updated_at: string;
  
  // UI Helpers
  initial?: string;
  is_liked?: boolean;
}

export interface ReviewStats {
  total_count: number;
  average_rating: number;
  rating_breakdown: Record<number, number>;
  has_content_count: number;
  has_media_count: number;
}

export interface ReviewListResponse {
  items: Review[];
  total: number;
}
