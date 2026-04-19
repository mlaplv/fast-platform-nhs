<script lang="ts">
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  const shopStore = getShopStore();
  const timeLeft = $derived(shopStore.timeLeft);
  const mkt = $props<{ timer_prefix: string }>();

  const formatTime = (s: number): string => {
    const mins = Math.floor(s / 60);
    const secs = (s % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };
</script>

<div class="elite-status-pill px-8 py-2 shadow-[0_0_20px_rgba(255,183,197,0.1)]">
  <span class="w-2 h-2 rounded-full bg-luxury-sakura mr-3 shadow-[0_0_8px_var(--luxury-sakura)]"></span>
  <span class="text-[10px] uppercase tracking-[0.4em]">{mkt.timer_prefix}</span>
  <span class="font-black tabular-nums text-white text-[10px] tracking-[0.4em]">{formatTime(timeLeft)}</span>
</div>
