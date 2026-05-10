<script lang="ts">
  import { onMount } from 'svelte';
  /**
   * IntelligenceHUD.svelte — Holographic Intelligence HUD
   * Component split from Toolbar.svelte to maintain < 500 lines.
   * Elite V2.7: Strictly typed, no any, high-performance logic.
   */
  import { fly, fade } from 'svelte/transition';
  import TrendingUpIcon from "@lucide/svelte/icons/trending-up";
  import XIcon from "@lucide/svelte/icons/x";
  import Maximize2Icon from "@lucide/svelte/icons/maximize-2";
  import Minimize2Icon from "@lucide/svelte/icons/minimize-2";  import { portal } from '$lib/core/actions/portal';
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import type { CopyrightResult, SEOResult, AIInspectResult, ToolbarAction, NeuralAnalysisController } from '$lib/state/types';
  import CheckResultPanel from '../../content-factory/CheckResultPanel.svelte';

  interface NeuralAnalysisData {
    runCopyrightCheck: () => void;
    runSeoAnalysis: () => void;
    runAiAnalysis: () => void;
    runAutoFix: (snippet: string, type: string, message: string) => Promise<string | null>;
    runNeuralRewrite: () => Promise<void>;
  }

  let {
    activeIntelAction = $bindable(),
    toolbarActions = [] as ToolbarAction[],
    intelPopoverPos,
    bulkFixLogs = [],
    copyrightResult,
    seoResult,
    aiReadyResult,
    isCopyrightLoading,
    isSeoLoading,
    isAiLoading,
    isBoosting,
    isBulkFixing,
    isRewriting = false,
    runBulkFix = null,
    analysisData,
    currentAnalysisStep,
    streamingText = '',
    streamingTarget = null,
    userPlanNote = $bindable(),
  }: {
    activeIntelAction: string | null;
    toolbarActions: ToolbarAction[];
    intelPopoverPos: { top: number; left: number };
    bulkFixLogs: string[];
    copyrightResult: CopyrightResult | null;
    seoResult: SEOResult | null;
    aiReadyResult: AIInspectResult | null;
    isCopyrightLoading: boolean;
    isSeoLoading: boolean;
    isAiLoading: boolean;
    isBoosting: boolean;
    isBulkFixing: boolean;
    isRewriting?: boolean;
    runBulkFix?: (() => void) | null;
    analysisData: NeuralAnalysisController | null;
    currentAnalysisStep: number | null;
    streamingText?: string;
    streamingTarget?: string | null;
    userPlanNote?: string;
  } = $props();

  let isExpanded = $state(false);

  onMount(() => {
    if (userPlanNote === undefined) userPlanNote = '';
  });

  const activeAction = $derived.by(() => {
    if (!activeIntelAction) return null;
    const found = toolbarActions.find(a => a.id === activeIntelAction);
    if (found) return found;
    if (activeIntelAction === 'clean') return { id: 'clean', label: 'Neural Clean', loading: isBulkFixing };
    
    // CNS V89.0: Auto-construct virtual action if missing from toolbar (Safety fallback)
    return { id: activeIntelAction, label: activeIntelAction.toUpperCase(), loading: false };
  });

  // CNS V86.5: Tự động reset trạng thái phóng to khi HUD đóng (Fix lỗi viewfull lưu state)
  $effect(() => {
    if (!activeAction) {
      isExpanded = false;
    }
  });

  let hudEl = $state<HTMLElement | null>(null);

  // CNS V85.5: Viewport Sentinel — Dynamic positioning to prevent clipping
  const geometry = $derived.by(() => {
    if (isExpanded) return {
      top: '4vh',
      left: '4vw',
      width: '92vw',
      height: '82vh',
      maxHeight: '82vh',
      borderRadius: '24px'
    };

    const targetHeight = 550;
    const targetWidth = 520;
    let top = intelPopoverPos.top;
    let left = intelPopoverPos.left;

    // Viewport Clipping Avoidance
    if (typeof window !== 'undefined') {
      if (top + targetHeight > window.innerHeight - 20) {
        top = Math.max(10, window.innerHeight - targetHeight - 20);
      }
      if (left + targetWidth > window.innerWidth - 20) {
        left = Math.max(10, window.innerWidth - targetWidth - 20);
      }
    }

    return {
      top: `${top}px`,
      left: `${left}px`,
      width: `${targetWidth}px`,
      height: 'auto',
      maxHeight: `min(${targetHeight}px, calc(100dvh - ${top}px - 20px))`,
      borderRadius: '12px'
    };
  });
