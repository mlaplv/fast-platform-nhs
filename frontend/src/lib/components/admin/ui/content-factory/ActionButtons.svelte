<script lang="ts">
  import {
    RotateCcw,
    Save,
    Check
  } from "lucide-svelte";

  let { 
    isLoading,
    status,
    viewingStep,
    step,
    isEditing,
    isProcessing,
    isPublishing,
    handleRetry,
    handleUpdateMetadata,
    handlePublish,
    handleApprove
  } = $props();
</script>

<div class="flex gap-4 mt-auto pt-8 shrink-0 relative z-10 border-t border-white/5 pb-4">
  <!-- ACTION 1: REGENERATE / RETRY (Always available as a fallback/abort) -->
  <button
    onclick={handleRetry}
    disabled={isLoading}
    class="flex-1 group/btn-retry relative overflow-hidden flex items-center justify-center gap-2 py-4 rounded-2xl bg-white/5 hover:bg-white/10 text-white/50 hover:text-white border border-white/10 transition-all font-black text-[10px] uppercase tracking-[0.2em] active:scale-95 {isProcessing ? 'border-amber-500/20 bg-amber-500/5 text-amber-400' : ''}"
    title="Chạy lại hoặc hủy bỏ để làm lại bước này"
  >
    <div class="absolute inset-0 bg-gradient-to-tr from-white/0 via-white/[0.02] to-white/0 opacity-0 group-hover/btn-retry:opacity-100 transition-opacity"></div>
    <RotateCcw size={16} class={isProcessing ? "animate-spin" : ""} />
    <span>{isProcessing ? "Làm Lại" : "Chạy Lại"}</span>
  </button>

  {#if status === "WAITING_FOR_REVIEW"}
    {#if viewingStep < step}
      <!-- VIEWING PREVIOUS STEP -->
      <button
        onclick={isEditing ? handleUpdateMetadata : () => viewingStep = step}
        disabled={isLoading}
        class="flex-1 group/btn-secondary relative overflow-hidden flex items-center justify-center gap-2 py-4 rounded-2xl bg-white/10 hover:bg-white/20 text-white font-black text-[10px] uppercase tracking-widest transition-all border border-white/10 disabled:opacity-50 active:scale-95"
      >
        {#if isLoading} <RotateCcw size={16} class="animate-spin" />
        {:else if isEditing} <Save size={16} />
          <span>Lưu thay đổi Phase {viewingStep}</span>
        {:else} <RotateCcw size={16} class="rotate-180" />
          <span>Về Phase {step} (Hiện tại)</span>
        {/if}
      </button>
    {:else}
      <!-- CURRENT STEP ACTION -->
      {#if viewingStep === 6 && step === 6}
        <!-- Step 6: Publish Button -->
        <button
          onclick={handlePublish}
          disabled={isLoading}
          class="flex-1 group/btn-publish relative overflow-hidden flex items-center justify-center gap-2 py-4 rounded-2xl bg-green-600 hover:bg-green-500 text-white font-black text-[10px] uppercase tracking-widest transition-all shadow-[0_15px_30px_-10px_rgba(22,163,74,0.4)] disabled:opacity-50 active:scale-95"
        >
          <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover/btn-publish:animate-shimmer pointer-events-none"></div>
          {#if isLoading} <RotateCcw size={16} class="animate-spin" />
          {:else} <Check size={16} strokeWidth={3} />
            <span>Xuất Bản Lên Web</span>
          {/if}
        </button>
      {:else}
        {#if isEditing}
          <button
            onclick={() => handleUpdateMetadata(step)}
            disabled={isLoading}
            class="flex-1 group/btn-save relative overflow-hidden flex items-center justify-center gap-2 py-4 rounded-2xl bg-white/10 hover:bg-white/20 text-white font-black text-[10px] uppercase tracking-widest transition-all border border-white/10 disabled:opacity-50 active:scale-95"
          >
            {#if isLoading} <RotateCcw size={16} class="animate-spin" />
            {:else} <Save size={16} />
              <span>Lưu Bản Thảo</span>
            {/if}
          </button>
        {/if}
        
        <button
          onclick={viewingStep === 6 ? handlePublish : handleApprove}
          disabled={isLoading || isPublishing}
          class="flex-1 group/btn-primary relative overflow-hidden flex items-center justify-center gap-2 py-4 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-black text-[10px] uppercase tracking-widest transition-all shadow-[0_15px_30px_-10px_rgba(37,99,235,0.4)] disabled:opacity-50 active:scale-95"
        >
          <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover/btn-primary:animate-shimmer pointer-events-none"></div>
          {#if isLoading || isPublishing} <RotateCcw size={16} class="animate-spin" />
          {:else}
            <Check size={16} strokeWidth={3} />
            <span>
              {#if viewingStep === 6} Xuất bản ngay
              {:else if isEditing} Duyệt & Lưu
              {:else} Duyệt & Tiếp tục
              {/if}
            </span>
          {/if}
        </button>
      {/if}
    {/if}
  {/if}
</div>
