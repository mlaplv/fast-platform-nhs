<script lang="ts">
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import XohiNanoSprite from "$lib/components/admin/XohiNanoSprite.svelte";
  import { generateErrorHash } from "$lib/utils/hash";
  
  // Elite V2.2: Deterministic error state derived from Svelte 5 Runes
  let status = $derived($page.status ?? 404);
  let message = $derived($page.error?.message ?? "Không tìm thấy tài nguyên (Not Found)");
  let errorHash = $derived(generateErrorHash(status, message));
</script>

<div class="min-h-screen bg-[#020202] flex flex-col items-center justify-center font-sans text-gray-100 p-6 selection:bg-[#00FFFF]/30 perspective-1000 overflow-hidden">
  
  <!-- Liquid Glass Atmosphere -->
  <div class="fixed inset-0 bg-[radial-gradient(circle_at_50%_-20%,#00FFFF10,transparent_50%)] pointer-events-none"></div>
  <div class="fixed inset-0 bg-[radial-gradient(circle_at_0%_100%,#FF00FF05,transparent_40%)] pointer-events-none"></div>
  
  <div class="max-w-md w-full relative group">
    
    <!-- Cybernetic Orbitals -->
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] border border-[#00FFFF]/5 rounded-full animate-spin-slow pointer-events-none"></div>
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[350px] h-[350px] border border-[#00FFFF]/10 rounded-full animate-spin-reverse-slow pointer-events-none"></div>

    <!-- Main Container: Liquid Glass (Viral 2026) -->
    <div class="relative z-10 bg-black/40 backdrop-blur-3xl border border-white/10 rounded-3xl p-10 flex flex-col items-center text-center shadow-[0_0_80px_rgba(0,0,0,0.5),inset_0_0_20px_rgba(255,255,255,0.02)] transition-all duration-500 hover:border-[#00FFFF]/30 hover:shadow-[0_0_100px_rgba(0,255,255,0.05)]">
      
      <!-- Top Aesthetic Line -->
      <div class="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-[2px] bg-gradient-to-r from-transparent via-[#00FFFF] to-transparent shadow-[0_0_15px_#00FFFF]"></div>
      
      <!-- NanoBot Core -->
      <div class="mb-8 relative transform transition-transform duration-700 group-hover:scale-110">
        <div class="absolute inset-0 bg-[#00FFFF]/30 blur-[30px] rounded-full animate-pulse"></div>
        <div class="relative z-20">
            <XohiNanoSprite />
        </div>
      </div>

      <!-- Error Content -->
      <div class="space-y-6 mb-12 w-full">
        <div class="relative inline-block">
            <h1 class="text-8xl font-mono text-[#00FFFF] font-extralight tracking-tighter drop-shadow-[0_0_20px_rgba(0,255,255,0.4)] animate-glitch" data-text={status}>
                {status}
            </h1>
        </div>
        
        <div class="h-[1px] w-12 bg-gradient-to-r from-transparent via-white/30 to-transparent mx-auto"></div>
        
        <div class="space-y-2">
            <p class="text-[10px] text-[#00FFFF]/70 font-mono tracking-[0.3em] uppercase">System Interruption Identified</p>
            <p class="text-xs text-gray-400 max-w-[280px] mx-auto leading-relaxed font-mono tracking-wider italic">
            "{message}"
            </p>
        </div>
        
        {#if $page.error?.stack}
          <div class="mt-6 p-4 bg-black/60 border border-white/5 rounded-xl text-left overflow-x-auto max-h-48 overflow-y-auto w-full custom-scrollbar">
            <pre class="text-[9px] text-[#00FFFF]/50 font-mono leading-tight">{$page.error.stack}</pre>
          </div>
        {/if}
      </div>

      <!-- Critical Action -->
      <button 
        onclick={() => goto("/")}
        class="group/btn relative px-10 py-4 w-full rounded-xl transition-all duration-300 overflow-hidden border border-[#00FFFF]/20 bg-[#00FFFF]/5 hover:bg-[#00FFFF]/10 active:scale-[0.98]"
      >
        <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover/btn:translate-x-full transition-transform duration-700"></div>
        <span class="relative z-10 text-[10px] font-mono tracking-[0.4em] text-white uppercase font-bold">
           Re-establish Core Connection
        </span>
      </button>

      <!-- Meta Info -->
      <div class="mt-10 flex flex-col gap-1 items-center">
        <div class="text-[8px] font-mono text-gray-600 tracking-[0.5em] uppercase">
             TraceID-Hash: <span class="text-[#00FFFF]/40">{errorHash}</span>
        </div>
        <div class="w-1 h-1 bg-[#00FFFF]/30 rounded-full animate-ping"></div>
      </div>
    </div>
  </div>
</div>

<style>
  :global(.animate-spin-slow) {
    animation: spin 30s linear infinite;
  }
  :global(.animate-spin-reverse-slow) {
    animation: spin-reverse 25s linear infinite;
  }
  @keyframes spin {
    from { transform: translate(-50%, -50%) rotate(0deg); }
    to { transform: translate(-50%, -50%) rotate(360deg); }
  }
  @keyframes spin-reverse {
    from { transform: translate(-50%, -50%) rotate(360deg); }
    to { transform: translate(-50%, -50%) rotate(0deg); }
  }
  
  .animate-glitch {
    position: relative;
  }
  .animate-glitch::before,
  .animate-glitch::after {
    content: attr(data-text);
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background: transparent;
  }
  .animate-glitch::before {
    left: 2px;
    text-shadow: -2px 0 #ff00ff;
    clip: rect(44px, 450px, 56px, 0);
    animation: glitch-anim 5s infinite linear alternate-reverse;
  }
  .animate-glitch::after {
    left: -2px;
    text-shadow: -2px 0 #00ffff;
    clip: rect(44px, 450px, 56px, 0);
    animation: glitch-anim2 5s infinite linear alternate-reverse;
  }

  @keyframes glitch-anim {
    0% { clip: rect(31px, 9999px, 94px, 0); }
    20% { clip: rect(62px, 9999px, 42px, 0); }
    40% { clip: rect(16px, 9999px, 78px, 0); }
    60% { clip: rect(58px, 9999px, 33px, 0); }
    80% { clip: rect(81px, 9999px, 12px, 0); }
    100% { clip: rect(45px, 9999px, 67px, 0); }
  }
  @keyframes glitch-anim2 {
    0% { clip: rect(65px, 9999px, 100px, 0); }
    20% { clip: rect(10px, 9999px, 53px, 0); }
    40% { clip: rect(78px, 9999px, 12px, 0); }
    60% { clip: rect(23px, 9999px, 89px, 0); }
    80% { clip: rect(5px, 9999px, 44px, 0); }
    100% { clip: rect(89px, 9999px, 22px, 0); }
  }

  .custom-scrollbar::-webkit-scrollbar {
    width: 2px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(0, 255, 255, 0.1);
    border-radius: 10px;
  }
</style>

