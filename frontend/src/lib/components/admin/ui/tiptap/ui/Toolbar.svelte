<script lang="ts">
  import { untrack, tick } from 'svelte';



  import type { Editor } from '@tiptap/core';
  import type { ToolbarAction, EditorAnnotation } from '$lib/types';
  import BoldIcon from "@lucide/svelte/icons/bold";
  import ItalicIcon from "@lucide/svelte/icons/italic";
  import UnderlineIcon from "@lucide/svelte/icons/underline";
  import UndoIcon from "@lucide/svelte/icons/undo";
  import RedoIcon from "@lucide/svelte/icons/redo";
  import PaletteIcon from "@lucide/svelte/icons/palette";
  import ImageIcon from "@lucide/svelte/icons/image";
  import Link2Icon from "@lucide/svelte/icons/link-2";
  import UnlinkIcon from "@lucide/svelte/icons/unlink";
  import EraserIcon from "@lucide/svelte/icons/eraser";
  import CodeIcon from "@lucide/svelte/icons/code";
  import Maximize2Icon from "@lucide/svelte/icons/maximize-2";
  import SparklesIcon from "@lucide/svelte/icons/sparkles";
  import AlignLeftIcon from "@lucide/svelte/icons/align-left";
  import AlignCenterIcon from "@lucide/svelte/icons/align-center";
  import AlignRightIcon from "@lucide/svelte/icons/align-right";
  import AlignJustifyIcon from "@lucide/svelte/icons/align-justify";
  import TrendingUpIcon from "@lucide/svelte/icons/trending-up";
  import MoreHorizontalIcon from "@lucide/svelte/icons/more-horizontal";
  import CloudDownloadIcon from "@lucide/svelte/icons/cloud-download";
  import { portal } from '$lib/core/actions/portal';
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import type { CleanOptions } from '$lib/state/xohiActions';
  import type { CopyrightResult, SEOResult, AIInspectResult, NeuralAnalysisController } from '$lib/state/types';
  import { fly, fade } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';
  import IntelligenceHUD from '../parts/IntelligenceHUD.svelte';
  import ToolbarMoreMenu from '../parts/ToolbarMoreMenu.svelte';
  import NeuralCleanMenu from '../parts/NeuralCleanMenu.svelte';

  let {
    editor,
    toolbarActions = [],
    annotations = [],
    onOpenImage,
    onOpenLink,
    onClearHighlights = null,
    onClean = null,
    fullScreen = false,
    onToggleFullScreen = null,
    showSource = $bindable(),
    // CNS V85.2: Intelligence Context
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
    runBulkFix = undefined,
    bulkFixLogs = [],
    // CNS V87.0: SSE streaming
    streamingText = '',
    streamingTarget = null,
    onAutoLeach = null,
    isLeaching = false,
  }: {
    editor: Editor | null;
    toolbarActions?: ToolbarAction[];
    annotations?: EditorAnnotation[];
    onOpenImage: () => void;
    onOpenLink: () => void;
    onClearHighlights?: (() => void) | null;
    onClean?: ((options?: CleanOptions, rawContent?: string) => Promise<string | null>) | null;
    fullScreen?: boolean;
    onToggleFullScreen?: (() => void) | null;
    showSource?: boolean;
    analysisData?: NeuralAnalysisController;
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
    streamingText?: string;
    streamingTarget?: string | null;
    onAutoLeach?: (() => void) | null;
    isLeaching?: boolean;
  } = $props();

  const FONTS = ['Be Vietnam Pro', 'Roboto', 'Georgia', 'Times New Roman', 'Courier New', 'Arial'];
  const COLORS = [
    '#ffffff', '#000000', '#64748b', '#94a3b8', '#cbd5e1', 
    '#ef4444', '#f87171', '#fca5a5', 
    '#f97316', '#fb923c', '#fdba74',
    '#eab308', '#facc15', '#fde68a',
    '#22c55e', '#4ade80', '#86efac',
    '#06b6d4', '#22d3ee', '#67e8f9',
    '#3b82f6', '#60a5fa', '#93c5fd',
    '#8b5cf6', '#a78bfa', '#c4b5fd',
    '#d946ef', '#f0abfc', '#f5d0fe'
  ];

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

  // --- RESPONSIVE LOGIC ---
  let containerRef = $state<HTMLElement | null>(null);
  let colorButtonRef = $state<HTMLElement | null>(null);
  let moreButtonRef = $state<HTMLElement | null>(null);
  let containerWidth = $state(0);
  let showMore = $state(false);
  let showColorPicker = $state(false);
  
  let colorPopupPos = $state({ top: 0, left: 0 });
  let morePopupPos = $state({ top: 0, left: 0 });
  let cleanPopupPos = $state({ top: 0, left: 0 });

  let showCleanOptions = $state(false);
  let cleanOptions = $state<CleanOptions>({
    stripFont: true,
    stripAlign: true,
    stripRedundantWrappers: true,
    stripEmpty: true,
    deduplicateContent: true
  });

  function updatePopupPositions() {
    if (showColorPicker && colorButtonRef) {
      const rect = colorButtonRef.getBoundingClientRect();
      colorPopupPos = { top: rect.bottom + 8, left: rect.right };
    }
    if (showMore && moreButtonRef) {
      const rect = moreButtonRef.getBoundingClientRect();
      morePopupPos = { top: rect.bottom + 12, left: rect.right };
    }
    if (showCleanOptions && cleanButtonRef) {
      const rect = cleanButtonRef.getBoundingClientRect();
      cleanPopupPos = { top: rect.bottom + 8, left: rect.right };
    }
  }

  let cleanButtonRef = $state<HTMLElement | null>(null);
  let intelPopoverPos = $state({ top: 0, left: 0 });
  let activeIntelAction = $state<string | null>(null);

  // [CNS V90.0] Removed aggressive Auto-Close Protocol. 
  // Closing is now handled by Controller (xohiAnalysis) or User manual action.
  let lastLoadingState = $state(false);
  
  $effect(() => {
    if (!activeIntelAction) {
      lastLoadingState = false;
      return;
    }
    const activeAction = toolbarActions.find(a => a.id === activeIntelAction);
    const isLoading = activeAction?.loading || false;
    lastLoadingState = isLoading;
  });



  $effect(() => {
    if (showColorPicker || showMore || showCleanOptions) {
      updatePopupPositions();
      window.addEventListener('scroll', updatePopupPositions, true);
      window.addEventListener('resize', updatePopupPositions);
      return () => {
        window.removeEventListener('scroll', updatePopupPositions, true);
        window.removeEventListener('resize', updatePopupPositions);
      };
    }
  });

  function handleToolbarScroll() {
    if (showColorPicker || showMore || showCleanOptions) {
      showColorPicker = false;
      showMore = false;
      showCleanOptions = false;
    }
  }
  
  // Container-based responsive states
  const isThin = $derived(containerWidth < 800); 
  const isCompact = $derived(containerWidth < 600);
  const isSuperCompact = $derived(containerWidth < 400);

  // --- REACTIVE STATE SYNC ---
  let updateTick = $state(0);

  $effect(() => {
    if (!editor) return;
    const update = () => { updateTick++; };
    editor.on('selectionUpdate', update);
    editor.on('transaction', update);
    return () => {
      if (editor) {
        editor.off('selectionUpdate', update);
        editor.off('transaction', update);
      }
    };
  });

  const active = $derived.by(() => {
    updateTick;
    if (!editor) return {
       format: 'p', font: 'Be Vietnam Pro', bold: false, italic: false, underline: false,
       strike: false, blockquote: false, code: false, color: 'white'
    };

    return {
      format: editor.isActive('heading', { level: 1 }) ? 'h1' :
              editor.isActive('heading', { level: 2 }) ? 'h2' :
              editor.isActive('heading', { level: 3 }) ? 'h3' : 'p',
      font: editor.getAttributes('textStyle').fontFamily || 'Be Vietnam Pro',
      bold: editor.isActive('bold'),
      italic: editor.isActive('italic'),
      underline: editor.isActive('underline'),
      strike: editor.isActive('strike'),
      blockquote: editor.isActive('blockquote'),
      code: editor.isActive('code'),
      color: editor.getAttributes('textStyle').color || 'white',
      bulletList: editor.isActive('bulletList'),
      orderedList: editor.isActive('orderedList'),
      alignLeft: editor.isActive({ textAlign: 'left' }),
      alignCenter: editor.isActive({ textAlign: 'center' }),
      alignRight: editor.isActive({ textAlign: 'right' }),
      alignJustify: editor.isActive({ textAlign: 'justify' }),
      link: editor.isActive('link') || (editor.state.selection.from !== editor.state.selection.to && editor.state.doc.rangeHasMark(editor.state.selection.from, editor.state.selection.to, editor.schema.marks.link)),
    };
  });


  // CNS V90.1: Local proxy state for userPlanNote to avoid crash when analysisData is null
  let localUserPlanNote = $state("");
  
  $effect(() => {
    if (analysisData) {
      // Sync from analysisData to local state when analysisData is available
      untrack(() => {
        localUserPlanNote = analysisData.userPlanNote;
      });
    }
  });

  $effect(() => {
    // Sync back to analysisData when local state changes (e.g. from HUD binding)
    if (analysisData && localUserPlanNote !== analysisData.userPlanNote) {
      analysisData.userPlanNote = localUserPlanNote;
    }
  });

