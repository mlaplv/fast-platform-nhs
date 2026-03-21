<script lang="ts">
    import { nanobot } from "$lib/state/nanobot.svelte";
    import FileManager from "./FileManager.svelte";
    import { fade } from "svelte/transition";

    function close() {
        nanobot.closeUniversalModal();
    }
</script>

<div
    class="fixed inset-0 flex flex-col pointer-events-auto overflow-hidden bg-[#0a0c12]/98 backdrop-blur-2xl"
    style="z-index: 99999;"
    transition:fade={{ duration: 250 }}
>
    <!-- Liquid Glass ambient glow -->
    <div class="absolute inset-0 z-0 pointer-events-none overflow-hidden opacity-30">
        <div class="absolute top-[-20%] right-[-10%] w-[60%] h-[60%] bg-[radial-gradient(circle_at_50%_50%,rgba(99,102,241,0.06),transparent_60%)]"></div>
        <div class="absolute bottom-[-20%] left-[-10%] w-[60%] h-[60%] bg-[radial-gradient(circle_at_50%_50%,rgba(99,102,241,0.04),transparent_60%)]"></div>
    </div>

    <!-- Main Content Area — full bleed, no wrapper chrome -->
    <div class="relative z-10 flex-1 overflow-hidden">
        <div class="w-full h-full flex flex-col">
            <FileManager standalone={true} onPickClose={close} />
        </div>
    </div>
</div>
