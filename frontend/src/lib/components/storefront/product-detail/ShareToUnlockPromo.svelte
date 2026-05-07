<script lang="ts">
  /**
   * @deprecated Use ShareToUnlockPromoDesktop or ShareToUnlockPromoMobile directly.
   * This wrapper is maintained for backward compatibility during the Elite V2.2 migration.
   */
  import ShareToUnlockPromoDesktop from './ShareToUnlockPromoDesktop.svelte';
  import ShareToUnlockPromoMobile from './ShareToUnlockPromoMobile.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import type { Product } from '$lib/types';

  interface Props {
    product: Product;
    compact?: boolean;
    variant?: 'bar' | 'floating' | 'funnel';
    onUnlock?: () => void;
  }

  let { product, compact = false, variant = 'bar', onUnlock }: Props = $props();
  const ui = getClientUi();

  // Smart resolution for legacy calls
  const resolvedVariant = $derived(variant);
  const isMobileTarget = $derived(resolvedVariant === 'floating' || resolvedVariant === 'funnel' || ui.isMobile);
</script>

{#if isMobileTarget}
  <ShareToUnlockPromoMobile 
    {product} 
    {compact} 
    variant={resolvedVariant === 'funnel' ? 'funnel' : 'floating'} 
    {onUnlock} 
  />
{:else}
  <ShareToUnlockPromoDesktop 
    {product} 
    {compact} 
    {onUnlock} 
  />
{/if}