</script>

<div 
  bind:this={containerRef}
  bind:clientWidth={containerWidth}
  onscroll={handleToolbarScroll}
  class="sticky top-0 w-full flex flex-nowrap items-center gap-2 md:gap-3 px-4 py-1.5 bg-[#0a0a0a]/90 backdrop-blur-[80px] border-b border-white/5 shadow-2xl transition-all duration-300 overflow-x-auto hide-scrollbar"
  style="z-index: {Z_INDEX_ADMIN.TIPTAP_TOOLBAR_DROPDOWN}"
>
  
  <!-- Group 1: Navigation -->
    <div class="tb-platter shrink-0">
      <button onclick={() => editor?.chain().focus().undo().run()} class="tb-btn" title="Undo"><UndoIcon size={12} /></button>
      <button onclick={() => editor?.chain().focus().redo().run()} class="tb-btn" title="Redo"><RedoIcon size={12} /></button>
      {#if onToggleFullScreen}
        <button onclick={onToggleFullScreen} class="tb-btn {fullScreen ? 'text-amber-500' : ''}" title={fullScreen ? "Exit Fullscreen" : "Enter Fullscreen"}>
          {#if fullScreen}
            <Maximize2Icon size={12} class="rotate-180" />
          {:else}
            <Maximize2Icon size={12} />
          {/if}
        </button>
      {/if}
      <button onclick={() => showSource = !showSource} class="tb-btn {showSource ? 'active-neural !bg-cyan-500/20' : ''}" title="View Source">
        <CodeIcon size={12} />
      </button>
    </div>

  <!-- Group 2: Typography (Main Bar) -->
  {#if !isThin}
    <div class="tb-platter shrink-0 px-2 flex">
      <select 
        class="tb-select font-black uppercase tracking-widest text-[8px] {active.format !== 'p' ? '!text-cyan-400 font-bold' : ''}" 
        value={active.format}
        onchange={handleParagraphChange}
      >
        <option value="p" class="bg-[#0d0d0d] text-white">Body</option>
        <option value="h1" class="bg-[#0d0d0d] text-white">H1</option>
        <option value="h2" class="bg-[#0d0d0d] text-white">H2</option>
        <option value="h3" class="bg-[#0d0d0d] text-white">H3</option>
      </select>
      <div class="w-px h-3 bg-white/5 mx-1"></div>
      <select 
        class="tb-select font-mono text-[8px] uppercase tracking-wider" 
        value={active.font}
        onchange={handleFontChange}
      >
        {#each FONTS as font}
          <option value={font} class="bg-[#0d0d0d] text-white">{font}</option>
        {/each}
      </select>
    </div>
  {/if}

  <!-- Group 3: Formatting -->
  <div class="tb-platter shrink-0">
    <button onclick={() => editor?.chain().focus().toggleBold().run()} class="tb-btn {active.bold ? 'active-neural' : ''}" title="Bold"><BoldIcon size={12} /></button>
    {#if !isCompact}
      <button onclick={() => editor?.chain().focus().toggleItalic().run()} class="tb-btn {active.italic ? 'active-neural' : ''}" title="Italic"><ItalicIcon size={12} /></button>
      <button onclick={() => editor?.chain().focus().toggleUnderline().run()} class="tb-btn {active.underline ? 'active-neural' : ''}" title="Underline"><UnderlineIcon size={12} /></button>
    {/if}
  </div>

  <!-- Group 3.5: Alignment (User Prioritized) -->
  {#if !isCompact}
    <div class="tb-platter shrink-0">
      <button onclick={() => editor?.chain().focus().setTextAlign('left').run()} class="tb-btn {active.alignLeft ? 'active-neural' : ''}" title="Align Left"><AlignLeftIcon size={12} /></button>
      <button onclick={() => editor?.chain().focus().setTextAlign('center').run()} class="tb-btn {active.alignCenter ? 'active-neural' : ''}" title="Align Center"><AlignCenterIcon size={12} /></button>
      <button onclick={() => editor?.chain().focus().setTextAlign('right').run()} class="tb-btn {active.alignRight ? 'active-neural' : ''}" title="Align Right"><AlignRightIcon size={12} /></button>
      <button onclick={() => editor?.chain().focus().setTextAlign('justify').run()} class="tb-btn {active.alignJustify ? 'active-neural' : ''}" title="Align Justify"><AlignJustifyIcon size={12} /></button>
    </div>
  {/if}

  <!-- Group 4: Media -->
  {#if !isSuperCompact}
    <div class="tb-platter shrink-0 border-cyan-500/10 bg-cyan-500/[0.02]">
      <button onclick={onOpenImage} class="tb-btn text-cyan-400/60 hover:text-cyan-400" title="Image"><ImageIcon size={12} /></button>
      <button onclick={onOpenLink} class="tb-btn {active.link ? 'active-neural' : 'text-cyan-400/60 hover:text-cyan-400'}" title="Link"><Link2Icon size={12} /></button>
      <button 
        onclick={() => editor?.chain().focus().unsetAllLinks().run()} 
        class="tb-btn text-rose-400/80 hover:text-rose-400 hover:bg-rose-500/10" 
        title="Remove All Links in Selection (Ctrl+Shift+K)"
      >
        <UnlinkIcon size={12} />
      </button>
      <button 
        onclick={() => {
          if (onClearHighlights) onClearHighlights();
          if (editor) {
            const { from, to } = editor.state.selection;
            if (from !== to) {
              editor.chain().focus().unsetAllMarks().run();
            } else {
              editor.chain().focus().selectAll().unsetAllMarks().setTextSelection(from).run();
            }
          }
        }} 
        class="tb-btn text-amber-400/60 hover:text-amber-400" 
        title="Clear Formatting & AI Highlights"
      >
        <EraserIcon size={12} />
      </button>
      <div class="w-px h-3 bg-white/5 mx-1"></div>
      <button 
        onclick={onAutoLeach} 
        class="tb-btn {isLeaching ? 'animate-pulse text-amber-400' : 'text-emerald-400/60 hover:text-emerald-400'}" 
        title="Auto-Leach: Cào ảnh ngoại về local"
        disabled={isLeaching}
      >
        {#if isLeaching}
          <div class="w-3 h-3 border-2 border-amber-400/20 border-t-amber-400 rounded-full animate-spin"></div>
        {:else}
          <CloudDownloadIcon size={12} />
        {/if}
      </button>
    </div>
  {/if}

  <!-- Group 5: Single Color Picker (User Requested) -->
  <div class="shrink-0 relative">
    <button 
      bind:this={colorButtonRef}
      onclick={() => showColorPicker = !showColorPicker}
      class="w-8 h-8 rounded-lg border border-white/10 flex items-center justify-center hover:bg-white/10 hover:border-white/20 active:scale-95 transition-all bg-white/[0.05]"
      title="Color Picker"
    >
      <div class="w-4 h-4 rounded-sm border border-black/50 overflow-hidden relative shadow-sm" style="background: {active.color};">
         <PaletteIcon size={10} class="absolute inset-0 m-auto mix-blend-difference text-white/80" />
      </div>
    </button>

    {#if showColorPicker}
      <div 
           use:portal
           class="fixed bg-[#0d0d0d] border border-white/10 rounded-xl p-3 shadow-[0_20px_50px_rgba(0,0,0,0.5)] flex flex-col gap-3 min-w-[200px]"
           style="top: {colorPopupPos.top}px; left: {colorPopupPos.left}px; transform: translateX(-100%); z-index: {Z_INDEX_ADMIN.TIPTAP_TOOLBAR_DROPDOWN}"
      >
        <div class="flex items-center justify-between px-1">
          <span class="text-[8px] font-black uppercase tracking-widest text-white/30">Color Swatches</span>
          <button onclick={() => { editor?.chain().focus().unsetColor().run(); showColorPicker = false; }} class="text-[8px] font-black uppercase text-rose-500/60 hover:text-rose-400">Reset</button>
        </div>
        <div class="grid grid-cols-6 gap-2">
          {#each COLORS as color}
            <button 
              onclick={() => { editor?.chain().focus().setColor(color).run(); showColorPicker = false; }} 
              class="w-5 h-5 rounded-md border border-white/10 hover:scale-125 transition-all shadow-sm" 
              style="background: {color};"
            ></button>
          {/each}
        </div>
      </div>
      <div use:portal class="fixed inset-0" style="z-index: {Z_INDEX_ADMIN.TIPTAP_TOOLBAR_OVERLAY}" onclick={() => showColorPicker = false}></div>
    {/if}
  </div>

  <!-- Overflow Toggle (The Dropdown - Always Visible for Extras) -->
  <div class="shrink-0 relative">
    <button
      bind:this={moreButtonRef}
      onclick={() => showMore = !showMore}
      class="tb-btn !bg-white/[0.08] hover:!bg-amber-500/20 border border-white/10 {showMore ? 'text-amber-500 border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.2)]' : ''}"
      title="More Tools"
    >
      <MoreHorizontalIcon size={14} />
    </button>

    <ToolbarMoreMenu
      bind:showMore
      {morePopupPos}
      {editor}
      {active}
      {isCompact}
      {isSuperCompact}
      {onOpenImage}
      {onOpenLink}
      {onToggleFullScreen}
      {fullScreen}
      {toolbarActions}
    />
  </div>

  <!-- Flexible Space -->
  <div class="flex-1"></div>

  <!-- Island: Intelligence & Actions -->
  <div class="flex items-center gap-2">
    {#if onClean}
      <div class="relative">
        <button
          bind:this={cleanButtonRef}
          onclick={() => showCleanOptions = !showCleanOptions}
          class="tb-neural-action bg-orange-500/10 text-orange-400 border-orange-500/20 hover:bg-orange-500 hover:text-white group {showCleanOptions ? 'active-neural !bg-orange-500 !text-white' : ''}"
          title="Neural Clean Options"
        >
          <SparklesIcon size={11} class={showCleanOptions ? '' : 'animate-pulse'} />
          <span class="{isThin ? 'hidden' : 'inline'} text-[9px]">Neural Clean</span>
          <TrendingUpIcon size={8} class="ml-0.5 opacity-60" />
        </button>

        <NeuralCleanMenu
          bind:showCleanOptions={showCleanOptions}
          {cleanPopupPos}
          bind:cleanOptions={cleanOptions}
          onClean={async (options) => {
            if (onClean) {
              activeIntelAction = 'clean';
              const rect = cleanButtonRef?.getBoundingClientRect();
              if (rect) {
                intelPopoverPos = { 
                  top: Math.round(rect.bottom + 8), 
                  left: Math.round(Math.min(rect.left, window.innerWidth - 440))
                };
              }

              // [Elite V2.2] Local Strip Links support
              if (options.stripLinks && editor) {
                editor.chain().focus().unsetAllLinks().run();
              }

              await onClean(options, editor?.getHTML());
            }
          }}
        />
      </div>
    {/if}

    {#if toolbarActions.length > 0}
      {#each toolbarActions.slice(0, isCompact ? (isSuperCompact ? 0 : 1) : toolbarActions.length) as action (action.id)}
        <div class="relative">
          <button
            onclick={(e) => { 
                e.stopPropagation();
                action.onclick(); 
                // CNS V85.22: Always ensure it's open on click, don't toggle off
                activeIntelAction = action.id || null;
                
                // CNS V87.1: Sync analysis activeTab to ensure highlights follow HUD focus
                if (analysisData && action.id !== 'clean' && !action.id.includes('-fix')) {
                  analysisData.activeTab = action.id;
                }

                const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
                intelPopoverPos = { 
                    top: Math.round(rect.bottom + 8), 
                    left: Math.round(Math.min(rect.left, window.innerWidth - 440))
                };
            }}
            disabled={action.loading || action.disabled}
            title={action.title || action.label}
            class="tb-neural-action {action.loading ? 'loading' : action.disabled ? 'disabled' : ''} {(action.active || activeIntelAction === action.id) && !action.loading ? 'active-neural scale-105' : ''} {action.isPerfect ? 'border-emerald-500/50 bg-emerald-500/10 text-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.2)]' : action.isLocked ? 'border-rose-500/30 bg-rose-500/5 text-rose-400/70' : action.colorClass || 'bg-cyan-500 text-black'} transition-all duration-300"
          >
            {#if action.loading}
              <div class="w-2.5 h-2.5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
            {/if}
            
            {#if action.icon && !action.loading}
               <svelte:component this={action.icon} size={11} class={action.isPerfect ? 'animate-pulse' : ''} />
            {/if}

            <span class="text-[9px] {isThin && toolbarActions.length > 1 ? 'hidden' : 'inline'}">{action.label}</span>
            <TrendingUpIcon size={8} class="ml-0.5 opacity-60" />
            
            {#if action.isPerfect && !action.loading}
               <div class="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,1)]"></div>
            {:else if action.isLocked && !action.loading}
               <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-lock"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            {/if}
          </button>
        </div>
      {/each}
    {/if}

    <IntelligenceHUD
      bind:activeIntelAction
      {toolbarActions}
      {intelPopoverPos}
      {bulkFixLogs}
      {copyrightResult}
      {seoResult}
      {aiReadyResult}
      {isCopyrightLoading}
      {isSeoLoading}
      {isAiLoading}
      {isBoosting}
      isBulkFixing={isBulkFixing}
      isRewriting={isRewriting}
      runBulkFix={runBulkFix}
      {analysisData}
      currentAnalysisStep={analysisData?.currentAnalysisStep ?? null}
      bind:userPlanNote={localUserPlanNote}
      {streamingText}
      {streamingTarget}
    />
  </div>
</div>

<style>
  @reference "tailwindcss";

  .tb-platter {
    @apply flex items-center gap-1 bg-white/[0.03] p-1 rounded-xl border border-white/10 shadow-xl backdrop-blur-md transition-all duration-300;
  }

  .tb-btn {
    @apply flex items-center justify-center w-8 h-8 rounded-lg text-white/30 hover:text-white hover:bg-white/5 transition-all duration-500 active:scale-90 cursor-pointer;
  }

  .active-neural {
    @apply bg-cyan-500 text-black shadow-[0_0_15px_rgba(6,182,212,0.4)] scale-105 border border-cyan-400/20;
  }

  .tb-select {
    @apply appearance-none bg-white/[0.03] text-white/40 px-2.5 py-1 h-8 outline-none cursor-pointer rounded-lg hover:bg-white/5 hover:text-white transition-all duration-500 border border-white/5;
  }

  .tb-select option {
    @apply bg-[#0d0d0d] text-white py-2;
  }

  .tb-neural-action {
    @apply flex items-center gap-1.5 px-4 py-2 rounded-lg text-[9px] uppercase tracking-[0.15em] transition-all duration-500 active:scale-95 border border-white/10 shadow-2xl;
  }

  .tb-neural-action.loading { @apply bg-white/5 text-white/20 cursor-wait; }
  .tb-neural-action.disabled { @apply opacity-30 grayscale; }

  .hide-scrollbar::-webkit-scrollbar { display: none; }
  .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
