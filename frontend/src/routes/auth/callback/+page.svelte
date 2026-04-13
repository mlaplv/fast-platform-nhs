<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { Loader2, ShieldCheck, CheckCircle2 } from 'lucide-svelte';
  import { fly } from 'svelte/transition';

  const ui = getClientUi();
  let status = $state<'processing' | 'success' | 'error'>('processing');
  let errorMessage = $state('');

  onMount(() => {
    // Wait for SvelteKit page store to initialize
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const error = params.get('error');

    if (error) {
      status = 'error';
      errorMessage = error;
      setTimeout(() => {
        goto('/');
      }, 3000);
      return;
    }

    if (!token) {
      status = 'error';
      errorMessage = 'Không hợp lệ (Missing Token)';
      setTimeout(() => {
        goto('/');
      }, 3000);
      return;
    }

    try {
      // Decode JWT Payload to feed AuthStore
      const payloadBase64 = token.split('.')[1];
      const payloadDecoded = JSON.parse(atob(payloadBase64));
      
      authStore.setSession(token, {
        id: payloadDecoded.id || 'unknown',
        email: payloadDecoded.sub || '',
        name: payloadDecoded.name || payloadDecoded.sub?.split('@')[0] || 'User',
        role: (payloadDecoded.roles && payloadDecoded.roles[0]) || 'CUSTOMER'
      });

      status = 'success';
      
      // Cleanup UI
      ui.closeModal();

      // Redirect home and clean URL
      setTimeout(() => {
        window.location.replace('/');
      }, 1500);

    } catch (err) {
      status = 'error';
      errorMessage = 'Token bị hỏng hoặc hết hạn';
      setTimeout(() => {
        goto('/');
      }, 3000);
    }
  });

</script>

<div class="fixed inset-0 bg-[#020202] z-[99999] flex items-center justify-center">
  <div class="bg-zinc-900 border border-white/10 shadow-2xl p-8 rounded-xl max-w-sm w-full text-center relative overflow-hidden">
    
    <!-- Background pulse aesthetic -->
    <div class="absolute inset-0 bg-gradient-to-t from-[#C18F7E]/10 to-transparent pointer-events-none"></div>

    {#if status === 'processing'}
      <div class="space-y-4 relative z-10 flex flex-col items-center">
        <Loader2 class="w-12 h-12 animate-spin text-[#C18F7E] mb-2" />
        <h2 class="text-xl font-black text-white uppercase tracking-widest">Đang Đồng Bộ</h2>
        <p class="text-xs text-slate-400">Đang mã hóa tuyến dữ liệu với máy chủ bảo mật của hệ thống...</p>
        
        <div class="flex items-center gap-2 mt-6 px-4 py-2 bg-black/40 rounded-full border border-white/5">
          <ShieldCheck class="w-4 h-4 text-emerald-500" />
          <span class="text-[9px] uppercase tracking-widest text-emerald-400 font-bold">256-bit encryption</span>
        </div>
      </div>
    {:else if status === 'success'}
      <div class="space-y-4 relative z-10 flex flex-col items-center" in:fly={{y: 20}}>
        <div class="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mb-2">
           <CheckCircle2 class="w-10 h-10 text-emerald-500" />
        </div>
        <h2 class="text-xl font-black text-white uppercase tracking-widest">Hoàn Tất</h2>
        <p class="text-xs text-slate-400">Đăng nhập thành công! Đang chuyển hướng bạn...</p>
      </div>
    {:else}
      <div class="space-y-4 relative z-10 flex flex-col items-center">
        <h2 class="text-xl font-black text-red-500 uppercase tracking-widest">Thất Bại</h2>
        <p class="text-xs text-slate-400">{errorMessage}</p>
        <p class="text-xs text-slate-500">Đang quay lại...</p>
      </div>
    {/if}
  </div>
</div>
