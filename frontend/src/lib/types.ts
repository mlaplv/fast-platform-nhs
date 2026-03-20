// TypeScript Type Definitions for Svelte Frontend

export interface Category {
  id: string;
  name: string;
  slug: string;
  parentId: string | null;
  productCount: number;
  children: Category[];
  createdAt: string;
}

export interface User {
  id: string;
  email: string;
  name: string | null;
  status: string;
  roles: Role[];
  createdAt: string;
}

export interface Role {
  id: string;
  name: string;
  code: string;
  description: string | null;
  permissions: Permission[];
}

export interface Permission {
  id: string;
  name: string;
  code: string;
  description: string | null;
}

export interface OrderItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
}

export interface OrderHistory {
  status: string;
  timestamp: string;
  actor: string;
  note?: string;
}

export interface Order {
  id: string;
  customerName: string;
  total: number;
  status: string;
  items: number;
  isSpam: boolean;
  spamScore?: number;
  fingerprint?: string;
  spamReason?: string;
  createdAt: string;
}

export interface OrderDetail extends Order {
  items: OrderItem[];
  history: OrderHistory[];
}

export interface Article {
  id: string;
  title: string;
  slug: string;
  excerpt: string | null;
  status: string;
  category: string;
  views: number;
  author: string;
  authorId: string | null;
  createdAt: string;
}

export interface Product {
    id: string;
    name: string;
    sku: string;
    price: number;
    stock: number;
    status: string;
    category: string;
    categoryId: string | null;
    description: string | null;
    type: string;
    createdAt: string;
}

export interface MediaMetadata {
  embedding?: number[];
  ai_tags?: string[];
  ai_description?: string;
  focal_point?: { x: number; y: number };
  original_source?: string;
  ai_sentiment?: string;
  [key: string]: unknown;
}

export interface MediaAsset {
  id: string;
  filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  dimensions: string | null;
  blurhash: string | null;
  alt_text: string | null;
  is_public: boolean;
  campaign_id: string | null;
  owner_id: string | null;
  created_at: string;
  media_metadata: MediaMetadata;
  _updatedAt?: number; // Internal cache buster
}

export interface MediaStatsBreakdown {
  type: string;
  count: number;
  size: number;
}

export interface MediaStats {
  total_count: number;
  total_size: number;
  breakdown: MediaStatsBreakdown[];
  storage_provider: string;
}

export interface MediaSseEvent {
  type: string;
  id?: string;
  asset_id?: string;
  alt_text?: string;
  metadata?: Record<string, unknown>;
  media_metadata?: Record<string, unknown>;
}

export interface JwtPayload {
  sub: string;
  name?: string;
  roles?: string[];
  perms?: string[];
  exp?: number;
  iat?: number;
}

export interface EditorAnnotation {
  text: string;         // Exact text to find and highlight in the editor
  type: string;         // 'copyright' | 'seo-error' | 'seo-warning' | 'seo-info' | specific type
  message: string;      // Vietnamese tooltip text
  source?: string;      // URL (for copyright)
  severity: string;     // 'low' | 'medium' | 'high' | 'info' | 'warning' | 'error'
}

export interface ToolbarAction {
  label: string;
  loading?: boolean;
  disabled?: boolean;       // Gate lock — nút bị khoá
  lockedMsg?: string;       // Tooltip hiển thị khi bị khoá
  onclick: () => void | Promise<void>;
  tooltipDetails?: {        // Tooltip chuyên nghiệp
    icon?: any;             // lucide-svelte icon component
    title: string;
    description: string;
    colorClass?: string;    // e.g. text-pink-400
  };
}

export interface BaseWidgetProps {
  data?: Record<string, unknown>;
}

