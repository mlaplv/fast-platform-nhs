<script lang="ts">
  import { onDestroy } from "svelte";
  import type { CopyrightResult, SEOResult, AIInspectResult } from "$lib/state/types";
  import { createPhaseController } from "$lib/state/xohiAnalysisPhases.svelte";
  import AnalysisLoading from "./AnalysisLoading.svelte";
  import AnalysisResultCopyright from "./AnalysisResultCopyright.svelte";
  import AnalysisResultSEO from "./AnalysisResultSEO.svelte";
  import AnalysisResultAI from "./AnalysisResultAI.svelte";

  let {
    activeTab, copyrightResult, isCopyrightLoading, seoResult, isSeoLoading,
    aiReadyResult, isAiLoading, isBoosting = false, runCopyrightCheck,
    runSeoAnalysis, runAiAnalysis, onfix = null,
    streamingText = "", streamingTarget = null,
    bulkFixLogs = [],
    runBulkFix,
    isBulkFixing = false,
  }: {
    activeTab: 'copyright' | 'seo' | 'ai' | 'enrich' | null;
    copyrightResult: CopyrightResult | null; isCopyrightLoading: boolean;
    seoResult: SEOResult | null; isSeoLoading: boolean;
    aiReadyResult: AIInspectResult | null; isAiLoading: boolean;
    isBoosting?: boolean; runCopyrightCheck: () => void;
    runSeoAnalysis: () => void; runAiAnalysis: () => void;
    onfix?: ((snippet: string, type: string, message: string) => Promise<string | null>) | null;
    streamingText?: string;
    streamingTarget?: string | null;
    bulkFixLogs?: string[];
    runBulkFix?: () => void;
    isBulkFixing?: boolean;
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
    else phaseCtrl.clearTimers();
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
    (activeTab === 'enrich' && isBoosting)
  );

  // ── CNS V87.0: Dashboard — chỉ hiển thị khi ≥1 kết quả có dữ liệu ────────
  const hasAnyResult = $derived(!!(copyrightResult || seoResult || aiReadyResult));

  // Gom tất cả annotations từ 3 nguồn
  const allAnnotations = $derived([
    ...(copyrightResult?.annotations ?? []),
    ...(seoResult?.seo_annotations ?? []),
    ...(aiReadyResult?.ai_annotations ?? []),
  ].filter(a => a.type !== 'fixed-area'));

  const totalIssues = $derived(allAnnotations.length);
  const highCount   = $derived(allAnnotations.filter(a => a.severity === 'high').length);
  const warnCount   = $derived(allAnnotations.filter(a =>
    a.severity === 'medium' || a.severity === 'warning'
  ).length);
  const lowCount    = $derived(allAnnotations.filter(a =>
    a.severity === 'low' || a.severity === 'info' || !a.severity
  ).length);

  // Health Score: trung bình các điểm hiện có
  const healthScore = $derived.by(() => {
    const scores: number[] = [];
    if (copyrightResult) scores.push(Math.round((copyrightResult.uniqueness_score ?? 0) * 100));
    if (seoResult) scores.push(seoResult.total_score ?? 0);
    if (aiReadyResult) scores.push(aiReadyResult.geo_score ?? 0);
    if (scores.length === 0) return null;
    return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
  });

  const healthColor = $derived(
    healthScore === null ? '#6b7280' :
    healthScore >= 80 ? '#10b981' :
    healthScore >= 60 ? '#3b82f6' :
    healthScore >= 40 ? '#f59e0b' : '#ef4444'
  );
</script>

