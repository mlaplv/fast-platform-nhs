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
