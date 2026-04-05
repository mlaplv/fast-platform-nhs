<script lang="ts">
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import Sparkles from "lucide-svelte/icons/sparkles";
  import Image from "lucide-svelte/icons/image";
  import FileText from "lucide-svelte/icons/file-text";
  import ShieldCheck from "lucide-svelte/icons/shield-check";
  import CheckCircle from "lucide-svelte/icons/check-circle";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import Play from "lucide-svelte/icons/play";
  import BarChart3 from "lucide-svelte/icons/bar-chart-3";
  import Clock from "lucide-svelte/icons/clock";
  import Megaphone from "lucide-svelte/icons/megaphone";
  import Loader2 from "lucide-svelte/icons/loader-2";
  import type { CampaignData } from "$lib/state/types";
  import type { Component } from "svelte";

  let { 
    campaign, 
    onAction, 
    onDelete, 
    isDeleting,
    isSelected = false,
    onToggleSelection
  } = $props<{
    campaign: CampaignData;
    onAction: (campaign: CampaignData) => void;
    onDelete: (id: string) => void;
    isDeleting: boolean;
    isSelected?: boolean;
    onToggleSelection?: (id: string) => void;
  }>();

  const STEP_LABELS: Record<number, { label: string; icon: Component }> = {
    1: { label: "Phân tích từ khóa", icon: Sparkles as unknown as Component },
    2: { label: "Săn ảnh", icon: Image as unknown as Component },
    3: { label: "Lập dàn ý", icon: FileText as unknown as Component },
    4: { label: "Soạn bản thảo", icon: FileText as unknown as Component },
    5: { label: "Kiểm tra đạo văn", icon: ShieldCheck as unknown as Component },
    6: { label: "Hoàn thiện & Xuất bản", icon: CheckCircle as unknown as Component }
  };

  const CAT_CONFIG: Record<string, { label: string; color: string; icon: Component; border: string }> = {
    CREATIVE_CONTENT: { 
      label: "CREATIVE", 
      color: "text-purple-400", 
      border: "border-purple-500/30",
      icon: Sparkles as unknown as Component
    },
    AD_MANAGEMENT: { 
      label: "AD_OPS", 
      color: "text-orange-400", 
      border: "border-orange-500/30",
      icon: BarChart3 as unknown as Component
    }
  };

  const STATUS_CONFIG: Record<string, { label: string; color: string; border: string; pulse?: boolean }> = {
    PROCESSING: { label: "PROCESSING", color: "text-amber-400", border: "border-amber-500/30", pulse: true },
    WAITING_FOR_REVIEW: { label: "REVIEWED", color: "text-blue-400", border: "border-blue-500/30" },
    COMPLETED: { label: "STABLE", color: "text-green-400", border: "border-green-500/30" },
    ERROR: { label: "FAILED", color: "text-red-400", border: "border-red-500/30" },
    REJECTED: { label: "ABORTED", color: "text-gray-500", border: "border-gray-500/20" }
  };

  function formatTime(iso: string): string {
    const date = new Date(iso);
    return date.toLocaleString("vi-VN", {
      hour: "2-digit",
      minute: "2-digit",
      day: "2-digit",
      month: "2-digit"
    });
  }

  const status = $derived(STATUS_CONFIG[campaign.status] || { label: campaign.status, color: "text-gray-400", border: "border-gray-500/20" });
  const cat = $derived(CAT_CONFIG[campaign.category] || { label: "GENERAL", color: "text-gray-400", border: "border-gray-500/20", icon: Megaphone as unknown as Component });
  const step = $derived(campaign.current_step || 1);
  const stepInfo = $derived(STEP_LABELS[step] || { label: "Neutral Zone", icon: Sparkles as unknown as Component });
</script>

<div
  class="campaign-item group flex flex-col md:flex-row items-stretch md:items-center gap-6 p-5 bg-[#0a0a0a] border {isSelected ? 'border-neon-cyan/40 shadow-[0_0_20px_rgba(0,255,255,0.05)]' : 'border-white/5'} hover:border-white/10 rounded-2xl transition-all duration-300 relative"
