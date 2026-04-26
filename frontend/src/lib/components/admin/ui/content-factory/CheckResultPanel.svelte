<script lang="ts">
  import { onDestroy } from "svelte";
  import type { CopyrightResult, SEOResult, AIInspectResult } from "$lib/state/types";
  import { createPhaseController } from "$lib/state/xohiAnalysisPhases.svelte";
  import AnalysisLoading from "./AnalysisLoading.svelte";
  import AnalysisResultCopyright from "./AnalysisResultCopyright.svelte";
  import AnalysisResultSEO from "./AnalysisResultSEO.svelte";
  import AnalysisResultAI from "./AnalysisResultAI.svelte";
import AnalysisLocked from "./AnalysisLocked.svelte";

  let {
    activeTab, copyrightResult, isCopyrightLoading, seoResult, isSeoLoading,
    aiReadyResult, isAiLoading, isBoosting = false, runCopyrightCheck,
    runSeoAnalysis, runAiAnalysis, onfix = null,
    streamingText = "", streamingTarget = null,
    bulkFixLogs = [],
    runBulkFix,
    isBulkFixing = false,
    isRewriting = false,
    runNeuralRewrite,
    userPlanNote = $bindable(''),
    currentAnalysisStep = null,
  }: {
    activeTab: 'copyright' | 'seo' | 'ai' | 'enrich' | null;
    copyrightResult: CopyrightResult | null; isCopyrightLoading: boolean;
    seoResult: SEOResult | null; isSeoLoading: boolean;
    aiReadyResult: AIInspectResult | null; isAiLoading: boolean;
    isBoosting?: boolean; runCopyrightCheck?: () => void;
    runSeoAnalysis?: () => void; runAiAnalysis?: () => void;
    onfix?: ((snippet: string, type: string, message: string) => Promise<string | null>) | null;
    streamingText?: string;
    streamingTarget?: string | null;
    bulkFixLogs?: string[];
    runBulkFix?: () => void;
    isBulkFixing?: boolean;
    isRewriting?: boolean;
    runNeuralRewrite?: () => Promise<void>;
    userPlanNote?: string;
    currentAnalysisStep?: number | null;
  } = $props();

  let isFixing = $state<string | null>(null);
  const phaseCtrl = createPhaseController();

  // CNS V85.22: Guard phase engine
  let prevLoadingKey = $state('');
  $effect(() => {
    const key = `${activeTab}-${isBoosting}-${isCopyrightLoading}-${isSeoLoading}-${isAiLoading}`;
    if (key === prevLoadingKey) return;
    prevLoadingKey = key;
    if (activeTab === 'enrich' && isBoosting) phaseCtrl.startPhaseEngine('enrich');
    else if (activeTab === 'copyright' && isCopyrightLoading) phaseCtrl.startPhaseEngine('copyright');
    else if (activeTab === 'seo' && isSeoLoading) phaseCtrl.startPhaseEngine('seo');
    else if (activeTab === 'ai' && isAiLoading) phaseCtrl.startPhaseEngine('ai');
    else if (isRewriting) phaseCtrl.startPhaseEngine('rewrite');
    else phaseCtrl.clearTimers();
  });
  let lastTriggeredTab = $state<string | null>(null);
  $effect(() => {
    if (isLoading || isBulkFixing || isRewriting || !activeTab) return;
    if (activeTab === lastTriggeredTab) return;
    
    // CNS V91.2: Auto-trigger analysis if tab is active but no results exist
    if (activeTab === 'copyright' && !copyrightResult && !isCopyrightLoading && runCopyrightCheck) {
      lastTriggeredTab = 'copyright';
      runCopyrightCheck();
    } else if (activeTab === 'seo' && !seoResult && !isSeoLoading && runSeoAnalysis) {
      lastTriggeredTab = 'seo';
      runSeoAnalysis();
    } else if (activeTab === 'ai' && !aiReadyResult && !isAiLoading && runAiAnalysis) {
      lastTriggeredTab = 'ai';
      runAiAnalysis();
    }
  });

  $effect(() => {
    if (isLoading && activeTab) {
      phaseCtrl.syncWithLogs(bulkFixLogs, activeTab);
    }
  });

  onDestroy(() => phaseCtrl.clearTimers());

  async function handleInternalFix(snippet: string, type: string, message: string) {
    if (!onfix || isFixing) return;
    isFixing = snippet;
    try { await onfix(snippet, type, message); } finally { isFixing = null; }
  }

  const isLoading = $derived(
    (activeTab === 'copyright' && isCopyrightLoading) ||
    (activeTab === 'seo' && isSeoLoading) ||
    (activeTab === 'ai' && isAiLoading) ||
    (activeTab === 'enrich' && isBoosting) ||
    isRewriting
  );

  // ── CNS V87.0: Dashboard removal — Cleaned up unused metrics ────────
</script>

