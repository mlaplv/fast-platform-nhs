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

  $effect(() => {
    if (activeTab === 'enrich' && isBoosting) phaseCtrl.startPhaseEngine('enrich');
    else if (isCopyrightLoading) phaseCtrl.startPhaseEngine('copyright');
    else if (isSeoLoading) phaseCtrl.startPhaseEngine('seo');
    else if (isAiLoading) phaseCtrl.startPhaseEngine('ai');
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

<div class="shrink-0 flex flex-col gap-2">
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
      <AnalysisResultSEO {seoResult} {runSeoAnalysis} />
    {:else}
      <div class="px-3 py-3 rounded-xl border border-white/5 bg-white/[0.02] text-center text-[9px] text-white/30">Nhấn <span class="text-blue-400/70 font-bold">SEO</span> để chấm điểm 7 tín hiệu SEO.</div>
    {/if}
  {:else if activeTab === 'ai'}
    {#if aiReadyResult}
      <AnalysisResultAI {aiReadyResult} {runAiAnalysis} />
    {:else}
      <div class="px-3 py-3 rounded-xl border border-white/5 bg-white/[0.02] text-center text-[9px] text-white/30">Nhấn <span class="text-purple-400/70 font-bold">AI MOD</span> để kiểm tra Viral Edge Score.</div>
    {/if}
  {/if}
</div>
