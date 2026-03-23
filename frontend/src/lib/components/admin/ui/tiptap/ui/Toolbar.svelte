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
  import AlignJustifyIcon from 'lucide-svelte/icons/align-justify';
  import PaletteIcon from 'lucide-svelte/icons/palette';
  import ImageIcon from 'lucide-svelte/icons/image';
  import Link2Icon from 'lucide-svelte/icons/link-2';
  import QuoteIcon from 'lucide-svelte/icons/quote';
  import CodeIcon from 'lucide-svelte/icons/code';
  import MinusIcon from 'lucide-svelte/icons/minus';
  import SparklesIcon from 'lucide-svelte/icons/sparkles';
  import MoreHorizontalIcon from 'lucide-svelte/icons/more-horizontal';
  import { portal } from '$lib/actions/portal';

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
  const COLORS = [
    '#ffffff', '#000000', '#64748b', '#94a3b8', '#cbd5e1', 
    '#ef4444', '#f87171', '#fca5a5', 
    '#f97316', '#fb923c', '#fdba74',
    '#eab308', '#facc15', '#fde68a',
    '#22c55e', '#4ade80', '#86efac',
    '#06b6d4', '#22d3ee', '#67e8f9',
    '#3b82f6', '#60a5fa', '#93c5fd',
    '#8b5cf6', '#a78bfa', '#c4b5fd',
    '#d946ef', '#f0abfc', '#f5d0fe'
  ];

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

  // --- RESPONSIVE LOGIC ---
  let containerRef = $state<HTMLElement | null>(null);
  let colorButtonRef = $state<HTMLElement | null>(null);
  let containerWidth = $state(0);
  let showMore = $state(false);
  let showColorPicker = $state(false);
  
  // Container-based responsive states
  const isThin = $derived(containerWidth < 900); 
  const isCompact = $derived(containerWidth < 700);
  const isSuperCompact = $derived(containerWidth < 500);

</script>

<div 
  bind:this={containerRef}
  bind:clientWidth={containerWidth}
  class="sticky top-0 z-[100] w-full flex flex-nowrap items-center gap-2 md:gap-3 px-4 py-1.5 bg-[#0a0a0a]/90 backdrop-blur-[80px] border-b border-white/5 shadow-2xl transition-all duration-300"
