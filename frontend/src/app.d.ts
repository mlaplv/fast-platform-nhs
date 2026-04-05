

declare global {
  namespace App {
    interface Locals {
      user?: {
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
}

export {};
