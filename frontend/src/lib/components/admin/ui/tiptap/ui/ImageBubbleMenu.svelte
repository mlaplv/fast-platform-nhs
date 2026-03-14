<script lang="ts">
  import type { Editor } from '@tiptap/core';
  import {
    AlignLeft,
    AlignCenter,
    AlignRight,
    Trash2,
    Settings,
    X,
    ImagePlus
  } from 'lucide-svelte';

  let { editor, onReplace }: { editor: Editor; onReplace: () => void } = $props();

  function setAlign(alignment: string) {
    const baseClass = 'max-w-full my-4';
    let alignClass = 'mx-auto block';

    if (alignment === 'left') alignClass = 'mr-auto ml-0 block';
    if (alignment === 'right') alignClass = 'ml-auto mr-0 block';

    editor.chain().focus().updateAttributes('image', {
      class: `${baseClass} ${alignClass}`
    }).run();
  }

  function deleteImage() {
    editor.chain().focus().deleteSelection().run();
  }
</script>

{#if editor}
  <div class="flex items-center gap-1 bg-[#1a2233] border border-white/10 rounded-lg px-1.5 py-1 shadow-lg">
    <button
      onmousedown={(e) => e.preventDefault()}
      onclick={() => setAlign('left')}
      class="p-2 rounded-lg hover:bg-white/10 text-white/60 hover:text-white transition-all active:scale-90 {editor.getAttributes('image').class?.includes('ml-0') ? 'text-blue-400 bg-blue-500/10' : ''}"
      title="Căn trái"
    >
      <AlignLeft size={16} />
    </button>
    <button
      onmousedown={(e) => e.preventDefault()}
      onclick={() => setAlign('center')}
      class="p-2 rounded-lg hover:bg-white/10 text-white/60 hover:text-white transition-all active:scale-90 {editor.getAttributes('image').class?.includes('mx-auto') ? 'text-blue-400 bg-blue-500/10' : ''}"
      title="Căn giữa"
    >
      <AlignCenter size={16} />
    </button>
    <button
      onmousedown={(e) => e.preventDefault()}
      onclick={() => setAlign('right')}
      class="p-2 rounded-lg hover:bg-white/10 text-white/60 hover:text-white transition-all active:scale-90 {editor.getAttributes('image').class?.includes('mr-0') && !editor.getAttributes('image').class?.includes('mx-auto') ? 'text-blue-400 bg-blue-500/10' : ''}"
      title="Căn phải"
    >
      <AlignRight size={16} />
    </button>

    <div class="w-px h-4 bg-white/10 mx-1"></div>

    <button
      onmousedown={(e) => e.preventDefault()}
      onclick={onReplace}
      class="p-2 rounded-lg hover:bg-blue-500/20 text-white/60 hover:text-blue-400 transition-all active:scale-90"
      title="Thay thế ảnh"
    >
      <ImagePlus size={16} />
    </button>

    <div class="w-px h-4 bg-white/10 mx-1"></div>

    <button
      onmousedown={(e) => e.preventDefault()}
      onclick={deleteImage}
      class="p-2 rounded-lg hover:bg-red-500/20 text-white/60 hover:text-red-400 transition-all active:scale-90"
      title="Xóa ảnh"
    >
      <Trash2 size={16} />
    </button>

    <div class="w-px h-4 bg-white/10 mx-1"></div>

    <div class="flex items-center gap-1 bg-black/20 rounded-lg p-1">
      {#each [25, 50, 75, 100] as size}
        <button
          onmousedown={(e) => e.preventDefault()}
          onclick={() => editor.chain().focus().updateAttributes('image', { width: `${size}%` }).run()}
          class="px-1.5 py-1 text-[10px] font-bold rounded hover:bg-white/10 transition-colors {editor.getAttributes('image').width === `${size}%` ? 'text-blue-400 bg-white/5' : 'text-white/40'}"
        >
          {size}%
        </button>
      {/each}
    </div>
  </div>
{/if}

<style>
  @reference "tailwindcss";
</style>
