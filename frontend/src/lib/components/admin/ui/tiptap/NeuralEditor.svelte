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
    /** Enable flex-1 fill behavior */
    flex?: boolean;
    /** Content Type: 'product' | 'article' */
    contentType?: string;
    /** Metadata provider function */
    getMetadata?: () => Record<string, object> | null;
    /** Whether the editor is in full screen mode */
    fullScreen?: boolean;
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
    assets = $bindable(),
    selectedAvatarUrl = $bindable(),
    selectedAssetIndex = $bindable(),
    analysisReport = $bindable(),
    flex = false,
    contentType = "article",
    getMetadata = () => null,
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
    contentType: () => contentType,
    getMetadata: () => getMetadata(),
    onUpdate: (cache, metrics) => {
      untrack(() => {
        analysisCache = cache;
        analysisMetrics = metrics;
      });
    }
  });

  let editorRef = $state<TiptapEditor | null>(null);
  let resultPanelEl = $state<HTMLElement | null>(null);

  onMount(() => {
    if (content === undefined) content = "";
    if (fullScreen === undefined) fullScreen = false;
    if (assets === undefined) assets = [];
    if (selectedAvatarUrl === undefined) selectedAvatarUrl = null;
    if (selectedAssetIndex === undefined) selectedAssetIndex = 0;
  });

  function scrollToPanel() {
    setTimeout(() => resultPanelEl?.scrollIntoView({ behavior: "smooth", block: "nearest" }), 50);
  }

  async function handleAction<T extends unknown[]>(action: (...args: T) => Promise<unknown> | unknown, ...args: T) {
    if (analysis.isCopyrightLoading || analysis.isSeoLoading || analysis.isAiLoading) return;
    await action(...args);
    scrollToPanel();
  }

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
      // Golden Criteria: Uniqueness >= 90% (Relaxed from 95%)
      isPerfect: analysis.copyrightResult ? (analysis.copyrightResult.uniqueness_score >= 0.90) : false,
      // Locked: Only if really bad (< 50%) or no result
      isLocked: analysis.copyrightResult ? (analysis.copyrightResult.uniqueness_score < 0.50) : false,
      active: analysis.activeTab === 'copyright',
      colorClass: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
      title: analysis.copyrightResult ? `Copyright: ${Math.round(analysis.copyrightResult.uniqueness_score * 100)}% uniqueness` : 'Click to scan Copyright'
    },
    // Progressive Disclosure: Always show if Copyright is done (>= 60%)
    ...(!analysis.seoLocked ? [{
      id: 'seo',
      label: analysis.seoResult ? `SEO ${analysis.seoResult.total_score}/100` : 'SEO Scan',
      icon: BarChart2,
      onclick: () => {
        if (analysis.activeTab === 'seo') handleAction(analysis.runSeoAnalysis, true);
        else {
          analysis.activeTab = 'seo';
          if (!analysis.seoResult && !analysis.isSeoLoading) handleAction(analysis.runSeoAnalysis);
        }
      },
      loading: analysis.isSeoLoading,
      isPerfect: analysis.seoResult ? (analysis.seoResult.total_score >= 90) : false,
      isLocked: analysis.seoResult ? (analysis.seoResult.total_score < 50) : false,
      active: analysis.activeTab === 'seo',
      colorClass: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      title: analysis.seoLocked ? 'Cần đạt trên 60% Copyright để chạy SEO' : (analysis.seoResult ? `SEO: ${analysis.seoResult.total_score}/100` : 'Click to scan SEO')
    }] : []),

    ...(!analysis.aiLocked ? [{
      id: 'ai',
      label: analysis.aiReadyResult ? `AI Mod ${analysis.aiReadyResult.geo_score}/100` : 'AI Mod',
      icon: Sparkles,
      onclick: () => {
        if (analysis.activeTab === 'ai') handleAction(analysis.runAiAnalysis, true);
        else {
          analysis.activeTab = 'ai';
          if (!analysis.aiReadyResult && !analysis.isAiLoading) handleAction(analysis.runAiAnalysis);
        }
      },
      loading: analysis.isAiLoading,
      isPerfect: analysis.aiReadyResult ? (analysis.aiReadyResult.viral_score >= 8.0) : false,
      isLocked: false, // AI Mod is never locked once SEO is decent
      active: analysis.activeTab === 'ai',
      colorClass: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
      title: analysis.aiLocked ? 'Cần đạt trên 60% SEO để chạy AI Mod' : (analysis.aiReadyResult ? `AI Mod: ${analysis.aiReadyResult.geo_score}/100` : 'Click to scan AI Mod')
    }] : []),

    ...(!analysis.enrichLocked ? [{
      id: 'enrich',
      label: analysis.isBoosting ? '🚀 ENRICHING...' : '🚀 AI BOOSTER',
      loading: analysis.isBoosting,
      disabled: analysis.seoScore !== null && analysis.seoScore >= 95,
      onclick: () => handleAction(analysis.runAiBooster),
      active: analysis.activeTab === 'enrich',
      colorClass: 'bg-pink-500/10 text-pink-400 border-pink-500/20'
    }] : []),

    // Contextual Fix All: Only show if critical issues exist in the active tab
    ...(analysis.activeTab === 'copyright' && (analysis.copyrightResult?.annotations?.filter(a => a.type !== 'fixed-area').length || 0) > 0 ? [{
      id: 'copyright-fix',
      label: analysis.isBulkFixing ? (analysis.bulkFixStatus || 'ĐANG PHẪU THUẬT...') : '✨ PHẪU THUẬT BẢN QUYỀN',
      icon: ShieldCheck,
      onclick: () => analysis.runBulkFix(),
      loading: analysis.isBulkFixing,
      colorClass: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30 font-black'
    }] : []),
    ...(analysis.activeTab === 'seo' && (analysis.seoResult?.seo_annotations?.filter(a => a.type !== 'fixed-area' && a.severity !== 'info').length || 0) > 0 ? [{
      id: 'seo-fix',
      label: analysis.isBulkFixing ? (analysis.bulkFixStatus || 'ĐANG PHẪU THUẬT...') : '✨ PHẪU THUẬT SEO',
      icon: BarChart2,
      onclick: () => analysis.runBulkFix(),
      loading: analysis.isBulkFixing,
      colorClass: 'bg-blue-500/20 text-blue-400 border-blue-500/30 font-black'
    }] : []),
    ...(analysis.activeTab === 'ai' && (analysis.aiReadyResult?.ai_annotations?.filter(a => a.type !== 'fixed-area' && a.severity === 'high').length || 0) > 0 ? [{
      id: 'ai-fix',
      label: analysis.isBulkFixing ? (analysis.bulkFixStatus || 'ĐANG PHẪU THUẬT...') : '✨ PHẪU THUẬT CẤU TRÚC (VIRAL)',
      icon: Sparkles,
      onclick: () => analysis.runBulkFix(),
      loading: analysis.isBulkFixing,
      colorClass: 'bg-purple-500/20 text-purple-400 border-purple-500/30 font-black'
    }] : [])
  ]);
  const allToolbarActions = $derived([...analysisActions, ...toolbarActions]);
</script>

<div 
  use:portal={fullScreen}
  class="flex flex-col {fullScreen ? 'fixed inset-0 bg-[#0a0d14] h-[100dvh] w-[100vw]' : (flex ? 'flex-1 min-h-0 relative' : 'gap-2 relative')}" 
  style={fullScreen ? `z-index: ${Z_INDEX_ADMIN.TIPTAP_FULLSCREEN}; pointer-events: auto;` : ''}
>

  <!-- Editor Container -->
  <div class="relative flex flex-col {editable ? 'bg-[#09090b]/40' : 'bg-transparent'} {fullScreen || flex ? 'flex-1 min-h-0' : ''}">
    <TiptapEditor
      bind:editorRef
      bind:content
      {editable}
      {placeholder}
      bind:fullScreen
      {flex}
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
      isRewriting={analysis.isRewriting}
      bulkFixLogs={analysis.bulkFixLogs}
      streamingText={analysis.streamingText}
      streamingTarget={analysis.streamingTarget}
    />
  </div>

</div>


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
