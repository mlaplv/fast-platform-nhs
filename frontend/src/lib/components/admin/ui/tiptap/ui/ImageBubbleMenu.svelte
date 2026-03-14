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
    // We target the image node directly
    editor.chain().focus().updateAttributes('image', { 
      class: `max-w-full my-4 shadow-lg flex ${alignment === 'center' ? 'mx-auto' : alignment === 'right' ? 'ml-auto mr-0' : 'mr-auto ml-0'}` 
    }).run();
  }

  function deleteImage() {
    editor.chain().focus().deleteSelection().run();
  }
</script>

{#if editor}
  <div class="flex items-center gap-1 bg-[#1a2233] border border-white/10 rounded-xl px-2 py-1.5 shadow-2xl backdrop-blur-md">
    <button 
      onclick={() => setAlign('left')}
      class="p-2 rounded-lg hover:bg-white/10 text-white/60 hover:text-white transition-all active:scale-90"
      title="Căn trái"
    >
      <AlignLeft size={16} />
    </button>
    <button 
      onclick={() => setAlign('center')}
      class="p-2 rounded-lg hover:bg-white/10 text-white/60 hover:text-white transition-all active:scale-90"
      title="Căn giữa"
    >
      <AlignCenter size={16} />
    </button>
    <button 
      onclick={() => setAlign('right')}
      class="p-2 rounded-lg hover:bg-white/10 text-white/60 hover:text-white transition-all active:scale-90"
      title="Căn phải"
    >
      <AlignRight size={16} />
    </button>
    
    <div class="w-px h-4 bg-white/10 mx-1"></div>
    
    <button 
      onclick={onReplace}
      class="p-2 rounded-lg hover:bg-blue-500/20 text-white/60 hover:text-blue-400 transition-all active:scale-90"
      title="Thay thế ảnh"
    >
      <ImagePlus size={16} />
    </button>

    <div class="w-px h-4 bg-white/10 mx-1"></div>
    
    <button 
      onclick={deleteImage}
      class="p-2 rounded-lg hover:bg-red-500/20 text-white/60 hover:text-red-400 transition-all active:scale-90"
      title="Xóa ảnh"
    >
      <Trash2 size={16} />
    </button>
  </div>
{/if}

<style>
  @reference "tailwindcss";
</style>
