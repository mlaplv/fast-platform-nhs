import { setContext, getContext } from 'svelte';

export function createClientUiState() {
    const state = $state({
        isFooterHidden: false
    });

    return {
        get isFooterHidden() { return state.isFooterHidden; },
        set isFooterHidden(val: boolean) { state.isFooterHidden = val; }
    };
}

const CLIENT_UI_KEY = Symbol('CLIENT_UI');

export function setClientUi() {
    return setContext(CLIENT_UI_KEY, createClientUiState());
}

export function getClientUi(): ReturnType<typeof createClientUiState> {
    return getContext(CLIENT_UI_KEY);
}
