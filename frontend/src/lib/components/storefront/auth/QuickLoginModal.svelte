<script lang="ts">
  import AuthForm from '$lib/components/storefront/auth/AuthForm.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { X } from 'lucide-svelte';
  import { fade, fly } from 'svelte/transition';

  const ui = getClientUi();
  let mode = $derived(ui.authModal.mode);
</script>

<div class="fixed inset-0 z-[var(--z-modal-overlay)] flex items-center justify-center p-4 bg-black/40 backdrop-blur-[2px]" in:fade>
  <div class="bg-white w-full max-w-sm rounded-none shadow-2xl border border-gray-100 overflow-hidden relative"
       in:fly={{ y: 20, duration: 400 }}>

    <div class="px-8 py-6 border-b border-gray-50 flex items-center justify-start relative">
      <h2 class="text-xl font-black text-gray-900 tracking-tighter uppercase">
        {mode === 'login' ? 'ĐĂNG NHẬP' : 'GIA NHẬP'}
      </h2>
      <button onclick={() => ui.closeModal()} class="absolute top-4 right-4 p-2 hover:bg-gray-100 transition-colors">
        <X class="w-5 h-5 text-gray-400" />
      </button>
    </div>

    <AuthForm onClose={() => ui.closeModal()} />
  </div>
</div>