<div class="shrink-0 flex flex-col">

  <!-- ── Dashboard: chỉ hiển thị khi ≥1 kết quả ── -->
  {#if hasAnyResult}
    <div class="px-3 py-2.5 border-b border-white/5 bg-black/20">
      <div class="flex items-center gap-3">
        <!-- Health Ring -->
        <div class="relative w-11 h-11 shrink-0">
          <svg class="w-full h-full -rotate-90" viewBox="0 0 40 40">
            <circle cx="20" cy="20" r="16" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="3"/>
            <circle cx="20" cy="20" r="16" fill="none"
              stroke={healthColor} stroke-width="3"
              stroke-dasharray={2 * Math.PI * 16}
              stroke-dashoffset={healthScore !== null ? 2 * Math.PI * 16 * (1 - healthScore / 100) : 2 * Math.PI * 16}
              stroke-linecap="round"
              style="transition: stroke-dashoffset 1s ease"/>
          </svg>
          <div class="absolute inset-0 flex items-center justify-center">
            <span class="text-[9px] font-black" style="color:{healthColor}">
              {healthScore !== null ? healthScore : '—'}
            </span>
          </div>
        </div>

        <!-- Metrics -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-1.5 mb-1.5">
            <span class="text-[7px] font-black uppercase tracking-widest text-white/20">Health Score</span>
            {#if totalIssues > 0}
              <span class="ml-auto text-[7px] font-black text-white/20">{totalIssues} vấn đề</span>
            {/if}
          </div>
          <div class="flex items-center gap-1.5 flex-wrap">
            {#if highCount > 0}
              <span class="px-1.5 py-0.5 rounded text-[7px] font-black bg-red-500/15 text-red-400 border border-red-500/20">
                🔴 {highCount} HIGH
              </span>
            {/if}
            {#if warnCount > 0}
              <span class="px-1.5 py-0.5 rounded text-[7px] font-black bg-amber-500/15 text-amber-400 border border-amber-500/20">
                ⚠️ {warnCount} WARN
              </span>
            {/if}
            {#if lowCount > 0}
              <span class="px-1.5 py-0.5 rounded text-[7px] font-black bg-blue-500/15 text-blue-400 border border-blue-500/20">
                💡 {lowCount} INFO
              </span>
            {/if}
            {#if totalIssues === 0}
              <span class="px-1.5 py-0.5 rounded text-[7px] font-black bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
                ✅ Không có lỗi
              </span>
            {/if}
          </div>
        </div>

        <!-- Mini score cards -->
        <div class="flex items-center gap-1.5 shrink-0">
          {#if copyrightResult}
            {@const s = Math.round((copyrightResult.uniqueness_score ?? 0) * 100)}
            {@const c = s >= 70 ? '#10b981' : s >= 50 ? '#f59e0b' : '#ef4444'}
            <div class="flex flex-col items-center gap-0.5">
              <span class="text-[8px] font-black" style="color:{c}">{s}%</span>
              <span class="text-[6px] text-white/20 uppercase">©</span>
            </div>
          {/if}
          {#if seoResult}
            {@const s = seoResult.total_score}
            {@const c = s >= 70 ? '#3b82f6' : s >= 50 ? '#f59e0b' : '#ef4444'}
            <div class="flex flex-col items-center gap-0.5">
              <span class="text-[8px] font-black" style="color:{c}">{s}</span>
              <span class="text-[6px] text-white/20 uppercase">SEO</span>
            </div>
          {/if}
          {#if aiReadyResult}
            {@const s = aiReadyResult.geo_score}
            {@const c = s >= 80 ? '#a855f7' : s >= 60 ? '#d946ef' : '#ef4444'}
            <div class="flex flex-col items-center gap-0.5">
              <span class="text-[8px] font-black" style="color:{c}">{s}%</span>
              <span class="text-[6px] text-white/20 uppercase">AI</span>
            </div>
          {/if}
        </div>
      </div>
    </div>
  {/if}

  <!-- ── Panel Content ── -->
  {#if isLoading}
    <AnalysisLoading tab={activeTab} phaseIndex={phaseCtrl.phaseIndex} phaseProgress={phaseCtrl.phaseProgress} logs={bulkFixLogs} />
  {:else if activeTab === 'copyright'}
    {#if copyrightResult}
      <AnalysisResultCopyright
        {copyrightResult} {isFixing} {runCopyrightCheck} {handleInternalFix}
        {streamingText} {streamingTarget} {runBulkFix} {isBulkFixing}
      />
    {:else}
      <div class="px-3 py-3 rounded-xl border border-white/5 bg-white/[0.02] text-center text-[9px] text-white/30">Nhấn <span class="text-orange-400/70 font-bold">COPYRIGHT</span> để phân tích đạo văn.</div>
    {/if}
  {:else if activeTab === 'seo'}
    {#if seoResult}
      <AnalysisResultSEO
        {seoResult} {runSeoAnalysis} {isFixing}
        handleInternalFix={onfix ? handleInternalFix : null}
        {streamingText} {streamingTarget} {runBulkFix} {isBulkFixing}
      />
    {:else}
      <div class="px-3 py-3 rounded-xl border border-white/5 bg-white/[0.02] text-center text-[9px] text-white/30">Nhấn <span class="text-blue-400/70 font-bold">SEO</span> để chấm điểm 7 tín hiệu SEO.</div>
    {/if}
  {:else if activeTab === 'ai'}
    {#if aiReadyResult}
      <AnalysisResultAI
        {aiReadyResult} {runAiAnalysis} {isFixing}
        handleInternalFix={onfix ? handleInternalFix : null}
        {streamingText} {streamingTarget} {runBulkFix} {isBulkFixing}
      />
    {:else}
      <div class="px-3 py-3 rounded-xl border border-white/5 bg-white/[0.02] text-center text-[9px] text-white/30">Nhấn <span class="text-purple-400/70 font-bold">AI MOD</span> để kiểm tra Viral Edge Score.</div>
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
             <div class="h-full bg-pink-500 animate-pulse" style="width: 100%"></div>
          </div>
          <span class="text-[8px] font-bold text-pink-400/60">OPERATING</span>
       </div>
    </div>
  {/if}
</div>
