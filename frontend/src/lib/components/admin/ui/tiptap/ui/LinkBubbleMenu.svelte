<script lang="ts">
  import type { Editor } from '@tiptap/core';
    import Edit3 from "@lucide/svelte/icons/edit-3";
  import Unlink from "@lucide/svelte/icons/unlink";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import Globe from "@lucide/svelte/icons/globe";

  let { editor, onEdit, onClose }: { 
    editor: Editor; 
    onEdit: () => void; 
    onClose: () => void 
  } = $props();

  function unlink() {
    if (!editor || editor.isDestroyed) return;
    editor.chain().focus().unsetLink().run();
    onClose();
  }

  let currentUrl = $derived(editor?.getAttributes('link').href || '');
  let displayUrl = $derived(currentUrl.replace(/^https?:\/\//, '').substring(0, 30) + (currentUrl.length > 30 ? '...' : ''));
</script>

{#if editor}
  <div class="flex items-center gap-1.5 p-1.5 bg-[#09090b]/95 border border-white/10 rounded-xl shadow-[0_0_30px_-5px_rgba(6,182,212,0.3)] backdrop-blur-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
    
    <!-- URL Preview -->
    <div class="flex items-center gap-2 px-2 py-1 bg-white/5 border border-white/5 rounded-lg mr-1 max-w-[200px]">
      <Globe size={11} class="text-cyan-400/60" />
      <span class="text-[10px] text-white/40 truncate font-mono">{displayUrl || 'No URL'}</span>
    </div>

    <div class="w-px h-4 bg-white/10 mx-0.5"></div>

    <!-- Actions -->
    <div class="flex items-center gap-0.5">
      <button 
        onclick={onEdit} 
        class="p-1.5 rounded-lg text-white/50 hover:bg-cyan-500/20 hover:text-cyan-400 transition-all active:scale-90" 
        title="Chỉnh sửa liên kết"
      >
        <Edit3 size={13} />
      </button>

      {#if currentUrl}
        <a 
          href={currentUrl} 
          target="_blank" 
          rel="noopener noreferrer"
          class="p-1.5 rounded-lg text-white/50 hover:bg-emerald-500/20 hover:text-emerald-400 transition-all active:scale-90" 
          title="Mở trong tab mới"
        >
          <ExternalLink size={13} />
        </a>
      {/if}

      <button 
        onclick={unlink} 
        class="p-1.5 rounded-lg text-white/50 hover:bg-red-500/20 hover:text-red-400 transition-all active:scale-90" 
        title="Gỡ bỏ liên kết"
      >
        <Unlink size={13} />
      </button>
    </div>
  </div>
{/if}

<style>
  @reference "tailwindcss";
</style>
