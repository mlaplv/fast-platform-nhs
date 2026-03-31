// Utility to safely access environment variables without triggering strict TS errors in some IDEs
interface ImportMetaEnv {
    DEV: boolean;
    [key: string]: unknown;
}

interface ImportMeta {
    env: ImportMetaEnv;
}

export const isDev = (): boolean => {
    try {
        return (import.meta as unknown as ImportMeta).env?.DEV || false;
    } catch (e) {
        return false;
    }
};

export const isAdminDomain = (): boolean => {
    if (typeof window === "undefined") return false;
    const hostname = window.location.hostname;
    // Elite V2.2: Chặn triệt để Nanobot trên Storefront (*.smartshop.test)
    // Chỉ cho phép chạy trên admin.smartshop.test hoặc localhost (dev)
    return hostname.startsWith("admin.") || hostname === "localhost" || hostname === "127.0.0.1";
};
