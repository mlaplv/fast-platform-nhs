<script lang="ts">
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { vuiState } from "$lib/vui";
  import { globalLatency } from "$lib/utils/telemetry.svelte";
  import { permissionState } from "$lib/state/permissions.svelte";
  import Activity from "lucide-svelte/icons/activity";
  import Power from "lucide-svelte/icons/power";
  import Cpu from "lucide-svelte/icons/cpu";
  import ShieldAlert from "lucide-svelte/icons/shield-alert";
  import Mic from "lucide-svelte/icons/mic";

  let status = $derived(nanobot.isVuiActive ? "ACTIVE" : "IDLE");
  let themeColor = $derived(
    nanobot.isVuiActive ? "text-[#00FFFF]" : "text-gray-500",
  );

  // V45.0 — Passive latency color
  let latencyColor = $derived(
    globalLatency.ms === null
      ? "text-gray-600"
      : globalLatency.ms < 100
        ? "text-green-500"
        : globalLatency.ms < 500
          ? "text-yellow-400"
          : "text-red-500",
  );
</script>

<div
  class="flex items-center gap-3 px-2.5 py-1 bg-white/[0.03] border border-white/10 rounded-lg backdrop-blur-xl group hover:border-white/20 transition-all duration-500"
>
  <!-- Core Identity & Status -->
  <div class="flex items-center gap-2 pr-3 border-r border-white/5">
    <div class="relative">
      <Cpu size={11} class="{themeColor} transition-colors duration-500" />
      {#if nanobot.isVuiActive}
        <div
          class="absolute inset-0 bg-[#00FFFF]/20 blur-xs rounded-full animate-pulse"
        ></div>
      {/if}
    </div>
    <div class="flex flex-col -gap-1">
      <span class="text-[8px] font-mono font-bold tracking-widest {themeColor}"
        >{status}</span
      >
      <div class="flex items-center gap-1.5 opacity-60">
        <!-- V45.0: Passive Latency -->
        <span
          class="text-[10px] font-mono uppercase tracking-widest {latencyColor}"
          >PING:{globalLatency.ms !== null
            ? `${globalLatency.ms}ms`
            : "--"}</span
        >
      </div>
    </div>
  </div>

  <!-- V45.0: MIC Status LED -->
  <div class="flex items-center gap-1.5 pr-3 border-r border-white/5">
    <div
      class="flex items-center gap-1 px-1.5 py-0.5 rounded bg-black/30 border border-white/10"
    >
      {#if vuiState.phase === "listening"}
        <div class="relative flex items-center gap-1">
          <div
            class="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse shadow-[0_0_6px_rgba(74,222,128,0.6)]"
          ></div>
          <Mic size={9} class="text-green-400" />
          <span
            class="text-[10px] font-mono uppercase tracking-widest text-green-400 opacity-80"
            >LISTENING</span
          >
        </div>
      {:else}
        <div class="flex items-center gap-1">
          <div class="w-1.5 h-1.5 bg-gray-600 rounded-full"></div>
          <Mic size={9} class="text-gray-600" />
          <span
            class="text-[10px] font-mono uppercase tracking-widest text-gray-600 opacity-80"
            >IDLE</span
          >
        </div>
      {/if}
    </div>
  </div>

  <!-- Audit Mode (Conditional) -->
  {#if permissionState.hasPermission("sys:admin")}
    <div class="flex items-center gap-1.5 pr-3 border-r border-white/5">
      <div
        class="flex items-center gap-1 px-1 py-0.5 rounded bg-red-500/10 border border-red-500/20 text-red-500"
      >
        <ShieldAlert size={9} />
        <span class="text-[10px] font-mono font-bold uppercase tracking-widest"
          >AUDIT</span
        >
      </div>
    </div>
  {/if}

  <!-- Protocol Actions -->
  <nav class="flex items-center gap-3">
    <button
      onclick={() => nanobot.processCommand("manage skills", "text")}
      title="Management Protocol"
      class="flex items-center gap-1 group/link cursor-pointer"
    >
      <Activity
        size={10}
        class="text-gray-600 group-hover/link:text-[#00FFFF] transition-colors"
      />
      <span
        class="text-[10px] font-mono uppercase tracking-widest text-gray-500 group-hover/link:text-gray-300 transition-colors opacity-80"
        >Skills</span
      >
    </button>

    <button
      onclick={() => nanobot.voice.hard_sleep()}
      title="Terminate Session"
      class="flex items-center gap-1 group/link cursor-pointer"
    >
      <Power
        size={10}
        class="text-gray-600 group-hover/link:text-red-500 transition-colors"
      />
      <span
        class="text-[10px] font-mono uppercase tracking-widest text-gray-400 group-hover/link:text-gray-200 transition-colors underline decoration-gray-700 opacity-80"
        >Halt</span
      >
    </button>
  </nav>
</div>
