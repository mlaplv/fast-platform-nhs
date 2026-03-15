<script lang="ts">
    import { fade, scale } from 'svelte/transition';
    import FileManager from './FileManager.svelte';
    import type { MediaAsset } from '$lib/types';

    interface Props {
        show: boolean;
        campaignId?: string;
        onClose: () => void;
        onSelect?: (asset: MediaAsset) => void;
    }

    let { show = $bindable(), campaignId, onClose, onSelect } = $props<Props>();

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Escape') onClose();
    }
</script>

{#if show}
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <div
        class="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-8 bg-black/80 backdrop-blur-sm"
        onclick={onClose}
        transition:fade={{ duration: 200 }}
        role="dialog"
    >
        <div
            class="relative w-full max-w-6xl h-[85vh] bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl overflow-hidden flex flex-col"
            onclick={(e) => e.stopPropagation()}
            transition:scale={{ start: 0.95, duration: 200 }}
        >
            <!-- Close Button -->
            <button
                onclick={onClose}
                class="absolute top-4 right-4 z-[110] p-2 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-full transition-colors text-zinc-500"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>

            <div class="flex-1 overflow-hidden">
                <FileManager {campaignId} {onSelect} standalone={true} />
            </div>
        </div>
    </div>
{/if}
