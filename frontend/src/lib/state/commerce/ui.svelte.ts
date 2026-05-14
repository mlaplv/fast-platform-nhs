import { setContext, getContext } from 'svelte';
import { BREAKPOINTS } from '$lib/constants/layout';
import type { ClientUiState, ShopInfo } from '$lib/types';

const CLIENT_UI_KEY = 'CLIENT_UI_CONTEXT';

// Elite V2.2: Reactive Global UI State (Nanobot Singleton Style)
// Protected by $state for absolute reactivity across chunks.
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
        onSuccess: undefined as (() => void) | undefined
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

let _globalUiInstance: ClientUiState | null = null;

export function createClientUiState(): ClientUiState {
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
            // Elite V2.2: Redundancy Guard - prevent double updates during hydration/navigation
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

        openLogin(onSuccess?: () => void) {
            globalState.authModal.mode = 'login';
            globalState.authModal.onSuccess = onSuccess;
            globalState.authModal.isOpen = true;
        },

        openRegister(onSuccess?: () => void) {
            globalState.authModal.mode = 'register';
            globalState.authModal.onSuccess = onSuccess;
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
            globalState.reportModal = {
                reviewId,
                onSuccess
            };
        },

        closeReportModal() {
            globalState.reportModal = null;
        },

        closeModal() {
            globalState.authModal.isOpen = false;
        },

        initObservers() {
            if (typeof window === 'undefined') return () => {};
            
            // Elite V2.2: Redundancy Guard - prevent multiple resize listeners
            if (globalState.isDetermined) return () => {};

            // Elite V2.2: Immediate determination
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
            // Rule 2.2: Force state for zero-hydration performance
            globalState.screenWidth = mobile ? 375 : 1440;
            globalState.isDetermined = true;
        },

        showToast(message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info', duration = 4000) {
            const id = Math.random().toString(36).substring(2, 9);
            globalState.toasts = [...globalState.toasts, { id, message, type, duration }];
            
            // Elite V3.0: Bridge to Pulse Bell
            import('$lib/state/notification.svelte').then(({ getNotificationState }) => {
                const notif = getNotificationState();
                
                // CNS V88.2: Hard Duplicate Check - Prevent visual stacking
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

export function setClientUi() {
    const state = createClientUiState();
    _globalUiInstance = state;
    return setContext(CLIENT_UI_KEY, state);
}

export function getClientUi(): ClientUiState {
    try {
        const state = getContext(CLIENT_UI_KEY) as ClientUiState;
        if (state) return state;
    } catch (e) {
        // Suppress lifecycle error
    }
    if (_globalUiInstance) return _globalUiInstance;
    
    // Fail-safe: Create a volatile instance if everything else fails (should not happen in Elite V2.2)
    return createClientUiState();
}
