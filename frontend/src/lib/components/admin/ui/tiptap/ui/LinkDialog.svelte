<script lang="ts">
  let {
    show = $bindable(),
    currentUrl = '',
    onApply
  }: {
    show: boolean;
    currentUrl: string;
    onApply: (url: string) => void;
  } = $props();

  let linkUrl = $state('');
  
  $effect(() => {
    if (show) linkUrl = currentUrl;
  });

  function handleApply() {
    onApply(linkUrl.trim());
    show = false;
  }
</script>

{#if show}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="fixed inset-0 z-[1000] flex items-center justify-center bg-black/60 backdrop-blur-sm" onclick={() => show = false}>
    <div class="bg-[#1a2233] border border-white/10 p-6 shadow-2xl w-96" onclick={(e) => e.stopPropagation()}>
      <h3 class="text-sm font-bold text-white mb-3">Chèn liên kết</h3>
      <input
        type="url"
        placeholder="https://..."
        bind:value={linkUrl}
        onkeydown={(e) => e.key === 'Enter' && handleApply()}
        class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-white/30 outline-none focus:border-blue-500/50 mb-3"
      />
      <div class="flex gap-2 justify-end">
        <button onclick={() => show = false} class="px-4 py-2 text-xs text-white/60 hover:text-white transition-colors">Hủy</button>
        <button onclick={handleApply} class="px-4 py-2 bg-blue-500 hover:bg-blue-400 text-white text-xs font-bold transition-colors">Áp dụng</button>
      </div>
    </div>
  </div>
{/if}
