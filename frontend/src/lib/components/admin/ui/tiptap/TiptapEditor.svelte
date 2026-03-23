<script lang="ts">
  import { onMount, onDestroy, untrack } from 'svelte';
  import { Editor } from '@tiptap/core';
  import { getEditorExtensions, editorProps } from './core/editor-config';
  import { AnnotationPluginKey } from './core/AnnotationPlugin';
  import type { EditorAnnotation, ToolbarAction } from '$lib/types';

  import Toolbar from './ui/Toolbar.svelte';
  import MediaVaultModal from "../../../media/MediaVaultModal.svelte";
  import LinkDialog from './ui/LinkDialog.svelte';
  import StatusBar from './ui/StatusBar.svelte';
  import AnnotationTooltip from './ui/AnnotationTooltip.svelte';
  import ImageBubbleMenu from './ui/ImageBubbleMenu.svelte';
  import type { MediaAsset } from '$lib/state/types';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { apiClient } from '$lib/utils/apiClient';

  let {
    content = $bindable(),
    onChange = () => {},
    editable = true,
    placeholder = "Start writing...",
    assets = $bindable([] as (MediaAsset | string)[]),
    selectedAvatarUrl = $bindable(null as string | null),
    selectedAssetIndex = $bindable(0),
    fullScreen = false,
    onToggleFullScreen = null,
    toolbarActions = [] as ToolbarAction[],
    annotations = [] as EditorAnnotation[],
    onfix = null,
    onblur = () => {},
    campaignId = undefined,
  }: {
    content?: string;
    onChange?: (val: string) => void;
    editable?: boolean;
    placeholder?: string;
    assets?: (MediaAsset | string)[];
    selectedAvatarUrl?: string | null;
    selectedAssetIndex?: number;
    fullScreen?: boolean;
    onToggleFullScreen?: (() => void) | null;
    toolbarActions?: ToolbarAction[];
    annotations?: EditorAnnotation[];
    onfix?: ((snippet: string, type: string, message: string) => Promise<string | null>) | null;
    onblur?: () => void;
    campaignId?: string;
  } = $props();

  let internalFullScreen = $state<boolean>(fullScreen);

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

  let showMediaVault = $state(false);
  let showLinkDialog = $state(false);
  let currentLinkUrl = $state('');
  
  // Guard against double-click bleed-through from dialog
  let lastDialogCloseAt = 0;
  $effect(() => {
    if (!showMediaVault) lastDialogCloseAt = Date.now();
  });

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
  let tooltipHideTimeout: ReturnType<typeof setTimeout> | null = null;
  let isHoveringTooltip = $state(false);
  let isInternalUpdating = false;
  let cleanStatus = $state<'idle' | 'cleaning' | 'done'>('idle');

  // Image Menu tracking
  let imageMenuVisible = $state(false);
  let imageMenuX = $state(0);
  let imageMenuY = $state(0);
  let blockClicks = $state(false);
  let lastInternalActionAt = 0;
  let isSyncLocked = false;

  // ✦ Cerberus 2026: Frontend Clean — Jaccard near-duplicate dedup + Viral 2026 Polish (Phase 76.9)
  // Extract meaningful word tokens: lowercase, NFC, strip digits + punctuation (Viral 2026 Core)
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

      // 2. Structural Dedup (Viral 2026 Edition)
      // Rule: Identify near-duplicate blocks while preserving the document hierarchy.
      const THRESHOLD = 0.85; 
      const keptTokens: Array<{ tokens: Set<string>; el: Element }> = [];
      let removedCount = 0;

      // We only dedup top-level blocks or list items to avoid destroying nested structures like figure/img
      const blocksToDedup = div.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li, blockquote');
      
      blocksToDedup.forEach(el => {
        const text = el.textContent?.trim() || "";
        if (text.length < 20) return; 

        const tokens = tokenize(text);
        const duplicate = keptTokens.find(k => jaccard(tokens, k.tokens) >= THRESHOLD);

        if (duplicate) {
          el.remove();
          removedCount++;
        } else {
          keptTokens.push({ tokens, el });
        }
      });

      console.log(`[Clean] Dedup done — removed: ${removedCount} blocks`);

      // 3. Viral 2026: Backend Semantic Polish
      const interimHTML = div.innerHTML;

      console.log('[Clean] 🚀 Calling Neural Backend Polish...');
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
        console.log('[Clean] ✨ Neural Polish Complete');
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
  
  const containerClass = $derived(`tiptap-shell flex flex-col w-full ${
    internalFullScreen
      ? 'fixed inset-0 z-[99999] bg-[#0a0d14]'
      : (editable
          ? 'bg-transparent'
          : 'bg-transparent overflow-visible')
  }`);

  let metricsTimer: ReturnType<typeof setTimeout> | null = null;
  function updateMetrics() {
    if (metricsTimer) return; // Already scheduled
    metricsTimer = setTimeout(() => {
      metricsTimer = null;
      if (!editor) return;
      const text = editor.getText();
      charCount = text.length;
      wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
    }, 300);
  }

  onMount(() => {
    if (content === undefined) content = "";
    editor = new Editor({
      element,
      content,
      editable,
      extensions: getEditorExtensions(placeholder),
      editorProps,
      onUpdate: () => {
        if (isInternalUpdating) return;
        const html = editor?.getHTML() ?? '';
        const cleaned = stripMarks(html);
        content = cleaned;
        onChange(cleaned);
        updateMetrics();
      },
    });
    updateMetrics();

    // Cerberus 2026: Attach visual-overlay events to window for portal-safe tracking
    window.addEventListener('annotation-hover', handleAnnotationHover);
    window.addEventListener('annotation-leave', handleAnnotationLeave);
  });

  onDestroy(() => {
    if (editor) editor.destroy();
    if (metricsTimer) clearTimeout(metricsTimer);
    if (imageScanTimer) clearTimeout(imageScanTimer);
    window.removeEventListener('annotation-hover', handleAnnotationHover);
    window.removeEventListener('annotation-leave', handleAnnotationLeave);
  });

  $effect(() => {
    if (showMediaVault || showLinkDialog) {
      if (imageMenuVisible) imageMenuVisible = false;
    }
  });

  $effect(() => {
    if (editor && !editor.isDestroyed) editor.setEditable(editable);
  });

  $effect(() => {
    // CNS V2.2: Stabilized Content Sync (Zero-Flicker)
    if (!editor || editor.isDestroyed || isInternalUpdating || isSyncLocked) return;
    
    const normalizedContent = content || "<p></p>";
    
    untrack(() => {
        const currentHTML = editor!.getHTML();
        
        // Use a more relaxed comparison to avoid loops (ignore whitespace between tags)
        const cleanContent = (html: string) => html.replace(/\s+/g, ' ').replace(/>\s+</g, '><').trim();
        
        if (cleanContent(normalizedContent) !== cleanContent(currentHTML)) {
            console.log('[Tiptap] Prop-driven content sync triggered');
            isInternalUpdating = true;
            const { from, to } = editor!.state.selection;
            editor!.commands.setContent(normalizedContent, false);
            
            // Re-sync selection if it was focused
            if (isFocused) {
                try { editor!.commands.setTextSelection({ from, to }); } catch (e) {}
            }
            setTimeout(() => { isInternalUpdating = false; }, 50);
        }
    });
  });

  // Elite V2.2: Scan Editor for Images — debounced to avoid regex on every keystroke
  let imageScanTimer: ReturnType<typeof setTimeout> | null = null;
  $effect(() => {
    if (!editor || editor.isDestroyed || isInternalUpdating) return;
    
    // Track content as dependency
    const _trigger = content; 
    
    // Debounce: only scan after 500ms of inactivity
    if (imageScanTimer) clearTimeout(imageScanTimer);
    imageScanTimer = setTimeout(() => {
      untrack(() => {
        if (!editor || editor.isDestroyed) return;
        const html = editor.getHTML();
        const imgRegex = /<img[^>]+src=["']([^"']+)["']/g;
        const found: string[] = [];
        let match;
        while ((match = imgRegex.exec(html)) !== null) {
          let src = match[1];
          if (src && !found.includes(src)) found.push(src);
        }
        
        const currentUrls = assets.map(a => typeof a === 'string' ? a : (a.file_path || a.url || ''));
        const hasChanged = found.length !== currentUrls.length || found.some(url => !currentUrls.includes(url));
        
        if (hasChanged) {
          assets = found;
        }
      });
    }, 500);
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
    if (tooltipHideTimeout) {
      clearTimeout(tooltipHideTimeout);
      tooltipHideTimeout = null;
    }
    const customEvent = e as CustomEvent;
    const data = customEvent.detail;
    if (!data || !data.id) return;

    tooltipX = data.x;
    tooltipY = data.y - 10; // Rule V2026: Small offset to avoid blocking initial hover
    tooltipText = data.message;
    tooltipType = data.type;
    tooltipId = data.id;
    tooltipSnippet = data.text;
    tooltipFrom = data.from;
    tooltipTo = data.to;
    tooltipVisible = true;
  }

  function handleAnnotationLeave() {
    if (isFixing || isHoveringTooltip) return;
    
    // Rule V2026: Substantial delay (600ms) to allow travel to tooltip
    if (tooltipHideTimeout) clearTimeout(tooltipHideTimeout);
    tooltipHideTimeout = setTimeout(() => {
      if (!isHoveringTooltip && !isFixing) {
        tooltipVisible = false;
      }
    }, 600);
  }

  function handleTooltipEnter() {
    isHoveringTooltip = true;
    if (tooltipHideTimeout) {
      clearTimeout(tooltipHideTimeout);
      tooltipHideTimeout = null;
    }
  }

  function handleTooltipLeave() {
    isHoveringTooltip = false;
    handleAnnotationLeave();
  }

  // Rule R82.48: Viewport Reliability — Portal for stacking context bypass
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

  function handleFocusOut(e: FocusEvent) {
    if (!onblur) return;
    const ct = e.currentTarget;
    const rt = e.relatedTarget;
    if (!rt || !(ct instanceof Node) || !ct.contains(rt as Node)) {
      onblur();
    }
  }

  function handleImageClick(e: MouseEvent | KeyboardEvent) {
    const target = e.target as HTMLElement;
    let img = target.closest('.tiptap-content img') as HTMLImageElement | null;
    // Also handle clicks on figcaption
    if (!img && target.closest('figcaption')) {
      img = target.closest('figure')?.querySelector('img') as HTMLImageElement | null;
    }
    if (img && editor) {
      editor.commands.focus();
      const pos = editor.view.posAtDOM(img, 0);
      if (pos >= 0) {
        const rect = img.getBoundingClientRect();
        imageMenuX = rect.left + rect.width / 2;
        imageMenuY = rect.top - 10;
        imageMenuVisible = true;
        editor.commands.setNodeSelection(pos);
      }
    } else if (!target.closest('.image-bubble-menu')) {
      imageMenuVisible = false;
    }
  }

  function handleDoubleClick(e: MouseEvent) {
    if (blockClicks) return;
    if (Date.now() - lastInternalActionAt < 800) return;
    if (Date.now() - lastDialogCloseAt < 500) return; // Prevent double-click bleed-through
    const target = e.target as HTMLElement;
    const img = target.closest('.tiptap-content img') as HTMLImageElement | null;
    if (img && editor) {
      showMediaVault = true;
      imageMenuVisible = false;
    }
  }

</script>

<div 
  class={containerClass}
  onfocusout={handleFocusOut}
>
  {#if editable}
    <Toolbar
      {editor}
      {toolbarActions}
      {annotations}
      onOpenImage={() => showMediaVault = true}
      onOpenLink={() => { currentLinkUrl = editor?.getAttributes('link').href || ''; showLinkDialog = true; }}
      onClearHighlights={() => editor?.commands.clearAllAnnotations()}
      onClean={handleClean}
      fullScreen={internalFullScreen}
      onToggleFullScreen={toggleFullScreen}
    />
  {/if}

  <div
    class="w-full overflow-y-auto document-scroll {internalFullScreen ? 'bg-[#0a0d14] flex-1' : 'bg-transparent max-h-[650px]'}"
    onclick={handleImageClick}
    ondblclick={handleDoubleClick}
    onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleImageClick(e); }}
    role="button"
    tabindex="0"
  >
    <div class="
      {internalFullScreen ? 'max-w-4xl mx-auto my-0 bg-[#0f172a] min-h-screen px-20 py-16 border-x border-white/5' : 'w-full bg-transparent min-h-[400px] px-6 py-4'}
      {!editable ? 'cursor-default' : ''}
    ">
      <div bind:this={element} class="tiptap-content prose prose-invert max-w-none {!editable ? 'opacity-90' : ''}"></div>
    </div>
  </div>

  {#if editable}
    <StatusBar {wordCount} {charCount} {isFocused} readTime="~{Math.ceil(wordCount/200)} phút đọc" />
  {/if}
</div>

  <div use:portal>
    <MediaVaultModal
      isOpen={showMediaVault}
      onClose={() => showMediaVault = false}
      {campaignId}
      bind:assets
      bind:selectedAvatarUrl
      bind:selectedAssetIndex
      onSelect={(url) => {
        if (editor) {
          blockClicks = true;
          imageMenuVisible = false;
          const safeUrl = resolveMediaUrl(url);
          
          // V22: Robust Insertion
          isSyncLocked = true;
          
          // Defer focus to avoid click-through when portal unmounts
          setTimeout(() => {
            if (!editor || editor.isDestroyed) { isSyncLocked = false; return; }
            
            if (editor.isActive('image')) {
              editor.chain().focus().updateAttributes('image', { src: safeUrl }).run();
            } else {
              editor.chain().focus().setImage({ src: safeUrl }).run();
            }
            
            // Final sync
            const cleaned = stripMarks(editor.getHTML());
            content = cleaned;
            onChange(cleaned);
            
            setTimeout(() => { 
              blockClicks = false; 
              isSyncLocked = false;
            }, 300);
          }, 50);
        }
      }}
    />
  </div>

  <div use:portal>
  let currentLinkData = $state({ url: '', title: '', target: null as string | null, rel: null as string | null });

  // ... (inside the toolbar open link handler)
  // onOpenLink={() => { 
  //   const attrs = editor?.getAttributes('link');
  //   currentLinkData = { 
  //     url: attrs?.href || '', 
  //     title: attrs?.title || '', 
  //     target: attrs?.target || null, 
  //     rel: attrs?.rel || null 
  //   }; 
  //   showLinkDialog = true; 
  // }}

// ... (in the template)
    <LinkDialog 
      bind:show={showLinkDialog} 
      currentData={currentLinkData} 
      onApply={(data) => {
        if (data.url && editor) {
          editor.chain().focus().setLink({ 
            href: data.url, 
            title: data.title, 
            target: data.target || undefined, 
            rel: data.rel || undefined 
          }).run();
        } else if (editor) {
          editor.chain().focus().unsetLink().run();
        }
      }} 
    />
  </div>
  <div use:portal>
    <AnnotationTooltip 
      bind:visible={tooltipVisible} 
      x={tooltipX} 
      y={tooltipY} 
      type={tooltipType} 
      text={tooltipText} 
      {isFixing} 
      onFix={handleFix} 
      onMouseEnter={handleTooltipEnter}
      onMouseLeave={handleTooltipLeave}
    />
  </div>

  {#if editor && editable && imageMenuVisible && !blockClicks && !showMediaVault && !showLinkDialog}
  <div
    use:portal
    class="fixed z-[3000] -translate-x-1/2 -translate-y-full pointer-events-auto transition-all duration-75 ease-out image-bubble-menu"
    style="left: {imageMenuX}px; top: {imageMenuY}px;"
  >
    <ImageBubbleMenu
      {editor}
      onReplace={() => {
        if (!blockClicks) showMediaVault = true;
      }}
      onClose={() => imageMenuVisible = false}
    />
  </div>
  {/if}

<style>
  @reference "tailwindcss";
  
  .document-scroll::-webkit-scrollbar {
    width: 4px;
  }
  .document-scroll::-webkit-scrollbar-track {
    background: transparent;
  }
  .document-scroll::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    transition: background 0.3s;
  }
  .document-scroll:hover::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.15);
  }
  
  :global(.tiptap-content) { @apply outline-none text-white/90 leading-relaxed; }
  :global(.tiptap-content p) { @apply my-4; }
  :global(.tiptap-content.prose) {
    --tw-prose-links: #00f3ff;
    --tw-prose-invert-links: #00f3ff;
  }
  :global(.tiptap-content h1) { @apply text-3xl font-black mb-6 text-white; }
  :global(.tiptap-content h2) { @apply text-2xl font-bold mb-4 mt-8 text-white/80; }
  :global(.tiptap-content h3) { @apply text-xl font-bold mb-3 mt-6 text-white/70; }
  :global(.tiptap-content img) { @apply rounded-lg my-4 mx-auto cursor-pointer border-2 border-transparent transition-all duration-200; }
  :global(.tiptap-content img.ProseMirror-selectednode) { @apply border-blue-500/50 shadow-lg shadow-blue-500/10; }

  /* Figure / Caption */
  :global(.tiptap-content figure.image-figure) {
    @apply my-6 mx-auto text-center;
  }
  :global(.tiptap-content figure.image-figure img) {
    @apply my-0;
  }
  :global(.tiptap-content figure.image-figure figcaption) {
    @apply text-xs text-white/40 mt-2 italic font-light tracking-wide;
  }

  /* Premium Highlighting (Neural Studio) */
  :global(.xohi-annotation) {
    @apply cursor-help transition-all duration-300 border-b-2;
    padding: 1px 0;
  }
  
  :global(.xohi-annotation.severity-low) {
    @apply bg-emerald-500/10 border-emerald-500/30 text-emerald-200/90;
  }
  :global(.xohi-annotation.severity-low:hover) {
    @apply bg-emerald-500/20 border-emerald-500/50;
  }

  :global(.xohi-annotation.severity-medium) {
    @apply bg-amber-500/15 border-amber-400/40 text-amber-100/90;
  }
  :global(.xohi-annotation.severity-medium:hover) {
    @apply bg-amber-500/25 border-amber-400/60;
  }

  :global(.xohi-annotation.severity-high) {
    @apply bg-red-500/20 border-red-500/50 text-red-100/90;
    animation: annotation-pulse 2s infinite ease-in-out;
  }
  :global(.xohi-annotation.severity-high:hover) {
    @apply bg-red-500/30 border-red-500/70;
  }

  :global(.xohi-annotation.type-fixed) {
    @apply bg-transparent border-transparent text-white/90 cursor-default;
    border-bottom: 2px dashed rgba(16, 185, 129, 0.4);
    text-decoration: none;
    animation: none;
  }

  /* Fixed-area: AI-repaired segment — professional emerald pulse × 3, then static */
  :global(.xohi-annotation.type-fixed-area) {
    background: rgba(16, 185, 129, 0.10);
    border-bottom: 2px solid rgba(16, 185, 129, 0.55);
    color: rgba(167, 243, 208, 0.95);
    cursor: help;
    animation: fixed-area-pulse 1.4s ease-in-out 3;
  }
  :global(.xohi-annotation.type-fixed-area:hover) {
    background: rgba(16, 185, 129, 0.20);
    border-bottom-color: rgba(52, 211, 153, 0.8);
  }
  @keyframes fixed-area-pulse {
    0%   { background: rgba(16, 185, 129, 0.10); box-shadow: none; }
    50%  { background: rgba(16, 185, 129, 0.30); box-shadow: 0 0 8px rgba(16, 185, 129, 0.35); }
    100% { background: rgba(16, 185, 129, 0.10); box-shadow: none; }
  }

  @keyframes annotation-pulse {
    0% { background-color: rgba(239, 68, 68, 0.15); }
    50% { background-color: rgba(239, 68, 68, 0.3); }
    100% { background-color: rgba(239, 68, 68, 0.15); }
  }
</style>
