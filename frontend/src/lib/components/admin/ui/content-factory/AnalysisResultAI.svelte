<script lang="ts">
  import Sparkles from "lucide-svelte/icons/sparkles";
  import CheckCircle2 from "lucide-svelte/icons/check-circle-2";
  import type { AIInspectResult } from "$lib/state/types";

  interface Props {
    aiReadyResult: AIInspectResult;
    runAiAnalysis: () => void;
    isFixing?: string | null;
    handleInternalFix?: ((snippet: string, type: string, message: string) => void) | null;
    runBulkFix?: () => void;
    isBulkFixing?: boolean;
    streamingText?: string;
    streamingTarget?: string | null;
  }

  let { aiReadyResult, runAiAnalysis, isFixing = null, handleInternalFix = null, runBulkFix, isBulkFixing = false, streamingText = '', streamingTarget = null }: Props = $props();

  const aiPct = $derived(aiReadyResult.geo_score);
  const aiColor = $derived(aiPct >= 85 ? '#a855f7' : aiPct >= 65 ? '#d946ef' : '#ef4444');

  const severityOrder = { high: 0, warning: 1, info: 2 };
  const sortedAnnotations = $derived(
    [...(aiReadyResult.ai_annotations ?? [])].sort(
      (a, b) => (severityOrder[a.severity as keyof typeof severityOrder] ?? 2) - (severityOrder[b.severity as keyof typeof severityOrder] ?? 2)
    )
  );
  const highCount = $derived(sortedAnnotations.filter(a => a.severity === 'high').length);
  const warnCount = $derived(sortedAnnotations.filter(a => a.severity === 'warning').length);
  const infoCount = $derived(sortedAnnotations.filter(a => a.severity === 'info' || !a.severity).length);
</script>

