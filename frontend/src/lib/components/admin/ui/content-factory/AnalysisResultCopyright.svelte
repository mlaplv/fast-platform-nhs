<script lang="ts">
  import { Sparkles, CheckCircle2 } from "lucide-svelte";
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

<div class="px-3 py-2 rounded-xl border flex items-center gap-4" style="background: {riskColor}08; border-color: {riskColor}20;">
  <div class="relative w-12 h-12 shrink-0">
    <svg class="w-full h-full -rotate-90" viewBox="0 0 48 48">
      <circle cx="24" cy="24" r="19" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="4"/>
      <circle cx="24" cy="24" r="19" fill="none" stroke={riskColor} stroke-width="4" stroke-dasharray={2 * Math.PI * 19} stroke-dashoffset={2 * Math.PI * 19 * (1 - copyrightResult.uniqueness_score)} stroke-linecap="round" style="transition:stroke-dashoffset 1.2s cubic-bezier(.4,0,.2,1)" />
    </svg>
    <span class="absolute inset-0 flex items-center justify-center text-[9px] font-black" style="color:{riskColor}">{pct}%</span>
  </div>
  <div class="flex-1 min-w-0">
    <div class="flex items-center gap-2 flex-wrap">
      <span class="text-[9px] font-black uppercase" style="color:{riskColor}">🔍 COPYRIGHT — {copyrightResult.risk_level === 'LOW' ? 'Rủi ro thấp ✅' : copyrightResult.risk_level === 'MEDIUM' ? 'Cần cải thiện ⚠️' : 'Rủi ro cao 🚨'}</span>
      <button onclick={runCopyrightCheck} class="text-[8px] text-white/20 hover:text-orange-400 transition-colors" title="Chạy lại">↻</button>
    </div>
    <p class="text-[9px] text-white/50 leading-relaxed truncate">{copyrightResult.verdict}</p>
    {#if copyrightResult.annotations?.length > 0}
      <div class="mt-2 flex flex-col gap-1.5">
        {#each copyrightResult.annotations as ann}
          {#if ann.type === 'fixed-area'}
            <!-- SUCCESS ROW: AI-repaired segment -->
            <div class="px-2 py-1.5 rounded-lg border border-emerald-500/20 bg-emerald-500/[0.06] flex items-start gap-2">
              <CheckCircle2 size={10} class="text-emerald-400 mt-0.5 shrink-0" />
              <div class="min-w-0">
                <span class="text-[7px] font-black text-emerald-400 uppercase">✅ ĐÃ SỬA</span>
                <p class="text-[8px] text-emerald-200/60 leading-relaxed mt-0.5 truncate italic">"{ann.text}"</p>
              </div>
            </div>
          {:else}
            {@const isInternal = ann.type === 'internal-dedup'}
            {@const annHex = ann.severity === 'high' ? '#ef4444' : ann.severity === 'medium' ? '#f59e0b' : '#eab308'}
            <div class="p-2 rounded-lg border bg-white/[0.02] flex flex-col gap-1.5 transition-all hover:bg-white/[0.04]" style="border-color: {annHex}20">
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
</div>
