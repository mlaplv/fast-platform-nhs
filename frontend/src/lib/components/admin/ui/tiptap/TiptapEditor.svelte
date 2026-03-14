<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Editor } from '@tiptap/core';
  import { getEditorExtensions, editorProps } from './core/editor-config';
  import { injectAnnotationStyles } from './extensions/AnnotationMark';
  import type { EditorAnnotation, ToolbarAction } from '$lib/types';

  import Toolbar from './ui/Toolbar.svelte';
  import ImageDialog from './ui/ImageDialog.svelte';
  import LinkDialog from './ui/LinkDialog.svelte';
  import StatusBar from './ui/StatusBar.svelte';
  import AnnotationTooltip from './ui/AnnotationTooltip.svelte';
  import ImageBubbleMenu from './ui/ImageBubbleMenu.svelte';

  let {
    content = "",
    onChange = () => {},
    editable = true,
    placeholder = "Start writing...",
    assets = [] as string[],
    fullScreen = $bindable(false),
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
  let isInternalUpdating = $state(false);
  let isSyncLocked = $state(false);
  let lastInternalActionAt = $state(0);
  let blockClicks = $state(false);
  let lastSentContent = $state("");

  // Image Menu tracking
  let scrollContainer: HTMLElement;
  let imageMenuVisible = $state(false);
  let imageMenuX = $state(0);
  let imageMenuY = $state(0);

  function stripMarks(html: string): string {
    // Loại bỏ các thẻ mark (highlights) và các thuộc tính data-annotation để so sánh nội dung thuần
    return html
      .replace(/<mark[^>]*>|<\/mark>/g, '')
      .replace(/ data-annotation-[^=]*="[^"]*"/g, '')
      .replace(/ class="xohi-annotation[^"]*"/g, '');
  }

  function generateStableId(text: string, message: string): string {
    let hash = 5381;
    const str = text + message;
    for (let i = 0; i < str.length; i++) {
      hash = (hash * 33) ^ str.charCodeAt(i);
    }
    return (hash >>> 0).toString(36);
  }

  const containerClass = $derived(`tiptap-shell flex flex-col ${
    fullScreen ? 'fixed inset-0 z-[2000] bg-[#0d1117]' : 'w-full h-full'
    } ${
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

  function updateImageMenuPosition() {
    if (!editor || !element || !scrollContainer) return;

    const selectedImg = element.querySelector('.ProseMirror-selectednode') as HTMLElement;
    if (selectedImg && editor.isActive('image')) {
      const scrollRect = scrollContainer.getBoundingClientRect();
      const imgRect = selectedImg.getBoundingClientRect();

      // Calculate position relative to viewport (for fixed positioning)
      imageMenuX = imgRect.left + (imgRect.width / 2);
      imageMenuY = imgRect.top - 8;
      imageMenuVisible = true;
    } else {
      imageMenuVisible = false;
    }
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
      if (isInternalUpdating) return;
      const html = editor?.getHTML() ?? '';
      console.log('[Tiptap] Content Changed:', html.substring(0, 50) + '...');
      onChange(stripMarks(html));
      updateMetrics();
      updateImageMenuPosition();
    },
      onSelectionUpdate: () => {
        updateImageMenuPosition();
      },
      onFocus: () => isFocused = true,
      onBlur: () => isFocused = false,
    });
    updateMetrics();
  });

  onDestroy(() => {
    if (editor) editor.destroy();
  });

  $effect(() => {
    if (editor && !editor.isDestroyed) editor.setEditable(editable);
  });

  $effect(() => {
    if (!editor || editor.isDestroyed) return;
    // Không tự động cập nhật content nếu đang focus hoặc đang mở Dialog
    if (isFocused || showImageDialog || showLinkDialog) {
      return;
    }

    // CHẶN CỰC MẠNH: Nếu đang khóa đồng bộ hoặc vừa có cập nhật nội bộ trong 1.5 giây qua
    if (isSyncLocked || (Date.now() - lastInternalActionAt < 1500)) {
      console.log('[Tiptap] Sync Locked - Protecting internal state');
      return;
    }

    const normalizedContent = content || "<p></p>";
    const currentHTML = editor.getHTML();

    if (stripMarks(normalizedContent) !== stripMarks(currentHTML)) {
      console.log('[Tiptap] Syncing content from prop');
      isInternalUpdating = true;
      editor.commands.setContent(content, false);
      updateMetrics();
      setTimeout(() => { isInternalUpdating = false; }, 50);
    }
  });

  $effect(() => {
    if (!editor || editor.isDestroyed) return;
    isInternalUpdating = true;
    try {
      const { doc, tr } = editor.state;
      let hasChanges = false;
      const annotationMarkType = editor.schema.marks.annotation;

      doc.descendants((node, pos) => {
        if (node.isText && node.marks.some(m => m.type === annotationMarkType)) {
          tr.removeMark(pos, pos + node.nodeSize, annotationMarkType);
          hasChanges = true;
        }
      });

      if (!annotations?.length) {
        if (hasChanges) editor.view.dispatch(tr);
        return;
      }

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

      const isAlphaNum = (c: string) => /[a-z0-9\u00C0-\u1EF9]/i.test(c);
      const docNormalMap: number[] = [];
      let docStrNormalized = '';
      for (let i = 0; i < docChars.length; i++) {
        if (isAlphaNum(docChars[i].char)) {
          docStrNormalized += docChars[i].char;
          docNormalMap.push(i);
        }
      }

      for (const ann of annotations) {
        if (!ann.text || ann.text.length < 3) continue;
        const pattern = ann.text.toLowerCase().split('').filter(isAlphaNum).join('');
        if (pattern.length < 3) continue;

        const maxErrors = Math.max(1, Math.floor(pattern.length * 0.1));
        const stableId = generateStableId(ann.text, ann.message);

        let bestMatchIdx = docStrNormalized.indexOf(pattern);
        if (bestMatchIdx === -1) {
          let bestDistance = maxErrors + 1;
          for (let i = 0; i <= docStrNormalized.length - pattern.length; i++) {
            let distance = 0;
            for (let j = 0; j < pattern.length; j++) {
              if (docStrNormalized[i+j] !== pattern[j]) {
                distance++;
                if (distance > maxErrors) break;
              }
            }
            if (distance < bestDistance) {
              bestDistance = distance;
              bestMatchIdx = i;
            }
          }
        }

        if (bestMatchIdx !== -1) {
          const startDocCharIdx = docNormalMap[bestMatchIdx];
          const endDocCharIdx = docNormalMap[bestMatchIdx + pattern.length - 1];
          if (startDocCharIdx !== undefined && endDocCharIdx !== undefined) {
            tr.addMark(docChars[startDocCharIdx].pos, docChars[endDocCharIdx].pos + 1, annotationMarkType.create({
              id: `ann-${stableId}`,
              type: ann.type,
              message: ann.message,
              source: ann.source || '',
              severity: ann.severity || 'medium',
            }));
            hasChanges = true;
          }
        }
      }
      if (hasChanges) editor.view.dispatch(tr);
    } finally {
      setTimeout(() => { isInternalUpdating = false; }, 50);
    }
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
    } else if (!target.closest('.tiptap-tooltip')) {
      tooltipVisible = false;
      lastTooltipAnchorId = '';
    }
  }

  function handleImageClick(e: MouseEvent) {
    if (blockClicks) return;
    const target = e.target as HTMLElement;
    const img = target.closest('.tiptap-content img') as HTMLImageElement | null;
    if (img && editor) {
      editor.commands.focus();
      const pos = editor.view.posAtDOM(img, 0);
      if (pos >= 0) editor.commands.setNodeSelection(pos);
    }
  }

  function handleDoubleClick(e: MouseEvent) {
    if (blockClicks) return;
    // Nếu vừa mới cập nhật nội bộ, chặn mở lại dialog ngay lập tức (phòng trường hợp click đúp quá nhanh)
    if (Date.now() - lastInternalActionAt < 800) return;

    const target = e.target as HTMLElement;
    if (target.closest('.tiptap-content img')) showImageDialog = true;
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

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Escape' && fullScreen) fullScreen = false;
  }
</script>

<svelte:window onkeydown={handleKeyDown} />

<div
  class={containerClass}
  onfocusout={(e) => { if (onblur && !e.currentTarget.contains(e.relatedTarget as Node)) onblur(); }}
>
  {#if editable}
    <Toolbar
      {editor}
      {toolbarActions}
      {annotations}
      onOpenImage={() => { if (!blockClicks) showImageDialog = true; }}
      onOpenLink={() => {
        if (blockClicks) return;
        currentLinkUrl = editor?.getAttributes('link').href || '';
        showLinkDialog = true;
      }}
      onAction={() => {
        isInternalUpdating = true;
        isSyncLocked = true;
        lastInternalActionAt = Date.now();
        setTimeout(() => {
          isInternalUpdating = false;
          isSyncLocked = false;
        }, 1000);
      }}
      onClearHighlights={() => { if (!blockClicks) editor?.commands.clearAllAnnotations(); }}
      bind:fullScreen
    />
  {/if}

  <div
    bind:this={scrollContainer}
    class="flex-1 overflow-y-auto document-scroll relative {fullScreen ? 'bg-[#0a0d14]' : 'bg-[#0d1117] p-6'}"
    onmousemove={handleMouseMove}
    onscroll={updateImageMenuPosition}
    onclick={handleImageClick}
    ondblclick={handleDoubleClick}
    onmouseleave={(e) => {
      const related = e.relatedTarget as HTMLElement;
      if (!isFixing && !related?.closest('.tiptap-tooltip')) {
        tooltipVisible = false;
        lastTooltipAnchorId = '';
      }
    }}
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

<ImageDialog
  bind:show={showImageDialog}
  {assets}
  onSelect={(url) => {
    if (editor) {
      console.log('[Tiptap] Internal UI Action: Image Replace');
      isInternalUpdating = true; // Chặn onUpdate tự động để tránh phát tin trùng lặp
      isSyncLocked = true;
      blockClicks = true;
      lastInternalActionAt = Date.now();

      // Đảm bảo focus để editor giữ trạng thái
      editor.commands.focus();

      // Thực hiện thay đổi
      if (editor.isActive('image')) {
        const attrs = editor.getAttributes('image');
        editor.chain().updateAttributes('image', { ...attrs, src: url }).run();
      } else {
        editor.chain().setImage({ src: url }).run();
      }

      // ÉP BUỘC báo cáo cho Parent ngay lập tức
      const html = editor.getHTML();
      onChange(stripMarks(html));

      showImageDialog = false;

      // Giải phóng block clicks sớm, nhưng giữ sync lock lâu hơn
      setTimeout(() => { blockClicks = false; }, 400);
      setTimeout(() => {
        isInternalUpdating = false;
        isSyncLocked = false;
      }, 1500);
    }
  }}
/>
<LinkDialog bind:show={showLinkDialog} currentUrl={currentLinkUrl} onApply={(url) => url ? editor?.chain().focus().setLink({ href: url }).run() : editor?.chain().focus().unsetLink().run()} />
<AnnotationTooltip bind:visible={tooltipVisible} x={tooltipX} y={tooltipY} type={tooltipType} text={tooltipText} {isFixing} onFix={handleFix} />

  {#if editor && editable && imageMenuVisible && !blockClicks && !showImageDialog && !showLinkDialog}
  <div
    class="fixed z-[3000] -translate-x-1/2 -translate-y-full pointer-events-auto transition-all duration-75 ease-out"
    style="left: {imageMenuX}px; top: {imageMenuY}px;"
  >
    <ImageBubbleMenu
      {editor}
      onAction={() => {
        isInternalUpdating = true;
        isSyncLocked = true;
        lastInternalActionAt = Date.now();
        setTimeout(() => {
          isInternalUpdating = false;
          isSyncLocked = false;
        }, 1000);
      }}
      onReplace={() => { if (!blockClicks) showImageDialog = true; }}
    />
  </div>
{/if}

<style>
  @reference "tailwindcss";
  :global(.tiptap-content) { @apply outline-none text-white/90 leading-relaxed; }
  :global(.tiptap-content p) { @apply my-4; }
  :global(.tiptap-content h1) { @apply text-3xl font-black mb-6 text-white; }
  :global(.tiptap-content h2) { @apply text-2xl font-bold mb-4 mt-8 text-white/80; }
  :global(.tiptap-content h3) { @apply text-xl font-bold mb-3 mt-6 text-white/70; }
  :global(.tiptap-content img) { @apply rounded-lg my-4 cursor-pointer border-2 border-transparent transition-all duration-200; }
  :global(.tiptap-content img.ProseMirror-selectednode) { @apply border-blue-500/50 shadow-lg shadow-blue-500/10; }
</style>
