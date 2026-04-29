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
    isRewriting?: boolean;
    runNeuralRewrite?: () => void;
    streamingText?: string;
    streamingTarget?: string | null;
    userPlanNote?: string;
  }

  let { copyrightResult, isFixing, runCopyrightCheck, handleInternalFix, runBulkFix, isBulkFixing = false, isRewriting = false, runNeuralRewrite, streamingText = '', streamingTarget = null, userPlanNote = $bindable('') }: Props = $props();

  let lineNotes = $state<Record<string, string>>({});

  // CNS V90.1: Surgical Plan Parser — Identifies headers and plan steps for individual annotation
  const verdictBlocks = $derived.by(() => {
    if (!copyrightResult.verdict) return [];
    const raw = copyrightResult.verdict.split(/\n\n|(?=\n#{1,6}\s)|(?=\n-\s?\[?[A-ZÀ-Ỹ]{4,})/);
    let isPlanActive = false;
    
    return raw.map(section => {
      const trimmed = section.trim();
      if (!trimmed) return null;
      
      const isHeader = trimmed.startsWith('#') || trimmed.includes('**[LUẬN ĐIỂM') || trimmed.includes('**[CHỨNG CỨ') || trimmed.includes('**[PHƯƠNG ÁN') || trimmed.includes('[1.') || trimmed.includes('[2.') || trimmed.includes('[3.') || (trimmed.startsWith('-') && trimmed.includes(':') && trimmed.length < 60);
      
      if (isHeader) {
        isPlanActive = trimmed.includes('PHƯƠNG ÁN');
      }

      return { text: trimmed, isHeader, isPlan: isPlanActive };
    }).filter(Boolean);
  });

  // CNS V90.1: Aggregator — Combines per-line notes into a single prompt injection
  $effect(() => {
    const aggregated = Object.entries(lineNotes)
      .filter(([_, note]) => note.trim())
      .map(([line, note]) => `[ĐỐI VỚI: ${line.substring(0, 50)}...]: ${note}`)
      .join('\n');
    
    if (aggregated !== userPlanNote) {
      userPlanNote = aggregated;
    }
  });

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

      <button 
        onclick={() => runCopyrightCheck(true)} 
        class="mr-3 w-8 h-8 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-white/30 hover:text-white hover:bg-white/10 transition-all"
        title="Làm mới báo cáo trắc nghiệm bản quyền"
        aria-label="Làm mới báo cáo"
      >
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
        {#each verdictBlocks as block}
          {#if block.isHeader}
            <div class="text-[11px] font-black text-emerald-400 uppercase tracking-[0.2em] pt-3 border-b border-emerald-500/10 pb-1 flex items-center justify-between group/header">
               <div class="flex items-center gap-2">
                 <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]"></div>
                 {block.text.replace(/#+\s?|\*\*|\[|\]/g, '').replace(':', '').trim()}
               </div>
            </div>
          {:else if block.isPlan}
            <div class="space-y-3 pl-3 border-l border-emerald-500/10 py-1">
              {#each block.text.split('\n') as line}
                {@const lTrim = line.trim()}
                {#if lTrim}
                  <div class="group/line relative">
                    <div class="flex items-start gap-2 {lineNotes[lTrim] !== undefined ? 'bg-blue-500/10 -mx-2 px-2 py-1 rounded-sm' : ''}">
                      <span class="text-[12px] {lineNotes[lTrim] !== undefined ? 'text-blue-300' : 'text-white/70'} leading-relaxed">
                        {line}
                      </span>
                      <button 
                        onclick={() => {
                          if (lineNotes[lTrim] === undefined) {
                            lineNotes[lTrim] = "";
                          } else {
                            delete lineNotes[lTrim];
                            lineNotes = { ...lineNotes };
                          }
                        }}
                        class="mt-1 p-0.5 rounded-sm bg-transparent text-blue-500/50 hover:text-blue-400 transition-all opacity-0 group-hover/line:opacity-100 {lineNotes[lTrim] !== undefined ? 'opacity-100 text-blue-400' : ''}"
                        title="Thêm chỉ đạo chiến lược"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-plus-square"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M8 12h8"/><path d="M12 8v8"/></svg>
                      </button>
                    </div>

                    {#if lineNotes[lTrim] !== undefined}
                      <div class="mt-2 p-3 bg-[#161b22] border border-[#30363d] rounded-lg shadow-2xl animate-in zoom-in-95 duration-150 z-20 relative max-w-[440px]">
                        <textarea 
                          bind:value={lineNotes[lTrim]}
                          placeholder="Ghi chú chiến lược..."
                          class="w-full bg-[#0d1117] border border-[#30363d] rounded-md text-[13px] text-[#c9d1d9] placeholder:text-[#484f58] focus:ring-1 focus:ring-blue-500/50 focus:border-blue-500/50 outline-none p-3 resize-none min-h-[90px] leading-relaxed mb-3 transition-all"
                        ></textarea>
                        <div class="flex justify-end items-center gap-2">
                          <button 
                            onclick={() => { 
                              delete lineNotes[lTrim];
                              lineNotes = { ...lineNotes };
                            }}
                            class="px-4 py-1.5 rounded-md bg-transparent hover:bg-[#30363d] text-[13px] font-semibold text-[#c9d1d9] transition-all"
                          >
                            Hủy
                          </button>
                          <button 
                            onclick={() => { 
                              if (!lineNotes[lTrim]) {
                                delete lineNotes[lTrim];
                                lineNotes = { ...lineNotes };
                              }
                            }}
                            class="px-4 py-1.5 rounded-md bg-[#21262d] border border-[#30363d] hover:bg-[#30363d] hover:border-[#8b949e] disabled:opacity-50 disabled:cursor-not-allowed text-[13px] font-semibold text-[#c9d1d9] transition-all"
                            disabled={!lineNotes[lTrim]?.trim()}
                          >
                            Xác nhận ghi chú
                          </button>
                        </div>
                      </div>
                    {/if}
                  </div>
                {/if}
              {/each}
            </div>
          {:else}
            <div class="text-[12px] text-white/70 leading-relaxed whitespace-pre-wrap pl-3 border-l border-white/5 py-1">
               {block.text}
            </div>
          {/if}
        {/each}
      </div>

      <!-- High-Value Source List (Elite V2.2) -->
      {#if copyrightResult.similar_sources && copyrightResult.similar_sources.length > 0}
        <div class="mt-4 px-3 py-2 bg-blue-500/5 rounded-xl border border-blue-500/10 shadow-inner">
          <div class="text-[9px] font-black text-blue-400 uppercase tracking-widest mb-2 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg> TOP_REFERENCE_SOURCES
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

    <!-- Supreme Control Island: Neural Rewrite & Bulk Fix (Viral 2026) -->
    <div class="mt-4 px-3 pb-3">
      <div class="grid {runBulkFix && copyrightResult.annotations?.filter(a => a.type !== 'fixed-area').length > 0 ? 'grid-cols-2' : 'grid-cols-1'} gap-2.5">
        
        <!-- Neural Rewrite Activation -->
        <button 
          onclick={() => runNeuralRewrite?.()}
          disabled={isBulkFixing || isRewriting}
          class="group relative overflow-hidden rounded-xl bg-gradient-to-br from-indigo-600 via-purple-600 to-indigo-700 p-[1px] transition-all hover:scale-[1.02] hover:shadow-[0_0_30px_rgba(99,102,241,0.4)] active:scale-[0.98] disabled:opacity-50 disabled:grayscale"
        >
          <div class="relative z-10 flex flex-col items-center justify-center gap-1 bg-black/40 px-2 py-2.5 rounded-[11px] transition-all group-hover:bg-transparent h-full">
            {#if isRewriting}
              <div class="w-4 h-4 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin"></div>
              <span class="text-[7px] font-black text-indigo-300 uppercase tracking-widest animate-pulse">REWRITING...</span>
            {:else}
              <div class="flex items-center gap-2">
                <div class="relative">
                  <Sparkles size={14} class="text-indigo-300 animate-pulse" />
                  <div class="absolute inset-0 bg-indigo-400 blur-sm opacity-50 animate-ping"></div>
                </div>
                <span class="text-[10px] font-black text-white uppercase tracking-widest leading-none">XOHI REWRITE</span>
              </div>
              <span class="text-[6px] font-bold text-indigo-300/60 uppercase tracking-[0.2em]">Neural_Synthesis_V88</span>
            {/if}
          </div>
          <!-- Scanning Glow -->
          <div class="absolute top-0 -left-[100%] w-[100%] h-full bg-gradient-to-r from-transparent via-white/20 to-transparent group-hover:left-[100%] transition-all duration-1000 ease-in-out"></div>
        </button>

        <!-- Fix All Emerald Button -->
        {#if runBulkFix && copyrightResult.annotations?.filter(a => a.type !== 'fixed-area').length > 0}
          <button 
            onclick={() => runBulkFix?.()}
            disabled={isBulkFixing || isRewriting}
            class="group relative overflow-hidden rounded-xl bg-gradient-to-br from-emerald-500 via-teal-600 to-emerald-700 p-[1px] transition-all hover:scale-[1.02] hover:shadow-[0_0_30px_rgba(16,185,129,0.3)] active:scale-[0.98] disabled:opacity-50"
          >
            <div class="relative z-10 flex flex-col items-center justify-center gap-1 bg-black/40 px-2 py-2.5 rounded-[11px] transition-all group-hover:bg-emerald-500 group-hover:text-black h-full">
              {#if isBulkFixing && !isRewriting}
                <div class="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                <span class="text-[7px] font-black uppercase tracking-widest animate-pulse">ĐANG PHẪU THUẬT...</span>
              {:else}
                <div class="flex items-center gap-2">
                   <CheckCircle2 size={14} class="group-hover:text-black transition-colors" />
                   <span class="text-[10px] font-black uppercase tracking-widest leading-none transition-colors">PHẪU THUẬT TOÀN DIỆN ({copyrightResult.annotations.filter(a => a.type !== 'fixed-area').length})</span>
                </div>
                <span class="text-[6px] font-bold opacity-60 uppercase tracking-[0.2em] group-hover:text-black/60">Auto_Repair_Active</span>
              {/if}
            </div>
          </button>
        {/if}
      </div>
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
                  <span class="w-2 h-2 border border-white/30 border-t-white rounded-full animate-spin"></span> ĐANG PHẪU THUẬT...
                {:else}
                  <Sparkles size={8} class="text-yellow-400" /> PHẪU THUẬT
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
