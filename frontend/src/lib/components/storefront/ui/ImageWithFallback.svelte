<script lang="ts">
  import { resolveMediaUrl } from "$lib/state/utils";

  let { 
    src, 
    alt = "image", 
    class: className = "", 
    aspectRatio = "aspect-video"
  } = $props<{
    src?: string | null;
    alt?: string;
    class?: string;
    aspectRatio?: string;
  }>();

  let isError = $state(false);
  const finalSrc = $derived(!src || isError ? null : resolveMediaUrl(src));

  function handleError() {
    isError = true;
  }
</script>

<div class="relative overflow-hidden bg-gray-50 {aspectRatio} {className}">
  {#if finalSrc}
    <img
      src={finalSrc}
      {alt}
      class="w-full h-full object-cover transition-transform duration-700"
      onerror={handleError}
      loading="lazy"
    />
  {:else}
    <div class="absolute inset-0 flex flex-col items-center justify-center bg-gray-100/50 text-gray-300">
      <svg
        class="w-12 h-12 mb-2 opacity-20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <rect width="18" height="18" x="3" y="3" rx="2" ry="2" />
        <circle cx="9" cy="9" r="2" />
        <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
      </svg>
      <span class="text-[8px] font-black uppercase tracking-[0.2em] opacity-30">No Image Available</span>
    </div>
  {/if}
</div>
