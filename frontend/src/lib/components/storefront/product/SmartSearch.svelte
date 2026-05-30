<script lang="ts">
  import { onMount, type Component } from 'svelte';

  interface Props {
    variant?: 'desktop' | 'mobile-overlay';
  }

  let { variant = 'desktop' }: Props = $props();

  let activeComponent = $state<Component<any> | null>(null);

  onMount(async () => {
    try {
      if (variant === 'desktop') {
        const { default: SmartSearchDesktop } = await import('./SmartSearchDesktop.svelte');
        activeComponent = SmartSearchDesktop;
      } else {
        const { default: SmartSearchMobile } = await import('./SmartSearchMobile.svelte');
        activeComponent = SmartSearchMobile;
      }
    } catch (e) {
      console.error('[SmartSearch] Dynamic import failed:', e);
    }
  });
</script>

{#if activeComponent}
  {@const DynamicComponent = activeComponent}
  <DynamicComponent />
{/if}
