import { setContext, getContext } from 'svelte';
import type { ClientUiState, ShopInfo } from '$lib/types';
import { BREAKPOINTS } from '$lib/constants/layout';

// Elite V2.2: Global Auth Modal State (Nanobot Singleton)
// This ensures reactivity even if context scoping is fragmented across chunks.
const globalAuthModal = $state({
    isOpen: false,
    mode: 'login' as 'login' | 'register',
    onSuccess: undefined as (() => void) | undefined
});

export function createClientUiState(): ClientUiState {
    const state = $state({
        isHeaderHidden: false,
        isFooterHidden: false,
        // Elite V2.2: Reactive Screen Runes
        screenWidth: typeof window !== 'undefined' ? window.innerWidth : 1024,
        screenHeight: typeof window !== 'undefined' ? window.innerHeight : 768,
        isHydrated: false,
        settings: null as ShopInfo | null
    });

    // Derived $mq (Media Query) Runes - No Hardcoding (R00)
    const isMobile = $derived(state.screenWidth < BREAKPOINTS.MOBILE);
    const isTablet = $derived(state.screenWidth >= BREAKPOINTS.MOBILE && state.screenWidth < BREAKPOINTS.TABLET);
    const isDesktop = $derived(state.screenWidth >= BREAKPOINTS.TABLET);
    const isPortrait = $derived(state.screenWidth < state.screenHeight);

    function handleResize() {
        if (typeof window === 'undefined') return;
        state.screenWidth = window.innerWidth;
        state.screenHeight = window.innerHeight;
    }

    return {
        get isHeaderHidden() { return state.isHeaderHidden; },
        set isHeaderHidden(val: boolean) { state.isHeaderHidden = val; },

        get isFooterHidden() { return state.isFooterHidden; },
        set isFooterHidden(val: boolean) { state.isFooterHidden = val; },
        
        // Elite V2.2: Auth Modal Controls (Global Singleton Hook)
        get authModal() { return globalAuthModal; },
        openLogin(onSuccess?: () => void) {
            console.log("[Global-UI] Opening Login Modal");
            globalAuthModal.mode = 'login';
            globalAuthModal.onSuccess = onSuccess;
            globalAuthModal.isOpen = true;
        },
        openRegister(onSuccess?: () => void) {
            console.log("[Global-UI] Opening Register Modal");
            globalAuthModal.mode = 'register';
            globalAuthModal.onSuccess = onSuccess;
            globalAuthModal.isOpen = true;
        },
        closeModal() {
            console.log("[Global-UI] Closing Modal");
            globalAuthModal.isOpen = false;
        },
        
        // Screen Getters (Statically Typed 100%)
        get screenWidth() { return state.screenWidth; },
        get screenHeight() { return state.screenHeight; },
        get isMobile() { return isMobile; },
        get isTablet() { return isTablet; },
        get isDesktop() { return isDesktop; },
        get isPortrait() { return isPortrait; },
        get isHydrated() { return state.isHydrated; },
        get settings() { return state.settings; },
        set settings(val: ShopInfo | null) { state.settings = val; },

        initObservers() {
            if (typeof window === 'undefined' || state.isHydrated) return;
            
            state.isHydrated = true;
            handleResize();
            window.addEventListener('resize', handleResize, { passive: true });
            
            return () => {
                window.removeEventListener('resize', handleResize);
            };
        }
    };
}

const CLIENT_UI_KEY = Symbol('CLIENT_UI');

export function setClientUi() {
    return setContext(CLIENT_UI_KEY, createClientUiState());
}

export function getClientUi(): ReturnType<typeof createClientUiState> {
    return getContext(CLIENT_UI_KEY);
}
