<script lang="ts">
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { fade, fly } from 'svelte/transition';
  import CheckCircle2 from "@lucide/svelte/icons/check-circle-2";
  import AlertCircle from "@lucide/svelte/icons/alert-circle";
  import Info from "@lucide/svelte/icons/info";
  import XCircle from "@lucide/svelte/icons/x-circle";
  import X from "@lucide/svelte/icons/x";

  const ui = getClientUi();

  const icons = {
    success: CheckCircle2,
    error: XCircle,
    warning: AlertCircle,
    info: Info
  };

  const colors = {
    success: 'text-emerald-400 border-emerald-500/30 shadow-emerald-900/20',
    error: 'text-red-400 border-red-500/30 shadow-red-900/20',
    warning: 'text-amber-400 border-amber-500/30 shadow-amber-900/20',
    info: 'text-blue-400 border-blue-500/30 shadow-blue-900/20'
  };
</script>

<div class="fixed top-6 left-1/2 -translate-x-1/2 sm:left-auto sm:translate-x-0 sm:right-4 lg:right-[calc((100vw-1200px)/2+1rem)] z-[var(--z-toast)] flex flex-col gap-3 w-full max-w-[calc(100vw-32px)] sm:w-[340px] pointer-events-none">
  {#each ui.toasts as toast (toast.id)}
    {@const Icon = icons[toast.type]}
    <div
      in:fly={{ y: -20, duration: 500, opacity: 0 }}
      out:fade={{ duration: 300 }}
      class="pointer-events-auto relative group"
    >
      <!-- iOS 26 Styled Glassmorphism - Ultra Thin, High Diffusion -->
      <div class="absolute inset-0 bg-white/70 dark:bg-black/70 backdrop-blur-3xl rounded-[22px] border border-white/40 dark:border-white/10 shadow-[0_20px_40px_-10px_rgba(0,0,0,0.15)] transition-all duration-300 group-hover:scale-[1.01]"></div>
      
      <div class="relative px-5 py-3.5 flex items-center gap-4 min-h-[64px]">
        <!-- Status Icon Container -->
        <div class="w-10 h-10 rounded-full bg-white shadow-sm flex items-center justify-center shrink-0 border border-gray-50">
          <Icon class="w-5 h-5 {toast.type === 'success' ? 'text-emerald-500' : toast.type === 'error' ? 'text-red-500' : 'text-blue-500'}" />
        </div>

        <!-- Content Area -->
        <div class="flex-1 min-w-0 pr-2">
          <p class="text-[14px] font-semibold leading-tight text-gray-900 dark:text-white break-words">
            {toast.message}
          </p>
          <p class="text-[11px] text-gray-500 dark:text-gray-400 font-medium mt-0.5">
            {toast.type === 'success' ? 'Thành công' : toast.type === 'error' ? 'Lỗi hệ thống' : 'Thông báo'}
          </p>
        </div>

        <!-- Progress Indicator (iOS 26 Style - Slim Pill) -->
        <div class="absolute bottom-1 left-6 right-6 h-[3px] bg-gray-100/50 dark:bg-white/10 rounded-full overflow-hidden shrink-0 opacity-40">
           <div 
             class="h-full {toast.type === 'success' ? 'bg-emerald-500' : toast.type === 'error' ? 'bg-red-500' : 'bg-blue-500'}"
             style="width: 100%; transition: width {toast.duration}ms linear; width: 0%;"
           ></div>
        </div>
      </div>
    </div>
  {/each}
</div>

<style>
  /* Custom shadow for Elite aesthetic */
  .shadow-2xl {
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  }
</style>
