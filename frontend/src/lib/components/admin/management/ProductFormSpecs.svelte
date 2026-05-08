<script lang="ts">
  import Tag from "@lucide/svelte/icons/tag";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Package from "@lucide/svelte/icons/package";

  let {
    formAttributes = $bindable()
  } = $props<{
    formAttributes: Record<string, string | number | boolean | null>;
  }>();

  let newAttrKey = $state("");
  let newAttrValue = $state("");

  function addAttribute() {
    if (newAttrKey.trim() && newAttrValue.trim()) {
      formAttributes = { ...formAttributes, [newAttrKey.trim()]: newAttrValue.trim() };
      newAttrKey = "";
      newAttrValue = "";
    }
  }

  function removeAttribute(key: string) {
    const updated = { ...formAttributes };
    delete updated[key];
    formAttributes = updated;
  }
</script>

<div class="section-label mb-3 text-purple-400/80">
  <Tag size={11} />
  Thông số kỹ thuật
</div>

<div class="flex flex-col gap-3">
  <div class="flex gap-2">
    <input bind:value={newAttrKey} placeholder="Thuộc tính..." class="flex-1 field-input border-b-purple-500/30 text-xs py-1.5 placeholder:text-purple-400/20" />
    <input bind:value={newAttrValue} placeholder="Giá trị..." class="flex-1 field-input border-b-purple-500/30 text-xs py-1.5 placeholder:text-purple-400/20" />
    <button onclick={addAttribute} class="px-3 bg-purple-500/10 hover:bg-purple-500 text-purple-500 hover:text-white rounded-lg text-[9px] font-black uppercase tracking-wider transition-all border border-purple-500/30 shadow-inner">Điền</button>
  </div>

  <div class="flex flex-col gap-2 max-h-[400px] overflow-y-auto pr-1 custom-scrollbar">
    {#each Object.entries(formAttributes) as [key, val]}
      <div class="flex items-center justify-between p-2.5 bg-white/[0.02] border border-white/5 rounded-xl group hover:border-purple-500/20 transition-colors">
        <div class="flex flex-col gap-0.5">
          <span class="text-[8px] font-black text-purple-400 uppercase tracking-widest">{key}</span>
          <span class="text-xs text-white/90 font-medium truncate w-[200px] block">{val}</span>
        </div>
        <button onclick={() => removeAttribute(key)} class="p-1.5 text-red-400/50 hover:text-red-500 rounded-lg hover:bg-red-500/10 opacity-0 group-hover:opacity-100 transition-all border border-transparent hover:border-red-500/20">
          <Trash2 size={12} />
        </button>
      </div>
    {/each}
    
    {#if Object.keys(formAttributes).length === 0}
      <div class="py-12 border border-dashed border-white/5 rounded-xl flex flex-col items-center justify-center opacity-30 mt-2 bg-black/40">
        <Package size={24} class="mb-2 text-purple-400/50" />
        <div class="text-[8px] font-black uppercase tracking-[0.2em] text-center w-[80%]">Sản phẩm chưa có thông số hệ thống</div>
      </div>
    {/if}
  </div>
</div>

<style>
  @reference "tailwindcss";
  .section-label { @apply flex items-center gap-2 text-[9px] font-black uppercase tracking-[0.35em] text-white/30; }
  .field-input { @apply w-full bg-transparent border-b border-white/8 px-1 py-1.5 text-white placeholder:text-white/15 outline-none transition-colors; }
</style>
