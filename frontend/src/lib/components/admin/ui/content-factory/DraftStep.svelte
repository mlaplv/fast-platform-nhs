<script lang="ts">
  import { onMount } from "svelte";
  import { Brain, ShieldCheck, BarChart2, Sparkles } from "lucide-svelte";
  import TiptapEditor from "../tiptap/TiptapEditor.svelte";
  import CheckResultPanel from "./CheckResultPanel.svelte";
  import CriteriaTooltip from "./CriteriaTooltip.svelte";
  import { processContentImages } from "$lib/state/utils";
  import { xohiImageStore } from "$lib/state/xohiImage.svelte";
  import { createAnalysisController } from "$lib/state/xohiAnalysis.svelte";
  import type { MediaAsset, CampaignOutline, CampaignSection, CampaignMetrics, AnalysisCache } from "$lib/state/types";

  interface Props {
    campaign_id: string; isEditing: boolean; editedDraft: string; draft_content: string;
    outline: CampaignOutline; assets: (MediaAsset | string)[]; isExpanded: boolean;
    selectedAvatarUrl: string | null; selectedAssetIndex: number;
    editorRef?: TiptapEditor | null; analysis_cache: AnalysisCache; analysis_metrics: CampaignMetrics;
    copyrightScore: number | null; seoScore: number | null; aiScore: number | null; isProcessing?: boolean;
  }

  let {
    campaign_id, isEditing, editedDraft = $bindable(), draft_content = $bindable(),
    outline = {} as CampaignOutline, assets = [] as (MediaAsset | string)[], isExpanded,
    selectedAvatarUrl = $bindable(), selectedAssetIndex = $bindable(),
    editorRef = $bindable(), analysis_cache = {} as AnalysisCache, analysis_metrics = {} as CampaignMetrics,
    copyrightScore = $bindable(), seoScore = $bindable(), aiScore = $bindable(), isProcessing = false
  }: Props = $props();

  const analysis = createAnalysisController({
    campaign_id, isEditing,
    getEditedDraft: () => editedDraft, getDraftContent: () => draft_content,
    setEditedDraft: (v) => { editedDraft = v; }, setDraftContent: (v) => { draft_content = v; },
    analysis_cache, analysis_metrics
  });

  let displayContent = $derived.by(() => {
    let base = isEditing ? (editedDraft || draft_content) : draft_content;
    if (!base) {
      const sections = outline?.sections || [];
      if (sections.length > 0) {
        base = sections.map((s: CampaignSection) => {
          const hText = (s.heading || "").replace(/^(H2|H3):/i, "").trim();
          const tag = (s.heading || "").toUpperCase().startsWith("H3") ? "h3" : "h2";
          return `<${tag}>${hText}</${tag}><p>${s.content || ""}</p>`;
        }).join("\n");
      } else if (typeof outline === 'string') base = outline;
    }
    return processContentImages(base, xohiImageStore.assets.length > 0 ? xohiImageStore.assets : assets);
  });

  $effect(() => { copyrightScore = analysis.copyrightScore; seoScore = analysis.seoScore; aiScore = analysis.aiScore; });

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
  function scrollToPanel() { setTimeout(() => resultPanelEl?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 50); }

  const handleAction = async (fn: Function, ...args: any[]) => { await fn(...args); scrollToPanel(); };
</script>

