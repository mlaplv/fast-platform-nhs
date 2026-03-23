<script lang="ts">
  import type { Editor } from '@tiptap/core';
  import type { ToolbarAction, EditorAnnotation } from '$lib/types';
  import BoldIcon from 'lucide-svelte/icons/bold';
  import ItalicIcon from 'lucide-svelte/icons/italic';
  import UnderlineIcon from 'lucide-svelte/icons/underline';
  import ListIcon from 'lucide-svelte/icons/list';
  import ListOrderedIcon from 'lucide-svelte/icons/list-ordered';
  import UndoIcon from 'lucide-svelte/icons/undo';
  import RedoIcon from 'lucide-svelte/icons/redo';
  import StrikethroughIcon from 'lucide-svelte/icons/strikethrough';
  import AlignLeftIcon from 'lucide-svelte/icons/align-left';
  import AlignCenterIcon from 'lucide-svelte/icons/align-center';
  import AlignRightIcon from 'lucide-svelte/icons/align-right';
  import AlignJustifyIcon from 'lucide-svelte/icons/align-justify';
  import ImageIcon from 'lucide-svelte/icons/image';
  import Link2Icon from 'lucide-svelte/icons/link-2';
  import BlockquoteIcon from 'lucide-svelte/icons/quote';
  import CodeIcon from 'lucide-svelte/icons/code';
  import MinusIcon from 'lucide-svelte/icons/minus';
  import SparklesIcon from 'lucide-svelte/icons/sparkles';

  let {
    editor,
    toolbarActions = [],
    annotations = [],
    onOpenImage,
    onOpenLink,
    onClearHighlights,
    onClean = null,
    fullScreen = false,
    onToggleFullScreen = null,
  }: {
    editor: Editor | null;
    toolbarActions?: ToolbarAction[];
    annotations?: EditorAnnotation[];
    onOpenImage: () => void;
    onOpenLink: () => void;
    onClearHighlights: () => void;
    onClean?: (() => void) | null;
    fullScreen?: boolean;
    onToggleFullScreen?: (() => void) | null;
  } = $props();

  const FONTS = ['Inter', 'Roboto', 'Georgia', 'Times New Roman', 'Courier New', 'Arial'];
  const COLORS = ['#ffffff', '#93c5fd', '#86efac', '#fde68a', '#fca5a5', '#c4b5fd', '#67e8f9', '#fb923c'];

  function handleParagraphChange(e: Event) {
    const val = (e.target as HTMLSelectElement).value;
    if (val === 'p') editor?.chain().focus().setParagraph().run();
    else if (val === 'h1') editor?.chain().focus().toggleHeading({ level: 1 }).run();
    else if (val === 'h2') editor?.chain().focus().toggleHeading({ level: 2 }).run();
    else if (val === 'h3') editor?.chain().focus().toggleHeading({ level: 3 }).run();
  }

  function handleFontChange(e: Event) {
    editor?.chain().focus().setFontFamily((e.target as HTMLSelectElement).value).run();
  }
</script>

