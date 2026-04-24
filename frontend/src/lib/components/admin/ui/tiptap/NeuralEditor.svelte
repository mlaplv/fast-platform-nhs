<script lang="ts">
  /**
   * NeuralEditor.svelte — Universal Shared Editor Component
   * Layer: Universal Editor (editor + AI, no campaign required)
   *
   * Usage (any module: News, Product, etc.):
   *   <NeuralEditor bind:content={formHtml} topic={formTitle} editable={true} />
   *
   * Rules: SvelteKit 5 Runes, strict typing, no anys, no TODO, no mock data
   */
  import { onMount, untrack } from "svelte";
  import { ShieldCheck, BarChart2, Sparkles } from "lucide-svelte";
  import TiptapEditor from "./TiptapEditor.svelte";
  import { createAnalysisController } from "$lib/state/xohiAnalysis.svelte";
  import { portal } from "$lib/core/actions/portal";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import NeuralProgressTooltip from "../content-factory/NeuralProgressTooltip.svelte";
  import type { AnalysisCache, CampaignMetrics } from "$lib/state/types";

  interface Props {
    /** Two-way bound HTML content */
    content: string;
    /** Optional: editor topic/keyword used by SEO analysis */
    topic?: string;
    /** Whether the editor is in edit mode */
    editable?: boolean;
    /** Placeholder text */
    placeholder?: string;
    /** Bindable: Analysis cache for results persistence */
    analysisCache?: AnalysisCache;
    /** Bindable: Metrics for scores persistence */
    analysisMetrics?: CampaignMetrics;
    /** Extra toolbar actions */
    toolbarActions?: ToolbarAction[];
    /** Editor annotations/highlights */
    annotations?: EditorAnnotation[];
    /** Optional: Campaign ID for persistent tracking */
    campaign_id?: string | null;
    /** Whether the system is currently processing (DraftStep mode) */
    isProcessing?: boolean;
    /** Bindable: selected images/assets */
    assets?: (MediaAsset | string)[];
    selectedAvatarUrl?: string | null;
    selectedAssetIndex?: number;
    /** Bindable: Detailed report from DB (CNS V87.0) */
    analysisReport?: Record<string, unknown>;
  }

  let {
    content = $bindable(),
    topic = "",
    editable = true,
    placeholder = "Nhập nội dung...",
    fullScreen = $bindable(false),
    analysisCache = $bindable(),
    analysisMetrics = $bindable(),
    toolbarActions = [],
    annotations = [],
    campaign_id = null,
    isProcessing = false,
    assets = $bindable([]),
    selectedAvatarUrl = $bindable(null),
    selectedAssetIndex = $bindable(0),
    analysisReport = {},
  }: Props = $props();

  // Internal edit buffer — mirrors content prop while editing
  let editBuffer = $state(content);

  // Keep editBuffer in sync when content is set from outside (Zero-Flicker)
  $effect(() => { 
    untrack(() => {
      // CNS V2.2: Use a safer comparison to avoid reactive loops while typing
      if (content && content !== editBuffer && content.length !== editBuffer.length) {
        editBuffer = content; 
      }
    });
  });


  // Footer Lockdown Logic
  $effect(() => {
    if (typeof document !== 'undefined') {
      if (fullScreen) document.body.classList.add('neural-fullscreen-active');
      else document.body.classList.remove('neural-fullscreen-active');
    }
  });

  // Neural Intelligence Controller — Universal Logic
  const analysis = createAnalysisController({
    campaign_id: () => campaign_id,
    topic: () => topic,
    isEditing: () => editable,
    getContent: () => editBuffer,
    getEditedDraft: () => editBuffer,
    getDraftContent: () => content,
    setEditedDraft: (v) => { editBuffer = v; content = v; },
    setDraftContent: (v) => { content = v; },
    analysis_cache: () => analysisCache,
    analysis_metrics: () => analysisMetrics,
    analysis_report: () => analysisReport,
    getIsProcessing: () => isProcessing,
    onUpdate: (cache, metrics) => {
      untrack(() => {
        analysisCache = cache;
        analysisMetrics = metrics;
      });
    }
  });

  let editorRef = $state<TiptapEditor | null>(null);
  let resultPanelEl = $state<HTMLElement | null>(null);

  function scrollToPanel() {
    setTimeout(() => resultPanelEl?.scrollIntoView({ behavior: "smooth", block: "nearest" }), 50);
  }

  const handleAction = async (fn: (...args: unknown[]) => Promise<void>, ...args: unknown[]) => {
    await fn(...args);
    scrollToPanel();
  };

  onMount(() => {
    if (content === undefined) content = "";
    if (!editBuffer) editBuffer = content;
  });

  // CNS V85.2: Unified Toolbar Actions for Analysis (Elite V2.2: Lock & Hover Logic)
  const analysisActions = $derived([
    {
      id: 'copyright',
      label: analysis.copyrightResult 
        ? `Copyright ${Math.round(analysis.copyrightResult.uniqueness_score * 100)}%`
        : 'Copyright',
      icon: ShieldCheck,
      onclick: () => {
        if (analysis.activeTab === 'copyright') {
          handleAction(analysis.runCopyrightCheck, true);
        } else {
          analysis.activeTab = 'copyright';
          if (!analysis.copyrightResult && !analysis.isCopyrightLoading) handleAction(analysis.runCopyrightCheck);
        }
      },
      loading: analysis.isCopyrightLoading,
      // Golden Criteria: Uniqueness >= 95% and no critical annotations
      isPerfect: analysis.copyrightResult ? (analysis.copyrightResult.uniqueness_score >= 0.95 && (analysis.copyrightResult.annotations?.length || 0) === 0) : false,
      isLocked: analysis.copyrightResult ? (analysis.copyrightResult.uniqueness_score < 0.90 || (analysis.copyrightResult.annotations?.length || 0) > 0) : false,
      active: analysis.activeTab === 'copyright',
      colorClass: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'
    },
    {
      id: 'seo',
      label: analysis.seoResult 
        ? `SEO ${analysis.seoResult.total_score}/100`
        : 'SEO Scan',
      icon: BarChart2,
      onclick: () => {
        if (analysis.activeTab === 'seo') {
          handleAction(analysis.runSeoAnalysis, true);
        } else {
          analysis.activeTab = 'seo';
          if (!analysis.seoResult && !analysis.isSeoLoading) handleAction(analysis.runSeoAnalysis);
        }
      },
      loading: analysis.isSeoLoading,
      // Golden Criteria: SEO Score >= 95
      isPerfect: analysis.seoResult ? (analysis.seoResult.score >= 95) : false,
      isLocked: analysis.seoResult ? (analysis.seoResult.score < 90) : false,
      active: analysis.activeTab === 'seo',
      colorClass: 'bg-blue-500/10 text-blue-400 border-blue-500/20'
    },
    {
      id: 'ai',
      label: analysis.aiReadyResult 
        ? `AI Mod ${analysis.aiReadyResult.geo_score}/100`
        : 'AI Mod',
      icon: Sparkles,
      onclick: () => {
        if (analysis.activeTab === 'ai') {
          handleAction(analysis.runAiAnalysis, true);
        } else {
          analysis.activeTab = 'ai';
          if (!analysis.aiReadyResult && !analysis.isAiLoading) handleAction(analysis.runAiAnalysis);
        }
      },
      loading: analysis.isAiLoading,
      // Golden Criteria: Viral Score >= 8.5 and no critical AI annotations
      isPerfect: analysis.aiReadyResult ? (analysis.aiReadyResult.viral_score >= 8.5 && (analysis.aiReadyResult.ai_annotations?.filter(a => a.severity === 'high')?.length || 0) === 0) : false,
      isLocked: analysis.aiReadyResult ? (analysis.aiReadyResult.viral_score < 7.0 || (analysis.aiReadyResult.ai_annotations?.filter(a => a.severity === 'high')?.length || 0) > 0) : false,
      active: analysis.activeTab === 'ai',
      colorClass: 'bg-purple-500/10 text-purple-400 border-purple-500/20'
    },
    // AI Booster (id: enrich)
    {
      id: 'enrich',
      label: analysis.isBoosting ? '🚀 ENRICHING...' : '🚀 AI BOOSTER',
      loading: analysis.isBoosting,
      disabled: !analysis.seoResult || analysis.seoResult.score >= 95,
      onclick: () => {
        // AI Booster is a transformation, allow re-run to inject fresh data if editor changed
        handleAction(analysis.runAiBooster);
      },
      colorClass: 'bg-pink-500/10 text-pink-400 border-pink-500/20'
    },
    // Fix All (Contextual - Always allow if result exists)
    ...((analysis.copyrightResult || analysis.seoResult || analysis.aiReadyResult) ? [{ 
      id: `${analysis.activeTab || 'neural'}-fix`,
      label: analysis.isBulkFixing ? (analysis.bulkFixStatus || '✨ FIXING...') : `✨ FIX ALL ${analysis.activeTab?.toUpperCase() || 'NEURAL'}`, 
      loading: analysis.isBulkFixing, 
      onclick: () => handleAction(analysis.runBulkFix),
      colorClass: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
    }] : [])
  ]);

  const allToolbarActions = $derived([...analysisActions, ...toolbarActions]);
