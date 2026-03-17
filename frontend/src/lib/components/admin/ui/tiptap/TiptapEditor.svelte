<script lang="ts">
  import { onMount, onDestroy, untrack } from 'svelte';
  import { Editor } from '@tiptap/core';
  import { getEditorExtensions, editorProps } from './core/editor-config';
  import { AnnotationPluginKey } from './core/AnnotationPlugin';
  import type { EditorAnnotation, ToolbarAction } from '$lib/types';

  import Toolbar from './ui/Toolbar.svelte';
  import ImageDialog from './ui/ImageDialog.svelte';
  import LinkDialog from './ui/LinkDialog.svelte';
  import StatusBar from './ui/StatusBar.svelte';
  import AnnotationTooltip from './ui/AnnotationTooltip.svelte';
  import type { MediaAsset } from '$lib/state/types';
  import { apiClient } from '$lib/utils/apiClient';

  let {
    content = "",
    onChange = () => {},
    editable = true,
    placeholder = "Start writing...",
    assets = [] as (MediaAsset | string)[],
    fullScreen = false,
    onToggleFullScreen = null,
    toolbarActions = [] as ToolbarAction[],
    annotations = [] as EditorAnnotation[],
    onfix = null,
    onblur = () => {},
  }: {
    content?: string;
    onChange?: (val: string) => void;
    editable?: boolean;
    placeholder?: string;
    assets?: (MediaAsset | string)[];
    fullScreen?: boolean;
    onToggleFullScreen?: (() => void) | null;
    toolbarActions?: ToolbarAction[];
    annotations?: EditorAnnotation[];
    onfix?: ((snippet: string, type: string, message: string) => Promise<string | null>) | null;
    onblur?: () => void;
  } = $props();

  let internalFullScreen = $state(fullScreen);
  $effect(() => { internalFullScreen = fullScreen; });

  const toggleFullScreen = () => {
    if (onToggleFullScreen) {
      onToggleFullScreen();
    } else {
      internalFullScreen = !internalFullScreen;
      if (typeof window !== 'undefined') {
        document.body.style.overflow = internalFullScreen ? 'hidden' : '';
      }
    }
  };

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
  let tooltipFrom = $state(0);
  let tooltipTo = $state(0);
  let tooltipX = $state(0);
  let tooltipY = $state(0);
  let isFixing = $state(false);
  let lastTooltipAnchorId = $state('');
  let isInternalUpdating = false;
  let cleanStatus = $state<'idle' | 'cleaning' | 'done'>('idle');

  // ✦ Cerberus 2026: Frontend Clean — Jaccard near-duplicate dedup + Viral 2026 Polish (Phase 76.9)
  async function handleClean() {
    console.log('[Clean] ▶ handleClean fired (Viral 2026 Edition)');
    if (!editor || editor.isDestroyed) {
      console.warn('[Clean] Editor not ready');
      return;
    }
    cleanStatus = 'cleaning';

    try {
      const html = editor.getHTML();
      console.log('[Clean] HTML length:', html.length);

      const div = document.createElement('div');
      div.innerHTML = html;

      // 1. Surgical Artifact Stripping: Remove rogue code blocks and excessive links
      // Viral articles should not contain raw <code> or <pre> blocks unless explicitly intended.
      const codeBlocks = div.querySelectorAll('pre, code');
      codeBlocks.forEach(cb => {
        console.log('[Clean] 🗑 Removing code block artifact');
        cb.remove();
      });

      // Scan for Link Density (Spam detection)
      const paragraphs = div.querySelectorAll('p');
      paragraphs.forEach(p => {
        const links = p.querySelectorAll('a');
        const textLen = p.textContent?.length || 0;
        if (links.length > 3 || (textLen > 0 && links.length / textLen > 0.05)) {
          // If a paragraph is just a bunch of links or has too many, unwrap links but keep text
          console.log('[Clean] 🔗 High link density detected - sanitizing');
          links.forEach(a => {
            const span = document.createElement('span');
            span.textContent = a.textContent;
            a.replaceWith(span);
          });
        }
      });

      // 2. Local Dedup (Jaccard)
      const allBlocks = div.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li, blockquote');
      console.log('[Clean] Total blocks for dedup:', allBlocks.length);

      // Extract meaningful word tokens: lowercase, NFC, strip digits + punctuation
      function tokenize(text: string): Set<string> {
        const normalized = text.toLowerCase().normalize('NFC');
        const words = normalized
          .replace(/\d+/g, '')                        // strip numbers (noise like 1111)
          .replace(/[^\w\s\u00C0-\u024F\u1E00-\u1EFF]/g, ' ')  // strip punctuation/emoji
          .split(/\s+/)
          .filter(w => w.length >= 2);                // skip very short tokens
        return new Set(words);
      }

      // Jaccard similarity between two word sets
      function jaccard(a: Set<string>, b: Set<string>): number {
        if (a.size === 0 && b.size === 0) return 1;
        if (a.size === 0 || b.size === 0) return 0;
        let intersect = 0;
        a.forEach(w => { if (b.has(w)) intersect++; });
        const union = a.size + b.size - intersect;
        return intersect / union;
      }

      const THRESHOLD = 0.82; // ≥82% word overlap → near-duplicate
      const kept: Array<{ el: Element; tokens: Set<string>; text: string }> = [];
      let removed = 0;
      const dedupedDiv = document.createElement('div');

      allBlocks.forEach((el, idx) => {
        const t = el.textContent?.trim() ?? '';
        if (!t || t.length < 15) {
          dedupedDiv.appendChild(el.cloneNode(true));
          return;
        }
        const tokens = tokenize(t);
        const isDup = kept.some(k => jaccard(tokens, k.tokens) >= THRESHOLD);

        if (!isDup) {
          kept.push({ el, tokens, text: t });
          dedupedDiv.appendChild(el.cloneNode(true));
        } else {
          removed++;
        }
      });

      console.log(`[Clean] Dedup done — removed: ${removed}`);

      // 3. Viral 2026: Backend Semantic Polish
      const interimHTML = dedupedDiv.innerHTML;

      console.log('[Clean] 🚀 Calling Viral 2026 Backend Polish...');
      const response = await apiClient.post<{ data: { content: string } }>('/api/v1/content/clean', {
        content: interimHTML
      });

      if (response && response.data && response.data.content) {
        const finalContent = response.data.content;
        isInternalUpdating = true;
        editor.commands.setContent(finalContent, false);
        const cleaned = stripMarks(editor.getHTML());
        onChange(cleaned);
        updateMetrics();
        isInternalUpdating = false;
        console.log('[Clean] ✨ Viral 2026 Polish Complete');
      } else {
        // Fallback to deduped content if backend fails
        isInternalUpdating = true;
        editor.commands.setContent(interimHTML, false);
        onChange(stripMarks(editor.getHTML()));
        isInternalUpdating = false;
        console.log('[Clean] Backend failed, applied local dedup only');
      }

    } catch (err) {
      console.error('[Clean] Viral Clean Failed:', err);
    } finally {
      cleanStatus = 'done';
      setTimeout(() => cleanStatus = 'idle', 2000);
    }
  }

  function stripMarks(html: string): string {
    return html.replace(/<mark[^>]*>|<\/mark>/g, '');
  }

  // Stable ID Hashing (djb2) to prevent tooltip flickering
  function generateStableId(text: string, message: string): string {
    let hash = 5381;
    const str = text + message;
    for (let i = 0; i < str.length; i++) {
      hash = (hash * 33) ^ str.charCodeAt(i);
    }
    return (hash >>> 0).toString(36);
  }
  
  const containerClass = $derived(`tiptap-shell flex flex-col w-full h-full ${
    internalFullScreen
      ? 'fixed inset-0 z-[99999] bg-[#0a0d14]'
      : (editable
          ? 'bg-[#0d1117] border ' + (isFocused ? 'border-blue-500/40' : 'border-white/10') + ' overflow-hidden shadow-2xl'
          : 'bg-transparent border-none overflow-visible')
  } transition-all duration-300 rounded-none`);

  function updateMetrics() {
    if (!editor) return;
    const text = editor.getText();
    charCount = text.length;
    wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  }

  onMount(() => {
    editor = new Editor({
      element,
      content,
      editable,
      extensions: getEditorExtensions(placeholder),
      editorProps,
      onUpdate: () => {
        if (isInternalUpdating) return;
        const html = editor?.getHTML() ?? '';
        onChange(stripMarks(html));
        updateMetrics();
      },
    });
    updateMetrics();

    // Cerberus 2026: Attach visual-overlay events
    element.addEventListener('annotation-hover', handleAnnotationHover);
    element.addEventListener('annotation-leave', handleAnnotationLeave);
  });

  onDestroy(() => {
    if (editor) editor.destroy();
    if (element) {
      element.removeEventListener('annotation-hover', handleAnnotationHover);
      element.removeEventListener('annotation-leave', handleAnnotationLeave);
    }
  });

  $effect(() => {
    if (editor && !editor.isDestroyed) editor.setEditable(editable);
  });

  $effect(() => {
    if (!editor || editor.isDestroyed) return;
    
    // Defensive content stabilization
    const normalizedContent = content || "<p></p>";
    const currentHTML = editor.getHTML();
    
    const cleanNew = stripMarks(normalizedContent).trim().replace(/\n/g, '');
    const cleanCurrent = stripMarks(currentHTML).trim().replace(/\n/g, '');

    if (cleanNew !== cleanCurrent) {
      isInternalUpdating = true;
      const { from, to } = editor.state.selection;
      editor.commands.setContent(normalizedContent, false);
      if (isFocused) {
        try { editor.commands.setTextSelection({ from, to }); } catch (e) {}
      }
      updateMetrics();
      isInternalUpdating = false;
    }
  });

  // Cerberus 2026: Sustainable Highlighting Sync
  $effect(() => {
    if (!editor || editor.isDestroyed) return;
    
    // Track annotations as dependency
    const _annotationsTrigger = annotations;
    
    // Dispatch to the plugin instead of mutating the doc with marks
    editor.view.dispatch(
      editor.state.tr.setMeta(AnnotationPluginKey, {
        type: 'SET_ANNOTATIONS',
        annotations: _annotationsTrigger || []
      })
    );
  });

  function handleAnnotationHover(e: Event) {
    if (isFixing) return;
    const customEvent = e as CustomEvent;
    const data = customEvent.detail;
    if (!data || !data.id) return;

    tooltipX = data.x;
    tooltipY = data.y - 12;
    tooltipText = data.message;
    tooltipType = data.type;
    tooltipId = data.id;
    tooltipSnippet = data.text;
    tooltipFrom = data.from;
    tooltipTo = data.to;
    tooltipVisible = true;
  }

  function handleAnnotationLeave() {
    if (!isFixing) {
      tooltipVisible = false;
    }
  }


  // Rule R82.48: Viewport Reliability — Use a portal to bypass stacking context issues
  function portal(node: HTMLElement) {
    document.body.appendChild(node);
    return {
      destroy() {
        if (node.parentNode) node.parentNode.removeChild(node);
      }
    };
  }

  async function handleFix() {
    if (!onfix || isFixing || !tooltipSnippet) return;
    isFixing = true;
    try {
      const newText = await onfix(tooltipSnippet, tooltipType, tooltipText);
      if (newText && editor) {
        // Use the precise positions from the decoration hover
        const { state, view } = editor;
        const tr = state.tr.insertText(newText, tooltipFrom, tooltipTo);
        view.dispatch(tr);
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
      onClean={handleClean}
      fullScreen={internalFullScreen}
      onToggleFullScreen={toggleFullScreen}
    />
  {/if}

  <div
    class="flex-1 overflow-y-auto document-scroll {internalFullScreen ? 'bg-[#0a0d14]' : 'bg-[#0d1117] p-6'}"
    onmouseleave={() => { if (!isFixing) tooltipVisible = false; }}
  >
    <div class="
      {internalFullScreen ? 'max-w-4xl mx-auto my-0 bg-[#0f172a] min-h-screen px-20 py-16 border-x border-white/5' : 'max-w-4xl mx-auto my-8 bg-[#111827] shadow-2xl min-h-[700px] px-16 py-12 border border-white/5'}
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
  <div use:portal>
    <AnnotationTooltip bind:visible={tooltipVisible} x={tooltipX} y={tooltipY} type={tooltipType} text={tooltipText} {isFixing} onFix={handleFix} />
  </div>

<style>
  @reference "tailwindcss";
  :global(.tiptap-content) { @apply outline-none text-white/90 leading-relaxed; }
  :global(.tiptap-content p) { @apply my-4; }
  :global(.tiptap-content h1) { @apply text-3xl font-black mb-6 text-white; }
  :global(.tiptap-content h2) { @apply text-2xl font-bold mb-4 mt-8 text-white/80; }
  :global(.tiptap-content h3) { @apply text-xl font-bold mb-3 mt-6 text-white/70; }
  :global(.tiptap-content img) { @apply rounded-lg shadow-xl my-8 mx-auto border border-white/5; }
</style>
