<script lang="ts">
  import { onMount, untrack } from "svelte";
  import { fade } from "svelte/transition";
  import { apiClient } from "$lib/utils/apiClient";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { vuiController } from "$lib/vui";
  
  // -- Sub-Components --
  import Header from "./content-factory/Header.svelte";
  import Timeline from "./content-factory/Timeline.svelte";
  import IdeaStep from "./content-factory/IdeaStep.svelte";
  import AssetStep from "./content-factory/AssetStep.svelte";
  import OutlineStep from "./content-factory/OutlineStep.svelte";
  import DraftStep from "./content-factory/DraftStep.svelte";
  import PublishStep from "./content-factory/PublishStep.svelte";
  import ActionButtons from "./content-factory/ActionButtons.svelte";
  import GateBlockModal from "./content-factory/GateBlockModal.svelte";

  let { 
    campaign_id,
    step = $bindable(),
    status = $bindable(),
    progress_msg = $bindable(),
    title = $bindable(),
    keywords = $bindable(),
    assets = $bindable(),
    outline = $bindable(),
    draft_content = $bindable(),
    finalHtml = $bindable(),
    selectedAvatarUrl = $bindable(), 
    selectedAssetIndex = $bindable(),
    creation_config = $bindable(),
    analysis_cache = $bindable(),
    analysis_metrics = $bindable()
  } = $props();

  // -- Local UI Orchestration --
  let viewingStep = $state(step);
  let isEditing = $state(false);
  let isProcessing = $derived(status === "PROCESSING");
  let isLoading = $state(false);
  let isPublishing = $state(false);
  let resultMsg = $state("");
  let customImageUrl = $state("");
  let editedKeywords = $state<any>({});
  let editedConfig = $state<any>({});
  let editedDraft = $state("");
  let editorRef = $state<any>(null);
  let maxStepSeen = $state(step);

  // -- Gate Score State (synced from DraftStep via bind:) --
  let copyrightScore = $state<number | null>(null);
  let seoScore = $state<number | null>(null);
  let aiScore = $state<number | null>(null);

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
    // Phase 72: Check both prop and keywords.creation_config for robust sync
    const baseConfig = creation_config && Object.keys(creation_config).length > 0
      ? creation_config 
      : (keywords?.creation_config || {});
    
    editedConfig = { ...DEFAULT_CONFIG, ...baseConfig };
    if (typeof editedConfig !== 'object') editedConfig = {};
    editedKeywords = JSON.parse(JSON.stringify(keywords || {}));
    editedDraft = draft_content || "";
    
    // Ensure viewingStep is valid
    if (viewingStep < 1 || viewingStep > 5) viewingStep = step || 1;
    if (viewingStep < 1) viewingStep = 1;
  });

  // Rule R82.42: Reactive Prep — Ensure editedDraft is ready for next steps
  $effect(() => {
    if (!isEditing && draft_content && draft_content !== editedDraft) {
      editedDraft = draft_content;
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
          label: '🔍 Bản Quyền',
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
          : { html: editedDraft } 
      } : {};
      await apiClient.post(`/api/v1/content/campaigns/${campaign_id}/approve`, payload);
      
      // Update local props to prevent $effect sync back to old values
      if (viewingStep === 1) {
        // CNS V72: Inclusion of creation_config in keywords prop sync for effect equality
        keywords = { ...editedKeywords, creation_config: { ...editedConfig } };
        creation_config = { ...editedConfig };
      } else if (viewingStep === 3) {
        outline = { html: editedDraft };
      } else if (viewingStep === 4) {
        draft_content = editedDraft;
      }

      isEditing = false;
      const stepNames: Record<number, string> = {
        1: "ý tưởng và từ khóa",
        2: "các hình ảnh",
        3: "dàn ý bài viết",
        4: "bản thảo nội dung",
        5: "bài viết"
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
        5: "bài viết"
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
        : (viewingStep === 3 ? { outline_data: { html: editedDraft } } : { draft_content: editedDraft });
        
      await apiClient.patch(`/api/v1/content/campaigns/${campaign_id}`, payload);
      
      if (viewingStep === 1) {
        // CNS V72: Inclusion of creation_config in keywords prop sync for effect equality
        keywords = { ...editedKeywords, creation_config: { ...editedConfig } };
        creation_config = { ...editedConfig };
      } else if (viewingStep === 3) {
        outline = { html: editedDraft };
      } else if (viewingStep === 4) {
        draft_content = editedDraft;
      }
      isEditing = false;
      editedDraft = ""; // R82.47: Clear edit buffer after successful save
      
      const stepNames: Record<number, string> = {
        1: "nội dung ý tưởng và từ khóa",
        2: "các hình ảnh",
        3: "dàn ý bài viết",
        4: "bản thảo nội dung",
        5: "bài viết"
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
      // Rule R109: REST Alignment — Use keys expected by ActionHandler.update_metadata
      await apiClient.patch(`/api/v1/content/campaigns/${campaign_id}`, {
        assets: assets, // Backend expects 'assets' NOT 'assets_data' in PATCH alias
        avatar: selectedAvatarUrl,
        selected_index: newIndex ?? selectedAssetIndex
      });
    } catch (e) { console.error("Sync failed:", e); }
  }

  function handleImageError(url: string) {
    assets = assets.filter(a => a !== url);
    if (selectedAvatarUrl === url) selectedAvatarUrl = assets[0] || null;
  }

  function deleteAsset(idx: number, e: MouseEvent) {
    e.stopPropagation();
    const removed = assets[idx];
    assets = assets.filter((_, i) => i !== idx);
    if (selectedAvatarUrl === removed) selectedAvatarUrl = assets[0] || null;
    vuiController.speak("Đã xóa ảnh.");
    syncAssetChanges();
  }

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
</script>

<div 
  class="content-review-card w-full {nanobot.isExpanded ? 'h-full bg-transparent' : 'bg-white/[0.02] border border-white/5 rounded-3xl'} flex flex-col p-8 transition-all duration-700 overflow-hidden shadow-2xl"
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

  <div class="flex-1 flex flex-col p-5 {nanobot.isExpanded ? 'p-8' : ''} overflow-y-auto custom-scrollbar relative z-10">
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
          bind:assets bind:customImageUrl bind:selectedAvatarUrl bind:selectedAssetIndex 
          {handleImageError} {syncAssetChanges} {deleteAsset} {handleRetry} {handleMouseMove} 
        />
      {:else if viewingStep === 3}
        <OutlineStep 
          {isEditing} bind:editedDraft bind:draft_content {outline} {assets} 
          isExpanded={nanobot.isExpanded} editorAnnotations={[]} {step}
        />
      {:else if viewingStep === 4}
        <DraftStep 
          {campaign_id} {isEditing} bind:editedDraft bind:draft_content 
          {assets} isExpanded={nanobot.isExpanded} bind:editorRef {outline}
          {analysis_cache} {analysis_metrics}
          bind:copyrightScore bind:seoScore bind:aiScore
        />
      {:else if viewingStep === 5}
        <PublishStep 
          {selectedAvatarUrl} bind:viewingStep bind:isEditing bind:keywords 
          {finalHtml} {draft_content} 
        />
      {/if}
  </div>

  {#if resultMsg}
    <div class="mt-6 p-4 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-300 text-[13px] font-bold">
      {resultMsg}
    </div>
  {/if}

  <ActionButtons 
    {isLoading} {status} {viewingStep} {step} {isEditing} {isProcessing} {isPublishing}
    {handleRetry} {handleUpdateMetadata} {handlePublish} {handleApprove}
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
  :global(.custom-scrollbar::-webkit-scrollbar-thumb) { background: rgba(59, 130, 246, 0.1); border-radius: 20px; }
  :global(.custom-scrollbar::-webkit-scrollbar-thumb:hover) { background: rgba(59, 130, 246, 0.6); }
  @keyframes shimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
  :global(.animate-shimmer) { position: relative; overflow: hidden; }
  :global(.animate-shimmer::after) { content: ''; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent); animation: shimmer 1.5s infinite linear; }
</style>
