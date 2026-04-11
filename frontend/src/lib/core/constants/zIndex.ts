export const Z_INDEX_CLIENT = {
  BASE: 0,
  WAVE: 1,
  SURFACE: 10,
  CONTENT: 20,
  POPUP: 50,
  HEADER: 100,
  MOBILE_TAB_BAR: 100,
  OVERLAY: 500,
  MOBILE_BOTTOM_SHEET_OVERLAY: 500,
  MODAL: 1000,
  MOBILE_BOTTOM_SHEET: 1000,
  FAB: 400,
  MOBILE_REVIEW_OVERLAY: 1200,
  TOAST: 2000,
  MOBILE_REVIEW_HEADER: 2000,
} as const;

export const Z_INDEX_ADMIN = {
  HUD: 10000,             // Info labels and hover frames
  BACKDROP: 1000000,      // Global masking layer
  EDITOR: 1000001,        // Inline text/html editors
  PICKER: 100000,         // Media picker backdrop
  PICKER_BOX: 100001,     // Media picker UI
  TOAST: 2000000,         // System notifications (Topmost)
} as const;
