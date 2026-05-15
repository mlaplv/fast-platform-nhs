<script lang="ts">
  import { onMount } from "svelte";
  import Mic from "@lucide/svelte/icons/mic";
  import Zap from "@lucide/svelte/icons/zap";
  import Plus from "@lucide/svelte/icons/plus";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Moon from "@lucide/svelte/icons/moon";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();

  let {
    wakeTriggers = $bindable(),
    sleepTriggers = $bindable(),
    onStartTraining,
  } = $props<{
    wakeTriggers: string[];
    sleepTriggers: string[];
    onStartTraining: (type: "wake" | "sleep") => void;
  }>();

  onMount(() => {
    if (wakeTriggers === undefined) wakeTriggers = [];
    if (sleepTriggers === undefined) sleepTriggers = [];
  });

  let editingWake = $state<number | null>(null);
  let editingSleep = $state<number | null>(null);

  function addWakeWord() {
    wakeTriggers = [...wakeTriggers, ""];
  }
  function addSleepWord() {
    sleepTriggers = [...sleepTriggers, ""];
  }
  function removeWakeWord(index: number) {
    wakeTriggers = wakeTriggers.filter((_, i) => i !== index);
  }
  function removeSleepWord(index: number) {
    sleepTriggers = sleepTriggers.filter((_, i) => i !== index);
  }
</script>

<div
  class="bg-black/40 backdrop-blur-md border border-white/10 rounded-[2.5rem] p-8 flex flex-col shadow-2xl min-h-[420px] max-h-[600px] transition-all"
>
  <div class="flex items-center justify-between mb-6">
    <div class="flex items-center gap-4 text-cyan-400">
      <div class="p-3 bg-cyan-500/10 rounded-2xl ring-1 ring-cyan-500/20">
        <Mic size={24} />
      </div>
      <h2 class="text-lg font-bold tracking-tight ">Core Triggers</h2>
    </div>
    <div class="px-4 py-2 bg-zinc-900 ring-1 ring-white/10 rounded-xl">
      <span
        class="text-[10px] font-mono text-zinc-500 font-bold tracking-widest"
        >TIER 1 SYSTEM</span
      >
    </div>
  </div>

  <div class="space-y-10 flex-1 overflow-y-auto custom-scrollbar pr-3">
    <!-- WAKE WORDS -->
    <div class="space-y-5">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div
            class="w-1.5 h-1.5 rounded-full bg-cyan-500 shadow-[0_0_8px_rgba(34,211,238,0.5)]"
          ></div>
          <span
            class="text-[11px] font-mono text-zinc-500 tracking-[0.2em]"
            >Activation Protocol (Wake)</span
          >
        </div>
        <button
          onclick={() => onStartTraining("wake")}
          class="flex items-center gap-2 px-3 py-1.5 rounded-full border border-cyan-500/20 text-[10px] font-mono text-cyan-500/60 hover:text-cyan-400 hover:bg-cyan-500/5 transition-all {nanobot.isTraining &&
          nanobot.trainingType === 'wake'
            ? 'bg-cyan-500/10 text-cyan-400 animate-pulse ring-1 ring-cyan-500/40'
            : ''}"
        >
          <Zap size={10} />
          NEURAL CAPTURE
        </button>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-2">
        {#each wakeTriggers as word, i}
          <div
            class="group relative h-8 px-3 bg-zinc-800/40 hover:bg-zinc-800/60 text-zinc-300 border border-white/5 rounded-lg flex items-center justify-center transition-all ring-1 ring-white/5 hover:ring-cyan-500/20 animate-in overflow-hidden"
          >
            {#if editingWake === i}
              <input
                bind:value={wakeTriggers[i]}
                onblur={() => (editingWake = null)}
                onkeydown={(e) => e.key === "Enter" && (editingWake = null)}
                class="bg-transparent outline-none text-[10px] font-mono text-cyan-400 w-full min-w-[3rem]"
                autofocus
              />
            {:else}
              <button
                onclick={() => (editingWake = i)}
                class="text-[10px] font-mono tracking-wide leading-none truncate"
                >{word || "---"}</button
              >
            {/if}
            <button
              onclick={() => removeWakeWord(i)}
              class="absolute right-1 opacity-0 group-hover:opacity-100 transition-all text-zinc-700 hover:text-red-400 bg-zinc-950/80 rounded p-0.5"
            >
              <Trash2 size={10} />
            </button>
          </div>
        {/each}
        <button
          onclick={addWakeWord}
          class="w-8 h-8 border border-dashed border-white/10 rounded-full flex items-center justify-center text-zinc-700 hover:text-cyan-400 hover:border-cyan-500/40 hover:bg-cyan-500/5 transition-all active:scale-95"
        >
          <Plus size={18} />
        </button>
      </div>
    </div>

    <!-- SLEEP WORDS -->
    <div class="space-y-5">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div
            class="w-1.5 h-1.5 rounded-full bg-red-500/60 shadow-[0_0_8px_rgba(239,68,68,0.5)]"
          ></div>
          <span
            class="text-[11px] font-mono text-zinc-500 tracking-[0.2em]"
            >Termination Protocol (Sleep)</span
          >
        </div>
        <button
          onclick={() => onStartTraining("sleep")}
          class="flex items-center gap-2 px-3 py-1.5 rounded-full border border-red-500/20 text-[10px] font-mono text-red-500/60 hover:text-red-400 hover:bg-red-500/5 transition-all {nanobot.isTraining &&
          nanobot.trainingType === 'sleep'
            ? 'bg-red-500/10 text-red-400 animate-pulse ring-1 ring-red-500/40'
            : ''}"
        >
          <Moon size={10} />
          NEURAL CAPTURE
        </button>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-2">
        {#each sleepTriggers as word, i}
          <div
            class="group relative h-8 px-3 bg-zinc-800/40 hover:bg-zinc-800/60 text-zinc-300 border border-white/5 rounded-lg flex items-center justify-center transition-all ring-1 ring-white/5 hover:ring-red-500/20 animate-in overflow-hidden"
          >
            {#if editingSleep === i}
              <input
                bind:value={sleepTriggers[i]}
                onblur={() => (editingSleep = null)}
                onkeydown={(e) => e.key === "Enter" && (editingSleep = null)}
                class="bg-transparent outline-none text-[10px] font-mono text-red-400 w-full min-w-[3rem]"
                autofocus
              />
            {:else}
              <button
                onclick={() => (editingSleep = i)}
                class="text-[10px] font-mono tracking-wide leading-none truncate"
                >{word || "---"}</button
              >
            {/if}
            <button
              onclick={() => removeSleepWord(i)}
              class="absolute right-1 opacity-0 group-hover:opacity-100 transition-all text-zinc-700 hover:text-red-400 bg-zinc-950/80 rounded p-0.5"
            >
              <Trash2 size={10} />
            </button>
          </div>
        {/each}
        <button
          onclick={addSleepWord}
          class="w-8 h-8 border border-dashed border-white/10 rounded-full flex items-center justify-center text-zinc-700 hover:text-red-500 hover:border-red-500/40 hover:bg-red-500/5 transition-all active:scale-95"
        >
          <Plus size={18} />
        </button>
      </div>
    </div>
  </div>
</div>