>
  <!-- Multi-select Checkbox (Phase 5) -->
  <div class="flex items-center pl-1 pr-1">
    <button 
      onclick={() => onToggleSelection?.(campaign.id)}
      class="w-5 h-5 rounded-md border-2 transition-all flex items-center justify-center
        {isSelected ? 'bg-neon-cyan border-neon-cyan' : 'border-white/10 bg-white/[0.02] group-hover:border-white/20'}"
    >
      {#if isSelected}
        <CheckCircle size={14} class="text-black" strokeWidth={3} />
      {/if}
    </button>
  </div>

  <!-- Main Grid Layout -->
  <div class="flex items-center gap-5 flex-1 min-w-0">
    <!-- Visual Core (Icon) -->
    <div
      class="w-14 h-14 rounded-xl bg-black border {cat.border} flex items-center justify-center shrink-0 group-hover:scale-105 transition-all
        {isSelected ? 'border-neon-cyan/30 bg-neon-cyan/5' : ''}"
    >
      <cat.icon size={24} class="{cat.color} opacity-70 group-hover:opacity-100 transition-opacity" />
    </div>

    <!-- Data Nexus -->
    <div class="flex-1 min-w-0">
      <div class="flex items-center gap-2 mb-2">
        <!-- Category Badge -->
        <div class="px-2 py-0.5 rounded border {cat.border} bg-white/[0.02] flex items-center gap-1.5 shrink-0">
          <cat.icon size={10} class={cat.color} />
          <span class="text-[9px] font-mono font-black tracking-widest uppercase {cat.color}">{cat.label}</span>
        </div>
        
        <!-- Status Badge -->
        <div class="px-2 py-0.5 rounded border {status.border} bg-white/[0.02] flex items-center gap-1.5 shrink-0 {status.pulse ? 'animate-pulse' : ''}">
           <div class="w-1 h-1 rounded-full bg-current {status.color}"></div>
           <span class="text-[9px] font-mono font-black tracking-widest uppercase {status.color}">{status.label}</span>
        </div>

        <div class="h-3 w-px bg-white/5 mx-1 hidden sm:block"></div>
        
        <div class="hidden sm:flex items-center gap-1.5 opacity-40 group-hover:opacity-60 transition-opacity">
           <Clock size={10} class="text-gray-400" />
           <span class="text-[9px] font-mono text-gray-500 uppercase">{formatTime(campaign.created_at)}</span>
        </div>
      </div>

      <h4 class="text-sm md:text-base font-bold text-gray-100 group-hover:text-neon-cyan transition-colors truncate max-w-2xl">
        {campaign.topic_data?.title || campaign.source_input || "Null_Pointer_Campaign"}
      </h4>

      <!-- Step & Progress Interface -->
      <div class="mt-3 flex items-center gap-4 flex-wrap">
         <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/5">
            <stepInfo.icon size={14} class="text-neon-cyan/60" />
            <span class="text-[11px] font-mono font-bold text-gray-400 uppercase tracking-tighter">
               Phase_0{step}: <span class="text-gray-200">{stepInfo.label}</span>
            </span>
         </div>

         {#if campaign.status === 'PROCESSING'}
            <div class="h-2 w-32 bg-white/5 rounded-full overflow-hidden border border-white/5">
               <div 
                 class="h-full bg-neon-cyan shadow-[0_0_10px_rgba(0,255,255,0.4)] transition-all duration-1000"
                 style="width: {(step / 6) * 100}%"
               ></div>
            </div>
         {/if}
      </div>
    </div>
  </div>

  <!-- Terminal Actions -->
  <div class="flex items-center gap-3 shrink-0 border-t md:border-t-0 md:border-l border-white/5 pt-4 md:pt-0 md:pl-6">
    {#if campaign.status === 'WAITING_FOR_REVIEW' || campaign.status === 'PROCESSING'}
      <button
        onclick={() => onAction(campaign)}
        class="flex items-center gap-2 px-5 py-2.5 bg-neon-cyan/10 hover:bg-neon-cyan text-neon-cyan hover:text-black font-black text-[10px] uppercase tracking-[0.2em] rounded-xl border border-neon-cyan/30 hover:border-neon-cyan transition-all active:scale-95 shadow-lg group/btn"
      >
        <Play size={14} class="group-hover/btn:fill-black" />
        Resume
      </button>
    {/if}

    <button
      onclick={() => onDelete(campaign.id)}
      disabled={isDeleting}
      class="p-2.5 rounded-xl bg-white/[0.02] border border-white/5 text-gray-600 hover:text-red-400 hover:bg-red-500/10 hover:border-red-500/30 transition-all opacity-20 md:opacity-0 group-hover:opacity-100 active:scale-95 touch-manipulation"
      title="Purge Campaign"
    >
      {#if isDeleting}
        <Loader2 size={16} class="animate-spin" />
      {:else}
        <Trash2 size={16} />
      {/if}
    </button>
  </div>
</div>

<style>
  .campaign-item:hover {
    background: rgba(255, 255, 255, 0.02);
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
  }
</style>
