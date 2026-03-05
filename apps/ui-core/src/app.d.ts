// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
  namespace App {
    // interface Error {}
    interface Locals {
      tenant: "admin" | "storefront";
      isMobile: boolean;
      user?: {
        email: string;
        role: string;
        roles?: string[];
        perms?: string[];
      };
      token?: string;
    }
    // interface PageData {}
    // interface PageState {}
    // interface Platform {}
  }

  // Vite `define` injected globals
  const __APP_VERSIONS__: {
    svelte: string;
    tailwind: string;
    sqlalchemy: string;
    alembic: string;
    litestar: string;
    pydantic_ai: string;
    litellm: string;
    prisma: string;
    python: string;
    caddy: string;
  };
}

export {};
