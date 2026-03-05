export interface SystemLog {
  id: string;
  timestamp: Date;
  message: string;
  source: string;
  type?: string;
  routerTier?: number;
}

export interface Notification {
  id: string;
  type: string;
  message: string;
  isRead: boolean;
  createdAt: string;
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
  | "VOICE_SETTINGS";

export type NanoBotState =
  | "IDLE"
  | "THINKING"
  | "PROCESSING"
  | "ERROR"
  | "SUCCESS"
  | "VOICE";

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
  | "view";

export type CommandEntity =
  | "category"
  | "product"
  | "order"
  | "news"
  | "user"
  | "permission";

export interface CommandAction {
  verb: CommandVerb;
  entity: CommandEntity;
  args?: string;
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
