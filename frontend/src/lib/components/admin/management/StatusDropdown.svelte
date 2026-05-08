<script lang="ts">
  import { fade, fly } from "svelte/transition";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import Activity from "@lucide/svelte/icons/activity";
  import Command from "@lucide/svelte/icons/command";
  import { ORDER_STATUS_MAP } from "$lib/constants/order";
  import { portal } from "$lib/core/actions/portal";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";

  let { 
    currentStatus = "", 
    options = [], 
    placeholder = "SELECT_ACTION",
    label = "",
    color = "text-gray-400",
    border = "border-white/10",
    onSelect,
    variant = "item", // "item" | "badge" | "bulk"
    actions = [], // { label: string, value: string, icon: any, color?: string }
    statusMap = ORDER_STATUS_MAP
  } = $props<{
    currentStatus?: string;
    options: string[];
    placeholder?: string;
    label?: string;
    color?: string;
    border?: string;
    onSelect: (value: string) => void;
    variant?: "item" | "badge" | "bulk";
    actions?: Array<{ label: string; value: string; icon: import('svelte').Component; color?: string }>;
    statusMap?: Record<string, { label: string; color: string; border: string }>;
  }>();

  let isOpen = $state<boolean>(false);
  let dropdownPos = $state<{ top: number; left: number; width: number; bottom: number }>({ top: 0, left: 0, width: 0, bottom: 0 });
  let isUpward = $state<boolean>(false);

  function toggle(e: MouseEvent) {
    e.stopPropagation();
    if (isOpen) {
      isOpen = false;
      return;
    }
    
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    
    // CNS V82.22: Dynamic Height Approximation for Flip Logic (Anti-Hardcode)
    const baseHeight = 100; // Header(45px) + Footer(35px) + Padding(20px)
    const verticalUnit = 38; // px per item (optimized for current design)
    const estimatedHeight = baseHeight + (options.length * verticalUnit) + (actions.length * verticalUnit);
    
    isUpward = (rect.bottom + estimatedHeight > viewportHeight) && (rect.top > estimatedHeight);

    dropdownPos = {
      top: isUpward ? 0 : rect.bottom + 4,
      bottom: isUpward ? (viewportHeight - rect.top) + 4 : 0,
      left: rect.left,
      width: rect.width
    };
    isOpen = true;
  }

  function handleSelect(value: string) {
    onSelect(value);
    isOpen = false;
  }

  function handleOutsideClick(e: MouseEvent) {
    if (isOpen) isOpen = false;
  }
</script>

<svelte:window onclick={handleOutsideClick} onscroll={handleOutsideClick} />

<div class="relative inline-block {variant === 'badge' ? '' : 'w-full'}">
  {#if variant === "badge"}
    <!-- Badge Style Trigger (V3) -->
    <button
      onclick={toggle}
      class="flex items-center gap-2.5 px-3 py-1.5 bg-black border {border}/40 hover:border-neon-cyan/60 transition-all duration-300 group {isOpen ? 'ring-1 ring-neon-cyan/20 border-neon-cyan' : ''}"
    >
      <span class="w-1.5 h-1.5 {color.replace('text-', 'bg-')} {isOpen ? 'animate-ping' : ''}"></span>
      <span class="text-[9px] font-mono font-black tracking-[0.2em] uppercase {color}">
        {label || statusMap[currentStatus]?.label || statusMap[currentStatus.toLowerCase()]?.label || currentStatus}
      </span>
      <div class="w-px h-3 bg-white/10 mx-0.5"></div>
      <ChevronDown size={10} class="text-gray-500 transition-transform duration-500 {isOpen ? 'rotate-180 text-neon-cyan' : 'group-hover:text-neon-cyan'}" />
    </button>
  {:else}
    <!-- Standard Action Trigger -->
    <button
      onclick={toggle}
      class="flex items-center justify-between gap-3 w-full px-4 h-10 bg-black/40 hover:bg-white/[0.05] border border-white/10 hover:border-neon-cyan/50 transition-all duration-300 group {isOpen ? 'border-neon-cyan' : ''}"
    >
      <div class="flex items-center gap-2 overflow-hidden">
        <Activity size={10} class="{isOpen ? 'text-neon-cyan animate-pulse' : 'text-gray-600'}" />
        <span class="text-[10px] font-mono uppercase tracking-[0.15em] truncate {isOpen ? 'text-white font-black' : 'text-neon-cyan/80 font-bold'}">
          {label || statusMap[currentStatus]?.label || currentStatus || placeholder}
        </span>
      </div>
      <ChevronDown size={12} class="text-gray-500 transition-all duration-500 {isOpen ? 'rotate-180 text-neon-cyan' : 'group-hover:text-neon-cyan'}" />
    </button>
  {/if}

  {#if isOpen}
    <div 
      use:portal
      in:fly={{ y: isUpward ? 12 : -12, duration: 400, opacity: 0 }}
      out:fade={{ duration: 200 }}
      class="fixed bg-[#0d0d0d] flex flex-col max-h-[400px] overflow-hidden"
      style="{isUpward ? `bottom: ${dropdownPos.bottom}px` : `top: ${dropdownPos.top}px`}; left: {dropdownPos.left}px; width: {dropdownPos.width}px; z-index: {Z_INDEX_ADMIN.POPOVER};"
    >
      
      <div class="px-1 py-1 overflow-y-auto custom-scrollbar flex-1">
        <div class="flex flex-col">
          {#if options.length === 0}
            <div class="px-3 py-2 text-[8px] font-mono text-gray-700 italic uppercase bg-black/20">End_Of_Life_Cycle</div>
          {:else}
            {#each options as statusKey, i}
              {@const val = statusMap[statusKey]}
              <button
                onclick={() => handleSelect(statusKey)}
                class="flex items-center gap-3 w-full px-3 py-2 hover:bg-neon-cyan/10 text-left transition-all group/opt border border-transparent hover:border-neon-cyan/20"
              >
                <div class="w-1 h-1 {val?.color ? val.color.replace('text-', 'bg-') : 'bg-gray-500'}"></div>
                <span class="text-[9px] font-mono font-bold tracking-wider uppercase {val?.color || 'text-gray-400'} group-hover/opt:text-white">
                  {val?.label || statusKey}
                </span>
              </button>
            {/each}
          {/if}
        </div>
      </div>

      {#if actions.length > 0}
        <div class="px-1 pb-1 border-t border-white/5">
          <div class="flex flex-col">
            {#each actions as action, i}
              <button
                onclick={() => handleSelect(action.value)}
                class="flex items-center gap-3 w-full px-3 py-1.5 hover:bg-white/5 transition-all group/util border border-transparent hover:border-white/10"
              >
                <div class="text-gray-500 group-hover/util:text-white">
                  <action.icon size={12} fill={action.value === "TOGGLE_SPAM" ? "currentColor" : "none"} />
                </div>
                <span class="text-[8px] font-mono {action.color || 'text-gray-400'} group-hover/util:text-white uppercase tracking-tight">
                  {action.label}
                </span>
              </button>
            {/each}
          </div>
        </div>
      {/if}

    </div>
  {/if}
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 2px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(0, 255, 255, 0.1);
    border-radius: 10px;
  }
  button {
    cursor: pointer;
    user-select: none;
    outline: none;
  }
</style>
