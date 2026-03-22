<script lang="ts">
  import { onMount } from "svelte";
  import { fade, scale, fly } from "svelte/transition";
  import { Sparkles, Cpu, Zap, Activity } from "lucide-svelte";

  interface Props {
    progress_msg: string;
    viewingStep: number;
    campaign_id?: string;
  }

  let { progress_msg = "", viewingStep, campaign_id }: Props = $props();

  // History of messages to create "Data Crystals"
  let messageHistory = $state<string[]>([]);
  
  $effect(() => {
    if (progress_msg && !messageHistory.includes(progress_msg)) {
      messageHistory = [progress_msg, ...messageHistory].slice(0, 5);
    }
  });

  const stepLabels = [
    "Khởi tạo Brain",
    "Trinh sát Ground Truth",
    "Thiết giáp Săn ảnh",
    "Phác thảo Neural",
    "Chế tác Nội dung",
    "Hậu kỳ & Viral Edge"
  ];
</script>

<div class="relative w-full h-full flex flex-col items-center justify-center overflow-hidden bg-slate-950/85 backdrop-blur-2xl p-12" in:fade>
  <!-- 1. Mesh Gradient Background (iPhone 18 Style) -->
  <div class="absolute inset-0 z-0 pointer-events-none overflow-hidden">
    <div class="absolute -top-[20%] -left-[10%] w-[60%] h-[60%] rounded-full bg-purple-600/20 blur-[120px] animate-mesh-1"></div>
    <div class="absolute top-[30%] -right-[10%] w-[50%] h-[50%] rounded-full bg-blue-600/20 blur-[100px] animate-mesh-2"></div>
    <div class="absolute -bottom-[10%] left-[20%] w-[40%] h-[40%] rounded-full bg-fuchsia-600/15 blur-[80px] animate-mesh-3"></div>
  </div>

  <!-- 2. The Neural Core (Glassmorphism) -->
  <div class="relative z-10 flex flex-col items-center gap-8">
    <div class="relative group">
      <!-- Outer Glows -->
      <div class="absolute inset-[-40px] bg-blue-500/20 rounded-full blur-[60px] animate-pulse opacity-60"></div>
      <div class="absolute inset-[-20px] bg-purple-500/15 rounded-full blur-[40px] animate-pulse-slow opacity-40"></div>
      
      <!-- Glass Sphere -->
      <div class="w-48 h-48 rounded-full border border-white/20 bg-white/5 backdrop-blur-3xl flex items-center justify-center relative overflow-hidden shadow-[0_0_50px_rgba(255,255,255,0.05),inset_0_0_20px_rgba(255,255,255,0.1)]">
        <!-- Inner Shimmers -->
        <div class="absolute inset-0 bg-gradient-to-tr from-white/10 to-transparent"></div>
        <div class="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_30%_30%,rgba(255,255,255,0.2)_0%,transparent_50%)]"></div>
        
        <!-- Animated Elements inside Core -->
        <div class="flex flex-col items-center gap-2">
           <Zap size={32} class="text-white animate-bounce-gentle drop-shadow-[0_0_15px_rgba(255,255,255,0.8)]" />
           <div class="text-[10px] font-black tracking-[0.3em] uppercase text-white/40">XOHI CORE</div>
        </div>
        
        <!-- Scanning Effect -->
        <div class="absolute inset-0 bg-gradient-to-b from-transparent via-white/5 to-transparent h-1/2 w-full animate-scan-v"></div>
      </div>
    </div>

    <!-- 3. Dynamic Progress Information -->
    <div class="flex flex-col items-center gap-3 max-w-md w-full text-center">
      <div class="space-y-1">
        <h3 class="text-xl md:text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-blue-200 to-white/70 tracking-tight">
          {stepLabels[viewingStep - 1] || "AI đang chế tác..."}
        </h3>
        <p class="text-[10px] md:text-[11px] font-bold text-blue-400/80 uppercase tracking-[0.2em] flex items-center justify-center gap-2">
          <Activity size={12} class="animate-pulse" /> Đẳng cấp Viral Edge V2.2
        </p>
      </div>

      <!-- Progressive Message -->
      <div class="mt-4 px-6 py-3 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md min-w-[280px] shadow-2xl overflow-hidden relative group" in:fly={{ y: 20 }}>
        <div class="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-blue-500 to-purple-500"></div>
        <span class="text-[13px] font-semibold text-white/90 leading-relaxed italic block truncate">
           "{progress_msg || 'Kế nối Neural Network...'}"
        </span>
      </div>
    </div>
  </div>

  <!-- 4. Data Crystals (Floating History) -->
  <div class="absolute inset-0 z-5 pointer-events-none">
    {#each messageHistory as msg, i}
      <div 
        class="absolute hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/5 backdrop-blur-sm text-[9px] font-medium text-white/30"
        style="
          left: {15 + (i * 10)}%; 
          top: {20 + (i * 15)}%; 
          animation: float {5 + i}s infinite ease-in-out;
          opacity: {1 - (i * 0.2)};
          transform: scale({1 - (i * 0.1)});
        "
        in:scale
      >
        <Sparkles size={8} class="text-white/20" />
        {msg.substring(0, 40)}{msg.length > 40 ? '...' : ''}
      </div>
    {/each}
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
    <div class="text-[8px] font-black text-white/20 uppercase tracking-[0.5em] animate-pulse">NEURAL PROCESSING UNIT · ACTIVATED</div>
  </div>
</div>

<style>
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
  
  :global(.text-glow) {
    text-shadow: 0 0 10px rgba(255, 255, 255, 0.4);
  }
</style>
