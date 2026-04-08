<script lang="ts">
  import { X } from "lucide-svelte";
  import { fade, scale } from "svelte/transition";
  import { onMount } from "svelte";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";

  interface Props {
    imageUrl: string | null;
    onClose: () => void;
  }

  let { imageUrl = $bindable(), onClose }: Props = $props();
  let mounted = $state(false);

  onMount(() => {
    mounted = true;
  });
</script>

{#if imageUrl && mounted}
  <div
    class="fixed inset-0 flex items-center justify-center p-4 bg-black/90 backdrop-blur-xl"
    style="z-index: {Z_INDEX_ADMIN.MODAL}"
    transition:fade
  >
    <button
      onclick={onClose}
      class="absolute top-8 right-8 p-3 bg-white/10 hover:bg-white/20 text-white rounded-full transition-all border border-white/10"
    >
      <X size={24} />
    </button>
    <img
      src={imageUrl}
      alt="Preview"
      class="max-w-full max-h-full object-contain rounded-2xl shadow-2xl"
      transition:scale={{ duration: 300, start: 0.9 }}
    />
  </div>
{/if}
