<script lang="ts">
  import { ScanFace } from "lucide-svelte";
  import { onMount } from "svelte";

  let {
    greetingTemplate = $bindable(),
    farewellTemplate = $bindable()
  } = $props<{
    greetingTemplate: string;
    farewellTemplate: string;
  }>();

  onMount(() => {
    if (greetingTemplate === undefined) greetingTemplate = "";
    if (farewellTemplate === undefined) farewellTemplate = "";
  });
</script>

<div class="bg-black/40 backdrop-blur-md border border-white/10 rounded-[2.5rem] p-6 sm:p-10 shadow-2xl relative overflow-hidden">
  <div class="absolute top-0 right-0 w-96 h-96 bg-purple-500/5 blur-[120px] rounded-full -translate-y-1/2 translate-x-1/2"></div>
  
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-6 mb-12">
    <div class="flex items-center gap-4 text-purple-400">
      <div class="p-3 bg-purple-500/10 rounded-2xl ring-1 ring-purple-500/20">
        <ScanFace size={24} />
      </div>
      <h2 class="text-lg font-bold tracking-tight uppercase">Neural Identity Protocols</h2>
    </div>
    
    <div class="flex items-center gap-4 px-6 py-3 bg-zinc-900 ring-1 ring-white/10 rounded-2xl w-full sm:w-auto justify-between sm:justify-start">
      <div class="flex items-center gap-2">
        <div class="w-2 h-2 rounded-full bg-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.5)]"></div>
        <span class="text-[10px] font-mono text-zinc-500 font-bold uppercase tracking-widest">Active ID: X-900</span>
      </div>
      <div class="w-px h-4 bg-zinc-800 hidden sm:block"></div>
      <span class="text-[10px] font-mono text-zinc-400">PROBABILISTIC_MATCH: 99.8%</span>
    </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-10">
    <!-- GREETING -->
    <div class="space-y-6">
      <div class="flex items-center gap-3">
        <div class="w-1.5 h-1.5 rounded-full bg-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.5)]"></div>
        <span class="text-[11px] font-mono text-zinc-500 uppercase tracking-[0.3em]">Engagement Protocol (Greeting)</span>
      </div>
      <div class="relative group">
        <div class="absolute -inset-1 bg-purple-500/10 rounded-[2rem] blur opacity-0 group-hover:opacity-100 transition-all duration-500"></div>
        <textarea
          bind:value={greetingTemplate}
          class="w-full relative h-48 bg-zinc-900/50 border border-white/10 rounded-[2rem] p-6 sm:p-8 text-sm font-sans leading-relaxed text-zinc-300 outline-none focus:border-purple-500/40 focus:bg-zinc-900 transition-all duration-500 custom-scrollbar resize-none"
        ></textarea>
      </div>
    </div>

    <!-- FAREWELL -->
    <div class="space-y-6">
      <div class="flex items-center gap-3">
        <div class="w-1.5 h-1.5 rounded-full bg-cyan-500 shadow-[0_0_8px_rgba(34,211,238,0.5)]"></div>
        <span class="text-[11px] font-mono text-zinc-500 uppercase tracking-[0.3em]">Disengagement Identity (Farewell)</span>
      </div>
      <div class="relative group">
        <div class="absolute -inset-1 bg-cyan-500/10 rounded-[2rem] blur opacity-0 group-hover:opacity-100 transition-all duration-500"></div>
        <textarea
          bind:value={farewellTemplate}
          class="w-full relative h-48 bg-zinc-900/50 border border-white/10 rounded-[2rem] p-6 sm:p-8 text-sm font-sans leading-relaxed text-zinc-300 outline-none focus:border-cyan-500/40 focus:bg-zinc-900 transition-all duration-500 custom-scrollbar resize-none"
        ></textarea>
      </div>
    </div>
  </div>
</div>
