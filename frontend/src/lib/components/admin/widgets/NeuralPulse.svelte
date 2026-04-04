<script lang="ts">
    import { onMount } from "svelte";

    let { health = 100, active = true } = $props();
    
    // Scale pulse frequency by health
    let duration = $derived(Math.max(0.5, (100 - (100 - health) * 0.8) / 20) + "s");
    let color = $derived(health > 90 ? "#10b981" : health > 70 ? "#f59e0b" : "#ef4444");
</script>

<div class="neural-pulse-container relative w-32 h-32 flex items-center justify-center">
    <!-- Outer Glow -->
    <div 
        class="absolute inset-0 rounded-full blur-2xl opacity-20 transition-colors duration-1000"
        style="background: {color}; transform: scale({active ? 1.2 : 0.8});"
    ></div>

    <!-- Core -->
    <div 
        class="relative w-16 h-16 rounded-full border-2 transition-colors duration-1000 flex items-center justify-center"
        style="border-color: {color}40; background: {color}05;"
    >
        <div 
            class="w-3 h-3 rounded-full shadow-[0_0_15px_rgba(255,255,255,0.5)]"
            style="background: {color};"
        ></div>
        
        <!-- Ripple 1 -->
        <div 
            class="absolute inset-0 rounded-full border transition-colors duration-1000 ripple-1"
            style="border-color: {color}60; animation-duration: {duration};"
        ></div>
        
        <!-- Ripple 2 -->
        <div 
            class="absolute inset-0 rounded-full border transition-colors duration-1000 ripple-2"
            style="border-color: {color}40; animation-duration: {duration}; animation-delay: 0.5s;"
        ></div>
    </div>

    <!-- Wave Indicator -->
    <svg class="absolute inset-0 w-full h-full pointer-events-none opacity-30" viewBox="0 0 100 100">
        <circle 
            cx="50" cy="50" r="48" 
            fill="none" 
            stroke={color} 
            stroke-width="0.5" 
            stroke-dasharray="1 4"
            class="animate-spin-slow"
        />
    </svg>
</div>

<style>
    .neural-pulse-container {
        filter: drop-shadow(0 0 10px rgba(0, 0, 0, 0.5));
    }

    .ripple-1, .ripple-2 {
        animation: pulse-out linear infinite;
    }

    @keyframes pulse-out {
        0% { transform: scale(1); opacity: 0.8; }
        100% { transform: scale(2.5); opacity: 0; }
    }

    .animate-spin-slow {
        animation: spin 20s linear infinite;
    }

    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
</style>
