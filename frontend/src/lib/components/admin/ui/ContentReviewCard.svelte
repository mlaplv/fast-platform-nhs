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

  let viewingStep = $state(step || 1), isEditing = $state(false), maxStepSeen = $state(step || 1), isProcessing = $derived(status === "PROCESSING");
  let customImageUrl = $state(""), editedKeywords = $state<CampaignKeywords>({}), editedConfig = $state<Record<string, unknown>>({}), editedDraft = $state(""), editedOutline = $state("");
  let showGateModal = $state(false), gateBlockers = $state<any[]>([]), focusTabFromModal = $state<string | null>(null);

  $effect(() => { if (status !== "PROCESSING") untrack(() => { campaign.isLoading = false; }); });
  $effect(() => { if (step > maxStepSeen) { maxStepSeen = step; viewingStep = step; } });
  $effect(() => { if (viewingStep >= 6 && !finalHtml && draft_content) untrack(() => { finalHtml = processContentImages(draft_content, xohiImageStore.assets.length > 0 ? xohiImageStore.assets : assets); }); });
  $effect(() => {
    const src = draft_content || finalHtml || "", out = outline?.html || "";
    if (isProcessing) { if (src && src !== editedDraft) editedDraft = src; if (out && out !== editedOutline) editedOutline = out; }
    else if (!isEditing) untrack(() => { if (src && src !== editedDraft) editedDraft = src; if (out && out !== editedOutline) editedOutline = out; });
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

    editedConfig = { style: "Chuyên nghiệp", word_count: 500, max_assets: 10, max_sections: 3, ...(creation_config && Object.keys(creation_config).length ? creation_config : (keywords?.creation_config || {})) };
    editedKeywords = JSON.parse(JSON.stringify(keywords || {})); editedDraft = draft_content || ""; editedOutline = outline?.html || "";
  });

  async function handleApprove() {
    const res = await campaign.approve(viewingStep, isEditing, editedKeywords, editedConfig, editedOutline, editedDraft);
    if (res === true) isEditing = false;
    else if (res?.gateBlocked) {
      gateBlockers = [
        ...(campaign.copyrightScore === null || campaign.copyrightScore < 90 ? [{ label: '🔍 COPYRIGHT', current: campaign.copyrightScore !== null ? `${campaign.copyrightScore}%` : 'Chưa kiểm tra', required: '≥ 90%', tab: 'copyright' }] : []),
        ...(campaign.seoScore === null || campaign.seoScore < 70 ? [{ label: '📊 SEO Score', current: campaign.seoScore !== null ? `${campaign.seoScore}/100` : 'Chưa kiểm tra', required: '≥ 70/100', tab: 'seo' }] : [])
      ];
      showGateModal = true;
    }
  }

  const handleRetry = async () => { if (await campaign.retry()) { editedDraft = ""; isEditing = false; } };
  const handleUpdateMetadata = async () => { if (await campaign.updateMetadata(viewingStep, editedKeywords, editedConfig, editedOutline, editedDraft)) { isEditing = false; editedDraft = ""; editedOutline = ""; } };
  const handleImageError = (url: string) => { const a = xohiImageStore.assets.find(x => x.file_path === url || x.url === url); if (a) xohiImageStore.removeAsset(a.id); else assets = assets.filter(x => typeof x === 'string' ? x !== url : x.url !== url); };
  const handleSelectKeyword = (kw: string) => { keywords.primary_keyword = kw; vuiController.speak(`Đã chọn ${kw}.`); apiClient.patch(`/api/v1/content/campaigns/${campaign_id}`, { keywords }); };
  const handleMouseMove = (e: MouseEvent) => { const el = e.currentTarget as HTMLElement, r = el.getBoundingClientRect(); el.style.setProperty('--mouse-x', `${((e.clientX - r.left) / r.width) * 100}%`); el.style.setProperty('--mouse-y', `${((e.clientY - r.top) / r.height) * 100}%`); };
</script>

<div class="content-review-card w-full h-full flex flex-col transition-all duration-700 overflow-hidden z-[150000] bg-slate-950/95 backdrop-blur-xl" in:fade={{ duration: 600 }}>
  <Header bind:viewingStep {step} {status} {progress_msg} {campaign_id} bind:isEditing toggleExpand={() => nanobot.toggleExpand()} isExpanded={nanobot.isExpanded} creation_config={isEditing ? editedConfig : creation_config} />
  <div class="flex-1 overflow-y-auto custom-scrollbar relative pb-24 flex flex-col min-h-0">
    {#if viewingStep === 1}
      <IdeaStep bind:isEditing {campaign_id} bind:keywords bind:editedKeywords creation_config={creation_config} bind:editedConfig {handleSelectKeyword} {handleUpdateMetadata} isLoading={campaign.isLoading} />
    {:else if viewingStep === 2}
      <AssetStep {isProcessing} isExpanded={nanobot.isExpanded} bind:assets bind:reserve_assets bind:customImageUrl bind:selectedAvatarUrl bind:selectedAssetIndex {handleImageError} syncAssetChanges={campaign.syncAssetChanges} {handleRetry} {handleMouseMove} />
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
  <ActionButtons isLoading={campaign.isLoading} {status} bind:viewingStep {step} bind:isEditing {isProcessing} isPublishing={campaign.isPublishing} {handleRetry} {handleUpdateMetadata} handlePublish={campaign.publish} {handleApprove} />
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
