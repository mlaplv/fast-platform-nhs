<script lang="ts">
  import Gift from "@lucide/svelte/icons/gift";
  import Clock from "@lucide/svelte/icons/clock";
  import Check from "@lucide/svelte/icons/check";
  import Tag from "@lucide/svelte/icons/tag";
  import Percent from "@lucide/svelte/icons/percent";
  import Truck from "@lucide/svelte/icons/truck";
  import Calendar from "@lucide/svelte/icons/calendar";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Edit from "@lucide/svelte/icons/edit";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import { formatCurrency, formatDate, timeAgo } from "$lib/utils/format";
  
  export interface Voucher {
    id: string;
    type: string;
    title?: string;
    subtitle?: string;
    value: number;
    min_spend: number;
    max_discount?: number | null;
    usage_limit?: number | null;
    used_count: number;
    start_date?: string | null;
    end_date?: string | null;
    is_active: boolean;
    category: string;
    is_default: boolean;
    priority: number;
    created_at: string;
  }

  interface VoucherListItemProps {
    voucher: Voucher;
    isSelected?: boolean;
    onOpenDetail: (id: string) => void;
    onDelete: (id: string) => void;
    onToggleSelect: (id: string) => void;
    onSetDefault?: (id: string) => void;
  }

  let props = $props<VoucherListItemProps>();

  function getVoucherIcon() {
    if (props.voucher.type === "PERCENT") return Percent;
    if (props.voucher.type === "SHIPPING") return Truck;
    return Tag;
  }

  const Icon = $derived(getVoucherIcon());
</script>

<div
  role="button"
  tabindex="0"
  onclick={() => props.onOpenDetail?.(props.voucher.id)}
  onkeydown={(e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      props.onOpenDetail?.(props.voucher.id);
    }
  }}
  class="voucher-item group flex flex-col sm:flex-row items-stretch sm:items-center gap-4 sm:gap-6 w-full {props.isSelected ? 'border-neon-cyan/50 bg-neon-cyan/[0.03]' : ''} {!props.voucher.is_active ? 'opacity-60 grayscale-[0.5]' : ''}"
