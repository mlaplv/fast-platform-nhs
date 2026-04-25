<script lang="ts">
  import { onMount, untrack } from "svelte";
  import Globe from "lucide-svelte/icons/globe";
  import FileText from "lucide-svelte/icons/file-text";
  import Image from "lucide-svelte/icons/image";
  import Settings from "lucide-svelte/icons/settings";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import ChevronDown from "lucide-svelte/icons/chevron-down";
  import ImagePlus from "lucide-svelte/icons/image-plus";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import Lock from "lucide-svelte/icons/lock";
  import Newspaper from "lucide-svelte/icons/newspaper";
  import AlertTriangle from "lucide-svelte/icons/triangle-alert";
  import MissionControlShell from "../ui/MissionControlShell.svelte";
  import MediaVaultModal from "../../media/MediaVaultModal.svelte";
  import NeuralEditor from "../ui/tiptap/NeuralEditor.svelte";
  import { resolveMediaUrl, processContentImages } from "$lib/state/utils";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import { apiClient } from "$lib/utils/apiClient";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import Plus from "lucide-svelte/icons/plus";
  import type { MediaAsset } from "$lib/types";
  import type { AnalysisCache, CampaignMetrics } from "$lib/state/types";

  const nanobot = useNanobot();
  
  let {
    isOpen = false,
    editingId,
    formTitle = $bindable(),
    formCategory = $bindable(),
    formStatus = $bindable(),
    formExcerpt = $bindable(),
    formContent = $bindable(),
    formSlug = $bindable(),
    formSeoTitle = $bindable(),
    formSeoDescription = $bindable(),
    formSeoKeywords = $bindable(),
    formSeoOgImage = $bindable(),
    formFeaturedImage = $bindable(),
    formFaqs = $bindable(),
    formAnalysisCache = $bindable(),
    formAnalysisMetrics = $bindable(),
    formAnalysisReport = $bindable(),
    dbCategories,
    onSave,
    onClose,
    generateSlug,
    isSaving,
    errors,
  } = $props<{
    editingId: string | null;
    formTitle: string;
    formCategory: string;
    formStatus: string;
    formExcerpt: string;
    formContent: string;
    formSlug: string;
    formSeoTitle: string;
    formSeoDescription: string;
    formSeoKeywords: string;
    formSeoOgImage: string | null;
    formFeaturedImage: string | null;
    formFaqs: { question: string; answer: string }[];
    dbCategories: readonly string[];
    onSave: () => void;
    onClose: () => void;
    generateSlug: (title: string) => string;
    isSaving?: boolean;
    isOpen?: boolean;
    errors?: Record<string, string>;
    formAnalysisCache?: AnalysisCache;
    formAnalysisMetrics?: CampaignMetrics;
    formAnalysisReport?: Record<string, unknown>;
  }>();

  let showMediaModal = $state(false);
  let selectingOgImage = $state(false);
  let selectedAvatarUrl = $state<string | null>(null);
  let selectedAssetIndex = $state(0);
  let contentAssets = $state<(MediaAsset | string)[]>([]);
  let featuredContextAssets = $state<(MediaAsset | string)[]>([]);

  // ⚡ PERF: One-time asset extraction — runs ONLY on mount, not on every keystroke
  let assetsExtracted = false;

  // Resolve legacy AI placeholders — uses untrack to prevent feedback loop
  $effect(() => {
    if (formContent && formContent.includes("[IMAGE_")) {
      const assets = untrack(() => contentAssets);
      formContent = processContentImages(formContent, assets);
    }
  });

  // Seed featured image into modal context — one-time only
  $effect(() => {
    const img = formFeaturedImage;
    if (img && untrack(() => featuredContextAssets.length) === 0) {
      featuredContextAssets = [img];
    }
  });

  onMount(() => {
    // ⚡ One-time asset extraction from existing content
    if (formContent && !assetsExtracted) {
      assetsExtracted = true;
      const imgRegex = /<img[^>]+src=["']([^"']+)["']/g;
      const found: string[] = [];
      let match: RegExpExecArray | null;
      while ((match = imgRegex.exec(formContent)) !== null) {
        if (match[1] && !found.includes(match[1])) found.push(match[1]);
      }
      if (found.length > 0) contentAssets = found;
    }

    if (!formTitle) formTitle = "";
    if (!formCategory) formCategory = dbCategories?.[0] ?? "";
    if (!formStatus) formStatus = "DRAFT";
    if (!formExcerpt) formExcerpt = "";
    if (!formContent) formContent = "";
    if (!formSlug) formSlug = "";
    if (!formSeoTitle) formSeoTitle = "";
    if (!formSeoDescription) formSeoDescription = "";
    if (formSeoOgImage === undefined) formSeoOgImage = null;
    if (formFeaturedImage === undefined) formFeaturedImage = null;
  });

  const seoTitleLen = $derived(formSeoTitle?.length ?? 0);
  const seoDescLen = $derived(formSeoDescription?.length ?? 0);

  let socialPreviewTab = $state<'facebook' | 'twitter'>('facebook');
  const ogTitle = $derived(formSeoTitle || formTitle || 'Tiêu đề bài viết');
  const ogDesc = $derived(formSeoDescription || formExcerpt || 'Mô tả ngắn gọn về bài viết...');
  const ogUrl = $derived(`micsmo.com/${formSlug || 'slug-bai-viet'}.p${editingId || 'pid'}`);
  const ogImg = $derived(formSeoOgImage ? resolveMediaUrl(formSeoOgImage) : (formFeaturedImage ? resolveMediaUrl(formFeaturedImage) : null));
  const isSlugLocked = $derived(formStatus === 'PUBLISHED' && !!editingId);

  let featuredImageBroken = $state(false);
  let ogImageBroken = $state(false);

  // Reset broken state when image URL changes
  $effect(() => {
    formFeaturedImage;
    featuredImageBroken = false;
  });
  $effect(() => {
    formSeoOgImage;
    ogImageBroken = false;
  });

  // GEO 2026: XOHI FAQ State
  let isSuggestingFaqs = $state(false);
  let isSuggestingSeo = $state(false);

  async function handleAiSuggestSeo() {
    if (!formTitle) {
      nanobot.showToast("Vui lòng nhập tiêu đề bài viết trước.", "warning");
      return;
    }
    isSuggestingSeo = true;
    try {
      const res = await apiClient.post<{ data: { seo_title: string; seo_description: string; seo_keywords: string } }>('/api/v1/articles/seo-suggest', {
        title: formTitle,
        content: formContent || formExcerpt || ''
      });
      if (res?.data) {
        formSeoTitle = res.data.seo_title || formSeoTitle;
        formSeoDescription = res.data.seo_description || formSeoDescription;
        formSeoKeywords = res.data.seo_keywords || formSeoKeywords;
        nanobot.showToast("XOHI đã tối ưu SEO thành công.", "success");
      }
    } catch (e) {
      console.error('XOHI Article SEO failed:', e);
      nanobot.showToast("Lỗi tối ưu SEO.", "error");
    } finally {
      isSuggestingSeo = false;
    }
  }

  async function handleAiSuggestFaqs() {
    if (!formTitle) {
      nanobot.showToast("Vui lòng nhập tiêu đề bài viết trước khi gọi XOHI.", "warning");
      return;
    }
    isSuggestingFaqs = true;
    try {
      const res = await apiClient.post<{ data: { question: string; answer: string }[] }>('/api/v1/articles/faq-suggest', {
        title: formTitle,
        content: formContent || formExcerpt || ''
      });
      if (res?.data && Array.isArray(res.data) && res.data.length > 0) {
        formFaqs = [...formFaqs, ...res.data];
        nanobot.showToast(`XOHI đã tạo ${res.data.length} câu hỏi FAQ thành công.`, "success");
      } else {
        nanobot.showToast("XOHI không thể tạo câu hỏi. Vui lòng thử lại.", "error");
      }
    } catch (e) {
      console.error('XOHI Article FAQ failed:', e);
      nanobot.showToast("Lỗi kết nối tới hệ thống AI XOHI.", "error");
    } finally {
      isSuggestingFaqs = false;
    }
  }

  function addFaqManual() {
    formFaqs = [...formFaqs, { question: '', answer: '' }];
  }

  function removeFaq(index: number) {
    formFaqs = formFaqs.filter((_, i) => i !== index);
  }
