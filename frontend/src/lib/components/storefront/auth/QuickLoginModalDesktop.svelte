<script lang="ts">
  import AuthForm from '$lib/components/storefront/auth/AuthForm.svelte';
  import X from "@lucide/svelte/icons/x";
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { portal } from '$lib/core/actions/portal';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { fade, scale } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';

  const ui = getClientUi();
  let mode = $derived(ui.authModal.mode);
</script>

<div 
  use:portal 
  class="fixed inset-0 flex items-center justify-center bg-black/80 backdrop-blur-xl p-6" 
  style:z-index={Z_INDEX_CLIENT.OVERLAY}
  in:fade={{ duration: 400 }}
  onclick={(e) => e.target === e.currentTarget && ui.closeModal()}
>
  <div 
    class="bg-white w-full max-w-[420px] rounded-none shadow-[0_30px_100px_rgba(0,0,0,0.5)] overflow-hidden relative flex flex-col max-h-[85vh] transition-all border border-gray-100"
    style:z-index={Z_INDEX_CLIENT.MODAL}
    in:scale={{ start: 0.98, duration: 300, easing: cubicOut }}
  >
    <!-- Sharp Professional Header (Desktop) -->
    <div class="relative flex flex-col items-center pt-4 pb-3 px-12 shrink-0 border-b border-gray-100">
        <!-- Branding Title -->
        <div class="flex flex-col items-center justify-center space-y-1 text-center">
            <h2 class="text-[18px] font-black text-gray-400 tracking-[0.2em] uppercase leading-tight">
              {mode === 'login' ? 'ĐĂNG NHẬP' : (mode === 'register' ? 'ĐĂNG KÝ' : 'TÀI KHOẢN')}
            </h2>
            <div class="w-4 h-0.5 bg-gray-100 mt-1"></div>
        </div>

        <!-- Close Button -->
        <button 
          onclick={() => ui.closeModal()} 
          class="absolute right-6 top-6 w-10 h-10 flex items-center justify-center text-gray-400 hover:text-black transition-all active:scale-90"
        >
          <X class="w-6 h-6" strokeWidth={1.5} />
        </button>
    </div>

    <!-- Form Content Area -->
    <div class="flex-1 overflow-y-auto overscroll-contain pb-2 custom-scrollbar">
      <AuthForm onClose={() => ui.closeModal()} rounded={false} />
    </div>
  </div>
</div>

