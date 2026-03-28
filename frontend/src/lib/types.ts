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

export interface CustomerInsight {
  ltv: number;
  total_orders: number;
  trust_score: number;
  first_order?: string;
  last_order?: string;
  previous_orders: {
    id: string;
    created_at: string;
    status: string;
    total: number;
    item_count: number;
  }[];
}

export interface Order {
  customerName?: string;
  customerPhone?: string;
  customerAddress?: string;
  customerIp?: string;
  userName?: string;
  finalCustomerName: string;
  total: number;
  status: string;
  itemCount: number;
  isSpam: boolean;
  spamScore?: number;
  fingerprint?: string;
  spamReason?: string;
  createdAt: string;
  successfulOrdersCount: number;
  cancelledOrdersCount: number;
}

export interface OrderDetail extends Order {
  items: OrderItem[];
  history: OrderHistory[];
  insight?: CustomerInsight;
  cancellationReason?: string;
}

export interface Article {
  id: string;
  title: string;
  slug: string;
  excerpt: string | null;
  content: string | null;
  seoTitle: string | null;
  seoDescription: string | null;
  seoKeywords: string | null;
  seoOgImage: string | null;
  status: string;
  category: string;
  featuredImage: string | null;
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
    discountPrice?: number;
    stock: number;
    status: string;
    category: string;
    categoryId: string | null;
    shortDescription: string | null;
    description: string | null;
    type: string;
    slug: string;
    seoTitle: string | null;
    seoDescription: string | null;
    images: string[];
    attributes: Record<string, unknown>;
    tierVariations: TierVariation[];
    variants: ProductVariant[];
    createdAt: string;
}

export interface TierVariation {
  name: string;
  options: string[];
  images: (string | null)[];
}

export interface ProductVariant {
  id: string;
  tierIndex: number[];
  sku: string;
  price: number;
  discountPrice?: number;
  stock: number;
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
  total_trash_count: number;
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
    icon?: import('svelte').Component;             // lucide-svelte icon component
    title: string;
    description: string;
    colorClass?: string;    // e.g. text-pink-400
  };
}

export interface BaseWidgetProps {
  data?: Record<string, unknown>;
}

export interface RecurringMetadata {
  monthly_type?: 'day_of_month' | 'day_of_week';
  day_of_month?: number;
  day_of_week?: number;
  week_index?: number;
}

export interface Appointment {
  id: string;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  type: 'STRATEGY' | 'DEPLOYMENT' | 'REVIEW';
  status: 'UPCOMING' | 'ONGOING' | 'COMPLETED';
  recurring_type: 'none' | 'daily' | 'weekly' | 'monthly';
  recurring_metadata: RecurringMetadata;
  metadata_json: Record<string, unknown>;
  created_at: string;
}

export interface AppointmentListResponse {
  items: Appointment[];
  total: number;
}
export interface Banner {
  id: string;
  title: string;
  description: string | null;
  image_url: string;
  link_url: string | null;
  position: string;
  order_index: number;
  is_active: boolean;
  device_type: string;
  created_at: string;
}

export interface BannerForm {
  id?: string;
  title: string;
  description: string;
  image_url: string;
  link_url: string;
  position: string;
  order_index: number;
  is_active: boolean;
  device_type: string;
}
