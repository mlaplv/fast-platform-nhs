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

<!-- Responsive Table Header (Hidden on Mobile) -->
<div class="hidden md:grid grid-cols-[40px_minmax(250px,2fr)_1fr_1fr_1fr_1fr_100px] gap-4 px-4 py-4 sticky top-0 bg-[#050505] z-10 border-b border-white/10 uppercase tracking-widest text-[9px] font-bold font-mono text-gray-400">
  <div class="text-center"></div>
  <div>Product Details</div>
  <div>Registry ID</div>
  <div>Valuation</div>
  <div>Quantity</div>
  <div>System Status</div>
  <div class="text-right">Operations</div>
</div>

<div class="flex flex-col flex-1 pb-10">
  <div class="flex flex-col xs:gap-2 gap-4 divide-y md:divide-y-[1px] divide-white/[0.02] md:divide-white/[0.05] md:gap-0 px-2 sm:px-4 md:px-0">
    {#each products as product (product.id)}
      {@const status = statusMap[product.status] || {
        label: product.status,
        color: "#666",
      }}
      <!-- Responsive List Item (Vertical card on Mobile, Grid row on Desktop) -->
      <div
        class="group relative flex flex-col md:grid md:grid-cols-[40px_minmax(250px,2fr)_1fr_1fr_1fr_1fr_100px] md:gap-4 md:items-center bg-[#0a0a0a] md:bg-transparent border border-white/5 md:border-none p-3 sm:p-4 rounded-xl md:rounded-none hover:bg-white/[0.03] transition-colors duration-300"
      >
        <!-- Selection Checkbox -->
        <div class="absolute top-2 left-2 md:relative md:top-auto md:left-auto md:flex md:justify-center z-10">
          <button
            onclick={() => onToggleSelect(product.id)}
            class="text-gray-600 hover:text-[#FFB800] transition-colors"
          >
            {#if selectedIds.has(product.id)}<CheckSquare size={16} />{:else}<Square size={16} />{/if}
          </button>
        </div>

        <!-- Product Image & Basic Info (Title/Category) -->
        <div class="flex items-start md:items-center gap-3 md:pl-0 pl-6 w-full">
          <div
            class="w-12 h-12 md:w-10 md:h-10 rounded-xl bg-gradient-to-br from-[#FFB800]/10 to-transparent border border-[#FFB800]/20 flex items-center justify-center shrink-0 shadow-[0_0_15px_rgba(255,184,0,0.05)] md:group-hover:scale-105 transition-transform duration-300"
          >
            <Package size={18} class="text-[#FFB800]/70" />
          </div>
          <div class="min-w-0 flex flex-col justify-center flex-1">
            <div class="text-[14px] md:text-[13px] font-bold text-gray-100 truncate group-hover:text-white transition-colors tracking-wide">
              {product.name}
            </div>
            <div class="text-[10px] font-mono text-[#FFB800]/50 mt-1 uppercase tracking-widest flex items-center gap-2">
              <span class="truncate">{product.category || "Uncategorized"}</span>
              <span class="md:hidden text-gray-600">|</span>
              <span class="md:hidden text-gray-500">{product.sku}</span>
            </div>
          </div>
        </div>

        <!-- Desktop SKU -->
        <div class="hidden md:block text-[10px] font-mono text-gray-500 uppercase tracking-wider group-hover:text-gray-300 transition-colors truncate">
          {product.sku}
        </div>

        <!-- Mobile: Grid for Stats / Desktop: Individual columns -->
        <!-- Valuation -->
        <div class="pl-[72px] md:pl-0 mt-3 md:mt-0 flex md:flex-none items-center justify-between md:justify-start">
          <span class="md:hidden text-[9px] font-mono text-gray-500 tracking-widest uppercase">Price</span>
          <span class="text-xs font-bold font-mono text-[#00FFFF] group-hover:text-white transition-colors tracking-wider">
            {formatCurrency(product.price)}
          </span>
        </div>

        <!-- Quantity -->
        <div class="pl-[72px] md:pl-0 mt-1 md:mt-0 flex md:flex-none items-center justify-between md:justify-start">
          <span class="md:hidden text-[9px] font-mono text-gray-500 tracking-widest uppercase">Stock</span>
          <span class="px-2.5 py-1 rounded bg-black/40 xl:bg-transparent xl:border-none md:px-0 md:py-0 border border-white/5 shadow-inner md:shadow-none text-[11px] font-mono font-bold {
            product.stock === 0 ? 'text-red-400 border-red-500/20' : 
            product.stock < 20 ? 'text-[#FFB800] border-[#FFB800]/20' : 
            'text-gray-300'
          }">
            {product.stock}
            <span class="text-[9px] text-gray-600 ml-1">UNITS</span>
          </span>
        </div>

        <!-- System Status -->
        <div class="pl-[72px] md:pl-0 mt-3 md:mt-0 flex md:flex-none justify-start items-center">
          <span
            class="px-3 py-1 md:py-1.5 rounded-lg text-[9px] font-bold font-mono uppercase tracking-widest shadow-inner inline-flex"
            style:color={status.color}
            style:border="1px solid {status.color}40"
            style:background="{status.color}15"
          >
            {status.label}
          </span>
        </div>

        <!-- Operations / Actions -->
        <div class="absolute bottom-3 right-3 md:relative md:bottom-auto md:right-auto md:flex shadow-[-20px_0_20px_-5px_transparent]">
          <div class="flex items-center gap-1.5 justify-end md:opacity-0 group-hover:opacity-100 transition-opacity duration-300 md:translate-x-2 md:group-hover:translate-x-0 w-full bg-[#0a0a0a] md:bg-transparent pl-2">
            <button
              onclick={(e) => { e.stopPropagation(); onEdit(product); }}
              class="p-2 text-gray-400 md:text-gray-500 hover:text-[#00FFFF] transition-colors rounded-xl md:bg-black/40 bg-white/5 border border-transparent hover:border-[#00FFFF]/20 shadow-sm"
              title="Edit Product"
            >
              <Pencil size={14} />
            </button>
            <button
              onclick={(e) => { e.stopPropagation(); onDelete(product.id); }}
              class="p-2 text-red-500 md:text-gray-500 hover:text-red-400 transition-colors rounded-xl md:bg-black/40 bg-white/5 border border-transparent hover:border-red-500/20 shadow-sm"
              title="Delete Product"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>
      </div>
    {/each}
  </div>
</div>
