<script lang="ts">
    import Menu from "@lucide/svelte/icons/menu";
  import { goto } from '$app/navigation';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import Avatar from './Avatar.svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { loyaltyStore } from '$lib/state/commerce/loyalty.svelte';


  interface Props {
    title: string;
    isMenuOpen: boolean;
  }
  let { title, isMenuOpen = $bindable() }: Props = $props();
  const ui = getClientUi();
</script>

<header
  class="fixed top-0 left-0 w-full bg-white/80 backdrop-blur-2xl border-b border-stone-100/40 transition-all duration-300"
  style="z-index: {Z_INDEX_CLIENT.HEADER}; padding-top: env(safe-area-inset-top);"
>
  <div class="flex items-center justify-between px-2 h-[52px]">
    <button 
      onclick={() => goto('/')} 
      class="w-10 h-10 flex items-center justify-center active:scale-90 transition-transform text-stone-900"
      aria-label="Quay lại"
    >
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M15 19l-7-7 7-7" />
        </svg>
    </button>

    <div class="flex-1 flex flex-col items-center justify-center overflow-hidden px-2">
        <h1 class="text-[14px] font-serif italic text-stone-900 truncate w-full text-center tracking-tight font-bold">
          {title}
        </h1>
        <div class="flex items-center justify-center gap-1.5 opacity-60">
          <span class="text-[7px] font-bold text-stone-500 uppercase tracking-[0.15em] truncate max-w-[100px]">
              {authStore.user?.name || 'Quý khách'}
          </span>
          <span class="text-[8px] font-black text-luxury-copper px-1 border-l border-stone-200">
             {loyaltyStore.data?.available_points ?? (authStore.user?.extra_metadata?.points || 0)} PTS
          </span>
        </div>

    </div>

    <!-- Menu Button -->
    <button 
      onclick={() => isMenuOpen = true} 
      class="w-10 h-10 flex items-center justify-center active:scale-90 transition-transform text-stone-900"
      aria-label="Mở menu"
    >
        <Menu class="w-5 h-5 text-stone-900" strokeWidth={2} />
    </button>
  </div>
</header>


