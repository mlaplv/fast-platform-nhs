import { setContext, getContext } from 'svelte';
import { BREAKPOINTS } from '$lib/constants/layout';
import type { ClientUiState, ShopInfo } from '$lib/types';

const CLIENT_UI_KEY = 'CLIENT_UI_CONTEXT';

// Elite V2.2: Reactive Global UI State (Nanobot Singleton Style)
// Refactored: Moved inside factory to prevent SSR state leakage between requests.
export function createClientUiState(): ClientUiState {
    const globalState = $state({
        isHeaderHidden: false,
        isFooterHidden: false,
        screenWidth: typeof window !== 'undefined' ? window.innerWidth : 1024,
        screenHeight: typeof window !== 'undefined' ? window.innerHeight : 768,
        isHydrated: false,
        isDetermined: false,
        settings: null as ShopInfo | null,
        authModal: {
            isOpen: false,
            mode: 'login' as 'login' | 'register' | 'profile',
            onSuccess: undefined as (() => void) | undefined,
            redirectUrl: undefined as string | undefined
        },
        confirmModal: null as {
            title: string;
            message: string;
            confirmLabel: string;
            cancelLabel: string;
            onConfirm: () => void;
            onCancel: () => void;
        } | null,
        reportModal: null as {
            reviewId: string;
            onSuccess?: () => void;
        } | null,
        toasts: [] as { id: string; message: string; type: 'success' | 'error' | 'info' | 'warning'; duration: number }[]
    });

    // Derived $mq (Media Query) Runes - Performance Optimized
    const isMobile = $derived(globalState.isDetermined && globalState.screenWidth < BREAKPOINTS.MOBILE);
    const isTablet = $derived(globalState.isDetermined && globalState.screenWidth >= BREAKPOINTS.MOBILE && globalState.screenWidth < BREAKPOINTS.TABLET);
    const isDesktop = $derived(globalState.isDetermined && globalState.screenWidth >= BREAKPOINTS.TABLET);
    const isPortrait = $derived(globalState.screenWidth < globalState.screenHeight);

    let resizeTimer: ReturnType<typeof setTimeout>;

    function handleResize() {
        if (typeof window === 'undefined') return;
        if (resizeTimer) clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            globalState.screenWidth = window.innerWidth;
            globalState.screenHeight = window.innerHeight;
        }, 250);
    }

    const instance: ClientUiState = {
        get isHeaderHidden() { return globalState.isHeaderHidden; },
        set isHeaderHidden(val: boolean) { globalState.isHeaderHidden = val; },

        get isFooterHidden() { return globalState.isFooterHidden; },
        set isFooterHidden(val: boolean) { globalState.isFooterHidden = val; },
        
        get isHydrated() { return globalState.isHydrated; },
        get isDetermined() { return globalState.isDetermined; },
        get settings() { return globalState.settings; },
        set settings(val: ShopInfo | null) { 
            if (JSON.stringify(globalState.settings) === JSON.stringify(val)) return;
            globalState.settings = val; 
        },

        get authModal() { return globalState.authModal; },
        get confirmModal() { return globalState.confirmModal; },
        get reportModal() { return globalState.reportModal; },
        get toasts() { return globalState.toasts; },

        get isMobile() { return isMobile; },
        get isTablet() { return isTablet; },
        get isDesktop() { return isDesktop; },
        get isPortrait() { return isPortrait; },

        openLogin(onSuccess?: () => void, redirectUrl?: string) {
            globalState.authModal.mode = 'login';
            globalState.authModal.onSuccess = onSuccess;
            globalState.authModal.redirectUrl = redirectUrl;
            globalState.authModal.isOpen = true;
        },

        openRegister(onSuccess?: () => void, redirectUrl?: string) {
            globalState.authModal.mode = 'register';
            globalState.authModal.onSuccess = onSuccess;
            globalState.authModal.redirectUrl = redirectUrl;
            globalState.authModal.isOpen = true;
        },

        openProfile() {
            globalState.authModal.mode = 'profile';
            globalState.authModal.isOpen = true;
        },

        openAddress() {
            globalState.authModal.mode = 'address';
            globalState.authModal.isOpen = true;
        },

        openPassword() {
            globalState.authModal.mode = 'password';
            globalState.authModal.isOpen = true;
        },

        openPurchase() {
            globalState.authModal.mode = 'purchase';
            globalState.authModal.isOpen = true;
        },

        openConfirm(options: { title: string; message: string; confirmLabel?: string; cancelLabel?: string }): Promise<boolean> {
            return new Promise((resolve) => {
                globalState.confirmModal = {
                    title: options.title,
                    message: options.message,
                    confirmLabel: options.confirmLabel || 'XÁC NHẬN',
                    cancelLabel: options.cancelLabel || 'HỦY',
                    onConfirm: () => {
                        globalState.confirmModal = null;
                        resolve(true);
                    },
                    onCancel: () => {
                        globalState.confirmModal = null;
                        resolve(false);
                    }
                };
            });
        },

        openReportReview(reviewId: string, onSuccess?: () => void) {
            globalState.reportModal = { reviewId, onSuccess };
        },

        closeReportModal() {
            globalState.reportModal = null;
        },

        closeModal() {
            globalState.authModal.isOpen = false;
        },

        initObservers() {
            if (typeof window === 'undefined') return () => {};
            if (globalState.isDetermined && globalState.isHydrated) return () => {};

            globalState.screenWidth = window.innerWidth;
            globalState.screenHeight = window.innerHeight;
            globalState.isDetermined = true;
            globalState.isHydrated = true;

            window.addEventListener('resize', handleResize, { passive: true });
            return () => {
                window.removeEventListener('resize', handleResize);
            };
        },

        forceMobile(mobile: boolean) {
            globalState.screenWidth = mobile ? 375 : 1440;
            globalState.isDetermined = true;
        },

        showToast(message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info', duration = 4000) {
            const id = Math.random().toString(36).substring(2, 9);
            globalState.toasts = [...globalState.toasts, { id, message, type, duration }];
            
            import('$lib/state/notification.svelte').then(({ getNotificationState }) => {
                const notif = getNotificationState();
                const recentNotifs = notif.notifications.slice(0, 5);
                const isDuplicate = recentNotifs.some(n => n.message === message);
                if (isDuplicate) return;

                notif.addPendingSignal({
                    id,
                    message,
                    severity: type.toUpperCase() as "CRITICAL" | "ACTION" | "PROGRESS" | "INFO",
                    isRead: false
                });
            }).catch(e => console.error("[UI] Pulse sync failed", e));

            setTimeout(() => {
                globalState.toasts = globalState.toasts.filter(t => t.id !== id);
            }, duration);
        }
    };

    return instance;
}

let _globalUiInstance: ClientUiState | null = null;

export function setClientUi() {
    // Elite V2.2: Context-first initialization
    const state = createClientUiState();
    // Maintain a volatile singleton for edge cases, but prefer Context
    if (typeof window !== 'undefined') _globalUiInstance = state;
    return setContext(CLIENT_UI_KEY, state);
}

export function getClientUi(): ClientUiState {
    try {
        const state = getContext(CLIENT_UI_KEY) as ClientUiState;
        if (state) return state;
    } catch (e) {}
    
    if (typeof window !== 'undefined' && _globalUiInstance) return _globalUiInstance;
    
    // Fallback: This creates a per-call instance if no context exists (e.g. background tasks)
    return createClientUiState();
}
