<script lang="ts">
  import { Shield, Sparkles } from 'lucide-svelte';
  import HelenIcon from '$lib/components/client/support/HelenIcon.svelte';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte';
  import { slide, fade } from 'svelte/transition';

  type NeuralStatus = 'idle' | 'verifying' | 'encoding' | 'submitting' | 'success' | 'error';
  
  const { status = 'idle', advice = '' } = $props<{
    status?: NeuralStatus;
    advice?: string;
  }>();

  const messages = {
    idle: 'Neural Guardian Active: Đơn hàng được bảo vệ bởi giao thức Stealth.',
    verifying: 'Đang xác thực thông tin đơn hàng...',
    encoding: 'Mã hóa địa chỉ & dữ liệu thanh toán...',
    submitting: 'Đang hoàn tất giao diện vận hành...',
    success: 'Đơn hàng đã được xác nhận bảo mật thành công!',
    error: 'Phát hiện sự cố Neural. Vui lòng thử lại.'
  };
</script>

<div class="neural-guardian relative overflow-hidden bg-white rounded-xl border border-gray-100 p-4 shadow-sm group">
  <!-- Specular Reflection Layer -->
  <div class="absolute inset-0 bg-gradient-to-br from-white/40 to-transparent pointer-events-none z-10"></div>
  
  <div class="flex items-center gap-4 relative z-20">
    <div class="relative">
      <div class="absolute -inset-2 bg-gradient-to-r from-luxury-sakura/20 to-luxury-gold/20 rounded-full blur-md animate-pulse"></div>
      <HelenIcon size={32} color="#C18F7E" isPaused={status === 'success'} />
    </div>
    
    <div class="flex flex-col flex-1 min-w-0">
      <div class="flex items-center gap-1.5 mb-0.5">
        <Sparkles size={10} class="text-luxury-gold fill-luxury-gold/20" />
        <span class="text-[9px] font-black uppercase tracking-[0.2em] text-gray-400">AI {supportAgent.config.agentName} Advisor</span>
      </div>
      
      <p class="text-[12px] font-bold text-gray-800 leading-tight">
        {#key status + advice}
          <span in:slide={{axis: 'y'}} class="block">
            {#if advice}
              <span class="text-slate-600 font-medium tracking-tight leading-relaxed block">{advice}</span>
            {:else}
              {messages[status]}
            {/if}
          </span>
        {/key}
      </p>
    </div>

    {#if status === 'success'}
      <div in:fade class="shrink-0 bg-green-50 p-1.5 rounded-full border border-green-100">
        <Shield size={16} class="text-green-500 fill-green-50" />
      </div>
    {/if}
  </div>

  <!-- Micro-interaction: Liquid pulse on the bottom border -->
  <div class="absolute bottom-0 left-0 h-[2px] bg-gradient-to-r from-transparent via-luxury-sakura/40 to-transparent w-full transition-all duration-1000 group-hover:via-luxury-gold/60"></div>
</div>

<style>
  .neural-guardian {
    transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .neural-guardian:hover {
    border-color: rgba(193, 143, 126, 0.2);
    box-shadow: 0 10px 30px -10px rgba(193, 143, 126, 0.1);
    transform: translateY(-1px);
  }
</style>
