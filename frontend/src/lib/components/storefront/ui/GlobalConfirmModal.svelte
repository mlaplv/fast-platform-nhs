<script lang="ts">
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import { Z_INDEX_CLIENT } from "$lib/core/constants/zIndex";

  const ui = getClientUi();
  const modal = $derived(ui.confirmModal);
</script>

<div 
  class="global-confirm-modal-root"
  class:active={!!modal}
>
  <!-- Backdrop -->
  <button 
    class="fixed inset-0 bg-black/75 border-none outline-none w-full h-full block cursor-pointer"
    style="z-index: {Z_INDEX_CLIENT.MODAL - 1};"
    onclick={() => modal?.onCancel()}
    aria-label="Đóng confirm"
  ></button>

  <!-- Modal Container -->
  <div 
    class="fixed inset-0 flex items-center justify-center p-4 pointer-events-none"
    style="z-index: {Z_INDEX_CLIENT.MODAL};"
  >
    <div 
      class="global-confirm-content w-full max-w-md bg-[#0a0a0a] border border-white/5 shadow-2xl pointer-events-auto overflow-hidden relative"
    >
      <!-- Premium Background Effects -->
      <div class="absolute inset-0 bg-gradient-to-br from-[#ee4d2d]/5 via-transparent to-transparent opacity-50"></div>
      <div class="absolute -top-24 -right-24 w-48 h-48 bg-[#ee4d2d]/10 rounded-full blur-[80px]"></div>

      <div class="relative z-10 p-8">
        <!-- Header -->
        <h3 class="text-xs font-black tracking-[0.3em] text-[#ee4d2d] mb-4 flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
          {modal?.title || ''}
        </h3>

        <!-- Body -->
        <p class="text-lg font-bold text-white italic leading-snug antialiased mb-8">
          {modal?.message || ''}
        </p>

        <!-- Actions -->
        <div class="grid grid-cols-2 gap-4">
          <button 
            onclick={() => modal?.onCancel()}
            class="py-4 px-6 border border-white/10 text-white font-black text-[10px] tracking-widest hover:bg-white/5 transition-all text-center bg-transparent cursor-pointer"
          >
            {modal?.cancelLabel || 'HỦY'}
          </button>
          
          <button 
            onclick={() => modal?.onConfirm()}
            class="py-4 px-6 bg-[#ee4d2d] text-white font-black text-[10px] tracking-widest hover:brightness-110 transition-all text-center relative group overflow-hidden cursor-pointer"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>
            <span class="relative z-10">{modal?.confirmLabel || 'XÁC NHẬN'}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .global-confirm-modal-root {
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.15s ease-out;
  }
  .global-confirm-modal-root.active {
    opacity: 1;
    pointer-events: auto;
  }
  .global-confirm-content {
    transform: scale(0.96);
    transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
  .global-confirm-modal-root.active .global-confirm-content {
    transform: scale(1);
  }
  div {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
  }
</style>

