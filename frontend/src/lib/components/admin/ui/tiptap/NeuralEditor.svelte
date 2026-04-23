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
  import { onMount } from "svelte";
  import { fade, fly } from "svelte/transition";
  import { Brain, ShieldCheck, BarChart2, Sparkles, X, ChevronUp } from "lucide-svelte";
  import TiptapEditor from "./TiptapEditor.svelte";
  import CheckResultPanel from "../content-factory/CheckResultPanel.svelte";
  import NeuralProgressTooltip from "../content-factory/NeuralProgressTooltip.svelte";
  import CriteriaTooltip from "../content-factory/CriteriaTooltip.svelte";
  import { createAnalysisController } from "$lib/state/xohiAnalysis.svelte";
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
  }

  let {
    content = $bindable(),
    topic = "",
    editable = true,
    placeholder = "Nhập nội dung...",
    fullScreen = $bindable(false),
    analysisCache = $bindable(),
    analysisMetrics = $bindable(),
  }: Props = $props();

  // Internal edit buffer — mirrors content prop while editing
  let editBuffer = $state(content);

  // Keep editBuffer in sync when content is set from outside (Zero-Flicker)
  $effect(() => { 
    if (content !== editBuffer) {
      editBuffer = content; 
    }
  });

  // Viral UI State
  let showResultsPanel = $state(false);

  // Footer Lockdown Logic
  $effect(() => {
    if (typeof document !== 'undefined') {
      if (fullScreen) document.body.classList.add('neural-fullscreen-active');
      else document.body.classList.remove('neural-fullscreen-active');
    }
  });

  // Adhoc analysis controller — no campaign_id needed
  const analysis = createAnalysisController({
    campaign_id: null,          // Explicit null → adhoc mode
    topic,
    isEditing: editable,
    getContent: () => editBuffer,
    getEditedDraft: () => editBuffer,
    getDraftContent: () => content,
    setEditedDraft: (v) => { editBuffer = v; content = v; },
    setDraftContent: (v) => { content = v; },
    analysis_cache: () => analysisCache,
    analysis_metrics: () => analysisMetrics,
    onUpdate: (cache, metrics) => {
      analysisCache = cache;
      analysisMetrics = metrics;
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
</script>

<div class="flex flex-col {fullScreen ? 'fixed inset-0 z-[var(--z-admin-tiptap-fullscreen)] bg-[#0a0d14] h-screen' : 'gap-2 relative'}">

  <!-- Editor Container -->
  <div class="relative flex flex-col {editable ? 'bg-[#09090b]/40' : 'bg-transparent'} {fullScreen ? 'flex-1 min-h-0' : ''}">
    <TiptapEditor
      bind:this={editorRef}
      content={editBuffer}
      editable={editable}
      placeholder={placeholder}
      fullScreen={fullScreen}
      onToggleFullScreen={() => fullScreen = !fullScreen}
      onChange={(val) => { if (editable && val !== editBuffer) { editBuffer = val; content = val; } }}
      onfix={analysis.runAutoFix}
      onClean={analysis.runCleanContent}
      annotations={analysis.editorAnnotations}
      toolbarActions={[
        { label: analysis.isCopyrightLoading ? '...' : '🔍 COPYRIGHT', loading: analysis.isCopyrightLoading, onclick: () => handleAction(analysis.runCopyrightCheck, true) },
        { label: analysis.isSeoLoading ? '...' : '📊 SEO', loading: analysis.isSeoLoading, disabled: analysis.seoLocked, onclick: () => handleAction(analysis.runSeoAnalysis, true), lockedMsg: analysis.seoLocked ? '🔒 SEO bị khoá — Cần COPYRIGHT ≥ 55 trước' : undefined },
        { label: analysis.isAiLoading ? '...' : '✨ AI MOD', loading: analysis.isAiLoading, disabled: analysis.aiLocked, onclick: () => handleAction(analysis.runAiAnalysis, true), lockedMsg: analysis.aiLocked ? '🔒 AI MOD bị khoá — Cần SEO ≥ 40 trước' : undefined },
        ...(analysis.activeTab && analysis.activeTab !== 'enrich' && analysis.editorAnnotations.length > 0 ? [{
          label: analysis.isBulkFixing ? (analysis.bulkFixStatus || '✨ ĐANG PHẪU THUẬT...') : `✨ SỬA TOÀN BỘ LỖI ${(analysis.activeTab ?? '').toUpperCase()}`,
          loading: analysis.isBulkFixing,
          onclick: () => handleAction(analysis.runBulkFix)
        }] : [])
      ]}
    />
  </div>

  <!-- Analysis Trigger HUD (Viral 2026 Style) -->
  <div class="{fullScreen ? 'fixed bottom-8 left-1/2 -translate-x-1/2 z-[700000]' : 'shrink-0 mt-2'}">
    <div class="flex items-center gap-1.5 p-1.5 {fullScreen ? 'bg-black/60 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5)]' : ''}">
      <!-- Copyright Trigger -->
      <div class="relative group">
        <button
          onclick={() => {
            if (analysis.activeTab === 'copyright' && !analysis.isCopyrightLoading) showResultsPanel = true;
            else { 
              analysis.activeTab = 'copyright'; 
              showResultsPanel = true;
              if (!analysis.copyrightResult && !analysis.isCopyrightLoading) handleAction(analysis.runCopyrightCheck); 
            }
          }}
          disabled={analysis.isCopyrightLoading}
          class="flex items-center gap-1.5 h-[36px] px-4 rounded-xl transition-all duration-300 {analysis.activeTab === 'copyright' ? 'bg-orange-500/20 border border-orange-500/40 text-orange-300' : 'bg-white/5 border border-white/10 text-white/60 hover:bg-white/10'}"
        >
          {#if analysis.isCopyrightLoading}<span class="w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>{:else}<ShieldCheck size={14} />{/if}
          <span class="text-[10px] uppercase font-black tracking-widest">Copyright</span>
          {#if analysis.copyrightScore}
            <span class="text-[9px] font-black px-1.5 py-0.5 rounded-md {analysis.copyrightScore >= 90 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-yellow-500/20 text-yellow-400'}">{analysis.copyrightScore}%</span>
          {/if}
        </button>
      </div>

      <!-- SEO Trigger -->
      <div class="relative group">
        <button
          onclick={() => {
            if (analysis.activeTab === 'seo' && !analysis.isSeoLoading) showResultsPanel = true;
            else { 
              analysis.activeTab = 'seo'; 
              showResultsPanel = true;
              if (!analysis.seoResult && !analysis.isSeoLoading && !analysis.seoLocked) handleAction(analysis.runSeoAnalysis); 
            }
          }}
          disabled={analysis.isSeoLoading || analysis.seoLocked}
          class="flex items-center gap-1.5 h-[36px] px-4 rounded-xl transition-all duration-300 {analysis.activeTab === 'seo' ? 'bg-blue-500/20 border border-blue-500/40 text-blue-300' : 'bg-white/5 border border-white/10 text-white/60 hover:bg-white/10'}"
        >
          {#if analysis.isSeoLoading}<span class="w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>{:else}<BarChart2 size={14} />{/if}
          <span class="text-[10px] uppercase font-black tracking-widest">SEO</span>
          {#if analysis.seoLocked}<span>🔒</span>{:else if analysis.seoResult}
            <span class="text-[9px] font-black px-1.5 py-0.5 rounded-md {analysis.seoResult.grade === 'A' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-blue-500/20 text-blue-400'}">{analysis.seoResult.grade}.{analysis.seoResult.total_score}</span>
          {/if}
        </button>
      </div>

      <!-- AI MOD Trigger -->
      <div class="relative group">
        <button
          onclick={() => {
            if (analysis.activeTab === 'ai' && !analysis.isAiLoading) showResultsPanel = true;
            else { 
              analysis.activeTab = 'ai'; 
              showResultsPanel = true;
              if (!analysis.aiReadyResult && !analysis.isAiLoading && !analysis.aiLocked) handleAction(analysis.runAiAnalysis); 
            }
          }}
          disabled={analysis.isAiLoading || analysis.aiLocked}
          class="flex items-center gap-1.5 h-[36px] px-4 rounded-xl transition-all duration-300 {analysis.activeTab === 'ai' ? 'bg-purple-500/20 border border-purple-500/40 text-purple-300' : 'bg-white/5 border border-white/10 text-white/60 hover:bg-white/10'}"
        >
          {#if analysis.isAiLoading}<span class="w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>{:else}<Sparkles size={14} />{/if}
          <span class="text-[10px] uppercase font-black tracking-widest">AI Mod</span>
          {#if analysis.aiLocked}<span>🔒</span>{:else if analysis.aiScore}
            <span class="text-[9px] font-black px-1.5 py-0.5 rounded-md {analysis.aiScore >= 85 ? 'bg-purple-500/20 text-purple-400' : 'bg-fuchsia-500/20 text-fuchsia-400'}">{analysis.aiScore}%</span>
          {/if}
        </button>
      </div>

      {#if fullScreen && showResultsPanel}
        <button 
          onclick={() => showResultsPanel = false}
          class="w-9 h-9 flex items-center justify-center rounded-xl bg-white/5 border border-white/10 text-white/40 hover:bg-white/10 hover:text-white transition-all ml-1"
        >
          <X size={16} />
        </button>
      {/if}
    </div>
  </div>

  <!-- TikTok-style Bottom Sheet (Viral 2026) -->
  {#if analysis.activeTab && showResultsPanel}
    {#if fullScreen}
      <div 
        class="fixed inset-0 bg-black/40 backdrop-blur-sm z-[750000]" 
        onclick={() => showResultsPanel = false}
        transition:fade={{ duration: 300 }}
      ></div>
    {/if}

    <div 
      class="{fullScreen 
        ? 'fixed bottom-0 left-0 right-0 z-[800000] bg-[#0c0c0e]/95 backdrop-blur-3xl border-t border-white/10 rounded-t-[32px] shadow-[0_-20px_100px_rgba(0,0,0,0.8)] p-6' 
        : 'mt-4 bg-black/20 rounded-2xl border border-white/5 p-4'}"
      transition:fly={{ y: 100, duration: 500, opacity: 0 }}
    >
      <!-- Drag Handle (Visual only for TikTok style) -->
      {#if fullScreen}
        <div class="w-12 h-1.5 bg-white/10 rounded-full mx-auto mb-6"></div>
      {/if}

      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <div class="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20">
            {#if analysis.activeTab === 'copyright'}<ShieldCheck size={18} class="text-cyan-400" />
            {:else if analysis.activeTab === 'seo'}<BarChart2 size={18} class="text-blue-400" />
            {:else}<Sparkles size={18} class="text-purple-400" />{/if}
          </div>
          <div>
            <h3 class="text-sm font-black text-white uppercase tracking-[0.2em]">
              {analysis.activeTab === 'copyright' ? 'BÁO CÁO BẢN QUYỀN' : analysis.activeTab === 'seo' ? 'PHÂN TÍCH SEO' : 'NEURAL ENRICHMENT'}
            </h3>
            <p class="text-[10px] text-white/40 font-mono tracking-widest mt-0.5">XOHI CORE ENGINE v4.0 • ACTIVE</p>
          </div>
        </div>

        {#if fullScreen}
          <button 
            onclick={() => showResultsPanel = false}
            class="w-10 h-10 flex items-center justify-center rounded-full bg-white/5 border border-white/10 text-white/60 hover:bg-white/10 hover:text-white transition-all"
          >
            <X size={20} />
          </button>
        {/if}
      </div>

      <div class="{fullScreen ? 'max-h-[60vh]' : 'max-h-96'} overflow-y-auto custom-scrollbar">
        <CheckResultPanel
          activeTab={analysis.activeTab}
          copyrightResult={analysis.copyrightResult}
          isCopyrightLoading={analysis.isCopyrightLoading}
          seoResult={analysis.seoResult}
          isSeoLoading={analysis.isSeoLoading}
          aiReadyResult={analysis.aiReadyResult}
          isAiLoading={analysis.isAiLoading}
          isBoosting={analysis.isBoosting}
          runCopyrightCheck={analysis.runCopyrightCheck}
          runSeoAnalysis={analysis.runSeoAnalysis}
          runAiAnalysis={analysis.runAiAnalysis}
          onfix={analysis.runAutoFix}
        />
      </div>
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

  /* Elite V2.2: Footer Suppression */
  :global(body.neural-fullscreen-active .admin-footer),
  :global(body.neural-fullscreen-active .admin-shell-footer),
  :global(body.neural-fullscreen-active .admin-pagination-footer),
  :global(body.neural-fullscreen-active [class*="footer"]) {
    display: none !important;
  }
</style>
