export interface SystemLog {
  id: string;
  timestamp: Date;
  message: string;
  source: string;
  type?: string;
  routerTier?: number;
  data?: Record<string, unknown>;
}

export interface Notification {
  id: string;
  type: string;
  message: string;
  isRead: boolean;
  created_at: string;
}

export type WidgetType =
  | "NONE"
  | "REVENUE_CHART"
  | "SHOW_REVENUE"
  | "SHOW_PRODUCT_EDIT"
  | "USER_TABLE"
  | "USER_MANAGEMENT"
  | "PERMISSION_MANAGEMENT"
  | "CATEGORY_MANAGEMENT"
  | "PRODUCT_MANAGEMENT"
  | "ORDER_MANAGEMENT"
  | "NEWS_MANAGEMENT"
  | "VOICE_SETTINGS"
  | "CAMPAIGNS"
  | "CONTENT_REVIEW"
  | "MEDIA_MANAGER"
  | "SYSTEM_SETTINGS"
  | "BANNER_MANAGEMENT"
  | "APPOINTMENTS";

export type NanoBotState =
  | "IDLE"
  | "THINKING"
  | "PROCESSING"
  | "ERROR"
  | "SUCCESS"
  | "VOICE";

export type CampaignStatus = "IDLE" | "PROCESSING" | "COMPLETED" | "PAUSED" | "ERROR";

export type HudPopupType = "NONE" | "NOTIFICATIONS" | "USER";

export interface Suggestion {
  label: string;
  command: string;
}

export interface PendingAction {
  id: string;
  draftId?: string; // Phase 3: Auditor Link
  description: string;
  actionType: "DELETE_USER" | "UPDATE_SYSTEM";
}

export interface ChatSettings {
  selective_persistence: boolean;
  save_ai_responses: boolean;
  auto_purge_days: number;
  cache_limit: number;
  [key: string]: unknown;
}

export interface IntentResponse {
  message?: string;
  action?: "READ" | "MUTATE" | "COUNT" | "ANALYZE";
  status?: string;
  data?: Record<string, unknown>;
  router_tier?: number;
  cost_tokens?: number;
  requires_confirmation?: boolean; // V21.0: Safety gate
}

export interface ScreenContext {
  current_route: string;
  active_widget: string;
  visible_data_ids: string[];
}

// ── Phase 12: Voice/Text CRUD Command Dispatch ──
export type CommandVerb =
  | "open"
  | "create"
  | "edit"
  | "delete"
  | "search"
  | "view"
  | "select"
  | "save"
  | "close";

export type CommandEntity =
  | "category"
  | "product"
  | "order"
  | "news"
  | "article"
  | "user"
  | "identity"
  | "permission"
  | "role"
  | "voice"
  | "campaign";

export interface CommandAction {
  verb: CommandVerb;
  entity: CommandEntity | "media";
  args?: string;
  metadata?: Record<string, unknown>;
  consumed?: boolean;
}

export interface FormField {
  key: string;
  label: string;
  type: "text" | "email" | "password" | "number" | "select" | "textarea";
  required?: boolean;
  placeholder?: string;
  defaultValue?: string;
  options?: { value: string; label: string }[];
}

export interface ConfirmDialog {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  isPrompt?: boolean;
  promptPlaceholder?: string;
  defaultValue?: string;
  fields?: FormField[];
  onConfirm: (value?: string | Record<string, string>) => void;
  onCancel?: () => void;
}

export type ToastType = "success" | "error" | "info" | "warning";

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

export interface AnalysisAnnotation {
  text: string;
  type: string;
  message?: string;
  reason?: string;
  source_url?: string;
  severity?: string;
}

export interface CopyrightResult {
  uniqueness_score: number;
  risk_level?: string;
  annotations: AnalysisAnnotation[];
}

export interface SeoSignal {
  label: string;
  score: number;
  status: string;
}

export interface SEOResult {
  total_score: number;
  grade: string;
  summary: string;
  signals: SeoSignal[];
  quick_wins: string[];
  seo_annotations: AnalysisAnnotation[];
}

export interface AIInspectResult {
  geo_score: number;
  summary: string;
  ai_annotations: AnalysisAnnotation[];
}

