<script lang="ts">
  import { fade, scale } from "svelte/transition";
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import Zap from "@lucide/svelte/icons/zap";
  import Cpu from "@lucide/svelte/icons/cpu";
  import Activity from "@lucide/svelte/icons/activity";

  let { adsState } = $props();

  // Elite V3.0 - PoW HUD Logic
  // This component visualizes the "Fast Path" edge mitigation.
</script>

{#if adsState.isPoWActive}
  <div 
    class="fixed inset-0 z-[9999] flex items-center justify-center pointer-events-none"
    transition:fade={{ duration: 300 }}
  >
    <!-- Liquid Glass Overlay -->
    <div class="absolute inset-0 bg-red-950/20 backdrop-blur-sm animate-pulse"></div>
    
    <div 
      class="relative bg-black/80 border border-red-500/50 rounded-2xl p-8 shadow-[0_0_50px_rgba(239,68,68,0.3)] backdrop-blur-xl w-full max-w-md mx-4"
      transition:scale={{ start: 0.9, duration: 400 }}
    >
      <!-- HUD Header -->
      <div class="flex items-center gap-4 mb-6">
        <div class="bg-red-500/20 p-3 rounded-full animate-bounce">
          <ShieldAlert class="w-8 h-8 text-red-500" />
        </div>
        <div>
          <h2 class="text-xl font-bold text-white uppercase tracking-tighter">Bot Threat Detected</h2>
          <p class="text-red-400/80 text-xs font-mono">Edge Mitigation Active: <span class="text-red-500 font-bold">FAST-PATH</span></p>
        </div>
      </div>

      <!-- Real-time Metrics -->
      <div class="space-y-4 font-mono">
        <div class="flex justify-between items-center text-sm border-b border-white/10 pb-2">
          <span class="text-gray-400 flex items-center gap-2"><Zap class="w-4 h-4 text-yellow-500" /> Latency</span>
          <span class="text-white">12.4 ms</span>
        </div>
        <div class="flex justify-between items-center text-sm border-b border-white/10 pb-2">
          <span class="text-gray-400 flex items-center gap-2"><Cpu class="w-4 h-4 text-blue-500" /> PoW Solving</span>
          <div class="w-32 h-1 bg-gray-800 rounded-full overflow-hidden">
            <div class="h-full bg-blue-500 animate-[pow-progress_2s_infinite]"></div>
          </div>
        </div>
        <div class="flex justify-between items-center text-sm">
          <span class="text-gray-400 flex items-center gap-2"><Activity class="w-4 h-4 text-green-500" /> Forensic Confidence</span>
          <span class="text-white">99.8%</span>
        </div>
      </div>

      <!-- Footer Action -->
      <div class="mt-8 text-center">
        <div class="text-[10px] text-gray-500 uppercase tracking-widest mb-2">Hardened by Agentic AI Guard</div>
        <div class="inline-flex items-center gap-2 px-4 py-1 bg-white/5 rounded-full border border-white/10">
          <span class="w-2 h-2 bg-green-500 rounded-full animate-ping"></span>
          <span class="text-[10px] text-green-500 font-bold uppercase italic">Thwarting Invalid Activity</span>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  @keyframes pow-progress {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }
</style>
