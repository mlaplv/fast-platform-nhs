<script lang="ts">
  import { liveEditStore } from "$lib/state/commerce/liveEdit.svelte";
  import { fade, fly } from 'svelte/transition';
  import CheckCircle2 from "@lucide/svelte/icons/check-circle-2";
  import AlertCircle from "@lucide/svelte/icons/alert-circle";
  import Info from "@lucide/svelte/icons/info";
  import X from "@lucide/svelte/icons/x";

  import { Z_INDEX_ADMIN } from "$lib/core/constants/zIndex";
  const notification = $derived(liveEditStore.notification);
  const isOpen = $derived(!!notification?.message);

  function close() {
    liveEditStore.notification.message = '';
    liveEditStore.notification.type = null;
  }
</script>

{#if isOpen}
  <div 
    class="fixed top-8 left-1/2 -translate-x-1/2 flex items-center gap-4 px-6 py-4 bg-slate-950/80 backdrop-blur-3xl border border-white/10 rounded-2xl shadow-[0_30px_100px_rgba(0,0,0,0.8)] min-w-[320px] max-w-md pointer-events-auto"
    style:z-index={Z_INDEX_ADMIN.TOAST}
    in:fly={{ y: -40, duration: 800, opacity: 0 }}
    out:fade={{ duration: 400 }}
  >
    <!-- Icon Layer -->
    <div class="flex-shrink-0">
      {#if notification.type === 'success'}
        <div class="relative">
          <CheckCircle2 class="text-emerald-400" size={24} />
          <div class="absolute inset-0 bg-emerald-400 blur-lg opacity-40"></div>
        </div>
      {:else if notification.type === 'alert'}
        <div class="relative">
          <AlertCircle class="text-rose-400" size={24} />
          <div class="absolute inset-0 bg-rose-400 blur-lg opacity-40"></div>
        </div>
      {:else}
        <div class="relative">
          <Info class="text-blue-400" size={24} />
          <div class="absolute inset-0 bg-blue-400 blur-lg opacity-40"></div>
        </div>
      {/if}
    </div>

    <!-- Content -->
    <div class="flex-1 pr-4">
      <h4 class="text-[8px] font-black tracking-[0.3em] text-white/30 mb-1 leading-none">
        SYSTEM_FEEDBACK // V2.2
      </h4>
      <p class="text-sm font-medium text-white/90 leading-snug">
        {notification.message}
      </p>
    </div>

    <!-- Action -->
    <button 
      onclick={close}
      class="p-2 -mr-2 text-white/20 hover:text-white/60 hover:bg-white/5 rounded-xl transition-all"
    >
      <X size={18} />
    </button>
  </div>
{/if}

<style lang="postcss">
  /* High-end glass reflection effect */
  div::after {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, transparent 50%, rgba(255,255,255,0.02) 100%);
    pointer-events: none;
  }
</style>
