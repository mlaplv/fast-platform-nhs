<script lang="ts">
  import { onMount } from "svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { fade, scale } from "svelte/transition";
  import X from "lucide-svelte/icons/x";
  import Activity from "lucide-svelte/icons/activity";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import ShieldCheck from "lucide-svelte/icons/shield-check";
  import AlertTriangle from "lucide-svelte/icons/alert-triangle";
  import Skull from "lucide-svelte/icons/skull";

  let { show = false, onClose } = $props<{
    show?: boolean;
    onClose: () => void;
  }>();

  let keyStats = $state<any[]>([]);
  let isLoading = $state(false);
  let testingIndex = $state<number | null>(null);

  async function fetchStats() {
    isLoading = true;
    try {
      const res = await apiClient.get<any[]>("/api/v1/admin/ai/keys");
      if (Array.isArray(res)) {
        keyStats = res;
      }
    } catch (e) {
      console.error("Failed to fetch key stats:", e);
    } finally {
      isLoading = false;
    }
  }

  async function testKey(index: number) {
    testingIndex = index;
    try {
      const res = await apiClient.post<any>(`/api/v1/admin/ai/test/${index}`);
      if (res?.status === "success") {
        nanobot.showToast("Key health verified successfully.", "success");
      } else {
        nanobot.showToast(res?.message || "Key test failed.", "error");
      }
      await fetchStats(); // Refresh
    } catch (e) {
      nanobot.showToast("Test Link Failure.", "error");
    } finally {
      testingIndex = null;
    }
  }

  async function resetAllKeys() {
    isLoading = true;
    try {
      const res = await apiClient.post<any>("/api/v1/admin/ai/keys/reset");
      if (res?.status === "success") {
        nanobot.showToast(res.message || "Đã reset toàn bộ keys về ACTIVE.", "success");
        await fetchStats();
      } else {
        nanobot.showToast(res?.message || "Reset thất bại.", "error");
      }
    } catch (e) {
      nanobot.showToast("Reset thất bại.", "error");
    } finally {
      isLoading = false;
    }
  }

  $effect(() => {
    if (show) fetchStats();
  });
</script>