>
  <div class="flex items-start sm:items-center gap-4 w-full">
    <!-- Selection Checkbox -->
    <div 
      class="shrink-0 flex items-center justify-center w-6 h-6 grayscale hover:grayscale-0 transition-all"
      onclick={(e) => { e.stopPropagation(); props.onToggleSelect?.(props.voucher.id); }}
      onkeydown={(e) => { if (e.key === ' ') { e.stopPropagation(); props.onToggleSelect?.(props.voucher.id); } }}
      role="checkbox"
      aria-checked={props.isSelected}
      tabindex="0"
    >
      <div class="w-4 h-4 rounded border-2 transition-all flex items-center justify-center
        {props.isSelected ? 'bg-neon-cyan border-neon-cyan' : 'bg-transparent border-white/20 group-hover:border-white/40'}">
        {#if props.isSelected}
          <Check size={12} strokeWidth={4} class="text-black" />
        {/if}
      </div>
    </div>

    <!-- Avatar / Icon (TikTok Style Viral Gift) -->
    <div
      class="w-10 h-10 sm:w-12 sm:h-12 rounded bg-black border border-white/5 flex items-center justify-center shrink-0 relative overflow-hidden group-hover:border-neon-cyan/30 transition-colors"
    >
      <div class="absolute inset-0 bg-gradient-to-br from-neon-cyan/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
      <Gift size={20} class="text-neon-cyan group-hover:scale-110 transition-transform duration-500" />
    </div>

    <!-- Core Data -->
    <div class="flex-1 min-w-0 flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 xl:gap-8">
      <!-- Identity & Code -->
      <div class="min-w-[150px] flex flex-col gap-1">
        <div class="text-[9px] font-mono text-gray-500 uppercase tracking-[0.3em] flex items-center gap-2">
          <span>CODE_ID</span>
          {#if !props.voucher.is_active}
             <span class="px-1.5 py-0.5 rounded-sm bg-red-500/10 text-red-400 border border-red-500/20 text-[7px] font-bold">INACTIVE</span>
          {/if}
        </div>
        <div class="text-[15px] font-black text-white tracking-widest uppercase group-hover:text-neon-cyan transition-colors flex items-center gap-3">
          {props.voucher.title || props.voucher.id}
          
          {#if props.voucher.title}
            <span class="text-[10px] text-gray-500 font-mono lowercase tracking-tighter">
              <span class="opacity-30">CODE:</span> {props.voucher.id}
            </span>
          {/if}
          
          <!-- Elite V2.2: AUTO-STICK Badge -->
          {#if props.voucher.is_default}
            <div 
              class="flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-500 text-black text-[8px] font-black tracking-widest animate-pulse shadow-[0_0_15px_rgba(16,185,129,0.6)]"
              title="Automatically applied in Checkout"
            >
              <Sparkles size={8} />
              AUTO-STICK
            </div>
          {:else}
            <button
              onclick={(e) => { e.stopPropagation(); props.onSetDefault?.(props.voucher.id); }}
              class="px-2 py-0.5 rounded border border-white/10 hover:border-emerald-500/50 hover:bg-emerald-500/10 text-gray-600 hover:text-emerald-400 transition-all text-[8px] font-mono uppercase tracking-tighter"
            >
              Set_Default
            </button>
          {/if}
        </div>
        <div class="flex items-center gap-2 text-[10px] text-gray-500 font-mono italic">
          {#if props.voucher.subtitle}
             <span class="text-emerald-400/80 font-bold mr-2">« {props.voucher.subtitle} »</span>
          {/if}
          <Icon size={10} class="text-neon-cyan/60" />
          <span class="text-neon-cyan/80 font-bold">{props.voucher.category}</span>
          <span class="text-white/20">|</span>
          <span>{props.voucher.type}</span>
          {#if props.voucher.priority > 0}
            <span class="text-white/20">|</span>
            <span class="text-amber-400/80">P{props.voucher.priority}</span>
          {/if}
        </div>
      </div>

      <!-- Discount Value -->
      <div class="min-w-[120px]">
        <div class="text-[9px] font-mono text-gray-500 uppercase tracking-widest mb-1">Benefit</div>
        <div class="text-[14px] font-bold text-emerald-400 flex items-center gap-1.5">
          {#if props.voucher.type === 'PERCENT'}
            <span class="bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">-{props.voucher.value}%</span>
          {:else}
            <span class="bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">-{formatCurrency(props.voucher.value)}</span>
          {/if}
        </div>
      </div>

      <!-- Usage Stats -->
      <div class="min-w-[100px]">
        <div class="text-[9px] font-mono text-gray-500 uppercase tracking-widest mb-1">Consumption</div>
        <div class="flex flex-col gap-1">
          <div class="flex items-center justify-between text-[10px] font-mono">
            <span class="text-neon-cyan font-bold">{props.voucher.used_count}</span>
            <span class="text-white/20">/</span>
            <span class="text-gray-400">{props.voucher.usage_limit || '∞'}</span>
          </div>
          <div class="w-full h-1 bg-white/5 rounded-full overflow-hidden">
            <div 
              class="h-full bg-neon-cyan shadow-[0_0_8px_rgba(0,243,255,0.5)]" 
              style:width="{props.voucher.usage_limit ? (props.voucher.used_count / props.voucher.usage_limit * 100) : 0}%"
            ></div>
          </div>
        </div>
      </div>

      <!-- Dates -->
      <div class="hidden xl:flex flex-col gap-1.5 min-w-[180px] border-l border-white/5 pl-6 font-mono">
        <div class="flex items-center gap-2 text-[10px] text-gray-400">
           <Calendar size={10} />
           <span>{props.voucher.start_date ? formatDate(props.voucher.start_date) : 'NOW'}</span>
           <span class="text-white/20">→</span>
           <span>{props.voucher.end_date ? formatDate(props.voucher.end_date) : 'EVER'}</span>
        </div>
        <div class="flex items-center gap-2 text-[9px] text-gray-600">
          <Clock size={10} />
          <span>Added {timeAgo(props.voucher.created_at)}</span>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex items-center gap-2 ml-auto">
      <button 
        onclick={(e) => { e.stopPropagation(); props.onOpenDetail?.(props.voucher.id); }}
        class="w-8 h-8 rounded border border-white/10 bg-white/5 flex items-center justify-center hover:bg-neon-cyan hover:text-black transition-all"
      >
        <Edit size={14} />
      </button>
      <button 
        onclick={(e) => { e.stopPropagation(); props.onDelete?.(props.voucher.id); }}
        class="w-8 h-8 rounded border border-rose-500/20 bg-rose-500/5 text-rose-400 flex items-center justify-center hover:bg-rose-500 hover:text-white transition-all"
      >
        <Trash2 size={14} />
      </button>
    </div>
  </div>
</div>

<style>
  .voucher-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem;
    background: #0a0a0a;
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 0.75rem;
    text-align: left;
    width: 100%;
    cursor: pointer;
    will-change: background-color;
  }
  @media (min-width: 640px) {
    .voucher-item {
      padding: 1.25rem;
    }
  }
  .voucher-item:hover {
    background: rgba(255, 255, 255, 0.03);
    border-color: rgba(0, 243, 255, 0.2);
  }
</style>
