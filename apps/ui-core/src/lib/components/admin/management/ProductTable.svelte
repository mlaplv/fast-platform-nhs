<script lang="ts">
  import Package from "lucide-svelte/icons/package";
  import Pencil from "lucide-svelte/icons/pencil";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import CheckSquare from "lucide-svelte/icons/check-square";
  import Square from "lucide-svelte/icons/square";

  let {
    products,
    selectedIds,
    statusMap,
    formatCurrency,
    onToggleSelect,
    onEdit,
    onDelete,
  } = $props<{
    products: any[];
    selectedIds: Set<string>;
    statusMap: Record<string, { label: string; color: string }>;
    formatCurrency: (n: number) => string;
    onToggleSelect: (id: string) => void;
    onEdit: (p: any) => void;
    onDelete: (id: string) => void;
  }>();
</script>

<table class="w-full text-left border-collapse">
  <thead
    class="sticky top-0 bg-black/80 backdrop-blur-md z-10 shadow-[0_4px_20px_rgba(0,0,0,0.5)]"
  >
    <tr>
      <th
        class="px-6 py-4 text-[9px] font-bold font-mono text-gray-500 uppercase tracking-widest border-b border-white/10 w-10"
      ></th>
      <th
        class="px-4 py-4 text-[9px] font-bold font-mono text-gray-400 uppercase tracking-widest border-b border-white/10"
        >Product Details</th
      >
      <th
        class="px-4 py-4 text-[9px] font-bold font-mono text-gray-400 uppercase tracking-widest border-b border-white/10"
        >Registry ID</th
      >
      <th
        class="px-4 py-4 text-[9px] font-bold font-mono text-gray-400 uppercase tracking-widest border-b border-white/10"
        >Valuation</th
      >
      <th
        class="px-4 py-4 text-[9px] font-bold font-mono text-gray-400 uppercase tracking-widest border-b border-white/10"
        >Quantity</th
      >
      <th
        class="px-4 py-4 text-[9px] font-bold font-mono text-gray-400 uppercase tracking-widest border-b border-white/10"
        >System Status</th
      >
      <th
        class="px-4 py-4 text-[9px] font-bold font-mono text-gray-400 uppercase tracking-widest border-b border-white/10 text-right"
        >Operations</th
      >
    </tr>
  </thead>
  <tbody class="divide-y divide-white/[0.02]">
    {#each products as product (product.id)}
      {@const status = statusMap[product.status] || {
        label: product.status,
        color: "#666",
      }}
      <tr
        class="hover:bg-white/[0.03] transition-colors duration-300 group relative"
      >
        <td class="px-6 py-5 relative z-10">
          <div
            class="absolute inset-y-0 left-0 w-[2px] bg-gradient-to-b from-[#FFB800]/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"
          ></div>
          <button
            onclick={() => onToggleSelect(product.id)}
            class="text-gray-600 hover:text-[#FFB800] transition-colors relative z-10"
          >
            {#if selectedIds.has(product.id)}<CheckSquare
                size={15}
              />{:else}<Square size={15} />{/if}
          </button>
        </td>
        <td class="px-4 py-5 font-mono">
          <div class="flex items-center gap-3">
            <div
              class="w-10 h-10 rounded-xl bg-gradient-to-br from-[#FFB800]/10 to-transparent border border-[#FFB800]/20 flex items-center justify-center shrink-0 shadow-[0_0_15px_rgba(255,184,0,0.05)] group-hover:scale-105 transition-transform duration-300"
            >
              <Package size={16} class="text-[#FFB800]/70" />
            </div>
            <div class="min-w-0 flex flex-col justify-center">
              <div
                class="text-[13px] font-bold text-gray-100 truncate group-hover:text-white transition-colors tracking-wide"
              >
                {product.name}
              </div>
              <div
                class="text-[10px] font-mono text-[#FFB800]/50 mt-1 uppercase tracking-widest"
              >
                {product.category || "Uncategorized"}
              </div>
            </div>
          </div>
        </td>
        <td
          class="px-4 py-5 text-[10px] font-mono text-gray-500 uppercase tracking-wider group-hover:text-gray-300 transition-colors"
          >{product.sku}</td
        >
        <td
          class="px-4 py-5 text-xs font-bold font-mono text-[#00FFFF] group-hover:text-white transition-colors tracking-wider flex items-center h-full mt-2"
          >{formatCurrency(product.price)}</td
        >
        <td class="px-4 py-5">
          <span
            class="px-2.5 py-1 rounded bg-black/40 border border-white/5 shadow-inner text-[11px] font-mono font-bold {product.stock ===
            0
              ? 'text-red-400 border-red-500/20'
              : product.stock < 20
                ? 'text-[#FFB800] border-[#FFB800]/20'
                : 'text-gray-300'}"
          >
            {product.stock}
            <span class="text-[9px] text-gray-600 ml-1">UNITS</span>
          </span>
        </td>
        <td class="px-4 py-5">
          <span
            class="px-3 py-1.5 rounded-lg text-[9px] font-bold font-mono uppercase tracking-widest shadow-inner relative overflow-hidden inline-flex"
            style:color={status.color}
            style:border="1px solid {status.color}40"
            style:background="{status.color}15"
          >
            <div
              class="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"
            ></div>
            {status.label}
          </span>
        </td>
        <td class="px-4 py-5 text-right relative z-10">
          <div
            class="flex items-center gap-1.5 justify-end opacity-0 group-hover:opacity-100 transition-opacity duration-300 translate-x-2 group-hover:translate-x-0"
          >
            <button
              onclick={(e) => {
                e.stopPropagation();
                onEdit(product);
              }}
              class="p-2 text-gray-500 hover:text-[#00FFFF] transition-colors rounded-xl hover:bg-[#00FFFF]/10 bg-black/40 border border-transparent hover:border-[#00FFFF]/20 shadow-sm"
              title="Edit Product"
            >
              <Pencil size={14} />
            </button>
            <button
              onclick={(e) => {
                e.stopPropagation();
                onDelete(product.id);
              }}
              class="p-2 text-gray-500 hover:text-red-400 transition-colors rounded-xl hover:bg-red-500/10 bg-black/40 border border-transparent hover:border-red-500/20 shadow-sm"
              title="Delete Product"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </td>
      </tr>
    {/each}
  </tbody>
</table>
