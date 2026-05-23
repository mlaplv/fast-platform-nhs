<script lang="ts">
  import { onMount, onDestroy } from 'svelte';

  interface Props {
    initialSeconds: number;
    onComplete?: () => void;
  }

  let { initialSeconds, onComplete }: Props = $props();
  let seconds = $state(0);
  let timer: ReturnType<typeof setInterval>;

  $effect.pre(() => {
    seconds = initialSeconds;
  });

  const hh = $derived(String(Math.floor(seconds / 3600)).padStart(2, '0'));
  const mm = $derived(String(Math.floor((seconds % 3600) / 60)).padStart(2, '0'));
  const ss = $derived(String(seconds % 60).padStart(2, '0'));

  onMount(() => {
    timer = setInterval(() => {
      if (seconds > 0) {
        seconds--;
      } else {
        clearInterval(timer);
        onComplete?.();
      }
    }, 1000);
  });

  onDestroy(() => {
    if (timer) clearInterval(timer);
  });
</script>

<div class="flex items-center gap-1 font-black text-xs">
  <span class="bg-red-600 text-white px-1.5 py-0.5 rounded">{hh}</span>
  <span class="text-red-600">:</span>
  <span class="bg-red-600 text-white px-1.5 py-0.5 rounded">{mm}</span>
  <span class="text-red-600">:</span>
  <span class="bg-red-600 text-white px-1.5 py-0.5 rounded">{ss}</span>
</div>
