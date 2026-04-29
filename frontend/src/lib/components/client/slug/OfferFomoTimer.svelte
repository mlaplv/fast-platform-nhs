<script lang="ts">
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';
  const shopStore = getShopStore();
  const timeLeft = $derived(shopStore.timeLeft);
  const { timer_prefix } = $props<{ timer_prefix: string }>();

  const formatTime = (s: number): string => {
    const mins = Math.floor(s / 60);
    const secs = (s % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };
</script>

<div class="elite-status-pill px-6 py-2 shadow-[0_0_20px_rgba(255,183,197,0.1)] hover:scale-[1.02] transition-transform duration-500">
  <div class="flex items-center gap-2">
    {#if timer_prefix}
      <EditableWrapper path="metadata.offer_timer_prefix" type="text" label="SỬA TIỀN TỐ HẸN GIỜ" class="inline" as="span">
        <span class="text-[9px] uppercase tracking-[0.3em] text-white/60 font-medium">{timer_prefix}</span>
      </EditableWrapper>
    {/if}
    <span class="font-black tabular-nums text-white text-[11px] tracking-[0.2em]">{formatTime(timeLeft)}</span>
  </div>
</div>
