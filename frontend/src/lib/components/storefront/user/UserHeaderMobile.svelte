<script lang="ts">
  import { Menu } from 'lucide-svelte';
  import { goto } from '$app/navigation';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import Avatar from './Avatar.svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';

  interface Props {
    title: string;
    isMenuOpen: boolean;
  }
  let { title, isMenuOpen = $bindable() }: Props = $props();
  const ui = getClientUi();
</script>

<header
  class="fixed top-0 left-0 w-full bg-white/90 backdrop-blur-md border-b border-gray-100"
  style="z-index: {Z_INDEX_CLIENT.HEADER}; padding-top: env(safe-area-inset-top);"
>
  <div class="flex items-center justify-between px-2 h-[52px]">
    <button onclick={() => goto('/')} class="w-10 h-10 flex items-center justify-center">
        <svg class="w-6 h-6 text-gray-900" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" /></svg>
    </button>

    <div class="flex-1 flex flex-col items-center justify-center overflow-hidden px-2">
        <h1 class="text-[13px] font-bold uppercase tracking-[2px] text-stone-900 truncate w-full text-center">
          {title}
        </h1>
        <div class="flex items-center gap-2 mt-0.5">
          <Avatar
            src={authStore.user?.avatar_url}
            name={authStore.user?.name}
            size="xs"
            class="!border-none"
          />
          <span class="text-[9px] font-bold text-stone-400 uppercase tracking-widest truncate max-w-[120px]">
              {authStore.user?.name || 'Quý khách'}
          </span>
        </div>
    </div>

    <!-- Menu Button -->
    <button onclick={() => isMenuOpen = true} class="w-10 h-10 flex items-center justify-center">
        <Menu class="w-6 h-6 text-gray-900" />
    </button>
  </div>
</header>
