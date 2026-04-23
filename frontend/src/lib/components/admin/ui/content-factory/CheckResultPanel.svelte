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
    runSeoAnalysis, runAiAnalysis, onfix = null
  }: {
    activeTab: 'copyright' | 'seo' | 'ai' | 'enrich' | null;
    copyrightResult: CopyrightResult | null; isCopyrightLoading: boolean;
    seoResult: SEOResult | null; isSeoLoading: boolean;
    aiReadyResult: AIInspectResult | null; isAiLoading: boolean;
    isBoosting?: boolean; runCopyrightCheck: () => void;
    runSeoAnalysis: () => void; runAiAnalysis: () => void;
    onfix?: ((snippet: string, type: string, message: string) => Promise<string | null>) | null;
  } = $props();

  let isFixing = $state<string | null>(null);
  const phaseCtrl = createPhaseController();

  // CNS V85.22: Guard phase engine - only restart when the active tab's loading state changes.
  // Prevents animation reset on every prop change.
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

  const isLoading = $derived((activeTab === 'copyright' && isCopyrightLoading) || (activeTab === 'seo' && isSeoLoading) || (activeTab === 'ai' && isAiLoading) || (activeTab === 'enrich' && isBoosting));
</script>

<div class="shrink-0 flex flex-col">
  {#if isLoading}
    <AnalysisLoading tab={activeTab} phaseIndex={phaseCtrl.phaseIndex} phaseProgress={phaseCtrl.phaseProgress} />
  {:else if activeTab === 'copyright'}
    {#if copyrightResult}
      <AnalysisResultCopyright {copyrightResult} {isFixing} {runCopyrightCheck} {handleInternalFix} />
    {:else}
      <div class="px-3 py-3 rounded-xl border border-white/5 bg-white/[0.02] text-center text-[9px] text-white/30">Nhấn <span class="text-orange-400/70 font-bold">COPYRIGHT</span> để phân tích đạo văn.</div>
    {/if}
  {:else if activeTab === 'seo'}
    {#if seoResult}
      <AnalysisResultSEO {seoResult} {runSeoAnalysis} {isFixing} handleInternalFix={onfix ? handleInternalFix : null} />
    {:else}
      <div class="px-3 py-3 rounded-xl border border-white/5 bg-white/[0.02] text-center text-[9px] text-white/30">Nhấn <span class="text-blue-400/70 font-bold">SEO</span> để chấm điểm 7 tín hiệu SEO.</div>
    {/if}
  {:else if activeTab === 'ai'}
    {#if aiReadyResult}
      <AnalysisResultAI {aiReadyResult} {runAiAnalysis} {isFixing} handleInternalFix={onfix ? handleInternalFix : null} />
    {:else}
      <div class="px-3 py-3 rounded-xl border border-white/5 bg-white/[0.02] text-center text-[9px] text-white/30">Nhấn <span class="text-purple-400/70 font-bold">AI MOD</span> để kiểm tra Viral Edge Score.</div>
    {/if}
  {:else if activeTab === 'enrich'}
    <div class="px-3 py-4 rounded-2xl border border-pink-500/10 bg-pink-500/[0.03] flex flex-col gap-3">
       <div class="flex items-center gap-2">
          <div class="p-1.5 rounded-lg bg-pink-500/10 text-pink-400">
             <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-brain"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .52 8.588A5.002 5.002 0 0 0 12 22a5 5 0 0 0 8-4.017s1.398-.24 2.128-1.57A4 4 0 0 0 21 11a4 4 0 0 0-3-3.95V7a3 3 0 0 0-6-2Z"/><path d="M12 12h.01"/><path d="M9 12h.01"/><path d="M15 12h.01"/></svg>
          </div>
          <span class="text-[11px] font-black uppercase tracking-widest text-pink-400">AI Booster™ Status</span>
       </div>
       <p class="text-[9px] text-white/50 leading-relaxed">
          Hệ thống đang tăng cường nội dung bằng dữ liệu thực tế. Các thay đổi được đánh dấu màu <span class="text-pink-400 font-bold">Hồng Neon</span> trong văn bản.
       </p>
       <div class="flex items-center gap-2 mt-1">
          <div class="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
             <div class="h-full bg-pink-500 animate-pulse" style="width: 100%"></div>
          </div>
          <span class="text-[8px] font-bold text-pink-400/60">OPTIMIZED</span>
       </div>
    </div>
  {/if}
</div>
