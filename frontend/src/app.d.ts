

declare global {
  namespace App {
    interface Locals {
      user?: {
        id?: string;
        name?: string;
        email: string;
        role: string | null;
        roles: string[];
        perms: string[];
      };
      token?: string;
      tenant: "admin" | "storefront" | "default";
      isMobile: boolean;
      // V2026: Identity Snapshot
      customer_context?: {
          is_recurring: boolean;
          is_trusted: boolean;
      };
    }
    // interface PageData {}
    // interface Platform {}
    interface Error {
      message: string;
      details?: string;
      stack?: string;
    }
  }

  // Elite V2026: Facebook SDK type (loaded via app.html)
  interface Window {
    FB: {
      ui(
        params: {
          method: string;
          href?: string;
          display?: string;
          [key: string]: unknown;
        },
        callback?: (response: { post_id?: string; error_message?: string } | null) => void
      ): void;
      init(params: { appId: string; version: string; [key: string]: unknown }): void;
    };
    fbq: (...args: unknown[]) => void;
  }
}

export {};
