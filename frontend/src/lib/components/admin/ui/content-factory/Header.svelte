<script lang="ts">
  import {
    Sparkles, Image as ImageIcon, FileText, Check, Rocket,
    RotateCcw, Pencil, X, Terminal, ChevronDown
  } from "lucide-svelte";
  import SupremeCloseButton from "../SupremeCloseButton.svelte";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import { fade, scale } from "svelte/transition";
  import { vuiController } from "$lib/vui";
  import { onMount } from "svelte";

  interface Props {
    viewingStep: number;
    step?: number;
    status: string;
    progress_msg?: string;
    campaign_id: string;
    isEditing: boolean;
    toggleExpand: () => void;
    isExpanded: boolean;
    creation_config?: Record<string, unknown>;
  }

  let {
    viewingStep = $bindable(),
    step = 1,
    status,
    progress_msg,
    campaign_id,
    isEditing = $bindable(),
    toggleExpand,
    isExpanded,
    creation_config = {}
  }: Props = $props();

  onMount(() => {
    if (viewingStep === undefined) viewingStep = 1;
    if (isEditing === undefined) isEditing = false;
  });
  let isMenuOpen = $state(false);
  let holdProgress = $state(0);
  let isHardKillReady = $state(false);

  const PHASES = [
    { s: 1, icon: Sparkles, label: "Ý tưởng", desc: "Brainstorming" },
    { s: 2, icon: ImageIcon, label: "Hình ảnh", desc: "Asset Hunt" },
    { s: 3, icon: FileText, label: "Dàn bài", desc: "Architecture" },
    { s: 4, icon: FileText, label: "Nội dung", desc: "Creative Pen" },
    { s: 5, icon: Check, label: "Kiểm tra", desc: "Plagiarism Cop" },
    { s: 6, icon: Rocket, label: "Xuất bản", desc: "Media & SEO" }
  ];

  let stepNames: Record<number, string> = {
    1: "Keyword Analysis",
    2: "Asset Hunting",
    3: "Content Outline",
    4: "Drafting",
    5: "Plagiarism Check",
    6: "Website Publisher"
  };

  let subtitle = $derived.by(() => {
    let base = "NEURAL XOHI · TRINITY CORE";
    const stepName = stepNames[viewingStep] || "Processing";
    const style = creation_config?.style || '';
    const wc = creation_config?.word_count ? `${creation_config.word_count} từ` : '';
    const extras = [style, wc].filter(Boolean).join('  ');
    
    if (extras) {
      return `${base} -> ${stepName}  ${extras}`;
    }
    return `${base} -> ${stepName}`;
  });
</script>

<div class="flex w-full items-center justify-between px-5 py-3 border-b border-cyan-500/20 bg-black md:bg-black/80 md:backdrop-blur-md shrink-0 relative z-[500] transition-all duration-500 {isExpanded ? 'mb-4' : ''}">
  <div class="flex items-center gap-4">
    <div class="relative">
      <button 
        onclick={() => isMenuOpen = !isMenuOpen}
        class="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center hover:bg-cyan-500/20 hover:scale-105 active:scale-95 transition-all shadow-[0_0_20px_rgba(34,211,238,0.15)] group"
      >
        <Terminal class="w-5 h-5 text-cyan-400 group-hover:rotate-12 transition-transform" />
        <div class="absolute -bottom-1 -right-1 w-4 h-4 bg-black rounded-full flex items-center justify-center border border-cyan-500/30">
          <ChevronDown class="w-3 h-3 text-cyan-400 {isMenuOpen ? 'rotate-180' : ''} transition-transform" />
        </div>
      </button>

      {#if isMenuOpen}
        <!-- Backdrop to close menu -->
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div class="fixed inset-0 z-[40000]" onclick={() => isMenuOpen = false}></div>

        <div 
          class="absolute top-14 left-0 w-64 bg-slate-900/95 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] overflow-hidden z-[50000]"
          transition:scale={{ start: 0.95, duration: 200 }}
        >
          <div class="px-4 py-3 border-b border-white/5 bg-white/5">
            <span class="text-[10px] font-black uppercase tracking-widest text-cyan-400">Điều hướng Phase</span>
          </div>
          <div class="p-2 space-y-1">
            {#each PHASES as phase}
              {@const isUnlocked = phase.s <= step}
              {@const isCurrent = phase.s === viewingStep}
              <button
                disabled={!isUnlocked}
                onclick={() => {
                  viewingStep = phase.s;
                  isEditing = false;
                  isMenuOpen = false;
                  vuiController.speak(`Đã chuyển sang bước ${phase.label}.`);
                }}
                class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-300 disabled:opacity-30 disabled:cursor-not-allowed group/item {isCurrent ? 'bg-cyan-500/20 text-cyan-300 shadow-[inset_0_1px_rgba(255,255,255,0.1)]' : 'text-white/70 hover:bg-white/5'}"
              >
                <div class="w-8 h-8 rounded-full border flex items-center justify-center shrink-0 transition-transform group-hover/item:scale-110 {isCurrent ? 'bg-cyan-500/20 border-cyan-500/30 text-cyan-400' : 'bg-white/5 border-white/10'}">
                  <phase.icon size={14} />
                </div>
                <div class="flex flex-col flex-1">
                  <span class="text-xs font-bold">{phase.label}</span>
                  <span class="text-[9px] opacity-60 uppercase tracking-wider font-mono">Phase 0{phase.s} - {phase.desc}</span>
                </div>
                {#if isCurrent}
                  <Pencil size={9} class="text-white/10 group-hover:text-blue-400" />
                {/if}
              </button>
            {/each}
          </div>
        </div>
      {/if}
    </div>
    
    <div>
      <h2 class="text-xs font-mono tracking-[0.15em] uppercase text-cyan-400 font-bold">
        PHASE {viewingStep}
      </h2>
      <p class="text-[9px] font-mono text-gray-500 uppercase tracking-wider hidden md:block">
        {subtitle}
      </p>
    </div>
  </div>

  <div class="flex items-center gap-3 relative z-[2100]">
    <!-- Edit Button Moved Up to Header -->
    {#if status !== "PROCESSING" && (viewingStep === 1 || viewingStep === 3 || viewingStep === 4)}
      <button
        onclick={() => { isEditing = !isEditing; }}
        class="flex items-center gap-2 px-3 py-1.5 rounded-lg border {isEditing ? 'bg-white/10 border-white/20 text-white' : 'bg-blue-500/10 border-blue-500/30 text-blue-400 hover:bg-blue-500/20'} transition-all duration-300"
      >
        {#if isEditing}
          <X size={14} />
          <span class="text-xs font-semibold">Hủy</span>
        {:else}
          <Pencil size={14} />
          <span class="text-xs font-semibold">Chỉnh sửa</span>
        {/if}
      </button>
    {/if}
    
    <!-- Modal Close Button (Supreme Power) -->
    <SupremeCloseButton {campaign_id} />
  </div>
</div>
