/**
 * Configuration for the AI Support Agent interface
 * Following Elite V2.2 Standards
 */
export const SUPPORT_AGENT_UI = {
  // Threshold in pixels to shrink the FAB
  SCROLL_SHRINK_THRESHOLD: 100,

  // Mobile layout spacing
  MOBILE_FAB_BOTTOM: '120px',
  MOBILE_FAB_RIGHT: '20px',

  // Desktop layout spacing
  DESKTOP_FAB_BOTTOM: '32px',
  DESKTOP_FAB_RIGHT: '32px',

  // Animation durations
  TRANSITION_MS: 500,
  MORPH_MS: 6000,
} as const;