</script>

{#if activeAction}
  <!-- CNS V89.0: Debug visibility check -->
  <div class="hidden">{console.log("[IntelligenceHUD] Rendering for:", activeAction.id)}</div>
  
  <!-- Holographic HUD Popover -->
  <div 
     bind:this={hudEl}
     use:portal
     class="fixed bg-[#0d1117]/98 backdrop-blur-3xl border border-white/10 shadow-[0_20px_60px_rgba(0,0,0,0.6)] flex flex-col overflow-hidden pointer-events-auto system-hologram"
     style="top: {geometry.top}; left: {geometry.left}; width: {geometry.width}; {isExpanded ? `height: ${geometry.height};` : ''} max-height: {geometry.maxHeight}; z-index: {Z_INDEX_ADMIN.NEURAL_HUD}; border-radius: {geometry.borderRadius};"
     transition:fade={{ duration: 200 }}
   >
     <!-- Scanlines Overlay -->
     <div class="absolute inset-0 pointer-events-none opacity-[0.03] scanlines-pattern"></div>
     
     <!-- Corner Brackets -->
     <div class="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-cyan-500/40 rounded-tl-lg m-1.5"></div>
     <div class="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-cyan-500/40 rounded-tr-lg m-1.5"></div>
     <div class="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-cyan-500/40 rounded-bl-lg m-1.5"></div>
     <div class="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-cyan-500/40 rounded-br-lg m-1.5"></div>

     <!-- Header: System Status -->
     <div class="px-4 py-3 border-b border-white/5 flex items-center justify-between relative bg-black/20 backdrop-blur-md">
        <div class="flex items-center gap-3">
           <div class="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center shadow-[0_0_20px_rgba(6,182,212,0.1)] relative group">
              <div class="absolute inset-0 bg-cyan-400/20 rounded-xl blur-md opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <TrendingUpIcon size={16} class="text-cyan-400 relative z-10" />
           </div>
           <div class="flex flex-col">
              <div class="flex items-center gap-2">
                 <span class="text-[12px] font-black tracking-[0.2em] text-white uppercase opacity-90">NEURAL TERMINAL</span>
                 <div class="px-1.5 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-[7px] font-black text-cyan-400 uppercase tracking-widest animate-pulse">Live</div>
              </div>
              <span class="text-[8px] font-black text-white/20 uppercase tracking-[0.4em]">Elite Protocol V2.2 // Surgical AI</span>
           </div>
        </div>
        <div class="flex items-center gap-1.5">
           <button onclick={(e) => { e.stopPropagation(); isExpanded = !isExpanded; }} class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-white/5 text-white/20 hover:text-white transition-all group" title={isExpanded ? "Collapse" : "Full View"}>
              {#if isExpanded}<Minimize2Icon size={14} class="group-hover:scale-110 transition-transform"/>{:else}<Maximize2Icon size={14} class="group-hover:scale-110 transition-transform"/>{/if}
           </button>
           <button onclick={(e) => { e.stopPropagation(); activeIntelAction = null; }} class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-rose-500/10 text-white/20 hover:text-rose-400 transition-all">
              <XIcon size={16}/>
           </button>
        </div>
     </div>

     <!-- AI Thinking Logs (Unified HUD Layer) -->
     {#if activeAction.loading || isBulkFixing || bulkFixLogs?.length > 0}
        <div class="px-0 py-0.5 border-b border-white/5">
           <div class="bg-black/60 p-3 max-h-40 overflow-y-auto custom-scrollbar flex flex-col gap-1.5 relative group">
              <div class="absolute top-2 right-2 flex gap-1">
                 <div class="w-1 h-1 rounded-full bg-cyan-500/40"></div>
                 <div class="w-1 h-1 rounded-full bg-cyan-500/20"></div>
              </div>
              {#each (bulkFixLogs || []).slice(-15) as log}
                 <div class="flex gap-2 text-[10px] font-mono tracking-tight py-0.5 border-b border-white/[0.02]" in:fade>
                    
                    <span class="text-white/80 leading-relaxed font-semibold">{log}</span>
                 </div>
              {/each}
              {#if activeAction.loading}
                 <div class="flex items-center gap-2 text-[9px] text-cyan-400 font-bold uppercase tracking-widest mt-1 animate-pulse">
                    <div class="flex gap-1">
                       <div class="w-1 h-3 bg-cyan-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                       <div class="w-1 h-3 bg-cyan-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                       <div class="w-1 h-3 bg-cyan-500 rounded-full animate-bounce"></div>
                    </div>
                    Neural Engine processing...
                 </div>
              {/if}
           </div>
        </div>
     {/if}

     <!-- Result Content -->
     {#if activeAction.id !== 'clean'}
     <div class="flex-1 overflow-y-auto custom-scrollbar p-0 min-h-0 relative">
        <div class="bg-white/[0.01] overflow-hidden">
          <CheckResultPanel
             activeTab={(activeAction.id.includes('-fix') ? activeAction.id.split('-')[0] : activeAction.id) as 'copyright' | 'seo' | 'ai' | 'enrich' | null}
             copyrightResult={copyrightResult}
             isCopyrightLoading={isCopyrightLoading}
             seoResult={seoResult}
             isSeoLoading={isSeoLoading}
             aiReadyResult={aiReadyResult}
             isAiLoading={isAiLoading}
             isBoosting={isBoosting}
             runCopyrightCheck={analysisData?.runCopyrightCheck}
             runSeoAnalysis={analysisData?.runSeoAnalysis}
             runAiAnalysis={analysisData?.runAiAnalysis}
             onfix={analysisData?.runAutoFix}
             {streamingTarget}
             {bulkFixLogs}
             runBulkFix={runBulkFix || undefined}
             isBulkFixing={isBulkFixing}
             isRewriting={isRewriting}
             runNeuralRewrite={analysisData?.runNeuralRewrite}
             bind:userPlanNote={userPlanNote}
             currentAnalysisStep={currentAnalysisStep}
             boosterAnnotations={analysisData?.boosterAnnotations ?? []}
          />
        </div>
     </div>
     {/if}

     <!-- Footer Stats -->
     <div class="px-4 py-1.5 bg-white/5 border-t border-white/5 flex items-center justify-between">
        <div class="text-[8px] font-mono text-white/20 uppercase tracking-tighter">Memory: 42.5MB // Latency: 12ms</div>
        <div class="flex items-center gap-1">
           <div class="w-1.5 h-1.5 rounded-full bg-cyan-500"></div>
           <span class="text-[8px] font-bold text-cyan-500/80 uppercase tracking-widest">Neural_Sync_Active</span>
        </div>
     </div>
  </div>

  <!-- Global Overlay -->
  <div 
    use:portal 
    transition:fade={{ duration: 200 }}
    class="fixed inset-0" 
    style="z-index: {Z_INDEX_ADMIN.TIPTAP_TOOLBAR_OVERLAY};" 
    onclick={(e) => {
       e.stopPropagation();
       if (e.target === e.currentTarget) activeIntelAction = null;
    }}
  ></div>
{/if}

<style>
  .system-hologram {
    box-shadow: 0 0 30px rgba(6, 182, 212, 0.1), inset 0 0 20px rgba(6, 182, 212, 0.05);
  }

  .scanlines-pattern {
    background: linear-gradient(
      rgba(18, 16, 16, 0) 50%, 
      rgba(0, 0, 0, 0.25) 50%
    ), linear-gradient(
      90deg, 
      rgba(255, 0, 0, 0.06), 
      rgba(0, 255, 0, 0.02), 
      rgba(0, 0, 255, 0.06)
    );
    background-size: 100% 2px, 3px 100%;
  }

  .glow-cyan {
    box-shadow: 0 0 10px rgba(6, 182, 212, 0.2);
  }

  .custom-scrollbar::-webkit-scrollbar {
    width: 3px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(6, 182, 212, 0.2);
    border-radius: 10px;
  }
</style>
