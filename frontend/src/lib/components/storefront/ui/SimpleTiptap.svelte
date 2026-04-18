<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Editor } from '@tiptap/core';
  import StarterKit from '@tiptap/starter-kit';
  import Placeholder from '@tiptap/extension-placeholder';
  import CharacterCount from '@tiptap/extension-character-count';
  import { Bold, Italic, List } from 'lucide-svelte';

  interface Props {
    content?: string;
    placeholder?: string;
    limit?: number;
    variant?: 'light' | 'dark';
    minHeight?: string;
  }

  let {
    content = $bindable(''),
    placeholder = 'Nhập nội dung...',
    limit = 5000,
    variant = 'light',
    minHeight = '160px'
  }: Props = $props();

  let element: HTMLElement;
  let editor = $state.raw<Editor | null>(null);
  let isInternalUpdating = false;

  onMount(() => {
    editor = new Editor({
      element,
      content,
      extensions: [
        StarterKit.configure({
          heading: false,
          codeBlock: false,
          horizontalRule: false,
          blockquote: false,
          strike: false,
          code: false,
        }),
        Placeholder.configure({
          placeholder,
          emptyEditorClass: 'is-editor-empty',
        }),
        CharacterCount.configure({
          limit,
        })
      ],
      editorProps: {
        attributes: {
          class: `focus:outline-none w-full p-0 tiptap-simple-content text-sm leading-relaxed ${variant === 'dark' ? 'text-white' : 'text-gray-900'}`,
          style: `min-height: ${minHeight};`,
        },
      },
      onUpdate: () => {
        isInternalUpdating = true;
        content = editor!.getHTML();
        setTimeout(() => isInternalUpdating = false, 0);
      },
    });
  });

  onDestroy(() => {
    if (editor) {
      editor.destroy();
    }
  });

  // Keep editor deeply synced if `content` changes from parent (zero-latency)
  $effect(() => {
    if (editor && !isInternalUpdating && content !== editor.getHTML()) {
      const { from, to } = editor.state.selection;
      editor.commands.setContent(content, false);
      try { editor.commands.setTextSelection({ from, to }) } catch(e) {}
    }
  });
</script>

<div 
  class="w-full transition-all rounded-none overflow-hidden relative group {variant === 'dark' ? 'bg-black/40 border-2 border-white/10 focus-within:border-sky-500/50' : 'bg-white border-2 border-gray-100 focus-within:border-black'}"
  data-variant={variant}
>
  <!-- Elite Simple Toolbar -->
  <div class="px-3 py-2 flex items-center gap-1.5 transition-opacity {variant === 'dark' ? 'bg-white/5 border-b border-white/5 opacity-80 group-focus-within:opacity-100' : 'bg-gray-50/50 border-b border-gray-100 opacity-60 group-focus-within:opacity-100'}">
     <button type="button" onclick={() => editor?.chain().focus().toggleBold().run()}
        class="w-7 h-7 flex items-center justify-center rounded-sm transition-colors {variant === 'dark' ? (editor?.isActive('bold') ? 'bg-sky-500/20 text-sky-400' : 'text-gray-400 hover:bg-white/5') : (editor?.isActive('bold') ? 'bg-black/10 text-black' : 'text-gray-500 hover:bg-black/5')}"
        title="In đậm"
     >
        <Bold class="w-3.5 h-3.5" strokeWidth={3} />
     </button>
     <button type="button" onclick={() => editor?.chain().focus().toggleItalic().run()}
        class="w-7 h-7 flex items-center justify-center rounded-sm transition-colors {variant === 'dark' ? (editor?.isActive('italic') ? 'bg-sky-500/20 text-sky-400' : 'text-gray-400 hover:bg-white/5') : (editor?.isActive('italic') ? 'bg-black/10 text-black' : 'text-gray-500 hover:bg-black/5')}"
        title="In nghiêng"
     >
        <Italic class="w-3.5 h-3.5" strokeWidth={3} />
     </button>
      <div class="w-px h-4 mx-1 {variant === 'dark' ? 'bg-white/10' : 'bg-gray-200'}"></div>
      <button type="button" onclick={() => editor?.chain().focus().toggleBulletList().run()}
        class="w-7 h-7 flex items-center justify-center rounded-sm transition-colors {variant === 'dark' ? (editor?.isActive('bulletList') ? 'bg-sky-500/20 text-sky-400' : 'text-gray-400 hover:bg-white/5') : (editor?.isActive('bulletList') ? 'bg-black/10 text-black' : 'text-gray-500 hover:bg-black/5')}"
        title="Danh sách"
     >
        <List class="w-4 h-4" strokeWidth={2.5} />
     </button>
  </div>

  <div class="px-5 py-3">
    <div bind:this={element} class="overflow-y-auto custom-scrollbar" style="height: {minHeight};"></div>
  </div>
  
  {#if limit}
    <div class="absolute bottom-3 right-4 text-[10px] text-gray-300 font-black">
      {editor?.storage.characterCount.characters() || 0} / {limit}
    </div>
  {/if}
</div>

<style>
  :global(.tiptap-simple-content.ProseMirror p.is-editor-empty:first-child::before) {
    color: #64748b;
    content: attr(data-placeholder);
    float: left;
    height: 0;
    pointer-events: none;
    font-weight: 500;
  }
  [data-variant="light"] :global(.tiptap-simple-content.ProseMirror p.is-editor-empty:first-child::before) {
    color: #9ca3af;
  }
  :global(.tiptap-simple-content p) {
    margin-bottom: 0.5rem;
  }
  :global(.tiptap-simple-content) {
    outline: none !important;
  }
  :global(.tiptap-simple-content ul) {
    list-style-type: disc !important;
    padding-left: 1.5rem !important;
    margin-top: 0.5rem !important;
    margin-bottom: 0.5rem !important;
  }
  :global(.tiptap-simple-content li p) {
    margin-bottom: 0 !important;
  }
</style>
