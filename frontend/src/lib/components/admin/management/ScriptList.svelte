<script lang="ts">
  import Search from "@lucide/svelte/icons/search";
  import Plus from "@lucide/svelte/icons/plus";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Video from "@lucide/svelte/icons/video";
  import ShoppingBag from "@lucide/svelte/icons/shopping-bag";
  import Clock from "@lucide/svelte/icons/clock";
  import OrderPagination from "./OrderPagination.svelte";
  import type { VideoScript } from "$lib/types";

  interface Props {
    scripts: VideoScript[];
    isLoading: boolean;
    selectedScriptId: string | null;
    searchInput: string;
    currentPage: number;
    pageSize: number;
    totalScripts: number;
    totalPages: number;
    onSearchInput: (e: Event) => void;
    onRefresh: () => void;
    onOpenDrawer: () => void;
  }

  let {
    scripts,
    isLoading,
    selectedScriptId = $bindable(),
    searchInput = $bindable(),
    currentPage = $bindable(),
    pageSize,
    totalScripts,
    totalPages,
    onSearchInput,
    onRefresh,
    onOpenDrawer
  }: Props = $props();
</script>

<!-- LEFT COLUMN: Scripts List & Filters -->
<div class="w-full md:w-[360px] shrink-0 border-r border-[#151515] flex flex-col h-full bg-[#050505]">
  
  <!-- Header Toolbar -->
  <div class="p-4 border-b border-[#151515] flex items-center justify-between gap-3 bg-[#080808]">
    <div class="relative flex-1">
      <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500" />
      <input
        type="text"
        placeholder="Tìm kịch bản..."
        class="w-full bg-[#111] border border-gray-800 rounded-md pl-9 pr-4 py-1.5 text-xs text-cyan-100 placeholder:text-gray-600 focus:outline-none focus:border-cyan-500/40 focus:bg-[#151515] transition-all"
        bind:value={searchInput}
        oninput={onSearchInput}
      />
    </div>
    
    <button
      onclick={onRefresh}
      class="p-2 bg-[#111] hover:bg-[#1a1a1a] border border-gray-800 rounded-md text-gray-400 hover:text-cyan-400 transition-colors"
      title="Tải lại danh sách"
    >
      <RefreshCw class="w-3.5 h-3.5" />
    </button>

    <button
      onclick={onOpenDrawer}
      class="flex items-center gap-1 px-3 py-1.5 bg-gradient-to-r from-pink-500 to-cyan-500 text-black text-xs font-semibold rounded-md hover:opacity-90 shadow-md shadow-cyan-500/10 transition-all shrink-0"
    >
      <Plus class="w-3.5 h-3.5 stroke-[3]" />
      <span>Tạo mới</span>
    </button>
  </div>

  <!-- Scripts Bento List -->
  <div class="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-2">
    {#if isLoading}
      <div class="h-full flex flex-col items-center justify-center gap-3 py-12">
        <div class="w-8 h-8 border-2 border-cyan-500/10 border-t-cyan-400 rounded-full animate-spin"></div>
        <span class="text-[10px] font-mono text-cyan-400/50 tracking-wider">LOADING_SCRIPTS...</span>
      </div>
    {:else}
      {@const scriptsList = scripts}
      {#if scriptsList.length === 0}
        <div class="h-full flex flex-col items-center justify-center gap-3 text-gray-600 py-16">
          <Video class="w-10 h-10 opacity-20" />
          <span class="text-[10px] font-mono tracking-widest uppercase">Chưa có kịch bản nào</span>
        </div>
      {:else}
        {#each scriptsList as script (script.id)}
          <!-- svelte-ignore a11y_click_events_have_key_events -->
          <!-- svelte-ignore a11y_no_static_element_interactions -->
          <div
            onclick={() => { selectedScriptId = script.id; }}
            class="group relative p-3 rounded-lg border transition-all cursor-pointer select-none
                   {selectedScriptId === script.id 
                     ? 'bg-cyan-950/20 border-cyan-500/40 shadow-sm shadow-cyan-500/5' 
                     : 'bg-[#0b0b0b] border-[#151515] hover:border-gray-800'}"
          >
            {#if selectedScriptId === script.id}
              <div class="absolute left-0 top-0 bottom-0 w-[3px] bg-cyan-500 rounded-l-md"></div>
            {/if}

            <div class="flex items-start justify-between gap-2">
              <h3 class="text-xs font-medium text-gray-200 line-clamp-2 leading-relaxed transition-colors group-hover:text-cyan-300">
                {script.title}
              </h3>
              
              <span class="text-[9px] px-1.5 py-0.5 rounded shrink-0 font-bold border tracking-wider
                           {script.style_platform === 'TikTok' 
                             ? 'bg-black text-white border-white/20' 
                             : 'bg-red-950/20 text-red-400 border-red-500/20'}">
                {script.style_platform || "Video"}
              </span>
            </div>

            <div class="mt-2.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px] text-gray-500">
              <span class="flex items-center gap-1">
                <ShoppingBag class="w-3 h-3 text-pink-500/50" />
                <span class="truncate max-w-[100px]">{script.product_name || "Sản phẩm"}</span>
              </span>
              <span class="flex items-center gap-1">
                <Clock class="w-3 h-3 text-cyan-500/50" />
                <span>{script.structured_script?.total_duration || 0}s</span>
              </span>
              <span class="ml-auto text-gray-600 text-[9px] font-mono">
                {new Date(script.created_at).toLocaleDateString("vi-VN")}
              </span>
            </div>
          </div>
        {/each}
      {/if}
    {/if}
  </div>

  <!-- Pagination footer -->
  <div class="border-t border-[#151515] bg-[#070707] shrink-0">
    <OrderPagination
      bind:currentPage={currentPage}
      totalPages={totalPages}
      pageSize={pageSize}
      totalItems={totalScripts}
    />
  </div>
</div>
