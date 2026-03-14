<script lang="ts">
  import { onMount, onDestroy, untrack } from 'svelte';
  import { Editor } from '@tiptap/core';
  import { getEditorExtensions, editorProps } from './core/editor-config';
  import { injectAnnotationStyles } from './extensions/AnnotationMark';
  import type { EditorAnnotation, ToolbarAction } from '$lib/types';

  import Toolbar from './ui/Toolbar.svelte';
  import ImageDialog from './ui/ImageDialog.svelte';
  import LinkDialog from './ui/LinkDialog.svelte';
  import StatusBar from './ui/StatusBar.svelte';
  import AnnotationTooltip from './ui/AnnotationTooltip.svelte';

  let {
    content = "",
    onChange = () => {},
    editable = true,
    placeholder = "Start writing...",
    assets = [] as string[],
    fullScreen = false,
    toolbarActions = [] as ToolbarAction[],
    annotations = [] as EditorAnnotation[],
    onfix = null,
    onblur = () => {},
  }: {
    content?: string;
    onChange?: (val: string) => void;
    editable?: boolean;
    placeholder?: string;
    assets?: string[];
    fullScreen?: boolean;
    toolbarActions?: ToolbarAction[];
    annotations?: EditorAnnotation[];
    onfix?: ((snippet: string, type: string, message: string) => Promise<string | null>) | null;
    onblur?: () => void;
  } = $props();

  let editor = $state<Editor | null>(null);
  let element: HTMLElement;
  let isFocused = $state(false);
  let wordCount = $state(0);
  let charCount = $state(0);

  let showImageDialog = $state(false);
  let showLinkDialog = $state(false);
  let currentLinkUrl = $state('');

  // Tooltip tracking
  let tooltipVisible = $state(false);
  let tooltipText = $state('');
  let tooltipSnippet = $state('');
  let tooltipType = $state('');
  let tooltipId = $state('');
  let tooltipX = $state(0);
  let tooltipY = $state(0);
  let isFixing = $state(false);
  let lastTooltipAnchorId = $state('');
  
  const containerClass = $derived(`tiptap-shell flex flex-col w-full h-full ${
    editable 
      ? 'bg-[#0d1117] border ' + (isFocused ? 'border-blue-500/40' : 'border-white/10') + ' overflow-hidden shadow-2xl' 
      : 'bg-transparent border-none overflow-visible'
  } transition-all duration-300 rounded-none`);

  function updateMetrics() {
    if (!editor) return;
    const text = editor.getText();
    charCount = text.length;
    wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  }

  onMount(() => {
    injectAnnotationStyles();
    editor = new Editor({
      element,
      content,
      editable,
      extensions: getEditorExtensions(placeholder),
      editorProps,
      onUpdate: () => {
        onChange(editor?.getHTML() ?? '');
        updateMetrics();
      },
      onFocus: () => isFocused = true,
      onBlur: () => isFocused = false,
    });
    updateMetrics();
  });

  onDestroy(() => {
    if (editor) editor.destroy();
  });

  // Reactive Syncs
  $effect(() => {
    if (editor && !editor.isDestroyed) editor.setEditable(editable);
  });

  $effect(() => {
    if (!editor || editor.isDestroyed) return;
    const normalizedContent = content || "<p></p>";
    if (normalizedContent !== editor.getHTML()) {
      editor.commands.setContent(content, false);
      updateMetrics();
    }
  });

  $effect(() => {
    if (!editor || editor.isDestroyed) return;
    editor.commands.clearAllAnnotations();
    if (!annotations?.length) return;

    const { doc } = editor.state;
    const tr = editor.state.tr;
    let hasChanges = false;

    // Fast pos look-up (Same logic as RichTextEditor.svelte)
    const docChars: { char: string; pos: number }[] = [];
    doc.descendants((node, pos) => {
      if (node.isText && node.text) {
        for (let i = 0; i < node.text.length; i++) {
          const c = node.text[i];
          if (!/[\s\u00A0\u200B\uFEFF]/.test(c)) {
            docChars.push({ char: c.toLowerCase(), pos: pos + i });
          }
        }
      }
    });
    const docStr = docChars.map(c => c.char).join('');

    for (const ann of annotations) {
      if (!ann.text || ann.text.length < 3) continue;
      const searchStr = ann.text.replace(/[\s\u00A0\u200B\uFEFF]+/g, '').toLowerCase();
      let idx = docStr.indexOf(searchStr);
      while (idx !== -1) {
        const startPos = docChars[idx].pos;
        const endPos = docChars[idx + searchStr.length - 1].pos + 1;
        tr.addMark(startPos, endPos, editor.schema.marks.annotation.create({
          id: `ann-${Math.random().toString(36).substring(2, 9)}`,
          type: ann.type,
          message: ann.message,
          source: ann.source || '',
          severity: ann.severity || 'medium',
        }));
        hasChanges = true;
        idx = docStr.indexOf(searchStr, idx + 1);
      }
    }
    if (hasChanges) editor.view.dispatch(tr);
  });

  function handleMouseMove(e: MouseEvent) {
    if (isFixing) return;
    const target = e.target as HTMLElement;
    const annEl = target.closest('.xohi-annotation') as HTMLElement | null;

    if (annEl) {
      const id = annEl.getAttribute('data-annotation-id') || '';
      if (!tooltipVisible || id !== lastTooltipAnchorId) {
        tooltipText = annEl.getAttribute('data-annotation-message') || '';
        tooltipType = annEl.getAttribute('data-annotation-type') || '';
        tooltipId = id;
        tooltipSnippet = annEl.textContent || '';
        lastTooltipAnchorId = id;
        tooltipX = e.clientX;
        tooltipY = e.clientY - 8;
        tooltipVisible = true;
      }
    } else {
        if (!target.closest('.tiptap-tooltip')) {
            tooltipVisible = false;
            lastTooltipAnchorId = '';
        }
    }
  }

  async function handleFix() {
    if (!onfix || isFixing || !tooltipSnippet) return;
    isFixing = true;
    try {
      const newText = await onfix(tooltipSnippet, tooltipType, tooltipText);
      if (newText && editor) {
        let tr = editor.state.tr;
        let found = false;
        editor.state.doc.descendants((node, pos) => {
          if (node.isText) {
            const mark = node.marks.find(m => m.type.name === 'annotation' && m.attrs.id === tooltipId);
            if (mark) {
              tr = tr.insertText(newText, pos, pos + node.nodeSize);
              found = true;
            }
          }
        });
        if (found) editor.view.dispatch(tr);
        tooltipType = 'fixed';
      }
    } finally {
      isFixing = false;
      setTimeout(() => { if (!isFixing) tooltipVisible = false; }, 1500);
    }
  }

