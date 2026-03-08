<script lang="ts">
  import {
    Check,
    RotateCcw,
    Edit2,
    Save,
    X,
    Sparkles,
    MessageSquare,
    Image as ImageIcon,
    FileText,
    ShieldCheck,
    CheckCircle,
  } from "lucide-svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { vuiState } from "$lib/vui/store/vui.state.svelte";
  import { fade, slide, scale } from "svelte/transition";

  let {
    campaign_id,
    keywords,
    assets = [],
    outline = null,
    step = 1,
    status = "WAITING_FOR_REVIEW",
  } = $props();

  let isEditing = $state(false);
  let editedKeywords = $state({ ...keywords });
  let isLoading = $state(false);
  let resultMsg = $state("");

  $effect(() => {
    editedKeywords = { ...keywords };
  });

  async function handleApprove() {
    isLoading = true;
    try {
      const resp = await apiClient.post(
        `/api/v1/content/campaigns/${campaign_id}/approve`,
        {
          approved: true,
          edited_data: isEditing ? editedKeywords : null,
        },
      );
      resultMsg = resp.message || "Đã duyệt thành công!";
      status = "PROCESSING";
      isEditing = false;
    } catch (e) {
      resultMsg = "Lỗi kết nối hệ thống...";
    } finally {
      isLoading = false;
      vuiState.setIsWaitingForAction(false);
    }
  }

  async function handleRetry() {
    isLoading = true;
    try {
      const resp = await apiClient.post(
        `/api/v1/content/campaigns/${campaign_id}/retry`,
        {},
      );
      resultMsg = resp.message || "Đang yêu cầu AI thực hiện lại...";
      status = "PROCESSING";
    } catch (e) {
      resultMsg = "Lỗi kết nối hệ thống...";
    } finally {
      isLoading = false;
      vuiState.setIsWaitingForAction(false);
    }
  }

  function toggleEdit() {
    if (isEditing) {
      editedKeywords = { ...keywords };
    }
    isEditing = !isEditing;
  }
</script>

<div
  class="content-review-card mt-4 p-5 rounded-2xl border border-white/10 bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl shadow-[0_20px_50px_rgba(0,0,0,0.3)] overflow-hidden transition-all duration-500 hover:border-blue-500/30 group"
  in:fade={{ duration: 400 }}