</script>

<MissionControlShell
  title={editingId ? `LƯU_TRỮ_TIN_TỨC // SỬA_${editingId.slice(0, 8)}` : "LƯU_TRỮ_TIN_TỨC // TẠO_MỚI"}
  variant="cyan"
  {isOpen}
  {onClose}
  headerIcon={Newspaper}
  fullScreen={true}
  zIndex={Z_INDEX_ADMIN.MODAL}
>
  <div class="w-full flex flex-col gap-0 pb-10">

  <section class="relative px-5 pt-5 pb-0" style="z-index: {Z_INDEX_ADMIN.SURFACE}">
    <div class="section-label">
      <Settings size={11} />
      Thông tin cơ bản
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-12 gap-x-8 gap-y-4 mt-4">
      <!-- Left Column: Title, Slug, Category, Status, Excerpt (8/12) -->
      <div class="xl:col-span-8 flex flex-col gap-4">
        <!-- Tiêu đề -->
        <div class="field-group">
          <label class="field-label flex items-center gap-2">
            Tiêu đề bài viết
            <span class="text-red-500">*</span>
          </label>
          <div class="relative">
            <input
              type="text"
              bind:value={formTitle}
              oninput={() => { if (!editingId) formSlug = generateSlug(formTitle); }}
              placeholder="Nhập tiêu đề Bài viết..."
              class="field-input text-xl font-bold"
            />
            <div class="field-line"></div>
          </div>
          {#if errors?.title}
            <p class="text-red-500 text-[10px] mt-1 font-bold">{errors.title}</p>
          {/if}
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">

          <!-- Slug -->
          <div class="field-group">
            <label class="field-label">Đường dẫn (Slug)</label>
            <div class="relative flex items-center gap-2">
              <div class="relative flex-1">
                <input
                  type="text"
                  bind:value={formSlug}
                  placeholder="duong-dan-bai-viet"
                  disabled={isSlugLocked}
                  class="field-input font-mono text-sm text-cyan-400/80 {isSlugLocked ? 'opacity-50 cursor-not-allowed' : ''}"
                />
                <div class="field-line"></div>
              </div>
              <button
                onclick={() => { if (!isSlugLocked) formSlug = generateSlug(formTitle); }}
                disabled={isSlugLocked}
                title={isSlugLocked ? 'Slug bị khóa — bài viết đã Published, thay đổi slug sẽ làm mất link trên Search Engine' : 'Tạo lại slug từ tiêu đề'}
                class="shrink-0 flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[8px] font-black uppercase tracking-wider cursor-pointer
                  {isSlugLocked
                    ? 'bg-red-500/10 border border-red-500/20 text-red-400/60 cursor-not-allowed'
                    : 'bg-white/5 border border-white/10 text-white/40 hover:text-cyan-400 hover:border-cyan-500/30 hover:bg-cyan-500/5'}"
              >
                {#if isSlugLocked}
                  <Lock size={10} />
                  Khóa
                {:else}
                  <RefreshCw size={10} />
                  Tạo lại
                {/if}
              </button>
            </div>
            {#if isSlugLocked}
              <p class="text-[8px] text-red-400/50 italic">⚠ Slug đã khóa — bài viết đang Published. Đổi slug = mất link trên Google.</p>
            {/if}
          </div>

          <!-- Category + Status side by side -->
          <div class="grid grid-cols-2 gap-5">
            <!-- Chuyên mục -->
            <div class="field-group">
              <label class="field-label">Chuyên mục</label>
              <div class="relative">
                <select 
                  value={formCategory} 
                  onchange={(e) => formCategory = e.currentTarget.value}
                  class="field-select"
                >
                  {#each dbCategories as c}
                    <option value={c} selected={c === formCategory} class="bg-[#0f0f0f]">{c}</option>
                  {/each}
                </select>
                <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-white/20">
                  <ChevronDown size={13} />
                </div>
              </div>
            </div>

            <!-- Trạng thái -->
            <div class="field-group">
              <label class="field-label">Trạng thái</label>
              <div class="flex items-center gap-1 p-0.5 bg-black/40 rounded-xl border border-white/5">
                {#each [['PUBLISHED','Live'], ['DRAFT','Thảo'], ['ARCHIVED','Lưu']] as [val, lbl]}
                  <button
                    onclick={() => formStatus = val}
                    class="flex-1 py-1.5 text-[8px] font-black uppercase tracking-tight rounded-lg
                      {formStatus === val ? 'bg-white/10 text-cyan-400 border border-white/10' : 'text-gray-600 hover:text-white'}"
                  >{lbl}</button>
                {/each}
              </div>
            </div>
          </div>
        </div>

        <!-- Excerpt -->
        <div class="field-group">
          <label class="field-label">Tóm tắt (Excerpt)</label>
          <textarea
            bind:value={formExcerpt}
            rows="4"
            placeholder="Tóm tắt ngắn gọn về bài viết..."
            class="w-full bg-white/[0.02] border border-white/8 rounded-xl p-3 text-sm text-white/70 placeholder:text-white/15 outline-none focus:border-cyan-500/30 resize-none"
          ></textarea>
        </div>
      </div>

      <!-- Right Column: Featured Image (4/12) -->
      <div class="xl:col-span-4">
        <div class="field-label mb-3 flex items-center gap-2">
          <Image size={11} class="text-cyan-400/60" />
          Ảnh đại diện
        </div>

        <div class="relative">
          {#if formFeaturedImage && formFeaturedImage.includes('/')}
            <div class="relative group aspect-[16/10] rounded-xl overflow-hidden border {featuredImageBroken ? 'border-red-500/30 bg-red-500/5' : 'border-white/10 bg-black/60'}">
              {#if featuredImageBroken}
                <!-- Broken Featured Image State -->
                <div class="absolute inset-0 flex flex-col items-center justify-center gap-3">
                  <AlertTriangle size={28} class="text-red-400/60" />
                  <span class="text-[9px] font-black uppercase tracking-widest text-red-400/60">Ảnh bị lỗi</span>
                  <div class="flex items-center gap-3 z-20">
                    <button
                      onclick={(e) => { e.stopPropagation(); showMediaModal = true; }}
                      class="px-4 py-1.5 bg-white text-black text-[9px] font-black uppercase tracking-wider rounded-lg hover:bg-cyan-400 transition-colors shadow-xl"
                    >Thay thế ảnh</button>
                    <button
                      onclick={(e) => { e.stopPropagation(); formFeaturedImage = null; }}
                      class="p-1.5 bg-red-500/20 text-red-400 border border-red-500/20 rounded-lg hover:bg-red-500 hover:text-white transition-all"
                      title="Xóa ảnh"
                    ><Trash2 size={14} /></button>
                  </div>
                </div>
              {:else}
                <img
                  src={resolveMediaUrl(formFeaturedImage)}
                  alt="Featured"
                  class="w-full h-full object-cover opacity-90"
                  onerror={() => featuredImageBroken = true}
                />
                <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center gap-3">
                  <button
                    onclick={() => showMediaModal = true}
                    class="px-4 py-1.5 bg-white text-black text-[9px] font-black uppercase tracking-wider rounded-lg"
                  >Thay đổi</button>
                  <button
                    onclick={() => formFeaturedImage = null}
                    class="p-1.5 bg-red-500/20 text-red-400 border border-red-500/20 rounded-lg hover:bg-red-500 hover:text-white"
                  ><Trash2 size={14} /></button>
                </div>
              {/if}
              <div class="absolute bottom-2 left-2 px-2 py-0.5 bg-black/60 border border-white/10 rounded text-[7px] font-black text-cyan-400 uppercase tracking-wider">
                {formFeaturedImage.startsWith('http') ? 'External' : 'Local'}
              </div>
            </div>
          {:else}
            <button
              onclick={() => showMediaModal = true}
              class="w-full aspect-[16/10] rounded-xl border border-dashed border-white/10 bg-white/[0.01] hover:bg-white/[0.03] hover:border-cyan-500/30 flex flex-col items-center justify-center gap-2 group"
            >
              <div class="w-8 h-8 rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-400/50 group-hover:text-cyan-400">
                <ImagePlus size={18} />
              </div>
              <div class="flex flex-col items-center gap-0.5">
                <span class="text-[9px] font-black uppercase tracking-wider text-white/30 group-hover:text-cyan-400">Chọn ảnh</span>
                <span class="text-[8px] text-white/10 italic">Recommend: 16:9</span>
              </div>
            </button>
          {/if}
        </div>
      </div>
    </div>
  </section>

  <!-- ── SECTION 2: Nội Dung Chính ──────────────────── -->
  <section class="relative px-5 pt-4 pb-0" style="z-index: {Z_INDEX_ADMIN.SURFACE}">
    <div class="section-label">
      <FileText size={11} />
      Nội dung bài viết
    </div>

    <div class="mt-3">
      <NeuralEditor
        bind:content={formContent}
        topic={formTitle}
        editable={true}
        placeholder="Viết nội dung bài viết tại đây..."
        contentType="article"
        getMetadata={() => ({
          excerpt: formExcerpt,
          category: formCategory,
          seo_keywords: formSeoKeywords,
          faqs: formFaqs || []
        })}
        bind:analysisCache={formAnalysisCache}
        bind:analysisMetrics={formAnalysisMetrics}
        bind:analysisReport={formAnalysisReport}
      />
    </div>
  </section>

  <!-- ── SECTION 3: SEO ──────────────────── -->
  <section class="relative px-5 pt-4 pb-0" style="z-index: {Z_INDEX_ADMIN.SURFACE}">
    <div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
      <!-- 3B: SEO -->
      <div>
        <div class="flex items-center justify-between mb-4">
          <div class="section-label !mb-0 italic !tracking-[0.4em]">
            <Globe size={11} />
            SEO - TỐI ƯU TÌM KIẾM
          </div>
          <button
            onclick={handleAiSuggestSeo}
            disabled={isSuggestingSeo}
            class="flex items-center gap-1.5 px-4 py-1.5 bg-[#0a192f] border border-cyan-900/50 rounded-lg text-[9px] font-black uppercase tracking-widest text-cyan-400 hover:bg-[#112240] hover:border-cyan-400/50 disabled:opacity-40 transition-all cursor-pointer shadow-[0_0_15px_rgba(34,211,238,0.1)]"
          >
            {#if isSuggestingSeo}
              <div class="w-3 h-3 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin"></div>
              XOHI_DRAFTING...
            {:else}
              <Globe size={10} class="animate-pulse" />
              XOHI GỢI Ý SEO
            {/if}
          </button>
        </div>

        <div class="flex flex-col gap-5">
          <div class="field-group">
            <label class="field-label">ĐỊA CHỈ URL (SLUG)</label>
            <div class="relative flex items-center gap-2">
              <div class="relative flex-1">
                <input
                  type="text"
                  bind:value={formSlug}
                  placeholder="duong-dan-bai-viet"
                  disabled={isSlugLocked}
                  class="field-input font-mono text-sm text-cyan-400/80 {isSlugLocked ? 'opacity-50 cursor-not-allowed' : ''}"
                />
                <div class="field-line"></div>
              </div>
              <button
                onclick={() => { if (!isSlugLocked) formSlug = generateSlug(formTitle); }}
                disabled={isSlugLocked}
                class="shrink-0 flex items-center gap-1 px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-[8px] font-black uppercase tracking-wider text-white/40 hover:text-cyan-400 hover:border-cyan-500/30 transition-all cursor-pointer"
              >
                <RefreshCw size={10} />
                TẠO LẠI
              </button>
            </div>
          </div>

          <!-- SEO Title -->
          <div class="field-group">
            <label class="field-label">
              TIÊU ĐỀ SEO (META TITLE)
              <span class="ml-auto {seoTitleLen > 60 ? 'text-red-400' : 'text-cyan-500/60'}">{seoTitleLen}/60</span>
            </label>
            <div class="relative">
              <input type="text" bind:value={formSeoTitle}
                placeholder="Tiêu đề SEO (50-60 ký tự)..."
                class="field-input text-sm font-bold"
              />
              <div class="field-line"></div>
            </div>
          </div>

          <div class="field-group">
            <label class="field-label">TỪ KHÓA SEO (KEYWORDS)</label>
            <div class="relative">
              <input type="text" bind:value={formSeoKeywords}
                placeholder="từ-khóa-1, từ-khóa-2, ..."
                class="field-input text-sm font-mono text-cyan-400/70"
              />
              <div class="field-line"></div>
            </div>
          </div>

          <!-- SEO Description -->
          <div class="field-group">
            <label class="field-label">
              MÔ TẢ SEO (META DESCRIPTION)
              <span class="ml-auto {seoDescLen > 160 ? 'text-red-400' : 'text-cyan-500/60'}">{seoDescLen}/160</span>
            </label>
            <textarea bind:value={formSeoDescription} rows="4"
              placeholder="Mô tả chuẩn SEO (150-160 ký tự)..."
              class="w-full bg-white/[0.02] border border-white/8 rounded-2xl p-4 text-sm text-white/60 placeholder:text-white/15 outline-none focus:border-cyan-500/30 resize-none leading-relaxed"
            ></textarea>
          </div>
        </div>
      </div>

      <!-- 3C: Preview Column (Right) -->
      <div class="mt-3 flex flex-col gap-4">
        <div class="section-label mb-0 italic text-white/20">
          Bản xem trước trực quan
        </div>
        
        <div class="flex flex-col gap-4">
          <!-- Google Snippet Preview -->
          <div class="bg-[#111] rounded-xl p-4 border border-white/5 flex flex-col gap-1">
            <div class="flex items-center gap-2 mb-2">
              <div class="w-5 h-5 rounded-full bg-white/5 flex items-center justify-center text-[8px] font-black text-white/30">G</div>
              <span class="text-[8px] font-black uppercase tracking-[0.3em] text-white/20">Google Search Preview</span>
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
            <div class="flex items-center gap-1 p-1 bg-black/40 border border-white/5 rounded-xl w-fit">
              {#each [['facebook', 'Facebook'], ['twitter', 'X / Twitter']] as [id, label]}
                <button
                  onclick={() => socialPreviewTab = id as 'facebook' | 'twitter'}
                  class="px-4 py-1.5 text-[8px] font-black uppercase tracking-widest rounded-lg transition-all
                    {socialPreviewTab === id ? 'bg-white/10 text-white' : 'text-white/30 hover:text-white/60'}"
                >{label}</button>
              {/each}
            </div>

            {#if socialPreviewTab === 'facebook'}
              <!-- Facebook OG Card -->
              <div class="rounded-xl overflow-hidden border border-[#3a3b3c] bg-[#242526]">
                {#if ogImg}
                  <img src={ogImg} alt="OG" class="w-full h-[180px] object-cover opacity-90" />
                {:else}
                  <div class="w-full h-[160px] bg-[#3a3b3c] flex items-center justify-center">
                    <span class="text-[9px] text-white/20 uppercase tracking-widest">Chưa có ảnh đại diện</span>
                  </div>
                {/if}
                <div class="p-4 flex flex-col gap-1">
                  <span class="text-[9px] text-[#b0b3b8] uppercase tracking-widest truncate">micsmo.com</span>
                  <div class="text-sm font-bold text-[#e4e6eb] line-clamp-2 leading-snug">{ogTitle}</div>
                  <div class="text-[11px] text-[#b0b3b8] line-clamp-2">{ogDesc}</div>
                </div>
              </div>
            {:else}
              <!-- Twitter/X Card -->
              <div class="rounded-xl overflow-hidden border border-white/10 bg-[#16181c]">
                {#if ogImg}
                  <img src={ogImg} alt="OG" class="w-full h-[180px] object-cover opacity-90" />
                {:else}
                  <div class="w-full h-[150px] bg-white/5 flex items-center justify-center">
                    <span class="text-[9px] text-white/20 uppercase tracking-widest">Chưa có ảnh đại diện</span>
                  </div>
                {/if}
                <div class="p-4 flex flex-col gap-1.5">
                  <div class="text-sm font-bold text-white line-clamp-1">{ogTitle}</div>
                  <div class="text-[11px] text-white/50 line-clamp-2 leading-relaxed">{ogDesc}</div>
                  <span class="text-[9px] text-white/30 mt-1 flex items-center gap-1">
                    <Globe size={10} /> {ogUrl}
                  </span>
                </div>
              </div>
            {/if}
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ── SECTION 4: FAQ (GEO 2026) ──────────────────── -->
  <section class="relative px-5 pt-4 pb-0" style="z-index: {Z_INDEX_ADMIN.SURFACE}">
    <div class="flex items-center justify-between">
      <div class="section-label">
        <Globe size={11} />
        Hỏi đáp (FAQ Schema - GEO 2026)
      </div>
      <div class="flex items-center gap-2">
        <button
          onclick={handleAiSuggestFaqs}
          disabled={isSuggestingFaqs}
          class="flex items-center gap-1.5 px-4 py-2 bg-[#1a2742] border border-[#2a4a7f] rounded-lg text-[9px] font-black uppercase tracking-wider text-cyan-300 hover:bg-[#243860] disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer"
        >
          {#if isSuggestingFaqs}
            <div class="w-3 h-3 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin"></div>
            Đang tạo...
          {:else}
            <Sparkles size={12} />
            XOHI GỢI Ý FAQ
          {/if}
        </button>
        <button
          onclick={addFaqManual}
          class="flex items-center gap-1 px-3 py-2 bg-white/5 border border-amber-500/30 rounded-lg text-[9px] font-black uppercase tracking-wider text-amber-400 hover:bg-amber-500/10 transition-all cursor-pointer"
        >
          <Plus size={12} />
          Thêm tay
        </button>
      </div>
    </div>

    <div class="mt-3 flex flex-col gap-3">
      {#if formFaqs.length === 0}
        <div class="text-center py-8 border border-dashed border-white/10 rounded-xl">
          <p class="text-[10px] text-white/20 uppercase tracking-widest font-black">Chưa có câu hỏi FAQ.</p>
          <p class="text-[9px] text-white/10 italic mt-1">Thêm FAQ để tăng cường thứ hạng trên AI Search.</p>
        </div>
      {:else}
        {#each formFaqs as faq, i}
          <div class="bg-white/[0.02] border border-white/8 rounded-xl p-4 flex flex-col gap-2">
            <div class="flex items-center justify-between">
              <span class="text-[8px] font-black uppercase tracking-widest text-white/20">Câu hỏi {i + 1}</span>
              <button onclick={() => removeFaq(i)} class="p-1 text-red-400/50 hover:text-red-400 transition-colors cursor-pointer">
                <Trash2 size={12} />
              </button>
            </div>
            <input
              type="text"
              bind:value={faq.question}
              placeholder="Nhập câu hỏi..."
              class="w-full bg-white/[0.03] border border-white/8 rounded-lg px-3 py-2 text-sm text-white/80 placeholder:text-white/15 outline-none focus:border-cyan-500/40"
            />
            <span class="text-[8px] font-black uppercase tracking-widest text-white/15">Câu trả lời:</span>
            <textarea
              bind:value={faq.answer}
              rows="2"
              placeholder="Nhập câu trả lời..."
              class="w-full bg-white/[0.03] border border-white/8 rounded-lg px-3 py-2 text-sm text-white/60 placeholder:text-white/15 outline-none focus:border-cyan-500/40 resize-none"
            ></textarea>
          </div>
        {/each}
      {/if}
    </div>
  </section>

  <!-- ── ACTION BAR ─────────────────── -->
  <section class="relative px-5 pt-3" style="z-index: {Z_INDEX_ADMIN.LAYOUT_HEADER}">
    <div class="flex items-center justify-between gap-4 py-2">
      <div class="flex items-center gap-2 text-[9px] font-black uppercase tracking-widest text-white/20">
        <div class="w-1.5 h-1.5 rounded-full bg-cyan-400"></div>
        Hệ thống Neural LIVE đang đồng bộ
      </div>

      <div class="flex items-center gap-3">
        <button
          onclick={onClose}
          class="px-5 py-2.5 text-[10px] font-black uppercase tracking-wider text-white/30 hover:text-white cursor-pointer"
        >Hủy bỏ</button>

        <button
          onclick={onSave}
          disabled={isSaving}
          class="flex items-center gap-2 px-8 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 text-black rounded-xl text-[10px] font-black uppercase tracking-wider cursor-pointer hover:brightness-110 active:scale-95 disabled:opacity-40 disabled:grayscale disabled:cursor-not-allowed"
        >
          {#if isSaving}
            <div class="w-3 h-3 border-2 border-black/30 border-t-black rounded-full animate-spin"></div>
            Syncing...
          {:else}
            {editingId ? "Cập nhật" : "Đăng tải"}
          {/if}
        </button>
      </div>
    </div>
  </section>
</div>
</MissionControlShell>

<MediaVaultModal
  isOpen={showMediaModal}
  onClose={() => showMediaModal = false}
  bind:assets={featuredContextAssets}
  bind:selectedAvatarUrl
  bind:selectedAssetIndex
  onSelect={(url) => { 
    if (selectingOgImage) {
      formSeoOgImage = url;
    } else {
      formFeaturedImage = url;
    }
    showMediaModal = false; 
    selectingOgImage = false;
  }}
/>

<style>
  @reference "tailwindcss";

  /* Section Label */
  .section-label {
    @apply flex items-center gap-2 text-[9px] font-black uppercase tracking-[0.35em] text-white/30;
  }

  /* Section Divider */
  .section-divider {
    @apply mx-5 my-4 h-px bg-white/5;
  }

  /* Field Group */
  .field-group {
    @apply flex flex-col gap-2;
  }

  /* Field Label */
  .field-label {
    @apply flex items-center gap-2 text-[9px] font-black text-white/25 uppercase tracking-[0.25em];
  }

  /* Borderless Input */
  .field-input {
    @apply w-full bg-transparent border-b border-white/8 px-1 py-2 text-white placeholder:text-white/15 outline-none focus:border-cyan-500/50;
  }

  /* Focus underline */
  .field-line {
    @apply absolute bottom-0 left-0 w-0 h-[1px] bg-cyan-500/60;
  }
  :global(.field-group:focus-within .field-line) {
    width: 100%;
  }

  /* Glass Select */
  .field-select {
    @apply w-full bg-black/40 border border-white/8 rounded-xl py-2.5 px-3 text-sm text-white/70 focus:outline-none focus:border-cyan-500/40 appearance-none cursor-pointer;
  }
</style>
