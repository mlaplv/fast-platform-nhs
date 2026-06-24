<script lang="ts">
  import { onMount, untrack } from "svelte";
  import Globe from "@lucide/svelte/icons/globe";
  import FileText from "@lucide/svelte/icons/file-text";
  import Image from "@lucide/svelte/icons/image";
  import Settings from "@lucide/svelte/icons/settings";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import ImagePlus from "@lucide/svelte/icons/image-plus";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Lock from "@lucide/svelte/icons/lock";
  import Newspaper from "@lucide/svelte/icons/newspaper";
  import AlertTriangle from "@lucide/svelte/icons/triangle-alert";
  import Package from "@lucide/svelte/icons/package";
  import X from "@lucide/svelte/icons/x";
  import MissionControlShell from "../ui/MissionControlShell.svelte";
  import MediaVaultModal from "../../media/MediaVaultModal.svelte";
  import ProductPickerModal from "./ProductPickerModal.svelte";
  import NeuralEditor from "../ui/tiptap/NeuralEditor.svelte";
  import { resolveMediaUrl, processContentImages } from "$lib/state/utils";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import { apiClient } from "$lib/utils/apiClient";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  import { portal } from "$lib/core/actions/portal";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Plus from "@lucide/svelte/icons/plus";
  import type { AnalysisCache, CampaignMetrics, MediaAsset } from "$lib/state/types";

  const nanobot = useNanobot();
  
  let {
    isOpen = $bindable(false),
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
    formRelatedProductId = $bindable(),
    formRelatedProductName = $bindable(),
    formRelatedProductImage = $bindable(),
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
    formRelatedProductId: string | null;
    formRelatedProductName: string;
    formRelatedProductImage: string | null;
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

  // CNS V2.2: Neural Slug Synchronization
  // Auto-generate slug from title ONLY for new articles (to avoid breaking SEO on existing ones)
  $effect(() => {
    if (!editingId && formTitle && formTitle.trim()) {
      untrack(() => {
        formSlug = generateSlug(formTitle);
      });
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
    if (!formSeoKeywords) formSeoKeywords = "";
    if (formSeoOgImage === undefined) formSeoOgImage = null;
    if (formFeaturedImage === undefined) formFeaturedImage = null;
    if (!formFaqs) formFaqs = [];
  });

  const seoTitleLen = $derived(formSeoTitle?.length ?? 0);
  const seoDescLen = $derived(formSeoDescription?.length ?? 0);

  let socialPreviewTab = $state<'facebook' | 'twitter'>('facebook');
  const ogTitle = $derived(formSeoTitle || formTitle || 'Tiêu đề bài viết');
  const ogDesc = $derived(formSeoDescription || formExcerpt || 'Mô tả ngắn gọn về bài viết...');
  const ogUrl = $derived(`osmo/${formSlug || 'slug-bai-viet'}.p${editingId || 'pid'}`);
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
  let isSuggestingExcerpt = $state(false);
  let isSuggestingContent = $state(false);
  let isEditorFullScreen = $state(false);

  // V2026: Product Picker + XOHI Title Generator
  let showProductPicker = $state(false);
  let isSuggestingTitles = $state(false);
  let suggestedTitlesGrouped = $state<{
    seo_sge: string[];
    guide_advanced: string[];
    related_keywords: string[];
  }>({ seo_sge: [], guide_advanced: [], related_keywords: [] });
  let showTitleSuggestions = $state(false);

  const isProductSelected = $derived(
    !!formRelatedProductId &&
    formRelatedProductId !== 'null' &&
    formRelatedProductId !== 'undefined' &&
    formRelatedProductId.trim() !== ''
  );

  async function handleAiSuggestTitles() {
    if (!isProductSelected) {
      nanobot.showToast("Vui lòng chọn sản phẩm liên kết trước khi sinh tiêu đề.", "warning");
      return;
    }
    isSuggestingTitles = true;
    suggestedTitlesGrouped = { seo_sge: [], guide_advanced: [], related_keywords: [] };
    showTitleSuggestions = true;
    try {
      const res = await apiClient.post<{
        data: {
          seo_sge: string[];
          guide_advanced: string[];
          related_keywords: string[];
        }
      }>('/api/v1/articles/title-suggest', {
        category: formCategory || '',
        keywords: formSeoKeywords || '',
        product_id: formRelatedProductId || ''
      });
      if (
        res?.data &&
        (res.data.seo_sge?.length > 0 ||
         res.data.guide_advanced?.length > 0 ||
         res.data.related_keywords?.length > 0)
      ) {
        suggestedTitlesGrouped = res.data;
        const total = (res.data.seo_sge?.length ?? 0) + (res.data.guide_advanced?.length ?? 0) + (res.data.related_keywords?.length ?? 0);
        nanobot.showToast(`XOHI đã gợi ý ${total} tiêu đề theo nhóm.`, "success");
      } else {
        nanobot.showToast("Hệ thống AI hiện chưa phản hồi tiêu đề phù hợp. Vui lòng thử lại hoặc thay đổi từ khóa.", "error");
        showTitleSuggestions = false;
      }
    } catch (e) {
      console.error('XOHI Title suggest failed:', e);
      nanobot.showToast("Lỗi kết nối máy chủ AI hoặc hệ thống đang bảo trì. Vui lòng thử lại sau.", "error");
      showTitleSuggestions = false;
    } finally {
      isSuggestingTitles = false;
    }
  }

  function selectSuggestedTitle(title: string) {
    formTitle = title;
    if (!editingId) formSlug = generateSlug(title);
    showTitleSuggestions = false;
    suggestedTitlesGrouped = { seo_sge: [], guide_advanced: [], related_keywords: [] };
    nanobot.showToast("Đã chọn tiêu đề.", "success");
  }

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
    formFaqs = formFaqs.filter((_: unknown, i: number) => i !== index);
  }

  async function handleAiSuggestExcerpt() {
    if (!formTitle) {
      nanobot.showToast("Vui lòng nhập tiêu đề bài viết trước.", "warning");
      return;
    }
    isSuggestingExcerpt = true;
    try {
      const res = await apiClient.post<{ data: string }>('/api/v1/articles/excerpt-suggest', {
        title: formTitle,
        category: formCategory || '',
        content: formContent || ''
      });
      if (res?.data && typeof res.data === 'string' && res.data.trim()) {
        formExcerpt = res.data.trim();
        nanobot.showToast("XOHI đã sinh tóm tắt thành công.", "success");
      } else {
        nanobot.showToast("XOHI chưa sinh được tóm tắt. Thử lại nhé.", "error");
      }
    } catch (e) {
      console.error('XOHI Excerpt suggest failed:', e);
      nanobot.showToast("Lỗi kết nối AI.", "error");
    } finally {
      isSuggestingExcerpt = false;
    }
  }

  async function handleAiSuggestContent() {
    if (!formTitle) {
      nanobot.showToast("Vui lòng nhập tiêu đề bài viết trước.", "warning");
      return;
    }
    isSuggestingContent = true;
    try {
      const res = await apiClient.post<{ data: string }>('/api/v1/articles/content-suggest', {
        title: formTitle,
        category: formCategory || '',
        excerpt: formExcerpt || ''
      });
      if (res?.data && typeof res.data === 'string' && res.data.trim()) {
        formContent = res.data.trim();
        nanobot.showToast("XOHI đã sinh nội dung bài viết thành công.", "success");
      } else {
        nanobot.showToast("XOHI chưa sinh được nội dung. Thử lại nhé.", "error");
      }
    } catch (e) {
      console.error('XOHI Content generate failed:', e);
      nanobot.showToast("Lỗi kết nối AI.", "error");
    } finally {
      isSuggestingContent = false;
    }
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
        <!-- Sản phẩm liên quan -->
        <div class="field-group">
          <label class="field-label flex items-center gap-2">
            Sản phẩm liên quan
          </label>
          {#if formRelatedProductId && formRelatedProductName}
            <div class="flex items-center gap-3 p-2 bg-white/[0.02] border border-cyan-500/20 rounded-xl">
              <div class="w-8 h-8 rounded-lg overflow-hidden bg-white/5 shrink-0 border border-white/5">
                {#if formRelatedProductImage}
                  <img src={resolveMediaUrl(formRelatedProductImage)} alt={formRelatedProductName} class="w-full h-full object-cover" />
                {:else}
                  <div class="w-full h-full flex items-center justify-center"><Package size={12} class="text-white/10" /></div>
                {/if}
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-xs text-white/80 truncate font-medium">{formRelatedProductName}</div>
                <div class="text-[8px] text-cyan-400/60 font-black tracking-widest mt-0.5">ĐÃ LIÊN KẾT</div>
              </div>
              <div class="flex items-center gap-1.5">
                <button
                  onclick={() => showProductPicker = true}
                  class="px-2.5 py-1 bg-white/5 border border-white/10 rounded-lg text-[8px] font-black tracking-wider text-white/40 hover:text-cyan-400 hover:border-cyan-500/30 transition-all cursor-pointer"
                >Đổi</button>
                <button
                  onclick={() => { formRelatedProductId = null; formRelatedProductName = ''; formRelatedProductImage = null; }}
                  class="p-1 text-red-400/50 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all cursor-pointer"
                ><X size={12} /></button>
              </div>
            </div>
          {:else}
            <button
              onclick={() => showProductPicker = true}
              class="w-full py-2 px-3 rounded-xl border border-dashed border-white/10 bg-white/[0.01] hover:bg-white/[0.03] hover:border-cyan-500/30 flex items-center justify-between group transition-all cursor-pointer"
            >
              <div class="flex items-center gap-2">
                <Package size={12} class="text-white/20 group-hover:text-cyan-400" />
                <span class="text-xs text-white/40 group-hover:text-cyan-400">Chọn sản phẩm liên kết...</span>
              </div>
              <span class="text-[8px] font-black tracking-wider text-white/15 group-hover:text-cyan-400">CHỌN SẢN PHẨM</span>
            </button>
          {/if}
        </div>

        <!-- Tiêu đề -->
        <div class="field-group">
          <div class="flex items-center justify-between">
            <label class="field-label flex items-center gap-2">
              Tiêu đề bài viết
              <span class="text-red-500">*</span>
            </label>
            <button
              onclick={handleAiSuggestTitles}
              disabled={isSuggestingTitles || !isProductSelected}
              class="flex items-center gap-1 px-3 py-1 bg-[#0a192f] border border-cyan-900/40 rounded-lg text-[8px] font-black tracking-widest text-cyan-400 hover:bg-[#112240] hover:border-cyan-400/40 disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer"
              title={!isProductSelected ? "Vui lòng chọn sản phẩm liên kết trước khi sinh tiêu đề" : "Sinh tiêu đề tự động bằng AI"}
            >
              {#if isSuggestingTitles}
                <div class="w-2.5 h-2.5 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin"></div>
                Đang phân tích...
              {:else}
                <Sparkles size={9} />
                XOHI sinh tiêu đề
              {/if}
            </button>
          </div>
          <div class="relative">
            <input
              type="text"
              bind:value={formTitle}
              oninput={(e) => { 
                const val = e.currentTarget.value;
                if (!editingId && val) formSlug = generateSlug(val); 
              }}
              placeholder="Nhập tiêu đề Bài viết..."
              class="field-input text-xl font-bold"
            />
            <div class="field-line"></div>
          </div>
          {#if errors?.title}
            <p class="text-red-500 text-[10px] mt-1 font-bold">{errors.title}</p>
          {/if}

          <!-- XOHI Title Suggestions Dropdown -->
          {#if showTitleSuggestions}
            <div class="mt-2 bg-[#0a0a0a] border border-white/10 rounded-xl overflow-hidden shadow-[0_10px_30px_rgba(0,0,0,0.5)]">
              <div class="px-3 py-2 border-b border-white/5 flex items-center justify-between">
                <span class="text-[8px] font-black tracking-[0.3em] text-white/20">GỢI Ý TIÊU ĐỀ THEO PHÂN TÍCH XOHI</span>
                <button onclick={() => { showTitleSuggestions = false; suggestedTitlesGrouped = { seo_sge: [], guide_advanced: [], related_keywords: [] }; }} class="p-1 text-white/20 hover:text-white transition-colors cursor-pointer"><X size={10} /></button>
              </div>
              {#if isSuggestingTitles}
                <div class="flex items-center justify-center py-8 gap-2">
                  <div class="w-3.5 h-3.5 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin"></div>
                  <span class="text-[9px] text-white/20 tracking-widest font-black">ĐANG PHÂN TÍCH TOP 10 GOOGLE & SGE...</span>
                </div>
              {:else}
                <!-- Nhóm 1: SEO & SGE -->
                {#if suggestedTitlesGrouped.seo_sge?.length > 0}
                  <div class="px-3 py-1.5 bg-cyan-950/20 border-b border-white/5 flex items-center gap-1.5">
                    <div class="w-1 h-3 bg-cyan-400 rounded-full"></div>
                    <span class="text-[8px] font-black tracking-widest text-cyan-400/80">NHÓM 1: TỐI ƯU SEO & SGE (TÊN SẢN PHẨM)</span>
                  </div>
                  {#each suggestedTitlesGrouped.seo_sge as title, i}
                    <button
                      onclick={() => selectSuggestedTitle(title)}
                      class="w-full text-left px-4 py-2 text-xs text-white/70 hover:text-cyan-400 hover:bg-cyan-500/5 border-b border-white/5 last:border-0 transition-all cursor-pointer flex items-center gap-2.5"
                    >
                      <span class="shrink-0 w-4 h-4 rounded bg-cyan-500/10 flex items-center justify-center text-[8px] font-black text-cyan-400">{i + 1}</span>
                      <span class="leading-normal">{title}</span>
                    </button>
                  {/each}
                {/if}

                <!-- Nhóm 2: Hướng dẫn & Nâng cao -->
                {#if suggestedTitlesGrouped.guide_advanced?.length > 0}
                  <div class="px-3 py-1.5 bg-purple-950/20 border-b border-b-white/5 border-t border-t-white/5 flex items-center gap-1.5">
                    <div class="w-1 h-3 bg-purple-400 rounded-full"></div>
                    <span class="text-[8px] font-black tracking-widest text-purple-400/80">NHÓM 2: HƯỚNG DẪN & NÂNG CAO (CÁCH DÙNG, MẸO...)</span>
                  </div>
                  {#each suggestedTitlesGrouped.guide_advanced as title, i}
                    <button
                      onclick={() => selectSuggestedTitle(title)}
                      class="w-full text-left px-4 py-2 text-xs text-white/70 hover:text-purple-400 hover:bg-purple-500/5 border-b border-white/5 last:border-0 transition-all cursor-pointer flex items-center gap-2.5"
                    >
                      <span class="shrink-0 w-4 h-4 rounded bg-purple-500/10 flex items-center justify-center text-[8px] font-black text-purple-400">{i + 1}</span>
                      <span class="leading-normal">{title}</span>
                    </button>
                  {/each}
                {/if}

                <!-- Nhóm 3: Từ khóa phụ bao phủ -->
                {#if suggestedTitlesGrouped.related_keywords?.length > 0}
                  <div class="px-3 py-1.5 bg-amber-950/20 border-b border-b-white/5 border-t border-t-white/5 flex items-center gap-1.5">
                    <div class="w-1 h-3 bg-amber-400 rounded-full"></div>
                    <span class="text-[8px] font-black tracking-widest text-amber-400/80">NHÓM 3: TỪ KHÓA PHỤ LIÊN QUAN (TĂNG ĐỘ BAO PHỦ)</span>
                  </div>
                  {#each suggestedTitlesGrouped.related_keywords as title, i}
                    <button
                      onclick={() => selectSuggestedTitle(title)}
                      class="w-full text-left px-4 py-2 text-xs text-white/70 hover:text-amber-400 hover:bg-amber-500/5 border-b border-white/5 last:border-0 transition-all cursor-pointer flex items-center gap-2.5"
                    >
                      <span class="shrink-0 w-4 h-4 rounded bg-amber-500/10 flex items-center justify-center text-[8px] font-black text-amber-400">{i + 1}</span>
                      <span class="leading-normal">{title}</span>
                    </button>
                  {/each}
                {/if}
              {/if}
            </div>
          {/if}
        </div>

        <!-- Category + Status side by side -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
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
                    class="flex-1 py-1.5 text-[8px] font-black tracking-tight rounded-lg
                      {formStatus === val ? 'bg-white/10 text-cyan-400 border border-white/10' : 'text-gray-600 hover:text-white'}"
                  >{lbl}</button>
                {/each}
            </div>
          </div>
        </div>

        <!-- Excerpt -->
        <div class="field-group">
          <div class="flex items-center justify-between">
            <label class="field-label">Tóm tắt (Excerpt)</label>
            <button
              onclick={handleAiSuggestExcerpt}
              disabled={isSuggestingExcerpt || !formTitle}
              class="flex items-center gap-1 px-3 py-1 bg-[#0a192f] border border-cyan-900/40 rounded-lg text-[8px] font-black tracking-widest text-cyan-400 hover:bg-[#112240] hover:border-cyan-400/40 disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer"
            >
              {#if isSuggestingExcerpt}
                <div class="w-2.5 h-2.5 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin"></div>
                Đang sinh...
              {:else}
                <Sparkles size={9} />
                XOHI sinh tóm tắt
              {/if}
            </button>
          </div>
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
                  <span class="text-[9px] font-black tracking-widest text-red-400/60">Ảnh bị lỗi</span>
                  <div class="flex items-center gap-3 z-20">
                    <button
                      onclick={(e) => { e.stopPropagation(); showMediaModal = true; }}
                      class="px-4 py-1.5 bg-white text-black text-[9px] font-black tracking-wider rounded-lg hover:bg-cyan-400 transition-colors shadow-xl"
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
                    class="px-4 py-1.5 bg-white text-black text-[9px] font-black tracking-wider rounded-lg"
                  >Thay đổi</button>
                  <button
                    onclick={() => formFeaturedImage = null}
                    class="p-1.5 bg-red-500/20 text-red-400 border border-red-500/20 rounded-lg hover:bg-red-500 hover:text-white"
                  ><Trash2 size={14} /></button>
                </div>
              {/if}
              <div class="absolute bottom-2 left-2 px-2 py-0.5 bg-black/60 border border-white/10 rounded text-[7px] font-black text-cyan-400 tracking-wider">
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
                <span class="text-[9px] font-black tracking-wider text-white/30 group-hover:text-cyan-400">Chọn ảnh</span>
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
    <div class="flex items-center justify-between mb-3">
      <div class="section-label">
        <FileText size={11} />
        Nội dung bài viết
      </div>
      <button
        onclick={handleAiSuggestContent}
        disabled={isSuggestingContent || !formTitle}
        class="flex items-center gap-1.5 px-4 py-1.5 bg-[#0a192f] border border-cyan-900/50 rounded-lg text-[9px] font-black tracking-widest text-cyan-400 hover:bg-[#112240] hover:border-cyan-400/50 disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer shadow-[0_0_12px_rgba(34,211,238,0.08)]"
      >
        {#if isSuggestingContent}
          <div class="w-3 h-3 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin"></div>
          XOHI_DRAFTING...
        {:else}
          <Sparkles size={10} class="animate-pulse" />
          XOHI sinh nội dung
        {/if}
      </button>
    </div>

    <div>
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
        bind:fullScreen={isEditorFullScreen}
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
            class="flex items-center gap-1.5 px-4 py-1.5 bg-[#0a192f] border border-cyan-900/50 rounded-lg text-[9px] font-black tracking-widest text-cyan-400 hover:bg-[#112240] hover:border-cyan-400/50 disabled:opacity-40 transition-all cursor-pointer shadow-[0_0_15px_rgba(34,211,238,0.1)]"
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
                onclick={() => { 
                  if (isSlugLocked) return;
                  const newSlug = generateSlug(formTitle || "");
                  if (newSlug === formSlug) {
                    nanobot.showToast("Đường dẫn đã tối ưu theo tiêu đề.", "info");
                  } else {
                    formSlug = newSlug;
                    nanobot.showToast("Đã cập nhật đường dẫn SEO.", "success");
                  }
                }}
                disabled={isSlugLocked}
                class="shrink-0 flex items-center gap-1 px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-[8px] font-black tracking-wider text-white/40 hover:text-cyan-400 hover:border-cyan-500/30 transition-all cursor-pointer"
              >
                <RefreshCw size={10} />
                TẠO LẠI
              </button>
            </div>
            {#if isSlugLocked}
              <p class="text-[8px] text-red-400/50 italic mt-1.5">⚠ Slug đã khóa — bài viết đang Published. Đổi slug = mất link trên Google.</p>
            {/if}
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
              <span class="text-[8px] font-black tracking-[0.3em] text-white/20">Google Search Preview</span>
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
                  class="px-4 py-1.5 text-[8px] font-black tracking-widest rounded-lg transition-all
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
                    <span class="text-[9px] text-white/20 tracking-widest">Chưa có ảnh đại diện</span>
                  </div>
                {/if}
                <div class="p-4 flex flex-col gap-1">
                  <span class="text-[9px] text-[#b0b3b8] tracking-widest truncate">osmo</span>
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
                    <span class="text-[9px] text-white/20 tracking-widest">Chưa có ảnh đại diện</span>
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
          class="flex items-center gap-1.5 px-4 py-2 bg-[#1a2742] border border-[#2a4a7f] rounded-lg text-[9px] font-black tracking-wider text-cyan-300 hover:bg-[#243860] disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer"
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
          class="flex items-center gap-1 px-3 py-2 bg-white/5 border border-amber-500/30 rounded-lg text-[9px] font-black tracking-wider text-amber-400 hover:bg-amber-500/10 transition-all cursor-pointer"
        >
          <Plus size={12} />
          Thêm tay
        </button>
      </div>
    </div>

    <div class="mt-3 flex flex-col gap-3">
      {#if formFaqs.length === 0}
        <div class="text-center py-8 border border-dashed border-white/10 rounded-xl">
          <p class="text-[10px] text-white/20 tracking-widest font-black">Chưa có câu hỏi FAQ.</p>
          <p class="text-[9px] text-white/10 italic mt-1">Thêm FAQ để tăng cường thứ hạng trên AI Search.</p>
        </div>
      {:else}
        {#each formFaqs as faq, i}
          <div class="bg-white/[0.02] border border-white/8 rounded-xl p-4 flex flex-col gap-2">
            <div class="flex items-center justify-between">
              <span class="text-[8px] font-black tracking-widest text-white/20">Câu hỏi {i + 1}</span>
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
            <span class="text-[8px] font-black tracking-widest text-white/15">Câu trả lời:</span>
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
  <div use:portal={isEditorFullScreen}>
    <section 
      class="{isEditorFullScreen ? 'fixed bottom-0 left-0 right-0 z-[950000]' : 'relative mt-auto'} px-8 py-10 flex justify-end items-center pointer-events-none" 
    >
      <div class="flex items-center gap-4 pointer-events-auto">
        <button
          onclick={onClose}
          class="px-8 py-3 bg-[#1a1a1a] text-white/60 hover:text-white rounded-xl text-[10px] font-black tracking-[0.2em] shadow-[0_10px_30px_rgba(0,0,0,0.5)] cursor-pointer active:scale-95 transition-all"
        >Hủy bỏ</button>

        <button
          onclick={onSave}
          disabled={isSaving}
          class="px-10 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 text-black rounded-xl text-[10px] font-black tracking-wider shadow-[0_10px_40px_rgba(6,182,212,0.3)] disabled:opacity-40 disabled:grayscale disabled:cursor-not-allowed cursor-pointer active:scale-95 transition-all"
        >
          {#if isSaving}
            <div class="flex items-center gap-3">
              <div class="w-3 h-3 border-2 border-black/30 border-t-black rounded-full animate-spin"></div>
              <span>Syncing...</span>
            </div>
          {:else}
            {editingId ? "Cập nhật" : "Đăng tải"}
          {/if}
        </button>
      </div>
    </section>
  </div>
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

<ProductPickerModal
  isOpen={showProductPicker}
  bind:selectedProductId={formRelatedProductId}
  onClose={() => showProductPicker = false}
  onSelect={(product) => {
    formRelatedProductId = product.id;
    formRelatedProductName = product.name;
    formRelatedProductImage = product.image;
    showProductPicker = false;
  }}
/>

<style>
  @reference "tailwindcss";

  /* Section Label */
  .section-label {
    @apply flex items-center gap-2 text-[9px] font-black tracking-[0.35em] text-white/30;
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
    @apply flex items-center gap-2 text-[9px] font-black text-white/25 tracking-[0.25em];
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
