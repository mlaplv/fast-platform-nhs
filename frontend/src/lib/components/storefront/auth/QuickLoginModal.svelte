<script lang="ts">
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import QuickLoginModalMobile from './QuickLoginModalMobile.svelte';
  import QuickLoginModalDesktop from './QuickLoginModalDesktop.svelte';

  const ui = getClientUi();
</script>

{#if ui.isMobile}
  <QuickLoginModalMobile />
{:else}
  <QuickLoginModalDesktop />
{/if}
