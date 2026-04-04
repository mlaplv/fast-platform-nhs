<script lang="ts">
  import Package from "lucide-svelte/icons/package";
  import Pencil from "lucide-svelte/icons/pencil";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import CheckSquare from "lucide-svelte/icons/check-square";
  import Square from "lucide-svelte/icons/square";
  import ExternalLink from "lucide-svelte/icons/external-link";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { formatCurrency } from "$lib/utils/format";
  import type { Product } from "$lib/types";

  let {
    products,
    selectedIds,
    statusMap,
    onToggleSelect,
    onEdit,
    onDelete,
  } = $props<{
    products: Product[];
    selectedIds: Set<string>;
    statusMap: Record<string, { label: string; color: string }>;
    onToggleSelect: (id: string) => void;
    onEdit: (p: Product) => void;
    onDelete: (id: string) => void;
  }>();

  $effect(() => {
    const action = nanobot.commandAction;
    if (action?.entity === "product") {
      if (action.verb === "edit" && action.args) {
        const target = products.find(
          (p) =>
            p.id === action.args ||
            p.name.toLowerCase().includes(action.args.toLowerCase()) ||
            p.sku.toLowerCase() === action.args.toLowerCase(),
        );
        if (target && nanobot.consumeCommand("edit", "product")) {
          onEdit(target);
        }
      }
      if (action.verb === "delete" && action.args) {
        const target = products.find(
          (p) =>
            p.id === action.args ||
            p.name.toLowerCase().includes(action.args.toLowerCase()) ||
            p.sku.toLowerCase() === action.args.toLowerCase(),
        );
        if (target && nanobot.consumeCommand("delete", "product")) {
          onDelete(target.id);
        }
      }
    }
  });
</script>

<!-- Responsive Table Header (Hidden on Mobile) -->
<div class="hidden md:grid grid-cols-[40px_minmax(250px,2fr)_1fr_1fr_1fr_1fr_100px] gap-4 px-4 py-4 sticky top-0 bg-[#050505] border-b border-white/10 uppercase tracking-widest text-[9px] font-bold font-mono text-gray-400"
     style="z-index: var(--z-sticky_header);">
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
        <div class="absolute top-2 left-2 md:relative md:top-auto md:left-auto md:flex md:justify-center"
             style="z-index: var(--z-surface);">
          <button
            onclick={(e: MouseEvent) => { e.stopPropagation(); onToggleSelect(product.id); }}
            class="text-gray-600 hover:text-[#FFB800] transition-colors"
          >
            {#if selectedIds.has(product.id)}<CheckSquare size={16} />{:else}<Square size={16} />{/if}
          </button>
        </div>

        <!-- Product Image & Basic Info (Title/Category) -->
        <div class="flex items-start md:items-center gap-4 md:pl-0 pl-6 w-full">
          <div
            class="w-14 h-14 md:w-12 md:h-12 rounded-2xl bg-zinc-900 border border-white/5 flex items-center justify-center shrink-0 overflow-hidden relative group-hover:border-[#FFB800]/30 transition-all duration-300 shadow-[inset_0_0_15px_rgba(0,0,0,0.5)]"
          >
            {#if product.images && product.images.length > 0 && product.images[0].includes('/')}
              <img 
                src={product.images[0]} 
                alt={product.name}
                class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110 opacity-80 group-hover:opacity-100"
              />
            {:else}
              <div class="w-full h-full bg-gradient-to-br from-[#FFB800]/10 to-transparent flex items-center justify-center">
                <Package size={20} class="text-[#FFB800]/40" />
              </div>
            {/if}
            <div class="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent pointer-events-none"></div>
          </div>
          <div class="min-w-0 flex flex-col justify-center flex-1">
            <div class="text-[14px] md:text-[13px] font-bold text-gray-100 truncate group-hover:text-[#FFB800] transition-colors tracking-wide">
              {product.name}
            </div>
            <div class="text-[10px] font-mono text-gray-500 mt-1 uppercase tracking-[0.2em] flex items-center gap-2">
              <span class="px-2 py-0.5 rounded-lg bg-white/5 border border-white/5 text-[8px] text-[#FFB800]/70">{product.category || "General_Node"}</span>
              <span class="md:hidden text-gray-800">/</span>
              <span class="md:hidden text-gray-600 font-bold">{product.sku}</span>
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
          <div class="flex items-center gap-1.5 justify-end md:translate-x-2 md:group-hover:translate-x-0 w-full bg-[#0a0a0a] md:bg-transparent pl-2">
            <a
              href="https://smartshop.test/{product.slug}"
              target="_blank"
              class="p-2 text-[#FFB800] hover:text-white transition-colors rounded-xl md:bg-black/40 bg-white/5 border border-[#FFB800]/20 hover:border-[#FFB800]/40 shadow-sm"
              title="View Landing Page"
              onclick={(e: MouseEvent) => e.stopPropagation()}
            >
              <ExternalLink size={14} />
            </a>
            <button
              onclick={(e: MouseEvent) => { e.stopPropagation(); onEdit(product); }}
              class="p-2 text-gray-400 md:text-gray-500 hover:text-[#00FFFF] transition-colors rounded-xl md:bg-black/40 bg-white/5 border border-transparent hover:border-[#00FFFF]/20 shadow-sm"
              title="Edit Product"
            >
              <Pencil size={14} />
            </button>
            <button
              onclick={(e: MouseEvent) => { e.stopPropagation(); onDelete(product.id); }}
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
