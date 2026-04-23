<script lang="ts">
  import { onMount, onDestroy, untrack, tick } from 'svelte';
  import { Editor } from '@tiptap/core';
  import { getEditorExtensions, editorProps } from './core/editor-config';
  import { AnnotationPluginKey } from './core/AnnotationPlugin';
  import type { EditorAnnotation, ToolbarAction } from '$lib/types';

  import Toolbar from './ui/Toolbar.svelte';
  import MediaVaultModal from "../../../media/MediaVaultModal.svelte";
  import LinkDialog from './ui/LinkDialog.svelte';
  import StatusBar from './ui/StatusBar.svelte';
  import AnnotationTooltip from './ui/AnnotationTooltip.svelte';
  import LinkBubbleMenu from './ui/LinkBubbleMenu.svelte';
  import ImageBubbleMenu from './ui/ImageBubbleMenu.svelte';
  import type { MediaAsset } from '$lib/state/types';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { apiClient } from '$lib/utils/apiClient';
  import { xohiActions, type CleanOptions } from '$lib/state/xohiActions';

  let {
    content = $bindable(),
    onChange = () => {},
    editable = true,
    placeholder = "Start writing...",
    assets = $bindable(),
    selectedAvatarUrl = $bindable(),
    selectedAssetIndex = $bindable(),
    fullScreen = false,
    onToggleFullScreen = null,
    toolbarActions = [] as ToolbarAction[],
    annotations = [] as EditorAnnotation[],
    onfix = null,
    onblur = () => {},
    campaignId = undefined,
    flex = false,
    onClean = null,
    syncAssetsMode = 'append',
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
    flex?: boolean;
    onClean?: (() => Promise<string | null>) | null;
    syncAssetsMode?: 'strict' | 'append';
  } = $props();

  let internalFullScreen = $state<boolean>(fullScreen);
  let showSource = $state(false);

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

  let editor = $state.raw<Editor | null>(null);
  let element: HTMLElement;
  let isFocused = $state(false);
  let wordCount = $state(0);
  let charCount = $state(0);

  let showMediaVault = $state(false);
  let showLinkDialog = $state(false);
  let currentLinkData = $state({ url: '', title: '', target: null as string | null, rel: null as string | null });
  
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
  let linkMenuVisible = $state(false);
  let linkMenuX = $state(0);
  let linkMenuY = $state(0);
  let blockClicks = $state(false);
  let lastInternalActionAt = 0;
  let isSyncLocked = false;

  // ✦ Cerberus NEURAL XOHI: Frontend Clean — Jaccard near-duplicate dedup + Viral NEURAL XOHI Polish (Phase 76.9)
  // Extract meaningful word tokens: lowercase, NFC, strip digits + punctuation (Viral NEURAL XOHI Core)
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

  async function handleClean(options: CleanOptions = { stripFont: true, stripAlign: true, stripRedundantWrappers: true, stripEmpty: true }) {
    if (!editor || editor.isDestroyed) {
      console.warn('[Clean] Editor not ready');
      return;
    }
    cleanStatus = 'cleaning';

    try {
      const html = editor.getHTML();
      
      // CNS V85.2: Use unified system cleaning logic
      const cleanedHTML = await xohiActions.runClean(html, options);

      if (cleanedHTML) {
        // Elite V2.2 Deep Sync: Lock everything to prevent race conditions
        isInternalUpdating = true;
        isSyncLocked = true;

        editor.commands.setContent(cleanedHTML, false);

        await tick();

        // CNS V84.5: DIRECT SYNC
        const finalContent = stripMarks(cleanedHTML);
        content = finalContent;
        onChange(finalContent);
        updateMetrics();

        // Safety lock
        setTimeout(() => {
            isInternalUpdating = false;
            isSyncLocked = false;
        }, 150);
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
      : (flex 
          ? 'flex-1 h-full bg-transparent min-h-0' 
          : (editable ? 'bg-transparent' : 'bg-transparent overflow-visible'))
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
    if (assets === undefined) assets = [];
    if (selectedAvatarUrl === undefined) selectedAvatarUrl = null;
    if (selectedAssetIndex === undefined) selectedAssetIndex = 0;
    
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
    if (editor && !editor.isDestroyed) {
      if (editor.isEditable !== editable) {
        untrack(() => {
          isInternalUpdating = true;
          editor!.setEditable(editable);
          setTimeout(() => { isInternalUpdating = false; }, 0);
        });
      }
    }
  });

  $effect(() => {
    // CNS V2.2: Stabilized Content Sync (Zero-Flicker)
    if (!editor || editor.isDestroyed || isInternalUpdating || isSyncLocked) return;
    
    const normalizedContent = content || "<p></p>";

    untrack(() => {
        const currentHTML = editor!.getHTML();

        // CNS V2.2: Deterministic HTML Normalization for Cross-Browser Comparison
        const normalizeHTML = (html: string) => {
            if (typeof document === 'undefined') return html.trim();
            const div = document.createElement('div');
            
            // CNS V2.2: Strip temporary marks for comparison to prevent sync loops
            const clean = stripMarks(html)
                .replace(/&nbsp;/g, ' ')
                .replace(/\s+/g, ' ')
                .trim();

            div.innerHTML = clean;

            // Rule 3: Recursive pruning of empty nodes to match Backend NASP logic
            const prune = (node: Node) => {
                for (let i = node.childNodes.length - 1; i >= 0; i--) {
                    const child = node.childNodes[i];
                    if (child.nodeType === 1) { // Element
                        prune(child);
                        const el = child as HTMLElement;
                        const isContainer = ['P', 'DIV', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'STRONG', 'B', 'EM', 'I', 'SPAN'].includes(el.tagName);
                        const isEmpty = el.innerHTML.replace(/&nbsp;/g, '').replace(/\s+/g, '').trim() === '' || el.innerHTML === '<br>';
                        if (isContainer && isEmpty) {
                            el.remove();
                        }
                    }
                }
            };
            prune(div);

            return div.innerHTML.replace(/>\s+</g, '><');
        };

        if (normalizeHTML(normalizedContent) !== normalizeHTML(currentHTML)) {
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
        
        if (syncAssetsMode === 'append') {
          const newFound = found.filter(url => !currentUrls.includes(url));
          if (newFound.length > 0) {
            assets = [...assets, ...newFound];
          }
        } else {
          const hasChanged = found.length !== currentUrls.length || found.some(url => !currentUrls.includes(url));
          if (hasChanged) {
            assets = found;
          }
        }
      });
    }, 500);
  });

  // Cerberus NEURAL XOHI: Sustainable Highlighting Sync
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
    tooltipY = data.y - 10; // Rule NEURAL XOHI: Small offset to avoid blocking initial hover
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
    
    // Rule NEURAL XOHI: Substantial delay (600ms) to allow travel to tooltip
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

    // Handle link clicks/selection
    const link = target.closest('.tiptap-content a') as HTMLAnchorElement | null;
    if (link && editor) {
      editor.commands.focus();
      const pos = editor.view.posAtDOM(link, 0);
      if (pos >= 0) {
        const rect = link.getBoundingClientRect();
        linkMenuX = rect.left + rect.width / 2;
        linkMenuY = rect.top - 10;
        linkMenuVisible = true;
        // Also update data for potential edit
        const attrs = editor.getAttributes('link');
        currentLinkData = { 
          url: attrs.href || '', 
          title: attrs.title || '', 
          target: attrs.target || null, 
          rel: attrs.rel || null 
        };
      }
    } else if (!target.closest('.link-bubble-menu')) {
      linkMenuVisible = false;
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
      onOpenLink={() => { 
        const attrs = editor?.getAttributes('link');
        currentLinkData = { 
          url: attrs?.href || '', 
          title: attrs?.title || '', 
          target: attrs?.target || null, 
          rel: attrs?.rel || null 
        }; 
        showLinkDialog = true; 
      }}
      onClearHighlights={() => editor?.commands.clearAllAnnotations()}
      onClean={onClean || handleClean}
      bind:showSource
      fullScreen={internalFullScreen}
      onToggleFullScreen={toggleFullScreen}
    />
  {/if}

  <div
    class="w-full flex flex-col overflow-y-auto document-scroll {internalFullScreen ? 'bg-[#0a0d14] flex-1 min-h-0' : (flex ? 'bg-transparent flex-1 min-h-0' : 'bg-transparent max-h-[650px]')}"
    onclick={(e) => { 
      if (e.target === e.currentTarget) editor?.commands.focus();
      handleImageClick(e); 
    }}
    ondblclick={handleDoubleClick}
    onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleImageClick(e); }}
    role="button"
    tabindex="0"
  >
    <div 
      class="
        {internalFullScreen ? 'w-full min-h-screen px-12 md:px-24 py-16 transition-all duration-300 flex flex-col' : (flex ? 'w-full bg-transparent flex-1 min-h-full px-6 py-4' : 'w-full bg-transparent min-h-[400px] px-6 py-4')}
        {!editable ? 'cursor-default' : 'cursor-text'}
      "
      onclick={() => { if (editable && !showSource) editor?.commands.focus(); }}
      role="presentation"
    >
      <div 
        bind:this={element} 
        class="tiptap-content prose prose-invert max-w-none {!editable ? 'opacity-90' : ''} {showSource ? 'hidden' : ''}"
      ></div>
      
      {#if showSource}
        <textarea
          bind:value={content}
          class="w-full {internalFullScreen ? 'flex-1 min-h-0' : 'min-h-[500px]'} bg-black/5 text-cyan-50/70 font-mono text-[11px] p-6 outline-none border border-white/5 rounded-xl resize-none leading-relaxed custom-scrollbar shadow-2xl"
          spellcheck="false"
          placeholder="HTML Source Code..."
        ></textarea>
      {/if}
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

  {#if linkMenuVisible && editor && !blockClicks}
    <div
      use:portal
      class="fixed z-[var(--z-admin-tiptap-link-bubble)] pointer-events-auto link-bubble-menu"
      style="left: {linkMenuX}px; top: {linkMenuY}px; transform: translate(-50%, -100%);"
      role="tooltip"
    >
      <LinkBubbleMenu
        {editor}
        onEdit={() => { showLinkDialog = true; linkMenuVisible = false; }}
        onClose={() => linkMenuVisible = false}
      />
    </div>
  {/if}

  {#if editor && editable && imageMenuVisible && !blockClicks && !showMediaVault && !showLinkDialog}
  <div
    use:portal
    class="fixed z-[var(--z-admin-tiptap-bubble-menu)] -translate-x-1/2 -translate-y-full pointer-events-auto transition-all duration-75 ease-out image-bubble-menu"
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
  :global(.tiptap-content p) { @apply my-2; }
  :global(.tiptap-content.prose) {
    --tw-prose-links: #00f3ff;
    --tw-prose-invert-links: #00f3ff;
  }
  :global(.tiptap-content h1) { @apply text-3xl font-black mb-4 text-white; }
  :global(.tiptap-content h2) { @apply text-2xl font-bold mb-2 mt-4 text-white/80; }
  :global(.tiptap-content h3) { @apply text-xl font-bold mb-1 mt-3 text-white/70; }
  :global(.tiptap-content img) { @apply rounded-lg my-2 mx-auto cursor-pointer border-2 border-transparent transition-all duration-200; }
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
  
  /* Enrich: AI Booster™ segment — liquid magenta glass */
  :global(.xohi-annotation.type-enrich) {
    background: rgba(236, 72, 153, 0.10);
    border-bottom: 2px solid rgba(236, 72, 153, 0.5);
    color: rgba(254, 215, 226, 0.95);
    cursor: help;
    animation: enrich-pulse 1.8s ease-in-out infinite;
  }
  :global(.xohi-annotation.type-enrich:hover) {
    background: rgba(236, 72, 153, 0.20);
    border-bottom-color: rgba(244, 114, 182, 0.8);
  }
  @keyframes enrich-pulse {
    0%   { background: rgba(236, 72, 153, 0.10); box-shadow: none; }
    50%  { background: rgba(236, 72, 153, 0.25); box-shadow: 0 0 12px rgba(236, 72, 153, 0.3); }
    100% { background: rgba(236, 72, 153, 0.10); box-shadow: none; }
  }

  @keyframes annotation-pulse {
    0% { background-color: rgba(239, 68, 68, 0.15); }
    50% { background-color: rgba(239, 68, 68, 0.3); }
    100% { background-color: rgba(239, 68, 68, 0.15); }
  }
</style>
