<script lang="ts">
  import { onMount } from "svelte";
  import { fade, fly, scale } from "svelte/transition";
  import { apiClient } from "$lib/utils/apiClient";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  
  import AdminModal from "../../ui/AdminModal.svelte";
  import Cpu from "lucide-svelte/icons/cpu";
  import Activity from "lucide-svelte/icons/activity";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import Zap from "lucide-svelte/icons/zap";
  import Shield from "lucide-svelte/icons/shield";
  import AlertTriangle from "lucide-svelte/icons/alert-triangle";
  import CheckCircle from "lucide-svelte/icons/check-circle";
  import Key from "lucide-svelte/icons/key";
  import Layers from "lucide-svelte/icons/layers";

  interface KeyStats {
    index: number;
    key_preview: string;
    fail_count: number;
    health_score: number;
    last_used: number;
    status: "ACTIVE" | "DEAD" | "COOLDOWN";
  }

  interface AIModelStatus {
    primary_model: string;
    ai_models: string[];
    discovered_models: string[];
  }

  let isOpen = $state(false);
  let keys = $state<KeyStats[]>([]);
  let modelStatus = $state<AIModelStatus | null>(null);
  let isRefreshing = $state(false);
  let isResetting = $state(false);
  let isDeepChecking = $state(false);
  let isSaving = $state(false);
  let isAutoOptimizing = $state(false);

  async function loadStats() {
    isRefreshing = true;
    try {
      const [kRes, mRes] = await Promise.all([
        apiClient.get<KeyStats[]>("/api/v1/admin/ai/keys"),
        apiClient.get<AIModelStatus>("/api/v1/admin/ai/models")
      ]);
      if (kRes) keys = kRes;
      if (mRes) modelStatus = mRes;
    } catch (e) {
      console.error("Neural fetch failed:", e);
    } finally {
      isRefreshing = false;
    }
  }

  async function autoOptimize() {
    isAutoOptimizing = true;
    try {
      const res = await apiClient.post<any>("/api/v1/admin/ai/models/auto-optimize");
      if (res?.ok) {
        nanobot.showToast(`Neural Link Optimized: ${res.data.top_3[0]} is now Lead.`, "success");
        await loadStats();
      }
    } catch (e) {
      nanobot.showToast("Optimization engine failure", "error");
    } finally {
      isAutoOptimizing = false;
    }
  }

  async function savePriority() {
    if (!modelStatus) return;
    isSaving = true;
    try {
      await apiClient.post("/api/v1/admin/ai/models", {
        primary_model: modelStatus.primary_model,
        ai_models: modelStatus.ai_models
      });
      nanobot.showToast("Cognitive Priority Synced to System DB", "success");
    } catch (e) {
      nanobot.showToast("Sync failed", "error");
    } finally {
      isSaving = false;
    }
  }

  function promoteModel(modelName: string) {
    if (!modelStatus) return;
    const waterfall = [modelName, ...modelStatus.ai_models.filter(m => m !== modelName)];
    modelStatus = {
      ...modelStatus,
      primary_model: modelName,
      ai_models: waterfall
    };
    nanobot.showToast(`${modelName} promoted to Lead Operative`, "info");
  }

  async function resetPool() {
    isResetting = true;
    try {
      await apiClient.post("/api/v1/admin/ai/keys/reset");
      nanobot.showToast("Neural Pool Purged & Re-synchronized", "success");
      await loadStats();
    } finally {
      isResetting = false;
    }
  }

  async function deepCheck() {
    isDeepChecking = true;
    try {
      await apiClient.post("/api/v1/admin/ai/keys/deep-check");
      nanobot.showToast("Deep Scan Complete: Quotas verified.", "success");
      await loadStats();
    } finally {
      isDeepChecking = false;
    }
  }

  function toggle() {
    isOpen = !isOpen;
    if (isOpen) loadStats();
  }

  onMount(() => {
    // Poll stats every 30s if open
    const interval = setInterval(() => {
      if (isOpen) loadStats();
    }, 30000);
    return () => clearInterval(interval);
  });

  const healthyKeys = $derived(keys.filter(k => k.status === "ACTIVE").length);
</script>

<!-- Neural Trigger Button -->
<button 
  onclick={toggle}
  class="h-9 px-3 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] transition-all flex items-center gap-2 group relative"
>
  <div class="absolute inset-0 rounded-xl bg-cyan-500/10 blur-md opacity-0 group-hover:opacity-100 transition-opacity"></div>
  <div class="relative flex items-center gap-2">
    <div class="w-2 h-2 rounded-full {healthyKeys > 0 ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}"></div>
    <span class="text-[10px] font-black text-zinc-400 group-hover:text-cyan-400 uppercase tracking-widest transition-colors">
      Neural Center
    </span>
    <div class="px-1.5 py-0.5 rounded-md bg-white/5 text-[9px] font-mono text-zinc-500 group-hover:text-cyan-300 transition-colors">
      {healthyKeys}/8
    </div>
  </div>
