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

<div class="sticky top-0 z-[100] w-full flex flex-nowrap overflow-x-auto hide-scrollbar items-center gap-2 md:gap-3 px-3 py-2 bg-[#09090b]/80 backdrop-blur-[40px] border-b border-white/10 shadow-[0_20px_40px_-10px_rgba(0,0,0,0.5),inset_0_1px_1px_rgba(255,255,255,0.05)] transition-all duration-500">
  
  <!-- Island: History -->
  <div class="tb-platter">
    <button onclick={() => editor?.chain().focus().undo().run()} class="tb-btn" title="Undo"><UndoIcon size={14} /></button>
    <button onclick={() => editor?.chain().focus().redo().run()} class="tb-btn" title="Redo"><RedoIcon size={14} /></button>
  </div>

  <!-- Island: Typography -->
  <div class="tb-platter hidden sm:flex">
    <div class="relative group">
      <select class="tb-select font-medium" onchange={handleParagraphChange}>
        <option value="p">Paragraph</option>
        <option value="h1">Heading 1</option>
        <option value="h2">Heading 2</option>
        <option value="h3">Heading 3</option>
      </select>
    </div>
    <div class="w-px h-4 bg-white/10 mx-0.5"></div>
    <div class="relative group">
      <select class="tb-select" onchange={handleFontChange}>
        {#each FONTS as font}
          <option value={font}>{font.split(' ')[0]}</option>
        {/each}
      </select>
    </div>
  </div>

  <!-- Island: Formatting (Liquid Active States) -->
  <div class="tb-platter">
    <button onclick={() => editor?.chain().focus().toggleBold().run()} class="tb-btn {editor?.isActive('bold') ? 'active' : ''}" title="Bold"><BoldIcon size={14} /></button>
    <button onclick={() => editor?.chain().focus().toggleItalic().run()} class="tb-btn {editor?.isActive('italic') ? 'active' : ''}" title="Italic"><ItalicIcon size={14} /></button>
    <button onclick={() => editor?.chain().focus().toggleUnderline().run()} class="tb-btn {editor?.isActive('underline') ? 'active' : ''}" title="Underline"><UnderlineIcon size={14} /></button>
    <button onclick={() => editor?.chain().focus().toggleStrike().run()} class="tb-btn {editor?.isActive('strike') ? 'active' : ''}" title="Strike"><StrikethroughIcon size={14} /></button>
  </div>

  <!-- Island: Alignment -->
  <div class="tb-platter">
    <button onclick={() => editor?.chain().focus().setTextAlign('left').run()} class="tb-btn {editor?.isActive({ textAlign: 'left' }) ? 'active' : ''}" title="Align Left"><AlignLeftIcon size={14} /></button>
    <button onclick={() => editor?.chain().focus().setTextAlign('center').run()} class="tb-btn {editor?.isActive({ textAlign: 'center' }) ? 'active' : ''}" title="Align Center"><AlignCenterIcon size={14} /></button>
    <button onclick={() => editor?.chain().focus().setTextAlign('right').run()} class="tb-btn {editor?.isActive({ textAlign: 'right' }) ? 'active' : ''}" title="Align Right"><AlignRightIcon size={14} /></button>
    <button onclick={() => editor?.chain().focus().setTextAlign('justify').run()} class="tb-btn {editor?.isActive({ textAlign: 'justify' }) ? 'active hidden md:flex' : 'hidden md:flex'}" title="Justify"><AlignJustifyIcon size={14} /></button>
  </div>

  <!-- Island: Layout Elements -->
  <div class="tb-platter hidden md:flex">
    <button onclick={() => editor?.chain().focus().toggleBulletList().run()} class="tb-btn {editor?.isActive('bulletList') ? 'active' : ''}" title="Bullet List"><ListIcon size={14} /></button>
    <button onclick={() => editor?.chain().focus().toggleOrderedList().run()} class="tb-btn {editor?.isActive('orderedList') ? 'active' : ''}" title="Ordered List"><ListOrderedIcon size={14} /></button>
    <div class="w-px h-4 bg-white/10 mx-0.5"></div>
    <button onclick={() => editor?.chain().focus().toggleBlockquote().run()} class="tb-btn {editor?.isActive('blockquote') ? 'active' : ''}" title="Quote"><BlockquoteIcon size={14} /></button>
    <button onclick={() => editor?.chain().focus().toggleCodeBlock().run()} class="tb-btn {editor?.isActive('codeBlock') ? 'active' : ''}" title="Code"><CodeIcon size={14} /></button>
    <button onclick={() => editor?.chain().focus().setHorizontalRule().run()} class="tb-btn" title="Divider"><MinusIcon size={14} /></button>
  </div>

  <!-- Island: Media Insert -->
  <div class="tb-platter">
    <button onclick={onOpenImage} class="tb-btn hover:text-blue-400 hover:bg-blue-500/10" title="Insert Image"><ImageIcon size={14} /></button>
    <button onclick={onOpenLink} class="tb-btn hover:text-blue-400 hover:bg-blue-500/10" title="Insert Link"><Link2Icon size={14} /></button>
  </div>

  <!-- Island: Color Rings -->
  <div class="tb-platter bg-transparent border-none shadow-none ring-0 gap-1.5 hidden xl:flex">
    {#each COLORS as color}
      <button
        onclick={() => editor?.chain().focus().setColor(color).run()}
        class="w-4 h-4 rounded-full ring-1 ring-white/20 hover:scale-125 transition-all duration-300 ease-[cubic-bezier(0.23,1,0.32,1)] shadow-[0_2px_10px_rgba(0,0,0,0.5)] cursor-pointer"
        style="background: {color}; box-shadow: inset 0 2px 4px rgba(255,255,255,0.3), 0 2px 10px rgba(0,0,0,0.5);"
        title="Color: {color}"
      ></button>
    {/each}
    <button
      onclick={() => editor?.chain().focus().unsetColor().run()}
      class="w-4 h-4 rounded-full bg-white/5 ring-1 ring-white/20 hover:scale-125 transition-all duration-300 flex items-center justify-center text-[8px] text-white/50 backdrop-blur-md"
      title="Reset color"
    >↺</button>
  </div>

  <!-- Flexible Space -->
  <div class="flex-1"></div>

  <!-- Island: Tools & Actions -->
  {#if toolbarActions.length > 0 || onClean || (annotations && annotations.length > 0)}
    <div class="tb-platter ml-auto">
      {#if annotations && annotations.length > 0}
        <button
          onclick={onClearHighlights}
          class="tb-pill bg-white/5 hover:bg-white/10 text-white/50 hover:text-white"
          title="Xóa tất cả highlights"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
          Highlight
        </button>
      {/if}

      {#if onClean}
        <button
          onclick={onClean}
          class="tb-pill bg-orange-500/10 hover:bg-orange-500/20 text-orange-400 border border-orange-500/20"
          title="Làm sạch: xóa trùng lặp, markdown thừa, rác"
        >
          <SparklesIcon size={12} />
          <span class="hidden sm:inline">Clean</span>
        </button>
      {/if}

      {#if toolbarActions.length > 0}
        <div class="w-px h-4 bg-white/10 mx-1"></div>
        {#each toolbarActions as action, i}
          <div class="relative group/action{i}">
            <button
              onclick={action.disabled ? undefined : action.onclick}
              disabled={action.loading || action.disabled}
              class="tb-pill {action.loading ? 'bg-white/5 text-white/30 cursor-wait' : action.disabled ? 'bg-white/[0.03] text-white/20' : 'bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.4)]'}"
              title={!action.tooltipDetails ? (action.lockedMsg || action.label) : undefined}
            >
              {#if action.loading}
                <span class="inline-block w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              {:else if action.disabled}
                <span class="text-[10px] opacity-60">🔒</span>
              {/if}
              {action.label}
            </button>

            {#if action.tooltipDetails && !action.disabled}
              <div class="absolute top-[calc(100%+12px)] right-0 w-64 bg-[#09090b]/90 backdrop-blur-3xl border border-white/10 rounded-[20px] p-4 shadow-[0_20px_50px_-10px_rgba(0,0,0,0.8)] z-[200] opacity-0 translate-y-3 pointer-events-none transition-all duration-400 ease-[cubic-bezier(0.23,1,0.32,1)] group-hover/action{i}:opacity-100 group-hover/action{i}:translate-y-0 hidden md:block text-left">
                <div class="flex items-center gap-2 mb-2 text-left">
                  {#if action.tooltipDetails.icon}
                    {@const Icon = action.tooltipDetails.icon}
                    <Icon size={16} class={action.tooltipDetails.colorClass || 'text-blue-400'} />
                  {/if}
                  <span class="text-xs font-black uppercase tracking-widest {action.tooltipDetails.colorClass || 'text-blue-400'}">{action.tooltipDetails.title}</span>
                </div>
                <p class="text-[11px] leading-relaxed text-white/60 normal-case tracking-normal text-left">{action.tooltipDetails.description}</p>
              </div>
            {/if}
          </div>
        {/each}
      {/if}
    </div>
  {/if}

</div>

<style>
  @reference "tailwindcss";

  /* The Platter (Island Container) */
  .tb-platter {
    @apply flex items-center gap-0.5 bg-white/[0.04] p-1 rounded-[16px] border border-white/[0.08] shadow-[inset_0_1px_1px_rgba(255,255,255,0.05),0_2px_10px_rgba(0,0,0,0.2)];
  }

  /* Standard Interaction Button */
  .tb-btn {
    @apply flex items-center justify-center w-8 h-8 rounded-[12px] text-white/50 hover:text-white hover:bg-white/10 transition-all duration-300 ease-[cubic-bezier(0.23,1,0.32,1)] active:scale-75 cursor-pointer;
  }

  /* Liquid Active State */
  .tb-btn.active {
    @apply bg-white text-black shadow-[0_0_15px_rgba(255,255,255,0.4)] scale-105;
  }

  /* Typography Glass Selects */
  .tb-select {
    @apply appearance-none bg-transparent text-white/70 text-[11px] px-3 py-1.5 h-8 outline-none cursor-pointer rounded-[12px] hover:bg-white/10 hover:text-white transition-all duration-300;
  }
  .tb-select option {
    @apply bg-zinc-900 text-white;
  }

  /* Modern Pill Action Buttons */
  .tb-pill {
    @apply flex items-center gap-1.5 px-3 py-1.5 rounded-[12px] text-[10px] font-black uppercase tracking-wider transition-all duration-300 ease-[cubic-bezier(0.23,1,0.32,1)] active:scale-[0.85] border border-transparent;
  }

  /* Cross-browser Scrollbar Hiding */
  .hide-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .hide-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
</style>
