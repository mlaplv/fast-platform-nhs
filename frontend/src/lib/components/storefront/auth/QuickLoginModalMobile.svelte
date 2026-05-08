<script lang="ts">
  import AuthForm from '$lib/components/storefront/auth/AuthForm.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { portal } from '$lib/core/actions/portal';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { fade, fly } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';

  const ui = getClientUi();
  let mode = $derived(ui.authModal.mode);
</script>

<div 
  use:portal 
  class="fixed inset-0 flex items-end justify-center bg-black/60 backdrop-blur-md" 
  style:z-index={Z_INDEX_CLIENT.OVERLAY}
  in:fade={{ duration: 300 }}
  onclick={(e) => e.target === e.currentTarget && ui.closeModal()}
>
  <div 
    class="bg-white w-full rounded-t-[32px] shadow-[0_-10px_50px_rgba(0,0,0,0.15)] overflow-hidden relative flex flex-col max-h-[92vh] transition-all"
    style:z-index={Z_INDEX_CLIENT.MOBILE_BOTTOM_SHEET}
    in:fly={{ y: '100%', duration: 450, easing: cubicOut }}
  >
    <!-- TikTok Style Header (Mobile) -->
    <div class="relative flex flex-col items-center pt-2 pb-2 px-6 shrink-0 border-b border-gray-50/50">
        <!-- Grab Handle -->
        <div class="w-8 h-1 bg-gray-100 rounded-full mb-3"></div>

        <!-- Branding Title -->
        <div class="flex flex-col items-center justify-center space-y-0 text-center">
            <h2 class="text-[16px] font-black text-gray-400 tracking-[0.2em] uppercase italic leading-tight">
              {mode === 'login' ? 'ĐĂNG NHẬP' : (mode === 'register' ? 'ĐĂNG KÝ' : 'TÀI KHOẢN')}
            </h2>
        </div>

        <!-- Close Button -->
        <button 
          onclick={() => ui.closeModal()} 
          class="absolute right-4 top-4 w-10 h-10 flex items-center justify-center text-gray-300 hover:text-black transition-all active:scale-90"
        >
          <X class="w-6 h-6" strokeWidth={2} />
        </button>
    </div>

    <!-- Form Content Area -->
    <div class="flex-1 overflow-y-auto overscroll-contain pb-safe custom-scrollbar">
      <AuthForm onClose={() => ui.closeModal()} rounded={true} />
    </div>
  </div>
</div>

<style>
  .pb-safe {
    padding-bottom: calc(env(safe-area-inset-bottom, 20px) + 4px);
  }
</style>
