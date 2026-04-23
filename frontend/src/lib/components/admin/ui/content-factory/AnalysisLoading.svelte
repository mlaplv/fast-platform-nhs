<script lang="ts">
  import ShieldCheck from "lucide-svelte/icons/shield-check";
  import BarChart2 from "lucide-svelte/icons/bar-chart-2";
  import Brain from "lucide-svelte/icons/brain";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import { PHASES } from "$lib/state/xohiAnalysisPhases.svelte";

  interface Props {
    tab: 'copyright' | 'seo' | 'ai' | 'enrich' | null;
    phaseIndex: number;
    phaseProgress: number;
  }

  let { tab, phaseIndex, phaseProgress }: Props = $props();

  const accentMap = {
    copyright: '#f97316',
    seo: '#3b82f6',
    enrich: '#ec4899',
    ai: '#a855f7'
  };

  const accentBgMap = {
    copyright: 'from-orange-950/80',
    seo: 'from-blue-950/80',
    enrich: 'from-pink-950/80',
    ai: 'from-purple-950/80'
  };

  const accentBorderMap = {
    copyright: 'border-orange-500/20',
    seo: 'border-blue-500/20',
    enrich: 'border-pink-500/20',
    ai: 'border-purple-500/20'
  };

  const labelMap = {
    copyright: 'Plagiarism Cop™',
    seo: 'SEO Strategist™',
    enrich: 'AI Booster™',
    ai: 'Viral Edge™'
  };

  const estimateMap = {
    copyright: 'Kết nối Google Search API + Gemini...',
    seo: 'So sánh Top 5 đối thủ real-time...',
    enrich: 'Injecting Real-world data & Expert Quotes...',
    ai: '8 tiêu chí Viral Edge đang chạy...'
  };

  const accent = $derived(accentMap[tab || 'copyright']);
  const accentBg = $derived(accentBgMap[tab || 'copyright']);
  const accentBorder = $derived(accentBorderMap[tab || 'copyright']);
  const phases = $derived(PHASES[tab || 'copyright'] || []);
</script>

<div class="relative overflow-hidden border {accentBorder} bg-gradient-to-br {accentBg} via-slate-950/90 to-slate-900/90 p-4 live-scanner">
  <div class="scan-line" style="--accent: {accent}"></div>
  <div class="flex items-center gap-3 mb-4">
    <div class="relative w-8 h-8">
      <div class="absolute inset-0 animate-ping opacity-20" style="background:{accent}"></div>
      <div class="relative w-8 h-8 flex items-center justify-center" style="background:{accent}20; border:1px solid {accent}30">
        {#if tab === 'copyright'}<ShieldCheck size={14} style="color:{accent}" />
        {:else if tab === 'seo'}<BarChart2 size={14} style="color:{accent}" />
        {:else if tab === 'enrich'}<Brain size={14} style="color:{accent}" />
        {:else}<Sparkles size={14} style="color:{accent}" />{/if}
      </div>
    </div>
    <div>
      <div class="text-[10px] font-black uppercase tracking-[0.15em]" style="color:{accent}">{labelMap[tab || 'copyright']}</div>
      <div class="text-[8px] text-white/30">AI đang xử lý...</div>
    </div>
    <div class="ml-auto flex items-center gap-1">
      <div class="w-1.5 h-1.5 rounded-full animate-pulse" style="background:{accent}"></div>
      <div class="w-1 h-1 rounded-full animate-pulse" style="background:{accent}; animation-delay:0.3s"></div>
      <div class="w-1.5 h-1.5 rounded-full animate-pulse" style="background:{accent}; animation-delay:0.6s"></div>
    </div>
  </div>

  <div class="flex flex-col gap-1.5">
    {#each phases as phase, i}
      {@const isDone = i < phaseIndex}
      {@const isActive = i === phaseIndex}
      {@const isPending = i > phaseIndex}
      <div class="flex items-center gap-2.5 transition-all duration-300 {isPending ? 'opacity-25' : 'opacity-100'}">
        <div class="w-5 h-5 rounded-full shrink-0 flex items-center justify-center text-[10px] transition-all duration-300 {isDone ? 'shadow-glow' : isActive ? 'ring-pulse' : ''}"
          style="{isDone ? `background:${accent}30; border:1px solid ${accent}60` : isActive ? `background:${accent}15; border:1px solid ${accent}40` : 'background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08)'}">
          {#if isDone} <span style="color:{accent}">✓</span>
          {:else if isActive} <span class="animate-spin inline-block text-[8px]" style="color:{accent}">⟳</span>
          {:else} <span class="text-white/20">{i + 1}</span> {/if}
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between gap-2 mb-1">
            <span class="text-[9px] font-medium {isDone ? 'text-white/60' : isActive ? 'text-white/90' : 'text-white/25'}">{phase.icon} {phase.label}</span>
            {#if isDone} <span class="text-[8px] font-black shrink-0" style="color:{accent}">100%</span>
            {:else if isActive} <span class="text-[8px] font-black shrink-0" style="color:{accent}">{Math.round(phaseProgress)}%</span> {/if}
          </div>
          <div class="h-px rounded-full bg-white/5 overflow-hidden">
            {#if isDone} <div class="h-full w-full rounded-full" style="background:{accent}60"></div>
            {:else if isActive} <div class="h-full rounded-full transition-all duration-100 progress-shimmer" style="width:{phaseProgress}%; background:linear-gradient(90deg, {accent}80, {accent})"></div> {/if}
          </div>
        </div>
      </div>
    {/each}
  </div>

  <div class="mt-3 pt-2 border-t border-white/5 flex items-center justify-between">
    <span class="text-[8px] text-white/20 italic">{estimateMap[tab || 'copyright']}</span>
    <span class="text-[8px] font-black animate-pulse" style="color:{accent}">LIVE</span>
  </div>
</div>

<style>
  .live-scanner { position: relative; backdrop-filter: blur(16px); }
  .scan-line { position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, var(--accent), transparent); animation: scan 2.5s linear infinite; opacity: 0.6; }
  @keyframes scan { 0% { top: 0%; opacity: 0; } 5% { opacity: 0.6; } 95% { opacity: 0.6; } 100% { top: 100%; opacity: 0; } }
  .progress-shimmer { position: relative; overflow: hidden; }
  .progress-shimmer::after { content: ''; position: absolute; top: 0; left: -100%; bottom: 0; width: 60%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent); animation: shimmer 1.2s infinite; }
  @keyframes shimmer { 0% { left: -100%; } 100% { left: 200%; } }
  .shadow-glow { box-shadow: 0 0 6px currentColor; }
</style>
