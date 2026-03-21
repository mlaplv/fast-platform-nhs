<script lang="ts">
  import type { SEOResult } from "$lib/state/types";

  interface Props {
    seoResult: SEOResult;
    runSeoAnalysis: () => void;
  }

  let { seoResult, runSeoAnalysis }: Props = $props();

  const gradeColor = $derived(seoResult.grade === 'A' ? '#10b981' : seoResult.grade === 'B' ? '#3b82f6' : seoResult.grade === 'C' ? '#f59e0b' : '#ef4444');
</script>

<div class="px-3 py-2 rounded-xl border flex flex-col gap-2" style="background: {gradeColor}08; border-color: {gradeColor}20;">
  <div class="flex items-center gap-3">
    <div class="w-9 h-9 rounded-lg shrink-0 flex items-center justify-center font-black text-lg" style="background:{gradeColor}15; color:{gradeColor}">{seoResult.grade}</div>
    <div class="flex-1 min-w-0">
      <div class="flex items-center gap-2">
        <span class="text-[9px] font-black uppercase" style="color:{gradeColor}">📊 SEO Score — {seoResult.total_score}/100</span>
        <button onclick={runSeoAnalysis} class="text-[8px] text-white/20 hover:text-blue-400 transition-colors" title="Chạy lại">↻</button>
      </div>
      <p class="text-[9px] text-white/50 leading-relaxed line-clamp-2">{seoResult.summary}</p>
    </div>
  </div>
  {#if seoResult.signals?.length > 0}
    <div class="grid grid-cols-2 gap-1">
      {#each seoResult.signals.slice(0, 4) as signal}
        {@const c = signal.score >= 80 ? '#10b981' : signal.score >= 60 ? '#3b82f6' : signal.score >= 40 ? '#f59e0b' : '#ef4444'}
        <div class="flex items-center gap-1.5">
          <span class="text-[7px] text-white/30 uppercase truncate w-16">{signal.label.replace(/_/g,' ')}</span>
          <div class="flex-1 h-0.5 rounded-full bg-white/5 overflow-hidden"><div class="h-full rounded-full" style="width:{signal.score}%;background:{c}"></div></div>
          <span class="text-[7px] font-black" style="color:{c}">{signal.score}</span>
        </div>
      {/each}
    </div>
  {/if}
  {#if seoResult.quick_wins?.length > 0} <p class="text-[8px] text-blue-300/50">⚡ {seoResult.quick_wins[0]}</p> {/if}
</div>
