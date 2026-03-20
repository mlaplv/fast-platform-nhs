<script lang="ts">
  import type { Editor } from '@tiptap/core';
  import {
    AlignLeft,
    AlignCenter,
    AlignRight,
    Trash2,
    ImagePlus,
    Check,
    X
  } from 'lucide-svelte';

  let { editor, onReplace }: { editor: Editor; onReplace: () => void } = $props();

  let altText = $state('');
  let titleText = $state('');

  // Sync from editor on mount / selection change
  $effect(() => {
    if (editor && !editor.isDestroyed) {
      const attrs = editor.getAttributes('image');
      altText = attrs.alt || '';
      titleText = attrs.title || '';
    }
  });

  function setAlign(alignment: 'left' | 'center' | 'right') {
    if (!editor || editor.isDestroyed) return;
    const currentClass = editor.getAttributes('image').class || '';
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
    const hasRight = currentClass.includes('ml-auto');
    const hasLeft = currentClass.includes('mr-auto');
    const alignClass = hasRight ? 'ml-auto mr-0' : (hasLeft && !currentClass.includes('mx-auto') ? 'mr-auto ml-0' : 'mx-auto');
    const sizeClass = size === 'small' ? 'max-w-[25%]' : size === 'medium' ? 'max-w-[50%]' : 'max-w-full';
    editor.chain().focus().updateAttributes('image', { 
      class: `${sizeClass} my-4 shadow-lg flex ${alignClass}` 
    }).run();
  }

  function applyProperties() {
    if (!editor || editor.isDestroyed) return;
    editor.chain().focus().updateAttributes('image', { 
      alt: altText || null, 
      title: titleText || null 
    }).run();
  }

  function deleteImage() {
    if (!editor || editor.isDestroyed) return;
    editor.chain().focus().deleteSelection().run();
  }

  // Auto-apply on blur for convenience
  function handleBlur() {
    applyProperties();
  }

  // Current state helpers
  let currentClass = $derived(editor?.getAttributes('image').class || '');
  let currentAlign = $derived(
    currentClass.includes('ml-auto') && !currentClass.includes('mx-auto') ? 'right'
    : currentClass.includes('mx-auto') ? 'center'
    : 'left'
  );
  let currentSize = $derived(
    currentClass.includes('max-w-[25%]') ? 'small'
    : currentClass.includes('max-w-[50%]') ? 'medium'
    : 'large'
  );
</script>

{#if editor}
  <div class="flex flex-col gap-0 bg-[#18181b]/90 border border-white/10 rounded-2xl shadow-[0_0_50px_-12px_rgba(59,130,246,0.2)] backdrop-blur-xl overflow-hidden min-w-[320px]">
    
    <!-- Row 1: Tools -->
    <div class="flex items-center gap-1 p-2 border-b border-white/5">
      <!-- Alignment -->
      <div class="flex items-center gap-0.5 bg-black/20 rounded-xl p-0.5 border border-white/5">
        <button onclick={() => setAlign('left')} class="p-1.5 rounded-lg transition-all active:scale-90 {currentAlign === 'left' ? 'bg-white/15 text-white' : 'text-white/50 hover:text-white hover:bg-white/10'}" title="Căn trái"><AlignLeft size={14} /></button>
        <button onclick={() => setAlign('center')} class="p-1.5 rounded-lg transition-all active:scale-90 {currentAlign === 'center' ? 'bg-white/15 text-white' : 'text-white/50 hover:text-white hover:bg-white/10'}" title="Căn giữa"><AlignCenter size={14} /></button>
        <button onclick={() => setAlign('right')} class="p-1.5 rounded-lg transition-all active:scale-90 {currentAlign === 'right' ? 'bg-white/15 text-white' : 'text-white/50 hover:text-white hover:bg-white/10'}" title="Căn phải"><AlignRight size={14} /></button>
      </div>

      <div class="w-px h-4 bg-white/10 mx-0.5"></div>

      <!-- Sizing -->
      <div class="flex items-center gap-0.5 bg-black/20 rounded-xl p-0.5 text-[10px] font-bold uppercase tracking-wider border border-white/5">
        <button onclick={() => setSize('small')} class="px-2 py-1 rounded-lg transition-all active:scale-90 {currentSize === 'small' ? 'bg-white/15 text-white' : 'text-white/50 hover:text-white hover:bg-white/10'}" title="25%">S</button>
        <button onclick={() => setSize('medium')} class="px-2 py-1 rounded-lg transition-all active:scale-90 {currentSize === 'medium' ? 'bg-white/15 text-white' : 'text-white/50 hover:text-white hover:bg-white/10'}" title="50%">M</button>
        <button onclick={() => setSize('large')} class="px-2 py-1 rounded-lg transition-all active:scale-90 {currentSize === 'large' ? 'bg-white/15 text-white' : 'text-white/50 hover:text-white hover:bg-white/10'}" title="100%">L</button>
      </div>

      <div class="w-px h-4 bg-white/10 mx-0.5"></div>

      <!-- Actions -->
      <button onclick={onReplace} class="p-1.5 rounded-lg text-white/50 hover:bg-blue-500/20 hover:text-blue-400 transition-all active:scale-90" title="Thay thế ảnh"><ImagePlus size={14} /></button>
      <button onclick={deleteImage} class="p-1.5 rounded-lg text-white/50 hover:bg-red-500/20 hover:text-red-400 transition-all active:scale-90" title="Xóa ảnh"><Trash2 size={14} /></button>
    </div>

    <!-- Row 2: Properties -->
    <div class="flex flex-col gap-1.5 p-2">
      <!-- Alt Text -->
      <div class="flex items-center gap-2">
        <span class="text-[9px] font-bold uppercase tracking-widest text-white/30 w-10 shrink-0">Alt</span>
        <input 
          type="text" 
          bind:value={altText} 
          placeholder="Mô tả hình ảnh cho SEO..."
          onblur={handleBlur}
          onkeydown={(e) => e.key === 'Enter' && applyProperties()}
          class="flex-1 bg-white/5 border border-white/5 rounded-lg px-2.5 py-1 text-[11px] text-white/80 placeholder:text-white/20 outline-none focus:border-blue-500/40 transition-colors"
        />
      </div>
      <!-- Title / Caption -->
      <div class="flex items-center gap-2">
        <span class="text-[9px] font-bold uppercase tracking-widest text-white/30 w-10 shrink-0">Title</span>
        <input 
          type="text" 
          bind:value={titleText} 
          placeholder="Chú thích ảnh (tooltip)..."
          onblur={handleBlur}
          onkeydown={(e) => e.key === 'Enter' && applyProperties()}
          class="flex-1 bg-white/5 border border-white/5 rounded-lg px-2.5 py-1 text-[11px] text-white/80 placeholder:text-white/20 outline-none focus:border-blue-500/40 transition-colors"
        />
      </div>
    </div>
  </div>
{/if}

<style>
  @reference "tailwindcss";
</style>
