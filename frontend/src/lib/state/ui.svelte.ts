import { safeRandomUUID } from "./utils";
import { type ConfirmDialog, type Toast, type ToastType } from "./types";

export function createUiState() {
  const state = $state({
    confirmDialog: null as ConfirmDialog | null,
    toasts: [] as Toast[],
    universalModalOpen: false,
    activeHudPopup: null as string | null,
    showQuickTips: false,
    heartbeatCollapsed: typeof window !== "undefined" 
      ? (localStorage.getItem("xohi_heartbeat_collapsed") !== null 
          ? localStorage.getItem("xohi_heartbeat_collapsed") === "true" 
          : true)
      : null,
  });

  function showConfirm(
    options: Omit<ConfirmDialog, "onConfirm" | "onCancel"> & { isPrompt: true },
  ): Promise<string | null>;
  function showConfirm(
    options: Omit<ConfirmDialog, "onConfirm" | "onCancel"> & {
      fields: import("./types").FormField[];
    },
  ): Promise<Record<string, string> | null>;
  function showConfirm(
    options: Omit<ConfirmDialog, "onConfirm" | "onCancel"> & {
      isPrompt?: false;
    },
  ): Promise<boolean>;
  function showConfirm(
    options: Omit<ConfirmDialog, "onConfirm" | "onCancel">,
  ): Promise<boolean | string | Record<string, string> | null> {
    return new Promise((resolve) => {
      state.confirmDialog = {
        ...options,
        onConfirm: (value?: string | Record<string, string>) => {
          state.confirmDialog = null;
          if (options.fields && options.fields.length > 0) {
            resolve(value ?? null);
          } else if (options.isPrompt) {
            resolve(typeof value === "string" ? value : "");
          } else {
            resolve(true);
          }
        },
        onCancel: () => {
          state.confirmDialog = null;
          if (options.fields && options.fields.length > 0) {
            resolve(null);
          } else if (options.isPrompt) {
            resolve(null);
          } else {
            resolve(false);
          }
        },
      };
    });
  }

  function showToast(
    message: string,
    type: ToastType = "info",
    duration: number = 4000,
  ) {
    const id = safeRandomUUID();
    const newToast: Toast = { id, message, type, duration };
    state.toasts = [...state.toasts, newToast];

    setTimeout(() => {
      state.toasts = state.toasts.filter((t: Toast) => t.id !== id);
    }, duration);
  }

  function removeToast(id: string) {
    state.toasts = state.toasts.filter((t: Toast) => t.id !== id);
  }

  return {
    get confirmDialog() {
      return state.confirmDialog;
    },
    get toasts() {
      return state.toasts;
    },
    get universalModalOpen() {
      return state.universalModalOpen;
    },

    setUniversalModalOpen(val: boolean) {
      state.universalModalOpen = val;
    },
    get activeHudPopup() {
      return state.activeHudPopup;
    },
    set activeHudPopup(val: string | null) {
      state.activeHudPopup = val;
    },
    get showQuickTips() {
      return state.showQuickTips;
    },
    set showQuickTips(val: boolean) {
      state.showQuickTips = val;
    },
    get heartbeatCollapsed() {
      return state.heartbeatCollapsed;
    },
    set heartbeatCollapsed(val: boolean | null) {
      state.heartbeatCollapsed = val;
      if (typeof window !== "undefined") {
        if (val === null) {
          localStorage.removeItem("xohi_heartbeat_collapsed");
        } else {
          localStorage.setItem("xohi_heartbeat_collapsed", String(val));
        }
      }
    },
    showConfirm,
    showToast,
    removeToast,
  };
}
