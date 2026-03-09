<script lang="ts">
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { fade } from "svelte/transition";
  import { apiClient } from "$lib/utils/apiClient";
  import MissionControlShell from "./ui/MissionControlShell.svelte";
  import ShieldAlert from "lucide-svelte/icons/shield-alert";
  import Check from "lucide-svelte/icons/check";
  import X from "lucide-svelte/icons/x";
  import Search from "lucide-svelte/icons/search";

  let analysis = $state<any>(null);
  let isAuditing = $state(false);

  $effect(() => {
    const currentPending = nanobot.pendingApprovals[0];
    if (currentPending && currentPending.draftId && !analysis && !isAuditing) {
      runAudit(currentPending.draftId);
    } else if (!currentPending) {
      analysis = null;
    }
  });

  async function runAudit(draftId: string) {
    isAuditing = true;
    try {
      analysis = await apiClient.get<any>(`/api/v1/auditor/${draftId}/analyze`);
    } catch (e) {
      console.error("Audit failed", e);
    } finally {
      isAuditing = false;
    }
  }
</script>

{#if nanobot.pendingApprovals.length > 0}
  <MissionControlShell
    title="Security Gateway"
    variant="red"
    isOpen={nanobot.pendingApprovals.length > 0}
    onClose={() => nanobot.denyAction(nanobot.pendingApprovals[0].id)}
    headerIcon={ShieldAlert}
    maxWidth="max-w-2xl"
    height="h-auto"
  >
    <div class="p-10 relative">
      <!-- Intent Origin -->
      <div class="mb-10 relative">
        <div
          class="text-[9px] text-white/40 font-mono uppercase tracking-[0.4em] mb-4 flex items-center gap-2"
        >
          <div class="w-1.5 h-1.5 bg-alert-red animate-ping rounded-full"></div>
          Origin: Agentic_Orchestrator
        </div>
        <div
          class="bg-white/[0.02] border-l-2 border-alert-red p-6 shadow-inner relative group"
        >
          <div
            class="absolute inset-0 bg-alert-red/[0.02] opacity-0 group-hover:opacity-100 transition-opacity"
          ></div>
          <p
            class="text-gray-300 text-base leading-relaxed font-light tracking-wide italic"
          >
            "{nanobot.pendingApprovals[0].description}"
          </p>
        </div>
      </div>

      <!-- Auditor Analysis -->
      <div class="relative">
        <div class="flex items-center justify-between mb-6">
          <div
            class="text-[10px] text-[#00FFFF] font-mono uppercase tracking-[0.4em] flex items-center gap-3"
          >
            <Search
              size={16}
              class={isAuditing
                ? "animate-spin text-neon-cyan"
                : "text-neon-cyan/60"}
            />
            Diagnostic Intelligence
          </div>
          {#if analysis}
            <div
              class="px-3 py-1 bg-alert-red/10 border border-alert-red/20 rounded-md"
            >
              <span
                class="text-[10px] font-mono font-bold {analysis.risk_score > 70
                  ? 'text-alert-red animate-pulse'
                  : 'text-hacker-green'}"
              >
                RISK_SCORE: {analysis.risk_score}%
              </span>
            </div>
          {/if}
        </div>

        <div
          class="bg-neon-cyan/[0.03] border border-neon-cyan/10 p-8 relative overflow-hidden"
        >
          {#if isAuditing}
            <div
              class="flex flex-col items-center justify-center py-8 space-y-6"
            >
              <div class="w-full h-[2px] bg-white/5 relative overflow-hidden">
                <div
                  class="h-full bg-neon-cyan absolute inset-0 animate-progress-loading shadow-[0_0_10px_rgba(0,255,255,0.5)]"
                ></div>
              </div>
              <span
                class="text-[11px] font-mono text-neon-cyan/60 animate-pulse tracking-[0.5em] uppercase"
                >Booting Diagnostics...</span
              >
            </div>
          {:else if analysis}
            <div in:fade={{ duration: 400 }}>
              <div class="flex items-center gap-4 mb-6">
                <div
                  class="w-2 h-2 rounded-full {analysis.impact_level ===
                  'CRITICAL'
                    ? 'bg-alert-red animate-ping'
                    : 'bg-hacker-green'}"
                ></div>
                <span
                  class="text-xs font-mono font-bold tracking-[0.3em] {analysis.impact_level ===
                  'CRITICAL'
                    ? 'text-alert-red'
                    : 'text-white'}"
                >
                  IMPACT_LEVEL: {analysis.impact_level}
                </span>
              </div>
              <ul class="space-y-3 mb-8">
                {#each analysis.insights as insight}
                  <li
                    class="text-xs text-neon-cyan/80 font-mono flex items-start gap-3 group/insight"
                  >
                    <span
                      class="text-neon-cyan group-hover:translate-x-1 transition-transform"
                      >0x_ACK</span
                    >
                    <span
                      class="text-gray-400 group-hover:text-white transition-colors"
                      >{insight}</span
                    >
                  </li>
                {/each}
              </ul>
              <div class="pt-6 border-t border-neon-cyan/10">
                <span
                  class="text-[9px] font-mono text-white/30 uppercase tracking-widest block mb-2"
                  >Primary Recommendation:</span
                >
                <div
                  class="text-sm font-mono text-neon-cyan font-bold tracking-wide"
                >
                  {analysis.recommendation}
                </div>
              </div>
            </div>
          {:else}
            <div class="flex flex-col items-center py-6">
              <div class="w-8 h-1 bg-white/10 animate-pulse mb-4"></div>
              <p
                class="text-[11px] text-gray-600 font-mono italic tracking-widest uppercase"
              >
                Awaiting diagnostic sequence...
              </p>
            </div>
          {/if}
        </div>
      </div>

      <!-- Actions Integration -->
      <div class="mt-10 flex gap-4">
        <button
          onclick={() => nanobot.denyAction(nanobot.pendingApprovals[0].id)}
          disabled={isAuditing}
          class="flex-1 py-5 bg-[#1a0000] hover:bg-alert-red/20 text-alert-red/60 hover:text-alert-red border border-alert-red/20 font-mono font-bold tracking-[0.4em] text-xs transition-all flex items-center justify-center gap-3 group disabled:opacity-30"
        >
          <X
            size={18}
            class="group-hover:rotate-90 transition-transform duration-500"
          />
          TERMINATE_INTENT
        </button>
        <button
          onclick={() => nanobot.approveAction(nanobot.pendingApprovals[0].id)}
          disabled={isAuditing}
          class="flex-1 py-5 bg-alert-red/10 hover:bg-alert-red text-alert-red hover:text-white border border-alert-red/40 hover:border-white/20 font-mono font-bold tracking-[0.4em] text-xs transition-all duration-500 flex items-center justify-center gap-3 shadow-[0_0_40px_rgba(255,0,0,0.1)] hover:shadow-[0_0_80px_rgba(255,0,0,0.4)] disabled:opacity-30 relative overflow-hidden group"
        >
          <!-- Dynamic Glow Effect -->
          <div
            class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"
          ></div>
          <Check size={20} />
          COMMIT_EXECUTION
        </button>
      </div>

      <div class="mt-8 flex justify-between items-center opacity-30">
        <div class="flex items-center gap-2">
          <div class="w-1.5 h-1.5 bg-hacker-green rounded-full"></div>
          <span
            class="text-[8px] text-white font-mono uppercase tracking-[0.3em]"
            >Encrypted Session Active</span
          >
        </div>
        <span class="text-[8px] text-neon-cyan font-mono italic">
          Node: {analysis?.audited_by || "Xohi_Global_Sec_Node_04"}
        </span>
      </div>
    </div>
  </MissionControlShell>
{/if}

<style>
  @keyframes progress-loading {
    0% {
      left: -100%;
      width: 30%;
    }
    50% {
      left: 40%;
      width: 60%;
    }
    100% {
      left: 100%;
      width: 30%;
    }
  }
  .animate-progress-loading {
    animation: progress-loading 2s infinite ease-in-out;
  }
</style>
