<script lang="ts">
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { fly, fade } from 'svelte/transition';
  import { 
    CheckCircle2, 
    AlertCircle, 
    Info, 
    XCircle,
    X
  } from 'lucide-svelte';

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

<div class="fixed top-24 right-4 z-[var(--z-toast)] flex flex-col gap-4 w-85 pointer-events-none">
  {#each ui.toasts as toast (toast.id)}
    {@const Icon = icons[toast.type]}
    <div
      in:fly={{ x: 50, duration: 400 }}
      out:fade={{ duration: 200 }}
      class="pointer-events-auto relative group"
    >
      <!-- Premium Glass Background - High Contrast Dark Liquid -->
      <div class="absolute inset-0 bg-black/90 backdrop-blur-3xl rounded-xl border-t border-l border-white/10 {colors[toast.type]} shadow-[0_30px_60px_-15px_rgba(0,0,0,0.6)] transition-all duration-300 group-hover:scale-[1.02]"></div>
      
      <div class="relative px-5 py-4 flex items-start gap-4">
        <!-- Status Icon -->
        <div class="mt-0.5 shrink-0">
          <Icon class="w-5 h-5 drop-shadow-sm" />
        </div>

        <!-- Content -->
        <div class="flex-1 min-w-0 flex flex-col justify-center min-h-[40px]">
          <p class="text-[13px] font-bold leading-normal text-white break-words overflow-hidden line-clamp-3">
            {toast.message}
          </p>
          <div class="mt-2.5 h-1 bg-white/10 rounded-full overflow-hidden shrink-0">
             <div 
               class="h-full {toast.type === 'success' ? 'bg-emerald-500' : toast.type === 'error' ? 'bg-red-500' : 'bg-blue-500'} shadow-[0_0_8px_currentColor]"
               style="width: 100%; transition: width {toast.duration}ms linear; width: 0%;"
             ></div>
          </div>
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