export interface CampaignSection {
  heading?: string;
  content?: string;
}

export interface CampaignOutline {
  sections?: CampaignSection[];
  html?: string;
}

// ── Phase 8: Campaign & Content Types (@agrules) ──

export interface MediaMetadata {
  embedding?: number[];
  ai_tags?: string[];
  ai_description?: string;
  focal_point?: { x: number; y: number };
  original_source?: string;
  sentiment?: string;
  analyzed_at?: string;
  status?: 'uploading' | 'ready' | 'error';
  error?: string;
  name?: string;
}

export interface MediaAsset {
  id: string;
  file_path: string;      // Backend field
  url?: string;            // UI legacy (deprecated)
  filename?: string;
  file_size?: number;
  mime_type?: string;
  dimensions?: string;
  blurhash?: string;
  alt_text?: string;
  is_public?: boolean;
  campaign_id?: string;
  owner_id?: string;
  created_at?: string;
  media_metadata?: MediaMetadata;
  linked_post_id?: string;
  linked_post_type?: string;
  // UI-specific fields (Managed by Campaign/Store)
  is_primary: boolean;
  order_index: number;
  _updatedAt?: number;
}

export interface CampaignKeywords {
  title?: string;
  primary_keyword?: string;
  secondary_keywords?: string[];
  persona?: string;
  category?: string;
  slug?: string;
  description?: string;
  creation_config?: Record<string, unknown>;
}

export interface CampaignMetrics {
  unique_score?: number;
  seo_score?: number;
  ai_ready_score?: number;
  draft_content?: string;
  last_analyzed?: string | number | Date;
}

export interface AnalysisCache {
  copyright?: { data: CopyrightResult };
  seo?: { data: SEOResult };
  ai_inspect?: { data: AIInspectResult };
}

export interface CampaignData {
  id: string;
  campaign_id?: string; // Sometimes used interchangeably in SSE
  category: string;
  step: number;
  status: string;
  progress_msg?: string;
  keywords?: CampaignKeywords;
  assets?: (MediaAsset | string)[];
  reserve_assets?: (MediaAsset | string)[];
  outline?: CampaignOutline;
  draft_content?: string;
  final_html?: string;
  unique_score?: number;
  analysis_cache?: AnalysisCache;
  analysis_metrics?: CampaignMetrics;
  selectedAvatarUrl?: string | null;
  selectedAssetIndex?: number;
  creation_config?: Record<string, unknown>;
  // SSE Aliases (Rule R122: Map legacy server keys to UI)
  topic_data?: CampaignKeywords;
  assets_data?: (MediaAsset | string)[];
  outline_data?: CampaignOutline;
  isSilent?: boolean;
  data?: Record<string, unknown>;
  gold_metadata?: {
    avatar?: string;
    selected_index?: number;
    reserve_assets?: (MediaAsset | string)[];
    creation_config?: Record<string, unknown>;
    analysis_cache?: AnalysisCache;
    analysis_metrics?: CampaignMetrics;
  };
}

export interface PulsePayload {
  id: string;
  step: number;
  message: string;
  status?: string;
  reason?: string;
  data?: Record<string, unknown>; 
}

export interface PulseSignal {
  notification_id: string;
  message: string;
  severity: "CRITICAL" | "ACTION" | "PROGRESS" | "INFO";
}

// ── Phase 12: AI Management Types ──
export interface AIModelConfig {
  primary_model: string | null;
  ai_models: string[];
  discovered_models?: string[];
}

export interface AIKeyStat {
  index: number;
  key_preview: string;
  health_score: number;
  status: 'ACTIVE' | 'COOLDOWN' | 'DEAD';
}

export interface GenericAIResponse {
  status: 'success' | 'error';
  message?: string;
  count?: number;
  models?: string[];
}

// ── Phase 12: Auditor & Security Types ──
export interface AuditorAnalysis {
  risk_score: number;
  impact_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  insights: string[];
  recommendation: string;
  audited_by?: string;
}

export interface GhostCompletionResponse {
  status?: 'done' | 'processing';
  message?: string;
  token?: string;
}
export interface GenericResponse<T = any> {
  status: 'success' | 'error';
  message?: string;
  data: T;
  logs?: string[];
}