<div class="p-5 md:p-8 space-y-4 flex flex-col">
  <div class="flex items-center gap-3 shrink-0">
    <div class="hidden md:block w-8 h-px bg-gradient-to-r from-transparent to-blue-500/50"></div>
    <h5 class="hidden md:block text-[11px] font-black uppercase tracking-[0.2em] text-blue-400/60">XOHI · <span class="bg-gradient-to-r from-blue-400 via-cyan-300 to-blue-500 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(99,179,237,0.6)]">NEURAL STUDIO</span></h5>
    {#if analysis.copyrightScore !== null}<span class="text-[9px] font-black uppercase {analysis.copyrightScore >= 90 ? 'text-emerald-400' : 'text-yellow-400'}">· Copyright {analysis.copyrightScore}%</span>{/if}
    {#if analysis.seoResult}<span class="text-[9px] font-black uppercase {analysis.seoResult.grade === 'A' ? 'text-emerald-400' : 'text-blue-400'}">· SEO {analysis.seoResult.grade} ({analysis.seoResult.total_score}/100)</span>{/if}
    {#if analysis.aiScore !== null}<span class="text-[9px] font-black uppercase {analysis.aiScore >= 85 ? 'text-purple-400' : 'text-fuchsia-400'}">· AI {analysis.aiScore}%</span>{/if}
    {#if lastAnalyzedTime}<span class="text-[8px] font-medium text-white/20 ml-auto">Lân cuối: {lastAnalyzedTime}</span>{/if}
  </div>

  <div class="flex flex-col relative transition-all duration-500 {isEditing ? 'border border-white/5 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.8)] bg-[#09090b]/40 backdrop-blur-2xl' : 'bg-transparent'}">
    {#if isProcessing && !displayContent}
      <div class="absolute inset-0 z-20 flex flex-col items-center justify-center bg-slate-950/60 backdrop-blur-md animate-in fade-in duration-700">
        <div class="w-20 h-20 rounded-full border-t-2 border-r-2 border-purple-500/40 animate-spin"></div>
        <span class="mt-8 text-[10px] font-black uppercase tracking-[0.3em] text-purple-400/80 animate-pulse">AI đang chấp bút bản thảo</span>
      </div>
    {/if}
    <TiptapEditor
      bind:this={editorRef} content={displayContent} bind:assets bind:selectedAvatarUrl bind:selectedAssetIndex editable={isEditing} placeholder="AI đang chấp bút bản thảo..." fullScreen={isExpanded} campaignId={campaign_id}
      onChange={(val) => { if (isEditing && val !== editedDraft) editedDraft = val; }}
      onfix={analysis.runAutoFix} annotations={analysis.editorAnnotations}
      toolbarActions={[
        { label: analysis.isCopyrightLoading ? '...' : '🔍 COPYRIGHT', loading: analysis.isCopyrightLoading, onclick: () => handleAction(analysis.runCopyrightCheck, true) },
        { label: analysis.isSeoLoading ? '...' : '📊 SEO', loading: analysis.isSeoLoading, disabled: analysis.seoLocked, onclick: () => handleAction(analysis.runSeoAnalysis, true), lockedMsg: analysis.seoLocked ? `🔒 SEO bị khoá — Cần COPYRIGHT ≥ 90 trước` : undefined },
        { label: analysis.isAiLoading ? '...' : '✨ AI MOD', loading: analysis.isAiLoading, disabled: analysis.aiLocked, onclick: () => handleAction(analysis.runAiAnalysis, true), lockedMsg: analysis.aiLocked ? `🔒 AI MOD bị khoá — Cần SEO ≥ 70 trước` : undefined },
        ...(analysis.seoResult && analysis.seoResult.total_score < 95 ? [{ label: analysis.isBoosting ? '🚀 ENRICHING...' : '🚀 AI BOOSTER', loading: analysis.isBoosting, onclick: () => handleAction(analysis.runAiBooster), tooltipDetails: { title: 'AI Booster™', description: 'Tự động cấy số liệu thực tế và câu quote chuyên gia để ép SEO vượt 95đ.', icon: Brain, colorClass: 'text-pink-400' } }] : []),
        ...(analysis.activeTab && analysis.activeTab !== 'enrich' && (analysis.editorAnnotations.length > 0) ? [{ label: analysis.isBulkFixing ? '✨ ĐANG PHẪU THUẬT...' : `✨ SỬA TOÀN BỘ LỖI ${analysis.activeTab.toUpperCase()}`, loading: analysis.isBulkFixing, onclick: () => handleAction(analysis.runBulkFix) }] : [])
      ]}
    />
  </div>

  <div class="shrink-0 flex flex-col gap-2">
    <div class="flex items-center gap-2">
      <div class="relative group">
        <button onclick={() => !analysis.copyrightResult && !analysis.isCopyrightLoading ? handleAction(analysis.runCopyrightCheck) : (analysis.activeTab = 'copyright')} disabled={analysis.isCopyrightLoading} class="flex items-center gap-1.5 px-3 py-1.5 {analysis.activeTab === 'copyright' ? 'bg-orange-500/15 border border-orange-500/40 text-orange-300' : 'bg-black/40 border border-white/10 text-white/60 hover:bg-white/5'}">
          {#if analysis.isCopyrightLoading}<span class="w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>{:else}<ShieldCheck size={12} />{/if}
          <span class="text-[10px] uppercase font-bold tracking-wider">COPYRIGHT</span>
          {#if analysis.copyrightScore}<span class="text-[8px] font-black px-1.5 py-0.5 rounded-full {analysis.copyrightScore >= 90 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-yellow-500/20 text-yellow-400'}">{analysis.copyrightScore}%</span>{/if}
        </button>
        <CriteriaTooltip type="copyright" />
      </div>

      <div class="relative group">
        <button onclick={() => !analysis.seoResult && !analysis.isSeoLoading && !analysis.seoLocked ? handleAction(analysis.runSeoAnalysis) : (analysis.activeTab = 'seo')} disabled={analysis.isSeoLoading || analysis.seoLocked} class="flex items-center gap-1.5 px-3 py-1.5 {analysis.activeTab === 'seo' ? 'bg-blue-500/15 border border-blue-500/40 text-blue-300' : 'bg-black/40 border border-white/10 text-white/60 hover:bg-white/5'}">
          {#if analysis.isSeoLoading}<span class="w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>{:else}<BarChart2 size={12} />{/if}
          <span class="text-[10px] uppercase font-bold tracking-wider">SEO</span>
          {#if analysis.seoLocked}<span>🔒</span>{:else if analysis.seoResult}<span class="text-[8px] font-black px-1.5 py-0.5 rounded-full {analysis.seoResult.grade === 'A' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-blue-500/20 text-blue-400'}">{analysis.seoResult.grade}.{analysis.seoResult.total_score}</span>{/if}
        </button>
        <CriteriaTooltip type="seo" locked={analysis.seoLocked} score={analysis.copyrightScore} />
      </div>

      <div class="relative group">
        <button onclick={() => !analysis.aiReadyResult && !analysis.isAiLoading && !analysis.aiLocked ? handleAction(analysis.runAiAnalysis) : (analysis.activeTab = 'ai')} disabled={analysis.isAiLoading || analysis.aiLocked} class="flex items-center gap-1.5 px-3 py-1.5 {analysis.activeTab === 'ai' ? 'bg-purple-500/15 border border-purple-500/40 text-purple-300' : 'bg-black/40 border border-white/10 text-white/60 hover:bg-white/5'}">
          {#if analysis.isAiLoading}<span class="w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>{:else}<Sparkles size={12} />{/if}
          <span class="text-[10px] uppercase font-bold tracking-wider">AI MOD</span>
          {#if analysis.aiLocked}<span>🔒</span>{:else if analysis.aiScore}<span class="text-[8px] font-black px-1.5 py-0.5 rounded-full {analysis.aiScore >= 85 ? 'bg-purple-500/20 text-purple-400' : 'bg-fuchsia-500/20 text-fuchsia-400'}">{analysis.aiScore}%</span>{/if}
        </button>
        <CriteriaTooltip type="ai" locked={analysis.aiLocked} score={analysis.seoScore} />
      </div>
    </div>

    {#if analysis.activeTab}
      <div bind:this={resultPanelEl} class="max-h-52 overflow-y-auto custom-scrollbar">
        <CheckResultPanel activeTab={analysis.activeTab} copyrightResult={analysis.copyrightResult} isCopyrightLoading={analysis.isCopyrightLoading} seoResult={analysis.seoResult} isSeoLoading={analysis.isSeoLoading} aiReadyResult={analysis.aiReadyResult} isAiLoading={analysis.isAiLoading} isBoosting={analysis.isBoosting} runCopyrightCheck={analysis.runCopyrightCheck} runSeoAnalysis={analysis.runSeoAnalysis} runAiAnalysis={analysis.runAiAnalysis} onfix={analysis.runAutoFix} />
      </div>
    {/if}
  </div>
</div>

<style>
  :global(.custom-scrollbar::-webkit-scrollbar) { width: 3px; }
  :global(.custom-scrollbar::-webkit-scrollbar-thumb) { background: rgba(59,130,246,0.1); }
  @keyframes shimmer { 0%, 100% { opacity: 0.3; } 50% { opacity: 0.7; } }
  .animate-pulse { animation: shimmer 2s infinite ease-in-out; }
</style>
