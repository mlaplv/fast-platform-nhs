<script lang="ts">
  import { Menu } from 'lucide-svelte';

  interface Props {
    title: string;
    isMenuOpen: boolean;
  }
  let { title, isMenuOpen = $bindable() }: Props = $props();
</script>

<header class="fixed top-0 left-0 w-full z-[var(--z-header)] flex items-center justify-between p-2 bg-white/90 backdrop-blur-md border-b border-gray-100 h-[48px]">
    <button onclick={() => history.back()} class="w-10 h-10 flex items-center justify-center">
        <svg class="w-6 h-6 text-gray-900" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" /></svg>
    </button>
    <h1 class="text-sm font-black text-gray-900 uppercase italic tracking-widest">{title}</h1>
    <!-- Menu Button -->
    <button onclick={() => isMenuOpen = true} class="w-10 h-10 flex items-center justify-center">
        <Menu class="w-6 h-6 text-gray-900" />
    </button>
</header>