<div class="sticky top-0 z-[100] w-full flex flex-nowrap overflow-x-auto hide-scrollbar items-center gap-2 md:gap-3 px-4 py-1 bg-white/[0.03] backdrop-blur-[80px] border-b border-white/5 shadow-xl transition-all duration-700">
  
  <!-- Island: Navigation & History -->
  <div class="tb-platter group/history">
    <button onclick={() => editor?.chain().focus().undo().run()} class="tb-btn" title="Undo"><UndoIcon size={13} /></button>
    <button onclick={() => editor?.chain().focus().redo().run()} class="tb-btn" title="Redo"><RedoIcon size={13} /></button>
    {#if onToggleFullScreen}
      <button onclick={onToggleFullScreen} class="tb-btn {fullScreen ? 'text-cyan-400' : ''}" title="Toàn màn hình">
        <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 3 6 6"/><path d="m9 21-6-6"/><path d="M21 3v6h-6"/><path d="M3 21v-6h6"/></svg>
      </button>
    {/if}
  </div>

  <!-- Island: Typography (Neural Dropdowns) -->
  <div class="tb-platter hidden lg:flex px-2">
    <select class="tb-select font-black uppercase tracking-widest text-[8px]" onchange={handleParagraphChange}>
      <option value="p">Paragraph</option>
      <option value="h1">Heading 1</option>
      <option value="h2">Heading 2</option>
      <option value="h3">Heading 3</option>
    </select>
    <div class="w-px h-3 bg-white/5 mx-1"></div>
    <select class="tb-select font-mono text-[8px] uppercase tracking-wider" onchange={handleFontChange}>
      {#each FONTS as font}
        <option value={font}>{font}</option>
      {/each}
    </select>
  </div>

  <!-- Island: Formatting (Neural Active States) -->
  <div class="tb-platter">
    <button onclick={() => editor?.chain().focus().toggleBold().run()} class="tb-btn {editor?.isActive('bold') ? 'active-neural' : ''}" title="Bold"><BoldIcon size={13} /></button>
    <button onclick={() => editor?.chain().focus().toggleItalic().run()} class="tb-btn {editor?.isActive('italic') ? 'active-neural' : ''}" title="Italic"><ItalicIcon size={13} /></button>
    <button onclick={() => editor?.chain().focus().toggleUnderline().run()} class="tb-btn {editor?.isActive('underline') ? 'active-neural' : ''}" title="Underline"><UnderlineIcon size={13} /></button>
    <button onclick={() => editor?.chain().focus().toggleStrike().run()} class="tb-btn {editor?.isActive('strike') ? 'active-neural' : ''}" title="Strike"><StrikethroughIcon size={13} /></button>
  </div>

  <!-- Island: Media & Links (Hyper-vibrant) -->
  <div class="tb-platter border-cyan-500/10 bg-cyan-500/[0.02]">
    <button onclick={onOpenImage} class="tb-btn text-cyan-400/60 hover:text-cyan-400" title="Insert Media"><ImageIcon size={13} /></button>
    <button onclick={onOpenLink} class="tb-btn text-cyan-400/60 hover:text-cyan-400" title="Link System"><Link2Icon size={13} /></button>
  </div>

  <!-- Island: Neural Color System -->
  <div class="tb-platter gap-0.5 px-1.5 min-w-[120px]">
    {#each COLORS as color}
      <button 
        onclick={() => editor?.chain().focus().setColor(color).run()} 
        class="w-4 h-4 rounded-full border border-white/10 transition-transform active:scale-75 hover:scale-125 cursor-pointer" 
        style="background: {color};"
        title={color}
      ></button>
    {/each}
    <div class="w-px h-3 bg-white/5 mx-1"></div>
    <button 
      onclick={() => editor?.chain().focus().unsetColor().run()} 
      class="tb-btn !w-6 !h-6 opacity-60 hover:opacity-100" 
      title="Reset Color"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3l18 18"/><path d="M21 3L3 21"/></svg>
    </button>
  </div>

  <!-- Flexible Space -->
  <div class="flex-1"></div>

  <!-- Island: Intelligence & Actions -->
  <div class="flex items-center gap-2">
    {#if onClean}
      <button
        onclick={onClean}
        class="tb-neural-action bg-orange-500/10 text-orange-400 border-orange-500/20 hover:bg-orange-500 hover:text-white"
        title="Neural Clean: Optimize content flow"
      >
        <SparklesIcon size={11} class="animate-pulse" />
        <span class="hidden xl:inline text-[9px]">Neural Clean</span>
      </button>
    {/if}

    {#if toolbarActions.length > 0}
      {#each toolbarActions as action, i}
        <button
          onclick={action.disabled ? undefined : action.onclick}
          disabled={action.loading || action.disabled}
          class="tb-neural-action {action.loading ? 'loading' : action.disabled ? 'disabled' : 'bg-cyan-500 text-black font-black'}"
        >
          {#if action.loading}
            <div class="w-2.5 h-2.5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
          {/if}
          <span class="text-[9px]">{action.label}</span>
        </button>
      {/each}
    {/if}
  </div>

</div>

<style>
  @reference "tailwindcss";

  .tb-platter {
    @apply flex items-center gap-1 bg-white/[0.03] p-1 rounded-xl border border-white/10 shadow-xl backdrop-blur-md transition-all duration-300;
  }

  .tb-btn {
    @apply flex items-center justify-center w-8 h-8 rounded-lg text-white/30 hover:text-white hover:bg-white/5 transition-all duration-500 active:scale-90 cursor-pointer;
  }

  .active-neural {
    @apply bg-cyan-500 text-black shadow-[0_0_15px_rgba(6,182,212,0.4)] scale-105 border border-cyan-400/20;
  }

  .tb-select {
    @apply appearance-none bg-transparent text-white/40 px-2 py-1 h-8 outline-none cursor-pointer rounded-lg hover:bg-white/5 hover:text-white transition-all duration-500;
  }

  .tb-neural-action {
    @apply flex items-center gap-1.5 px-4 py-2 rounded-lg text-[9px] uppercase tracking-[0.15em] transition-all duration-500 active:scale-95 border border-white/10 shadow-2xl;
  }

  .tb-neural-action.loading { @apply bg-white/5 text-white/20 cursor-wait; }
  .tb-neural-action.disabled { @apply opacity-30 grayscale; }

  .hide-scrollbar::-webkit-scrollbar { display: none; }
  .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
