<script lang="ts">
  import type { Editor } from '@tiptap/core';
  import Edit3 from "@lucide/svelte/icons/edit-3";
  import Unlink from "@lucide/svelte/icons/unlink";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import Globe from "@lucide/svelte/icons/globe";
  import Shield from "@lucide/svelte/icons/shield";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Users from "@lucide/svelte/icons/users";
  import Type from "@lucide/svelte/icons/type";
  import Check from "@lucide/svelte/icons/check";
  import X from "@lucide/svelte/icons/x";

  import { untrack } from 'svelte';

  let { 
    editor, 
    linkPos,
    currentLinkData,
    linkMenuVisible = $bindable(),
    onEdit, 
    onClose 
  }: { 
    editor: Editor; 
    linkPos: number | null;
    currentLinkData: any;
    linkMenuVisible: boolean;
    onEdit: () => void; 
    onClose: () => void 
  } = $props();

  let url = $state('');
  let title = $state('');
  let isTargetBlank = $state(false);
  let isNoFollow = $state(false);
  let isSponsored = $state(false);
  let isUgc = $state(false);

  // Track original attributes to determine if dirty
  let originalUrl = $state('');
  let originalTitle = $state('');
  let originalTargetBlank = $state(false);
  let originalNoFollow = $state(false);
  let originalSponsored = $state(false);
  let originalUgc = $state(false);

  $effect(() => {
    // Only track linkPos. When it changes, read currentLinkData inside untrack
    const pos = linkPos;
    if (pos !== null) {
      untrack(() => {
        if (currentLinkData) {
          url = currentLinkData.url || '';
          title = currentLinkData.title || '';
          isTargetBlank = currentLinkData.target === '_blank';
          const relValue = currentLinkData.rel || '';
          isNoFollow = relValue.includes('nofollow');
          isSponsored = relValue.includes('sponsored');
          isUgc = relValue.includes('ugc');

          // Store original values
          originalUrl = url;
          originalTitle = title;
          originalTargetBlank = isTargetBlank;
          originalNoFollow = isNoFollow;
          originalSponsored = isSponsored;
          originalUgc = isUgc;
        }
      });
    }
  });

  let isDirty = $derived(
    url !== originalUrl ||
    title !== originalTitle ||
    isTargetBlank !== originalTargetBlank ||
    isNoFollow !== originalNoFollow ||
    isSponsored !== originalSponsored ||
    isUgc !== originalUgc
  );

  function handleSave() {
    if (!editor || linkPos === null) return;

    if (!url.trim()) {
      unlink();
      return;
    }

    const relParts = [];
    if (isNoFollow) relParts.push('nofollow');
    if (isSponsored) relParts.push('sponsored');
    if (isUgc) relParts.push('ugc');
    if (isTargetBlank) {
      relParts.push('noopener');
      relParts.push('noreferrer');
    }
    const relValue = relParts.length > 0 ? relParts.join(' ') : null;

    editor.chain()
      .focus()
      .setTextSelection(linkPos + 1)
      .extendMarkRange('link')
      .setLink({
        href: url.trim(),
        title: title.trim(),
        target: isTargetBlank ? '_blank' : null,
        rel: relValue
      })
      .run();

    linkMenuVisible = false;
    onClose();
  }

  function unlink() {
    if (!editor || linkPos === null) return;
    editor.chain()
      .focus()
      .setTextSelection(linkPos + 1)
      .extendMarkRange('link')
      .unsetLink()
      .run();
    linkMenuVisible = false;
    onClose();
  }
</script>

