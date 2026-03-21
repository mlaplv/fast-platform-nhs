<script lang="ts">
  import type { AIInspectResult } from "$lib/state/types";

  interface Props {
    aiReadyResult: AIInspectResult;
    runAiAnalysis: () => void;
  }

  let { aiReadyResult, runAiAnalysis }: Props = $props();

  const aiPct = $derived(aiReadyResult.geo_score);
  const aiColor = $derived(aiPct >= 85 ? '#a855f7' : aiPct >= 65 ? '#d946ef' : '#ef4444');
</script>

<div class="px-3 py-2 rounded-xl border flex items-center gap-4" style="background: {aiColor}08; border-color: {aiColor}20;">
  <div class="relative w-12 h-12 shrink-0">
    <svg class="w-full h-full -rotate-90" viewBox="0 0 48 48">
      <circle cx="24" cy="24" r="19" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="4"/>
      <circle cx="24" cy="24" r="19" fill="none" stroke={aiColor} stroke-width="4" stroke-dasharray={2 * Math.PI * 19} stroke-dashoffset={2 * Math.PI * 19 * (1 - aiPct/100)} stroke-linecap="round" style="transition:stroke-dashoffset 1.2s cubic-bezier(.4,0,.2,1)" />
    </svg>
    <span class="absolute inset-0 flex items-center justify-center text-[9px] font-black" style="color:{aiColor}">{aiPct}%</span>
  </div>
  <div class="flex-1 min-w-0">
    <div class="flex items-center gap-2 flex-wrap">
      <span class="text-[9px] font-black uppercase tracking-wider" style="color:{aiColor}">✨ Viral Edge™</span>
      <button onclick={runAiAnalysis} class="text-[8px] text-white/20 hover:text-purple-400 transition-colors" title="Chạy lại">↻</button>
    </div>
    <p class="text-[9px] text-white/50 leading-relaxed line-clamp-2">{aiReadyResult.summary}</p>
  </div>
</div>
