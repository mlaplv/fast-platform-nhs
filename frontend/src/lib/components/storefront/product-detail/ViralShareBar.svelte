<script lang="ts">
  /**
   * @deprecated Use ViralShareBarDesktop or ViralShareBarMobile directly.
   * This wrapper is maintained for backward compatibility during the Elite V2.2 migration.
   */
  import ViralShareBarDesktop from './ViralShareBarDesktop.svelte';
  import ViralShareBarMobile from './ViralShareBarMobile.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import type { Product } from '$lib/types';

  interface Props {
    product: Product;
    variant?: 'desktop' | 'mobile' | 'funnel';
    onShareComplete?: () => void;
    likeCount?: number;
    hideLikes?: boolean;
    dark?: boolean;
  }

  let { 
    product, 
    variant = 'desktop', 
    onShareComplete, 
    likeCount = 0, 
    hideLikes = false,
    dark = false
  }: Props = $props();

  const ui = getClientUi();
  const isMobileTarget = $derived(variant === 'mobile' || variant === 'funnel' || ui.isMobile);
</script>

{#if isMobileTarget}
  <ViralShareBarMobile 
    {product} 
    variant={variant === 'funnel' ? 'funnel' : 'mobile'}
    {onShareComplete}
    {likeCount}
    {hideLikes}
    {dark}
  />
{:else}
  <ViralShareBarDesktop 
    {product} 
    {onShareComplete}
    {likeCount}
    {hideLikes}
    {dark}
  />
{/if}
