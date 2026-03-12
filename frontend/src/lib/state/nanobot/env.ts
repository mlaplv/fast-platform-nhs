// Utility to safely access environment variables without triggering strict TS errors in some IDEs
export const isDev = () => {
    try {
        return (import.meta as any).env?.DEV || false;
    } catch (e) {
        return false;
    }
};