</script>

<div 
  use:portal={fullScreen}
  class="flex flex-col {fullScreen ? 'fixed inset-0 bg-[#0a0d14] h-[100dvh]' : 'gap-2 relative'}" 
  style={fullScreen ? `z-index: ${Z_INDEX_ADMIN.TIPTAP_FULLSCREEN}` : ''}
>

  <!-- Editor Container -->
  <div class="relative flex flex-col {editable ? 'bg-[#09090b]/40' : 'bg-transparent'} {fullScreen ? 'flex-1 min-h-0' : ''}">
    <TiptapEditor
      bind:editorRef
      bind:content
      {editable}
      {placeholder}
      fullScreen={fullScreen}
      onToggleFullScreen={() => fullScreen = !fullScreen}
      onChange={(val) => { if (editable && val !== editBuffer) { editBuffer = val; content = val; } }}
      onfix={analysis.runAutoFix}
      onClean={analysis.runCleanContent}
      annotations={analysis.editorAnnotations}
      toolbarActions={allToolbarActions}
      analysisData={analysis}
      runBulkFix={analysis.runBulkFix}
      {campaign_id}
      bind:assets
      bind:selectedAvatarUrl
      bind:selectedAssetIndex
      copyrightResult={analysis.copyrightResult}
      seoResult={analysis.seoResult}
      aiReadyResult={analysis.aiReadyResult}
      isCopyrightLoading={analysis.isCopyrightLoading}
      isSeoLoading={analysis.isSeoLoading}
      isAiLoading={analysis.isAiLoading}
      isBoosting={analysis.isBoosting}
      isBulkFixing={analysis.isBulkFixing}
      bulkFixLogs={analysis.bulkFixLogs}
      streamingText={analysis.streamingText}
      streamingTarget={analysis.streamingTarget}
    />
  </div>

</div>

<NeuralProgressTooltip 
  active={analysis.isBulkFixing || analysis.bulkFixStatus === "Hoàn tất ✅"} 
  logs={analysis.bulkFixLogs} 
  status={analysis.bulkFixStatus} 
  onClose={() => analysis.bulkFixStatus = ""}
/>

<style>
  :global(.custom-scrollbar::-webkit-scrollbar) { width: 3px; }
  :global(.custom-scrollbar::-webkit-scrollbar-thumb) { background: rgba(59,130,246,0.1); }

  /* Elite V2.2: Footer Suppression */
  :global(body.neural-fullscreen-active .admin-footer),
  :global(body.neural-fullscreen-active .admin-shell-footer),
  :global(body.neural-fullscreen-active .admin-pagination-footer),
  :global(body.neural-fullscreen-active [class*="footer"]) {
    display: none !important;
  }
</style>
