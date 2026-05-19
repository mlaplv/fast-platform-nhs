<script lang="ts">
    import Shield from "@lucide/svelte/icons/shield";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Terminal from "@lucide/svelte/icons/terminal";
  import HelenIcon from '$lib/components/client/support/HelenIcon.svelte';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte';
  import { slide, fade } from 'svelte/transition';

  type NeuralStatus = 'idle' | 'verifying' | 'encoding' | 'submitting' | 'success' | 'error';
  
  const { status = 'idle', advice = '' } = $props<{
    status?: NeuralStatus;
    advice?: string;
  }>();

  const messages = {
    idle: 'Liên kết Neural: Giao thức Stealth đang bảo vệ phiên làm việc.',
    verifying: 'Đang đồng bộ dữ liệu Neural...',
    encoding: 'Mã hóa AES-256 Stealth...',
    submitting: 'Đang hoàn tất DNA giao dịch...',
    success: 'Đã xác minh tính toàn vẹn Neural.',
    error: 'Phát hiện xung đột Neural.'
  };
</script>

<div class="neural-guardian-agentic relative overflow-hidden bg-gradient-to-r from-stone-50/80 to-white/40 backdrop-blur-xl rounded-2xl border-l-[3px] border-luxury-copper/40 p-4 py-3 shadow-[0_15px_40px_rgba(0,0,0,0.02)] group">
  <!-- Dynamic Scanline -->
  <div class="absolute inset-x-0 h-[100%] w-[1px] bg-gradient-to-b from-transparent via-luxury-copper/20 to-transparent left-0 animate-scan pointer-events-none"></div>
  
  <!-- Neural Pulse Indicator -->
  <div class="absolute top-0 right-0 p-3 opacity-20">
    <div class="w-1.5 h-1.5 rounded-full bg-luxury-copper animate-ping"></div>
  </div>

  <div class="relative z-20">
    <!-- Agentic Mono Header -->
    <div class="flex items-center gap-2 mb-1.5">
      <Terminal size={8} class="text-luxury-copper" />
      <span class="text-[8px] font-mono font-bold tracking-[0.4em] text-stone-400 select-none">
        {supportAgent.config.agentName}.AI Cố vấn AI
      </span>
      {#if status !== 'idle' && status !== 'success'}
        <span class="w-1 h-3 bg-luxury-copper/40 animate-pulse rounded-full"></span>
      {/if}
    </div>
    
    <!-- Content Area with Inline Icon -->
    <div class="text-[12px] font-bold text-stone-800 leading-tight">
      {#key status + advice}
        <div in:fade={{ duration: 400 }} class="block">
          {#if advice}
            <div class="text-stone-600 font-medium tracking-tight leading-relaxed inline">
              <span class="inline-flex mr-0.5 align-middle -mt-0.5"><HelenIcon size={14} color="#c5a059" isPaused={status === 'success'} /></span>{advice}<span class="inline-block w-1.5 h-4 ml-1 bg-luxury-copper/40 animate-caret align-middle"></span>
            </div>
          {:else}
            <div class="text-stone-800 inline">
              <span class="inline-flex mr-0.5 align-middle -mt-0.5"><HelenIcon size={14} color="#c5a059" isPaused={status === 'success'} /></span>{messages[status]}<span class="inline-block w-1.5 h-4 ml-1 bg-luxury-copper/40 animate-caret align-middle"></span>
            </div>
          {/if}
        </div>
      {/key}
    </div>

    <!-- Integrity Shield on Success -->
    {#if status === 'success'}
      <div in:fade={{ delay: 300 }} class="absolute -top-1 right-0 flex flex-col items-center gap-0.5 opacity-60">
        <Shield size={12} class="text-luxury-copper" />
        <span class="text-[6px] font-black text-luxury-copper tracking-tighter">Đã bảo mật</span>
      </div>
    {/if}
  </div>

  <!-- Bottom Specular Highlight -->
  <div class="absolute bottom-0 left-0 h-[1px] bg-gradient-to-r from-transparent via-luxury-copper/10 to-transparent w-full"></div>
</div>

<style>
  .neural-guardian-agentic {
    transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
  }
  .neural-guardian-agentic:hover {
    background-color: rgba(255, 255, 255, 0.6);
    box-shadow: 0 20px 50px -10px rgba(197, 160, 89, 0.08);
    border-left-width: 5px;
    transform: translateX(4px);
  }

  @keyframes scan {
    0% { transform: translateX(0); opacity: 0; }
    10% { opacity: 0.5; }
    90% { opacity: 0.5; }
    100% { transform: translateX(800px); opacity: 0; }
  }
  .animate-scan {
    animation: scan 4s linear infinite;
  }

  @keyframes caret {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
  }
  .animate-caret {
    animation: caret 1s step-end infinite;
  }
</style>
