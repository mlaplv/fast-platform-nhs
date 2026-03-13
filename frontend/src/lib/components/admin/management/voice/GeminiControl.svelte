<script lang="ts">
  import { apiClient } from "$lib/utils/apiClient";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import Cpu from "lucide-svelte/icons/cpu";
  import Activity from "lucide-svelte/icons/activity";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";

  let { onOpenDiagnostics } = $props<{
    onOpenDiagnostics: () => void;
  }>();

  let bulkKeys = $state("");
  let isSyncing = $state(false);

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
        bulkKeys = ""; // Clear after success
      } else {
        nanobot.showToast(res?.message || "Failed to sync keys.", "error");
      }
    } catch (e) {
      nanobot.showToast("Link Failure: Could not reach Admin AI API.", "error");
    } finally {
      isSyncing = false;
    }
  }
</script>

<div class="bg-zinc-950/40 border border-white/5 rounded-xl p-5 space-y-4">
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

  <div class="space-y-2">
    <label class="block text-[10px] text-zinc-500 font-bold uppercase tracking-wider">
      Bulk Key Entry (Comma-Separated)
    </label>
    <textarea
      bind:value={bulkKeys}
      placeholder="Paste AIzaSy... keys here, separated by commas"
      class="w-full h-24 bg-black/50 border border-white/5 rounded-lg p-3 text-xs font-mono text-zinc-300 focus:outline-none focus:border-emerald-500/30 transition-all resize-none"
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
