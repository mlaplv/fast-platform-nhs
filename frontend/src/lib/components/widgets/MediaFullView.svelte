<script lang="ts">
    import { useNanobot } from '$lib/state/nanobot.svelte';
    const nanobot = useNanobot();
    let { data } = $props<{ data: { url: string; mime_type?: string; title?: string } }>();

    function close() {
        nanobot.closeUniversalModal();
    }
</script>

<div class="w-full h-full flex flex-col bg-black relative">
    <button
        onclick={close}
        class="absolute top-4 left-4 z-50 px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg text-xs font-bold backdrop-blur-md transition-all"
    >
        ← Quay lại Thư viện
    </button>
    <div class="flex-1 flex items-center justify-center p-4">
        {#if data.mime_type?.startsWith('video/')}
            <video src={data.url} controls autoplay class="max-w-full max-h-full" />
        {:else}
            <img src={data.url} alt={data.title} class="max-w-full max-h-full object-contain" />
        {/if}
    </div>
</div>