</button>

<AdminModal 
  {isOpen} 
  onClose={() => isOpen = false} 
  title="Neural Intelligence Center"
  subtitle="Trinity Core V2.2 | Global AI Orchestration"
  variant="cyan"
  headerIcon={Cpu}
  maxWidth="max-w-5xl"
>
  <div class="space-y-8">
    <!-- Auto-Optimize Hero Section -->
    <div class="relative group">
      <div class="absolute inset-0 bg-gradient-to-r from-cyan-500/20 via-indigo-500/20 to-emerald-500/20 blur-xl opacity-50 group-hover:opacity-100 transition-opacity rounded-3xl"></div>
      <div class="relative bg-black/60 border border-white/10 rounded-3xl p-6 flex items-center justify-between overflow-hidden">
        <div class="flex items-center gap-6">
          <div class="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center relative">
            <div class="absolute inset-0 bg-cyan-500 animate-ping opacity-20 rounded-2xl"></div>
            <Zap size={32} class="text-cyan-400 relative z-10" />
          </div>
          <div class="flex flex-col gap-1">
            <h2 class="text-lg font-black text-white uppercase tracking-widest italic">Auto-Optimize Neural Stack</h2>
            <p class="text-xs text-zinc-400 font-medium max-w-md">Automatically scans all keys, verifies real-time quotas, and selects the top 3 supreme models for your stack.</p>
          </div>
        </div>
        <button 
          onclick={autoOptimize}
          disabled={isAutoOptimizing}
          class="h-14 px-10 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white text-xs font-black uppercase tracking-[0.3em] rounded-2xl shadow-[0_20px_50px_rgba(6,182,212,0.3)] hover:shadow-[0_25px_60px_rgba(6,182,212,0.4)] transition-all hover:-translate-y-1 active:translate-y-0 disabled:opacity-50 disabled:translate-y-0"
        >
          {isAutoOptimizing ? "Optimizing Neural Links..." : "Run Neural Optimization"}
        </button>
      </div>
    </div>

    <!-- Top Stats Bar -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-zinc-900/30 border border-white/5 rounded-2xl p-4 flex flex-col gap-1">
        <span class="text-[9px] font-black text-zinc-500 uppercase tracking-widest">Lead Operative</span>
        <div class="flex items-center gap-2">
          <Zap size={14} class="text-amber-400" />
          <span class="text-xs font-mono font-bold text-zinc-100 truncate">
            {modelStatus?.primary_model || "Loading..."}
          </span>
        </div>
      </div>
      <div class="bg-zinc-900/30 border border-white/5 rounded-2xl p-4 flex flex-col gap-1">
        <span class="text-[9px] font-black text-zinc-500 uppercase tracking-widest">Cognitive Pool</span>
        <div class="flex items-center gap-2">
          <Key size={14} class="text-cyan-400" />
          <span class="text-xs font-mono font-bold text-zinc-100">
            {keys.length} Valid Keys // {healthyKeys} Ready
          </span>
        </div>
      </div>
      <div class="bg-zinc-900/30 border border-white/5 rounded-2xl p-4 flex flex-col gap-1">
        <span class="text-[9px] font-black text-zinc-500 uppercase tracking-widest">System Health</span>
        <div class="flex items-center gap-2">
          <Activity size={14} class={healthyKeys > 3 ? "text-emerald-400" : "text-red-400"} />
          <span class="text-xs font-mono font-bold text-zinc-100">
            {healthyKeys > 3 ? "OPTIMAL" : healthyKeys > 0 ? "DEGRADED" : "CRITICAL"}
          </span>
        </div>
      </div>
    </div>

    <!-- Keys Grid -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-xs font-black text-white uppercase tracking-[0.2em] flex items-center gap-2">
          <Shield size={14} class="text-cyan-500" />
          API Key Matrix (8 Slots)
        </h3>
        <div class="flex items-center gap-2">
          <button 
            onclick={deepCheck}
            disabled={isDeepChecking}
            class="h-8 px-4 bg-amber-500/10 hover:bg-amber-500/20 text-amber-500 text-[10px] font-black uppercase tracking-widest rounded-lg border border-amber-500/20 transition-all flex items-center gap-2"
          >
            <RefreshCw size={12} class={isDeepChecking ? "animate-spin" : ""} />
            {isDeepChecking ? "Scanning Quotas..." : "Deep Quota Scan"}
          </button>
          <button 
            onclick={resetPool}
            disabled={isResetting}
            class="h-8 px-4 bg-red-500/10 hover:bg-red-500/20 text-red-500 text-[10px] font-black uppercase tracking-widest rounded-lg border border-red-500/20 transition-all flex items-center gap-2"
          >
            <Zap size={12} class={isResetting ? "animate-pulse" : ""} />
            {isResetting ? "Purging..." : "Neural Purge"}
          </button>
        </div>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        {#each Array(8) as _, i}
          {@const k = keys.find(item => item.index === i)}
          <div class="relative group">
            <div class="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <div class="relative bg-zinc-900/40 border border-white/5 rounded-2xl p-4 flex flex-col gap-3 transition-all group-hover:border-white/10 h-full">
              <div class="flex items-center justify-between">
                <span class="text-[9px] font-mono text-zinc-600">SLOT_0{i+1}</span>
                {#if k}
                  <div class="w-1.5 h-1.5 rounded-full {k.status === 'ACTIVE' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : k.status === 'COOLDOWN' ? 'bg-amber-500' : 'bg-red-500'}"></div>
                {/if}
              </div>
              
              {#if k}
                <div class="flex flex-col gap-0.5">
                  <span class="text-[11px] font-mono text-zinc-300 truncate">{k.key_preview}</span>
                  <span class="text-[8px] font-black uppercase tracking-tighter {k.status === 'ACTIVE' ? 'text-emerald-500' : k.status === 'COOLDOWN' ? 'text-amber-500' : 'text-red-500'}">
                    {k.status}
                  </span>
                </div>
                <div class="mt-auto pt-3 border-t border-white/5 flex items-center justify-between">
                  <div class="flex flex-col">
                    <span class="text-[8px] text-zinc-600 uppercase font-black">Fails</span>
                    <span class="text-[10px] font-mono text-zinc-400">{k.fail_count}</span>
                  </div>
                  <div class="flex flex-col items-end">
                    <span class="text-[8px] text-zinc-600 uppercase font-black">Health</span>
                    <span class="text-[10px] font-mono text-zinc-400">{k.health_score}%</span>
                  </div>
                </div>
              {:else}
                <div class="flex-1 flex items-center justify-center border border-dashed border-white/5 rounded-xl">
                  <span class="text-[10px] font-black text-zinc-700 uppercase tracking-widest">Empty</span>
                </div>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>

    <!-- Waterfall Section -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-xs font-black text-white uppercase tracking-[0.2em] flex items-center gap-2">
          <Layers size={14} class="text-indigo-500" />
          Cognitive Fallback Stack (Click to Promote)
        </h3>
        <button 
          onclick={savePriority}
          disabled={isSaving || !modelStatus}
          class="h-8 px-6 bg-indigo-500 text-white text-[10px] font-black uppercase tracking-widest rounded-lg shadow-[0_0_20px_rgba(99,102,241,0.3)] hover:bg-indigo-400 transition-all disabled:opacity-50"
        >
          {isSaving ? "Syncing..." : "Save Priority to DB"}
        </button>
      </div>
      <div class="bg-black/40 border border-white/5 rounded-2xl p-1 overflow-hidden">
        <div class="flex items-center">
          {#if modelStatus}
            {#each [modelStatus.primary_model, ...modelStatus.ai_models.filter(m => m !== modelStatus?.primary_model)] as model, idx}
              <button 
                onclick={() => promoteModel(model)}
                class="flex items-center hover:bg-white/[0.02] transition-colors group/mod"
              >
                <div class="px-4 py-3 flex flex-col gap-0.5 min-w-[150px] border-r border-white/5 last:border-0">
                  <span class="text-[8px] font-black {idx === 0 ? 'text-emerald-500' : 'text-zinc-600'} uppercase tracking-widest flex items-center gap-1">
                    {#if idx === 0}<Zap size={8} />{/if}
                    Rank {idx + 1}
                  </span>
                  <span class="text-[11px] font-mono {idx === 0 ? 'text-white font-bold' : 'text-zinc-400'} group-hover/mod:text-indigo-400 transition-colors truncate">
                    {model}
                  </span>
                </div>
              </button>
            {/each}
          {:else}
            <div class="p-4 text-zinc-600 text-xs italic">Calculating cognitive flow...</div>
          {/if}
        </div>
      </div>
    </div>
  </div>

  {#snippet footer()}
    <div class="flex items-center gap-6 text-[10px] text-zinc-600 font-mono">
      <div class="flex items-center gap-2">
        <CheckCircle size={12} class="text-emerald-500" />
        <span>R00 Compliance: ACTIVE</span>
      </div>
      <div class="flex items-center gap-2">
        <AlertTriangle size={12} class="text-amber-500" />
        <span>Auto-Heal: ENABLED</span>
      </div>
    </div>
    <div class="flex-1"></div>
    <button 
      onclick={loadStats}
      class="px-6 py-2.5 bg-white/5 hover:bg-white/10 text-white text-[10px] font-black uppercase tracking-widest rounded-xl transition-all flex items-center gap-2"
    >
      <RefreshCw size={14} class={isRefreshing ? "animate-spin" : ""} />
      Refresh Telemetry
    </button>
  {/snippet}
</AdminModal>

<style>
  @reference "tailwindcss";
</style>
