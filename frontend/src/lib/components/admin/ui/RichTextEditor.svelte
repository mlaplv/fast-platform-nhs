<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Editor } from '@tiptap/core';
  import StarterKit from '@tiptap/starter-kit';
  import Placeholder from '@tiptap/extension-placeholder';
  import Link from '@tiptap/extension-link';
  import Image from '@tiptap/extension-image';
  import Underline from '@tiptap/extension-underline';
  import TextAlign from '@tiptap/extension-text-align';
  import { TextStyle } from '@tiptap/extension-text-style';
  import Color from '@tiptap/extension-color';
  import FontFamily from '@tiptap/extension-font-family';
  import CharacterCount from '@tiptap/extension-character-count';
  import Typography from '@tiptap/extension-typography';
  import { AnnotationMark, injectAnnotationStyles } from './AnnotationMark';
  import type { EditorAnnotation, ToolbarAction } from '$lib/types';

  import BoldIcon from 'lucide-svelte/icons/bold';
  import ItalicIcon from 'lucide-svelte/icons/italic';
  import UnderlineIcon from 'lucide-svelte/icons/underline';
  import Heading1Icon from 'lucide-svelte/icons/heading-1';
  import Heading2Icon from 'lucide-svelte/icons/heading-2';
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
  import Sparkles from 'lucide-svelte/icons/sparkles';
  import Check from 'lucide-svelte/icons/check';


  let {
    content = "",
    onChange = () => {},
    editable = true,
    placeholder = "Start writing...",
    assets = [] as string[],
    fullScreen = false,
    toolbarActions = [] as ToolbarAction[],
    annotations = [] as EditorAnnotation[],
    onfix = null as ((snippet: string, type: string, message: string) => Promise<string | null>) | null,
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

  // Toolbar state
  let tBold = $state(false);
  let tItalic = $state(false);
  let tUnderline = $state(false);
  let tStrike = $state(false);
  let tH1 = $state(false);
  let tH2 = $state(false);
  let tH3 = $state(false);
  let tBullet = $state(false);
  let tOrdered = $state(false);
  let tAlignLeft = $state(false);
  let tAlignCenter = $state(false);
  let tAlignRight = $state(false);
  let tAlignJustify = $state(false);
  let tBlockquote = $state(false);
  let tCode = $state(false);

  // Image URL modal state
  let showImageDialog = $state(false);
  let imageUrl = $state('');
  let showLinkDialog = $state(false);
  let linkUrl = $state('');

  // Annotation tooltip state
  let tooltipVisible = $state(false);
  let tooltipText = $state('');
  let tooltipSnippet = $state('');  // actual text in editor to be replaced
  let tooltipSource = $state('');
  let tooltipType = $state('');
  let tooltipId = $state('');
  let tooltipX = $state(0);
  let tooltipY = $state(0);
  let isFixing = $state(false);
  let lastTooltipAnchorId = $state(''); // Rule R82.49: Sticky Tooltip — Anchor ID for stability

  function updateToolbarState() {
    if (!editor) return;
    tBold = editor.isActive('bold');
    tItalic = editor.isActive('italic');
    tUnderline = editor.isActive('underline');
    tStrike = editor.isActive('strike');
    tH1 = editor.isActive('heading', { level: 1 });
    tH2 = editor.isActive('heading', { level: 2 });
    tH3 = editor.isActive('heading', { level: 3 });
    tBullet = editor.isActive('bulletList');
    tOrdered = editor.isActive('orderedList');
    tAlignLeft = editor.isActive({ textAlign: 'left' });
    tAlignCenter = editor.isActive({ textAlign: 'center' });
    tAlignRight = editor.isActive({ textAlign: 'right' });
    tAlignJustify = editor.isActive({ textAlign: 'justify' });
    tBlockquote = editor.isActive('blockquote');
    tCode = editor.isActive('codeBlock');
    
    // Update metrics
    const text = editor.getText();
    charCount = text.length;
    wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  }

  let fileInput = $state<HTMLInputElement | null>(null);

  onMount(() => {
    injectAnnotationStyles();

    editor = new Editor({
      element: element,
      content: content,
      editable: editable,
      extensions: [
        StarterKit.configure({ 
          typography: false,
          // Disable extensions that might be duplicated or are added separately
          bold: true,
          italic: true,
          strike: true,
          code: true,
          history: true,
          // If these exist in this version's StarterKit, disable them to avoid duplicates
          link: false,
          underline: false
        } as any),
        Typography,
        Underline,
        Link.configure({
          openOnClick: false,
          HTMLAttributes: { class: 'text-blue-400 underline hover:text-blue-300 transition-colors cursor-pointer' },
        }),
        Image.configure({
          inline: false,
          HTMLAttributes: { class: 'max-w-full mx-auto my-4 shadow-lg' },
        }),
        TextAlign.configure({ types: ['heading', 'paragraph'] }),
        TextStyle,
        Color,
        FontFamily.configure({ types: ['textStyle'] }),
        CharacterCount,
        Placeholder.configure({
          placeholder: placeholder,
          emptyEditorClass: 'is-editor-empty',
        }),
        AnnotationMark,
      ],
      editorProps: {
        attributes: {
          class: 'focus:outline-none w-full',
        },
      },
      onUpdate: () => {
        if (!editor) return;
        const html = editor.getHTML();
        onChange(html);
        updateToolbarState();
      },
      onSelectionUpdate: () => updateToolbarState(),
      onFocus: () => isFocused = true,
      onBlur: () => {
        isFocused = false;
      },
    });

    updateToolbarState();
  });

  onDestroy(() => {
    if (editor) editor.destroy();
  });

  // Expose editor methods to parent via bind:this
  export const getHTML = () => editor?.getHTML() ?? '';
  export const commands = {
    setContent: (content: string, emitUpdate?: boolean) => editor?.commands.setContent(content, emitUpdate),
  };


  // R82.43: Sync editable state reactively
  $effect(() => {
    if (editor && !editor.isDestroyed) {
      editor.setEditable(editable);
    }
  });

  // R82.44: Sync content from props (Only if changed externally)
  $effect(() => {
    if (!editor || editor.isDestroyed || content === undefined) return;
    
    const currentHtml = editor.getHTML();
    // Use string comparison with a fallback to empty paragraph for blank content
    const normalizedContent = content === "" ? "<p></p>" : content;
    const normalizedCurrent = currentHtml === "" ? "<p></p>" : currentHtml;

    if (normalizedContent !== normalizedCurrent) {
      editor.commands.setContent(content, false);
      updateToolbarState();
    }
  });

  // ── Annotation Apply Effect ─────────────────────────────────────
  $effect(() => {
    if (!editor || editor.isDestroyed) return;
    const anns = annotations;

    editor.commands.clearAllAnnotations();
    if (!anns || anns.length === 0) return;

    const { doc } = editor.state;
    const { tr } = editor.state;
    let hasChanges = false;

    // Rule R82.45: Robust Text Matching — Handle NBSP (\u00A0) and standard spaces consistently
    interface CharPos { char: string; pos: number; }
    const docChars: CharPos[] = [];
    doc.descendants((node, pos) => {
      if (node.isText && node.text) {
        for (let i = 0; i < node.text.length; i++) {
          const c = node.text[i];
          // Use a broader whitespace check including \u00A0 (NBSP)
          if (!/[\s\u00A0\u200B\uFEFF]/.test(c)) {
            docChars.push({ char: c.toLowerCase(), pos: pos + i });
          }
        }
      }
    });
    
    const docStr = docChars.map(c => c.char).join('');

    for (const ann of anns) {
      if (!ann.text || ann.text.trim().length < 3) continue;

      const searchStr = ann.text.replace(/[\s\u00A0\u200B\uFEFF]+/g, '').toLowerCase();
      if (!searchStr) continue;

      let idx = docStr.indexOf(searchStr);
      if (idx === -1) {
        console.warn(`[RichTextEditor] Annotation Match Failed: "${ann.text.substring(0, 30)}..." not found in docStr.`);
        continue;
      }

      while (idx !== -1) {
        // Double check indices are within bounds
        if (idx < docChars.length && (idx + searchStr.length - 1) < docChars.length) {
          const startPos = docChars[idx].pos;
          const endPos = docChars[idx + searchStr.length - 1].pos + 1;

          tr.addMark(
            startPos, endPos,
            editor!.schema.marks.annotation.create({
              id: `ann-${Math.random().toString(36).substring(2, 9)}`,
              type: ann.type,
              message: ann.message,
              source: ann.source || '',
              severity: ann.severity || 'medium',
            })
          );
          hasChanges = true;
        }
        idx = docStr.indexOf(searchStr, idx + 1);
      }
    }

    if (hasChanges) {
      editor.view.dispatch(tr);
    }
  });

  // ── Annotation Tooltip ─────────────────────────────────────────
  let tooltipEl = $state<HTMLElement | null>(null);

  function handleEditorMouseMove(e: MouseEvent) {
    if (isFixing) return;
    
    const target = e.target as HTMLElement;
    const annotationEl = target.closest('.xohi-annotation') as HTMLElement | null;

    if (annotationEl) {
      const annotationId = annotationEl.getAttribute('data-annotation-id') || '';
      
      // R62.1: Tooltip Stickiness — If mouse is over the tooltip itself, don't hide it
      if (tooltipEl && (tooltipEl === target || tooltipEl.contains(target))) {
        return;
      }

      // R82.49: Sticky Logic — Only update position if we ENTER a new annotation or toolip was hidden
      // This stops "đuổi hình bắt bóng" (chasing) because it stays static while in the same mark.
      if (!tooltipVisible || annotationId !== lastTooltipAnchorId) {
        tooltipText = annotationEl.getAttribute('data-annotation-message') || '';
        tooltipSource = annotationEl.getAttribute('data-annotation-source') || '';
        tooltipType = annotationEl.getAttribute('data-annotation-type') || '';
        tooltipId = annotationId;
        tooltipSnippet = annotationEl.textContent || '';
        lastTooltipAnchorId = annotationId;

        // R82.50: Proximity Optimization — Anchor to mouse pixel horizontally to be "near"
        // but snap vertically to the current line (approximated by mouse clientY)
        tooltipX = e.clientX;
        tooltipY = e.clientY - 8; // Offset upwards slightly from cursor
        
        tooltipVisible = true;
      }
    } else {
      // If we move out of an annotation, hide it unless we are over the tooltip itself
      if (tooltipEl && (tooltipEl === target || tooltipEl.contains(target))) {
        return;
      }
      tooltipVisible = false;
      lastTooltipAnchorId = '';
    }
  }

  function handleEditorMouseLeave(e: MouseEvent) {
    if (isFixing) return;
    
    // Check if we are moving INTO the tooltip
    const relatedTarget = e.relatedTarget as HTMLElement;
    if (tooltipEl && (tooltipEl === relatedTarget || tooltipEl.contains(relatedTarget))) {
      return;
    }
    
    tooltipVisible = false;
  }

  async function handleTooltipFix() {
    if (!onfix || isFixing || !tooltipSnippet || !tooltipId) return;
    isFixing = true;
    try {
      const newText = await onfix(tooltipSnippet, tooltipType, tooltipText);
      if (newText && editor) {
        let minPos = Infinity;
        let maxPos = -Infinity;
        const markType = editor.schema.marks.annotation;

        // If fixing internal-dedup, replace ALL exact matches in the document to save user clicks
        const isInternalDedup = tooltipType === 'internal-dedup';
        let foundMatches = false;

        let currentTr = editor.state.tr;

        // For internal-dedup, we want to replace ALL exact text matches in the document
        if (isInternalDedup) {
           // We must collect ranges first, then apply in REVERSE order so positions don't shift
           const rangesToReplace: {start: number, end: number}[] = [];
           
           editor.state.doc.descendants((node, pos) => {
             if (node.isText && node.text) {
               // Find ALL occurrences within this specific text node
               let startIndex = 0;
               let matchIdx = node.text.indexOf(tooltipSnippet, startIndex);
               while (matchIdx !== -1) {
                 const absoluteStart = pos + matchIdx;
                 const absoluteEnd = absoluteStart + tooltipSnippet.length;
                 rangesToReplace.push({ start: absoluteStart, end: absoluteEnd });
                 
                 // Move start index forward to find subsequent matches in the same node
                 startIndex = matchIdx + tooltipSnippet.length;
                 matchIdx = node.text.indexOf(tooltipSnippet, startIndex);
               }
             }
           });
           
           // Sort descending by start position to prevent offset shifts during replacement
           rangesToReplace.sort((a, b) => b.start - a.start);
           
           for (const range of rangesToReplace) {
             currentTr = currentTr.insertText(newText, range.start, range.end);
             foundMatches = true;
           }
           
        } else {
          // Standard logic: find ONLY the mark with the matching ID
          let minPos = Infinity;
          let maxPos = -Infinity;
          
          editor.state.doc.descendants((node, pos) => {
            if (node.isText) {
              const hasMark = node.marks.find(m => m.type === markType && m.attrs.id === tooltipId);
              if (hasMark) {
                minPos = Math.min(minPos, pos);
                maxPos = Math.max(maxPos, pos + node.nodeSize);
              }
            }
          });

          if (minPos !== Infinity && maxPos !== -Infinity) {
             currentTr = currentTr.insertText(newText, minPos, maxPos);
             foundMatches = true;
          }
        }

        if (foundMatches) {
          editor.view.dispatch(currentTr);
          tooltipSnippet = newText;
          tooltipType = 'fixed'; // Show completed state
        }
      }
    } finally {
      isFixing = false;
      // Keep tooltip visible for a moment so user sees the "✅ Đã Sửa" state
      setTimeout(() => {
        if (!isFixing) tooltipVisible = false;
      }, 1500);
    }
  }

  function insertImage() {
    if (imageUrl.trim() && editor) {
      editor.chain().focus().setImage({ src: imageUrl.trim() }).run();
      imageUrl = '';
      showImageDialog = false;
    }
  }

  function handleFileUpload(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file && editor) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const result = e.target?.result as string;
        editor?.chain().focus().setImage({ src: result }).run();
        showImageDialog = false;
      };
      reader.readAsDataURL(file);
    }
  }

  function setLink() {
    if (!editor) return;
    if (linkUrl.trim()) {
      editor.chain().focus().setLink({ href: linkUrl.trim() }).run();
    } else {
      editor.chain().focus().unsetLink().run();
    }
    linkUrl = '';
    showLinkDialog = false;
  }

  function getReadTime() {
    const minutes = Math.ceil(wordCount / 200);
    return `~${minutes} phút đọc`;
  }

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

  function handleImageError(e: Event) {
    (e.target as HTMLImageElement).src = 'https://placehold.co/400x300?text=Image+Error';
  }

  const FONTS = ['Inter', 'Roboto', 'Georgia', 'Times New Roman', 'Courier New', 'Arial'];
  const COLORS = ['#ffffff', '#93c5fd', '#86efac', '#fde68a', '#fca5a5', '#c4b5fd', '#67e8f9', '#fb923c'];

  function clearAnnotations() {
    if (editor) editor.commands.clearAllAnnotations();
  }

  function handleFocusOut(e: FocusEvent) {
    // Phase 73: Only trigger onblur if focus is moving OUTSIDE the entire shell
    // This prevents closing the editor when clicking on toolbar buttons
    const currentTarget = e.currentTarget as HTMLElement;
    const relatedTarget = e.relatedTarget as Node;
    
    if (editable && onblur && currentTarget && !currentTarget.contains(relatedTarget)) {
      onblur();
    }
  }
