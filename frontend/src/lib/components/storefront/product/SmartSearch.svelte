<script lang="ts">
  import SmartSearchDesktop from './SmartSearchDesktop.svelte';
  import SmartSearchMobile from './SmartSearchMobile.svelte';

  interface Props {
    variant?: 'desktop' | 'mobile-overlay';
  }

  let { variant = 'desktop' }: Props = $props();
</script>

{#if variant === 'desktop'}
  <SmartSearchDesktop />
{:else}
  <SmartSearchMobile />
{/if}
