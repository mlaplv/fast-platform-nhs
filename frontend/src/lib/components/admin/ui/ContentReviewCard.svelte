<script lang="ts">
  import { onMount, untrack } from "svelte";
  import { fade } from "svelte/transition";
  import { apiClient } from "$lib/utils/apiClient";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { vuiController } from "$lib/vui";
  import { xohiImageStore } from "$lib/state/xohiImage.svelte";
  import { processContentImages } from "$lib/state/utils";
  import { createCampaignController } from "$lib/state/xohiCampaign.svelte";
  import Header from "./content-factory/Header.svelte";
  import IdeaStep from "./content-factory/IdeaStep.svelte";
  import AssetStep from "./content-factory/AssetStep.svelte";
  import OutlineStep from "./content-factory/OutlineStep.svelte";
  import DraftStep from "./content-factory/DraftStep.svelte";
  import ValidationPreviewStep from "./content-factory/ValidationPreviewStep.svelte";
  import PublishStep from "./content-factory/PublishStep.svelte";
  import ActionButtons from "./content-factory/ActionButtons.svelte";
  import GateBlockModal from "./content-factory/GateBlockModal.svelte";
  import UltraPremiumLoading from "./content-factory/UltraPremiumLoading.svelte";
  import type { CampaignKeywords, MediaAsset, CampaignOutline, CampaignMetrics, AnalysisCache } from "$lib/state/types";

  interface Props {
    campaign_id: string; step: number; status: string; progress_msg?: string; title?: string;
    keywords: CampaignKeywords; assets: (MediaAsset | string)[]; reserve_assets: string[];
    outline: CampaignOutline; draft_content: string; finalHtml: string;
    selectedAvatarUrl: string | null; selectedAssetIndex: number; creation_config: Record<string, unknown>;
    analysis_cache: AnalysisCache; analysis_metrics: CampaignMetrics;
  }

  let {
    campaign_id, step = $bindable(), status = $bindable(), progress_msg = $bindable(),
    keywords = $bindable(), assets = $bindable(), reserve_assets = $bindable(),
    outline = $bindable(), draft_content = $bindable(), finalHtml = $bindable(),
    selectedAvatarUrl = $bindable(), selectedAssetIndex = $bindable(),
    creation_config = $bindable(), analysis_cache = $bindable(), analysis_metrics = $bindable()
  }: Props = $props();

  const campaign = createCampaignController({
    get campaign_id() { return campaign_id; }, get keywords() { return keywords; }, set keywords(v) { keywords = v; },
    get creation_config() { return creation_config; }, set creation_config(v) { creation_config = v; },
    get outline() { return outline; }, set outline(v) { outline = v; },
    get draft_content() { return draft_content; }, set draft_content(v) { draft_content = v; },
    get assets() { return assets; }, set assets(v) { assets = v; },
    get reserve_assets() { return reserve_assets; }, set reserve_assets(v) { reserve_assets = v; },
    get selectedAvatarUrl() { return selectedAvatarUrl; }, set selectedAvatarUrl(v) { selectedAvatarUrl = v; },
    get selectedAssetIndex() { return selectedAssetIndex; }, set selectedAssetIndex(v) { selectedAssetIndex = v; },
    get analysis_metrics() { return analysis_metrics; }, get analysis_cache() { return analysis_cache; }
  });

  let viewingStep = $state(step || 1), isEditing = $state(false), maxStepSeen = $state(step || 1);
  let isProcessing = $derived(status === "PROCESSING");
  let isAnalysisRunning = $derived.by(() => {
    if (!progress_msg) return false;
    const keywords = ["tầm soát", "quét", "phân tích", "rà soát", "Booster", "phẫu thuật", "Neural Engine", "Surgical Precision", "điểm số", "Copyright Check", "SEO Analysis", "AI MOD"];
    return keywords.some(kw => progress_msg.toLowerCase().includes(kw.toLowerCase()));
  });

  let customImageUrl = $state(""), editedKeywords = $state<CampaignKeywords>({}), editedConfig = $state<Record<string, unknown>>({
    style: "Viral",
    word_count: 500,
    max_assets: 10,
    max_sections: 3
  }), editedDraft = $state(""), editedOutline = $state("");
  let showGateModal = $state(false), gateBlockers = $state<any[]>([]), focusTabFromModal = $state<string | null>(null);

  let isOverlaySticky = $state(false);
  let stickyTimer: ReturnType<typeof setTimeout> | null = null;

  $effect(() => { if (status !== "PROCESSING") untrack(() => { campaign.isLoading = false; campaign.isStepProcessing = false; }); });
  // CNS V82.5: Auto-jump to new step when it arrives from pulse, but allow looking back
  $effect(() => { 
    if (step > maxStepSeen) {
      untrack(() => { maxStepSeen = step; viewingStep = step; isEditing = false; campaign.isStepProcessing = false; });
    }
  });

  const stepLabels = [
    "Khởi tạo Brain",           // 1: Idea
    "Thiết giáp Săn ảnh",       // 2: Assets
    "Phác thảo Neural",         // 3: Outline
    "Chế tác Nội dung",         // 4: Draft
    "Kiểm định Viral Edge",     // 5: Analysis
    "Vinh quang & Viral"        // 6: Publish
  ];

  let isAnalysisMessage = $derived.by(() => {
    if (!progress_msg) return false;
    const keywords = [
      "tầm soát", "quét", "phân tích", "rà soát", "Booster", "phẫu thuật", "Neural Engine", 
      "Surgical Precision", "điểm số", "Copyright Check", "SEO Analysis", "AI MOD", 
      "Clean", "làm sạch", "Enrich", "tối ưu", "đánh giá"
    ];
    return keywords.some(kw => progress_msg.toLowerCase().includes(kw.toLowerCase()));
  });

  let analysisSession = $state(false);

  // CNS V85.4: Analysis Session Lock — persistent suppression during tools
  $effect(() => {
    if (isProcessing) {
      if (isAnalysisMessage) {
        analysisSession = true;
        isOverlaySticky = false;
        if (stickyTimer) { clearTimeout(stickyTimer); stickyTimer = null; }
      }
    } else {
      // Back to IDLE: Reset session
      analysisSession = false;
      isOverlaySticky = false;
      if (stickyTimer) { clearTimeout(stickyTimer); stickyTimer = null; }
    }
  });

  // Keep sticky for major transitions to prevent "chập điện"
  $effect(() => {
    if (isProcessing && !isAnalysisMessage && progress_msg) {
      const stepIndicators = ["Chế tác", "Phác thảo", "Khởi tạo", "Thiết giáp", "Vinh quang", "phát hành"];
      if (stepIndicators.some(w => progress_msg.includes(w))) {
        isOverlaySticky = true;
        if (stickyTimer) clearTimeout(stickyTimer);
        stickyTimer = setTimeout(() => { isOverlaySticky = false; stickyTimer = null; }, 2500);
      }
    }
  });

  let shouldShowOverlay = $derived(
    (isProcessing || isOverlaySticky) && !analysisSession && !isAnalysisMessage
  );



  $effect(() => { if (viewingStep >= 6 && !finalHtml && draft_content) untrack(() => { finalHtml = processContentImages(draft_content, xohiImageStore.assets.length > 0 ? xohiImageStore.assets : assets); }); });
  $effect(() => {
    const src = draft_content || finalHtml || "", out = outline?.html || "";
    if (isProcessing) {
      if (src && src !== editedDraft) editedDraft = src;
      if (out && out !== editedOutline) editedOutline = out;
    }

    // Reactive Data Synchronization (Enforce Defaults & Props)
    if (!isEditing) {
      untrack(() => {
        const sourceFromProp = (creation_config && typeof creation_config === 'object') ? creation_config : {};
        const sourceFromKeywords = (keywords?.creation_config && typeof keywords.creation_config === 'object') ? keywords.creation_config : {};
        const rawSource = Object.keys(sourceFromProp).length > 0 ? sourceFromProp : sourceFromKeywords;

        const cleanSource: Record<string, unknown> = {};
        for (const [k, v] of Object.entries(rawSource)) {
          if (v !== undefined && v !== null && v !== "") cleanSource[k] = v;
        }

        // Phase 82.11: Strict Style Validation (Sếp's Anti-Blank Shield)
        const validStyles = ["Chuyên nghiệp", "Sáng tạo", "Viral", "Hàn lâm"];
        if (cleanSource.style && !validStyles.includes(cleanSource.style as string)) {
          delete cleanSource.style;
        }

        if (cleanSource.word_count !== undefined) cleanSource.word_count = Number(cleanSource.word_count);
        if (cleanSource.max_assets !== undefined) cleanSource.max_assets = Number(cleanSource.max_assets);
        if (cleanSource.max_sections !== undefined) cleanSource.max_sections = Number(cleanSource.max_sections);

        editedConfig = {
          style: "Viral",
          word_count: 500,
          max_assets: 10,
          max_sections: 3,
          ...cleanSource
        };

        if (src && src !== editedDraft) editedDraft = src;
        if (out && out !== editedOutline) editedOutline = out;
        editedKeywords = JSON.parse(JSON.stringify(keywords || {}));
      });
    }
  });

  onMount(() => {
    if (step === undefined) step = 1;
    if (status === undefined) status = "IDLE";
    if (progress_msg === undefined) progress_msg = "";
    if (keywords === undefined) keywords = {} as CampaignKeywords;
    if (assets === undefined) assets = [];
    if (reserve_assets === undefined) reserve_assets = [];
    if (outline === undefined) outline = {} as CampaignOutline;
    if (draft_content === undefined) draft_content = "";
    if (finalHtml === undefined) finalHtml = "";
    if (selectedAvatarUrl === undefined) selectedAvatarUrl = null;
    if (selectedAssetIndex === undefined) selectedAssetIndex = 0;
    if (creation_config === undefined) creation_config = {};
    if (analysis_cache === undefined) analysis_cache = {} as AnalysisCache;
    if (analysis_metrics === undefined) analysis_metrics = {} as CampaignMetrics;

    // Phase 82.5: Initial sync is handled by the $effect above after mount
    editedDraft = draft_content || ""; 
    editedOutline = outline?.html || "";
  });

  async function handleApprove() {
    const res = await campaign.approve(viewingStep, isEditing, editedKeywords, editedConfig, editedOutline, editedDraft);
    if (res === true) {
      isEditing = false;
    } else if (res?.gateBlocked) {
      gateBlockers = [
        ...(campaign.copyrightScore === null || campaign.copyrightScore < 90 ? [{ label: '🔍 COPYRIGHT', current: campaign.copyrightScore !== null ? `${campaign.copyrightScore}%` : 'Chưa kiểm tra', required: '≥ 90%', tab: 'copyright' }] : []),
        ...(campaign.seoScore === null || campaign.seoScore < 70 ? [{ label: '📊 SEO Score', current: campaign.seoScore !== null ? `${campaign.seoScore}/100` : 'Chưa kiểm tra', required: '≥ 70/100', tab: 'seo' }] : [])
      ];
      showGateModal = true;
    }
  }

  const handleRetry = async () => { 
    // CNS V82.50: Hard Wipe UI state immediately
    status = "PROCESSING";
    progress_msg = "💥 Đang dọn sạch dữ liệu và khởi động lại...";
    
    untrack(() => {
      if (viewingStep === 2) {
        xohiImageStore.clearAll();
        assets = [];
        reserve_assets = [];
      }
      editedDraft = "";
      editedOutline = "";
    });

    if (await campaign.retry()) { 
      isEditing = false; 
    } 
  };
  const handleUpdateMetadata = async () => { if (await campaign.updateMetadata(viewingStep, editedKeywords, editedConfig, editedOutline, editedDraft)) { isEditing = false; editedDraft = ""; editedOutline = ""; } };
  
  // CNS V82.11: Root Cause Fix - Total Disposal after Step 6 Publication
  const handlePublish = async () => {
    if (await campaign.publish()) {
      // Small delay for the "Success" toast to be visible before closing
      setTimeout(() => {
        if (typeof nanobot.fullPurge === 'function') {
          nanobot.fullPurge(campaign_id);
        }
      }, 1500);
    }
  };

  const handleImageError = (url: string) => { const a = xohiImageStore.assets.find(x => x.file_path === url || x.url === url); if (a) xohiImageStore.removeAsset(a.id); else assets = assets.filter(x => typeof x === 'string' ? x !== url : x.url !== url); };
  const handleSelectKeyword = (kw: string) => { keywords.primary_keyword = kw; vuiController.speak(`Đã chọn ${kw}.`); apiClient.patch(`/api/v1/content/campaigns/${campaign_id}`, { keywords: $state.snapshot(keywords) }); };
  const handleMouseMove = (e: MouseEvent) => { const el = e.currentTarget as HTMLElement, r = el.getBoundingClientRect(); el.style.setProperty('--mouse-x', `${((e.clientX - r.left) / r.width) * 100}%`); el.style.setProperty('--mouse-y', `${((e.clientY - r.top) / r.height) * 100}%`); };
