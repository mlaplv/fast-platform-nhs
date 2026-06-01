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
  class="fixed top-0 left-0 w-full bg-white border-b border-stone-100/40 transition-all duration-300"
  style="z-index: {Z_INDEX_CLIENT.HEADER}; padding-top: env(safe-area-inset-top);"
>
  <div class="flex items-center justify-between px-2 h-[52px]">
    <button 
      onclick={() => goto('/')} 
      class="w-10 h-10 flex items-center justify-center active:scale-90 transition-transform text-stone-800"
      aria-label="Quay lại"
    >
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M15 19l-7-7 7-7" />
        </svg>
    </button>

    <div class="flex-1 flex flex-col items-center justify-center overflow-hidden px-2">
        <h1 class="text-[14px] font-serif italic text-stone-800 truncate w-full text-center tracking-tight font-bold">
          {title}
        </h1>
        <div class="flex items-center justify-center gap-2 mt-0.5">
          <span class="text-[9.5px] font-semibold text-stone-500 tracking-wide truncate max-w-[120px]">
              {authStore.user?.name || 'Quý khách'}
          </span>
          <span class="w-px h-2.5 bg-stone-200"></span>
          <span class="text-[9.5px] font-black text-luxury-copper tracking-wide">
             {loyaltyStore.data?.available_points ?? (authStore.user?.extra_metadata?.points || 0)} {loyaltyStore.data?.point_unit ?? "điểm"}
          </span>
        </div>

    </div>

    <!-- Menu Button -->
    <button 
      onclick={() => isMenuOpen = true} 
      class="w-10 h-10 flex items-center justify-center active:scale-90 transition-transform text-stone-800"
      aria-label="Mở menu"
    >
        <Menu class="w-5 h-5 text-stone-800" strokeWidth={2} />
    </button>
  </div>
</header>


