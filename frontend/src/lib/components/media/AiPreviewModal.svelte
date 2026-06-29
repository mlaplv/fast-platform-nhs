<script lang="ts">
  import X from "@lucide/svelte/icons/x";
  import Check from "@lucide/svelte/icons/check";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import AlertTriangle from "@lucide/svelte/icons/alert-triangle";
  import Image from "@lucide/svelte/icons/image";
  import { mediaStore } from '$lib/state/media.svelte';
  import { useNanobot } from '$lib/state/nanobot.svelte';
  import { Z_INDEX_ADMIN } from '$lib/core/constants/z_index_admin';

  interface Props {
    show: boolean;
    initialPrompt: string;
    campaignId?: string | null;
    onSelect: (url: string) => void;
  }

  let {
    show = $bindable(),
    initialPrompt = "",
    campaignId = null,
    onSelect
  }: Props = $props();

  const nanobot = useNanobot();

  let prompt = $state("");
  let notes = $state("");
  let previewUrl = $state<string | null>(null);
  let isGenerating = $state(false);
  let isSaving = $state(false);
  let errorMsg = $state<string | null>(null);

  // Initialize prompt from initialPrompt prop on mount or show change
  $effect(() => {
    if (show && initialPrompt && !prompt) {
      prompt = initialPrompt;
    }
  });

  // Handle Cancel / Close -> Clean up temporary file to prevent storage pollution
  async function handleClose() {
    if (previewUrl && !isSaving) {
      try {
        await mediaStore.generatePreview("", "16:9", previewUrl);
      } catch (e: unknown) {
        console.warn("Temp image cleanup failed on close:", (e as Error).message);
      }
    }
    previewUrl = null;
    prompt = "";
    notes = "";
    errorMsg = null;
    show = false;
  }

  // Generate / Regenerate AI Image preview
  async function handleGenerate() {
    if (!prompt.trim()) {
      errorMsg = "Vui lòng nhập mô tả hoặc tiêu đề bài viết.";
      return;
    }

    isGenerating = true;
    errorMsg = null;

    try {
      let finalPrompt = prompt;
      if (notes.trim()) {
        finalPrompt = `${prompt}. Note: ${notes}`;
      }

      const result = await mediaStore.generatePreview(finalPrompt, "16:9", previewUrl);
      if (result && result.file_path) {
        previewUrl = result.file_path;
        notes = ""; 
      } else {
        errorMsg = "Không nhận được phản hồi từ mô hình sinh ảnh.";
      }
    } catch (e: unknown) {
      errorMsg = (e as Error).message || "Đã xảy ra lỗi trong quá trình sinh ảnh.";
      nanobot.showToast("Sinh ảnh thất bại", "error");
    } finally {
      isGenerating = false;
    }
  }

  // Approve & Save image permanently to Media Vault
  async function handleApprove() {
    if (!previewUrl) return;

    isSaving = true;
    errorMsg = null;

    try {
      const asset = await mediaStore.savePreview(previewUrl, prompt, campaignId);
      if (asset && asset.file_path) {
        nanobot.showToast("Đã lưu ảnh AI vào thư viện thành công!", "success");
        onSelect(asset.file_path);
        previewUrl = null;
        await handleClose();
      } else {
        errorMsg = "Không thể đăng ký ảnh vào hệ thống quản lý.";
      }
    } catch (e: unknown) {
      errorMsg = (e as Error).message || "Không thể lưu ảnh.";
      nanobot.showToast("Lưu ảnh thất bại", "error");
    } finally {
      isSaving = false;
    }
  }
</script>

