<script lang="ts">
  import { slide } from "svelte/transition";
  import X from "lucide-svelte/icons/x";

  let {
    editingId,
    formName = $bindable(),
    formSku = $bindable(),
    formPrice = $bindable(),
    formStock = $bindable(),
    formCategory = $bindable(),
    formStatus = $bindable(),
    categories,
    onSave,
    onClose,
  } = $props<{
    editingId: string | null;
    formName: string;
    formSku: string;
    formPrice: number;
    formStock: number;
    formCategory: string;
    formStatus: "active" | "draft";
    categories: { id: string; name: string }[];
    onSave: () => void;
    onClose: () => void;
  }>();
</script>

<div
  class="bg-white/[0.02] border border-[#FFB800]/10 rounded-2xl p-4 flex flex-col gap-3"
  transition:slide
>
  <div class="text-[10px] font-mono text-[#FFB800] uppercase tracking-widest">
    {editingId ? "✏️ Chỉnh sửa sản phẩm" : "➕ Thêm sản phẩm mới"}
  </div>
  <div class="flex items-center gap-3">
    <input
      bind:value={formName}
      placeholder="Tên sản phẩm..."
      class="flex-1 bg-transparent border border-white/5 rounded-xl py-2 px-4 text-xs text-gray-200 placeholder:text-gray-700 focus:outline-none focus:border-[#FFB800]/30 font-sans"
    />
    <input
      bind:value={formSku}
      placeholder="SKU..."
      class="w-28 bg-transparent border border-white/5 rounded-xl py-2 px-4 text-xs text-gray-200 placeholder:text-gray-700 focus:outline-none focus:border-[#FFB800]/30 font-mono uppercase"
    />
    <select
      bind:value={formCategory}
      class="w-40 bg-[#0a0a0a] border border-white/5 rounded-xl py-2 px-4 text-xs text-gray-200 focus:outline-none focus:border-[#FFB800]/30 font-sans"
    >
      <option value="">-- Chọn danh mục --</option>
      {#each categories as cat}
        <option value={cat.id}>{cat.name}</option>
      {/each}
    </select>
  </div>
  <div class="flex items-center gap-3">
    <div class="flex items-center gap-2 flex-1">
      <label
        for="formPrice"
        class="text-[9px] font-mono text-gray-600 uppercase shrink-0"
        >Giá:</label
      >
      <input
        id="formPrice"
        bind:value={formPrice}
        type="number"
        placeholder="0"
        class="flex-1 bg-transparent border border-white/5 rounded-xl py-2 px-4 text-xs text-gray-200 focus:outline-none focus:border-[#FFB800]/30 font-mono"
      />
    </div>
    <div class="flex items-center gap-2 flex-1">
      <label
        for="formStock"
        class="text-[9px] font-mono text-gray-600 uppercase shrink-0"
        >Kho:</label
      >
      <input
        id="formStock"
        bind:value={formStock}
        type="number"
        placeholder="0"
        class="flex-1 bg-transparent border border-white/5 rounded-xl py-2 px-4 text-xs text-gray-200 focus:outline-none focus:border-[#FFB800]/30 font-mono"
      />
    </div>
    <select
      bind:value={formStatus}
      class="bg-[#0a0a0a] border border-white/5 rounded-xl py-2 px-4 text-xs text-gray-200 focus:outline-none focus:border-[#FFB800]/30 font-mono"
    >
      <option value="draft">Nháp</option>
      <option value="active">Đang bán</option>
    </select>
    <button
      onclick={onSave}
      class="px-4 py-2 bg-[#FFB800]/10 border border-[#FFB800]/30 rounded-xl text-[10px] font-mono text-[#FFB800] hover:bg-[#FFB800]/20 transition-all uppercase tracking-wider"
    >
      {editingId ? "Cập nhật" : "Tạo mới"}
    </button>
    <button
      onclick={onClose}
      class="p-2 text-gray-600 hover:text-white transition-colors"
    >
      <X size={14} />
    </button>
  </div>
</div>
