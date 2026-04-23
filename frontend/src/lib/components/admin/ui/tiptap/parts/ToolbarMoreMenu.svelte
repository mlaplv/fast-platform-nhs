<script lang="ts">
  /**
   * ToolbarMoreMenu.svelte — Overflow Tools Menu
   * Component split from Toolbar.svelte to maintain < 500 lines.
   * Elite V2.7: Strictly typed, no any, high-performance logic.
   */
  import type { Editor } from '@tiptap/core';
  import ListIcon from 'lucide-svelte/icons/list';
  import ListOrderedIcon from 'lucide-svelte/icons/list-ordered';
  import AlignLeftIcon from 'lucide-svelte/icons/align-left';
  import AlignCenterIcon from 'lucide-svelte/icons/align-center';
  import AlignRightIcon from 'lucide-svelte/icons/align-right';
  import AlignJustifyIcon from 'lucide-svelte/icons/align-justify';
  import QuoteIcon from 'lucide-svelte/icons/quote';
  import CodeIcon from 'lucide-svelte/icons/code';
  import MinusIcon from 'lucide-svelte/icons/minus';
  import StrikethroughIcon from 'lucide-svelte/icons/strikethrough';
  import BoldIcon from 'lucide-svelte/icons/bold';
  import ItalicIcon from 'lucide-svelte/icons/italic';
  import UnderlineIcon from 'lucide-svelte/icons/underline';
  import ImageIcon from 'lucide-svelte/icons/image';
  import Link2Icon from 'lucide-svelte/icons/link-2';
  import SparklesIcon from 'lucide-svelte/icons/sparkles';
  import { fade } from 'svelte/transition';
  import { portal } from '$lib/core/actions/portal';
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import type { ToolbarAction } from '$lib/types';

  interface TiptapActiveStates {
    bold?: boolean;
    italic?: boolean;
    underline?: boolean;
    bulletList?: boolean;
    orderedList?: boolean;
    blockquote?: boolean;
    code?: boolean;
    alignLeft?: boolean;
    alignCenter?: boolean;
    alignRight?: boolean;
    alignJustify?: boolean;
    strike?: boolean;
  }

  let {
    showMore = $bindable(),
    morePopupPos,
    editor,
    active,
    isCompact,
    isSuperCompact,
    onOpenImage,
    onOpenLink,
    onToggleFullScreen,
    fullScreen,
    toolbarActions = [] as ToolbarAction[]
  }: {
    showMore: boolean;
    morePopupPos: { top: number; left: number };
    editor: Editor | null;
    active: TiptapActiveStates;
    isCompact: boolean;
    isSuperCompact: boolean;
    onOpenImage: () => void;
    onOpenLink: () => void;
    onToggleFullScreen: (() => void) | null;
    fullScreen: boolean;
    toolbarActions: ToolbarAction[];
  } = $props();
</script>

