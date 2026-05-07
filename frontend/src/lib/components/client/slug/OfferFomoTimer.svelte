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

<div class="relative inline-flex items-center bg-[#111] border border-white/10 rounded-full px-4 py-1.5 shadow-xl z-10 animate-bounce-slight">
  <div class="flex items-center gap-2">
    {#if timer_prefix}
      <EditableWrapper path="metadata.offer_timer_prefix" type="text" label="SỬA TIỀN TỐ HẸN GIỜ" class="inline" as="span">
        <span class="text-[9px] uppercase tracking-[0.2em] text-white/50 font-medium">{timer_prefix}</span>
      </EditableWrapper>
    {/if}
    <span class="font-black tabular-nums text-[#ffb7c5] text-[11px] tracking-[0.1em] drop-shadow-[0_0_8px_rgba(255,183,197,0.4)]">{formatTime(timeLeft)}</span>
  </div>
  <!-- Tooltip Arrow Pointing Down -->
  <div class="absolute -bottom-[5px] left-1/2 -translate-x-1/2 w-2.5 h-2.5 bg-[#111] border-b border-r border-white/10 rotate-45"></div>
</div>

<style>
  .animate-bounce-slight {
    animation: bounce-slight 3s infinite ease-in-out;
  }
  @keyframes bounce-slight {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-3px); }
  }
</style>