</script>

<div class="content-review-card w-full h-full flex flex-col transition-all duration-700 overflow-hidden z-[150000] bg-slate-950/95 backdrop-blur-xl" in:fade={{ duration: 600 }}>
  <Header bind:viewingStep {step} {status} {progress_msg} {campaign_id} bind:isEditing toggleExpand={() => nanobot.toggleExpand()} isExpanded={nanobot.isExpanded} creation_config={isEditing ? editedConfig : creation_config} />
  <div class="flex-1 {(viewingStep === 3 || viewingStep === 4 || viewingStep === 6) ? 'overflow-hidden pb-0' : 'overflow-y-auto custom-scrollbar pb-24'} relative flex flex-col min-h-0">
    {#if shouldShowOverlay}
       <div class="absolute inset-0 z-[100]">
          <UltraPremiumLoading 
            {progress_msg} 
            {viewingStep} 
            {campaign_id} 
            {isAnalysisMessage}
            liveContent={viewingStep === 3 ? editedOutline : (viewingStep === 4 ? editedDraft : '')}
          />
       </div>
    {/if}
    
    <div class={isProcessing ? 'invisible h-0 overflow-hidden' : 'flex-1 flex flex-col min-h-0'}>
      {#if viewingStep === 1}
        <IdeaStep bind:isEditing {campaign_id} bind:keywords bind:editedKeywords creation_config={creation_config} bind:editedConfig {handleSelectKeyword} {handleUpdateMetadata} isLoading={campaign.isLoading} />
      {:else if viewingStep === 2}
        <AssetStep {campaign_id} {isProcessing} isExpanded={nanobot.isExpanded} bind:assets bind:reserve_assets bind:customImageUrl bind:selectedAvatarUrl bind:selectedAssetIndex {handleImageError} syncAssetChanges={campaign.syncAssetChanges} {handleRetry} {handleMouseMove} />
      {:else if viewingStep === 3}
        <OutlineStep {isEditing} bind:editedOutline {outline} bind:assets bind:selectedAvatarUrl bind:selectedAssetIndex isExpanded={nanobot.isExpanded} {campaign_id} {isProcessing} />
      {:else if viewingStep === 4}
        <DraftStep {campaign_id} {isEditing} bind:editedDraft {draft_content} bind:assets bind:selectedAvatarUrl bind:selectedAssetIndex isExpanded={nanobot.isExpanded} {outline} {analysis_cache} {analysis_metrics} {isProcessing} bind:copyrightScore={campaign.copyrightScore} bind:seoScore={campaign.seoScore} bind:aiScore={campaign.aiScore} />
      {:else if viewingStep === 5}
        <ValidationPreviewStep {draft_content} {assets} {keywords} copyrightScore={campaign.copyrightScore} seoScore={campaign.seoScore} aiScore={campaign.aiScore} {analysis_cache} isExpanded={nanobot.isExpanded} />
      {:else if viewingStep === 6}
        <PublishStep bind:selectedAvatarUrl bind:selectedAssetIndex bind:viewingStep bind:isEditing bind:keywords bind:finalHtml bind:draft_content bind:assets {campaign_id} {apiClient} copyrightScore={campaign.copyrightScore} seoScore={campaign.seoScore} aiScore={campaign.aiScore} {analysis_cache} />
      {/if}
    </div>
  </div>
  <ActionButtons isLoading={campaign.isLoading} {status} bind:viewingStep {step} bind:isEditing {isProcessing} isPublishing={campaign.isPublishing} {handleRetry} {handleUpdateMetadata} {handlePublish} {handleApprove} />
</div>

{#if showGateModal}<GateBlockModal blockers={gateBlockers} onClose={() => showGateModal = false} onViewDetails={(tab) => { showGateModal = false; focusTabFromModal = tab; }} />{/if}

<style>
  .content-review-card { position: relative; isolation: isolate; }
  :global(.custom-scrollbar::-webkit-scrollbar) { width: 3px; }
  :global(.custom-scrollbar::-webkit-scrollbar-thumb) { background: rgba(59, 130, 246, 0.1); }
  @keyframes shimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
  :global(.animate-shimmer) { position: relative; overflow: hidden; }
  :global(.animate-shimmer::after) { content: ''; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent); animation: shimmer 1.5s infinite linear; }
</style>