<div class="flex flex-col">
  <!-- Header: Score + Summary -->
  <div class="relative pt-3 pb-1 overflow-hidden" style="border-color: {aiColor}20;">
    <div class="absolute -top-10 -right-10 w-32 h-32 blur-[50px] opacity-15" style="background:{aiColor}"></div>
    <div class="relative z-10 flex items-center justify-between gap-4 px-3">
      <div class="flex items-center gap-4">
        <!-- Score Donut -->
        <div class="relative w-16 h-16 shrink-0">
          <svg class="w-full h-full -rotate-90" viewBox="0 0 48 48">
            <circle cx="24" cy="24" r="20" fill="none" stroke="rgba(255,255,255,0.03)" stroke-width="3"/>
            <circle cx="24" cy="24" r="20" fill="none" stroke={aiColor} stroke-width="4"
              stroke-dasharray={2 * Math.PI * 20}
              stroke-dashoffset={2 * Math.PI * 20 * (1 - aiPct / 100)}
              stroke-linecap="round"
              style="transition:stroke-dashoffset 1.2s cubic-bezier(.4,0,.2,1)" />
          </svg>
          <div class="absolute inset-0 flex flex-col items-center justify-center">
            <span class="text-[13px] font-black tracking-tighter" style="color:{aiColor}">{aiPct}%</span>
            <span class="text-[6px] font-black opacity-30 uppercase tracking-[0.2em]">Edge</span>
          </div>
        </div>
        <div class="flex flex-col gap-1.5">
          <span class="text-sm font-black uppercase tracking-[0.1em]" style="color:{aiColor}">
            {aiPct >= 85 ? '✨ Viral Edge Elite' : aiPct >= 65 ? '⚡ AI-Ready Standard' : '🔴 Blacklist Risk'}
          </span>
          <div class="flex items-center gap-1.5 opacity-30">
            <span class="text-[9px] font-black uppercase tracking-[0.3em]">Protocol_GEO_Viral_V2.2</span>
          </div>
        </div>
      </div>

      <!-- Re-scan button -->
      <button onclick={() => runAiAnalysis(true)}
        class="mr-3 w-8 h-8 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-white/30 hover:text-white hover:bg-purple-500/20 hover:border-purple-500/40 transition-all"
        title="Chạy lại (Force Re-scan)">
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/></svg>
      </button>
    </div>

    <!-- Verdict -->
    <div class="px-4 py-4 bg-black/40 border-b border-white/5 shadow-inner">
      <div class="flex items-center gap-2 mb-3 opacity-30">
        <div class="w-1.5 h-1.5 rounded-full bg-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.6)]"></div>
        <span class="text-[10px] font-black uppercase tracking-[0.2em]">Neural_Viral_Verdict</span>
      </div>
      <p class="text-[13px] text-white/90 leading-[1.6] font-medium tracking-tight whitespace-pre-line">
        {aiReadyResult.summary.replace(/\*\*\*/g, '').trim()}
      </p>
    </div>

    <!-- Fix All AI-Ready Button -->
    {#if runBulkFix && sortedAnnotations.length > 0}
      <div class="px-3 py-2 border-b border-purple-500/10 bg-purple-500/[0.02]">
        <button 
          onclick={() => runBulkFix?.()}
          disabled={isBulkFixing}
          class="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-purple-500/10 border border-purple-500/30 hover:bg-purple-500 hover:text-white hover:border-purple-400 text-purple-400 text-[10px] font-black uppercase tracking-widest transition-all shadow-[0_0_20px_rgba(168,85,247,0.1)] active:scale-95 disabled:opacity-50"
        >
          {#if isBulkFixing}
            <div class="w-3 h-3 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
            ĐANG PHẪU THUẬT...
          {:else}
            <Sparkles size={12} class="animate-pulse" />
            PHẪU THUẬT CẤU TRÚC ({sortedAnnotations.length})
          {/if}
        </button>
      </div>
    {/if}

    <!-- Badge tổng lỗi -->
    {#if sortedAnnotations.length > 0}
      <div class="px-3 py-2 flex items-center gap-3 border-b border-white/5">
        <span class="text-[7px] font-black text-white/20 uppercase tracking-widest">Phát hiện</span>
        {#if highCount > 0}<span class="px-2 py-0.5 rounded-full text-[8px] font-black bg-red-500/15 text-red-400 border border-red-500/20">{highCount} HIGH</span>{/if}
        {#if warnCount > 0}<span class="px-2 py-0.5 rounded-full text-[8px] font-black bg-amber-500/15 text-amber-400 border border-amber-500/20">{warnCount} WARN</span>{/if}
        {#if infoCount > 0}<span class="px-2 py-0.5 rounded-full text-[8px] font-black bg-purple-500/15 text-purple-400 border border-purple-500/20">{infoCount} INFO</span>{/if}
      </div>
    {/if}
  </div>

  <!-- Annotation list -->
  {#if sortedAnnotations.length > 0}
    <div class="flex flex-col">
      {#each sortedAnnotations as ann}
        {#if ann.type === 'fixed-area'}
          <div class="px-3 py-2 border-b border-emerald-500/20 bg-emerald-500/[0.04] flex items-start gap-2">
            <CheckCircle2 size={10} class="text-emerald-400 mt-0.5 shrink-0" />
            <div class="min-w-0">
              <span class="text-[7px] font-black text-emerald-400 uppercase">✅ ĐÃ SỬA</span>
              <p class="text-[8px] text-emerald-200/60 leading-relaxed mt-0.5 truncate italic">"{ann.text}"</p>
            </div>
          </div>
        {:else}
          {@const annHex = ann.severity === 'high' ? '#ef4444' : ann.severity === 'warning' ? '#f59e0b' : '#a855f7'}
          {@const annLabel = ann.severity === 'high' ? '🔴 CRITICAL' : ann.severity === 'warning' ? '⚠️ WARNING' : '💡 INFO'}
          <div class="px-3 py-3 border-b bg-white/[0.01] flex flex-col gap-1.5 transition-all hover:bg-white/[0.02]" style="border-color: {annHex}15">
            <div class="flex items-start justify-between gap-2">
              <span class="text-[7px] font-black px-1 py-0.5 rounded uppercase" style="background:{annHex}20; color:{annHex}">{annLabel} — {ann.type?.replace(/_/g,' ').toUpperCase()}</span>
              {#if handleInternalFix}
                <button
                  onclick={() => handleInternalFix!(ann.text, ann.type || 'ai', ann.message || '')}
                  disabled={!!isFixing}
                  class="shrink-0 flex items-center gap-1 px-2 py-0.5 rounded border border-white/10 hover:bg-purple-500/20 hover:border-purple-500/40 hover:text-purple-300 text-[7px] font-black uppercase transition-all disabled:opacity-40 cursor-pointer">
                  {#if streamingTarget === ann.text}
                    <span class="text-[8px] text-white/80 font-mono leading-relaxed max-w-[160px] truncate">{streamingText}<span class="inline-block w-1 h-2.5 bg-purple-400 animate-pulse ml-0.5 -mb-0.5"></span></span>
                  {:else if isFixing === ann.text}
                    <span class="w-2 h-2 border border-white/30 border-t-purple-400 rounded-full animate-spin"></span> ĐANG PHẪU THUẬT...
                  {:else}
                    <Sparkles size={8} class="text-purple-400" /> PHẪU THUẬT
                  {/if}
                </button>
              {/if}
            </div>
            <p class="text-[12px] text-white/80 leading-relaxed tracking-tight">
              <span class="text-white/40 font-mono italic">"{ann.text}"</span> <br/>
              <span class="text-purple-200/90">{ann.message}</span>
            </p>
          </div>
        {/if}
      {/each}
    </div>
  {/if}
</div>
