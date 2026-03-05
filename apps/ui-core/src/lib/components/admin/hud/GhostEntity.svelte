<script lang="ts">
    import { omni } from "$lib/state/omni.svelte";
    import { nanobot } from "$lib/state/nanobot.svelte";

    let { isGhostSpeaking, rec, vol } = $props<{
        isGhostSpeaking: boolean;
        rec: boolean;
        vol: number;
    }>();

    function setOrb(node: HTMLDivElement) {
        omni.orbElement = node;
    }
</script>

<div class="relative w-[600px] h-[600px] flex items-center justify-center transform translate-x-[50%] -translate-y-[50%] transition-opacity duration-1000 {isGhostSpeaking || rec ? 'opacity-100' : 'opacity-60'}">
    
    <!-- DATA RESONANCE WAVES (Corner outwards) -->
    {#if rec || isGhostSpeaking}
        {#each Array(3) as _, i}
            <div class="absolute inset-0 rounded-full border border-cyan-400/20 animate-[vuiPing_3s_infinite] transform-gpu vui-ping-wave-{i}"></div>
        {/each}
    {/if}

    <!-- AMBIENT NEURAL GLOW (Optimized) -->
    <div class="absolute inset-0 rounded-full blur-[100px] opacity-20 pointer-events-none transition-colors duration-1000 transform-gpu
        {isGhostSpeaking ? 'bg-indigo-600' : rec ? 'bg-cyan-500' : 'bg-gray-800'}"></div>
    
    <!-- NEURAL RINGS (Floating Layers) -->
    <div class="absolute w-[480px] h-[480px] rounded-full border border-white/5 animate-[spin_20s_linear_infinite] opacity-40 transform-gpu"></div>
    <div class="absolute w-[420px] h-[420px] rounded-full border-[0.5px] border-dashed border-cyan-400/20 animate-[spin_15s_linear_infinite_reverse] transform-gpu"></div>

    <!-- THE ENTITY CORE -->
    <div use:setOrb class="relative w-[360px] h-[360px] rounded-full border border-white/20 bg-gradient-to-tr from-black to-transparent shadow-[0_0_120px_rgba(0,0,0,0.9)] flex items-center justify-center overflow-hidden transition-transform duration-75 ease-out will-change-transform transform-gpu">
        
        <!-- INNER NEURAL PATTERN -->
        <div class="absolute inset-0 opacity-30 transform-gpu animate-[vuiBreath_8s_easeInOutSine_infinite]">
            <div class="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_30%,rgba(34,211,238,0.1)_70%)]"></div>
            <div class="absolute inset-0 bg-[repeating-conic-gradient(from_0deg,transparent_0deg_20deg,rgba(255,255,255,0.02)_21deg_25deg)]"></div>
        </div>

        <!-- BRAIN PULSE -->
        <div class="w-32 h-32 rounded-full blur-3xl transition-all duration-700 transform-gpu
            {isGhostSpeaking ? 'bg-indigo-400/40 scale-125' : rec ? 'bg-cyan-400/40 scale-110' : 'bg-white/5 scale-100' }"></div>
        
        {#if rec && !isGhostSpeaking}
            <div class="absolute inset-16 rounded-full border-2 border-cyan-400/30 animate-ping transform-gpu"></div>
        {/if}
    </div>
</div>

<style>
    @keyframes vuiPing { 
        0% { transform: scale(1); opacity: 0.5; }
        100% { transform: scale(3); opacity: 0; }
    }
    @keyframes vuiBreath {
        0%, 100% { transform: scale(1); opacity: 0.3; }
        50% { transform: scale(1.1); opacity: 0.5; }
    }

    .vui-ping-wave-1 { animation-delay: 1s; }
    .vui-ping-wave-2 { animation-delay: 2s; }
</style>
