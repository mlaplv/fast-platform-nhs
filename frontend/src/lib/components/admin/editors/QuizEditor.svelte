<script lang="ts">
  import { slide } from 'svelte/transition';

  import { liveEditStore } from "$lib/state/commerce/liveEdit.svelte";
  import Check from "@lucide/svelte/icons/check";
  import RotateCcw from "@lucide/svelte/icons/rotate-ccw";
  import Plus from "@lucide/svelte/icons/plus";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import ChevronUp from "@lucide/svelte/icons/chevron-up";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import Settings2 from "@lucide/svelte/icons/settings-2";
  import Smile from "@lucide/svelte/icons/smile";
  import X from "@lucide/svelte/icons/x";
  import type { Product, QuizQuestion } from '$lib/types';

  let { path, onSave } = $props<{
    path: string;
    onSave: (val: QuizQuestion[]) => void;
  }>();

  // Helper to deep get value from product metadata
  function getMetadataValue(p: string): QuizQuestion[] {
    if (!liveEditStore.dirtyProduct) {
        console.warn("QuizEditor: No dirtyProduct in store.");
        return [];
    }
    
    const keys = p.split(".");
    let current: any = liveEditStore.dirtyProduct as Product;

    for (const key of keys) {
      if (!current || typeof current !== 'object') {
        // Elite V2.2 Fallback: If metadata is stringified, try to parse it
        if (typeof current === 'string' && current.trim().startsWith('{')) {
          try {
            current = JSON.parse(current);
            // After parsing, try the key again
            current = current[key];
          } catch(e) { return []; }
        } else {
          return [];
        }
      } else {
        current = current[key];
      }
    }
    
    // Final check and deep clone to avoid proxy reference issues
    if (Array.isArray(current)) {
      return JSON.parse(JSON.stringify(current));
    }
    
    // Level 2 Fallback: If metadata was flattened or path is different
    if (p.includes('quiz_questions')) {
        const fallback = liveEditStore.dirtyMetadata?.quiz_questions;
        if (Array.isArray(fallback)) return JSON.parse(JSON.stringify(fallback));
    }

    return [];
  }

  // Local state for complex editing
  let questions = $state<QuizQuestion[]>(getMetadataValue(path));

  // Sync effect if store was delayed
  $effect(() => {
    if (questions.length === 0 && liveEditStore.dirtyProduct) {
      const refreshed = getMetadataValue(path);
      if (refreshed.length > 0) questions = refreshed;
    }
  });

  function addQuestion() {
    questions.push({
      title: "Câu hỏi mới",
      options: [
        { label: "Lựa chọn 1", value: "val1", icon: "✨" },
        { label: "Lựa chọn 2", value: "val2", icon: "🔬" }
      ]
    });
  }

  function removeQuestion(index: number) {
    questions.splice(index, 1);
  }

  function moveQuestion(index: number, direction: 'up' | 'down') {
    if (direction === 'up' && index > 0) {
      [questions[index], questions[index - 1]] = [questions[index - 1], questions[index]];
    } else if (direction === 'down' && index < questions.length - 1) {
      [questions[index], questions[index + 1]] = [questions[index + 1], questions[index]];
    }
  }

  function addOption(qIndex: number) {
    questions[qIndex].options.push({
      label: "Lựa chọn mới",
      value: `val${questions[qIndex].options.length + 1}`,
      icon: "⚡"
    });
  }

  function removeOption(qIndex: number, optIndex: number) {
    questions[qIndex].options.splice(optIndex, 1);
  }

  function save() {
    onSave(questions);
  }

  function reset() {
    questions = getMetadataValue(path);
  }
</script>

