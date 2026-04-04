<script lang="ts">
    import { onMount } from 'svelte';
    import { fade } from 'svelte/transition';
    import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
    import Activity from "lucide-svelte/icons/activity";
    import Zap from "lucide-svelte/icons/zap";
    import ShieldAlert from "lucide-svelte/icons/shield-alert";
    import Brain from "lucide-svelte/icons/brain";
    import ChevronRight from "lucide-svelte/icons/chevron-right";

    let status = $state(null);
    let loading = $state(true);

    onMount(async () => {
        await loadStatus();
    });

    async function loadStatus() {
        try {
            const res = await fetch('/api/v1/admin/ai/brain/status');
            if (res.ok) status = await res.json();
        } catch (e) {
            console.error('BrainHealth poll failed:', e);
        } finally {
            loading = false;
        }
    }

    function openBrain() {
        nanobot.openWidget("BRAIN_MANAGEMENT");
    }
</script>

<div 
  class="relative group overflow-hidden bg-[#0a0a0a]/80 backdrop-blur-3xl border border-white/5 rounded-[2.5rem] p-8 transition-all duration-700 hover:border-indigo-500/30"
  in:fade={{ duration: 1000, delay: 200 }}
>
  <!-- Background Aura -->
  <div class="absolute -bottom-20 -left-20 w-64 h-64 bg-indigo-500/10 blur-[100px] rounded-full group-hover:bg-indigo-500/20 transition-all duration-1000"></div>
  
  <div class="relative z-10">
    <div class="flex items-center justify-between mb-8">
      <div class="flex items-center gap-4">
        <div class="p-3 bg-white/5 rounded-2xl border border-white/10 group-hover:border-indigo-500/50 transition-colors">
          <Brain size={24} class="text-white group-hover:text-indigo-400 transition-colors" />
        </div>
        <div>
          <h2 class="text-xl font-black tracking-tighter text-white uppercase italic">Neural Health HUD</h2>
          <p class="text-[10px] font-mono text-gray-500 tracking-[0.3em] uppercase">Intelligence Vectoring V2.2</p>
        </div>
      </div>
      
      <button 
        onclick={openBrain}
        class="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all group/btn"
      >
        <span class="text-[10px] font-black uppercase tracking-widest text-gray-400 group-hover/btn:text-white">Audit Hub</span>
        <ChevronRight size={14} class="text-gray-600 group-hover/btn:text-white group-hover/btn:translate-x-0.5 transition-all" />
      </button>
    </div>

    {#if loading}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 opacity-20">
            {#each Array(3) as _}
                <div class="h-24 bg-white/5 rounded-3xl animate-pulse"></div>
            {/each}
        </div>
    {:else if status}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Nodes -->
            <div class="relative p-6 rounded-3xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] transition-all">
                <div class="flex justify-between items-start mb-4">
                    <Activity size={16} class="text-indigo-400" />
                    <span class="text-[9px] font-mono text-gray-600 uppercase tracking-widest">Knowledge</span>
                </div>
                <div class="text-3xl font-black text-white tracking-tighter mb-1">{status.total_nodes}</div>
                <div class="text-[10px] font-mono text-gray-500 uppercase tracking-widest">Active Units</div>
            </div>

            <!-- Health -->
            <div class="relative p-6 rounded-3xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] transition-all">
                <div class="flex justify-between items-start mb-4">
                    <Zap size={16} class="text-emerald-400" />
                    <span class="text-[9px] font-mono text-gray-600 uppercase tracking-widest">Vector Core</span>
                </div>
                <div class="text-3xl font-black text-emerald-400 tracking-tighter mb-1">{status.vector_health}%</div>
                <div class="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                    <div class="h-full bg-emerald-500" style="width: {status.vector_health}%"></div>
                </div>
            </div>

            <!-- Conflicts -->
            <div class="relative p-6 rounded-3xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] transition-all">
                <div class="flex justify-between items-start mb-4">
                    <ShieldAlert size={16} class={status.duplicates.length > 0 ? 'text-amber-500' : 'text-blue-500'} />
                    <span class="text-[9px] font-mono text-gray-600 uppercase tracking-widest">Synapses</span>
                </div>
                <div class="text-3xl font-black tracking-tighter mb-1 {status.duplicates.length > 0 ? 'text-amber-500' : 'text-blue-500'}">
                    {status.duplicates.length}
                </div>
                <div class="text-[10px] font-mono text-gray-500 uppercase tracking-widest">Conflicts Detected</div>
            </div>
        </div>
    {/if}
  </div>
</div>
