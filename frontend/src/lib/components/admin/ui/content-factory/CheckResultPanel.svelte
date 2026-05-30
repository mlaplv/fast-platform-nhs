<script lang="ts">
  import { onDestroy } from "svelte";
  import type { CopyrightResult, SEOResult, AIInspectResult, AnalysisAnnotation } from "$lib/state/types";
  import { createPhaseController } from "$lib/state/xohiAnalysisPhases.svelte";
  import { stripBoostTags } from "$lib/state/xohiAnalysisLogic";
  import AnalysisLoading from "./AnalysisLoading.svelte";
  import AnalysisResultCopyright from "./AnalysisResultCopyright.svelte";
  import AnalysisResultSEO from "./AnalysisResultSEO.svelte";
  import AnalysisResultAI from "./AnalysisResultAI.svelte";
  import AnalysisLocked from "./AnalysisLocked.svelte";
  import CheckCircle2 from "@lucide/svelte/icons/check-circle-2";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";

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
    runBulkBoosterFix,
    runAiBooster,
    userPlanNote = $bindable(),
    currentAnalysisStep = null,
    boosterAnnotations = [],
    clinicalSources = [],
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
    runBulkBoosterFix?: () => Promise<void>;
    runAiBooster?: () => Promise<void>;
    userPlanNote?: string;
    currentAnalysisStep?: number | null;
    boosterAnnotations?: AnalysisAnnotation[];
    clinicalSources?: Array<{
      title_vi: string;
      title_original: string;
      source_domain: string;
      source_url: string;
      year: string;
      snippet_vi: string;
      relevance: string;
    }>;
  } = $props();

  $effect.pre(() => {
    if (userPlanNote === undefined) {
      userPlanNote = '';
    }
  });

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
    <div class="flex flex-col">
      <!-- Header: Booster Status -->
      <div class="relative pt-3 pb-1 overflow-hidden">
        <div class="absolute -top-10 -right-10 w-32 h-32 blur-[50px] opacity-15 bg-pink-500"></div>
        <div class="relative z-10 flex items-center gap-3 px-3">
          <div class="p-2 rounded-xl bg-pink-500/10 border border-pink-500/20 shadow-[0_0_15px_rgba(236,72,153,0.15)]">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-pink-400"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .52 8.588A5.002 5.002 0 0 0 12 22a5 5 0 0 0 8-4.017s1.398-.24 2.128-1.57A4 4 0 0 0 21 11a4 4 0 0 0-3-3.95V7a3 3 0 0 0-6-2Z"/><path d="M12 12h.01"/><path d="M9 12h.01"/><path d="M15 12h.01"/></svg>
          </div>
            <div class="flex items-center gap-2">
              <span class="text-sm font-black tracking-[0.1em] text-pink-400">
                🔪 Surgeon Booster™
              </span>
              {#if boosterAnnotations.length > 0 && !isBoosting}
                <button 
                  onclick={() => runAiBooster?.()}
                  class="p-1.5 rounded-lg hover:bg-pink-500/10 text-pink-500/40 hover:text-pink-400 transition-all active:scale-90"
                  title="Chạy lại Booster"
                >
                  <RefreshCw size={12} strokeWidth={3} />
                </button>
              {/if}
            </div>
            <div class="flex items-center gap-1.5 opacity-30">
              <span class="text-[9px] font-black tracking-[0.3em]">Protocol_EEAT_Boost_V2.2</span>
            </div>
          
          {#if boosterAnnotations.some(a => !a.is_applied) && !isBoosting}
            <div class="ml-auto pr-3">
              <button 
                onclick={runBulkBoosterFix}
                disabled={isBulkFixing}
                class="px-3 py-1.5 rounded-lg bg-emerald-500 text-black text-[9px] font-black tracking-widest hover:bg-emerald-400 hover:scale-105 active:scale-95 transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)] flex items-center gap-2"
              >
                <CheckCircle2 size={12} />
                Duyệt tất cả
              </button>
            </div>
          {/if}
        </div>
      </div>

      {#if boosterAnnotations.length > 0}
        <!-- Summary Verdict -->
        <div class="px-4 py-3 bg-black/40 border-b border-white/5 shadow-inner">
          <div class="flex items-center gap-2 mb-2 opacity-30">
            <div class="w-1.5 h-1.5 rounded-full bg-pink-500 shadow-[0_0_8px_rgba(236,72,153,0.6)]"></div>
            <span class="text-[10px] font-black tracking-[0.2em]">Neural_Boost_Verdict</span>
          </div>
          <p class="text-[13px] text-white/90 leading-[1.6] font-medium tracking-tight">
            ✅ Đã phẫu thuật thành công <span class="text-pink-400 font-black">{boosterAnnotations.length}</span> đoạn văn. Các điểm cải tiến được highlight <span class="text-pink-400 font-bold">Hồng Neon</span> trong văn bản.
          </p>
        </div>

        <!-- Badge -->
        <div class="px-3 py-2 flex items-center gap-3 border-b border-white/5">
          <span class="text-[7px] font-black text-white/20 tracking-widest">Patches ({boosterAnnotations.length})</span>
          <span class="px-2 py-0.5 rounded-full text-[8px] font-black bg-pink-500/10 text-pink-400 border border-pink-500/20 tracking-tighter">Review Required</span>
        </div>

        <!-- Annotation List -->
        <div class="flex flex-col">
          {#each boosterAnnotations as ann, i}
            <div class="px-3 py-3 border-b bg-white/[0.01] flex flex-col gap-1.5 transition-all hover:bg-white/[0.02]" style="border-color: rgba(236,72,153,0.1)">
              <div class="flex items-start justify-between gap-2">
                <span class="text-[7px] font-black px-1 py-0.5 rounded bg-pink-500/20 text-pink-400">✨ PATCH #{i + 1}</span>
                
                {#if onfix}
                  {#if ann.is_applied}
                    <div class="flex items-center gap-1 px-2 py-1 rounded bg-emerald-500/10 border border-emerald-500/20 text-[8px] font-black text-emerald-400 tracking-widest">
                      ĐÃ DUYỆT ✅
                    </div>
                  {:else}
                    <button 
                      onclick={() => handleInternalFix(ann.search_string || ann.text, 'enrich', ann.replacement_string || '')}
                      disabled={isFixing === (ann.search_string || ann.text)}
                      class="px-2 py-1 rounded bg-emerald-500/20 border border-emerald-500/30 text-[8px] font-black text-emerald-400 tracking-widest hover:bg-emerald-500 hover:text-white transition-all disabled:opacity-50"
                    >
                      {#if isFixing === (ann.search_string || ann.text)}
                        PHẪU THUẬT...
                      {:else}
                        DUYỆT & NỐI THÊM
                      {/if}
                    </button>
                  {/if}
                {/if}
              </div>
              <p class="text-[12px] text-white/80 leading-relaxed tracking-tight">
                {#if ann.replacement_string}
                  <span class="text-white/40 font-mono italic text-[10px] truncate block max-w-full">
                    Sẽ chèn/thay: "{stripBoostTags(ann.replacement_string).slice(0, 100)}..."
                  </span>
                {/if}
                <span class="text-pink-200/90 mt-1 block text-[11px] font-bold">{ann.message || ''}</span>
              </p>
            </div>
          {/each}
        </div>
      {:else}
        <!-- Static Status (no patches yet) -->
        <div class="px-3 py-4 bg-pink-500/[0.03] flex flex-col gap-3">
           <p class="text-[9px] text-white/50 leading-relaxed">
              Hệ thống sẵn sàng phẫu thuật nội dung. Nhấn <span class="text-pink-400 font-bold">AI BOOSTER</span> để bắt đầu.
           </p>
           <div class="flex items-center gap-2 mt-1">
              <div class="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                 <div class="h-full bg-pink-500 {isBoosting ? 'animate-pulse' : ''}" style="width: {isBoosting ? '100%' : '0%'}"></div>
              </div>
              <span class="text-[8px] font-bold text-pink-400/60 tracking-tighter">{isBoosting ? 'Operating' : 'System Ready'}</span>
           </div>
        </div>
      {/if}

      <!-- ═══ JAPAN CLINICAL EVIDENCE SECTION ═══ -->
      {#if clinicalSources && clinicalSources.length > 0 && !isBoosting}
        <div class="mt-2 border-t border-white/5">
          <!-- Header -->
          <div class="px-3 py-2 flex items-center gap-2 bg-sky-500/5">
            <div class="w-1.5 h-1.5 rounded-full bg-sky-400 shadow-[0_0_6px_rgba(56,189,248,0.6)]"></div>
            <span class="text-[8px] font-black tracking-[0.25em] text-sky-400/80">NGHIÊN CỨU & LÂM SÀNG</span>
            <span class="ml-auto px-1.5 py-0.5 rounded-full bg-sky-500/10 border border-sky-500/20 text-[7px] font-black text-sky-400">
              🇯🇵 {clinicalSources.length} NGUỒN UY TÍN
            </span>
          </div>

          <!-- Source cards -->
          <div class="flex flex-col divide-y divide-white/[0.04]">
            {#each clinicalSources as src, si}
              <div class="px-3 py-3 flex flex-col gap-1.5 hover:bg-sky-500/[0.03] transition-colors">
                <!-- Domain badge + year -->
                <div class="flex items-center gap-2">
                  <span class="px-1.5 py-0.5 rounded text-[7px] font-black bg-sky-500/10 border border-sky-500/20 text-sky-300 tracking-tight">
                    {src.source_domain}
                  </span>
                  {#if src.year && src.year !== 'N/A'}
                    <span class="text-[8px] text-white/30 font-mono">{src.year}</span>
                  {/if}
                  <span class="ml-auto text-[7px] font-black text-white/15 tracking-widest">#{si + 1}</span>
                </div>

                <!-- Title (VI) -->
                <p class="text-[11px] font-bold text-sky-200/90 leading-snug">
                  {src.title_vi}
                </p>

                <!-- Snippet VI -->
                {#if src.snippet_vi}
                  <p class="text-[10px] text-white/55 leading-relaxed line-clamp-3">
                    {src.snippet_vi}
                  </p>
                {/if}

                <!-- Relevance tag -->
                {#if src.relevance}
                  <p class="text-[9px] text-sky-400/60 italic leading-relaxed">
                    🎯 {src.relevance}
                  </p>
                {/if}

                <!-- Footer: original title + verify link -->
                <div class="flex items-center gap-2 mt-0.5 pt-1.5 border-t border-white/[0.04]">
                  <span class="text-[8px] text-white/20 font-mono truncate flex-1" title={src.title_original}>
                    {src.title_original.slice(0, 55)}{src.title_original.length > 55 ? '…' : ''}
                  </span>
                  {#if src.source_url}
                    <a
                      href={src.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      class="flex-shrink-0 px-1.5 py-0.5 rounded text-[7px] font-black text-sky-400 bg-sky-500/10 border border-sky-500/20 hover:bg-sky-500/20 transition-colors tracking-tight"
                    >
                      Verify ↗
                    </a>
                  {/if}
                </div>
              </div>
            {/each}
          </div>

          <!-- Disclaimer -->
          <div class="px-3 py-2 bg-black/20">
            <p class="text-[7.5px] text-white/20 leading-relaxed">
              ⚠️ Tất cả nguồn trên đã được AI dịch thuần Việt từ bản gốc Nhật/Anh. Nhấn <span class="text-sky-400/60">Verify ↗</span> để đọc bản gốc và xác minh độc lập.
            </p>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>
