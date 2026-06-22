<script lang="ts">
  import type { Editor } from '@tiptap/core';
  import Table from "@lucide/svelte/icons/table";
  import ArrowUp from "@lucide/svelte/icons/arrow-up";
  import ArrowDown from "@lucide/svelte/icons/arrow-down";
  import ArrowLeft from "@lucide/svelte/icons/arrow-left";
  import ArrowRight from "@lucide/svelte/icons/arrow-right";
  import Merge from "@lucide/svelte/icons/merge";
  import Split from "@lucide/svelte/icons/split";
  import Heading from "@lucide/svelte/icons/heading";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import AlignLeft from "@lucide/svelte/icons/align-left";
  import AlignCenter from "@lucide/svelte/icons/align-center";
  import AlignRight from "@lucide/svelte/icons/align-right";
  import AlignJustify from "@lucide/svelte/icons/align-justify";

  let { editor, onClose }: { editor: Editor; onClose: () => void } = $props();

  // Helper check for cell merge/split abilities (reacts to editor state updates)
  let canMerge = $derived(editor ? editor.can().mergeCells() : false);
  let canSplit = $derived(editor ? editor.can().splitCell() : false);

  // Helper to determine alignment in active cell
  let currentAlign = $derived(
    editor?.isActive({ textAlign: 'center' }) ? 'center'
    : editor?.isActive({ textAlign: 'right' }) ? 'right'
    : editor?.isActive({ textAlign: 'justify' }) ? 'justify'
    : 'left'
  );

  let isHeaderRow = $derived(editor?.isActive('tableHeader') || false);

  function execute(command: () => void) {
    if (!editor || editor.isDestroyed) return;
    command();
  }
</script>

