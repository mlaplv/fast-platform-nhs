<script lang="ts">
    import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();

  async function toggleCampaignMode() {
    await nanobot.toggleCampaignMode();
  }
</script>

<section class="mt-auto">
  <div class="flex items-center gap-3 text-red-500/60 mb-8 px-2">
    <ShieldAlert size={20} />
    <h2 class="text-xs font-mono font-bold tracking-[0.3em]">
      Security Grid
    </h2>
  </div>
  
  <button
    onclick={toggleCampaignMode}
    disabled={nanobot.isTogglingCampaign}
    class="w-full group p-6 bg-black/40 backdrop-blur-md border transition-all duration-500 rounded-3xl active:scale-95 flex flex-col gap-4 {nanobot.isCampaignMode
      ? 'border-red-500/40 shadow-[0_0_40px_rgba(239,68,68,0.15)] bg-red-500/5'
      : 'border-white/5 grayscale opacity-50 hover:grayscale-0 hover:opacity-100 hover:bg-white/5'}"
  >
    <div class="flex items-center justify-between">
      <span class="text-xs font-mono font-bold tracking-widest {nanobot.isCampaignMode ? 'text-red-400' : 'text-zinc-500'}">
        Fortress Mode
      </span>
      
      <div class="w-12 h-6 bg-zinc-900 rounded-full border border-white/10 relative">
        {#if nanobot.isTogglingCampaign}
          <div class="absolute inset-0 flex items-center justify-center">
            <RefreshCw size={12} class="animate-spin text-red-400" />
          </div>
        {:else}
          <div class="absolute top-1 bottom-1 w-4 h-4 rounded-full transition-all duration-500 {nanobot.isCampaignMode ? 'bg-red-500 left-7 shadow-[0_0_15px_rgba(239,68,68,0.6)]' : 'bg-zinc-700 left-1'}"></div>
        {/if}
      </div>
    </div>
    
    <p class="text-[10px] font-mono text-zinc-600 leading-relaxed tracking-wider">
      Engagement Restricted: <br/>
      <span class={nanobot.isCampaignMode ? 'text-red-400/80' : ''}>Anti-Spam Shield {nanobot.isCampaignMode ? 'Active' : 'Standby'}</span>
    </p>
  </button>
</section>