>
  
  <!-- Group 1: Navigation -->
  <div class="tb-platter shrink-0">
    <button onclick={() => editor?.chain().focus().undo().run()} class="tb-btn" title="Undo"><UndoIcon size={12} /></button>
    <button onclick={() => editor?.chain().focus().redo().run()} class="tb-btn" title="Redo"><RedoIcon size={12} /></button>
    {#if onToggleFullScreen && !isCompact}
      <button onclick={onToggleFullScreen} class="tb-btn {fullScreen ? 'text-amber-500' : ''}" title="Toggle Fullscreen">
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>
      </button>
    {/if}
  </div>

  <!-- Group 2: Typography (Main Bar) -->
  {#if !isThin}
    <div class="tb-platter shrink-0 px-2 flex">
      <select class="tb-select font-black uppercase tracking-widest text-[8px]" onchange={handleParagraphChange}>
        <option value="p">Body</option>
        <option value="h1">H1</option>
        <option value="h2">H2</option>
        <option value="h3">H3</option>
      </select>
      <div class="w-px h-3 bg-white/5 mx-1"></div>
      <select class="tb-select font-mono text-[8px] uppercase tracking-wider" onchange={handleFontChange}>
        {#each FONTS as font}
          <option value={font}>{font}</option>
        {/each}
      </select>
    </div>
  {/if}

  <!-- Group 3: Formatting -->
  <div class="tb-platter shrink-0">
    <button onclick={() => editor?.chain().focus().toggleBold().run()} class="tb-btn {editor?.isActive('bold') ? 'active-neural' : ''}" title="Bold"><BoldIcon size={12} /></button>
    {#if !isCompact}
      <button onclick={() => editor?.chain().focus().toggleItalic().run()} class="tb-btn {editor?.isActive('italic') ? 'active-neural' : ''}" title="Italic"><ItalicIcon size={12} /></button>
      <button onclick={() => editor?.chain().focus().toggleUnderline().run()} class="tb-btn {editor?.isActive('underline') ? 'active-neural' : ''}" title="Underline"><UnderlineIcon size={12} /></button>
    {/if}
  </div>

  <!-- Group 4: Media -->
  {#if !isSuperCompact}
    <div class="tb-platter shrink-0 border-cyan-500/10 bg-cyan-500/[0.02]">
      <button onclick={onOpenImage} class="tb-btn text-cyan-400/60 hover:text-cyan-400" title="Image"><ImageIcon size={12} /></button>
      <button onclick={onOpenLink} class="tb-btn text-cyan-400/60 hover:text-cyan-400" title="Link"><Link2Icon size={12} /></button>
    </div>
  {/if}

  <!-- Group 5: Single Color Picker (User Requested) -->
  <div class="shrink-0 relative">
    <button 
      bind:this={colorButtonRef}
      onclick={() => showColorPicker = !showColorPicker}
      class="w-8 h-8 rounded-lg border border-white/10 flex items-center justify-center hover:bg-white/10 hover:border-white/20 active:scale-95 transition-all bg-white/[0.05]"
      title="Color Picker"
    >
      <div class="w-4 h-4 rounded-sm border border-black/50 overflow-hidden relative shadow-sm" style="background: {editor?.getAttributes('textStyle').color || 'white'};">
         <PaletteIcon size={10} class="absolute inset-0 m-auto mix-blend-difference text-white/80" />
      </div>
    </button>

    {#if showColorPicker}
      <div 
           class="absolute top-full right-0 mt-2 z-[1001] bg-[#0d0d0d] border border-white/10 rounded-xl p-3 shadow-[0_20px_50px_rgba(0,0,0,0.5)] flex flex-col gap-3 min-w-[200px]"
      >
        <div class="flex items-center justify-between px-1">
          <span class="text-[8px] font-black uppercase tracking-widest text-white/30">Color Swatches</span>
          <button onclick={() => { editor?.chain().focus().unsetColor().run(); showColorPicker = false; }} class="text-[8px] font-black uppercase text-rose-500/60 hover:text-rose-400">Reset</button>
        </div>
        <div class="grid grid-cols-6 gap-2">
          {#each COLORS as color}
            <button 
              onclick={() => { editor?.chain().focus().setColor(color).run(); showColorPicker = false; }} 
              class="w-5 h-5 rounded-md border border-white/10 hover:scale-125 transition-all shadow-sm" 
              style="background: {color};"
            ></button>
          {/each}
        </div>
      </div>
      <div class="fixed inset-0 z-[1000]" onclick={() => showColorPicker = false}></div>
    {/if}
  </div>

  <!-- Overflow Toggle (The Dropdown - Always Visible for Extras) -->
  <div class="shrink-0 relative">
    <button 
      onclick={() => showMore = !showMore}
      class="tb-btn !bg-white/[0.08] hover:!bg-amber-500/20 border border-white/10 {showMore ? 'text-amber-500 border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.2)]' : ''}"
      title="More Tools"
    >
      <MoreHorizontalIcon size={14} />
    </button>

    {#if showMore}
      <div 
           class="absolute top-full right-0 mt-3 z-[1001] bg-[#0d0d0d]/95 backdrop-blur-3xl border border-white/10 rounded-xl p-3 shadow-[0_30px_60px_rgba(0,0,0,0.8)] flex flex-col gap-3 min-w-[240px]"
      >
        <!-- Extra Tools (Always in More) -->
        <div class="flex flex-col gap-2 p-2 bg-white/5 rounded-lg border border-white/5">
           <span class="text-[7px] font-black uppercase tracking-widest text-white/20 px-1">Extended Tools</span>
           <div class="flex gap-1.5">
             <button onclick={() => { editor?.chain().focus().toggleBlockquote().run(); showMore=false; }} class="tb-btn !h-8 !w-8 {editor?.isActive('blockquote') ? 'active-neural' : ''}"><QuoteIcon size={12}/></button>
             <button onclick={() => { editor?.chain().focus().toggleCode().run(); showMore=false; }} class="tb-btn !h-8 !w-8 {editor?.isActive('code') ? 'active-neural' : ''}"><CodeIcon size={12}/></button>
             <button onclick={() => { editor?.chain().focus().setHorizontalRule().run(); showMore=false; }} class="tb-btn !h-8 !w-8"><MinusIcon size={12}/></button>
           </div>
        </div>

        <!-- Hidden Groups depending on width -->
        {#if isCompact}
           <div class="flex flex-col gap-2 p-2 bg-white/5 rounded-lg border border-white/5">
             <span class="text-[7px] font-black uppercase tracking-widest text-white/20 px-1">Formatting</span>
             <div class="flex gap-1">
               <button onclick={() => { editor?.chain().focus().toggleBold().run(); }} class="tb-btn !h-8 !w-8 {editor?.isActive('bold') ? 'active-neural' : ''}"><BoldIcon size={12}/></button>
               <button onclick={() => { editor?.chain().focus().toggleItalic().run(); }} class="tb-btn !h-8 !w-8 {editor?.isActive('italic') ? 'active-neural' : ''}"><ItalicIcon size={12}/></button>
               <button onclick={() => { editor?.chain().focus().toggleUnderline().run(); }} class="tb-btn !h-8 !w-8 {editor?.isActive('underline') ? 'active-neural' : ''}"><UnderlineIcon size={12}/></button>
               <button onclick={() => { editor?.chain().focus().toggleStrike().run(); }} class="tb-btn !h-8 !w-8 {editor?.isActive('strike') ? 'active-neural' : ''}"><StrikethroughIcon size={12}/></button>
             </div>
           </div>
        {/if}

        {#if isSuperCompact}
          <div class="flex flex-col gap-2 p-2 bg-white/5 rounded-lg border border-white/5">
             <span class="text-[7px] font-black uppercase tracking-widest text-white/20 px-1">Media & Views</span>
             <div class="flex items-center justify-between">
                <div class="flex gap-1">
                  <button onclick={onOpenImage} class="tb-btn !h-8 !w-8"><ImageIcon size={12}/></button>
                  <button onclick={onOpenLink} class="tb-btn !h-8 !w-8"><Link2Icon size={12}/></button>
                </div>
                <div class="w-px h-6 bg-white/10 mx-2"></div>
                <button onclick={onToggleFullScreen} class="tb-btn !h-8 !w-8 {fullScreen ? 'text-amber-500' : ''}"><SparklesIcon size={12}/></button>
             </div>
          </div>
        {/if}

        {#if isThin}
          <div class="flex flex-col gap-2 p-2 bg-white/5 rounded-lg border border-white/5">
             <span class="text-[7px] font-black uppercase tracking-widest text-white/20 px-1">Typography</span>
             <div class="flex gap-2">
                <select class="tb-select !bg-black/60 border border-white/5 !flex-1 !h-9 !text-[8px]" onchange={handleParagraphChange}>
                  <option value="p">Body Text</option>
                  <option value="h1">Heading 1</option>
                  <option value="h2">Heading 2</option>
                  <option value="h3">Heading 3</option>
                </select>
                <select class="tb-select !bg-black/60 border border-white/5 !flex-1 !h-9 !text-[8px]" onchange={handleFontChange}>
                   {#each FONTS as font} <option value={font}>{font}</option> {/each}
                </select>
             </div>
          </div>
        {/if}
      </div>
      <div class="fixed inset-0 z-[1000]" onclick={() => showMore = false}></div>
    {/if}
  </div>

  <!-- Flexible Space -->
  <div class="flex-1"></div>

  <!-- Island: Intelligence & Actions -->
  <div class="flex items-center gap-2">
    {#if onClean}
      <button
        onclick={onClean}
        class="tb-neural-action bg-orange-500/10 text-orange-400 border-orange-500/20 hover:bg-orange-500 hover:text-white group"
        title="Neural Clean"
      >
        <SparklesIcon size={11} class="animate-pulse" />
        <span class="{isThin ? 'hidden' : 'inline'} text-[9px]">Neural Clean</span>
      </button>
    {/if}

    {#if toolbarActions.length > 0}
      {#each toolbarActions.slice(0, isCompact ? (isSuperCompact ? 0 : 1) : toolbarActions.length) as action, i}
        <button
          onclick={action.disabled ? undefined : action.onclick}
          disabled={action.loading || action.disabled}
          class="tb-neural-action {action.loading ? 'loading' : action.disabled ? 'disabled' : 'bg-cyan-500 text-black font-black'} {!isThin && action.label.length > 10 ? 'px-6' : 'px-4'}"
        >
          {#if action.loading}
            <div class="w-2.5 h-2.5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
          {/if}
          <span class="text-[9px] {isThin && toolbarActions.length > 1 ? 'hidden' : 'inline'}">{action.label}</span>
          {#if isThin && toolbarActions.length > 1}
             <SparklesIcon size={10} />
          {/if}
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