<div class="shrink-0 flex flex-col">


  <!-- ── Panel Content ── -->
  {#if isLoading}
    <AnalysisLoading tab={isRewriting ? 'rewrite' : activeTab} phaseIndex={phaseCtrl.phaseIndex} phaseProgress={phaseCtrl.phaseProgress} realStep={currentAnalysisStep} logs={bulkFixLogs} />
  {:else if activeTab === 'copyright'}
    {#if copyrightResult}
      <AnalysisResultCopyright
        {copyrightResult} {isFixing} {runCopyrightCheck} {handleInternalFix}
        {streamingText} {streamingTarget} {runBulkFix} {isBulkFixing} {isRewriting}
        {runNeuralRewrite}
        bind:userPlanNote={userPlanNote}
      />
    {:else}
      <button 
        class="w-full px-3 py-3 rounded-xl border border-white/5 bg-white/[0.02] text-center text-[9px] text-white/30 hover:bg-white/[0.05] hover:border-orange-500/20 transition-all group"
        onclick={runCopyrightCheck}
      >
        Nhấn <span class="text-orange-400/70 font-bold group-hover:text-orange-400">COPYRIGHT</span> để phân tích đạo văn.
      </button>
    {/if}
  {:else if activeTab === 'seo'}
    {#if copyrightResult && (copyrightResult.uniqueness_score < 0.60)}
      <div class="px-2 py-4">
        <AnalysisLocked 
          title="SEO Scan Restricted"
          requirement="Cấp độ tác chiến chưa đạt. SEO Scan yêu cầu nội dung có độ độc bản tối thiểu 60% để đảm bảo hiệu quả Ranking."
          currentValue="{Math.round(copyrightResult.uniqueness_score * 100)}%"
          targetValue="60%"
          colorClass="text-orange-400"
          onAction={runCopyrightCheck}
          actionLabel="Quét lại Copyright"
        />
      </div>
    {:else if seoResult}
      <AnalysisResultSEO
        {seoResult} {runSeoAnalysis} {isFixing}
        handleInternalFix={onfix ? handleInternalFix : null}
        {streamingText} {streamingTarget} {runBulkFix} {isBulkFixing}
      />
    {:else}
      <button 
        class="w-full px-3 py-3 rounded-xl border border-white/5 bg-white/[0.02] text-center text-[9px] text-white/30 hover:bg-white/[0.05] hover:border-blue-500/20 transition-all group"
        onclick={runSeoAnalysis}
      >
        Nhấn <span class="text-blue-400/70 font-bold group-hover:text-blue-400">SEO</span> để chấm điểm 7 tín hiệu SEO.
      </button>
    {/if}
  {:else if activeTab === 'ai'}
    {#if seoResult && seoResult.total_score < 60}
      <div class="px-2 py-4">
        <AnalysisLocked 
          title="AI Mod Restricted"
          requirement="Tín hiệu SEO chưa đủ mạnh. AI Mod yêu cầu bài viết đạt chuẩn SEO tối thiểu 60 điểm để đánh giá khả năng Viral."
          currentValue={seoResult.total_score}
          targetValue="60"
          colorClass="text-blue-400"
          onAction={runSeoAnalysis}
          actionLabel="Tối ưu SEO ngay"
        />
      </div>
    {:else if aiReadyResult}
      <AnalysisResultAI
        {aiReadyResult} {runAiAnalysis} {isFixing}
        handleInternalFix={onfix ? handleInternalFix : null}
        {streamingText} {streamingTarget} {runBulkFix} {isBulkFixing}
      />
    {:else}
      <button 
        class="w-full px-3 py-3 rounded-xl border border-white/5 bg-white/[0.02] text-center text-[9px] text-white/30 hover:bg-white/[0.05] hover:border-purple-500/20 transition-all group"
        onclick={runAiAnalysis}
      >
        Nhấn <span class="text-purple-400/70 font-bold group-hover:text-purple-400">AI MOD</span> để kiểm tra Viral Edge Score.
      </button>
    {/if}
  {:else if activeTab === 'enrich'}
    <div class="px-3 py-4 rounded-2xl border border-pink-500/10 bg-pink-500/[0.03] flex flex-col gap-3">
       <div class="flex items-center gap-2">
          <div class="p-1.5 rounded-lg bg-pink-500/10 text-pink-400">
             <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-brain"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .52 8.588A5.002 5.002 0 0 0 12 22a5 5 0 0 0 8-4.017s1.398-.24 2.128-1.57A4 4 0 0 0 21 11a4 4 0 0 0-3-3.95V7a3 3 0 0 0-6-2Z"/><path d="M12 12h.01"/><path d="M9 12h.01"/><path d="M15 12h.01"/></svg>
          </div>
          <span class="text-[11px] font-black uppercase tracking-widest text-pink-400">Surgeon Booster™ Status</span>
       </div>
       <p class="text-[9px] text-white/50 leading-relaxed">
          Hệ thống đang phẫu thuật nội dung. Các thay đổi được highlight <span class="text-pink-400 font-bold">Hồng Neon</span> trong văn bản.
       </p>
       <div class="flex items-center gap-2 mt-1">
          <div class="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
             <div class="h-full bg-pink-500 {isBoosting ? 'animate-pulse' : ''}" style="width: {isBoosting ? '100%' : '0%'}"></div>
          </div>
          <span class="text-[8px] font-bold text-pink-400/60 uppercase tracking-tighter">{isBoosting ? 'Operating' : 'System Ready'}</span>
       </div>
    </div>
  {/if}
</div>
