<script lang="ts">
  import AuthForm from '$lib/components/storefront/auth/AuthForm.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { X } from 'lucide-svelte';
  import { fade, fly } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';

  const ui = getClientUi();
  let mode = $derived(ui.authModal.mode);
</script>

<!-- TikTok Style Bottom Sheet Overlay -->
<div class="fixed inset-0 z-[var(--z-modal-overlay)] flex items-end justify-center bg-black/60 backdrop-blur-md" 
     in:fade={{ duration: 300 }}
     onclick={(e) => e.target === e.currentTarget && ui.closeModal()}>
  
  <div class="bg-white w-full max-w-lg rounded-t-[32px] shadow-[0_-8px_40px_rgba(0,0,0,0.2)] overflow-hidden relative flex flex-col max-h-[92vh]"
       in:fly={{ y: '100%', duration: 450, easing: cubicOut }}>
    
    <!-- Grab Handle (TikTok Signature) -->
    <div class="w-full h-8 flex items-center justify-center shrink-0">
      <div class="w-10 h-1.5 bg-gray-200 rounded-full"></div>
    </div>

    <!-- Header Section (Lean & Mean) -->
    <div class="px-8 pt-2 pb-4 flex items-center justify-between shrink-0">
      <h2 class="text-2xl font-black text-black tracking-tighter uppercase leading-none">
        {mode === 'login' ? 'Đăng nhập' : (mode === 'register' ? 'Đăng ký' : 'Tài khoản')}
      </h2>
      <button onclick={() => ui.closeModal()} class="p-2 bg-gray-100 rounded-full active:scale-95 transition-all">
        <X class="w-5 h-5 text-black" />
      </button>
    </div>

    <!-- Form Content Area -->
    <div class="flex-1 overflow-y-auto overscroll-contain scrollbar-hide pb-safe">
      <AuthForm onClose={() => ui.closeModal()} />
    </div>
  </div>
</div>

<style>
  /* Elite 2026: Hide scrollbar for auth form inside bottom sheet */
  .scrollbar-hide::-webkit-scrollbar {
    display: none;
  }
  .scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
  
  .pb-safe {
    padding-bottom: calc(env(safe-area-inset-bottom, 20px) + 20px);
  }
</style>
