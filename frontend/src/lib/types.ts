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
  planning?: OrderPlanning;
  order_metadata?: {
    zalo_status?: 'ACTIVE' | 'NOT_FOUND' | 'PENDING';
    [key: string]: unknown;
  };
}

export interface OrderPlanning {
  assigned_to?: string;
  scheduled_at?: string;
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
  planning_notes?: string;
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

export interface PromotionDeal {
  buy_qty: number;
  get_qty: number;
  fixed_price: number;
  label: string;
  scope: 'global' | 'variant_only';
}

export interface ProductMetadata {
  active_deals?: PromotionDeal[];
  landing_type?: 'standard' | 'tiktok' | 'stealth';
  scarcity_seconds?: number;
  show_reviews?: boolean;
  video_url?: string;
  reviews_headline?: string;
  reviews_trust_score?: string;
  reviews_count_text?: string;
  reviews?: Review[];
  quiz_questions?: QuizQuestion[];
  science_headline?: string;
  science_subheadline?: string;
  science_claims?: ScienceClaim[];
  science_mechanism_image?: string;
  science_mechanism_image_alt?: string;
  science_stats?: ScienceStat;
  science_guarantee?: ScienceGuarantee;
  offer_headline?: string;
  offer_subheadline?: string;
  offer_timer_prefix?: string;
  offer_shipping_prefix?: string;
  offer_savings_prefix?: string;
  offer_booking_suffix?: string;
  offer_trust_verified_by?: string;
  offer_compliance_note?: string;
  offer_label_activation?: string;
  offer_label_full_treatment?: string;
  offer_label_expert_choice?: string;
  offer_label_scarcity?: string;
  offer_cta_start?: string;
  offer_cta_full?: string;
  hero_headline?: string;
  hero_video_url?: string;
  hero_cta_text?: string;
  hero_metrics?: HeroMetric[];
  header_nav_links?: NavLink[];
  checkout_phone_error?: string;
  checkout_address_error?: string;
  checkout_footer_text?: string;
  mobile_handle?: string;
  mobile_hashtags?: string;
  mobile_music_label?: string;
  mobile_shop_avatar?: string;
  mobile_stats_likes?: number;
  mobile_stats_comments?: number;
  mobile_stats_shares?: number;
  mobile_stats_saves?: number;
  mobile_label_share?: string;
  mobile_label_purchase?: string;
  mobile_disk_image?: string;
  mobile_bottom_sheet_title?: string;
  mobile_bottom_sheet_cta?: string;
  mobile_free_shipping_label?: string;
  mobile_variant_selection_label?: string;
  diagnostics_headline?: string;
  diagnostics_subheadline?: string;
  diagnostics_disclaimer?: string;
  science_mechanism_label?: string;
  science_scan_label?: string;
  science_viewer_label?: string;
  quiz_result_headline?: string;
  quiz_result_subheadline?: string;
  quiz_result_cta?: string;
  quiz_restart_label?: string;
  sync_loading_text?: string;
  seo_site_name?: string;
  reviews_cta_write?: string;
  reviews_form_title?: string;
  reviews_form_name_label?: string;
  reviews_form_phone_label?: string;
  reviews_form_location_label?: string;
  reviews_form_rating_label?: string;
  reviews_form_content_label?: string;
  reviews_form_placeholder_content?: string;
  reviews_form_cta_submit?: string;
  reviews_form_success_title?: string;
  reviews_form_success_msg?: string;
  checkout_title?: string;
  checkout_trust_active?: string;
  checkout_reservation_msg?: string;
  checkout_success_title?: string;
  checkout_success_msg?: string;
  checkout_label_summary?: string;
  checkout_label_phone?: string;
  checkout_label_address?: string;
  checkout_label_total?: string;
  checkout_label_cta?: string;
  checkout_label_processing?: string;
  checkout_placeholder_phone?: string;
  checkout_placeholder_address?: string;
  offer_label_distributor?: string;
  offer_label_support?: string;
  offer_label_commitment?: string;
  offer_label_license?: string;
  mobile_loading_text?: string;
  [key: string]: unknown;
}

export interface NavLink {
  id: string;
  label: string;
  href: string;
}

export interface HeroMetric {
  label: string;
  value: string;
  desc: string;
  color: string;
}

export interface Review {
  id: string | number;
  name: string;
  phone?: string;
  location: string;
  rating: number;
  content: string;
  initial: string;
  avatar?: string;
}

export interface QuizOption {
  label: string;
  desc: string;
  value: string;
  icon: string;
}

export interface QuizQuestion {
  id: string | number;
  title: string;
  subtitle: string;
  options: QuizOption[];
}

export interface ScienceClaim {
  label: string;
  content: string;
  image?: string;
}

export interface ScienceStat {
  value: string;
  unit: string;
  label: string;
  description: string;
}

export interface ScienceGuarantee {
  icon: string;
  label: string;
  description: string;
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
  metadata: ProductMetadata;
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