{#if editor}
  <div class="flex flex-col gap-3 p-3.5 bg-[#09090b]/95 border border-white/10 rounded-2xl shadow-[0_15px_50px_-10px_rgba(0,0,0,0.8),0_0_30px_-5px_rgba(6,182,212,0.2)] backdrop-blur-2xl overflow-hidden w-[320px] animate-in fade-in zoom-in-95 duration-200">
    
    <!-- URL INPUT -->
    <div class="flex flex-col gap-1">
      <div class="flex items-center justify-between">
        <label class="text-[8px] font-black text-cyan-400/50 uppercase tracking-wider flex items-center gap-1.5">
          <Globe size={10} />
          Target URL
        </label>
        {#if url}
          <a 
            href={url} 
            target="_blank" 
            rel="noopener noreferrer"
            class="text-[8px] font-black text-emerald-400 hover:text-emerald-300 transition-colors uppercase tracking-wider flex items-center gap-1"
          >
            Visit Site
            <ExternalLink size={9} />
          </a>
        {/if}
      </div>
      <input 
        type="text" 
        bind:value={url}
        placeholder="https://example.com"
        class="w-full bg-black/40 border border-white/5 rounded-lg px-2.5 py-1.5 text-xs text-cyan-400 font-mono focus:border-cyan-500/50 focus:outline-none transition-colors"
      />
    </div>

    <!-- TITLE INPUT -->
    <div class="flex flex-col gap-1">
      <label class="text-[8px] font-black text-cyan-400/50 uppercase tracking-wider flex items-center gap-1.5">
        <Type size={10} />
        Link Title (SEO ALT Text)
      </label>
      <input 
        type="text" 
        bind:value={title}
        placeholder="Descriptive tooltip text..."
        class="w-full bg-black/40 border border-white/5 rounded-lg px-2.5 py-1.5 text-xs text-white/80 focus:border-cyan-500/50 focus:outline-none transition-colors"
      />
    </div>

    <!-- SEO & SGE BADGES -->
    <div class="flex flex-col gap-1.5 pt-1 border-t border-white/5">
      <span class="text-[8px] font-black text-white/30 uppercase tracking-wider">SEO & SGE Controls</span>
      <div class="grid grid-cols-2 gap-1.5">
        <!-- New Tab -->
        <button 
          onclick={() => isTargetBlank = !isTargetBlank}
          class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-[9px] font-bold transition-all select-none
            {isTargetBlank ? 'bg-cyan-500/10 border-cyan-500/35 text-cyan-400' : 'bg-white/[0.02] border-white/5 text-white/30'}"
        >
          <ExternalLink size={10} />
          <span>New Tab</span>
        </button>

        <!-- No Follow -->
        <button 
          onclick={() => isNoFollow = !isNoFollow}
          class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-[9px] font-bold transition-all select-none
            {isNoFollow ? 'bg-orange-500/10 border-orange-500/35 text-orange-400' : 'bg-white/[0.02] border-white/5 text-white/30'}"
        >
          <Shield size={10} />
          <span>No Follow</span>
        </button>

        <!-- Sponsored -->
        <button 
          onclick={() => isSponsored = !isSponsored}
          class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-[9px] font-bold transition-all select-none
            {isSponsored ? 'bg-purple-500/10 border-purple-500/35 text-purple-400' : 'bg-white/[0.02] border-white/5 text-white/30'}"
        >
          <Sparkles size={10} />
          <span>Sponsored</span>
        </button>

        <!-- UGC -->
        <button 
          onclick={() => isUgc = !isUgc}
          class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-[9px] font-bold transition-all select-none
            {isUgc ? 'bg-pink-500/10 border-pink-500/35 text-pink-400' : 'bg-white/[0.02] border-white/5 text-white/30'}"
        >
          <Users size={10} />
          <span>UGC</span>
        </button>
      </div>
    </div>

    <!-- ACTIONS -->
    <div class="flex items-center justify-between pt-2 border-t border-white/5 mt-0.5">
      <button 
        onclick={unlink}
        class="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-wider text-red-400 hover:bg-red-500/10 transition-colors"
        title="Remove this link"
      >
        <Unlink size={11} />
        <span>Unlink</span>
      </button>

      <div class="flex items-center gap-1.5">
        <button 
          onclick={() => { linkMenuVisible = false; onClose(); }}
          class="flex items-center justify-center p-1.5 rounded-lg text-white/40 hover:text-white hover:bg-white/5 transition-colors"
          title="Cancel and Close"
        >
          <X size={13} />
        </button>

        <button 
          onclick={handleSave}
          disabled={!isDirty}
          class="flex items-center gap-1 px-3 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-wider transition-all
            {isDirty 
              ? 'bg-cyan-500 text-black hover:brightness-110 shadow-[0_0_12px_rgba(6,182,212,0.4)] cursor-pointer' 
              : 'bg-white/5 text-white/20 cursor-not-allowed'}"
          title="Apply Changes"
        >
          <Check size={11} />
          <span>Save</span>
        </button>
      </div>
    </div>

  </div>
{/if}

<style>
  @reference "tailwindcss";
</style>