{#if showMore}
  <div
       use:portal
       class="fixed bg-[#0d0d0d]/95 backdrop-blur-3xl border border-white/10 rounded-xl p-3 shadow-[0_30px_60px_rgba(0,0,0,0.8)] flex flex-col gap-3 min-w-[240px]"
       style="top: {morePopupPos.top}px; left: {morePopupPos.left}px; transform: translateX(-100%); z-index: {Z_INDEX_ADMIN.TIPTAP_TOOLBAR_DROPDOWN}"
  >
    <!-- Extra Tools (Always in More) -->
    <div class="flex flex-col gap-2 p-2 bg-white/5 rounded-lg border border-white/5">
       <span class="text-[7px] font-black uppercase tracking-widest text-white/20 px-1">Extended Tools</span>
        <div class="flex gap-1.5">
           <button onclick={() => { editor?.chain().focus().toggleBulletList().run(); showMore=false; }} class="tb-btn !h-8 !w-8 {active.bulletList ? 'active-neural' : ''}" title="Bullet List"><ListIcon size={12}/></button>
           <button onclick={() => { editor?.chain().focus().toggleOrderedList().run(); showMore=false; }} class="tb-btn !h-8 !w-8 {active.orderedList ? 'active-neural' : ''}" title="Ordered List"><ListOrderedIcon size={12}/></button>
           <button onclick={() => { editor?.chain().focus().toggleBlockquote().run(); showMore=false; }} class="tb-btn !h-8 !w-8 {active.blockquote ? 'active-neural' : ''}" title="Quote"><QuoteIcon size={12}/></button>
           <button onclick={() => { editor?.chain().focus().toggleCode().run(); showMore=false; }} class="tb-btn !h-8 !w-8 {active.code ? 'active-neural' : ''}" title="Code"><CodeIcon size={12}/></button>
           <button onclick={() => { editor?.chain().focus().setHorizontalRule().run(); showMore=false; }} class="tb-btn !h-8 !w-8" title="Horizontal Rule"><MinusIcon size={12}/></button>
        </div>
    </div>

    <div class="flex flex-col gap-2 p-2 bg-white/5 rounded-lg border border-white/5">
       <span class="text-[7px] font-black uppercase tracking-widest text-white/20 px-1">Text Alignment</span>
       <div class="flex gap-1.5">
         <button onclick={() => { editor?.chain().focus().setTextAlign('left').run(); showMore=false; }} class="tb-btn !h-8 !w-8 {active.alignLeft ? 'active-neural' : ''}"><AlignLeftIcon size={12}/></button>
         <button onclick={() => { editor?.chain().focus().setTextAlign('center').run(); showMore=false; }} class="tb-btn !h-8 !w-8 {active.alignCenter ? 'active-neural' : ''}"><AlignCenterIcon size={12}/></button>
         <button onclick={() => { editor?.chain().focus().setTextAlign('right').run(); showMore=false; }} class="tb-btn !h-8 !w-8 {active.alignRight ? 'active-neural' : ''}"><AlignRightIcon size={12}/></button>
         <button onclick={() => { editor?.chain().focus().setTextAlign('justify').run(); showMore=false; }} class="tb-btn !h-8 !w-8 {active.alignJustify ? 'active-neural' : ''}"><AlignJustifyIcon size={12}/></button>
       </div>
    </div>

    <div class="flex flex-col gap-2 p-2 bg-white/5 rounded-lg border border-white/5">
       <span class="text-[7px] font-black uppercase tracking-widest text-white/20 px-1">Extra Formatting</span>
       <div class="flex gap-1.5">
         <button onclick={() => { editor?.chain().focus().toggleStrike().run(); showMore=false; }} class="tb-btn !h-8 !w-8 {active.strike ? 'active-neural' : ''}"><StrikethroughIcon size={12}/></button>
       </div>
    </div>

    <!-- Hidden Groups depending on width -->
    {#if isCompact}
       <div class="flex flex-col gap-2 p-2 bg-white/5 rounded-lg border border-white/5">
         <span class="text-[7px] font-black uppercase tracking-widest text-white/20 px-1">Formatting</span>
         <div class="flex gap-1">
           <button onclick={() => { editor?.chain().focus().toggleBold().run(); }} class="tb-btn !h-8 !w-8 {active.bold ? 'active-neural' : ''}"><BoldIcon size={12}/></button>
           <button onclick={() => { editor?.chain().focus().toggleItalic().run(); }} class="tb-btn !h-8 !w-8 {active.italic ? 'active-neural' : ''}"><ItalicIcon size={12}/></button>
           <button onclick={() => { editor?.chain().focus().toggleUnderline().run(); }} class="tb-btn !h-8 !w-8 {active.underline ? 'active-neural' : ''}"><UnderlineIcon size={12}/></button>
           <button onclick={() => { editor?.chain().focus().toggleStrike().run(); }} class="tb-btn !h-8 !w-8 {active.strike ? 'active-neural' : ''}"><StrikethroughIcon size={12}/></button>
         </div>
       </div>
    {/if}

    {#if isSuperCompact}
      <div class="flex flex-col gap-2 p-2 bg-white/5 rounded-lg border border-white/5">
         <span class="text-[7px] font-black uppercase tracking-widest text-white/20 px-1">Media & Views</span>
         <div class="flex items-center justify-between">
            <div class="flex gap-1">
              <button onclick={onOpenImage} class="tb-btn !h-8 !w-8"><ImageIcon size={12}/></button>
              <button onclick={onOpenLink} class="tb-btn !h-8 !w-8"><Link2Icon size={12}/></button>
            </div>
            <div class="w-px h-6 bg-white/10 mx-2"></div>
            <button onclick={onToggleFullScreen} class="tb-btn !h-8 !w-8 {fullScreen ? 'text-amber-500' : ''}"><SparklesIcon size={12}/></button>
         </div>
      </div>
    {/if}


    <!-- CNS V85.23: AI Booster & Extra Actions Overflow -->
    {#if toolbarActions.length > 0}
      <div class="flex flex-col gap-2 p-2 bg-pink-500/5 rounded-lg border border-pink-500/10">
         <span class="text-[7px] font-black uppercase tracking-widest text-pink-400/40 px-1 italic">Intelligence Actions</span>
         <div class="flex flex-wrap gap-2">
            {#each toolbarActions as action (action.id)}
              <button
                onclick={() => { action.onclick(); showMore = false; }}
                disabled={action.loading || action.disabled}
                class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-wider transition-all {action.loading ? 'opacity-50' : action.disabled ? 'opacity-30 cursor-not-allowed' : 'bg-pink-500/10 text-pink-400 hover:bg-pink-500 hover:text-white border border-pink-500/20'}"
              >
                {#if action.loading}<div class="w-2 h-2 border border-white/20 border-t-white rounded-full animate-spin"></div>{/if}
                {action.label}
              </button>
            {/each}
         </div>
      </div>
    {/if}
  </div>
  <div use:portal transition:fade={{ duration: 150 }} class="fixed inset-0" style="z-index: {Z_INDEX_ADMIN.TIPTAP_TOOLBAR_OVERLAY}" onclick={() => showMore = false}></div>
{/if}

<style>
  @reference "tailwindcss";
  .tb-btn {
    @apply flex items-center justify-center w-8 h-8 rounded-lg text-white/30 hover:text-white hover:bg-white/5 transition-all duration-500 active:scale-90 cursor-pointer;
  }
  .active-neural {
    @apply bg-cyan-500 text-black shadow-[0_0_15px_rgba(6,182,212,0.4)] scale-105 border border-cyan-400/20;
  }
</style>
