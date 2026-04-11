import { setContext, getContext } from 'svelte';
import type { ClientUiState } from '$lib/types';
import { BREAKPOINTS } from '$lib/constants/layout';

export function createClientUiState(): ClientUiState {
    const state = $state({
        isHeaderHidden: false,
        isFooterHidden: false,
        // Elite V2.2: Reactive Screen Runes
        screenWidth: typeof window !== 'undefined' ? window.innerWidth : 1024,
        screenHeight: typeof window !== 'undefined' ? window.innerHeight : 768,
        isHydrated: false,
        settings: null
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
        
        // Screen Getters (Statically Typed 100%)
        get screenWidth() { return state.screenWidth; },
        get screenHeight() { return state.screenHeight; },
        get isMobile() { return isMobile; },
        get isTablet() { return isTablet; },
        get isDesktop() { return isDesktop; },
        get isPortrait() { return isPortrait; },
        get isHydrated() { return state.isHydrated; },
        get settings() { return state.settings; },
        set settings(val: any) { state.settings = val; },

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
