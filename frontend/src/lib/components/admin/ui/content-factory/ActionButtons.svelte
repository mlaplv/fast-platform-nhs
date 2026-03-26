<script lang="ts">
  import {
    RotateCcw,
    Save,
    Check,
    ArrowLeft,
    ArrowRight,
    ChevronRight,
    Loader2,
    Play
  } from "lucide-svelte";

  import { onMount } from "svelte";
  import type { CampaignStatus } from "$lib/state/types";

  interface Props {
    isLoading: boolean;
    status: CampaignStatus | string;
    viewingStep: number;
    step: number;
    isEditing: boolean;
    isProcessing: boolean;
    isPublishing: boolean;
    handleRetry: () => void | Promise<void>;
    handleUpdateMetadata: () => void | Promise<void>;
    handlePublish: () => void | Promise<void>;
    handleApprove: () => void | Promise<void>;
  }

  let {
    isLoading,
    status,
    viewingStep = $bindable(),
    step,
    isEditing = $bindable(),
    isProcessing,
    isPublishing,
    handleRetry,
    handleUpdateMetadata,
    handlePublish,
    handleApprove
  }: Props = $props();

  onMount(() => {
    if (viewingStep === undefined) viewingStep = 1;
    if (isEditing === undefined) isEditing = false;
  });
</script>

<div class="fixed bottom-6 right-6 z-[250000] flex flex-col items-end pointer-events-none">
  <!-- iPhone 18 "Water Droplet" Liquid Dock -->
  <div 
    class="pointer-events-auto flex items-center gap-1 p-1 rounded-full bg-white/[0.01] backdrop-blur-[80px] saturate-[2.5] contrast-[1.1] border border-white/10 shadow-[0_25px_60px_rgba(0,0,0,0.5),inset_0_1px_3px_rgba(255,255,255,0.05)] transition-all duration-700 hover:scale-[1.08] active:scale-100 group"
  >
    
    <!-- Navigation Cluster: Symbols Only -->
    <div class="flex items-center gap-0.5 px-0.5">
      {#if viewingStep > 1}
        <button
          onclick={() => { viewingStep--; isEditing = false; }}
          disabled={isPublishing}
          class="w-9 h-9 flex items-center justify-center rounded-full hover:bg-white/10 text-white/40 hover:text-white transition-all active:scale-75"
          title="Back"
        >
          <ArrowLeft size={16} strokeWidth={2.5} />
        </button>
      {/if}

      {#if viewingStep < step}
        <button
          onclick={() => { viewingStep++; isEditing = false; }}
          disabled={isPublishing}
          class="w-9 h-9 flex items-center justify-center rounded-full hover:bg-white/10 text-white/40 hover:text-white transition-all active:scale-75"
          title="Forward"
        >
          <ArrowRight size={16} strokeWidth={2.5} />
        </button>
      {/if}

      <button
        onclick={handleRetry}
        disabled={isLoading || isProcessing}
        class="w-9 h-9 flex items-center justify-center rounded-full hover:bg-white/10 text-white/40 hover:text-white transition-all active:scale-75 group/retry"
        title="Retry"
      >
        <RotateCcw 
          size={16} 
          strokeWidth={2.5} 
          class={isProcessing ? 'animate-spin text-cyan-400' : 'group-hover:rotate-[-45deg] transition-transform'} 
        />
      </button>

      {#if isEditing}
        <button
          onclick={handleUpdateMetadata}
          disabled={isLoading}
          class="w-9 h-9 flex items-center justify-center rounded-full bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/10 transition-all active:scale-75"
          title="Save Changes"
        >
          <Save size={16} strokeWidth={2.5} />
        </button>
      {/if}
    </div>

    <!-- Minimal Separator -->
    <div class="w-px h-5 bg-white/10 mx-0.5"></div>

    <!-- Compact Primary Action: Intense Glow -->
    <button
      onclick={viewingStep === 6 ? handlePublish : (viewingStep < step ? () => { viewingStep = step; isEditing = false; } : handleApprove)}
      disabled={isLoading || isPublishing || (isProcessing && viewingStep === step)}
      class="group/primary relative h-9 px-4 flex items-center gap-2 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 font-black text-[10px] uppercase tracking-[0.15em] text-white shadow-[0_10px_25px_rgba(6,182,212,0.3)] hover:shadow-[0_15px_35px_rgba(6,182,212,0.5)] active:scale-95 transition-all overflow-hidden"
    >
      <!-- Neural Shimmer -->
      <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent -translate-x-full group-hover/primary:animate-shimmer" aria-hidden="true"></div>
      
      {#if isLoading || isPublishing} 
        <Loader2 size={14} class="animate-spin" />
      {:else if isProcessing && viewingStep === step}
        <div class="flex items-center gap-2">
          <Loader2 size={12} class="animate-spin opacity-50" />
          <span>NEURAL XOHI...</span>
        </div>
      {:else}
        <span class="relative">
          {#if viewingStep === 6} Launch
          {:else if viewingStep < step} Phase {step}
          {:else} Duyệt P{viewingStep}
          {/if}
        </span>
        <ChevronRight size={12} strokeWidth={3} class="opacity-70 group-hover/primary:translate-x-0.5 transition-transform" />
      {/if}
    </button>
    
    {#if isProcessing}
      <!-- Rescue Sync Trigger (Visible during processing) -->
      <button
        onclick={async () => {
          isLoading = true;
          try {
            // Signal a UI-only update to check for DB status changes
            await handleUpdateMetadata(); 
          } finally {
            isLoading = false;
          }
        }}
        class="w-9 h-9 flex items-center justify-center rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 hover:bg-cyan-500/20 transition-all ml-1 group"
        title="Force Sync: Nếu bị đơ quá lâu, hãy bấm để cập nhật dữ liệu mới nhất từ server"
      >
        <RotateCcw size={14} class="group-hover:rotate-180 transition-transform duration-500" />
      </button>
    {/if}
  </div>
</div>

<style>
  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }
  :global(.animate-shimmer) {
    animation: shimmer 1.5s infinite;
  }
</style>