>
  <!-- Background Glow -->
  <div
    class="absolute -top-24 -right-24 w-48 h-48 bg-blue-500/10 blur-[80px] rounded-full pointer-events-none group-hover:bg-blue-500/20 transition-all duration-700"
  ></div>

  <div class="flex items-center justify-between mb-5 relative z-10">
    <div class="flex items-center gap-3">
      <div
        class="p-2 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/20 shadow-inner"
      >
        {#if step === 1} <Sparkles size={16} />
        {:else if step === 2} <ImageIcon size={16} />
        {:else if step === 3} <FileText size={16} />
        {:else if step === 5} <ShieldCheck size={16} />
        {:else} <CheckCircle size={16} />
        {/if}
      </div>
      <div class="flex flex-col">
        <span class="text-[10px] uppercase font-black tracking-[0.2em] text-blue-400/80">
          Phase {step}
        </span>
        <span class="text-xs font-bold text-white/90">
          {#if step === 1}Keyword Analysis
          {:else if step === 2}Asset Hunting
          {:else if step === 3}Content Outline
          {:else if step === 4}Drafting
          {:else if step === 5}Plagiarism Audit
          {:else}Finalization
          {/if}
        </span>
      </div>

      {#if status === "PROCESSING"}
        <div
          class="ml-2 flex items-center gap-1.5 px-2 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-400 animate-pulse"
        >
          <RotateCcw size={10} class="animate-spin" />
          <span class="font-medium">AI is working...</span>
        </div>
      {/if}
    </div>

    {#if status === "WAITING_FOR_REVIEW" && step === 1}
      <button
        onclick={toggleEdit}
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

  <div class="space-y-5 relative z-10">
    <!-- STEP 1: KEYWORDS -->
    {#if step === 1}
      {#if isEditing}
        <div class="space-y-4" transition:slide>
          <div class="group/input">
            <label class="text-[10px] text-white/40 uppercase font-bold mb-1.5 ml-1 block">Tiêu đề bài viết</label>
            <div class="relative">
              <MessageSquare size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" />
              <input
                bind:value={editedKeywords.title}
                class="w-full bg-black/20 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-all"
              />
            </div>
          </div>
          <div class="group/input">
            <label class="text-[10px] text-white/40 uppercase font-bold mb-1.5 ml-1 block">Từ khóa chính</label>
            <div class="relative">
              <Sparkles size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" />
              <input
                bind:value={editedKeywords.primary_keyword}
                class="w-full bg-black/20 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-all"
              />
            </div>
          </div>
        </div>
      {:else}
        <div class="space-y-2">
          <h4 class="text-lg font-bold text-white leading-snug tracking-tight">{keywords.title}</h4>
          <p class="text-[11px] text-white/40 font-medium uppercase tracking-wider">Style: <span class="text-white/70 italic">{keywords.persona}</span></p>
        </div>
        <div class="flex flex-wrap gap-2">
          <span class="px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-[11px] font-bold border border-blue-500/30">
            {keywords.primary_keyword}
          </span>
          {#each (keywords.secondary_keywords || []).slice(0, 4) as kw}
            <span class="px-3 py-1 rounded-full bg-white/5 text-white/40 text-[11px] font-medium border border-white/5">{kw}</span>
          {/each}
        </div>
      {/if}

    <!-- STEP 2: ASSET GALLERY -->
    {:else if step === 2}
      <div class="grid grid-cols-2 gap-3" transition:slide>
        {#each (assets || []).slice(0, 4) as url}
          <div class="aspect-video rounded-xl overflow-hidden border border-white/10 bg-white/5 group/img relative">
            <img src={url} alt="Hunted asset" class="w-full h-full object-cover transition-transform duration-500 group-hover/img:scale-110" />
            <div class="absolute inset-0 bg-black/40 opacity-0 group-hover/img:opacity-100 transition-opacity flex items-center justify-center">
               <Check size={20} class="text-blue-400" />
            </div>
          </div>
        {/each}
      </div>
      <p class="text-[11px] text-white/40 italic">Đã tìm thấy {assets.length} ảnh chất lượng cao. Sếp duyệt để em lập dàn ý nhé!</p>

    <!-- STEP 3: OUTLINE -->
    {:else if step === 3}
      <div class="space-y-3" transition:slide>
        <h5 class="text-sm font-bold text-blue-400">{outline?.title || "Dàn ý bài viết"}</h5>
        <ul class="space-y-2">
          {#each (outline?.sections || []) as section}
            <li class="flex items-start gap-3">
              <span class="mt-1 w-1.5 h-1.5 rounded-full bg-blue-500"></span>
              <span class="text-xs text-white/80 leading-relaxed font-medium">{section}</span>
            </li>
          {/each}
        </ul>
      </div>
    {/if}
  </div>

  {#if resultMsg}
    <div
      class="mt-5 flex items-start gap-2.5 p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-300 transition-all"
      transition:scale={{ start: 0.95, duration: 200 }}
    >
      <div class="mt-0.5 p-1 rounded-full bg-blue-500/20"><Check size={12} /></div>
      <p class="text-[12px] font-medium leading-relaxed">{resultMsg}</p>
    </div>
  {/if}

  {#if status === "WAITING_FOR_REVIEW"}
    <div class="flex gap-3 mt-6 relative z-10">
      <button
        onclick={handleApprove}
        disabled={isLoading}
        class="group/btn-primary flex-1 relative flex items-center justify-center gap-2 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm transition-all shadow-[0_10px_20px_-5px_rgba(37,99,235,0.4)] disabled:opacity-50"
      >
        {#if isLoading} <RotateCcw size={18} class="animate-spin" />
        {:else} <Check size={18} />
          <span>{isEditing ? "Lưu & Tiếp tục" : "Duyệt & Chạy tiếp"}</span>
        {/if}
      </button>

      <button
        onclick={handleRetry}
        disabled={isLoading}
        class="flex items-center justify-center px-4 rounded-xl bg-white/5 hover:bg-white/10 text-white/50 border border-white/10 transition-all disabled:opacity-50"
        title="Yêu cầu AI làm lại bước này"
      >
        <RotateCcw size={18} class={isLoading ? "animate-spin" : ""} />
      </button>
    </div>
  {/if}
</div>

<style>
  .content-review-card { position: relative; }
</style>
