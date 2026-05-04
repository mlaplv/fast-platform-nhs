<script lang="ts">
  import Globe from "lucide-svelte/icons/globe";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import { resolveMediaUrl } from "$lib/state/utils";

  let {
    formName,
    formSlug = $bindable(),
    formSeoTitle = $bindable(),
    formSeoDescription = $bindable(),
    formSeoKeywords = $bindable(),
    formImages,
    generateSlug
  } = $props<{
    formName: string;
    formSlug: string;
    formSeoTitle: string;
    formSeoDescription: string;
    formSeoKeywords: string;
    formImages: string[];
    generateSlug: (name: string) => string;
  }>();

  let socialPreviewTab = $state<'facebook' | 'twitter'>('facebook');
  
  let isAiLoading = $state(false);

  async function handleAiSuggest() {
    if (!formName) return;
    isAiLoading = true;
    try {
      // Elite V2.2: R00 AI Suggest Call
      const res = await fetch('/api/v1/products/seo-suggest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: formName, description: formSeoDescription || '' })
      });
      const json = (await res.json()) as { data?: { title?: string; description?: string; keywords?: string; } };
      if (json && json.data) {
        // Fallback or explicit overwrite
        formSeoTitle = json.data.title || formSeoTitle;
        formSeoDescription = json.data.description || formSeoDescription;
        formSeoKeywords = json.data.keywords || formSeoKeywords;
      }
    } catch (e) {
      console.error('AI Suggest failed:', e);
    } finally {
      isAiLoading = false;
    }
  }

  const seoTitleLen = $derived(formSeoTitle?.length ?? 0);
  const seoDescLen = $derived(formSeoDescription?.length ?? 0);
  const ogTitle = $derived(formSeoTitle || formName || 'Tên sản phẩm');
  const ogDesc = $derived(formSeoDescription || 'Mô tả ngắn gọn về sản phẩm...');
  const ogUrl = $derived(`osmo/${formSlug || 'slug-san-pham'}`);
  const ogImg = $derived(formImages && formImages.length > 0 ? resolveMediaUrl(formImages[0]) : null);
</script>

