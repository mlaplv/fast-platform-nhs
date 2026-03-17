<script lang="ts">
  import { onMount, untrack } from "svelte";
  import { fade } from "svelte/transition";
  import { apiClient } from "$lib/utils/apiClient";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { vuiController } from "$lib/vui";
  import { xohiImageStore } from "$lib/state/xohiImage.svelte";
  import Header from "./content-factory/Header.svelte";
  import Timeline from "./content-factory/Timeline.svelte";
  import IdeaStep from "./content-factory/IdeaStep.svelte";
  import AssetStep from "./content-factory/AssetStep.svelte";
  import OutlineStep from "./content-factory/OutlineStep.svelte";
  import DraftStep from "./content-factory/DraftStep.svelte";
  import ValidationPreviewStep from "./content-factory/ValidationPreviewStep.svelte";
  import PublishStep from "./content-factory/PublishStep.svelte";
  import ActionButtons from "./content-factory/ActionButtons.svelte";
  import GateBlockModal from "./content-factory/GateBlockModal.svelte";
  import TiptapEditor from "./tiptap/TiptapEditor.svelte";
  import type {
    CampaignKeywords,
    CampaignMetrics,
    MediaAsset,
    CampaignOutline,
    CopyrightResult,
    SEOResult,
    AIInspectResult
  } from "$lib/state/types";

  interface Props {
    campaign_id: string;
    step: number;
    status: string;
    progress_msg?: string;
    title?: string;
    keywords: CampaignKeywords;
    assets: (MediaAsset | string)[];
    reserve_assets: string[];
    outline: CampaignOutline;
    draft_content: string;
    finalHtml: string;
    selectedAvatarUrl: string | null;
    selectedAssetIndex: number;
    creation_config: Record<string, unknown>;
    analysis_cache: {
      copyright?: { data: CopyrightResult };
      seo?: { data: SEOResult };
      ai_inspect?: { data: AIInspectResult };
    };
    analysis_metrics: CampaignMetrics;
  }

  let {
    campaign_id,
    step = $bindable(),
    status = $bindable(),
    progress_msg = $bindable(),
    title = $bindable(),
    keywords = $bindable(),
    assets = $bindable(),
    reserve_assets = $bindable(),
    outline = $bindable(),
    draft_content = $bindable(),
    finalHtml = $bindable(),
    selectedAvatarUrl = $bindable(),
    selectedAssetIndex = $bindable(),
    creation_config = $bindable(),
    analysis_cache = $bindable(),
    analysis_metrics = $bindable()
  }: Props = $props();

  // -- Local UI Orchestration --
  let viewingStep = $state(step || 1);
  let isEditing = $state(false);
  let isProcessing = $derived(status === "PROCESSING");
  let isLoading = $state(false);
  
  // Rule R82.43: Global Spinner Sync — Ensure buttons re-enable when AI finishing
  $effect(() => {
    if (status !== "PROCESSING") {
      untrack(() => { isLoading = false; });
    }
  });

  let isPublishing = $state(false);
  let resultMsg = $state("");
  let customImageUrl = $state("");
  let editedKeywords = $state<CampaignKeywords>({});
  let editedConfig = $state<Record<string, unknown>>({});
  let editedDraft = $state("");
  let editedOutline = $state(""); // CNS V85: Separate buffer for Step 3 to prevent draft pollution
  let editorRef = $state<TiptapEditor | null>(null); // Tiptap component ref
  let maxStepSeen = $state(step);

  // -- Gate Score State (synced from DraftStep via bind:) --
  let copyrightScore = $state<number | null>(null);
  let seoScore = $state<number | null>(null);
  let aiScore = $state<number | null>(null);

  // Phase 73: Initialize scores from metrics & cache (Single Source of Truth)
  $effect(() => {
    // 1. Data Source: analysis_metrics (Gold DB)
    if (analysis_metrics) {
      if (copyrightScore === null && analysis_metrics.unique_score !== undefined) {
        copyrightScore = Math.round(analysis_metrics.unique_score * 100);
      }
      if (seoScore === null && analysis_metrics.seo_score !== undefined) {
        seoScore = analysis_metrics.seo_score;
      }
      if (aiScore === null && analysis_metrics.ai_ready_score !== undefined) {
        aiScore = analysis_metrics.ai_ready_score;
      }
    }

    // 2. Data Source: analysis_cache (In-memory/Recent)
    if (analysis_cache) {
      if (copyrightScore === null && analysis_cache.copyright?.data?.uniqueness_score !== undefined) {
        copyrightScore = Math.round(analysis_cache.copyright.data.uniqueness_score * 100);
      }
      if (seoScore === null && analysis_cache.seo?.data?.total_score !== undefined) {
        seoScore = analysis_cache.seo.data.total_score;
      }
      if (aiScore === null && analysis_cache.ai_inspect?.data?.geo_score !== undefined) {
        aiScore = analysis_cache.ai_inspect.data.geo_score;
      }
    }
  });

  // -- Gate Block Modal --
  let showGateModal = $state(false);
  let gateBlockers = $state<Array<{ label: string; current: string; required: string; tab: 'copyright' | 'seo' | 'ai' }>>([]);
  let focusTabFromModal = $state<'copyright' | 'seo' | 'ai' | null>(null);

  const DEFAULT_CONFIG = {
    style: "Chuyên nghiệp",
    word_count: 500,
    max_assets: 10,
    max_sections: 3
  };

  // -- Sync & Initialization --
  // Rule R82.41: Smart Auto-Advance — Only jump to current step if it increases
  $effect(() => { 
    if (step > maxStepSeen) {
      maxStepSeen = step;
      viewingStep = step;
    }
  });

  onMount(() => {
    // Rule R82.10.2: Content Integrity Guard — Manual fallbacks for bindable props without defaults (Svelte 5 safety)
    if (step === undefined) step = 1;
    if (status === undefined) status = "IDLE";
    if (progress_msg === undefined) progress_msg = "";
    if (keywords === undefined) keywords = {};
    if (assets === undefined) assets = [];
    if (reserve_assets === undefined) reserve_assets = [];
    if (outline === undefined) outline = {};
    if (draft_content === undefined) draft_content = "";
    if (creation_config === undefined) creation_config = {};
    if (selectedAvatarUrl === undefined) selectedAvatarUrl = null;
    if (selectedAssetIndex === undefined) selectedAssetIndex = 0;
    if (analysis_cache === undefined) analysis_cache = {};
    if (analysis_metrics === undefined) analysis_metrics = {};

    // Local UI Orchestration Initialization
    
    viewingStep = step;
    // Merge defaults with creation_config to ensure all keys are present
    const baseConfig = creation_config && Object.keys(creation_config).length > 0
      ? creation_config 
      : (keywords?.creation_config || {});
    
    editedConfig = { ...DEFAULT_CONFIG, ...baseConfig };
    if (typeof editedConfig !== 'object') editedConfig = {};
    editedKeywords = JSON.parse(JSON.stringify(keywords || {}));
    
    // CNS V73.5: Minimal state restoration — Don't pollute draft_content with outline
    // The child components (OutlineStep, DraftStep) handle display-only fallbacks
    editedDraft = draft_content || "";
    editedOutline = outline?.html || "";
    
    // Ensure finalHtml is not empty if we are in step 6
    if (viewingStep >= 6 && !finalHtml) {
      finalHtml = draft_content;
    }
    
    // Ensure viewingStep is valid
    if (viewingStep < 1 || viewingStep > 6) viewingStep = step || 1;
    if (viewingStep < 1) viewingStep = 1;
  });

  // Rule R82.42: Reactive Prep — Ensure editedDraft is ready for next steps
  $effect(() => {
    // CNS V73.8: Expert Streaming Sync
    // When generating (status === "PROCESSING") or viewing (isEditing === false), 
    // we must sync the external draft_content (SSE/Pulse) to our local buffer.
    const source = draft_content || finalHtml || "";
    
    // Expert Optimizer: Always prioritize source if it's non-empty and has changed
    // This fixed the "white screen" when streaming starts.
    if (source && (isProcessing || !isEditing)) {
      if (source !== editedDraft) {
        untrack(() => {
          editedDraft = source;
          // Ensure draft_content itself is never empty if we have source
          if (!draft_content) draft_content = source;
        });
      }
    }
    
    // R102: Content integrity safeguard — Ensure draft_content is synchronized with source if missing
    // But ONLY if source is actually a draft, not a fallback
    if (!draft_content && source) {
      untrack(() => { draft_content = source; });
    }
  });

  // Keep editedConfig in sync for Ghost UI summary display (Phase 33)
  $effect(() => {
     if (!isEditing && creation_config) {
       const next = { ...DEFAULT_CONFIG, ...creation_config };
       if (JSON.stringify(next) !== JSON.stringify(untrack(() => editedConfig))) {
         editedConfig = next;
       }
     }
  });

  // Sync keywords to editedKeywords when not editing
  $effect(() => {
    if (!isEditing && keywords) {
      if (JSON.stringify(keywords) !== JSON.stringify(untrack(() => editedKeywords))) {
        editedKeywords = JSON.parse(JSON.stringify(keywords));
      }
    }
  });

  // -- Event Handlers --
  async function handleApprove() {
    if (isLoading) return;

    // Gate Check — chỉ áp dụng ở Step 4 (bản thảo)
    if (viewingStep === 4) {
      const blockers: typeof gateBlockers = [];
      if (copyrightScore === null || copyrightScore < 90) {
        blockers.push({
          label: '🔍 COPYRIGHT',
          current: copyrightScore !== null ? `${copyrightScore}%` : 'Chưa kiểm tra',
          required: '≥ 90%',
          tab: 'copyright'
        });
      }
      if (seoScore === null || seoScore < 70) {
        blockers.push({
          label: '📊 SEO Score',
          current: seoScore !== null ? `${seoScore}/100` : 'Chưa kiểm tra',
          required: '≥ 70/100',
          tab: 'seo'
        });
      }
      if (blockers.length > 0) {
        gateBlockers = blockers;
        showGateModal = true;
        vuiController.speak('Bài viết chưa đủ điều kiện. Vui lòng xem hướng dẫn và sửa lỗi trước khi duyệt.');
        return;
      }
    }

    isLoading = true;
    try {
      const payload = isEditing ? { 
        edited_data: viewingStep === 1 
          ? { ...editedKeywords, creation_config: editedConfig } 
          : { html: viewingStep === 3 ? editedOutline : editedDraft } 
      } : {};
      await apiClient.post(`/api/v1/content/campaigns/${campaign_id}/approve`, payload);
      
      // Update local props to prevent $effect sync back to old values
      if (viewingStep === 1) {
        // CNS V72: Inclusion of creation_config in keywords prop sync for effect equality
        keywords = { ...editedKeywords, creation_config: { ...editedConfig } };
        creation_config = { ...editedConfig };
      } else if (viewingStep === 3) {
        outline = { ...outline, html: editedOutline };
      } else if (viewingStep === 4) {
        draft_content = editedDraft;
      }

      isEditing = false;
      const stepNames: Record<number, string> = {
        1: "ý tưởng và từ khóa",
        2: "các hình ảnh",
        3: "dàn ý bài viết",
        4: "bản thảo nội dung",
        5: "kết quả kiểm tra",
        6: "bài viết hoàn thiện"
      };
      vuiController.speak(`Đã duyệt ${stepNames[viewingStep] || 'thành công'}!`);
    } catch (e) {
      console.error("Approve failed:", e);
    } finally {
      isLoading = false;
    }
  }

  async function handleRetry() {
    if (isLoading) return;
    isLoading = true;
    try {
      await apiClient.post(`/api/v1/content/campaigns/${campaign_id}/retry`);
      editedDraft = ""; // R82.46: Clear edit buffer on retry to show fresh AI output
      isEditing = false;
      
      const stepNames: Record<number, string> = {
        1: "ý tưởng và từ khóa",
        2: "các hình ảnh",
        3: "dàn ý bài viết",
        4: "bản thảo nội dung",
        5: "kết quả kiểm tra",
        6: "bài viết hoàn thiện"
      };
      vuiController.speak(`Đang chạy lại bước ${stepNames[viewingStep] || 'này'}.`);
    } catch (e) {
      console.error("Retry failed:", e);
    } finally {
      isLoading = false;
    }
  }

  async function handleUpdateMetadata() {
    isLoading = true;
    try {
      const payload = viewingStep === 1 
        ? { keywords: { ...editedKeywords, creation_config: editedConfig } } 
        : (viewingStep === 3 ? { outline_data: { html: editedOutline } } : { draft_content: editedDraft });
        
      await apiClient.patch(`/api/v1/content/campaigns/${campaign_id}`, payload);
      
      if (viewingStep === 1) {
        // CNS V72: Inclusion of creation_config in keywords prop sync for effect equality
        keywords = { ...editedKeywords, creation_config: { ...editedConfig } };
        creation_config = { ...editedConfig };
      } else if (viewingStep === 3) {
        outline = { ...outline, html: editedOutline };
      } else if (viewingStep === 4) {
        draft_content = editedDraft;
      }
      isEditing = false;
      editedDraft = ""; // R82.47: Clear edit buffer after successful save
      editedOutline = "";
      
      const stepNames: Record<number, string> = {
        1: "ý tưởng và từ khóa",
        2: "các hình ảnh",
        3: "dàn ý bài viết",
        4: "bản thảo nội dung",
        5: "kết quả kiểm tra",
        6: "bài viết hoàn thiện"
      };
      vuiController.speak(`Đã lưu ${stepNames[viewingStep] || 'thành công'}.`);
    } catch (e) {
      console.error("Update failed:", e);
    } finally {
      isLoading = false;
    }
  }

  async function handlePublish() {
    if (isPublishing) return;
    isPublishing = true;
    try {
      await apiClient.post(`/api/v1/content/campaigns/${campaign_id}/publish`);
      resultMsg = "Xuất bản thành công!";
      vuiController.speak("Bài viết đã được xuất bản.");
    } catch (e) {
      console.error("Publish failed:", e);
    } finally {
      isPublishing = false;
    }
  }

  async function syncAssetChanges(newIndex?: number) {
    try {
      // Phase 15.3: Sử dụng dữ liệu từ Store nếu đang ở Step 2
      const currentAssets = viewingStep === 2 ? xohiImageStore.assets : assets;
      const currentAvatar = viewingStep === 2 ? (xohiImageStore.primaryAsset?.filePath || xohiImageStore.primaryAsset?.url) : selectedAvatarUrl;

      // Rule R109: REST Alignment — Use keys expected by ActionHandler.update_metadata
      await apiClient.patch(`/api/v1/content/campaigns/${campaign_id}`, {
        assets: currentAssets, // Backend expects 'assets' NOT 'assets_data' in PATCH alias
        avatar: currentAvatar || selectedAvatarUrl,
        selected_index: newIndex ?? selectedAssetIndex,
        gold_metadata: { reserve_assets } // R120: Persist reserve list
      });
    } catch (e) { console.error("Sync failed:", e); }
  }

  function handleImageError(url: string) {
    // Phase 15.3: Xóa ảnh lỗi thông qua Store để kích hoạt hiệu ứng phản ứng
    const asset = xohiImageStore.assets.find(a => a.filePath === url || a.url === url);
    if (asset) {
      xohiImageStore.removeAsset(asset.id);
      vuiController.speak("Đã tự động loại bỏ ảnh không tải được.");
    } else {
      assets = assets.filter(a => typeof a === 'string' ? a !== url : a.url !== url);
    }
  }

  // deleteAsset legacy has been replaced by xohiImageStore.removeAsset in sub-components


  function handleMouseMove(e: MouseEvent) {
    const el = e.currentTarget as HTMLElement;
    const rect = el.getBoundingClientRect();
    el.style.setProperty('--mouse-x', `${((e.clientX - rect.left) / rect.width) * 100}%`);
    el.style.setProperty('--mouse-y', `${((e.clientY - rect.top) / rect.height) * 100}%`);
  }

  function handleSelectKeyword(kw: string) {
    keywords.primary_keyword = kw;
    vuiController.speak(`Đã chọn ${kw}.`);
    apiClient.patch(`/api/v1/content/campaigns/${campaign_id}`, { keywords });
  }

  let lastScrollY = 0;
  let isCompact = $state(false);

  function handleScroll(e: Event) {
    const target = e.target as HTMLElement;
    const currentScrollY = target.scrollTop;
    
    // Rule: Compact when scrolling down, expand when scrolling up or at extremeties
    if (currentScrollY > lastScrollY && currentScrollY > 100) {
      isCompact = true;
    } else {
      isCompact = false;
    }
    
    // Auto-expand at bottom
    if (target.scrollHeight - target.scrollTop <= target.clientHeight + 50) {
      isCompact = false;
    }
    
    lastScrollY = currentScrollY;
  }
