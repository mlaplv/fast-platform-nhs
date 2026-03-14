<script lang="ts">
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import XohiNanoSprite from "$lib/components/admin/XohiNanoSprite.svelte";
  
  // Safely extract status and message
  let status = $derived($page.status ?? 404);
  let message = $derived($page.error?.message ?? "Không tìm thấy dữ liệu (Not Found)");
</script>

<div class="min-h-screen bg-[#050505] flex flex-col items-center justify-center font-sans text-gray-100 p-6 selection:bg-[#00FFFF]/30">
  
  <div class="max-w-md w-full relative">
    <!-- Cyberpunk Decorative Ring -->
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 border-[1px] border-[#00FFFF]/5 rounded-full animate-spin-slow pointer-events-none"></div>
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 border-[1px] border-[#00FFFF]/10 rounded-full animate-spin-reverse-slow pointer-events-none"></div>

    <div class="relative z-10 bg-black/80 backdrop-blur-xl border border-white/10 rounded-2xl p-10 flex flex-col items-center text-center shadow-[0_0_50px_rgba(0,255,255,0.05)] overflow-hidden">
      
      <!-- Top Cyber Line -->
      <div class="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-[#00FFFF]/50 to-transparent"></div>
      
      <!-- NanoBot Icon -->
      <div class="mb-8 relative">
        <div class="absolute inset-0 bg-[#00FFFF]/20 blur-[20px] rounded-full"></div>
        <XohiNanoSprite />
      </div>

      <!-- Error Data -->
      <div class="space-y-4 mb-10 w-full">
        <h1 class="text-7xl font-mono text-[#00FFFF] font-light tracking-tighter mix-blend-screen drop-shadow-[0_0_15px_rgba(0,255,255,0.5)]">
          {status}
        </h1>
        <div class="h-px w-16 bg-white/20 mx-auto"></div>
        <p class="text-sm text-gray-400 max-w-[280px] mx-auto leading-relaxed font-mono uppercase tracking-widest">
           {message}
        </p>
      </div>

      <!-- Actions -->
      <button 
        onclick={() => goto("/")}
        class="group relative px-8 py-3 w-full border border-white/20 bg-white/5 hover:bg-white/10 rounded-lg transition-all duration-300 overflow-hidden"
      >
        <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
        <span class="relative z-10 text-[11px] font-mono tracking-[0.2em] text-white uppercase whitespace-nowrap">
           TRỞ VỀ TRẠM KIỂM SOÁT (HOME)
        </span>
      </button>

      <!-- Bottom System Hash -->
      <div class="mt-8 text-[9px] font-mono text-gray-700 tracking-widest uppercase">
         SYS_ERR_HASH: {Math.random().toString(16).substring(2, 10)}
      </div>
    </div>
  </div>
</div>

<style>
  :global(.animate-spin-slow) {
    animation: spin 20s linear infinite;
  }
  :global(.animate-spin-reverse-slow) {
    animation: spin-reverse 15s linear infinite;
  }
  @keyframes spin {
    from { transform: translate(-50%, -50%) rotate(0deg); }
    to { transform: translate(-50%, -50%) rotate(360deg); }
  }
  @keyframes spin-reverse {
    from { transform: translate(-50%, -50%) rotate(360deg); }
    to { transform: translate(-50%, -50%) rotate(0deg); }
  }
</style>
