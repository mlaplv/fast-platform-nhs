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
  import { Brain, ShieldCheck, BarChart2, Sparkles } from "lucide-svelte";
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
    /** Full-screen expand mode */
    fullScreen?: boolean;
  }

  let {
    content = $bindable(),
    topic = "",
    editable = true,
    placeholder = "Nhập nội dung...",
    fullScreen = false,
  }: Props = $props();

  // Internal edit buffer — mirrors content prop while editing
  let editBuffer = $state(content);

  // Keep editBuffer in sync when content is set from outside (Zero-Flicker)
  $effect(() => { 
    if (content !== editBuffer) {
      editBuffer = content; 
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
    analysis_cache: {} as AnalysisCache,
    analysis_metrics: {} as CampaignMetrics,
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

<div class="flex flex-col gap-2">

  <!-- Editor Container -->
  <div class="relative flex flex-col {editable ? 'bg-[#09090b]/40' : 'bg-transparent'}">
    <TiptapEditor
      bind:this={editorRef}
      content={editBuffer}
      editable={editable}
      placeholder={placeholder}
      fullScreen={fullScreen}
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

  <!-- Analysis Trigger Buttons -->
  <div class="shrink-0 flex flex-col gap-2">
    <div class="flex items-center gap-2">
      <div class="relative group">
        <button
          onclick={() => {
            if (analysis.activeTab === 'copyright' && !analysis.isCopyrightLoading) handleAction(analysis.runCopyrightCheck, true);
            else { analysis.activeTab = 'copyright'; if (!analysis.copyrightResult && !analysis.isCopyrightLoading) handleAction(analysis.runCopyrightCheck); }
          }}
          disabled={analysis.isCopyrightLoading}
          class="flex items-center gap-1.5 h-[32px] px-3 {analysis.activeTab === 'copyright' ? 'bg-orange-500/15 border border-orange-500/40 text-orange-300' : 'bg-black/40 border border-white/10 text-white/60 hover:bg-white/5'}"
        >
          {#if analysis.isCopyrightLoading}<span class="w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>{:else}<ShieldCheck size={12} />{/if}
          <span class="text-[10px] uppercase font-bold tracking-wider">COPYRIGHT</span>
          {#if analysis.copyrightScore}
            <span class="text-[8px] font-black px-1.5 py-0.5 rounded-full {analysis.copyrightScore >= 90 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-yellow-500/20 text-yellow-400'}">{analysis.copyrightScore}%</span>
          {/if}
        </button>
        <CriteriaTooltip type="copyright" />
      </div>

      <div class="relative group">
        <button
          onclick={() => {
            if (analysis.activeTab === 'seo' && !analysis.isSeoLoading) handleAction(analysis.runSeoAnalysis, true);
            else { analysis.activeTab = 'seo'; if (!analysis.seoResult && !analysis.isSeoLoading && !analysis.seoLocked) handleAction(analysis.runSeoAnalysis); }
          }}
          disabled={analysis.isSeoLoading || analysis.seoLocked}
          class="flex items-center gap-1.5 h-[32px] px-3 {analysis.activeTab === 'seo' ? 'bg-blue-500/15 border border-blue-500/40 text-blue-300' : 'bg-black/40 border border-white/10 text-white/60 hover:bg-white/5'}"
        >
          {#if analysis.isSeoLoading}<span class="w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>{:else}<BarChart2 size={12} />{/if}
          <span class="text-[10px] uppercase font-bold tracking-wider">SEO</span>
          {#if analysis.seoLocked}<span>🔒</span>{:else if analysis.seoResult}
            <span class="text-[8px] font-black px-1.5 py-0.5 rounded-full {analysis.seoResult.grade === 'A' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-blue-500/20 text-blue-400'}">{analysis.seoResult.grade}.{analysis.seoResult.total_score}</span>
          {/if}
        </button>
        <CriteriaTooltip type="seo" locked={analysis.seoLocked} score={analysis.copyrightScore} />
      </div>

      <div class="relative group">
        <button
          onclick={() => {
            if (analysis.activeTab === 'ai' && !analysis.isAiLoading) handleAction(analysis.runAiAnalysis, true);
            else { analysis.activeTab = 'ai'; if (!analysis.aiReadyResult && !analysis.isAiLoading && !analysis.aiLocked) handleAction(analysis.runAiAnalysis); }
          }}
          disabled={analysis.isAiLoading || analysis.aiLocked}
          class="flex items-center gap-1.5 h-[32px] px-3 {analysis.activeTab === 'ai' ? 'bg-purple-500/15 border border-purple-500/40 text-purple-300' : 'bg-black/40 border border-white/10 text-white/60 hover:bg-white/5'}"
        >
          {#if analysis.isAiLoading}<span class="w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>{:else}<Sparkles size={12} />{/if}
          <span class="text-[10px] uppercase font-bold tracking-wider">AI MOD</span>
          {#if analysis.aiLocked}<span>🔒</span>{:else if analysis.aiScore}
            <span class="text-[8px] font-black px-1.5 py-0.5 rounded-full {analysis.aiScore >= 85 ? 'bg-purple-500/20 text-purple-400' : 'bg-fuchsia-500/20 text-fuchsia-400'}">{analysis.aiScore}%</span>
          {/if}
        </button>
        <CriteriaTooltip type="ai" locked={analysis.aiLocked} score={analysis.seoScore} />
      </div>
    </div>

    {#if analysis.activeTab}
      <div bind:this={resultPanelEl} class="max-h-52 overflow-y-auto custom-scrollbar">
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
    {/if}
  </div>
</div>

<NeuralProgressTooltip
  active={analysis.isBulkFixing}
  logs={analysis.bulkFixLogs}
  status={analysis.bulkFixStatus}
/>

<style>
  :global(.custom-scrollbar::-webkit-scrollbar) { width: 3px; }
  :global(.custom-scrollbar::-webkit-scrollbar-thumb) { background: rgba(59,130,246,0.1); }
</style>