{#if show}
  <div class="fixed inset-0 z-[100000] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md" transition:fade>
    <div 
      class="w-full max-w-4xl bg-zinc-950 border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh]"
      transition:scale={{ start: 0.95, duration: 300 }}
    >
      <header class="p-6 border-b border-white/5 flex items-center justify-between bg-zinc-900/50">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-cyan-500/10 rounded-lg">
            <Activity size={20} class="text-cyan-400" />
          </div>
          <div>
            <h2 class="text-lg font-black text-white italic tracking-tight">COGNITIVE POOL DIAGNOSTICS</h2>
            <p class="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Real-time Gemini Key Health Matrix</p>
          </div>
        </div>
        <button onclick={onClose} class="text-zinc-500 hover:text-white transition-colors">
          <X size={24} />
        </button>
      </header>

      <div class="flex-1 overflow-y-auto custom-scrollbar p-6">
        {#if isLoading && keyStats.length === 0}
          <div class="h-64 flex flex-col items-center justify-center gap-4">
            <RefreshCw size={32} class="text-cyan-500 animate-spin" />
            <span class="text-xs font-mono text-cyan-500/50 uppercase tracking-widest">Scanning Neural Pathways...</span>
          </div>
        {:else}
          <div class="space-y-4">
            <div class="grid grid-cols-6 gap-4 px-4 py-2 text-[10px] font-black text-zinc-500 uppercase tracking-widest border-b border-white/5">
              <div class="col-span-1">Index</div>
              <div class="col-span-2">Key Preview</div>
              <div class="col-span-1 text-center">Health</div>
              <div class="col-span-1 text-center">Status</div>
              <div class="col-span-1 text-right">Actions</div>
            </div>

            {#each keyStats as stat}
              <div class="grid grid-cols-6 gap-4 px-4 py-4 items-center bg-white/[0.02] border border-white/5 rounded-xl hover:bg-white/[0.04] transition-all group">
                <div class="text-xs font-mono text-zinc-500">#{stat.index}</div>
                <div class="col-span-2 text-xs font-mono text-zinc-300">{stat.key_preview}</div>
                <div class="col-span-1 flex justify-center">
                  <div class="w-12 h-1 bg-zinc-800 rounded-full overflow-hidden">
                    <div 
                      class="h-full {stat.health_score > 70 ? 'bg-emerald-500' : stat.health_score > 30 ? 'bg-amber-500' : 'bg-red-500'}" 
                      style="width: {stat.health_score}%"
                    ></div>
                  </div>
                </div>
                <div class="col-span-1 flex justify-center">
                  {#if stat.status === 'ACTIVE'}
                    <span class="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 text-[9px] font-black rounded border border-emerald-500/20 flex items-center gap-1">
                      <ShieldCheck size={10} />
                      ACTIVE
                    </span>
                  {:else if stat.status === 'COOLDOWN'}
                    <span class="px-2 py-0.5 bg-amber-500/10 text-amber-400 text-[9px] font-black rounded border border-amber-500/20 flex items-center gap-1">
                      <RefreshCw size={10} class="animate-spin" />
                      COOLING
                    </span>
                  {:else}
                    <span class="px-2 py-0.5 bg-red-500/10 text-red-400 text-[9px] font-black rounded border border-red-500/20 flex items-center gap-1">
                      <Skull size={10} />
                      DEAD
                    </span>
                  {/if}
                </div>
                <div class="col-span-1 text-right">
                  <button 
                    onclick={() => testKey(stat.index)}
                    disabled={testingIndex === stat.index}
                    class="p-2 hover:bg-cyan-500/20 rounded-lg text-zinc-500 hover:text-cyan-400 transition-all disabled:opacity-50"
                  >
                    <RefreshCw size={14} class={testingIndex === stat.index ? 'animate-spin' : ''} />
                  </button>
                </div>
              </div>
            {/each}

            {#if keyStats.length === 0}
              <div class="h-32 flex flex-col items-center justify-center border-2 border-dashed border-white/5 rounded-2xl">
                <AlertTriangle size={24} class="text-zinc-700 mb-2" />
                <span class="text-xs text-zinc-600 font-bold uppercase tracking-widest">No keys detected in cognitive pool</span>
              </div>
            {/if}
          </div>
        {/if}
      </div>

      <footer class="p-6 border-t border-white/5 bg-zinc-900/30 flex justify-between items-center">
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-emerald-500"></div>
            <span class="text-[10px] text-zinc-500 font-bold">ACTIVE: {keyStats.filter(k => k.status === 'ACTIVE').length}</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-amber-500"></div>
            <span class="text-[10px] text-zinc-500 font-bold">COOLDOWN: {keyStats.filter(k => k.status === 'COOLDOWN').length}</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-red-500"></div>
            <span class="text-[10px] text-zinc-500 font-bold">DEAD: {keyStats.filter(k => k.status === 'DEAD').length}</span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button 
            onclick={resetAllKeys}
            disabled={isLoading}
            class="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 text-[10px] font-black uppercase tracking-widest rounded-lg border border-red-500/20 transition-all flex items-center gap-2 disabled:opacity-50"
          >
            <Skull size={12} />
            Reset All Keys
          </button>
          <button 
            onclick={fetchStats}
            disabled={isLoading}
            class="px-4 py-2 bg-white/5 hover:bg-white/10 text-white text-[10px] font-black uppercase tracking-widest rounded-lg border border-white/10 transition-all flex items-center gap-2 disabled:opacity-50"
          >
            <RefreshCw size={12} class={isLoading ? 'animate-spin' : ''} />
            Refresh Matrix
          </button>
        </div>
      </footer>
    </div>
  </div>
{/if}
