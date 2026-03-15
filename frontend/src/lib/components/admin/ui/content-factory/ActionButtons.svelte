<script lang="ts">
  import {
    RotateCcw,
    Save,
    Check,
    ArrowLeft,
    ChevronRight,
    Loader2
  } from "lucide-svelte";

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
    handleApprove,
    isCompact = false // Safari-style scale prop
  } = $props();
</script>

<div class="flex flex-col md:flex-row gap-4 md:gap-4 mt-auto pt-2 md:pt-8 relative md:relative z-[2100] pb-4 md:pb-4 transition-all duration-500 {isCompact ? 'scale-90 translate-y-2 opacity-80' : 'scale-100 translate-y-0 opacity-100'} md:static absolute bottom-0 left-0 w-full px-4 md:px-0 pointer-events-none md:pointer-events-auto">
  <!-- Mobile Navigation Layout: Liquid Glass iOS 26 Design -->
  <div class="flex md:hidden items-center justify-between w-full h-[56px] px-2.5 bg-white/[0.01] backdrop-blur-[40px] rounded-full border border-white/[0.05] shadow-[0_20px_50px_rgba(0,0,0,0.5)] pointer-events-auto">
    
    <!-- Left Group: Secondary Actions -->
    <div class="flex items-center gap-1.5">
      <!-- Back / Lùi lại -->
      {#if viewingStep > 1}
        <button
          onclick={() => { viewingStep--; isEditing = false; }}
          disabled={isLoading}
          class="w-11 h-11 flex items-center justify-center rounded-full bg-white/[0.05] border border-white/[0.1] text-white/40 active:scale-90 transition-all active:bg-white/10"
          title="Lùi lại"
        >
          <ArrowLeft size={18} strokeWidth={2.5} />
        </button>
      {/if}

      <!-- Retry / Chạy lại -->
      <button
        onclick={handleRetry}
        disabled={isLoading}
        class="w-11 h-11 flex items-center justify-center rounded-full bg-white/[0.05] border border-white/[0.1] text-white/40 active:scale-90 transition-all active:bg-white/10"
        title="Chạy lại phase {viewingStep}"
      >
        <RotateCcw size={18} strokeWidth={2.5} class={isProcessing ? "animate-spin" : ""} />
      </button>

      <!-- Save / Lưu (Only if editing) -->
      {#if isEditing}
        <button
          onclick={handleUpdateMetadata}
          disabled={isLoading}
          class="w-11 h-11 flex items-center justify-center rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 active:scale-90 transition-all "
          title="Lưu bản thảo"
        >
          <Save size={18} strokeWidth={2.5} />
        </button>
      {/if}
    </div>

    <!-- Center/Right: Primary Action -->
    <div class="flex-1 flex justify-end">
      <button
        onclick={viewingStep === 6 ? handlePublish : (viewingStep < step ? () => viewingStep = step : handleApprove)}
        disabled={isLoading || isPublishing}
        class="group relative h-11 px-6 flex items-center gap-2 rounded-full bg-blue-600 shadow-[0_0_20px_rgba(37,99,235,0.3)] active:scale-95 transition-all overflow-hidden"
      >
        <!-- Liquid Shine Effect -->
        <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-active:translate-x-full transition-transform duration-700"></div>
        
        {#if isLoading || isPublishing} 
          <Loader2 size={16} class="animate-spin text-white" />
        {:else}
          <span class="text-xs font-black uppercase tracking-widest text-white drop-shadow-sm">
            {#if viewingStep === 6} Xuất bản
            {:else if viewingStep < step} Tiếp tục P{step}
            {:else} Duyệt
            {/if}
          </span>
          <div class="flex items-center -mr-1">
             <ChevronRight size={14} strokeWidth={3} class="text-white/60" />
             <ChevronRight size={14} strokeWidth={3} class="text-white/40 -ml-2" />
          </div>
        {/if}
      </button>
    </div>
  </div>


  <!-- Standard Desktop Layout (Hidden on Mobile) -->
  <div class="hidden md:flex gap-4 w-full">
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
        {#if viewingStep === 6 && step === 6}
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
              onclick={handleUpdateMetadata}
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
</div>