{#if editor}
  <div class="flex flex-col gap-0 bg-[#18181b]/95 border border-white/10 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.6),0_0_30px_rgba(16,185,129,0.15)] backdrop-blur-xl overflow-hidden min-w-[340px] p-1 animate-in fade-in zoom-in-95 duration-150">
    
    <!-- Table Header Info Bar -->
    <div class="flex items-center gap-2 px-3 py-2 border-b border-white/5 bg-white/[0.02]">
      <Table size={13} class="text-emerald-400" />
      <span class="text-[10px] font-black text-white/50 uppercase tracking-wider">Clinical Table Tool</span>
    </div>

    <!-- Group 1: Alignment & Headers -->
    <div class="flex items-center gap-1.5 p-1.5 border-b border-white/5">
      <!-- Text Alignment -->
      <div class="flex items-center gap-0.5 bg-black/30 rounded-xl p-0.5 border border-white/5">
        <button 
          onclick={() => execute(() => editor.chain().focus().setTextAlign('left').run())} 
          class="p-1.5 rounded-lg transition-all active:scale-90 {currentAlign === 'left' ? 'bg-emerald-500/20 text-emerald-400' : 'text-white/40 hover:text-white hover:bg-white/5'}" 
          title="Căn trái văn bản"
        >
          <AlignLeft size={13} />
        </button>
        <button 
          onclick={() => execute(() => editor.chain().focus().setTextAlign('center').run())} 
          class="p-1.5 rounded-lg transition-all active:scale-90 {currentAlign === 'center' ? 'bg-emerald-500/20 text-emerald-400' : 'text-white/40 hover:text-white hover:bg-white/5'}" 
          title="Căn giữa văn bản"
        >
          <AlignCenter size={13} />
        </button>
        <button 
          onclick={() => execute(() => editor.chain().focus().setTextAlign('right').run())} 
          class="p-1.5 rounded-lg transition-all active:scale-90 {currentAlign === 'right' ? 'bg-emerald-500/20 text-emerald-400' : 'text-white/40 hover:text-white hover:bg-white/5'}" 
          title="Căn phải văn bản"
        >
          <AlignRight size={13} />
        </button>
        <button 
          onclick={() => execute(() => editor.chain().focus().setTextAlign('justify').run())} 
          class="p-1.5 rounded-lg transition-all active:scale-90 {currentAlign === 'justify' ? 'bg-emerald-500/20 text-emerald-400' : 'text-white/40 hover:text-white hover:bg-white/5'}" 
          title="Căn đều văn bản"
        >
          <AlignJustify size={13} />
        </button>
      </div>

      <div class="w-px h-4 bg-white/10 mx-0.5"></div>

      <!-- Headers & Merge -->
      <div class="flex items-center gap-1">
        <button 
          onclick={() => execute(() => editor.chain().focus().toggleHeaderRow().run())} 
          class="flex items-center gap-1 px-2.5 py-1.5 rounded-xl border text-[9px] font-black transition-all select-none
            {isHeaderRow ? 'bg-emerald-500/20 border-emerald-500/30 text-emerald-400' : 'bg-white/[0.02] border-white/5 text-white/40 hover:bg-white/5'}"
          title="Bật/Tắt Dòng Tiêu Đề (Header Row)"
        >
          <Heading size={10} />
          <span>Dòng đầu</span>
        </button>

        <button 
          onclick={() => execute(() => editor.chain().focus().toggleHeaderColumn().run())} 
          class="flex items-center gap-1 px-2.5 py-1.5 rounded-xl border text-[9px] font-black transition-all select-none bg-white/[0.02] border-white/5 text-white/40 hover:bg-white/5 hover:text-white"
          title="Bật/Tắt Cột Tiêu Đề (Header Column)"
        >
          <Heading size={10} class="rotate-90" />
          <span>Cột đầu</span>
        </button>
      </div>
    </div>

    <!-- Group 2: Row & Column Management -->
    <div class="flex flex-col gap-1.5 p-2 border-b border-white/5">
      <div class="flex items-center justify-between">
        <span class="text-[8px] font-black text-white/30 uppercase tracking-widest px-1">Row & Column Operations</span>
      </div>
      
      <div class="grid grid-cols-2 gap-1.5">
        <!-- Row Controls -->
        <div class="flex flex-col gap-1 p-1 bg-black/25 rounded-xl border border-white/5">
          <span class="text-[7px] font-black text-white/20 uppercase tracking-wider px-1 text-center">Rows</span>
          <div class="grid grid-cols-3 gap-1">
            <button onclick={() => execute(() => editor.chain().focus().addRowBefore().run())} class="p-1.5 rounded-lg bg-white/5 text-white/60 hover:text-white hover:bg-white/10 flex items-center justify-center transition-all active:scale-95" title="Thêm dòng phía trên"><ArrowUp size={11} /></button>
            <button onclick={() => execute(() => editor.chain().focus().addRowAfter().run())} class="p-1.5 rounded-lg bg-white/5 text-white/60 hover:text-white hover:bg-white/10 flex items-center justify-center transition-all active:scale-95" title="Thêm dòng phía dưới"><ArrowDown size={11} /></button>
            <button onclick={() => execute(() => editor.chain().focus().deleteRow().run())} class="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 hover:text-rose-300 flex items-center justify-center transition-all active:scale-95" title="Xóa dòng hiện tại"><Trash2 size={11} /></button>
          </div>
        </div>

        <!-- Column Controls -->
        <div class="flex flex-col gap-1 p-1 bg-black/25 rounded-xl border border-white/5">
          <span class="text-[7px] font-black text-white/20 uppercase tracking-wider px-1 text-center">Columns</span>
          <div class="grid grid-cols-3 gap-1">
            <button onclick={() => execute(() => editor.chain().focus().addColumnBefore().run())} class="p-1.5 rounded-lg bg-white/5 text-white/60 hover:text-white hover:bg-white/10 flex items-center justify-center transition-all active:scale-95" title="Thêm cột bên trái"><ArrowLeft size={11} /></button>
            <button onclick={() => execute(() => editor.chain().focus().addColumnAfter().run())} class="p-1.5 rounded-lg bg-white/5 text-white/60 hover:text-white hover:bg-white/10 flex items-center justify-center transition-all active:scale-95" title="Thêm cột bên phải"><ArrowRight size={11} /></button>
            <button onclick={() => execute(() => editor.chain().focus().deleteColumn().run())} class="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 hover:text-rose-300 flex items-center justify-center transition-all active:scale-95" title="Xóa cột hiện tại"><Trash2 size={11} /></button>
          </div>
        </div>
      </div>
    </div>

    <!-- Group 3: Merge, Split & Danger -->
    <div class="flex items-center justify-between p-2 bg-white/[0.01]">
      <div class="flex items-center gap-1">
        <!-- Merge Cells -->
        <button 
          onclick={() => execute(() => editor.chain().focus().mergeCells().run())}
          disabled={!canMerge}
          class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-[9px] font-black uppercase tracking-wider transition-all select-none
            {canMerge 
              ? 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30' 
              : 'bg-white/[0.01] text-white/10 border border-white/5 cursor-not-allowed'}"
          title="Gộp các ô đang chọn"
        >
          <Merge size={11} />
          <span>Gộp ô</span>
        </button>

        <!-- Split Cell -->
        <button 
          onclick={() => execute(() => editor.chain().focus().splitCell().run())}
          disabled={!canSplit}
          class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-[9px] font-black uppercase tracking-wider transition-all select-none
            {canSplit 
              ? 'bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30' 
              : 'bg-white/[0.01] text-white/10 border border-white/5 cursor-not-allowed'}"
          title="Tách ô đang gộp"
        >
          <Split size={11} />
          <span>Tách ô</span>
        </button>
      </div>

      <!-- Delete Table -->
      <button 
        onclick={() => { execute(() => editor.chain().focus().deleteTable().run()); onClose(); }}
        class="flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-[9px] font-black uppercase tracking-wider text-rose-500 hover:bg-rose-500/10 hover:text-rose-400 transition-colors"
        title="Xóa toàn bộ bảng"
      >
        <Trash2 size={11} />
        <span>Xóa Bảng</span>
      </button>
    </div>

  </div>
{/if}

<style>
  @reference "tailwindcss";
</style>