<div class="space-y-8 pb-20">
  <!-- Header HUD -->
  <div class="flex items-center justify-between border-b border-white/5 pb-4">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 bg-blue-500/10 rounded-xl flex items-center justify-center text-blue-400">
        <Settings2 size={20} />
      </div>
      <div>
        <h3 class="text-sm font-semibold text-white uppercase tracking-widest">QUẢN LÝ BỘ CÂU HỎI</h3>
        <p class="text-[8px] text-blue-400 font-mono tracking-widest mt-1">SOURCE: {path.toUpperCase()} // SYNC_ACTIVE</p>
      </div>
    </div>
    <button 
      onclick={addQuestion}
      class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-[10px] font-semibold uppercase tracking-widest transition-all"
    >
      <Plus size={14} /> THÊM CÂU HỎI
    </button>
  </div>

  <!-- Questions List -->
  <div class="space-y-6">
    {#each questions as question, qIndex (qIndex)}
      <div 
        class="bg-white/[0.02] border border-white/10 rounded-2xl overflow-hidden shadow-xl"
        transition:slide
      >
        <!-- Question Header -->
        <div class="px-6 py-4 bg-white/[0.03] flex items-center justify-between border-b border-white/5">
          <div class="flex items-center gap-3">
            <span class="text-[10px] font-semibold text-blue-400/50 font-mono">#{qIndex + 1}</span>
            <input 
              bind:value={question.title}
              class="bg-transparent border-none text-white font-medium text-sm outline-none w-64 placeholder:text-white/10 focus:text-blue-400 transition-colors"
              placeholder="Nhập tiêu đề câu hỏi..."
            />
          </div>
          <div class="flex items-center gap-2">
            <button onclick={() => moveQuestion(qIndex, 'up')} disabled={qIndex === 0} class="p-2 hover:bg-white/5 text-white/40 disabled:opacity-5 transition-all"><ChevronUp size={14} /></button>
            <button onclick={() => moveQuestion(qIndex, 'down')} disabled={qIndex === questions.length - 1} class="p-2 hover:bg-white/5 text-white/40 disabled:opacity-5 transition-all"><ChevronDown size={14} /></button>
            <button onclick={() => removeQuestion(qIndex)} class="p-2 hover:bg-red-500/10 text-red-400/60 hover:text-red-400 transition-all ml-2"><Trash2 size={14} /></button>
          </div>
        </div>

        <!-- Options Manager -->
        <div class="p-6 space-y-4">
          <div class="flex items-center justify-between">
            <h4 class="text-[9px] font-semibold text-white/30 uppercase tracking-[0.2em] italic">Danh sách lựa chọn</h4>
            <button onclick={() => addOption(qIndex)} class="text-[9px] font-semibold text-blue-400/80 hover:text-blue-400 uppercase tracking-widest flex items-center gap-1 transition-all"><Plus size={12} /> THÊM OPTION</button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            {#each question.options as opt, optIndex (optIndex)}
              <div class="flex items-center gap-2 bg-white/[0.03] p-2 rounded-xl border border-white/5 group">
                <div class="relative w-10 h-10 flex-none bg-blue-500/5 rounded-lg border border-white/5 flex items-center justify-center text-xl overflow-hidden">
                   <input bind:value={opt.icon} class="absolute inset-0 w-full h-full bg-transparent border-none text-center text-lg outline-none cursor-default" />
                </div>
                <div class="flex-1 space-y-1">
                  <input bind:value={opt.label} class="w-full bg-transparent border-none text-[10px] font-medium text-white outline-none placeholder:text-white/5" placeholder="Tên lựa chọn" />
                  <input bind:value={opt.value} class="w-full bg-transparent border-none text-[7px] font-mono text-white/20 outline-none uppercase tracking-widest" placeholder="Mã (value)" />
                </div>
                <button onclick={() => removeOption(qIndex, optIndex)} class="opacity-0 group-hover:opacity-100 p-2 text-red-400/40 hover:text-red-400 transition-all"><X size={12} /></button>
              </div>
            {/each}
          </div>
        </div>
      </div>
    {/each}
  </div>

  <!-- Global Actions -->
  <div class="fixed bottom-10 right-8 z-[var(--z-admin-hud)] pointer-events-none">
    <div class="flex flex-col gap-4 pointer-events-auto">
      <button 
        onclick={reset}
        class="w-14 h-14 bg-white/5 hover:bg-white/10 text-white/40 rounded-full transition-all border border-white/10 backdrop-blur-3xl flex items-center justify-center shadow-2xl"
        title="Khôi phục"
      >
        <RotateCcw size={20} />
      </button>
      <button 
        onclick={save}
        class="w-16 h-16 bg-blue-600 hover:bg-blue-500 text-white rounded-full transition-all active:scale-90 shadow-[0_20px_50px_rgba(37,99,235,0.4)] flex items-center justify-center border border-blue-400/20"
        title="Cập nhật phán quyết"
      >
        <Check size={28} strokeWidth={3} />
      </button>
    </div>
  </div>
</div>

<style lang="postcss">
  input::placeholder {
    opacity: 0.3;
  }
</style>
