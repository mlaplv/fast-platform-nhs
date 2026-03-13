<script lang="ts">
  import { onMount } from "svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import Cpu from "lucide-svelte/icons/cpu";
  import Activity from "lucide-svelte/icons/activity";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import Layers from "lucide-svelte/icons/layers";
  import Zap from "lucide-svelte/icons/zap";

  let { onOpenDiagnostics } = $props<{
    onOpenDiagnostics: () => void;
  }>();

  let bulkKeys = $state("");
  let primaryModel = $state("");
  let waterfallModels = $state<string[]>([]);
  
  let isSyncing = $state(false);
  let isSavingModels = $state(false);
  let isDiscovering = $state(false);

  async function discoverModels() {
    isDiscovering = true;
    try {
      const res = await apiClient.get<any>("/api/v1/admin/ai/models/discover");
      if (res?.status === "success" && res.models?.length) {
        // V75.6: Store in global persistent state
        nanobot.setDiscoveredModels(res.models);
        nanobot.showToast(`Neural Discovery: Found ${res.models.length} active models.`, "success");
      }
    } catch (e) {
      nanobot.showToast("Model discovery failed. Check link health.", "error");
    } finally {
      isDiscovering = false;
    }
  }

  // Reactive derived state for the UI list
  let geminiModels = $derived(nanobot.discoveredModels);

  onMount(async () => {
    // 1. Fetch saved config
    try {
      const res = await apiClient.get<any>("/api/v1/admin/ai/models");
      if (res) {
        primaryModel = res.primary_model || "";
        waterfallModels = res.ai_models || [];
        // V75.7: Populate global state with suggestions from DB
        if (res.discovered_models) {
          nanobot.setDiscoveredModels(res.discovered_models);
        }
      }
    } catch (e) {
      console.error("Failed to fetch model config:", e);
    }
  });

  async function syncKeys() {
    if (!bulkKeys.trim()) {
      nanobot.showToast("Please enter at least one Gemini key.", "error");
      return;
    }
    isSyncing = true;
    try {
      const res = await apiClient.post<any>("/api/v1/admin/ai/keys/bulk", { keys: bulkKeys });
      if (res?.status === "success") {
        nanobot.showToast(`Successfully synchronized ${res.count} Gemini keys.`, "success");
        bulkKeys = ""; 
      } else {
        nanobot.showToast(res?.message || "Failed to sync keys.", "error");
      }
    } catch (e) {
      nanobot.showToast("Link Failure: Could not reach Admin AI API.", "error");
    } finally {
      isSyncing = false;
    }
  }

  async function saveModelConfig() {
    isSavingModels = true;
    try {
      const res = await apiClient.post<any>("/api/v1/admin/ai/models", {
        primary_model: primaryModel,
        ai_models: waterfallModels
      });
      if (res?.status === "success") {
        nanobot.showToast("AI Model Waterfall logic updated successfully.", "success");
      }
    } catch (e) {
      nanobot.showToast("Failed to update model configuration.", "error");
    } finally {
      isSavingModels = false;
    }
  }

  function addModel(model: string) {
    if (model && !waterfallModels.includes(model)) {
      waterfallModels = [...waterfallModels, model];
    }
  }

  // V75.5: Custom Dropdown Logic (Premium Vibe)
  let showPrimaryDropdown = $state(false);
  let showWaterfallDropdown = $state(false);

  onMount(async () => {
    // 1. Fetch saved config
    try {
      const res = await apiClient.get<any>("/api/v1/admin/ai/models");
      if (res) {
        primaryModel = res.primary_model || "";
        waterfallModels = res.ai_models || [];
      }
    } catch (e) {
      console.error("Failed to fetch model config:", e);
    }

    // 2. Click away logic
    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('.model-dropdown-container')) {
        showPrimaryDropdown = false;
        showWaterfallDropdown = false;
      }
    };
    window.addEventListener('click', handleClick);
    return () => window.removeEventListener('click', handleClick);
  });
</script>

