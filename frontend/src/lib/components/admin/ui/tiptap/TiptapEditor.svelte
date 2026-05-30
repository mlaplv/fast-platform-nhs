<script lang="ts">
  import { onMount, onDestroy, untrack, tick } from 'svelte';
  import { Editor } from '@tiptap/core';
  import { getEditorExtensions, editorProps } from './core/editor-config';
  import { AnnotationPluginKey } from './core/AnnotationPlugin';
  import type { EditorAnnotation, ToolbarAction } from '$lib/types';

  import Toolbar from './ui/Toolbar.svelte';
  import EditorOverlays from './parts/EditorOverlays.svelte';
  import StatusBar from './ui/StatusBar.svelte';
  import type { MediaAsset } from '$lib/state/types';
  import { xohiActions, type CleanOptions } from '$lib/state/xohiActions';
  import type { CopyrightResult, SEOResult, AIInspectResult, NeuralAnalysisController } from '$lib/state/types';
  import { normalizeHTML, stripMarks, beautifyHTML } from './utils/editorUtils';
  import { apiClient } from '$lib/utils/apiClient';
  import { getNanobot } from '$lib/state/nanobot.svelte';
  import { portal } from '$lib/core/actions/portal';
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import { createAnnotationManager } from './parts/AnnotationManager.svelte';
  import { createEditorHandlers } from './parts/EditorHandlers.svelte';
  import './TiptapEditor.css';
  import '$lib/styles/neural-highlights.css';

  let {
    content = $bindable(),
    onChange = () => {},
    editable = true,
    placeholder = "Start writing...",
    assets = $bindable(),
    selectedAvatarUrl = $bindable(),
    selectedAssetIndex = $bindable(),
    fullScreen = $bindable(),
    onToggleFullScreen = null,
    toolbarActions = [] as ToolbarAction[],
    annotations = [] as EditorAnnotation[],
    onfix = null,
    onblur = () => {},
    campaignId = undefined,
    flex = false,
    onClean = null,
    syncAssetsMode = 'append',
    analysisData = undefined,
    copyrightResult = null,
    seoResult = null,
    aiReadyResult = null,
    isCopyrightLoading = false,
    isSeoLoading = false,
    isAiLoading = false,
    isBoosting = false,
    isBulkFixing = false,
    isRewriting = false,
    runBulkFix = null,
    bulkFixLogs = [],
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
    onClean?: ((options?: CleanOptions, rawContent?: string) => Promise<string | null>) | null;
    syncAssetsMode?: 'strict' | 'append';
    analysisData?: NeuralAnalysisController | null;
    copyrightResult?: CopyrightResult | null;
    seoResult?: SEOResult | null;
    aiReadyResult?: AIInspectResult | null;
    isCopyrightLoading?: boolean;
    isSeoLoading?: boolean;
    isAiLoading?: boolean;
    isBoosting?: boolean;
    isBulkFixing?: boolean;
    isRewriting?: boolean;
    runBulkFix?: () => void;
    bulkFixLogs?: string[];
  } = $props();

  // Full screen state is now driven directly by the bindable fullScreen prop.

  let showSource = $state(false);
  
  // CNS V88.5: Auto-format HTML when entering source mode
  $effect(() => {
    if (showSource) {
      untrack(() => {
        content = beautifyHTML(content || '');
      });
    }
  });

  const toggleFullScreen = () => {
    if (onToggleFullScreen) {
      onToggleFullScreen();
    } else {
      fullScreen = !fullScreen;
      if (typeof window !== 'undefined') {
        document.body.style.overflow = fullScreen ? 'hidden' : '';
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
  let lastDialogCloseAt = 0;
  $effect(() => { if (!showMediaVault) lastDialogCloseAt = Date.now(); });

  const annManager = createAnnotationManager({
    getOnFix: () => onfix,
    getEditor: () => editor
  });
  let isInternalUpdating = $state(false);
  // CNS V89: Annotation loop guard — track last dispatched key to prevent redundant SET_ANNOTATIONS
  // CNS V93: Plain let — loop guard for annotation dispatch (plugin self-heals on doc change)
  let _lastAnnotationKey = '';

  // --- Elite V2.2 Auto-Leach Queue ---
  let leachQueue = $state<string[]>([]);
  let isLeaching = $state(false);

  async function runAutoLeach() {
    if (isLeaching || !editor || editor.isDestroyed) return;
    
    const externalFound = new Set<string>();
    const currentHostname = typeof window !== 'undefined' ? window.location.hostname : 'smartshop.test';

    const isSafeUrl = (url: string): boolean => {
      try {
        if (!url.startsWith('http')) return false;
        const parsed = new URL(url);
        // CNS V95: SSRF & Loopback Protection
        const blocked = ['localhost', '127.0.0.1', '0.0.0.0', '::1', currentHostname, 'smartshop.test', 'api.osmo.vn', 'admin.osmo.vn'];
        if (blocked.some(b => parsed.hostname.includes(b))) return false;
        // Private IP Ranges (RFC1918)
        if (/^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)/.test(parsed.hostname)) return false;
        return true;
      } catch {
        return false;
      }
    };

    // Phase 1: Intelligent Scan (ProseMirror AST traversal is 10x faster than regex)
    editor.view.state.doc.descendants((node) => {
      if (node.type.name === 'image') {
        const src = node.attrs.src;
        if (src && isSafeUrl(src)) {
          externalFound.add(src);
        }
      }
    });

    if (externalFound.size === 0) {
      getNanobot().showToast("Dạ sếp, không tìm thấy ảnh ngoại cần cào.", "info");
      return;
    }

    const targets = Array.from(externalFound);
    leachQueue = [...targets];
    isLeaching = true;
    const nanobot = getNanobot();

    // Store full asset metadata for SEO attribute injection
    interface LeachResult { src: string; width: number; height: number; alt: string; }
    const resultMap = new Map<string, LeachResult>();

    try {
      // Phase 2: Concurrent Neural Fetching (Elite V2.2 Parallelism)
      while (leachQueue.length > 0) {
        const batch = leachQueue.splice(0, 3);
        await Promise.allSettled(batch.map(async (url) => {
          try {
            const res = await apiClient.post('/api/v1/media/fetch-remote', {
              url,
              campaign_id: campaignId || undefined
            });

            if (res.status === 'success' && res.data?.file_path) {
              // Parse dimensions returned from backend (format: "750x422")
              const dims = (res.data.dimensions as string | undefined) || '750x0';
              const [w, h] = dims.split('x').map(Number);
              // Derive SEO alt from filename: strip extension, replace hyphens
              const rawFilename = (res.data.filename as string | undefined) || 'article-image';
              const altText = rawFilename.replace(/\.webp$/i, '').replace(/-/g, ' ');

              resultMap.set(url, {
                src: res.data.file_path as string,
                width: w || 750,
                height: h || 0,
                alt: altText,
              });

              if (campaignId) {
                await apiClient.post('/api/v1/media/link-to-post', {
                  asset_ids: [res.data.id],
                  post_id: campaignId,
                  post_type: 'article'
                }).catch(e => console.error("[Auto-Leach] Link failed", e));
              }
            }
          } catch (error) {
            console.error("[Auto-Leach] Lỗi cào ảnh:", url, error);
          }
        }));
      }

      // Phase 3: Atomic Transaction — O(N) one-pass, inject full SEO attrs
      if (resultMap.size > 0 && editor && !editor.isDestroyed) {
        let tr = editor.view.state.tr;
        editor.view.state.doc.descendants((node, pos) => {
          if (node.type.name === 'image' && resultMap.has(node.attrs.src)) {
            const result = resultMap.get(node.attrs.src)!;
            tr = tr.setNodeMarkup(pos, null, {
              ...node.attrs,
              src: result.src,
              // SEO: explicit dimensions prevent layout shift (CLS = 0)
              width: result.width,
              height: result.height > 0 ? result.height : null,
              // SEO: alt text from clean filename (inherit existing if already set)
              alt: node.attrs.alt || result.alt,
              // Performance: native lazy load + async decode
              loading: 'lazy',
              decoding: 'async',
              // Layout safety: never overflow container
              style: 'max-width: 100%; height: auto;',
            });
          }
        });

        if (tr.docChanged) {
          editor.view.dispatch(tr);
          nanobot.showToast(`Đã cào thành công ${resultMap.size} ảnh về hệ thống sếp ơi!`, "success");
        }
      }
    } finally {
      isLeaching = false;
      leachQueue = [];
    }
  }

  // Image Menu tracking
  let imageMenuVisible = $state(false);
  let imageMenuX = $state(0);
  let imageMenuY = $state(0);
  let linkMenuVisible = $state(false);
  let linkMenuX = $state(0);
  let linkMenuY = $state(0);
  let blockClicks = $state(false);

  const handlers = createEditorHandlers({
    get editor() { return editor; },
    get showMediaVault() { return showMediaVault; },
    set showMediaVault(v) { showMediaVault = v; },
    get imageMenuVisible() { return imageMenuVisible; },
    set imageMenuVisible(v) { imageMenuVisible = v; },
    get imageMenuX() { return imageMenuX; },
    set imageMenuX(v) { imageMenuX = v; },
    get imageMenuY() { return imageMenuY; },
    set imageMenuY(v) { imageMenuY = v; },
    onblur
  });
  let lastInternalActionAt = 0;
  let isSyncLocked = $state(false);

  // CNS V88.4: Direct Editor Apply — bypasses reactive chain for guaranteed update
  async function applyContentToEditor(newHtml: string) {
    if (!editor || editor.isDestroyed) return;
    isInternalUpdating = true;
    isSyncLocked = true;
    try {
      editor.commands.setContent(newHtml, false);
      
      // [CNS V94 FINAL] Re-apply annotations on new doc immediately after force-apply.
      // Otherwise, the highlights are lost and the effect loop guard (_lastAnnotationKey) prevents them from re-rendering.
      const currentAnnotations = annotations || [];
      if (currentAnnotations.length > 0) {
        const annKey = JSON.stringify(currentAnnotations.map(a => ({ id: a.id, text: a.text?.slice(0, 50), type: a.type })));
        _lastAnnotationKey = annKey;
        editor.view.dispatch(
          editor.state.tr.setMeta(AnnotationPluginKey, {
            type: 'SET_ANNOTATIONS',
            annotations: currentAnnotations
          })
        );
      }

      await tick();
      const finalContent = stripMarks(newHtml);
      content = finalContent;
      onChange(finalContent);
      updateMetrics();
    } finally {
      setTimeout(() => { isInternalUpdating = false; isSyncLocked = false; }, 150);
    }
  }

  const containerClass = $derived(`tiptap-shell flex flex-col w-full ${
    fullScreen
      ? `flex-1 h-full min-h-0 bg-[#0a0d14]`
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
    if (fullScreen === undefined) fullScreen = false;
    
    editor = new Editor({
      element,
      content,
      editable,
      extensions: getEditorExtensions(placeholder),
      editorProps,
      onUpdate: ({ transaction }) => {
        // [CNS V94 ROOT FIX] SET_ANNOTATIONS only changes decorations, NOT the doc.
        // If doc didn't change, content couldn't have changed — skip entirely.
        // This is the root cause of the loop: annotation dispatch triggered onUpdate
        // which detected a "diff" due to stripMarks normalization → loop.
        if (!transaction.docChanged) return;
        if (isInternalUpdating || isSyncLocked) return;
        const html = editor?.getHTML() ?? '';
        const cleaned = stripMarks(html);
        
        // CNS V2.2: Guard against redundant writes that trigger effects
        untrack(() => {
          if (normalizeHTML(cleaned, stripMarks) !== normalizeHTML(content || '', stripMarks)) {
            content = cleaned;
            onChange(cleaned);
            updateMetrics();
          }
        });
      },
      onFocus: () => {
        isFocused = true;
      },
      onBlur: () => {
        isFocused = false;
        onblur();
      },
      onSelectionUpdate: () => {
        // CNS V88.2: Ensure metrics update on selection change (e.g. word count of selected text could be next)
        updateMetrics();
      }
    });
    updateMetrics();

    // Cerberus 2026: Attach visual-overlay events to window for portal-safe tracking
    window.addEventListener('annotation-hover', annManager.handleAnnotationHover);
    window.addEventListener('annotation-leave', annManager.handleAnnotationLeave);
  });

  onDestroy(() => {
    if (editor) editor.destroy();
    if (metricsTimer) clearTimeout(metricsTimer);
    if (imageScanTimer) clearTimeout(imageScanTimer);
    window.removeEventListener('annotation-hover', annManager.handleAnnotationHover);
    window.removeEventListener('annotation-leave', annManager.handleAnnotationLeave);
  });

  $effect(() => {
    if (showMediaVault || showLinkDialog) {
      if (imageMenuVisible) imageMenuVisible = false;
    }
  });

  $effect(() => {
    if (editor && !editor.isDestroyed) {
      const isCurrentlyEditable = editor.isEditable;
      if (isCurrentlyEditable !== editable) {
        untrack(() => {
          isInternalUpdating = true;
          editor!.setEditable(editable);
          setTimeout(() => { isInternalUpdating = false; }, 0);
        });
      }
    }
  });

  $effect(() => {
    // CNS V2.3: Stabilized Content Sync (Zero-Flicker & No Scroll Jump)
    if (!editor || editor.isDestroyed || isInternalUpdating || isSyncLocked) return;
    
    // [CRITICAL] If editor is focused, it IS the master. 
    // Do NOT sync back from props to avoid scroll/cursor resets during active editing.
    // EXCEPTION: If we are in 'isRewriting' mode, the AI is the master.
    if (isFocused && !isRewriting) return;

    const normalizedContent = content || "<p></p>";

    untrack(() => {
        const currentHTML = editor!.getHTML();
        
        // Use a faster string-based check first to avoid expensive DOM normalization
        if (normalizedContent === currentHTML) return;

        const normProp = normalizeHTML(normalizedContent, stripMarks);
        const normCurrent = normalizeHTML(currentHTML, stripMarks);

        if (normProp !== normCurrent) {
            isInternalUpdating = true;
            const { from, to } = editor!.state.selection;
            
            // CNS V88.6: Use setContent with emitUpdate: false to prevent feedback loops
            editor!.commands.setContent(normalizedContent, false);

            // [CNS V94 ROOT LOOP FIX] After setContent, Tiptap re-serializes HTML slightly
            // differently (Typography, whitespace normalization). If we don't sync `content`
            // to match what Tiptap actually stored, normalizeHTML will keep differing on
            // every re-run → infinite setContent loop (the 253x bug).
            // Sync content binding to Tiptap's actual output to break the loop.
            // NOTE: Do NOT call onChange here. Content sync is Parent→Editor direction.
            // onChange is handled exclusively by onUpdate (Editor→Parent direction).
            const actualHTML = stripMarks(editor!.getHTML());
            content = actualHTML;

            // [CNS V94 FINAL] Re-apply annotations on new doc immediately.
            // onUpdate has !transaction.docChanged guard → SET_ANNOTATIONS dispatch is safe.
            const currentAnnotations = annotations || [];
            if (currentAnnotations.length > 0) {
              const annKey = JSON.stringify(currentAnnotations.map(a => ({ id: a.id, text: a.text?.slice(0, 50), type: a.type })));
              _lastAnnotationKey = annKey;
              editor!.view.dispatch(
                editor!.state.tr.setMeta(AnnotationPluginKey, {
                  type: 'SET_ANNOTATIONS',
                  annotations: currentAnnotations
                })
              );
            }

            // Re-sync selection if valid
            try { 
              const maxPos = editor!.state.doc.content.size;
              editor!.commands.setTextSelection({ 
                from: Math.min(from, maxPos), 
                to: Math.min(to, maxPos) 
              }); 
            } catch (e) {}
            
            setTimeout(() => { isInternalUpdating = false; }, 50);
        }
    });
  });

  // CNS V88.4: Force-apply content after Bulk Fix / AI Booster completes
  // The reactive sync above may skip updates due to normalizeHTML equality or focus guards.
  // This effect watches isBulkFixing transition true→false and force-pushes content into editor.
  let _prevBulkFixing = false;
  $effect(() => {
    const currentBulk = isBulkFixing;
    if (_prevBulkFixing && !currentBulk && editor && !editor.isDestroyed) {
      // Bulk operation just completed — force apply content
      const newContent = content || '<p></p>';
      untrack(() => {
        applyContentToEditor(newContent);
      });
    }
    _prevBulkFixing = currentBulk;
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
  // [CNS V94] isInternalUpdating removed from here — it caused content sync to re-run
  // every time annotations were dispatched. onUpdate checks HTML equality instead.
  $effect(() => {
    if (!editor || editor.isDestroyed) return;

    const currentAnnotations = annotations || [];
    const newKey = JSON.stringify(currentAnnotations.map(a => ({ id: a.id, text: a.text?.slice(0, 50), type: a.type })));

    console.log(`[Neural Editor] Evaluating SET_ANNOTATIONS. Annotations count: ${currentAnnotations.length}, newKey: ${newKey.substring(0, 50)}...`);

    // [LOOP GUARD] Skip dispatch if annotations haven't actually changed
    if (newKey === _lastAnnotationKey) {
      console.log("[Neural Editor] SET_ANNOTATIONS skipped (no change).");
      return;
    }

    untrack(() => {
      console.log(`[Neural Editor] Dispatching SET_ANNOTATIONS with ${currentAnnotations.length} items.`);
      _lastAnnotationKey = newKey;
      editor!.view.dispatch(
        editor!.state.tr.setMeta(AnnotationPluginKey, {
          type: 'SET_ANNOTATIONS',
          annotations: currentAnnotations
        })
      );
    });
  });

</script>

<div 
  class={containerClass}
  onfocusout={handlers.handleFocusOut}
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
      onClearHighlights={() => annotations = []}
      onClean={onClean}
      bind:showSource={showSource}
      fullScreen={fullScreen}
      onToggleFullScreen={toggleFullScreen}
      analysisData={analysisData}
      copyrightResult={copyrightResult}
      seoResult={seoResult}
      aiReadyResult={aiReadyResult}
      isCopyrightLoading={isCopyrightLoading}
      isSeoLoading={isSeoLoading}
      isAiLoading={isAiLoading}
      isBoosting={isBoosting}
      isBulkFixing={isBulkFixing}
      isRewriting={isRewriting}
      runBulkFix={runBulkFix}
      bulkFixLogs={bulkFixLogs}
      onAutoLeach={runAutoLeach}
      isLeaching={isLeaching}
    />
  {/if}

  <div
    class="w-full overflow-y-auto document-scroll relative {fullScreen ? 'bg-[#0a0d14] flex-1 min-h-0' : (flex ? 'bg-transparent flex-1 min-h-0' : 'bg-transparent max-h-[650px]')}"
    onclick={(e) => { 
      if (e.target === e.currentTarget) editor?.commands.focus();
      handlers.handleImageClick(e); 
    }}
    ondblclick={handlers.handleDoubleClick}
    onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') handlers.handleImageClick(e); }}
    role="button"
    tabindex="0"
  >
    <div 
      class="
        {fullScreen ? 'w-full min-h-full px-4 pt-4 pb-16 transition-all duration-300 flex flex-col' : (flex ? 'w-full bg-transparent min-h-full px-6 pt-4 pb-16 flex flex-col' : 'w-full bg-transparent min-h-[400px] px-6 pt-4 pb-16 flex flex-col')}
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
          class="w-full {fullScreen ? 'flex-1 min-h-0' : 'min-h-[500px]'} bg-[#050505] text-white/70 font-mono text-[12px] p-6 outline-none border border-white/5 rounded-xl resize-none leading-relaxed custom-scrollbar shadow-2xl"
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

<EditorOverlays
  {editor}
  {editable}
  bind:showMediaVault={showMediaVault}
  bind:showLinkDialog={showLinkDialog}
  {campaignId}
  bind:assets={assets}
  bind:selectedAvatarUrl={selectedAvatarUrl}
  bind:selectedAssetIndex={selectedAssetIndex}
  bind:blockClicks={blockClicks}
  bind:imageMenuVisible={imageMenuVisible}
  bind:linkMenuVisible={linkMenuVisible}
  bind:isSyncLocked={isSyncLocked}
  bind:content={content}
  {onChange}
  {currentLinkData}
  bind:tooltipVisible={annManager.state.tooltipVisible}
  tooltipX={annManager.state.tooltipX}
  tooltipY={annManager.state.tooltipY}
  tooltipType={annManager.state.tooltipType}
  tooltipText={annManager.state.tooltipText}
  isFixing={annManager.state.isFixing}
  handleFix={annManager.handleFix}
  handleTooltipEnter={annManager.handleTooltipEnter}
  handleTooltipLeave={annManager.handleTooltipLeave}
  {linkMenuX}
  {linkMenuY}
  {imageMenuX}
  {imageMenuY}
/>
