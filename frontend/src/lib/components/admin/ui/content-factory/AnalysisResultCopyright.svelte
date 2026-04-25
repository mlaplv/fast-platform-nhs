<script lang="ts">
  import Sparkles from "lucide-svelte/icons/sparkles";
  import CheckCircle2 from "lucide-svelte/icons/check-circle-2";
  import type { CopyrightResult } from "$lib/state/types";

  interface Props {
    copyrightResult: CopyrightResult;
    isFixing: string | null;
    runCopyrightCheck: (force?: boolean) => void;
    handleInternalFix: (snippet: string, type: string, message: string) => void;
    runBulkFix?: () => void;
    isBulkFixing?: boolean;
    runNeuralRewrite?: () => void;
    streamingText?: string;
    streamingTarget?: string | null;
  }

  let { copyrightResult, isFixing, runCopyrightCheck, handleInternalFix, runBulkFix, isBulkFixing = false, runNeuralRewrite, streamingText = '', streamingTarget = null }: Props = $props();

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
            <span class="text-[13px] font-black tracking-tighter" style="color:{riskColor}">{pct}%</span>
            <span class="text-[6px] font-black opacity-30 uppercase tracking-[0.2em]">Rating</span>
          </div>
        </div>

        <!-- Risk Level & Protocol -->
        <div class="flex flex-col gap-1.5 px-3">
          <div class="flex flex-col gap-1.5">
            <span class="text-sm font-black uppercase tracking-[0.1em]" style="color:{riskColor}">
              {copyrightResult.risk_level === 'LOW' ? 'PROTECTED' : copyrightResult.risk_level === 'MEDIUM' ? 'STRICT CAUTION' : 'CRITICAL RISK'}
            </span>
            <div class="flex items-center gap-1.5 opacity-30">
              <span class="text-[9px] font-black uppercase tracking-[0.3em]">Protocol_XoHi_System_V2.2</span>
            </div>
          </div>
        </div>
      </div>

      <button onclick={() => runCopyrightCheck(true)} class="mr-3 w-8 h-8 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-white/30 hover:text-white hover:bg-white/10 transition-all">
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/></svg>
      </button>
    </div>

    <!-- Verdict -->
    <div class="px-4 py-4 bg-black/40 border-b border-white/5 shadow-inner">
      <div class="flex items-center gap-2 mb-3 opacity-30">
        <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]"></div>
        <span class="text-[10px] font-black uppercase tracking-[0.2em]">Neural_Legal_Verdict</span>
      </div>
      
      <div class="text-[13px] text-white/80 leading-[1.6] font-medium tracking-tight space-y-4">
        {#each copyrightResult.verdict.split('\n\n') as section}
          {#if section.startsWith('###') || section.includes('**[LUẬN ĐIỂM') || section.includes('**[CHỨNG CỨ') || section.includes('**[PHƯƠNG ÁN')}
            <div class="text-[11px] font-black text-emerald-400 uppercase tracking-[0.2em] pt-3 border-b border-emerald-500/10 pb-1 flex items-center gap-2">
               <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]"></div>
               {section.replace(/###|\*\*|\[|\]/g, '').replace(':', '').trim()}
            </div>
          {:else if section.startsWith('####')}
            <div class="text-[10px] font-black text-white/40 uppercase tracking-widest pt-1 flex items-center gap-1.5 ml-2">
               <div class="w-1 h-1 rounded-full bg-white/20"></div>
               {section.replace('####', '').trim()}
            </div>
          {:else}
            <div class="whitespace-pre-line pl-3 border-l border-white/5 text-white/70 bg-white/[0.01] p-3 rounded-r-lg">
              {@html section
                .replace(/\*\*(.*?)\*\*/g, '<span class="text-white font-bold">$1</span>')
                .replace(/^- (.*?)($|\n)/gm, '<div class="flex gap-2 items-start ml-2 mb-1.5"><span class="text-emerald-500/50 mt-1.5">›</span><span>$1</span></div>')
                .replace(/^(\d+\. .*?)($|\n)/gm, '<div class="flex gap-2 items-start ml-2 mb-1.5"><span class="text-emerald-400 font-black mt-0.5">$1</span></div>')
              }
            </div>
          {/if}
        {/each}
      </div>

      <!-- High-Value Source List (Elite V2.2) -->
      {#if copyrightResult.similar_sources && copyrightResult.similar_sources.length > 0}
        <div class="mt-4 px-3 py-2 bg-blue-500/5 rounded-xl border border-blue-500/10 shadow-inner">
          <div class="text-[9px] font-black text-blue-400 uppercase tracking-widest mb-2 flex items-center gap-2">
            <Globe size={10} /> TOP_REFERENCE_SOURCES
          </div>
          <div class="space-y-1.5">
            {#each copyrightResult.similar_sources.slice(0, 3) as source}
              <a href={source} target="_blank" class="block text-[11px] text-white/50 hover:text-blue-300 transition-colors truncate pl-2 border-l border-white/10 font-mono">
                {source}
              </a>
            {/each}
          </div>
        </div>
      {/if}
    </div>

      <!-- Neural Rewrite Activation (Elite V2.2) -->
      <div class="mt-5 pt-4 border-t border-white/5">
        <button 
          onclick={() => runNeuralRewrite?.()}
          disabled={isBulkFixing}
          class="group relative w-full overflow-hidden rounded-xl bg-gradient-to-br from-indigo-600/20 to-purple-600/20 border border-indigo-500/30 p-[1px] transition-all hover:border-indigo-400 hover:shadow-[0_0_30px_rgba(99,102,241,0.2)] active:scale-[0.98] disabled:opacity-50"
        >
          <div class="relative z-10 flex items-center justify-center gap-3 bg-black/40 px-4 py-3 rounded-[11px] transition-all group-hover:bg-transparent">
            <div class="relative">
              <Sparkles size={16} class="text-indigo-400 animate-pulse" />
              <div class="absolute inset-0 bg-indigo-400 blur-sm opacity-50 animate-ping"></div>
            </div>
            <div class="flex flex-col items-start">
              <span class="text-[11px] font-black text-white uppercase tracking-widest leading-none">KÍCH HOẠT XOHI REWRITE</span>
              <span class="text-[7px] font-bold text-indigo-300/60 uppercase tracking-[0.2em] mt-1">Creative_Neural_Synthesis_V88.5</span>
            </div>
          </div>
          <!-- Internal Glow -->
          <div class="absolute top-0 -left-[100%] w-[100%] h-full bg-gradient-to-r from-transparent via-white/10 to-transparent group-hover:left-[100%] transition-all duration-1000 ease-in-out"></div>
        </button>
      </div>
    </div>

    <!-- Fix All Emerald Button -->
    {#if runBulkFix && copyrightResult.annotations?.filter(a => a.type !== 'fixed-area').length > 0}
      <div class="px-3 py-2 border-b border-emerald-500/10 bg-emerald-500/[0.02]">
        <button 
          onclick={() => runBulkFix?.()}
          disabled={isBulkFixing && copyrightResult.annotations.filter(a => a.type !== 'fixed-area').length === 0}
          class="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 hover:bg-emerald-500 hover:text-black hover:border-emerald-400 text-emerald-400 text-[10px] font-black uppercase tracking-widest transition-all shadow-[0_0_20px_rgba(16,185,129,0.1)] active:scale-95 disabled:opacity-50"
        >
          {#if isBulkFixing}
            <div class="w-3 h-3 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
            NEURAL_FIXING...
          {:else}
            <Sparkles size={12} class="animate-pulse" />
            FIX ALL COPYRIGHT ({copyrightResult.annotations.filter(a => a.type !== 'fixed-area').length})
          {/if}
        </button>
      </div>
    {/if}
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
              <span class="text-[8px] font-black text-emerald-400 uppercase">✅ ĐÃ SỬA</span>
              <p class="text-[12px] text-white/80 leading-relaxed mt-0.5 tracking-tight">
                <span class="text-white/40 font-mono italic">"{ann.text}"</span>
              </p>
            </div>
          </div>
        {:else}
          {@const isInternal = ann.type === 'internal-dedup'}
          {@const annHex = ann.severity === 'high' ? '#ef4444' : ann.severity === 'medium' ? '#f59e0b' : '#eab308'}
          <div class="px-3 py-3 border-b bg-white/[0.01] flex flex-col gap-1.5 transition-all hover:bg-white/[0.02]" style="border-color: {annHex}15">
            <div class="flex items-start justify-between gap-2">
              <span class="text-[7px] font-black px-1 py-0.5 rounded uppercase" style="background: {annHex}20; color: {annHex}">{isInternal ? '🔁 TRÙNG LẶP NỘI BỘ' : `🚨 COPYRIGHT ${ann.severity?.toUpperCase()}`}</span>
              <button onclick={() => handleInternalFix(ann.text, ann.type || 'copyright', ann.reason || 'Cần kiểm tra COPYRIGHT')} disabled={!!isFixing} class="shrink-0 flex items-center gap-1 px-2 py-0.5 rounded border border-white/10 hover:bg-white/10 text-[7px] font-black uppercase transition-all disabled:opacity-40">
                {#if streamingTarget === ann.text}
                  <span class="text-[8px] text-white/80 font-mono leading-relaxed">{streamingText}<span class="inline-block w-1 h-2.5 bg-orange-400 animate-pulse ml-0.5 -mb-0.5"></span></span>
                {:else if isFixing === ann.text}
                  <span class="w-2 h-2 border border-white/30 border-t-white rounded-full animate-spin"></span> FIXING...
                {:else}
                  <Sparkles size={8} class="text-yellow-400" /> SỬA LỖI
                {/if}
              </button>
            </div>
            <p class="text-[12px] text-white/80 leading-relaxed tracking-tight">
              <span class="text-white/40 font-mono italic">"{ann.text}"</span> <br/>
              <span class="text-orange-200/90">{ann.reason}</span>
            </p>
            {#if ann.source_url && !isInternal}<a href={ann.source_url} target="_blank" class="text-[7px] text-blue-400/60 hover:text-blue-400 underline truncate">🔗 Nguồn: {ann.source_url}</a>{/if}
          </div>
        {/if}
      {/each}
    </div>
  {/if}
</div>