</script>

<div 
  class={containerClass}
  onfocusout={(e) => { if (onblur && !e.currentTarget.contains(e.relatedTarget as Node)) onblur(); }}
>
  {#if editable}
    <Toolbar 
      {editor} 
      {toolbarActions} 
      {annotations}
      onOpenImage={() => showImageDialog = true}
      onOpenLink={() => { currentLinkUrl = editor?.getAttributes('link').href || ''; showLinkDialog = true; }}
      onClearHighlights={() => editor?.commands.clearAllAnnotations()}
    />
  {/if}

  <div 
    class="flex-1 overflow-y-auto document-scroll {fullScreen ? 'bg-[#0a0d14]' : 'bg-[#0d1117] p-6'}"
    onmousemove={handleMouseMove}
    onmouseleave={() => { if (!isFixing) tooltipVisible = false; }}
  >
    <div class="
      {fullScreen ? 'max-w-4xl mx-auto my-0 bg-[#0f172a] min-h-screen px-20 py-16 border-x border-white/5' : 'max-w-4xl mx-auto my-8 bg-[#111827] shadow-2xl min-h-[700px] px-16 py-12 border border-white/5'}
      {!editable ? 'cursor-default' : ''}
    ">
      <div bind:this={element} class="tiptap-content prose prose-invert max-w-none {!editable ? 'opacity-90' : ''}"></div>
    </div>
  </div>

  {#if editable}
    <StatusBar {wordCount} {charCount} {isFocused} readTime="~{Math.ceil(wordCount/200)} phút đọc" />
  {/if}
</div>

<ImageDialog bind:show={showImageDialog} {assets} onSelect={(url) => editor?.chain().focus().setImage({ src: url }).run()} />
<LinkDialog bind:show={showLinkDialog} currentUrl={currentLinkUrl} onApply={(url) => url ? editor?.chain().focus().setLink({ href: url }).run() : editor?.chain().focus().unsetLink().run()} />
<AnnotationTooltip bind:visible={tooltipVisible} x={tooltipX} y={tooltipY} type={tooltipType} text={tooltipText} {isFixing} onFix={handleFix} />

<style>
  @reference "tailwindcss";
  :global(.tiptap-content) { @apply outline-none text-white/90 leading-relaxed; }
  :global(.tiptap-content p) { @apply my-4; }
  :global(.tiptap-content h1) { @apply text-3xl font-black mb-6 text-white; }
  :global(.tiptap-content h2) { @apply text-2xl font-bold mb-4 mt-8 text-white/80; }
  :global(.tiptap-content h3) { @apply text-xl font-bold mb-3 mt-6 text-white/70; }
  :global(.tiptap-content img) { @apply rounded-lg shadow-xl my-8 mx-auto border border-white/5; }
</style>