<div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
  <!-- SEO Config -->
  <div>
    <div class="flex items-center justify-between mb-3">
      <div class="section-label mb-0">
        <Globe size={11} />
        SEO Search Engine
      </div>
      <button type="button" onclick={handleAiSuggest} disabled={isAiLoading} class="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-wider cursor-pointer bg-blue-500/10 border border-blue-500/30 text-blue-400 hover:bg-blue-600 hover:text-white transition-colors disabled:opacity-50">
        {#if isAiLoading}
          <RefreshCw size={10} class="animate-spin" />
          Đang phân tích...
        {:else}
          <Globe size={10} />
          AI Suggest
        {/if}
      </button>
    </div>

    <div class="flex flex-col gap-4">
      <!-- Slug -->
      <div class="field-group">
        <label class="field-label flex items-center gap-2">Bí danh URL</label>
        <div class="relative flex items-center gap-2">
          <div class="relative flex-1">
            <input
              type="text"
              bind:value={formSlug}
              placeholder="duong-dan-san-pham"
              class="field-input border-b-amber-500/30 font-mono text-sm text-amber-400/80"
            />
            <div class="field-line bg-amber-500/60"></div>
          </div>
          <button
            onclick={() => { formSlug = generateSlug(formName); }}
            title="Tạo lại slug từ tên sản phẩm"
            class="shrink-0 flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[8px] font-black uppercase tracking-wider cursor-pointer bg-white/5 border border-white/10 text-white/40 hover:text-amber-400 hover:border-amber-500/30 hover:bg-amber-500/5"
          >
            <RefreshCw size={10} />
            Tạo lại
          </button>
        </div>
      </div>

      <!-- SEO Title -->
      <div class="field-group">
        <label class="field-label">
          SEO Meta Title
          <span class="ml-auto {seoTitleLen > 60 ? 'text-red-400' : 'text-amber-500/60'}">{seoTitleLen}/60</span>
        </label>
        <div class="relative">
          <input type="text" bind:value={formSeoTitle}
            placeholder="Tiêu đề SEO (50-60 ký tự)..."
            class="field-input text-sm border-b-amber-500/30"
          />
          <div class="field-line bg-amber-500/60"></div>
        </div>
      </div>

      <!-- SEO Keywords -->
      <div class="field-group">
        <label class="field-label">SEO Keywords</label>
        <div class="relative">
          <input type="text" bind:value={formSeoKeywords}
            placeholder="Các từ khóa SEO cách nhau bởi dấu phẩy..."
            class="field-input text-sm border-b-amber-500/30"
          />
          <div class="field-line bg-amber-500/60"></div>
        </div>
      </div>

      <!-- SEO Description -->
      <div class="field-group">
        <label class="field-label">
          SEO Meta Description
          <span class="ml-auto {seoDescLen > 160 ? 'text-red-400' : 'text-amber-500/60'}">{seoDescLen}/160</span>
        </label>
        <textarea bind:value={formSeoDescription} rows="4"
          placeholder="Mô tả chuẩn SEO (150-160 ký tự)..."
          class="w-full bg-white/[0.02] border border-white/8 rounded-xl p-3 text-sm text-white/60 placeholder:text-white/15 outline-none focus:border-amber-500/30 resize-y min-h-[100px] shadow-inner"
          style="field-sizing: content;"
        ></textarea>
      </div>
    </div>
  </div>

  <!-- Preview Column -->
  <div class="flex flex-col gap-4 mt-6 xl:mt-0">
    <div class="section-label italic text-white/20 mb-0">Visual Preview</div>
    
    <div class="flex flex-col gap-4">
      <!-- Google Snippet Preview -->
      <div class="bg-[#111] rounded-xl p-4 border border-white/5 flex flex-col gap-1 shadow-inner">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <div class="w-5 h-5 rounded-full bg-white/5 flex items-center justify-center text-[8px] font-black text-white/30">G</div>
            <span class="text-[8px] font-black uppercase tracking-[0.3em] text-white/20">Google Search Preview</span>
          </div>
          <span class="text-[7px] font-mono text-white/20 px-1.5 py-0.5 border border-white/5 rounded">Auto-Synced</span>
        </div>
        <div class="text-[13px] text-[#8ab4f8] truncate font-medium cursor-pointer hover:underline">{ogTitle}</div>
        <div class="flex items-center gap-1.5 text-[10px] text-[#bdc1c6] truncate">
          <span class="px-1 py-0.5 bg-white/5 text-[7px] border border-white/10 text-white/40 rounded font-bold">https</span>
          {ogUrl}
        </div>
        <div class="text-[11px] text-[#9aa0a6] line-clamp-2 leading-relaxed">{ogDesc}</div>
      </div>

      <!-- Social Media OG Preview -->
      <div class="flex flex-col gap-3">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="flex items-center gap-1 p-1 bg-black/40 border border-white/5 rounded-xl w-fit">
            {#each [['facebook', 'Facebook'], ['twitter', 'X / Twitter']] as [id, label]}
              <button
                onclick={() => socialPreviewTab = id as 'facebook' | 'twitter'}
                class="px-4 py-1.5 text-[8px] font-black uppercase tracking-widest rounded-lg transition-all
                  {socialPreviewTab === id ? 'bg-white/10 text-white border border-white/10' : 'text-white/30 hover:text-white/60'}"
              >{label}</button>
            {/each}
          </div>
          <div class="text-[9px] text-amber-500/50 italic mr-2 text-right leading-tight">
            *Hình SEO tự động trích xuất từ<br/>Ảnh Đại Diện số 1
          </div>
        </div>

        {#if socialPreviewTab === 'facebook'}
          <!-- Facebook OG Card -->
          <div class="rounded-xl overflow-hidden border border-[#3a3b3c] bg-[#242526] shadow-lg max-w-[400px]">
            <div class="w-full aspect-[1.91/1] bg-[#3a3b3c] flex items-center justify-center overflow-hidden">
              {#if ogImg}
                <img src={ogImg} alt="OG" class="w-full h-full object-cover opacity-90" />
              {:else}
                <span class="text-[9px] text-white/20 uppercase tracking-widest">Không có Avatar SEO</span>
              {/if}
            </div>
            <div class="p-3 flex flex-col gap-1 bg-[#242526]">
              <span class="text-[9px] text-[#b0b3b8] uppercase tracking-widest truncate">osmo</span>
              <div class="text-sm font-bold text-[#e4e6eb] line-clamp-2 leading-snug">{ogTitle}</div>
              <div class="text-[11px] text-[#b0b3b8] line-clamp-2 mt-0.5">{ogDesc}</div>
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>

<style>
  @reference "tailwindcss";
  .section-label { @apply flex items-center gap-2 text-[9px] font-black uppercase tracking-[0.35em] text-white/30; }
  .field-group { @apply flex flex-col gap-2; }
  .field-label { @apply flex items-center gap-2 text-[9px] font-black text-white/25 uppercase tracking-[0.25em]; }
  .field-input { @apply w-full bg-transparent border-b border-white/8 px-1 py-1.5 text-white placeholder:text-white/15 outline-none transition-colors; }
  .field-line { @apply absolute bottom-0 left-0 w-0 h-[1px] bg-amber-500/60 transition-all duration-300; }
  :global(.field-group:focus-within .field-line) { @apply w-full; }
</style>