</script>

<!-- Main editor container -->
<div 
  class="editor-shell flex flex-col w-full h-full {editable ? 'bg-[#0d1117] border ' + (isFocused ? 'border-blue-500/40' : 'border-white/10') + ' overflow-hidden' : 'bg-transparent border-none overflow-visible'} transition-all duration-300"
  onfocusout={handleFocusOut}
>

  {#if editable}
  <!-- Row 1: Primary toolbar -->
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
    <button onclick={() => editor?.chain().focus().toggleBold().run()} class="tb-btn {tBold ? 'active' : ''}" title="Bold (Ctrl+B)"><BoldIcon size={13} /></button>
    <button onclick={() => editor?.chain().focus().toggleItalic().run()} class="tb-btn {tItalic ? 'active' : ''}" title="Italic (Ctrl+I)"><ItalicIcon size={13} /></button>
    <button onclick={() => editor?.chain().focus().toggleUnderline().run()} class="tb-btn {tUnderline ? 'active' : ''}" title="Underline (Ctrl+U)"><UnderlineIcon size={13} /></button>
    <button onclick={() => editor?.chain().focus().toggleStrike().run()} class="tb-btn {tStrike ? 'active' : ''}" title="Strikethrough"><StrikethroughIcon size={13} /></button>

    <div class="tb-divider"></div>

    <!-- Text alignment -->
    <button onclick={() => editor?.chain().focus().setTextAlign('left').run()} class="tb-btn {tAlignLeft ? 'active' : ''}" title="Align Left"><AlignLeftIcon size={13} /></button>
    <button onclick={() => editor?.chain().focus().setTextAlign('center').run()} class="tb-btn {tAlignCenter ? 'active' : ''}" title="Align Center"><AlignCenterIcon size={13} /></button>
    <button onclick={() => editor?.chain().focus().setTextAlign('right').run()} class="tb-btn {tAlignRight ? 'active' : ''}" title="Align Right"><AlignRightIcon size={13} /></button>
    <button onclick={() => editor?.chain().focus().setTextAlign('justify').run()} class="tb-btn {tAlignJustify ? 'active' : ''}" title="Justify"><AlignJustifyIcon size={13} /></button>

    <div class="tb-divider"></div>

    <!-- Lists -->
    <button onclick={() => editor?.chain().focus().toggleBulletList().run()} class="tb-btn {tBullet ? 'active' : ''}" title="Bullet List"><ListIcon size={13} /></button>
    <button onclick={() => editor?.chain().focus().toggleOrderedList().run()} class="tb-btn {tOrdered ? 'active' : ''}" title="Ordered List"><ListOrderedIcon size={13} /></button>

    <div class="tb-divider"></div>

    <!-- Insert -->
    <button onclick={() => showImageDialog = true} class="tb-btn" title="Insert Image"><ImageIcon size={13} /></button>
    <button onclick={() => { linkUrl = editor?.getAttributes('link').href ?? ''; showLinkDialog = true; }} class="tb-btn" title="Insert Link"><Link2Icon size={13} /></button>
    <button onclick={() => editor?.chain().focus().toggleBlockquote().run()} class="tb-btn {tBlockquote ? 'active' : ''}" title="Blockquote"><BlockquoteIcon size={13} /></button>
    <button onclick={() => editor?.chain().focus().toggleCodeBlock().run()} class="tb-btn {tCode ? 'active' : ''}" title="Code Block"><CodeIcon size={13} /></button>
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

    <!-- Custom Toolbar Actions (injected from parent) -->
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

    <!-- Clear Annotations Button (shows only when active) -->
    {#if annotations && annotations.length > 0}
      {#if !toolbarActions.length}
        <div class="tb-divider ml-auto"></div>
      {/if}
      <button
        onclick={clearAnnotations}
        class="flex items-center gap-1 px-2 py-0.5 text-[9px] font-black uppercase tracking-wide border transition-all bg-white/5 hover:bg-white/10 border-white/10 text-white/40 hover:text-white active:scale-95"
        title="Xóa tất cả highlights"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
        Xóa Highlight
      </button>
    {/if}
  </div>
  {/if}

  <!-- Editor content area — the document page -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="flex-1 overflow-y-auto document-scroll {editable ? (fullScreen ? 'bg-[#0a0d14] p-0' : 'bg-[#0d1117] p-6') : 'bg-transparent text-white/90'}"
    onmousemove={handleEditorMouseMove}
    onmouseleave={handleEditorMouseLeave}
  >
    <!-- White page with shadow -->
    <div class="{editable ? (fullScreen ? 'max-w-[95%] mx-auto my-0 bg-[#0f172a] min-h-screen px-20 py-16 shadow-none border-x border-white/5' : 'max-w-[95%] mx-auto my-8 bg-[#111827] shadow-[0_0_0_1px_rgba(255,255,255,0.05),0_20px_60px_rgba(0,0,0,0.5)] min-h-[600px] px-16 py-12') : (fullScreen ? 'max-w-[95%] mx-auto px-10 py-12' : 'max-w-full mx-auto px-6 py-4')}">
      <div bind:this={element} class="editor-content transition-all duration-300"></div>
    </div>
  </div>

  <!-- Status Bar -->
  {#if editable}
  <div class="flex items-center gap-4 px-4 py-1.5 bg-white/[0.02] border-t border-white/5 text-[10px] text-white/30 font-mono shrink-0">
    <span>📄 {wordCount} từ</span>
    <span>🔤 {charCount} ký tự</span>
    <span class="ml-auto text-blue-500/50">{getReadTime()}</span>
    <div class="w-1.5 h-1.5 rounded-full {isFocused ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-white/20'} transition-colors ml-2" title={isFocused ? 'Đang soạn thảo...' : 'Đang tạm dừng'}></div>
  </div>
  {/if}
</div>

<!-- Image Dialog -->
{#if showImageDialog}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm" onclick={() => showImageDialog = false}>
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <div class="bg-[#1a2233] border border-white/10 p-6 shadow-2xl w-[90%] max-w-[800px]" onclick={(e) => e.stopPropagation()}>
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-bold text-white">Chèn hình ảnh</h3>
        <button onclick={() => showImageDialog = false} class="text-white/40 hover:text-white"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg></button>
      </div>

      {#if assets && assets.length > 0}
         <div class="text-[10px] uppercase font-bold text-blue-400 mb-2 tracking-wider">Chọn từ Kho Ảnh </div>
         <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 mb-4 max-h-[400px] overflow-y-auto pr-1 custom-scrollbar">
            {#each assets.filter(a => a) as asset}
              {@const assetUrl = typeof asset === 'string' ? asset : (asset.url || asset.link)}
              {@const fullUrl = assetUrl.startsWith('http') || assetUrl.startsWith('data:') ? assetUrl : (assetUrl.startsWith('/') ? assetUrl : '/storage/' + assetUrl)}
              <!-- svelte-ignore a11y_click_events_have_key_events -->
              <!-- svelte-ignore a11y_no_static_element_interactions -->
              <div 
                 class="aspect-video overflow-hidden border border-white/10 hover:border-blue-500 cursor-pointer transition-colors bg-white/5"
                 onclick={() => { imageUrl = fullUrl; insertImage(); }}
                 title="Chèn ảnh này"
              >
                  <img 
                    src={fullUrl} 
                    alt="asset" 
                    class="w-full h-full object-cover" 
                    onerror={handleImageError} 
                  />
              </div>
            {/each}
          </div>
          <div class="flex items-center gap-2 mb-3">
            <div class="h-px bg-white/10 flex-1"></div>
            <span class="text-xs text-white/40 font-mono text-center">HOẶC CHÈN QUA URL / TẢI LÊN</span>
            <div class="h-px bg-white/10 flex-1"></div>
          </div>
      {/if}

      <div class="flex flex-col gap-3 mb-4">
        <button 
          onclick={() => fileInput?.click()}
          class="w-full flex items-center justify-center gap-2 py-3 bg-blue-500/10 border border-blue-500/20 text-blue-400 hover:bg-blue-500/20 transition-all text-xs font-bold"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          Tải ảnh lên từ thiết bị
        </button>
        <input 
          type="file" 
          bind:this={fileInput} 
          accept="image/*" 
          class="hidden" 
          onchange={handleFileUpload} 
        />
      </div>

      <input
        type="url"
        placeholder="Dán URL hình ảnh vào đây..."
        bind:value={imageUrl}
        onkeydown={(e) => e.key === 'Enter' && insertImage()}
        class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-white/30 outline-none focus:border-blue-500/50 mb-3"
      />
      <div class="flex gap-2 justify-end">
        <button onclick={() => showImageDialog = false} class="px-4 py-2 text-xs text-white/60 hover:text-white transition-colors">Hủy</button>
        <button onclick={insertImage} class="px-4 py-2 bg-blue-500 hover:bg-blue-400 text-white text-xs font-bold transition-colors">Chèn URL</button>
      </div>
    </div>
  </div>
{/if}

<!-- Link Dialog -->
{#if showLinkDialog}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm" onclick={() => showLinkDialog = false}>
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <div class="bg-[#1a2233] border border-white/10 p-6 shadow-2xl w-96" onclick={(e) => e.stopPropagation()}>
      <h3 class="text-sm font-bold text-white mb-3">Chèn liên kết</h3>
      <input
        type="url"
        placeholder="https://..."
        bind:value={linkUrl}
        onkeydown={(e) => e.key === 'Enter' && setLink()}
        class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-white/30 outline-none focus:border-blue-500/50 mb-3"
      />
      <div class="flex gap-2 justify-end">
        <button onclick={() => showLinkDialog = false} class="px-4 py-2 text-xs text-white/60 hover:text-white transition-colors">Hủy</button>
        <button onclick={setLink} class="px-4 py-2 bg-blue-500 hover:bg-blue-400 text-white text-xs font-bold transition-colors">Áp dụng</button>
      </div>
    </div>
  </div>
{/if}

  <!-- Annotation Tooltip -->
  {#if tooltipVisible && (tooltipText || tooltipType === 'fixed')}
    {@const _isFixed = tooltipType === 'fixed'}
    {@const _isInternal = tooltipType === 'internal-dedup'}
    <div 
      bind:this={tooltipEl}
      class="fixed z-[100001] pointer-events-none transition-opacity duration-150"
      style="left: {tooltipX}px; top: {tooltipY}px; transform: translate(-50%, -100%)"
    >
      <div class="shadow-2xl border backdrop-blur-xl p-3 text-[10px] leading-relaxed w-56 pointer-events-auto {
        _isFixed ? 'bg-emerald-950/95 border-emerald-500/30 text-emerald-100' : 
        _isInternal ? 'bg-fuchsia-950/95 border-fuchsia-500/30 text-fuchsia-100' :
        tooltipType === 'copyright' ? 'bg-orange-950/95 border-orange-500/30 text-orange-100' :
        tooltipType.startsWith('seo-') ? 'bg-blue-950/95 border-blue-400/30 text-blue-50' :
        'bg-slate-900/95 border-white/10 text-white'
      }">
        <div class="flex flex-col gap-2">
          <div class="flex items-start justify-between gap-3">
            <span class="font-black uppercase tracking-widest opacity-40 shrink-0 text-[8px] mt-0.5">
              {_isFixed ? '✨ Hoàn tất' : tooltipType.replace(/_/g, ' ')}
            </span>
            {#if _isFixed}
              <span class="text-emerald-400 font-bold bg-emerald-400/10 px-1.5 py-0.5 flex items-center gap-1 shrink-0">
                <Check size={10} /> ĐÃ SỬA
              </span>
            {/if}
          </div>

          <p class="font-medium { _isFixed ? 'text-emerald-200/80' : _isInternal ? 'text-fuchsia-200/80' : 'text-white/80' }">
            {_isFixed ? 'Đoạn văn này đã được Surgical Agent xử lý chuẩn xác.' : tooltipText}
          </p>
          
          {#if !_isFixed}
            <div class="h-px bg-white/5 my-1"></div>
            
            <div class="flex items-center justify-between">
              <span class="text-[8px] opacity-30 italic shrink-0">Surgical Agent Ready</span>
              
              <button 
                class="flex items-center gap-1.5 px-2.5 py-1 bg-white/10 hover:bg-white/20 text-white transition-all font-bold disabled:opacity-40"
                onclick={handleTooltipFix}
                disabled={isFixing}
              >
                {#if isFixing}
                  <span class="inline-block w-2.5 h-2.5 border-2 border-white/20 border-t-white rounded-full animate-spin"></span>
                  SỬA...
                {:else}
                  <Sparkles size={10} class="text-yellow-400" />
                  SỬA LỖI
                {/if}
              </button>
            </div>
          {/if}
          
          {#if tooltipSource && !_isFixed && !_isInternal}
            <a
              href={tooltipSource}
              target="_blank"
              rel="noopener noreferrer"
              class="pointer-events-auto mt-1 block text-[8px] text-red-300/70 hover:text-red-200 underline truncate transition-colors"
            >🔗 Nguồn: {tooltipSource}</a>
          {/if}
        </div>
      </div>
      <!-- Triangle pointer -->
      <div class="w-3 h-3 rotate-45 mx-auto -mt-1.5 border-r border-b backdrop-blur-xl {
        _isFixed ? 'bg-emerald-950/95 border-emerald-500/30' : 
        _isInternal ? 'bg-fuchsia-950/95 border-fuchsia-500/30' :
        tooltipType === 'copyright' ? 'bg-orange-950/95 border-orange-500/30' :
        tooltipType.startsWith('seo-') ? 'bg-blue-950/95 border-blue-400/30' :
        'bg-slate-900/95 border-white/10'
      }"></div>
    </div>
  {/if}

<style>
  .document-scroll {
    scrollbar-width: thin;
    scrollbar-color: rgba(255,255,255,0.1) transparent;
  }
  .document-scroll::-webkit-scrollbar { width: 6px; }
  .document-scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }

  :global(.tb-btn) {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4px 6px;
    border-radius: 6px;
    color: rgba(255,255,255,0.5);
    transition: all 0.15s;
    min-width: 26px;
    height: 26px;
    border: 1px solid transparent;
  }
  :global(.tb-btn:hover) {
    color: white;
    background: rgba(255,255,255,0.08);
  }
  :global(.tb-btn.active) {
    color: #60a5fa;
    background: rgba(59,130,246,0.15);
    border-color: rgba(59,130,246,0.25);
  }
  :global(.tb-divider) {
    width: 1px;
    height: 18px;
    background: rgba(255,255,255,0.08);
    margin: 0 4px;
    flex-shrink: 0;
  }

  /* ProseMirror document styling */
  :global(.editor-content .ProseMirror) {
    outline: none;
    color: rgba(255,255,255,0.88);
    font-size: 15px;
    line-height: 1.85;
    font-family: 'Inter', -apple-system, sans-serif;
    min-height: 400px;
  }
  :global(.editor-content .ProseMirror p.is-editor-empty:first-child::before) {
    content: attr(data-placeholder);
    float: left;
    color: rgba(255,255,255,0.15);
    pointer-events: none;
    height: 0;
    font-style: italic;
  }
  :global(.editor-content .ProseMirror h1) {
    font-size: 2em;
    font-weight: 900;
    margin: 1.5em 0 0.5em;
    color: #fff;
    letter-spacing: -0.03em;
    line-height: 1.2;
  }
  :global(.editor-content .ProseMirror h2) {
    font-size: 1.5em;
    font-weight: 800;
    margin: 1.2em 0 0.5em;
    color: #e2e8f0;
    letter-spacing: -0.02em;
  }
  :global(.editor-content .ProseMirror h3) {
    font-size: 1.2em;
    font-weight: 700;
    margin: 1em 0 0.4em;
    color: #cbd5e1;
  }
  :global(.editor-content .ProseMirror p) {
    margin-bottom: 1em;
  }
  :global(.editor-content .ProseMirror ul, .editor-content .ProseMirror ol) {
    padding-left: 1.5em;
    margin: 0.75em 0;
  }
  :global(.editor-content .ProseMirror ul) { list-style-type: disc; }
  :global(.editor-content .ProseMirror ol) { list-style-type: decimal; }
  :global(.editor-content .ProseMirror li) { margin-bottom: 0.3em; }
  :global(.editor-content .ProseMirror blockquote) {
    border-left: 4px solid rgba(99,102,241,0.6);
    padding: 0.75em 1.25em;
    background: rgba(99,102,241,0.05);
    border-radius: 0 12px 12px 0;
    margin: 1em 0;
    color: rgba(255,255,255,0.65);
    font-style: italic;
  }
  
  /* Placeholder Styling (Fix: "Black screen" when empty) */
  :global(.editor-content .ProseMirror p.is-editor-empty:first-child::before) {
    content: attr(data-placeholder);
    float: left;
    color: rgba(255, 255, 255, 0.4);
    pointer-events: none;
    height: 0;
    font-style: italic;
    font-weight: 500;
  }
  :global(.editor-content .ProseMirror code) {
    background: rgba(0,0,0,0.4);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 0.15em 0.4em;
    border-radius: 4px;
    font-family: 'Fira Code', monospace;
    font-size: 0.875em;
    color: #7dd3fc;
  }
  :global(.editor-content .ProseMirror pre) {
    background: rgba(0,0,0,0.5);
    border: 1px solid rgba(255,255,255,0.06);
    padding: 1.25em 1.5em;
    border-radius: 12px;
    overflow-x: auto;
    margin: 1em 0;
  }
  :global(.editor-content .ProseMirror pre code) {
    background: none;
    border: none;
    padding: 0;
    font-size: 0.9em;
    color: #e2e8f0;
  }
  :global(.editor-content .ProseMirror hr) {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.08);
    margin: 1.5em 0;
  }
  :global(.editor-content .ProseMirror img) {
    max-width: 100%;
    border-radius: 12px;
    margin: 1.5em auto;
    display: block;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    border: 1px solid rgba(255,255,255,0.06);
  }
</style>
