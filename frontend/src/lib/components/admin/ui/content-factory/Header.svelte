<script lang="ts">
  import {
    Sparkles,
    Image as ImageIcon,
    FileText,
    ShieldCheck,
    CheckCircle,
    RotateCcw,
    Maximize2,
    Minimize2,
    Edit2,
    X
  } from "lucide-svelte";

  let { 
    viewingStep,
    status,
    progress_msg,
    campaign_id,
    isEditing = $bindable(false),
    toggleExpand,
    isExpanded
  } = $props();
</script>

<div class="flex items-center justify-between mb-5 relative z-10 {isExpanded ? 'mb-8' : ''}">
  <div class="flex items-center gap-3">
    <div
      class="p-2 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/20 shadow-inner"
    >
      {#if viewingStep === 1} <Sparkles size={16} />
      {:else if viewingStep === 2} <ImageIcon size={16} />
      {:else if viewingStep === 3} <FileText size={16} />
      {:else if viewingStep === 4} <FileText size={16} />
      {:else if viewingStep === 5} <ShieldCheck size={16} />
      {:else} <CheckCircle size={16} />
      {/if}
    </div>
    <div class="flex flex-col">
      <span class="text-[10px] uppercase font-black tracking-[0.2em] text-blue-400/80">
        Phase {viewingStep}
      </span>
      <span class="text-xs font-bold text-white/90">
        {#if viewingStep === 1}Keyword Analysis
        {:else if viewingStep === 2}Asset Hunting
        {:else if viewingStep === 3}Content Outline
        {:else if viewingStep === 4}Drafting
        {:else if viewingStep === 5}Website Publisher
        {/if}
      </span>
    </div>

    {#if status === "PROCESSING"}
      <div
        class="ml-2 flex items-center gap-1.5 px-2 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-400 animate-pulse"
      >
        <RotateCcw size={10} class="animate-spin" />
        <span class="font-medium">{progress_msg || "AI is working..."}</span>
      </div>
    {/if}
  </div>

  <div class="flex items-center gap-2 relative z-[2100]">
    <button
      onclick={toggleExpand}
      class="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-white/40 hover:text-white border border-white/5 transition-all duration-300"
      title={isExpanded ? "Collapse View" : "Expand to Neural Fullview"}
    >
      {#if isExpanded}
        <Minimize2 size={16} />
      {:else}
        <Maximize2 size={16} />
      {/if}
    </button>

  {#if status === "WAITING_FOR_REVIEW" && (viewingStep === 1 || viewingStep === 3 || viewingStep === 4)}
    <button
      onclick={() => { 
        isEditing = !isEditing; 
        if (import.meta.env.DEV) console.log("[Header] Toggle isEditing:", isEditing); 
      }}
      class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/60 hover:text-white border border-white/5 transition-all duration-300"
    >
      {#if isEditing}
        <X size={14} />
        <span class="text-xs font-semibold">Hủy</span>
      {:else}
        <Edit2 size={14} />
        <span class="text-xs font-semibold">Chỉnh sửa</span>
      {/if}
    </button>
  {/if}
  </div>
</div>