<div class="bg-zinc-950/40 border border-white/5 rounded-xl p-5 space-y-6">
  <div class="flex items-center justify-between">
    <h3 class="text-sm font-black text-emerald-400 uppercase tracking-widest flex items-center gap-2">
      <Cpu size={16} />
      Gemini Cognitive Core
    </h3>
    <button 
      onclick={onOpenDiagnostics}
      class="text-[10px] uppercase tracking-widest font-bold text-zinc-500 hover:text-cyan-400 transition-colors flex items-center gap-1.5"
    >
      <Activity size={12} />
      Live Diagnostics
    </button>
  </div>

  <!-- Key Management Section -->
  <div class="space-y-4 pt-2 border-t border-white/5">
    <div class="space-y-2">
      <label class="block text-[10px] text-zinc-500 font-bold uppercase tracking-wider">
        Bulk Key Entry (Comma-Separated)
      </label>
      <textarea
        bind:value={bulkKeys}
        placeholder="Paste AIzaSy... keys here, separated by commas"
        class="w-full h-20 bg-black/50 border border-white/5 rounded-lg p-3 text-xs font-mono text-zinc-300 focus:outline-none focus:border-emerald-500/30 transition-all resize-none"
      ></textarea>
    </div>

    <div class="flex justify-end">
      <button
        onclick={syncKeys}
        disabled={isSyncing}
        class="h-8 px-4 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 text-[10px] font-black uppercase tracking-widest rounded-md border border-emerald-500/20 transition-all flex items-center gap-2 disabled:opacity-50"
      >
        {#if isSyncing}
          <RefreshCw size={12} class="animate-spin" />
        {/if}
        {isSyncing ? "Syncing Logic..." : "Sync Cognitive Pool"}
      </button>
    </div>
  </div>

  <!-- Model Waterfall Section -->
  <div class="space-y-4 pt-4 border-t border-white/5">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <Layers size={14} class="text-cyan-400" />
        <span class="text-[10px] font-black text-zinc-400 uppercase tracking-widest">Neural Waterfall Strategy</span>
      </div>
      <button 
        onclick={discoverModels}
        disabled={isDiscovering}
        class="text-[9px] uppercase tracking-widest font-bold text-zinc-500 hover:text-cyan-400 transition-colors flex items-center gap-1.5 bg-cyan-950/10 px-2 py-1 rounded border border-white/5 disabled:opacity-50"
      >
        <RefreshCw size={10} class={isDiscovering ? "animate-spin" : ""} />
        {isDiscovering ? "Discovering..." : "Refresh Google Models"}
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
      <div class="space-y-2 relative model-dropdown-container">
        <label class="block text-[10px] text-zinc-500 font-bold uppercase tracking-wider flex items-center gap-2">
          <Zap size={10} class="text-amber-400" />
          Primary Model (Default)
        </label>
        <div class="relative group">
          <input 
            type="text"
            bind:value={primaryModel}
            onfocus={() => showPrimaryDropdown = true}
            placeholder="Select or type model ID..."
            class="w-full h-10 bg-black/50 border border-white/10 rounded-lg px-3 text-xs font-mono text-cyan-400 focus:outline-none focus:border-cyan-500/50 transition-all placeholder:text-zinc-700"
          />
          <button 
            type="button"
            onclick={() => showPrimaryDropdown = !showPrimaryDropdown}
            class="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-zinc-500 hover:text-white font-bold"
          >
            {showPrimaryDropdown ? '▲' : '▼'}
          </button>
        </div>

        {#if showPrimaryDropdown}
          <div class="absolute z-50 left-0 right-0 mt-1 max-h-60 overflow-y-auto bg-zinc-900 border border-white/10 rounded-lg shadow-2xl backdrop-blur-xl ring-1 ring-white/5">
            {#each geminiModels as model}
              <button 
                type="button"
                onclick={() => { primaryModel = model; handlePrimaryChange(model); showPrimaryDropdown = false; }}
                class="w-full text-left px-4 py-2 text-xs font-mono text-zinc-400 hover:text-cyan-400 hover:bg-white/5 transition-all border-b border-white/5 last:border-0"
              >
                {model}
              </button>
            {/each}
          </div>
        {/if}
        <p class="text-[9px] text-zinc-600 italic">This model will be tried first for all requests.</p>
      </div>

      <div class="space-y-2 relative model-dropdown-container">
        <label class="block text-[10px] text-zinc-500 font-bold uppercase tracking-wider flex items-center gap-2">
          <Layers size={10} class="text-cyan-400" />
          Waterfall Chain (Failover)
        </label>
        <div class="flex flex-wrap gap-2 p-2 bg-black/50 border border-white/5 rounded-lg min-h-[2.5rem]">
          {#each waterfallModels as model, i}
            <span class="px-2 py-0.5 bg-cyan-950/30 text-cyan-300 text-[10px] rounded border border-cyan-500/20 flex items-center gap-1 group">
              {model}
              <button type="button" onclick={() => waterfallModels = waterfallModels.filter((_, idx) => idx !== i)} class="text-cyan-500/50 hover:text-red-400 transition-colors">×</button>
            </span>
          {/each}
          <div class="flex-1 min-w-[120px] relative">
            <input 
              type="text"
              placeholder="+ Add model..."
              class="w-full bg-transparent border-none text-[10px] text-zinc-400 focus:outline-none placeholder:text-zinc-700 h-6"
              onfocus={() => showWaterfallDropdown = true}
              onkeydown={(e) => {
                if (e.key === 'Enter' && (e.target as HTMLInputElement).value.trim()) {
                  addModel((e.target as HTMLInputElement).value.trim());
                  (e.target as HTMLInputElement).value = '';
                  showWaterfallDropdown = false;
                }
              }}
            />
            {#if showWaterfallDropdown}
              <div class="absolute z-50 left-0 right-0 top-full mt-2 max-h-48 overflow-y-auto bg-zinc-900 border border-white/10 rounded-lg shadow-2xl ring-1 ring-white/5">
                {#each geminiModels as model}
                  {#if !waterfallModels.includes(model)}
                    <button 
                      type="button"
                      onclick={() => { addModel(model); showWaterfallDropdown = false; }}
                      class="w-full text-left px-3 py-1.5 text-[10px] font-mono text-zinc-400 hover:text-emerald-400 hover:bg-white/5 transition-all"
                    >
                      {model}
                    </button>
                  {/if}
                {/each}
              </div>
            {/if}
          </div>
        </div>
        <p class="text-[9px] text-zinc-600 italic">Press Enter to add manual or select from list.</p>
      </div>
    </div>

    <div class="flex justify-end pt-2">
      <button
        onclick={saveModelConfig}
        disabled={isSavingModels}
        class="h-8 px-4 bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-400 text-[10px] font-black uppercase tracking-widest rounded-md border border-cyan-500/20 transition-all flex items-center gap-2 disabled:opacity-50 shadow-[0_4px_20px_rgba(34,211,238,0.1)]"
      >
        {#if isSavingModels}
          <RefreshCw size={12} class="animate-spin" />
        {:else}
          <Layers size={12} />
        {/if}
        {isSavingModels ? "Re-Routing..." : "Update Neural Waterfall"}
      </button>
    </div>
  </div>
</div>
