<script lang="ts">
  import type { Editor } from '@tiptap/core';
  import {
    AlignLeft,
    AlignCenter,
    AlignRight,
    Trash2,
    ImagePlus,
    Type,
    Check
  } from 'lucide-svelte';

  let { editor, onReplace }: { editor: Editor; onReplace: () => void } = $props();

  let showAltInput = $state(false);
  let altText = $state('');

  // Svelte 5 rune to sync external changes defensively
  $effect(() => {
    if (editor && !editor.isDestroyed) {
      altText = editor.getAttributes('image').alt || '';
    }
  });

  function setAlign(alignment: 'left' | 'center' | 'right') {
    if (!editor || editor.isDestroyed) return;
    const currentClass = editor.getAttributes('image').class || '';
    
    // Extract size context
    const hasSmall = currentClass.includes('max-w-[25%]');
    const hasMed = currentClass.includes('max-w-[50%]');
    const sizeClass = hasSmall ? 'max-w-[25%]' : hasMed ? 'max-w-[50%]' : 'max-w-full';
    
    const alignClass = alignment === 'center' ? 'mx-auto' : alignment === 'right' ? 'ml-auto mr-0' : 'mr-auto ml-0';
    
    editor.chain().focus().updateAttributes('image', { 
      class: `${sizeClass} my-4 shadow-lg flex ${alignClass}` 
    }).run();
  }

  function setSize(size: 'small' | 'medium' | 'large') {
    if (!editor || editor.isDestroyed) return;
    const currentClass = editor.getAttributes('image').class || '';
    
    // Extract alignment context
    const hasRight = currentClass.includes('ml-auto');
    const hasLeft = currentClass.includes('mr-auto');
    const alignClass = hasRight ? 'ml-auto mr-0' : (hasLeft && !currentClass.includes('mx-auto') ? 'mr-auto ml-0' : 'mx-auto');

    const sizeClass = size === 'small' ? 'max-w-[25%]' : size === 'medium' ? 'max-w-[50%]' : 'max-w-full';

    editor.chain().focus().updateAttributes('image', { 
      class: `${sizeClass} my-4 shadow-lg flex ${alignClass}` 
    }).run();
  }

  function applyAltText() {
    if (!editor || editor.isDestroyed) return;
    editor.chain().focus().updateAttributes('image', { alt: altText }).run();
    showAltInput = false;
  }

  function deleteImage() {
    if (!editor || editor.isDestroyed) return;
    editor.chain().focus().deleteSelection().run();
  }

  const inactiveBtnClass = "text-white/60 hover:text-white hover:bg-white/10";
</script>

{#if editor}
  <div class="flex flex-col gap-2 p-2 bg-[#18181b]/80 border border-white/10 rounded-2xl shadow-[0_0_50px_-12px_rgba(59,130,246,0.2)] backdrop-blur-xl group">
    
    <!-- Ambient glow under the menu -->
    <div class="absolute inset-0 bg-blue-500/5 blur-xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>

    {#if showAltInput}
      <div class="relative flex items-center gap-2 px-1 animate-in fade-in slide-in-from-top-2">
        <input 
          type="text" 
          bind:value={altText} 
          placeholder="Nhập Alt text..." 
          class="w-48 bg-zinc-900/50 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder:text-zinc-500 outline-none focus:border-blue-500/50 transition-colors"
          onkeydown={(e) => e.key === 'Enter' && applyAltText()}
        />
        <button 
          onclick={applyAltText} 
          class="p-1.5 rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500 hover:text-white transition-all shadow-lg"
          title="Lưu Alt text"
        >
          <Check size={14} />
        </button>
      </div>
    {:else}
      <!-- Main Toolbar -->
      <div class="relative flex items-center gap-1">
        <!-- Alignment -->
        <div class="flex items-center gap-0.5 bg-black/20 rounded-xl p-0.5 border border-white/5">
          <button onclick={() => setAlign('left')} class="p-2 rounded-lg {inactiveBtnClass} transition-all active:scale-90" title="Căn trái"><AlignLeft size={16} /></button>
          <button onclick={() => setAlign('center')} class="p-2 rounded-lg {inactiveBtnClass} transition-all active:scale-90" title="Căn giữa"><AlignCenter size={16} /></button>
          <button onclick={() => setAlign('right')} class="p-2 rounded-lg {inactiveBtnClass} transition-all active:scale-90" title="Căn phải"><AlignRight size={16} /></button>
        </div>

        <div class="w-px h-4 bg-white/10 mx-1"></div>

        <!-- Sizing -->
        <div class="flex items-center gap-0.5 bg-black/20 rounded-xl p-0.5 text-[10px] font-bold uppercase tracking-wider text-white/60 border border-white/5">
          <button onclick={() => setSize('small')} class="px-2.5 py-1.5 rounded-lg hover:bg-white/10 hover:text-white transition-all active:scale-90" title="Nhỏ 25%">S</button>
          <button onclick={() => setSize('medium')} class="px-2.5 py-1.5 rounded-lg hover:bg-white/10 hover:text-white transition-all active:scale-90" title="Vừa 50%">M</button>
          <button onclick={() => setSize('large')} class="px-2.5 py-1.5 rounded-lg hover:bg-white/10 hover:text-white transition-all active:scale-90" title="Lớn 100%">L</button>
        </div>
        
        <div class="w-px h-4 bg-white/10 mx-1"></div>
        
        <!-- Actions -->
        <div class="flex items-center gap-0.5">
            <button onclick={() => showAltInput = true} class="p-2 rounded-lg {inactiveBtnClass} transition-all active:scale-90" title="Thêm tiêu đề Alt"><Type size={16} /></button>
            <button onclick={onReplace} class="p-2 rounded-lg hover:bg-blue-500/20 text-white/60 hover:text-blue-400 transition-all active:scale-90" title="Thay thế ảnh"><ImagePlus size={16} /></button>
            <button onclick={deleteImage} class="p-2 rounded-lg hover:bg-red-500/20 text-white/60 hover:text-red-400 transition-all active:scale-90" title="Xóa ảnh"><Trash2 size={16} /></button>
        </div>
      </div>
    {/if}
  </div>
{/if}

<style>
  @reference "tailwindcss";
</style>
