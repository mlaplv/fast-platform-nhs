<script lang="ts">
  import Sparkles from "lucide-svelte/icons/sparkles";
  import CheckCircle2 from "lucide-svelte/icons/check-circle-2";
  import type { CopyrightResult } from "$lib/state/types";

  interface Props {
    copyrightResult: CopyrightResult;
    isFixing: string | null;
    runCopyrightCheck: () => void;
    handleInternalFix: (snippet: string, type: string, message: string) => void;
  }

  let { copyrightResult, isFixing, runCopyrightCheck, handleInternalFix }: Props = $props();

  const pct = $derived(Math.round(copyrightResult.uniqueness_score * 100));
  const riskColor = $derived(copyrightResult.risk_level === 'LOW' ? '#10b981' : copyrightResult.risk_level === 'MEDIUM' ? '#f59e0b' : '#ef4444');
</script>

<div class="flex flex-col">
  <!-- Supreme System Header: Score & Risk -->
  <div class="relative pt-3 pb-1 bg-white/[0.01] overflow-hidden" style="border-color: {riskColor}20;">
    <!-- Background Glow -->
    <div class="absolute -top-10 -left-10 w-32 h-32 blur-[40px] opacity-20" style="background: {riskColor}"></div>
    
    <div class="relative z-10 flex items-center justify-between gap-4 px-3">
      <div class="flex items-center gap-4">
        <!-- Rank Circle -->
        <div class="relative w-16 h-16 shrink-0 glow-effect">
          <svg class="w-full h-full -rotate-90" viewBox="0 0 48 48">
            <circle cx="24" cy="24" r="20" fill="none" stroke="rgba(255,255,255,0.03)" stroke-width="3"/>
            <circle cx="24" cy="24" r="20" fill="none" stroke={riskColor} stroke-width="4" stroke-dasharray={2 * Math.PI * 20} stroke-dashoffset={2 * Math.PI * 20 * (1 - copyrightResult.uniqueness_score)} stroke-linecap="round" class="transition-all duration-1000 ease-out" />
          </svg>
          <div class="absolute inset-0 flex flex-col items-center justify-center">
            <span class="text-[14px] font-black tracking-tighter" style="color:{riskColor}">{pct}%</span>
            <span class="text-[7px] font-bold opacity-30 uppercase tracking-tighter">Rank</span>
          </div>
        </div>

        <!-- Risk Level & Protocol -->
        <div class="flex flex-col gap-1 px-3">
          <div class="flex items-center gap-2">
            <span class="text-[11px] font-black uppercase tracking-[0.1em]" style="color:{riskColor}">
              {copyrightResult.risk_level === 'LOW' ? 'PROTECTED ✅' : copyrightResult.risk_level === 'MEDIUM' ? 'STRICT CAUTION ⚠️' : 'CRITICAL RISK 🚨'}
            </span>
          </div>
          <div class="flex items-center gap-1.5 opacity-40">
            <span class="text-[8px] font-mono uppercase tracking-widest">Protocol_XoHi_2026</span>
          </div>
        </div>
      </div>

      <button onclick={() => runCopyrightCheck(true)} class="mr-3 w-8 h-8 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-white/30 hover:text-white hover:bg-white/10 transition-all">
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/></svg>
      </button>
    </div>

    <!-- Verdict (Full Width) -->
    <div class="px-3 py-3 bg-black/20 border-b border-white/5">
      <div class="flex items-center gap-2 mb-2 opacity-30">
        <div class="w-1 h-1 rounded-full bg-white"></div>
        <span class="text-[7px] font-black uppercase tracking-widest">Neural_Verdict_Report</span>
      </div>
      <p class="text-[10px] text-white/80 leading-relaxed font-medium whitespace-pre-wrap">{copyrightResult.verdict}</p>
    </div>
  </div>

  <!-- Detailed Annotations List -->
  {#if copyrightResult.annotations?.length > 0}
    <div class="flex flex-col">
      {#each copyrightResult.annotations as ann}
        {#if ann.type === 'fixed-area'}
          <!-- SUCCESS ROW: AI-repaired segment -->
          <div class="px-3 py-2 border-b border-emerald-500/20 bg-emerald-500/[0.04] flex items-start gap-2">
            <CheckCircle2 size={10} class="text-emerald-400 mt-0.5 shrink-0" />
            <div class="min-w-0">
              <span class="text-[7px] font-black text-emerald-400 uppercase">✅ ĐÃ SỬA</span>
              <p class="text-[8px] text-emerald-200/60 leading-relaxed mt-0.5 truncate italic">"{ann.text}"</p>
            </div>
          </div>
        {:else}
          {@const isInternal = ann.type === 'internal-dedup'}
          {@const annHex = ann.severity === 'high' ? '#ef4444' : ann.severity === 'medium' ? '#f59e0b' : '#eab308'}
          <div class="px-3 py-3 border-b bg-white/[0.01] flex flex-col gap-1.5 transition-all hover:bg-white/[0.02]" style="border-color: {annHex}15">
            <div class="flex items-start justify-between gap-2">
              <span class="text-[7px] font-black px-1 py-0.5 rounded uppercase" style="background: {annHex}20; color: {annHex}">{isInternal ? '🔁 TRÙNG LẶP NỘI BỘ' : `🚨 COPYRIGHT ${ann.severity?.toUpperCase()}`}</span>
              <button onclick={() => handleInternalFix(ann.text, ann.type || 'copyright', ann.reason || 'Cần kiểm tra COPYRIGHT')} disabled={!!isFixing} class="shrink-0 flex items-center gap-1 px-2 py-0.5 rounded border border-white/10 hover:bg-white/10 text-[7px] font-black uppercase transition-all disabled:opacity-40">
                {#if isFixing === ann.text} <span class="w-2 h-2 border border-white/30 border-t-white rounded-full animate-spin"></span> FIXING...
                {:else} <Sparkles size={8} class="text-yellow-400" /> SỬA LỖI {/if}
              </button>
            </div>
            <p class="text-[8px] text-white/70 leading-relaxed"><span class="text-white/30 italic">"{ann.text}"</span> — {ann.reason}</p>
            {#if ann.source_url && !isInternal}<a href={ann.source_url} target="_blank" class="text-[7px] text-blue-400/60 hover:text-blue-400 underline truncate">🔗 Nguồn: {ann.source_url}</a>{/if}
          </div>
        {/if}
      {/each}
    </div>
  {/if}
</div>
