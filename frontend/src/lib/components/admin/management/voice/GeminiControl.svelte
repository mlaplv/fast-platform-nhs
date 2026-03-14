<script lang="ts">
  import { onMount, tick } from "svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import Cpu from "lucide-svelte/icons/cpu";
  import Activity from "lucide-svelte/icons/activity";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import Layers from "lucide-svelte/icons/layers";
  import Zap from "lucide-svelte/icons/zap";
  import Check from "lucide-svelte/icons/check";
  import ArrowUp from "lucide-svelte/icons/arrow-up";
  import ArrowDown from "lucide-svelte/icons/arrow-down";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import Plus from "lucide-svelte/icons/plus";
  import Trophy from "lucide-svelte/icons/trophy";

  let { onOpenDiagnostics } = $props<{
    onOpenDiagnostics: () => void;
  }>();

  // State Management
  let bulkKeys = $state("");
  let priorityStack = $state<string[]>([]);
  
  let isSyncing = $state(false);
  let isSavingModels = $state(false);
  let isDiscovering = $state(false);
  
  // Persistence Tracking
  let savedStack = $state<string[]>([]);
  let hasSavedOnce = $state(false);

  // Discovery State
  let showDiscoveryDropdown = $state(false);

  // Load Initial Config
  onMount(async () => {
    try {
      const res = await apiClient.get<any>("/api/v1/admin/ai/models");
      if (res) {
        // Construct the stack: Primary first, then waterfall
        const primary = res.primary_model;
        const waterfall = res.ai_models || [];
        
        // Ensure primary is at the top and avoid duplicates
        const fullStack = primary ? [primary, ...waterfall.filter(m => m !== primary)] : waterfall;
        priorityStack = fullStack;
        savedStack = [...fullStack];
        
        if (primary) hasSavedOnce = true;
        if (res.discovered_models) {
          nanobot.setDiscoveredModels(res.discovered_models);
        }
      }
    } catch (e) {
      console.error("Failed to fetch model config:", e);
    }

    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('.discovery-container')) {
        showDiscoveryDropdown = false;
      }
    };
    window.addEventListener('click', handleClick);
    return () => window.removeEventListener('click', handleClick);
  });

  // Actions
  async function syncKeys() {
    if (!bulkKeys.trim()) {
      nanobot.showToast("Please enter at least one Gemini key.", "error");
      return;
    }
    isSyncing = true;
    try {
      const res = await apiClient.post<any>("/api/v1/admin/ai/keys/bulk", { keys: bulkKeys });
      if (res?.status === "success") {
        nanobot.showToast(`Neural Link Established: ${res.count} keys synced.`, "success");
        bulkKeys = ""; 
      } else {
        nanobot.showToast(res?.message || "Link synchronization failed.", "error");
      }
    } catch (e) {
      nanobot.showToast("Critical Link Failure: API unreachable.", "error");
    } finally {
      isSyncing = false;
    }
  }

  async function discoverModels() {
    isDiscovering = true;
    try {
      const res = await apiClient.get<any>("/api/v1/admin/ai/models/discover");
      if (res?.status === "success" && res.models?.length) {
        nanobot.setDiscoveredModels(res.models);
        nanobot.showToast(`Deep Scan: Found ${res.models.length} active models.`, "success");
        showDiscoveryDropdown = true;
      }
    } catch (e) {
      nanobot.showToast("Scanning failed. Provider might be throttled.", "error");
    } finally {
      isDiscovering = false;
    }
  }

  async function savePriorityStack() {
    if (priorityStack.length === 0) {
      nanobot.showToast("Neural Stack cannot be empty.", "error");
      return;
    }
    isSavingModels = true;
    try {
      const primary = priorityStack[0];
      const waterfall = priorityStack.slice(1);
      
      const res = await apiClient.post<any>("/api/v1/admin/ai/models", {
        primary_model: primary,
        ai_models: waterfall
      });

      if (res?.status === "success") {
        savedStack = [...priorityStack];
        hasSavedOnce = true;
        nanobot.showToast(`Stack Persistent: Lead is ${primary}`, "success");
      }
    } catch (e) {
      nanobot.showToast("Sync failure: Backend rejected the stack.", "error");
    } finally {
      isSavingModels = false;
    }
  }

  // Stack Mutators
  function setAsLead(index: number) {
    const model = priorityStack[index];
    const rest = priorityStack.filter((_, i) => i !== index);
    priorityStack = [model, ...rest];
    nanobot.showToast(`${model} promoted to Lead Operative.`, "success");
  }

  function moveUp(index: number) {
    if (index === 0) return;
    const newStack = [...priorityStack];
    [newStack[index - 1], newStack[index]] = [newStack[index], newStack[index - 1]];
    priorityStack = newStack;
  }

  function moveDown(index: number) {
    if (index === priorityStack.length - 1) return;
    const newStack = [...priorityStack];
    [newStack[index + 1], newStack[index]] = [newStack[index], newStack[index + 1]];
    priorityStack = newStack;
  }

  function removeModel(index: number) {
    priorityStack = priorityStack.filter((_, i) => i !== index);
  }

  function addModelFromDiscovery(model: string) {
    if (!priorityStack.includes(model)) {
      priorityStack = [...priorityStack, model];
    }
    showDiscoveryDropdown = false;
  }

  // Derived
  const hasUnsavedChanges = $derived(JSON.stringify(priorityStack) !== JSON.stringify(savedStack));
