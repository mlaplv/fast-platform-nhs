<script lang="ts">
  import { onMount } from "svelte";
  import { Brain, ShieldCheck, BarChart2, Sparkles } from "lucide-svelte";
  import TiptapEditor from "../tiptap/TiptapEditor.svelte";
  import CheckResultPanel from "./CheckResultPanel.svelte";
  import CriteriaTooltip from "./CriteriaTooltip.svelte";
  import NeuralProgressTooltip from "./NeuralProgressTooltip.svelte";
  import UltraPremiumLoading from "./UltraPremiumLoading.svelte";
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
    get analysis_cache() { return analysis_cache; },
    get analysis_metrics() { return analysis_metrics; }
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
  let isFullResults = $state(false); // CNS V85: Detailed view for IDE-like progress
  
  function scrollToPanel() { setTimeout(() => resultPanelEl?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 50); }
  const handleAction = async (fn: Function, ...args: any[]) => { await fn(...args); scrollToPanel(); };
</script>

<div class="p-5 md:p-8 flex flex-col flex-1 min-h-0 overflow-hidden">
  <div class="flex items-center gap-3 shrink-0 mb-4">
    <div class="hidden md:block w-8 h-px bg-gradient-to-r from-transparent to-blue-500/50"></div>
    <h5 class="hidden md:block text-[11px] font-black uppercase tracking-[0.2em] text-blue-400/60">XOHI · <span class="bg-gradient-to-r from-blue-400 via-cyan-300 to-blue-500 bg-clip-text text-transparent drop-shadow-[0_0_8px_rgba(99,179,237,0.6)]">NEURAL STUDIO</span></h5>
    
    <div class="flex items-center gap-2 ml-4 overflow-x-auto no-scrollbar pb-1">
      <button
        onclick={() => {
          if (analysis.activeTab === 'copyright') {
            handleAction(analysis.runCopyrightCheck, true);
          } else {
            analysis.activeTab = 'copyright';
            if (!analysis.copyrightResult && !analysis.isCopyrightLoading) handleAction(analysis.runCopyrightCheck);
          }
        }}
        disabled={analysis.isCopyrightLoading}
        class="flex items-center gap-1.5 text-[10px] sm:text-xs font-black uppercase px-3 py-1.5 rounded-lg border {analysis.activeTab === 'copyright' ? 'border-orange-500/50 bg-orange-500/10 text-orange-400' : 'border-white/10 bg-white/5 text-white/40 hover:text-white/60'} {analysis.isCopyrightLoading ? 'opacity-70' : ''} transition-all active:scale-95"
      >
        {#if analysis.isCopyrightLoading}<span class="w-3 h-3 border-2 border-white/20 border-t-orange-400 rounded-full animate-spin"></span>{/if}
        COPYRIGHT {analysis.copyrightScore !== null ? `${analysis.copyrightScore}%` : ''}
      </button>
      
      <button
        onclick={() => {
          if (!analysis.seoLocked) {
            if (analysis.activeTab === 'seo') {
              handleAction(analysis.runSeoAnalysis, true);
            } else {
              analysis.activeTab = 'seo';
              if (!analysis.seoResult && !analysis.isSeoLoading) handleAction(analysis.runSeoAnalysis);
            }
          }
        }}
        disabled={analysis.seoLocked || analysis.isSeoLoading}
        class="flex items-center gap-1.5 text-[10px] sm:text-xs font-black uppercase px-3 py-1.5 rounded-lg border {analysis.activeTab === 'seo' ? 'border-blue-500/50 bg-blue-500/10 text-blue-400' : 'border-white/10 bg-white/5 text-white/40 hover:text-white/60'} {analysis.seoLocked ? 'opacity-30 cursor-not-allowed' : ''} {analysis.isSeoLoading ? 'opacity-70' : ''} transition-all active:scale-95"
      >
        {#if analysis.isSeoLoading}<span class="w-3 h-3 border-2 border-white/20 border-t-blue-400 rounded-full animate-spin"></span>{/if}
        SEO {analysis.seoResult ? analysis.seoResult.grade : ''}
      </button>

      <button
        onclick={() => {
          if (!analysis.aiLocked) {
            if (analysis.activeTab === 'ai') {
              handleAction(analysis.runAiAnalysis, true);
            } else {
              analysis.activeTab = 'ai';
              if (!analysis.aiReadyResult && !analysis.isAiLoading) handleAction(analysis.runAiAnalysis);
            }
          }
        }}
        disabled={analysis.aiLocked || analysis.isAiLoading}
        class="flex items-center gap-1.5 text-[10px] sm:text-xs font-black uppercase px-3 py-1.5 rounded-lg border {analysis.activeTab === 'ai' ? 'border-purple-500/50 bg-purple-500/10 text-purple-400' : 'border-white/10 bg-white/5 text-white/40 hover:text-white/60'} {analysis.aiLocked ? 'opacity-30 cursor-not-allowed' : ''} {analysis.isAiLoading ? 'opacity-70' : ''} transition-all active:scale-95"
      >
        {#if analysis.isAiLoading}<span class="w-3 h-3 border-2 border-white/20 border-t-purple-400 rounded-full animate-spin"></span>{/if}
        AI MOD {analysis.aiScore !== null ? `${analysis.aiScore}%` : ''}
      </button>

      {#if analysis.isBoosting}
        <div class="flex items-center gap-1.5 text-[10px] sm:text-xs font-black uppercase px-3 py-1.5 rounded-lg border border-pink-500/50 bg-pink-500/10 text-pink-400 animate-pulse shadow-[0_0_15px_rgba(236,72,153,0.2)]">
          <Brain size={12} class="animate-bounce" />
          BOOSTING...
        </div>
      {/if}

      {#if analysis.activeTab}
        <button 
          onclick={() => isFullResults = !isFullResults}
          class="flex items-center gap-1.5 text-[10px] font-black uppercase px-3 py-1.5 rounded-lg border {isFullResults ? 'border-blue-400 bg-blue-500/20 text-white' : 'border-blue-500/20 bg-blue-500/5 text-blue-400/60'} hover:text-blue-400 hover:border-blue-500/40 transition-all ml-2"
        >
          {isFullResults ? '☒ THU NHỎ' : '✦ VIEW FULL'}
        </button>
      {/if}
    </div>

    {#if lastAnalyzedTime}<span class="hidden sm:block text-[8px] font-medium text-white/20 ml-auto uppercase tracking-widest">Update: {lastAnalyzedTime}</span>{/if}
  </div>

  <div class="flex flex-col relative flex-1 min-h-0 transition-all duration-500 {isEditing ? 'border border-white/5 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.8)] bg-[#09090b]/40 backdrop-blur-2xl' : 'bg-transparent'}">
    {#if isProcessing}
      <div class="absolute inset-0 z-[100]">
        <UltraPremiumLoading 
          progress_msg="AI đang chấp bút bản thảo..." 
          viewingStep={4} 
          campaign_id={campaign_id} 
          liveContent={displayContent || ""} 
        />
      </div>
    {/if}
    <TiptapEditor
      bind:this={editorRef} content={displayContent} bind:assets bind:selectedAvatarUrl bind:selectedAssetIndex editable={isEditing} placeholder="AI đang chấp bút bản thảo..." fullScreen={isExpanded} campaignId={campaign_id} flex={true} syncAssetsMode="append"
      onChange={(val) => { if (isEditing && val !== editedDraft) editedDraft = val; }}
      onfix={analysis.runAutoFix} annotations={analysis.editorAnnotations}
      onClean={analysis.runCleanContent}
      toolbarActions={[
        { label: analysis.isCopyrightLoading ? '...' : '🔍 COPYRIGHT', loading: analysis.isCopyrightLoading, onclick: () => handleAction(analysis.runCopyrightCheck, true) },
        { label: analysis.isSeoLoading ? '...' : '📊 SEO', loading: analysis.isSeoLoading, disabled: analysis.seoLocked, onclick: () => handleAction(analysis.runSeoAnalysis, true), lockedMsg: analysis.seoLocked ? `🔒 SEO bị khoá — Cần COPYRIGHT ≥ 55 trước` : undefined },
        { label: analysis.isAiLoading ? '...' : '✨ AI MOD', loading: analysis.isAiLoading, disabled: analysis.aiLocked, onclick: () => handleAction(analysis.runAiAnalysis, true), lockedMsg: analysis.aiLocked ? `🔒 AI MOD bị khoá — Cần SEO ≥ 40 trước` : undefined },
        ...(analysis.seoResult && analysis.seoResult.total_score < 95 ? [{ label: analysis.isBoosting ? '🚀 ENRICHING...' : '🚀 AI BOOSTER', loading: analysis.isBoosting, onclick: () => handleAction(analysis.runAiBooster), tooltipDetails: { title: 'AI Booster™', description: 'Tự động cấy số liệu thực tế và câu quote chuyên gia để ép SEO vượt 95đ.', icon: Brain, colorClass: 'text-pink-400' } }] : []),
        ...(analysis.activeTab && analysis.activeTab !== 'enrich' && (analysis.editorAnnotations.length > 0) ? [{ 
          label: analysis.isBulkFixing ? (analysis.bulkFixStatus || '✨ ĐANG PHẪU THUẬT...') : `✨ SỬA TOÀN BỘ LỖI ${analysis.activeTab.toUpperCase()}`, 
          loading: analysis.isBulkFixing, 
          onclick: () => handleAction(analysis.runBulkFix) 
        }] : [])
      ]}
    />
  </div>

    {#if analysis.activeTab}
      <div 
        bind:this={resultPanelEl} 
        class="overflow-y-auto custom-scrollbar border-t border-white/5 p-4 transition-all duration-500 {isFullResults ? 'absolute inset-0 z-50 bg-[#09090b]/98 backdrop-blur-3xl' : 'mt-4 max-h-52 md:max-h-72 shrink-0 bg-white/[0.02] rounded-2xl border border-white/5 shadow-2xl'}"
      >
        {#if isFullResults}
          <div class="flex items-center justify-between mb-8 border-b border-white/10 pb-4 shrink-0">
             <div class="flex items-center gap-3">
               <div class="w-3 h-3 rounded-full bg-blue-500 blur-sm animate-pulse"></div>
               <h2 class="text-xl font-black uppercase tracking-widest text-white/80">Chi tiết Phân tích {analysis.activeTab.toUpperCase()}</h2>
             </div>
             <button onclick={() => isFullResults = false} class="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-xs font-black text-white/60 hover:text-white hover:bg-white/10 transition-all">✕ ĐÓNG LẠI</button>
          </div>
        {:else}
          <div class="flex items-center justify-between mb-3 shrink-0">
             <span class="text-[9px] font-black uppercase tracking-widest text-white/20">Kết quả phân tích</span>
             <button onclick={() => isFullResults = true} class="text-[9px] font-black text-blue-400/40 hover:text-blue-400 transition-colors uppercase tracking-widest flex items-center gap-1">
                <Sparkles size={10} /> XEM TOÀN BỘ (FULL VIEW)
             </button>
          </div>
        {/if}
        <CheckResultPanel activeTab={analysis.activeTab} copyrightResult={analysis.copyrightResult} isCopyrightLoading={analysis.isCopyrightLoading} seoResult={analysis.seoResult} isSeoLoading={analysis.isSeoLoading} aiReadyResult={analysis.aiReadyResult} isAiLoading={analysis.isAiLoading} isBoosting={analysis.isBoosting} runCopyrightCheck={analysis.runCopyrightCheck} runSeoAnalysis={analysis.runSeoAnalysis} runAiAnalysis={analysis.runAiAnalysis} onfix={analysis.runAutoFix} />
      </div>
    {/if}
</div>

<NeuralProgressTooltip 
  active={analysis.isBulkFixing} 
  logs={analysis.bulkFixLogs} 
  status={analysis.bulkFixStatus} 
/>

<style>
  :global(.custom-scrollbar::-webkit-scrollbar) { width: 3px; }
  :global(.custom-scrollbar::-webkit-scrollbar-thumb) { background: rgba(59,130,246,0.1); }
  @keyframes shimmer { 0%, 100% { opacity: 0.3; } 50% { opacity: 0.7; } }
  .animate-pulse { animation: shimmer 2s infinite ease-in-out; }
</style>
