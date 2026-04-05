<script lang="ts">
  import { onMount } from "svelte";
  import { fade, scale, fly } from "svelte/transition";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import Cpu from "lucide-svelte/icons/cpu";
  import Zap from "lucide-svelte/icons/zap";
  import Activity from "lucide-svelte/icons/activity";
  import Brain from "lucide-svelte/icons/brain";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();

  interface Props {
    progress_msg: string;
    viewingStep: number;
    campaign_id?: string;
    liveContent?: string;
    isAnalysisMessage?: boolean;
  }

  let { progress_msg = "", viewingStep, campaign_id, liveContent = "", isAnalysisMessage = false }: Props = $props();

  // CNS V85.2: Live Telemetry (Neural Metrics) - Optimized to prevent UI thread blockage
  let telemetry = $derived.by(() => {
    // Phase 86.5: Scout Intelligence - Simulate metrics for Step 1 (Thinking Data)
    if (viewingStep === 1) {
      if (!progress_msg) return { words: 0, sentences: 0, images: 0, sections: 0 };
      // Neural Scout Metrics: Nodes, Keywords, Sources, Analysis %
      return { 
        words: 12, 
        sentences: 8, 
        images: 10, 
        sections: progress_msg.includes("giải mã") ? 88 : (progress_msg.includes("thực địa") ? 42 : 15) 
      };
    }

    if (!liveContent || liveContent.length < 10) return { words: 0, sentences: 0, images: 0, sections: 0 };
    
    // Use faster, simpler counting logic for telemetry
    const words = liveContent.split(/\s+/).length;
    const imgTags = (liveContent.match(/<img/gi) || []).length;
    const mdImages = (liveContent.match(/!\[.*?\]\(.*?\)/g) || []).length;
    const placeholders = (liveContent.match(/\[IMAGE_\d+\]/gi) || []).length;
    const images = imgTags + mdImages + placeholders;
    const sections = (liveContent.match(/<h[2-6]/gi) || []).length + (liveContent.match(/^#{2,6}\s/gm) || []).length;
    const sentences = (liveContent.match(/[.!?]+/g) || []).length;
    
    return { words: Math.max(0, words), sentences, images, sections };
  });

  // CNS V86.5: Neural Streaming Content
  // CNS V86.5: Neural Streaming Content (Ultra-Safe Fallback)
  let streamingText = $derived((nanobot && typeof nanobot.liveStreamBuffer === 'string') ? (nanobot.liveStreamBuffer || liveContent || "") : (liveContent || ""));
  let showStream = $derived((viewingStep === 3 || viewingStep === 4) && !isAnalysisMessage && streamingText.length > 0);

  // History of messages for the "Live Feed" effect
  let messageHistory = $state<string[]>([]);
  
  $effect(() => {
    if (progress_msg && !messageHistory.includes(progress_msg)) {
      // Don't add the same message twice, and keep only the last 5
      messageHistory = [progress_msg, ...messageHistory].slice(0, 5);
    }
  });

  const stepLabels = [
    "Khởi tạo Brain",           // 1: Idea
    "Thiết giáp Săn ảnh",       // 2: Assets
    "Phác thảo Neural",         // 3: Outline
    "Chế tác Nội dung",         // 4: Draft
    "Kiểm định Viral Edge",     // 5: Analysis
    "Vinh quang & Viral"        // 6: Publish
  ];

  // Map messages to status icons
  function getStatusIcon(msg: string, isLatest: boolean) {
    if (isLatest) return "animate-pulse text-blue-400";
    return "text-green-500/50";
  }
</script>

<div class="relative w-full h-full flex flex-col items-center justify-center overflow-hidden bg-slate-950/90 backdrop-blur-xl p-12" style="z-index: {Z_INDEX_ADMIN.SYSTEM};" in:fade>
  <!-- 1. Mesh Gradient Background - Simplified for Performance -->
  <div class="absolute inset-0 z-0 pointer-events-none overflow-hidden opacity-60">
    <div class="absolute -top-[20%] -left-[10%] w-[60%] h-[60%] rounded-full bg-purple-600/10 blur-[80px] animate-mesh-1"></div>
    <div class="absolute top-[30%] -right-[10%] w-[50%] h-[50%] rounded-full bg-blue-600/10 blur-[60px] animate-mesh-2"></div>
  </div>

  <!-- 2. The Neural Core (Glassmorphism) -->
  <div class="relative z-10 flex flex-col items-center gap-8">
    <div class="relative group">
      <!-- Outer Glows -->
      <div class="absolute inset-[-40px] bg-blue-500/20 rounded-full blur-[60px] animate-pulse opacity-60"></div>
      <div class="absolute inset-[-20px] bg-purple-500/15 rounded-full blur-[40px] animate-pulse-slow opacity-40"></div>
      
      <!-- Glass Sphere -->
      <div class="w-48 h-48 md:w-56 md:h-56 rounded-full border border-white/20 bg-white/5 backdrop-blur-3xl flex items-center justify-center relative overflow-hidden shadow-[0_0_80px_rgba(59,130,246,0.15),inset_0_0_30px_rgba(255,255,255,0.1)]">
        <!-- Inner Shimmers -->
        <div class="absolute inset-0 bg-gradient-to-tr from-white/10 to-transparent"></div>
        <div class="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_30%_30%,rgba(255,255,255,0.2)_0%,transparent_50%)]"></div>
        
        <!-- Animated Elements inside Core -->
        <div class="flex flex-col items-center gap-2">
           {#if viewingStep === 3}
             <Brain size={40} class="text-cyan-400 animate-pulse drop-shadow-[0_0_20px_rgba(34,211,238,0.8)]" />
           {:else}
             <Zap size={40} class="text-white animate-bounce-gentle drop-shadow-[0_0_20px_rgba(255,255,255,1)]" />
           {/if}
           <div class="text-[11px] font-black tracking-[0.4em] uppercase text-white/50">NEURAL XOHI</div>
        </div>
        
        <!-- Scanning Effect -->
        <div class="absolute inset-0 bg-gradient-to-b from-transparent via-white/10 to-transparent h-1/2 w-full animate-scan-v"></div>
      </div>

      <!-- CNS V86.5: Neural Stream Panel (The 'Root Cause' Visual Fix) -->
      {#if showStream}
        <div 
          class="absolute -inset-x-20 -bottom-40 h-32 overflow-hidden pointer-events-none opacity-30 mask-linear-fade"
          transition:fade
        >
          <div class="text-[10px] font-mono text-blue-300 leading-relaxed break-all text-center animate-neural-scroll">
            {streamingText.replace(/<[^>]*>?/gm, ' ')}
            {streamingText.replace(/<[^>]*>?/gm, ' ')}
          </div>
        </div>
      {/if}
    </div>

    <!-- 3. Progress Log (Claude/IDE Style) -->
    <div class="w-full max-w-lg mt-8 space-y-3 px-4">
      <div class="flex items-center gap-2 mb-4">
        <div class="w-2 h-2 rounded-full bg-blue-500 animate-ping"></div>
        <span class="text-[10px] font-black uppercase tracking-[0.3em] text-white/40">Neural Xohi Execution Logs</span>
      </div>

      <div class="space-y-2 font-mono">
        <!-- Active Task -->
        {#if progress_msg}
          <div class="p-4 rounded-xl bg-white/[0.08] border border-white/20 backdrop-blur-md shadow-2xl relative overflow-hidden group mb-4" in:fly={{ y: 20 }}>
            <div class="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-blue-400 to-cyan-300"></div>
            <div class="flex items-center gap-3">
              <Activity size={16} class="text-blue-400 animate-pulse" />
              <div class="flex flex-col gap-0.5">
                <span class="text-[8px] font-black uppercase tracking-widest text-blue-400/60">Executing Task</span>
                <span class="text-[14px] font-bold text-white leading-tight">
                  {progress_msg}
                </span>
              </div>
            </div>
            <!-- Progress Shimmer -->
            <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full animate-progress-shimmer"></div>
          </div>
        {/if}

        <!-- Historical Feed (Claude/IDE Style) -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          <div class="space-y-1.5 opacity-80 pl-1 border-r border-white/5 pr-4">
            <span class="text-[8px] font-black uppercase text-white/20 tracking-widest block mb-2">Process Stack</span>
            {#each messageHistory.slice(1) as logMsg, i}
              <div 
                class="flex items-center gap-3 py-1 px-2 rounded-lg hover:bg-white/5 transition-colors group/log"
                in:fly={{ x: -10, delay: i * 50 }}
              >
                <div class="w-3.5 h-3.5 rounded-full bg-green-500/10 border border-green-500/20 flex items-center justify-center shrink-0 shadow-[0_0_10px_rgba(34,197,94,0.1)]">
                  <div class="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
                </div>
                <span class="text-[10px] text-white/40 group-hover/log:text-white/60 transition-colors truncate">
                  {logMsg}
                </span>
                <span class="ml-auto text-[7px] font-black text-green-500/30 uppercase tracking-tighter">Done</span>
              </div>
            {/each}
            {#if viewingStep === 3 && !isAnalysisMessage}
               <div class="flex items-center gap-3 py-1 px-2 animate-pulse">
                  <div class="w-2 h-2 rounded-full bg-cyan-500"></div>
                  <span class="text-[10px] text-cyan-400 font-mono tracking-tighter italic">Architecting neural nodes...</span>
               </div>
            {:else if viewingStep === 4 && !isAnalysisMessage}
               <div class="flex items-center gap-3 py-1 px-2 animate-pulse">
                  <div class="w-2 h-2 rounded-full bg-blue-500"></div>
                  <span class="text-[10px] text-blue-400 font-mono tracking-tighter italic">Neural surgeon injecting patterns...</span>
               </div>
            {/if}
          </div>

          <!-- CNS V85.2: Live Telemetry Dashboard -->
          <div class="space-y-3">
             <span class="text-[8px] font-black uppercase text-white/20 tracking-widest block mb-2">Neural Telemetry</span>
             <div class="grid grid-cols-2 gap-2">
                <div class="bg-white/5 border border-white/10 rounded-xl p-3 flex flex-col items-center justify-center gap-1 group/tel">
                   <span class="text-[9px] font-black text-white/30 uppercase tracking-tighter transition-colors group-hover/tel:text-blue-400">
                     {viewingStep === 1 ? 'Nodes' : 'Words'}
                   </span>
                   <span class="text-xl font-black text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.2)]">
                     {#if viewingStep === 1 && telemetry.words > 0}
                        <span class="animate-pulse">{telemetry.words}</span>
                     {:else}
                        {telemetry.words}
                     {/if}
                   </span>
                </div>
                <div class="bg-white/5 border border-white/10 rounded-xl p-3 flex flex-col items-center justify-center gap-1 group/tel">
                   <span class="text-[9px] font-black text-white/30 uppercase tracking-tighter transition-colors group-hover/tel:text-cyan-400">
                     {viewingStep === 1 ? 'Keywords' : 'Sentences'}
                   </span>
                   <span class="text-xl font-black text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.2)]">
                     {#if viewingStep === 1 && telemetry.sentences > 0}
                        <span class="animate-pulse">{telemetry.sentences}</span>
                     {:else}
                        {telemetry.sentences}
                     {/if}
                   </span>
                </div>
                <div class="bg-white/5 border border-white/10 rounded-xl p-3 flex flex-col items-center justify-center gap-1 group/tel">
                   <span class="text-[9px] font-black text-white/30 uppercase tracking-tighter transition-colors group-hover/tel:text-emerald-400">
                     {viewingStep === 1 ? 'Sources' : 'Images'}
                   </span>
                   <span class="text-xl font-black text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.2)]">{telemetry.images}</span>
                </div>
                <div class="bg-white/5 border border-white/10 rounded-xl p-3 flex flex-col items-center justify-center gap-1 group/tel">
                   <span class="text-[9px] font-black text-white/30 uppercase tracking-tighter transition-colors group-hover/tel:text-purple-400">
                     {viewingStep === 1 ? 'Analysis %' : 'Sections'}
                   </span>
                   <span class="text-xl font-black text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.2)]">
                     {telemetry.sections}{viewingStep === 1 ? '%' : ''}
                   </span>
                </div>
             </div>
          </div>
        </div>

        <div class="h-px bg-white/5 my-4"></div>

        <!-- System Specs -->
        <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
          <div class="flex items-center gap-2 px-3 py-2 rounded-lg bg-black/40 border border-white/5 text-[9px] text-white/30">
            <Cpu size={12} class="text-blue-500/30" />
            <span>Neural Xohi Engine V2</span>
          </div>
          <div class="flex items-center gap-2 px-3 py-2 rounded-lg bg-black/40 border border-white/5 text-[9px] text-white/30">
            <Sparkles size={12} class="text-cyan-500/30" />
            <span>Style: {stepLabels[viewingStep - 1]?.split(" ")[0] || 'Viral'}</span>
          </div>
          <div class="hidden md:flex items-center gap-2 px-3 py-2 rounded-lg bg-black/40 border border-white/5 text-[9px] text-white/30">
            <Zap size={12} class="text-yellow-500/30" />
            <span>Latency: 42ms</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 4. Metadata Clusters (Subtle technical details) -->
  <div class="absolute bottom-32 left-10 md:left-20 z-10 flex flex-col gap-2 pointer-events-none opacity-40">
    <div class="text-[8px] font-mono text-white/30 uppercase tracking-[0.2em] mb-2 font-black">Environment Specs</div>
    <div class="flex items-center gap-2 px-2 py-1 bg-white/5 border border-white/10 rounded-md text-[9px] font-mono text-blue-300">
      <div class="w-1 h-1 rounded-full bg-blue-500"></div>
      ID: {campaign_id?.slice(0, 8) || 'SYSTEM'}
    </div>
    <div class="flex items-center gap-2 px-2 py-1 bg-white/5 border border-white/10 rounded-md text-[9px] font-mono text-cyan-300">
      <div class="w-1 h-1 rounded-full bg-cyan-500"></div>
      STEP: 0{viewingStep}/06
    </div>
  </div>

  <!-- 5. Status Indicators (Bottom) -->
  <div class="absolute bottom-0 left-0 right-0 h-48 bg-gradient-to-t from-slate-950 via-slate-950/80 to-transparent z-10 pointer-events-none"></div>
  <div class="absolute bottom-12 left-0 right-0 flex flex-col items-center gap-6 z-20">
    <div class="flex items-center gap-6">
       {#each Array(6) as _, i}
         <div class="relative">
            {#if i + 1 === viewingStep}
               <div class="absolute inset-0 bg-blue-500/50 rounded-full blur-md animate-ping"></div>
            {/if}
            <div class="w-2 h-2 rounded-full transition-all duration-500 {i + 1 <= viewingStep ? 'bg-white scale-110' : 'bg-white/10 scale-90'}"></div>
         </div>
       {/each}
    </div>
    <div class="text-[8px] font-black text-white/20 uppercase tracking-[0.5em] animate-pulse">NEURAL PROCESSING UNIT · NEURAL XOHI ACTIVE</div>
  </div>
</div>

<style>
  @reference "tailwindcss";
  
  @keyframes mesh-1 {
    0%, 100% { transform: translate(0, 0) scale(1); }
    50% { transform: translate(10%, 15%) scale(1.1); }
  }
  @keyframes mesh-2 {
    0%, 100% { transform: translate(0, 0) scale(1); }
    50% { transform: translate(-15%, -10%) scale(0.9); }
  }
  @keyframes mesh-3 {
    0%, 100% { transform: translate(0, 0) scale(1.1); }
    50% { transform: translate(20%, -5%) scale(1); }
  }
  @keyframes scan-v {
    0% { transform: translateY(-100%); }
    100% { transform: translateY(200%); }
  }
  @keyframes progress-shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(200%); }
  }
  @keyframes float {
    0%, 100% { transform: translateY(0) rotate(0); }
    50% { transform: translateY(-20px) rotate(2deg); }
  }
  @keyframes bounce-gentle {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
  }
  .animate-pulse-slow { animation: pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
  .animate-mesh-1 { animation: mesh-1 20s infinite ease-in-out; }
  .animate-mesh-2 { animation: mesh-2 15s infinite ease-in-out; }
  .animate-mesh-3 { animation: mesh-3 25s infinite ease-in-out; }
  .animate-scan-v { animation: scan-v 3s linear infinite; }
  .animate-progress-shimmer { animation: progress-shimmer 2.5s infinite linear; }
  
  @keyframes neural-scroll {
    0% { transform: translateY(0); }
    100% { transform: translateY(-50%); }
  }
  .animate-neural-scroll { animation: neural-scroll 60s linear infinite; }
  
  .mask-linear-fade {
    mask-image: linear-gradient(to bottom, transparent, black 20%, black 80%, transparent);
  }
  
  :global(.text-glow) {
    text-shadow: 0 0 10px rgba(255, 255, 255, 0.4);
  }
</style>
