<script lang="ts">
  import { onMount, tick } from "svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import type { AIModelConfig, GenericAIResponse } from "$lib/state/types";
  import Cpu from "@lucide/svelte/icons/cpu";
  import Activity from "@lucide/svelte/icons/activity";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Layers from "@lucide/svelte/icons/layers";
  import Zap from "@lucide/svelte/icons/zap";
  import Check from "@lucide/svelte/icons/check";
  import ArrowUp from "@lucide/svelte/icons/arrow-up";
  import ArrowDown from "@lucide/svelte/icons/arrow-down";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Plus from "@lucide/svelte/icons/plus";
  import Trophy from "@lucide/svelte/icons/trophy";
  import Settings from "@lucide/svelte/icons/settings";
  import Shield from "@lucide/svelte/icons/shield";
  import Database from "@lucide/svelte/icons/database";
  import X from "@lucide/svelte/icons/x";

  import { dndzone } from "svelte-dnd-action";
  import { portal } from "$lib/actions/portal";
  
  let { onOpenDiagnostics } = $props<{
    onOpenDiagnostics: () => void;
  }>();

  // State Management
  let bulkKeys = $state("");
  
  // DnD requires objects with IDs
  let items = $state<Array<{id: string, name: string}>>([]);
  
  let isSyncing = $state(false);
  let isSavingModels = $state(false);
  let isDiscovering = $state(false);
  
  // Persistence Tracking
  let savedStack = $state<string[]>([]);
  let hasSavedOnce = $state(false);

  // Discovery State
  let showDiscoveryDropdown = $state(false);
  let dropdownAnchor = $state<HTMLElement | null>(null);
  let showAll = $state(false);

  interface AIOrchestrationConfig {
    blacklist: string[];
    role_patterns: Record<string, string[]>;
    lockdown: boolean;
    error_mapping: Record<string, string>;
  }

  // Orchestration State
  let showOrchestrationModal = $state(false);
  let orchestrationConfig = $state<AIOrchestrationConfig | null>(null);
  let isSavingOrchestration = $state(false);

  // Load Initial Config
  onMount(async () => {
    try {
      const [modelRes, orchRes] = await Promise.all([
        apiClient.get<AIModelConfig>("/api/v1/admin/ai/models"),
        fetch("/api/v1/admin/ai/orchestration").then(r => r.json())
      ]);

      if (modelRes) {
        const primary = modelRes.primary_model;
        const waterfall = modelRes.ai_models || [];
        const fullStack = primary ? [primary, ...waterfall.filter(m => m !== primary)] : waterfall;
        
        items = fullStack.map(m => ({ id: m, name: m }));
        savedStack = [...fullStack];
        
        if (primary) hasSavedOnce = true;
        if (modelRes.discovered_models) {
          nanobot.setDiscoveredModels(modelRes.discovered_models);
        }
      }

      if (orchRes) {
        orchestrationConfig = orchRes;
      }
    } catch (e) {
      console.error("Failed to initialize AI management:", e);
    }

    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('.discovery-container') && !target.closest('.portal-dropdown')) {
        showDiscoveryDropdown = false;
      }
    };
    window.addEventListener('click', handleClick);
    return () => window.removeEventListener('click', handleClick);
  });

  async function loadOrchestration() {
    try {
      const resp = await fetch("/api/v1/admin/ai/orchestration");
      if (resp.ok) orchestrationConfig = await resp.json();
    } catch (e) {}
  }

  async function saveOrchestration() {
    if (!orchestrationConfig) return;
    isSavingOrchestration = true;
    try {
      const resp = await fetch("/api/v1/admin/ai/orchestration", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(orchestrationConfig)
      });
      if (resp.ok) {
        nanobot.showToast("Neural Orchestration hot-reloaded!", "success");
        showOrchestrationModal = false;
      }
    } catch (e) {
      nanobot.showToast("Failed to update orchestration rules", "error");
    } finally {
      isSavingOrchestration = false;
    }
  }

  // Actions
  async function syncKeys() {
    if (!bulkKeys.trim()) {
      nanobot.showToast("Please enter at least one Gemini key.", "error");
      return;
    }
    isSyncing = true;
    try {
      const res = await apiClient.post<GenericAIResponse>("/api/v1/admin/ai/keys/bulk", { keys: bulkKeys });
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

  async function discoverModels(e: MouseEvent) {
    dropdownAnchor = e.currentTarget as HTMLElement;
    isDiscovering = true;
    try {
      const res = await apiClient.get<GenericAIResponse>("/api/v1/admin/ai/models/discover");
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
    if (items.length === 0) {
      nanobot.showToast("Neural Stack cannot be empty.", "error");
      return;
    }
    isSavingModels = true;
    try {
      const currentStack = items.map(i => i.name);
      const primary = currentStack[0];
      const waterfall = currentStack.slice(1);

      const res = await apiClient.post<GenericAIResponse>("/api/v1/admin/ai/models", {
        primary_model: primary,
        ai_models: waterfall
      });

      if (res?.status === "success") {
        savedStack = [...currentStack];
        hasSavedOnce = true;
        nanobot.showToast(`Stack Persistent: Lead is ${primary}`, "success");
      }
    } catch (e) {
      nanobot.showToast("Sync failure: Backend rejected the stack.", "error");
    } finally {
      isSavingModels = false;
    }
  }

  // DnD Handlers
  function handleDndConsider(e: CustomEvent<DndEvent<{id: string, name: string}>>) {
    items = e.detail.items;
  }

  function handleDndFinalize(e: CustomEvent<DndEvent<{id: string, name: string}>>) {
    items = e.detail.items;
  }

  function setAsLead(index: number) {
    const model = items[index];
    const rest = items.filter((_, i) => i !== index);
    items = [model, ...rest];
    nanobot.showToast(`${model.name} promoted to Lead Operative.`, "success");
  }

  function removeModel(index: number) {
    items = items.filter((_, i) => i !== index);
  }

  function addModelFromDiscovery(model: string) {
    if (!items.find(i => i.name === model)) {
      items = [...items, { id: model, name: model }];
    }
    showDiscoveryDropdown = false;
  }

  // Dropdown Positioning
  function toggleDiscovery(e: MouseEvent) {
    dropdownAnchor = e.currentTarget as HTMLElement;
    showDiscoveryDropdown = !showDiscoveryDropdown;
  }

  // Derived
  const priorityStack = $derived(items.map(i => i.name));
  const hasUnsavedChanges = $derived(JSON.stringify(priorityStack) !== JSON.stringify(savedStack));

  let dropdownStyle = $state("");

  // Elite V2.2: Universal Model Scoring (Client-side)
  function scoreModel(name: string): number {
    const m = (name || "").toLowerCase();
    let score = 0;
    if (m.includes("3.1")) score += 1000;
    else if (m.includes("3")) score += 900;
    else if (m.includes("2.5")) score += 800;
    else if (m.includes("2.0")) score += 700;
    else if (m.includes("1.5")) score += 600;

    if (m.includes("pro")) score += 100;
    else if (m.includes("ultra")) score += 200;
    else if (m.includes("flash")) score += 50;
    
    if (m.includes("customtools")) score += 10;
    return score;
  }

  const sortedDiscovered = $derived(
    [...nanobot.discoveredModels].sort((a, b) => scoreModel(b) - scoreModel(a))
  );

  $effect(() => {
    if (showDiscoveryDropdown && dropdownAnchor) {
      const rect = dropdownAnchor.getBoundingClientRect();
      const isTopHalf = rect.top < window.innerHeight / 2;
      const isRightSide = rect.left > window.innerWidth / 2;
      
      dropdownStyle = `
        ${isRightSide ? `right: ${window.innerWidth - rect.right}px;` : `left: ${rect.left}px;`}
        min-width: 340px;
        ${isTopHalf ? `top: ${rect.bottom + 12}px;` : `bottom: ${window.innerHeight - rect.top + 12}px;`}
      `;
    }
  });
</script>

<style>
  @keyframes pulse-emerald {
    0%, 100% { border-color: rgba(16, 185, 129, 0.2); }
    50% { border-color: rgba(16, 185, 129, 0.5); }
  }
  .lead-card {
    animation: pulse-emerald 2s infinite;
  }
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 20px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(34, 211, 238, 0.3);
  }
  /* DnD Styles */
  :global(.dnd-ghost) {
    opacity: 0.5;
    background: rgba(16, 185, 129, 0.1) !important;
    border: 1px dashed rgba(16, 185, 129, 0.5) !important;
  }
</style>

<div class="bg-zinc-950/40 border border-white/5 rounded-2xl p-5 space-y-5 flex flex-col h-[600px] flex-shrink-0 relative">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div class="flex flex-col gap-1">
      <h3 class="text-xs font-black text-emerald-400 uppercase tracking-[0.2em] flex items-center gap-2">
        <Cpu size={16} />
        Neural Order
      </h3>
      <p class="text-[10px] text-zinc-500 font-medium">Configure priority stack & cognitive fallback.</p>
    </div>
    <div class="flex items-center gap-2">
      <button 
        onclick={() => showOrchestrationModal = true}
        class="h-8 px-3 bg-zinc-900/50 hover:bg-zinc-900 text-[10px] uppercase tracking-widest font-black text-zinc-500 hover:text-amber-400 transition-all flex items-center gap-2 rounded-lg border border-white/5"
      >
        <Settings size={12} />
        Expert Rules
      </button>
      <button 
        onclick={onOpenDiagnostics}
        class="h-8 px-3 bg-zinc-900/50 hover:bg-zinc-900 text-[10px] uppercase tracking-widest font-black text-zinc-400 hover:text-cyan-400 transition-all flex items-center gap-2 rounded-lg border border-white/5"
      >
        <Activity size={12} />
        Diagnostics
      </button>
    </div>
  </div>

  <!-- Orchestration Modal -->
  {#if showOrchestrationModal}
    <div 
      use:portal={"body"}
      class="fixed inset-0 z-[10000] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
    >
      <div class="w-full max-w-2xl bg-zinc-950 border border-white/10 rounded-3xl shadow-[0_30px_100px_rgba(0,0,0,0.9)] overflow-hidden flex flex-col max-h-[90vh]">
        <div class="p-6 border-b border-white/5 flex items-center justify-between bg-zinc-900/30">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-2xl bg-amber-500/10 flex items-center justify-center text-amber-500 border border-amber-500/20">
              <Shield size={20} />
            </div>
            <div>
              <h4 class="text-sm font-black text-zinc-100 uppercase tracking-widest">Neural Orchestration</h4>
              <p class="text-[10px] text-zinc-500 font-medium">Global AI governance, blacklists & patterns.</p>
            </div>
          </div>
          <button onclick={() => showOrchestrationModal = false} class="text-zinc-500 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        <div class="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
          <div class="space-y-2">
            <label class="text-[10px] text-zinc-500 font-black uppercase tracking-widest flex items-center gap-2">
              <Database size={12} />
              JSON Configuration (Real DB)
            </label>
            <textarea
              value={JSON.stringify(orchestrationConfig, null, 2)}
              oninput={(e) => {
                try {
                  orchestrationConfig = JSON.parse(e.currentTarget.value);
                } catch(e) {}
              }}
              class="w-full h-[400px] bg-black/60 border border-white/5 rounded-2xl p-5 text-[11px] font-mono text-amber-200/80 focus:outline-none focus:border-amber-500/30 transition-all custom-scrollbar leading-relaxed"
            ></textarea>
            <p class="text-[9px] text-zinc-600 italic">⚠️ Changing these values will affect ALL AI services globally (Flash/Brain/Support).</p>
          </div>
        </div>

        <div class="p-6 bg-zinc-900/30 border-t border-white/5 flex items-center justify-end gap-3">
          <button 
            onclick={() => showOrchestrationModal = false}
            class="px-5 py-2.5 text-[11px] font-black uppercase tracking-widest text-zinc-500 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button 
            onclick={saveOrchestration}
            disabled={isSavingOrchestration}
            class="px-8 py-2.5 bg-amber-500 text-black text-[11px] font-black uppercase tracking-widest rounded-xl hover:bg-amber-400 transition-all shadow-[0_10px_30px_rgba(245,158,11,0.2)] disabled:opacity-50"
          >
            {isSavingOrchestration ? 'Reloading...' : 'Apply Global Rules'}
          </button>
        </div>
      </div>
    </div>
  {/if}

  <!-- Key Syncing -->
  <div class="space-y-3">
    <div class="flex items-center justify-between">
      <label for="bulk-keys" class="text-[10px] text-zinc-500 font-black uppercase tracking-widest">Cognitive Pool (Keys)</label>
      <button
        onclick={syncKeys}
        disabled={isSyncing || !bulkKeys}
        class="h-7 px-3 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 text-[9px] font-black uppercase tracking-widest rounded-md border border-emerald-500/10 transition-all disabled:opacity-30"
      >
        {isSyncing ? 'Establishing...' : 'Sync Pool'}
      </button>
    </div>
    <textarea
      id="bulk-keys"
      bind:value={bulkKeys}
      placeholder="Paste comma-separated Gemini API keys..."
      class="w-full h-12 bg-black/40 border border-white/5 rounded-xl p-3 text-[11px] font-mono text-zinc-400 focus:outline-none focus:border-emerald-500/30 transition-all resize-none"
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

    <!-- Models List with DnD -->
    <div 
      class="space-y-2 py-1"
      use:dndzone={{items, flipDurationMs: 200, dropTargetStyle: {}}}
      onconsider={handleDndConsider}
      onfinalize={handleDndFinalize}
    >
      {#each items as item, i (item.id)}
        <div 
          class="group flex items-center gap-2 p-2.5 bg-zinc-900/30 border rounded-xl transition-all {i === 0 ? 'bg-emerald-500/5 border-emerald-500/20 lead-card' : 'border-white/5 hover:border-white/10'} {!showAll && i >= 3 ? 'hidden' : 'flex'}"
        >
          <!-- Drag Handle -->
          <div class="cursor-grab active:cursor-grabbing p-1 -ml-1 text-zinc-700 hover:text-zinc-400 transition-colors">
            <Layers size={12} />
          </div>

          <!-- Rank Badge -->
          <div class="w-6 flex flex-col items-center justify-center">
            <span class="text-[10px] font-black {i === 0 ? 'text-emerald-400' : 'text-zinc-600'}">#{i + 1}</span>
            {#if i === 0}
              <Trophy size={10} class="text-emerald-500" />
            {/if}
          </div>

          <!-- Model Info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-[11px] font-mono font-bold {i === 0 ? 'text-zinc-100' : 'text-zinc-400'} truncate">
                {item.name}
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

      {#if items.length > 3}
        <button 
          onclick={() => showAll = !showAll}
          class="w-full py-2 text-[9px] font-black uppercase tracking-[0.2em] text-zinc-500 hover:text-cyan-400 transition-colors flex items-center justify-center gap-2"
        >
          {showAll ? 'Collapse Stack' : `Show All (${items.length - 3} more)`}
          <ArrowDown size={10} class={showAll ? "rotate-180 transition-transform" : "transition-transform"} />
        </button>
      {/if}
    </div>

    <!-- Quick Add Selection -->
    <div class="relative discovery-container mt-2">
      <button 
        onclick={toggleDiscovery}
        class="w-full p-3 border border-dashed border-white/5 hover:border-white/10 rounded-xl flex items-center justify-center gap-2 text-zinc-600 hover:text-zinc-400 transition-all group"
      >
        <Plus size={14} class="group-hover:rotate-90 transition-transform duration-300" />
        <span class="text-[10px] font-black uppercase tracking-widest">Enlist New Operative</span>
      </button>

      {#if showDiscoveryDropdown && nanobot.discoveredModels.length}
        <div 
          use:portal={"body"}
          class="portal-dropdown fixed z-[9999] bg-black/95 border border-cyan-500/30 rounded-2xl shadow-[0_20px_80px_rgba(0,0,0,0.9)] backdrop-blur-3xl p-1 custom-scrollbar overflow-y-auto ring-1 ring-white/10"
          style={dropdownStyle}
        >
          <div class="p-3 border-b border-white/5 mb-1 sticky top-0 bg-black/90 backdrop-blur-md flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-pulse"></div>
              <span class="text-[9px] font-black text-cyan-400 uppercase tracking-[0.2em]">Available Neural Models</span>
            </div>
            <span class="text-[8px] font-mono text-zinc-600">{nanobot.discoveredModels.length} Active</span>
          </div>
          <div class="max-h-[400px] overflow-y-auto px-1 py-1 space-y-0.5">
            {#each sortedDiscovered as m}
              {#if !priorityStack.includes(m)}
                <button 
                  onclick={() => addModelFromDiscovery(m)}
                  class="w-full text-left px-3 py-2.5 text-[11px] font-mono text-zinc-400 hover:text-cyan-300 hover:bg-cyan-500/10 rounded-xl transition-all flex items-center justify-between group"
                >
                  <span class="break-all">{m}</span>
                  <Plus size={12} class="opacity-0 group-hover:opacity-100 text-cyan-500 transition-opacity" />
                </button>
              {/if}
            {/each}
          </div>
        </div>
      {/if}
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
