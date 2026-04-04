<script lang="ts">
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import Database from "lucide-svelte/icons/database";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import History from "lucide-svelte/icons/history";
  import ShieldCheck from "lucide-svelte/icons/shield-check";

  import { onMount } from "svelte";

  let { chatSettings = $bindable() } = $props();

  onMount(() => {
    if (chatSettings === undefined) chatSettings = {};
  });

  const options = [
    {
      id: "selective_persistence",
      label: "Selective Persistence",
      desc: "Only save critical messages (User requests, Voice commands) to Database. Highly recommended.",
      icon: ShieldCheck,
      color: "text-emerald-400"
    },
    {
      id: "save_ai_responses",
      label: "Save AI Responses",
      desc: "Save every single AI text response to DB. Turn OFF to save storage and prevent DB bloat.",
      icon: Database,
      color: "text-blue-400"
    }
  ];

  const numericSettings = [
    {
      id: "auto_purge_days",
      label: "Auto-Purge Cycle",
      desc: "Automatic deletion of ephemeral chat logs after N days.",
      unit: "Days",
      icon: Trash2
    },
    {
      id: "cache_limit",
      label: "Redis Cache Limit",
      desc: "Number of recent messages to keep in ultra-fast memory.",
      unit: "Msgs",
      icon: History
    }
  ];
</script>

<div class="space-y-6">
  <div class="flex items-center gap-3">
    <div class="p-2 bg-cyan-500/10 rounded-lg">
      <Database size={18} class="text-cyan-400" />
    </div>
    <div>
      <h3 class="text-sm font-bold text-white uppercase tracking-wider">Resource Discipline</h3>
      <p class="text-[10px] text-zinc-500 font-mono">Chat Persistence & Storage Governance</p>
    </div>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    {#each options as opt}
      <div 
        class="flex items-start gap-4 p-4 rounded-2xl border transition-all text-left
               {chatSettings[opt.id] 
                 ? 'bg-cyan-500/5 border-cyan-500/20 shadow-[0_4px_20px_rgba(8,145,178,0.1)]' 
                 : 'bg-white/[0.02] border-white/5'}"
      >
        <div class="p-2 rounded-xl {chatSettings[opt.id] ? 'bg-cyan-500/20 ' + opt.color : 'bg-white/5 text-zinc-500'} transition-colors">
          <opt.icon size={20} />
        </div>
        <div class="flex-1 space-y-1 min-w-0">
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2 min-w-0">
              <span class="text-xs font-bold uppercase tracking-tight {chatSettings[opt.id] ? 'text-cyan-400' : 'text-zinc-400'}">{opt.label}</span>
            </div>
            <!-- Toggle Switch -->
            <button
              onclick={() => chatSettings[opt.id] = !chatSettings[opt.id]}
              class="relative flex-shrink-0 w-10 h-[22px] rounded-full transition-colors duration-200 ease-in-out focus:outline-none
                     {chatSettings[opt.id] ? 'bg-cyan-500/80' : 'bg-zinc-700'}"
              role="switch"
              aria-checked={chatSettings[opt.id]}
            >
              <span 
                class="absolute top-[3px] left-[3px] w-4 h-4 rounded-full bg-white shadow transition-transform duration-200 ease-in-out
                       {chatSettings[opt.id] ? 'translate-x-[18px]' : 'translate-x-0'}"
              ></span>
            </button>
          </div>
          <p class="text-[10px] leading-relaxed text-zinc-500">{opt.desc}</p>
        </div>
      </div>
    {/each}
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    {#each numericSettings as n}
      <div class="p-4 rounded-2xl bg-white/[0.02] border border-white/5 space-y-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <n.icon size={16} class="text-zinc-500" />
            <span class="text-[10px] font-bold uppercase text-zinc-400 tracking-wider">{n.label}</span>
          </div>
          <div class="flex items-center gap-2 bg-black/40 px-2 py-1 rounded-lg border border-white/5">
            <input 
              type="number" 
              bind:value={chatSettings[n.id]}
              class="w-12 bg-transparent border-none text-xs font-mono text-cyan-400 focus:ring-0 p-0 text-center"
            />
            <span class="text-[8px] text-zinc-600 font-bold uppercase">{n.unit}</span>
          </div>
        </div>
        <p class="text-[9px] text-zinc-500 leading-tight italic">{n.desc}</p>
      </div>
    {/each}
  </div>
</div>
