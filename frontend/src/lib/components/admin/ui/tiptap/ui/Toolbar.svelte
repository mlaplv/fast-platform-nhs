<script lang="ts">
  import type { Editor } from '@tiptap/core';
  import type { ToolbarAction } from '$lib/types';
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

  let { 
    editor, 
    toolbarActions = [], 
    annotations = [],
    onOpenImage,
    onOpenLink,
    onClearHighlights
  }: {
    editor: Editor | null;
    toolbarActions?: ToolbarAction[];
    annotations?: any[];
    onOpenImage: () => void;
    onOpenLink: () => void;
    onClearHighlights: () => void;
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

<div class="flex flex-wrap items-center gap-0.5 px-2 py-1.5 bg-white/[0.03] border-b border-white/5 pb-2">
  <!-- History -->
  <button onclick={() => editor?.chain().focus().undo().run()} class="tb-btn" title="Undo"><UndoIcon size={13} /></button>
  <button onclick={() => editor?.chain().focus().redo().run()} class="tb-btn" title="Redo"><RedoIcon size={13} /></button>
  <div class="tb-divider"></div>

  <!-- Paragraph Style -->
  <select
    class="bg-white/5 text-white/70 text-xs border border-white/10 rounded px-2 py-0.5 h-6 mr-1 outline-none focus:border-blue-500/50 cursor-pointer"
    onchange={handleParagraphChange}
  >
    <option value="p">Paragraph</option>
    <option value="h1">Heading 1</option>
    <option value="h2">Heading 2</option>
    <option value="h3">Heading 3</option>
  </select>

  <!-- Font family -->
  <select
    class="bg-white/5 text-white/70 text-xs border border-white/10 rounded px-2 py-0.5 h-6 mr-1 outline-none focus:border-blue-500/50 cursor-pointer"
    onchange={handleFontChange}
  >
    {#each FONTS as font}
      <option value={font}>{font}</option>
    {/each}
  </select>

  <div class="tb-divider"></div>

  <!-- Formatting -->
  <button onclick={() => editor?.chain().focus().toggleBold().run()} class="tb-btn {editor?.isActive('bold') ? 'active' : ''}" title="Bold (Ctrl+B)"><BoldIcon size={13} /></button>
  <button onclick={() => editor?.chain().focus().toggleItalic().run()} class="tb-btn {editor?.isActive('italic') ? 'active' : ''}" title="Italic (Ctrl+I)"><ItalicIcon size={13} /></button>
  <button onclick={() => editor?.chain().focus().toggleUnderline().run()} class="tb-btn {editor?.isActive('underline') ? 'active' : ''}" title="Underline (Ctrl+U)"><UnderlineIcon size={13} /></button>
  <button onclick={() => editor?.chain().focus().toggleStrike().run()} class="tb-btn {editor?.isActive('strike') ? 'active' : ''}" title="Strikethrough"><StrikethroughIcon size={13} /></button>

  <div class="tb-divider"></div>

  <!-- Text alignment -->
  <button onclick={() => editor?.chain().focus().setTextAlign('left').run()} class="tb-btn {editor?.isActive({ textAlign: 'left' }) ? 'active' : ''}" title="Align Left"><AlignLeftIcon size={13} /></button>
  <button onclick={() => editor?.chain().focus().setTextAlign('center').run()} class="tb-btn {editor?.isActive({ textAlign: 'center' }) ? 'active' : ''}" title="Align Center"><AlignCenterIcon size={13} /></button>
  <button onclick={() => editor?.chain().focus().setTextAlign('right').run()} class="tb-btn {editor?.isActive({ textAlign: 'right' }) ? 'active' : ''}" title="Align Right"><AlignRightIcon size={13} /></button>
  <button onclick={() => editor?.chain().focus().setTextAlign('justify').run()} class="tb-btn {editor?.isActive({ textAlign: 'justify' }) ? 'active' : ''}" title="Justify"><AlignJustifyIcon size={13} /></button>

  <div class="tb-divider"></div>

  <!-- Lists -->
  <button onclick={() => editor?.chain().focus().toggleBulletList().run()} class="tb-btn {editor?.isActive('bulletList') ? 'active' : ''}" title="Bullet List"><ListIcon size={13} /></button>
  <button onclick={() => editor?.chain().focus().toggleOrderedList().run()} class="tb-btn {editor?.isActive('orderedList') ? 'active' : ''}" title="Ordered List"><ListOrderedIcon size={13} /></button>

  <div class="tb-divider"></div>

  <!-- Insert -->
  <button onclick={onOpenImage} class="tb-btn" title="Insert Image"><ImageIcon size={13} /></button>
  <button title="Insert Link" onclick={onOpenLink} class="tb-btn"><Link2Icon size={13} /></button>
  <button onclick={() => editor?.chain().focus().toggleBlockquote().run()} class="tb-btn {editor?.isActive('blockquote') ? 'active' : ''}" title="Blockquote"><BlockquoteIcon size={13} /></button>
  <button onclick={() => editor?.chain().focus().toggleCodeBlock().run()} class="tb-btn {editor?.isActive('codeBlock') ? 'active' : ''}" title="Code Block"><CodeIcon size={13} /></button>
  <button onclick={() => editor?.chain().focus().setHorizontalRule().run()} class="tb-btn" title="Horizontal Rule"><MinusIcon size={13} /></button>

  <div class="tb-divider"></div>

  <!-- Text Color -->
  <div class="flex items-center gap-0.5 mr-1">
    {#each COLORS as color}
      <button
        onclick={() => editor?.chain().focus().setColor(color).run()}
        class="w-4 h-4 border border-white/20 hover:scale-110 transition-transform shadow-inner"
        style="background: {color}"
        title="Text color: {color}"
      ></button>
    {/each}
    <button
      onclick={() => editor?.chain().focus().unsetColor().run()}
      class="w-4 h-4 border border-white/20 hover:scale-110 transition-transform text-[8px] text-white/50 flex items-center justify-center"
      title="Reset color"
    >↺</button>
  </div>

  <!-- Custom Toolbar Actions -->
  {#if toolbarActions.length > 0}
    <div class="tb-divider ml-auto"></div>
    {#each toolbarActions as action}
      <button
        onclick={action.disabled ? undefined : action.onclick}
        disabled={action.loading || action.disabled}
        class="flex items-center gap-1 px-2 py-0.5 text-[9px] font-black uppercase tracking-wide border transition-all
          {action.loading
            ? 'bg-white/5 border-white/10 text-white/30 cursor-wait'
            : action.disabled
              ? 'bg-white/[0.03] border-white/5 text-white/20 cursor-not-allowed opacity-50'
              : 'bg-white/5 hover:bg-white/10 border-white/10 text-white/60 hover:text-white active:scale-95'}"
        title={action.lockedMsg || action.label}
      >
        {#if action.loading}
          <span class="inline-block w-2.5 h-2.5 border border-white/30 border-t-transparent rounded-full animate-spin"></span>
        {:else if action.disabled}
          <span class="text-[8px] opacity-60">🔒</span>
        {/if}
        {action.label}
      </button>
    {/each}
  {/if}

  <!-- Clear Highlights -->
  {#if annotations && annotations.length > 0}
    <div class="tb-divider ml-auto"></div>
    <button
      onclick={onClearHighlights}
      class="flex items-center gap-1 px-2 py-0.5 text-[9px] font-black uppercase tracking-wide border transition-all bg-white/5 hover:bg-white/10 border-white/10 text-white/40 hover:text-white active:scale-95"
      title="Xóa tất cả highlights"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
      Xóa Highlight
    </button>
  {/if}
</div>

<style>
  @reference "tailwindcss";
  .tb-btn {
    @apply p-1.5 rounded-md text-white/40 hover:text-white hover:bg-white/5 transition-all active:scale-90;
  }
  .tb-btn.active {
    @apply text-blue-400 bg-blue-500/10 border border-blue-500/20;
  }
  .tb-divider {
    @apply w-px h-4 bg-white/10 mx-1;
  }
</style>
