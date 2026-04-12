<script lang="ts">
  import { liveEditStore } from "$lib/state/commerce/liveEdit.svelte";
  import { Check, RotateCcw } from "lucide-svelte";
  import type { Product } from '$lib/types';

  let { path, type, onSave } = $props<{
    path: string;
    type: 'text' | 'html';
    onSave: (val: string) => void;
  }>();

  // Get current value from dirty metadata
  function getValue(p: string) {
    if (!liveEditStore.dirtyProduct) return "";
    const keys = p.split(".");
    let current: any = liveEditStore.dirtyProduct as Product;
    for (const key of keys) {
        if (!current) return "";
        current = (current as any)[key];
    }
    return current || "";
  }

  let val = $state(getValue(path));

  function save() {
    onSave(val);
  }

  function reset() {
    val = getValue(path);
  }
</script>

<div class="space-y-6">
  <div class="relative group">
    <textarea 
      bind:value={val}
      rows="6"
      class="w-full bg-white/5 border border-white/10 rounded-2xl p-6 text-white text-base placeholder:text-white/10 focus:border-blue-500/50 focus:ring-4 focus:ring-blue-500/10 transition-all outline-none font-medium leading-relaxed"
      placeholder="Nhập nội dung tại đây..."
    ></textarea>
  </div>

  <div class="flex items-center gap-3">
    <button 
      onclick={save}
      class="flex-1 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-[11px] font-black uppercase tracking-[.3em] transition-all active:scale-95 shadow-lg flex items-center justify-center gap-2"
    >
      <Check size={16} />
      CẬP NHẬT
    </button>
    <button 
      onclick={reset}
      class="p-4 bg-white/5 hover:bg-white/10 text-white/40 rounded-xl transition-all"
      title="Khôi phục"
    >
      <RotateCcw size={18} />
    </button>
  </div>
</div>