{#if show}
  <div 
    class="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center transition-all p-4 duration-300"
    style="z-index: {Z_INDEX_ADMIN.MODAL}"
  >
    <div class="bg-[#0b0f17]/90 border border-white/10 rounded-2xl w-full max-w-2xl overflow-hidden shadow-[0_0_50px_rgba(6,182,212,0.15)] flex flex-col max-h-[90vh]">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-white/[0.02]">
        <div class="flex items-center gap-2.5">
          <div class="w-7 h-7 rounded-lg bg-cyan-500/10 flex items-center justify-center text-cyan-400">
            <Sparkles size={16} class="animate-pulse" />
          </div>
          <div>
            <h3 class="text-sm font-black text-white tracking-wider uppercase">XOHI Sinh Ảnh Banner AI</h3>
            <p class="text-[9px] text-white/40 font-semibold mt-0.5">Mô hình: Gemini Nano Banana (750px x 400px WebP)</p>
          </div>
        </div>
        <button 
          onclick={handleClose}
          disabled={isGenerating || isSaving}
          class="p-1.5 hover:bg-white/5 text-white/50 hover:text-white rounded-lg transition-all disabled:opacity-20"
        >
          <X size={16} />
        </button>
      </div>

      <!-- Content -->
      <div class="p-6 flex-1 overflow-y-auto space-y-5">
        {#if errorMsg}
          <div class="flex items-start gap-3 p-3.5 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-[11px] leading-relaxed">
            <AlertTriangle size={16} class="shrink-0 mt-0.5" />
            <span class="font-medium">{errorMsg}</span>
          </div>
        {/if}

        <!-- Title / Primary Prompt -->
        <div class="space-y-1.5">
          <label class="text-[10px] font-black text-white/50 uppercase tracking-widest block font-sans">Mô tả / Prompt chính</label>
          <textarea
            bind:value={prompt}
            disabled={isGenerating || isSaving || !!previewUrl}
            placeholder="Mô tả nội dung bức ảnh bạn muốn sinh (Nên dùng tiếng Anh để đạt kết quả tốt nhất)..."
            rows="3"
            class="w-full bg-white/[0.02] border border-white/8 rounded-xl p-3 text-xs text-white placeholder:text-white/20 outline-none focus:border-cyan-500/30 resize-none disabled:opacity-50 transition-colors font-sans"
          ></textarea>
        </div>

        <!-- Preview Area -->
        {#if previewUrl || isGenerating}
          <div class="space-y-1.5">
            <label class="text-[10px] font-black text-white/50 uppercase tracking-widest block font-sans">Xem trước ảnh nháp (750x400)</label>
            <div class="relative aspect-[750/400] rounded-xl border border-white/10 bg-black/40 overflow-hidden flex items-center justify-center group shadow-inner">
              {#if isGenerating}
                <!-- Glassmorphism Loading Spinner -->
                <div class="absolute inset-0 bg-[#0b0f17]/60 backdrop-blur-sm z-10 flex flex-col items-center justify-center gap-3">
                  <div class="w-8 h-8 border-3 border-cyan-400/20 border-t-cyan-400 rounded-full animate-spin"></div>
                  <span class="text-[10px] font-black tracking-widest text-cyan-400 animate-pulse uppercase font-sans">Đang phác thảo...</span>
                </div>
              {/if}

              {#if previewUrl}
                <img 
                  src={previewUrl} 
                  alt="Preview" 
                  class="w-full h-full object-cover"
                />
              {:else}
                <div class="flex flex-col items-center gap-2 text-white/20">
                  <Image size={32} strokeWidth={1} />
                  <span class="text-[9px] font-bold tracking-wider font-sans">Chưa có ảnh preview</span>
                </div>
              {/if}
            </div>
          </div>
        {/if}

        <!-- Notes / Regeneration Feedback -->
        {#if previewUrl}
          <div class="space-y-1.5">
            <label class="text-[10px] font-black text-white/50 uppercase tracking-widest block font-sans">Chỉ dẫn bổ sung để sinh lại (Ghi chú)</label>
            <textarea
              bind:value={notes}
              disabled={isGenerating || isSaving}
              placeholder="Ví dụ: 'Make the lighting warm and sunset tone', 'add fresh coffee beans on the table'..."
              rows="2"
              class="w-full bg-white/[0.02] border border-white/8 rounded-xl p-3 text-xs text-white placeholder:text-white/20 outline-none focus:border-purple-500/30 resize-none disabled:opacity-50 transition-colors font-sans"
            ></textarea>
          </div>
        {/if}
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-white/10 bg-white/[0.01] flex items-center justify-between gap-3">
        <div>
          {#if previewUrl}
            <button
              onclick={() => { previewUrl = null; notes = ""; }}
              disabled={isGenerating || isSaving}
              class="px-4 py-2 hover:bg-white/5 text-white/40 hover:text-white border border-white/10 rounded-xl text-[10px] font-black tracking-wider uppercase transition-all disabled:opacity-30 font-sans"
            >
              Làm lại từ đầu
            </button>
          {/if}
        </div>

        <div class="flex items-center gap-3">
          <button
            onclick={handleClose}
            disabled={isGenerating || isSaving}
            class="px-4 py-2 hover:bg-white/5 text-white/50 hover:text-white rounded-xl text-[10px] font-black tracking-wider uppercase transition-all disabled:opacity-30 font-sans"
          >
            Hủy
          </button>

          {#if !previewUrl}
            <button
              onclick={handleGenerate}
              disabled={isGenerating || !prompt.trim()}
              class="px-5 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-xl text-[10px] font-black tracking-wider uppercase hover:shadow-[0_0_15px_rgba(6,182,212,0.4)] disabled:from-zinc-800 disabled:to-zinc-800 disabled:text-white/30 disabled:shadow-none transition-all flex items-center gap-2 font-sans"
            >
              {#if isGenerating}
                <RefreshCw size={11} class="animate-spin" />
                Đang sinh ảnh...
              {:else}
                <Sparkles size={11} />
                Sinh ảnh AI
              {/if}
            </button>
          {:else}
            <div class="flex items-center gap-2">
              {#if notes.trim()}
                <button
                  onclick={handleGenerate}
                  disabled={isGenerating}
                  class="px-5 py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 border border-purple-500/30 rounded-xl text-[10px] font-black tracking-wider uppercase transition-all flex items-center gap-2 disabled:opacity-30 font-sans"
                >
                  <RefreshCw size={11} class={isGenerating ? "animate-spin" : ""} />
                  Sinh lại ảnh
                </button>
              {/if}
              
              <button
                onclick={handleApprove}
                disabled={isSaving || isGenerating}
                class="px-5 py-2 bg-emerald-500 text-black rounded-xl text-[10px] font-black tracking-wider uppercase hover:bg-emerald-400 disabled:bg-zinc-800 disabled:text-white/30 transition-all flex items-center gap-2 font-sans"
              >
                {#if isSaving}
                  <div class="w-3 h-3 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                  Đang lưu...
                {:else}
                  <Check size={11} />
                  Duyệt & Lưu
                {/if}
              </button>
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
{/if}
