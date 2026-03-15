import type { JwtPayload } from "$lib/types";

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
    }
    // interface PageData {}
    // interface Platform {}
  }
}

export {};
