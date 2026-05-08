<script lang="ts">
  import { onMount } from "svelte";
  import Brain from "@lucide/svelte/icons/brain";

  interface Capability {
    id: string;
    active: boolean;
    name: string;
    desc: string;
  }

  let { 
    capabilities = $bindable() 
  } = $props<{
    capabilities: Capability[];
  }>();

  onMount(() => {
    if (capabilities === undefined) capabilities = [];
  });

  function toggleCapability(id: string) {
    const cap = capabilities.find((c) => c.id === id);
    if (cap) cap.active = !cap.active;
  }
</script>

<section>
  <div class="flex items-center gap-3 text-zinc-400 mb-8 px-2">
    <Brain size={20} class="text-amber-500/80" />
    <h2 class="text-xs font-mono font-bold uppercase tracking-[0.3em]">
      Neural Modules
    </h2>
  </div>
  
  <div class="space-y-3">
    {#each capabilities as cap}
      <button
        onclick={() => toggleCapability(cap.id)}
        class="w-full group p-5 bg-white/5 hover:bg-white/10 border border-white/5 rounded-2xl text-left transition-all duration-300 active:scale-[0.98] flex flex-col gap-3"
      >
        <div class="flex items-center justify-between">
          <span class="text-[10px] font-mono font-bold text-zinc-500 uppercase tracking-widest group-hover:text-amber-500/80 transition-colors">
            {cap.id}
          </span>
          
          <!-- CUSTOM TOGGLE SWITCH -->
          <div class="w-10 h-5 bg-zinc-900 rounded-full border border-white/10 relative transition-colors {cap.active ? 'bg-amber-500/20 border-amber-500/30' : ''}">
            <div class="absolute top-1 bottom-1 w-3 h-3 rounded-full transition-all duration-300 {cap.active ? 'bg-amber-400 left-6 shadow-[0_0_10px_rgba(251,191,36,0.5)]' : 'bg-zinc-700 left-1'}"></div>
          </div>
        </div>

        <div>
          <h3 class="text-sm font-bold text-zinc-200 uppercase tracking-tight mb-1 group-hover:text-white transition-colors">
            {cap.name}
          </h3>
          <p class="text-[10px] text-zinc-500 leading-relaxed font-sans">
            {cap.desc}
          </p>
        </div>
      </button>
    {/each}
  </div>
</section>
