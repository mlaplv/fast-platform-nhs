<script lang="ts">
  import Tag from "@lucide/svelte/icons/tag";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Package from "@lucide/svelte/icons/package";
  import Edit2 from "@lucide/svelte/icons/edit-2";
  import Plus from "@lucide/svelte/icons/plus";

  import type { ProductFormState } from "$lib/types";

  let {
    formState = $bindable()
  } = $props<{
    formState: ProductFormState;
  }>();

  let newAttrKey = $state("");
  let newAttrValue = $state("");
  let showForm = $state(false);
  let originalKey = $state<string | null>(null);

  function addAttribute() {
    if (newAttrKey.trim() && newAttrValue.trim()) {
      const key = newAttrKey.trim();
      const val = newAttrValue.trim();

      // Nếu đang edit và đổi tên key -> Xóa key cũ
      if (originalKey && originalKey !== key) {
        delete formState.attributes[originalKey];
      }

      formState.attributes[key] = val;
      
      // Reset form
      newAttrKey = "";
      newAttrValue = "";
      originalKey = null;
      showForm = false; // Tự động đóng sau khi xong cho gọn
    }
  }

  function removeAttribute(key: string) {
    delete formState.attributes[key];
  }

  function renameKey(oldKey: string, newKey: string) {
    newKey = newKey.trim();
    if (!newKey || oldKey === newKey) return;

    if (formState.attributes[newKey]) return;

    const entries = Object.entries(formState.attributes);
    const result: Record<string, string> = {};
    for (const [k, v] of entries) {
      if (k === oldKey) {
        result[newKey] = v;
      } else {
        result[k] = v;
      }
    }
    formState.attributes = result;
  }

  function startEdit(key: string, val: string) {
    newAttrKey = key;
    newAttrValue = val;
    originalKey = key;
    showForm = true;
  }
</script>

<div class="section-label mb-4 flex items-center justify-between">
  <div class="flex items-center gap-2 text-purple-400/80">
    <Tag size={11} />
    Thông số kỹ thuật
  </div>
  <button 
    type="button"
    onclick={() => showForm = !showForm}
    class="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400 text-[9px] font-black tracking-widest hover:bg-purple-500/20 transition-all shadow-lg shadow-purple-500/5"
  >
    {#if showForm}
      ĐÓNG
    {:else}
      <Edit2 size={10} />
      EDIT / THÊM
    {/if}
  </button>
</div>

<div class="flex flex-col gap-3">
{#if showForm}
    <div class="flex gap-2 p-3 rounded-xl bg-purple-500/[0.03] border border-purple-500/10 mb-2 animate-in fade-in slide-in-from-top-1 duration-200">
      <input bind:value={newAttrKey} placeholder="Thuộc tính..." class="flex-1 field-input border-b-purple-500/30 text-xs py-1.5 placeholder:text-purple-400/20" />
      <input bind:value={newAttrValue} placeholder="Giá trị..." class="flex-1 field-input border-b-purple-500/30 text-xs py-1.5 placeholder:text-purple-400/20" />
      <button onclick={addAttribute} class="px-4 bg-purple-500/20 hover:bg-purple-500 text-purple-400 hover:text-white rounded-lg text-[9px] font-black tracking-wider transition-all border border-purple-500/30 shadow-inner">
        {originalKey ? 'CẬP NHẬT' : 'ĐIỀN'}
      </button>
    </div>
  {/if}

  <div class="flex flex-col gap-2 max-h-[400px] overflow-y-auto pr-1 custom-scrollbar">
    {#each Object.entries(formState.attributes) as [key, val]}
      <div class="flex items-center justify-between p-2.5 bg-white/[0.02] border border-white/5 rounded-xl group hover:border-purple-500/20 transition-colors">
        <div class="flex flex-col gap-0.5 flex-1">
          <input 
            type="text"
            value={key}
            onblur={(e) => renameKey(key, e.currentTarget.value)}
            class="text-[8px] font-black text-purple-400 tracking-widest bg-transparent border-none outline-none p-0 uppercase placeholder:text-purple-400/20 focus:text-purple-300 transition-colors" 
          />
          <input 
            type="text"
            bind:value={formState.attributes[key]}
            class="text-xs text-white/90 font-medium bg-transparent border-none outline-none p-0 w-full placeholder:text-white/20 focus:text-white transition-colors" 
          />
        </div>
        <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">
          <button 
            type="button"
            onclick={() => startEdit(key, val)} 
            class="p-1.5 text-purple-400/50 hover:text-purple-400 rounded-lg hover:bg-purple-500/10 border border-transparent hover:border-purple-500/20"
          >
            <Edit2 size={12} />
          </button>
          <button 
            type="button"
            onclick={() => removeAttribute(key)} 
            class="p-1.5 text-red-400/50 hover:text-red-500 rounded-lg hover:bg-red-500/10 border border-transparent hover:border-red-500/20"
          >
            <Trash2 size={12} />
          </button>
        </div>
      </div>
    {/each}
    
    {#if Object.keys(formState.attributes).length === 0}
      <div class="py-12 border border-dashed border-white/5 rounded-xl flex flex-col items-center justify-center opacity-30 mt-2 bg-black/40">
        <Package size={24} class="mb-2 text-purple-400/50" />
        <div class="text-[8px] font-black tracking-[0.2em] text-center w-[80%]">Sản phẩm chưa có thông số hệ thống</div>
      </div>
    {/if}
  </div>
</div>

<style>
  @reference "tailwindcss";
  .section-label { @apply flex items-center gap-2 text-[9px] font-black tracking-[0.35em] text-white/30; }
  .field-input { @apply w-full bg-transparent border-b border-white/8 px-1 py-1.5 text-white placeholder:text-white/15 outline-none transition-colors; }
</style>
