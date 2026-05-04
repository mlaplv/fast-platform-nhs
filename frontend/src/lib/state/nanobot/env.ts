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

    // Elite V2.2: Context Isolation
    // Logic: Strictly requires 'admin.' prefix OR local dev host
    // Chặn triệt để Nanobot trên Storefront (osmo)
    const isLocal = hostname === "localhost" || hostname === "127.0.0.1" || hostname.startsWith("192.168.");
    const hasAdminSubdomain = hostname.startsWith("admin.");

    return hasAdminSubdomain || isLocal;
};
