<script lang="ts">
  import { onMount, untrack } from "svelte";
  import Brain from "lucide-svelte/icons/brain";
  import ShieldCheck from "lucide-svelte/icons/shield-check";
  import BarChart2 from "lucide-svelte/icons/bar-chart-2";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import NeuralEditor from "../tiptap/NeuralEditor.svelte";
  import UltraPremiumLoading from "./UltraPremiumLoading.svelte";
  import { processContentImages } from "$lib/state/utils";
  import { xohiImageStore } from "$lib/state/xohiImage.svelte";
  import { createOutlineController } from "$lib/state/xohiOutline.svelte";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import type { MediaAsset, CampaignOutline, CampaignSection, CampaignMetrics, AnalysisCache } from "$lib/state/types";
  import InteractiveDashboard from "$lib/components/ui/InteractiveDashboard.svelte";

  function isJson(str: string) {
    if (typeof str !== 'string') return false;
    try {
      const parsed = JSON.parse(str);
      return typeof parsed === 'object' && parsed !== null && ('hero_headline' in parsed || 'spec_bento' in parsed);
    } catch (e) {
      return false;
    }
  }

  interface Props {
    campaign_id: string; isEditing: boolean; editedDraft: string; draft_content: string;
    outline: CampaignOutline; assets: (MediaAsset | string)[]; isExpanded: boolean;
    selectedAvatarUrl: string | null; selectedAssetIndex: number;
    editorRef?: any | null; analysis_cache: AnalysisCache; analysis_metrics: CampaignMetrics;
    analysis_report: Record<string, any>;
    copyrightScore: number | null; seoScore: number | null; aiScore: number | null; isProcessing?: boolean;
  }

  let {
    campaign_id, isEditing, editedDraft = $bindable(), draft_content = $bindable(),
    outline = {} as CampaignOutline, assets = [] as (MediaAsset | string)[], isExpanded,
    selectedAvatarUrl = $bindable(), selectedAssetIndex = $bindable(),
    editorRef = $bindable(), analysis_cache = $bindable({} as AnalysisCache), analysis_metrics = $bindable({} as CampaignMetrics),
    analysis_report = {},
    copyrightScore = $bindable(), seoScore = $bindable(), aiScore = $bindable(), isProcessing = false
  }: Props = $props();

  // CNS V86.5: Robust Logic Consolidation (Trị tận gốc)
  // Use the standardized Outline Controller for fallback rendering
  const outlineCtrl = createOutlineController({
    getOutline: () => outline,
    getEditedOutline: () => editedDraft,
    getAssets: () => assets,
    setEditedOutline: (v) => { editedDraft = v; }
  });

  let displayContent = $derived.by(() => {
    // Phase 86.5: Root Cause Solution - If we have a draft, use it. If not, use the robust outline parser.
    let base = isEditing ? (editedDraft || draft_content) : draft_content;
    if (!base) {
      base = outlineCtrl.getStructuredOutline();
    }
    return processContentImages(base, xohiImageStore.assets.length > 0 ? xohiImageStore.assets : assets);
  });

  // CNS V85.20: Sử dụng untrack để ngắt vòng phản hồi reactive (Reactive Feedback Loop).
  // Đọc analysis.scores (reactive) nhưng ghi lên bindable parent props mà KHÔNG tạo dependency mới.
  // Sync scores back to parent for UI indicator
  $effect(() => {
    untrack(() => {
      copyrightScore = analysis_metrics.unique_score ? Math.round(analysis_metrics.unique_score * 100) : null;
      seoScore = analysis_metrics.seo_score || null;
      aiScore = analysis_metrics.ai_ready_score || null;
    });
  });

  let lastAnalyzedTime = $derived.by(() => {
    if (!analysis_metrics?.last_analyzed) return null;
    try { return new Date(analysis_metrics.last_analyzed as string).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }); } catch { return null; }
  });

  onMount(() => {
    if (editedDraft === undefined) editedDraft = "";
    if (draft_content === undefined) draft_content = "";
    if (selectedAvatarUrl === undefined) selectedAvatarUrl = null;
    if (selectedAssetIndex === undefined) selectedAssetIndex = 0;
    if (copyrightScore === undefined) copyrightScore = null;
    if (seoScore === undefined) seoScore = null;
    if (aiScore === undefined) aiScore = null;

    if (isEditing && !editedDraft) {
      editedDraft = draft_content || (typeof outline === 'string' ? outline : outline?.html) || "";
    }

  });

  let resultPanelEl = $state<HTMLElement | null>(null);
  let isFullResults = $state(false); // CNS V85: Detailed view for IDE-like progress
  
  function scrollToPanel() { setTimeout(() => resultPanelEl?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 50); }
  // CNS V85.23: Fully typed action dispatcher — no `Function` or `any[]` per CLAUDE.md
  type AnalysisActionFn = (force?: boolean, skipSave?: boolean) => Promise<string | null | undefined | void>;
  async function handleAction(actionFn: AnalysisActionFn, force?: boolean, skipSave?: boolean) { 
    await actionFn(force, skipSave); 
    scrollToPanel(); 
  }
</script>


<div class="flex flex-col flex-1 min-h-0 overflow-hidden">

  <div class="flex flex-col relative flex-1 min-h-0 transition-all duration-500 {isEditing ? 'border border-white/5 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.8)] bg-[#09090b]/40 backdrop-blur-2xl' : 'bg-transparent'}">
    {#if isProcessing}
      <div class="absolute inset-0" style="z-index: {Z_INDEX_ADMIN.STICKY_HEADER}">
        <UltraPremiumLoading 
          progress_msg="AI đang chấp bút bản thảo..." 
          viewingStep={4} 
          campaign_id={campaign_id} 
          liveContent={displayContent || ""} 
        />
      </div>
    {/if}
    
    {#if isJson(editedDraft || draft_content)}
      <div class="p-4 overflow-y-auto w-full h-full custom-scrollbar flex-1 relative">
         <InteractiveDashboard data={editedDraft || draft_content} compact={false} />
         {#if isEditing}
           <div class="mt-4 p-4 border border-yellow-500/50 bg-yellow-500/10 rounded-lg text-yellow-200/80 text-sm flex gap-2">
             <span>⚠️</span>
             <span>Giao diện này đang sử dụng Neural Data-driven API. Tính năng chỉnh sửa trực tiếp qua Tiptap Editor đã bị vô hiệu hóa cho định dạng này. Vui lòng sử dụng tính năng "Sửa hàng loạt" hoặc "Neural Rewrite" từ công cụ AI ở Sidebar để tinh chỉnh dữ liệu.</span>
           </div>
         {/if}
      </div>
    {:else}
      <NeuralEditor
        bind:content={editedDraft}
        topic={outline?.title || ""}
        editable={isEditing}
        placeholder="AI đang chấp bút bản thảo..."
        fullScreen={isExpanded}
        campaign_id={campaign_id}
        isProcessing={isProcessing}
        bind:assets
        bind:selectedAvatarUrl
        bind:selectedAssetIndex
        bind:analysisCache={analysis_cache}
        bind:analysisMetrics={analysis_metrics}
        analysisReport={analysis_report}
        flex={true}
      />
    {/if}
  </div>

</div>


<style>
  :global(.custom-scrollbar::-webkit-scrollbar) { width: 3px; }
  :global(.custom-scrollbar::-webkit-scrollbar-thumb) { background: rgba(59,130,246,0.1); }
  @keyframes shimmer { 0%, 100% { opacity: 0.3; } 50% { opacity: 0.7; } }
  .animate-pulse { animation: shimmer 2s infinite ease-in-out; }
</style>