</script>

<style>
  @keyframes pulse-emerald {
    0%, 100% { border-color: rgba(16, 185, 129, 0.2); }
    50% { border-color: rgba(16, 185, 129, 0.5); }
  }
  .lead-card {
    animation: pulse-emerald 2s infinite;
  }
</style>

<div class="bg-zinc-950/40 border border-white/5 rounded-2xl p-6 space-y-8 flex flex-col h-full">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div class="flex flex-col gap-1">
      <h3 class="text-xs font-black text-emerald-400 uppercase tracking-[0.2em] flex items-center gap-2">
        <Cpu size={16} />
        Neural Order
      </h3>
      <p class="text-[10px] text-zinc-500 font-medium">Configure priority stack & cognitive fallback.</p>
    </div>
    <button 
      onclick={onOpenDiagnostics}
      class="h-8 px-3 bg-zinc-900/50 hover:bg-zinc-900 text-[10px] uppercase tracking-widest font-black text-zinc-400 hover:text-cyan-400 transition-all flex items-center gap-2 rounded-lg border border-white/5"
    >
      <Activity size={12} />
      Diagnostics
    </button>
  </div>

  <!-- Key Syncing -->
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <label class="text-[10px] text-zinc-500 font-black uppercase tracking-widest">Cognitive Pool (Keys)</label>
      <button
        onclick={syncKeys}
        disabled={isSyncing || !bulkKeys}
        class="h-7 px-3 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 text-[9px] font-black uppercase tracking-widest rounded-md border border-emerald-500/10 transition-all disabled:opacity-30"
      >
        {isSyncing ? 'Establishing...' : 'Sync Pool'}
      </button>
    </div>
    <textarea
      bind:value={bulkKeys}
      placeholder="Paste comma-separated Gemini API keys..."
      class="w-full h-16 bg-black/40 border border-white/5 rounded-xl p-3 text-[11px] font-mono text-zinc-400 focus:outline-none focus:border-emerald-500/30 transition-all resize-none"
    ></textarea>
  </div>

  <!-- Priority Stack -->
  <div class="flex-1 flex flex-col min-h-0 space-y-4 pt-4 border-t border-white/5">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <Layers size={14} class="text-cyan-400" />
        <span class="text-xs font-black text-zinc-300 uppercase tracking-widest">Priority Stack</span>
      </div>
      <button 
        onclick={discoverModels}
        disabled={isDiscovering}
        class="h-7 px-3 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 text-[9px] font-black uppercase tracking-widest rounded-md border border-cyan-500/10 transition-all disabled:opacity-30 flex items-center gap-2"
      >
        <RefreshCw size={10} class={isDiscovering ? "animate-spin" : ""} />
        Neural Discovery
      </button>
    </div>

    <!-- Models List -->
    <div class="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-2">
      {#each priorityStack as model, i}
        <div 
          class="group flex items-center gap-3 p-3 bg-zinc-900/30 border rounded-xl transition-all {i === 0 ? 'bg-emerald-500/5 border-emerald-500/20 lead-card' : 'border-white/5 hover:border-white/10'}"
        >
          <!-- Rank Badge -->
          <div class="w-8 flex flex-col items-center justify-center">
            <span class="text-[10px] font-black {i === 0 ? 'text-emerald-400' : 'text-zinc-600'}">#{i + 1}</span>
            {#if i === 0}
              <Trophy size={10} class="text-emerald-500" />
            {/if}
          </div>

          <!-- Model Info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-[11px] font-mono font-bold {i === 0 ? 'text-zinc-100' : 'text-zinc-400'} truncate">
                {model}
              </span>
              {#if i === 0}
                <span class="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 text-[8px] font-black rounded uppercase tracking-tighter">Leader</span>
              {:else}
                <span class="px-1.5 py-0.5 bg-zinc-800 text-zinc-500 text-[8px] font-black rounded uppercase tracking-tighter">Backup</span>
              {/if}
            </div>
          </div>

          <!-- Controls -->
          <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {#if i !== 0}
              <button 
                onclick={() => setAsLead(i)}
                title="Promote to Lead"
                class="p-1.5 hover:bg-emerald-500/20 text-emerald-400/50 hover:text-emerald-400 rounded transition-colors"
              >
                <Zap size={14} />
              </button>
            {/if}
            <div class="flex bg-zinc-800/50 rounded-lg p-0.5 mx-1">
              <button 
                onclick={() => moveUp(i)}
                disabled={i === 0}
                class="p-1 hover:text-white disabled:opacity-20 transition-colors"
                title="Move Up"
              >
                <ArrowUp size={12} />
              </button>
              <button 
                onclick={() => moveDown(i)}
                disabled={i === priorityStack.length - 1}
                class="p-1 hover:text-white disabled:opacity-20 transition-colors"
                title="Move Down"
              >
                <ArrowDown size={12} />
              </button>
            </div>
            <button 
              onclick={() => removeModel(i)}
              class="p-1.5 hover:bg-red-500/20 text-red-400/50 hover:text-red-400 rounded transition-colors"
              title="Decommission"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>
      {/each}

      <!-- Quick Add Selection -->
      <div class="relative discovery-container">
        <button 
          onclick={() => showDiscoveryDropdown = !showDiscoveryDropdown}
          class="w-full p-3 border border-dashed border-white/5 hover:border-white/10 rounded-xl flex items-center justify-center gap-2 text-zinc-600 hover:text-zinc-400 transition-all group"
        >
          <Plus size={14} class="group-hover:rotate-90 transition-transform duration-300" />
          <span class="text-[10px] font-black uppercase tracking-widest">Enlist New Operative</span>
        </button>

        {#if showDiscoveryDropdown && nanobot.discoveredModels.length}
          <div class="absolute z-50 left-0 right-0 bottom-full mb-2 max-h-48 overflow-y-auto bg-zinc-900 border border-white/10 rounded-xl shadow-2xl backdrop-blur-xl p-1">
            {#each nanobot.discoveredModels as m}
              {#if !priorityStack.includes(m)}
                <button 
                  onclick={() => addModelFromDiscovery(m)}
                  class="w-full text-left px-4 py-2 text-[10px] font-mono text-zinc-500 hover:text-emerald-400 hover:bg-emerald-500/5 rounded-lg transition-all"
                >
                  {m}
                </button>
              {/if}
            {/each}
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- Footer Actions -->
  <div class="pt-4 border-t border-white/5 flex items-center justify-between">
    <div class="flex flex-col">
      {#if hasUnsavedChanges}
        <span class="text-[9px] text-amber-400 font-black animate-pulse flex items-center gap-1 uppercase tracking-widest">
          <Activity size={10} />
          Unsaved Modifications
        </span>
      {:else if hasSavedOnce}
        <span class="text-[9px] text-emerald-500 font-bold flex items-center gap-1 uppercase tracking-widest">
          <Check size={10} />
          Neural Sync: Active
        </span>
      {/if}
    </div>

    <button
      onclick={savePriorityStack}
      disabled={isSavingModels || !hasUnsavedChanges}
      class="h-10 px-6 {hasUnsavedChanges ? 'bg-amber-500' : 'bg-zinc-800'} text-zinc-950 text-[10px] font-black uppercase tracking-[0.2em] rounded-xl transition-all hover:scale-[1.02] active:scale-95 disabled:opacity-50 disabled:scale-100 flex items-center gap-2"
    >
      {#if isSavingModels}
        <RefreshCw size={14} class="animate-spin text-zinc-950" />
        Committing...
      {:else}
        {hasUnsavedChanges ? 'Update Priority' : 'Synced'}
      {/if}
    </button>
  </div>
</div>