</script>

<div 
  class="content-review-card w-full {nanobot.isExpanded ? 'h-full bg-transparent' : 'h-full md:h-[85vh] bg-[#0c0a0f]/80 md:backdrop-blur-3xl md:border md:border-white/10'} flex flex-col p-4 md:p-6 transition-all duration-700 overflow-hidden md:shadow-[0_30px_100px_rgba(0,0,0,0.8)] rounded-none z-[150000]"
  in:fade={{ duration: 600 }}
>
  <Header 
    {viewingStep} {status} {progress_msg} {campaign_id} 
    bind:isEditing 
    toggleExpand={ () => { nanobot.toggleExpand(); } }
    isExpanded={nanobot.isExpanded}
    creation_config={isEditing ? editedConfig : creation_config}
  />

  <Timeline {step} bind:viewingStep bind:isEditing />

  <div 
    class="flex-1 min-h-0 flex flex-col p-4 md:p-5 {nanobot.isExpanded ? 'p-8' : ''} {viewingStep === 6 ? 'overflow-hidden pb-5' : 'overflow-y-auto pb-32 md:pb-5'} custom-scrollbar relative z-10"
    onscroll={handleScroll}
  >
    {#if viewingStep === 1}
      <IdeaStep 
        bind:isEditing 
        {campaign_id} 
        bind:keywords 
        bind:editedKeywords
        creation_config={creation_config}
        bind:editedConfig
        {handleSelectKeyword}
        {handleUpdateMetadata}
        {isLoading} 
      />
      {:else if viewingStep === 2}
        <AssetStep
          {isProcessing} isExpanded={nanobot.isExpanded}
          bind:assets bind:reserve_assets bind:customImageUrl bind:selectedAvatarUrl bind:selectedAssetIndex
          {handleImageError} {syncAssetChanges} {handleRetry} {handleMouseMove}
        />
      {:else if viewingStep === 3}
        <OutlineStep 
          {isEditing} bind:editedOutline={editedOutline} {outline} {assets} 
          isExpanded={nanobot.isExpanded} editorAnnotations={[]} {step}
        />
      {:else if viewingStep === 4}
        <DraftStep 
          {campaign_id} {isEditing} bind:editedDraft {draft_content} 
          {assets} isExpanded={nanobot.isExpanded} bind:editorRef {outline}
          {analysis_cache} {analysis_metrics}
          bind:copyrightScore bind:seoScore bind:aiScore
        />
      {:else if viewingStep === 5}
        <ValidationPreviewStep
          {draft_content} {assets} {keywords}
          {copyrightScore} {seoScore} {aiScore}
          {analysis_cache} isExpanded={nanobot.isExpanded}
        />
      {:else if viewingStep === 6}
        <PublishStep
          {selectedAvatarUrl} bind:viewingStep bind:isEditing bind:keywords
          bind:finalHtml bind:draft_content {assets} {campaign_id} {apiClient}
          {copyrightScore} {seoScore} {aiScore} {analysis_cache}
        />
      {/if}
  </div>

  {#if resultMsg}
    <div class="mt-6 p-4 bg-blue-500/10 border border-blue-500/20 text-blue-300 text-[13px] font-bold">
      {resultMsg}
    </div>
  {/if}

  <ActionButtons
    {isLoading} {status} bind:viewingStep {step} bind:isEditing {isProcessing} {isPublishing}
    {handleRetry} {handleUpdateMetadata} {handlePublish} {handleApprove}
    {isCompact}
  />
</div>

<!-- Gate Block Modal -->
{#if showGateModal}
  <GateBlockModal
    blockers={gateBlockers}
    onClose={() => { showGateModal = false; }}
    onViewDetails={(tab) => {
      showGateModal = false;
      focusTabFromModal = tab;
    }}
  />
{/if}

<style>
  .content-review-card { position: relative; isolation: isolate; }
  :global(.custom-scrollbar::-webkit-scrollbar) { width: 3px; }
  :global(.custom-scrollbar::-webkit-scrollbar-thumb) { background: rgba(59, 130, 246, 0.1); border-radius: 0; }
  :global(.custom-scrollbar::-webkit-scrollbar-thumb:hover) { background: rgba(59, 130, 246, 0.6); }
  @keyframes shimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
  :global(.animate-shimmer) { position: relative; overflow: hidden; }
  :global(.animate-shimmer::after) { content: ''; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent); animation: shimmer 1.5s infinite linear; }
</style>
