<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, slide, fly } from 'svelte/transition';
  import MapPin from "@lucide/svelte/icons/map-pin";
  import Search from "@lucide/svelte/icons/search";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import Check from "@lucide/svelte/icons/check";
  import X from "@lucide/svelte/icons/x";

  interface Ward {
    name: string;
  }

  interface Province {
    id: string;
    name: string;
    code: string;
    wards: string[];
  }

  let { onSelect, value = { province: '', ward: '' }, light = false } = $props<{
    onSelect: (data: { province: string, ward: string }) => void;
    value?: { province: string, ward: string };
    light?: boolean;
  }>();

  // State Management (Runes)
  let provinces = $state<Province[]>([]);
  let isLoading = $state(true);
  let step = $state<'province' | 'ward'>('province');
  let searchQuery = $state('');
  let isOpen = $state(false);

  // Derived Values
  const selectedProvince = $derived(provinces.find(p => p.name === value.province));
  
  function normalize(str: string) {
    return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase();
  }

  const filteredProvinces = $derived.by(() => {
    let query = normalize(searchQuery);
    if (query === 'hcm') query = 'ho chi minh';
    if (query === 'hn') query = 'ha noi';
    if (!query) return provinces;
    
    return provinces.filter(p => {
        const normalizedP = normalize(p.name);
        return normalizedP.includes(query);
    });
  });

  const filteredWards = $derived.by(() => {
    if (!selectedProvince) return [];
    let query = normalize(searchQuery);
    if (!query) return selectedProvince.wards;
    
    return selectedProvince.wards.filter(w => normalize(w).includes(query));
  });

  onMount(async () => {
    try {
      // Lazy Load Address Data - Corrected path
      const response = await fetch('/resources/vn_divisions.json');
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      // Bỏ qua object hướng dẫn đầu tiên
      provinces = data.slice(1);
    } catch (e) {
      console.error('Failed to load address data', e);
      isLoading = false;
    } finally {
      isLoading = false;
    }
  });

  function selectProvince(p: Province) {
    onSelect({ province: p.name, ward: '' });
    step = 'ward';
    searchQuery = '';
  }

  function selectWard(w: string) {
    onSelect({ ...value, ward: w });
    isOpen = false;
    searchQuery = '';
  }

  function reset() {
    step = 'province';
    searchQuery = '';
  }

  function toggle() {
    isOpen = !isOpen;
    if (isOpen) {
        searchQuery = '';
        step = 'province'; // Elite V2.2: Always start from province for zero-friction re-selection
    }
  }
</script>

<div class="relative w-full">
  <!-- Trigger Button -->
  <button 
    onclick={toggle}
    class="w-full h-[52px] rounded-2xl px-5 flex items-center justify-between transition-all {light ? 'bg-slate-100/50 border-slate-200 text-slate-900' : 'bg-white/[0.03] border-white/10 text-white'} border {isOpen ? (light ? 'border-sky-500 ring-2 ring-sky-500/10' : 'border-[#FFB7C5]/50 ring-2 ring-[#FFB7C5]/10') : ''}"
  >
    <div class="flex items-center gap-3 overflow-hidden">
      <MapPin class="w-4 h-4 {value.province ? (light ? 'text-sky-500' : 'text-[#FFB7C5]') : (light ? 'text-slate-300' : 'text-white/20')}" />
      <div class="flex flex-col items-start leading-tight">
        {#if value.province}
          <span class="text-[8px] {light ? 'text-slate-400' : 'text-white/40'} font-black uppercase tracking-[0.15em]">Khu vực</span>
          <span class="{light ? 'text-slate-900' : 'text-white'} text-[13px] font-bold truncate tracking-tight">
            {value.province}{value.ward ? `, ${value.ward}` : ''}
          </span>
        {:else}
          <span class="{light ? 'text-slate-400' : 'text-white/40'} text-[13px] font-bold uppercase tracking-wider italic">Chọn Khu Vực *</span>
        {/if}
      </div>
    </div>
    <ChevronRight class="w-4 h-4 {light ? 'text-slate-300' : 'text-white/20'} transition-transform {isOpen ? 'rotate-90' : ''}" />
  </button>

  <!-- Dropdown Modal (Elite Glass) -->
  {#if isOpen}
    <div 
      class="absolute top-[calc(100%+8px)] left-0 w-full z-[2000] border rounded-2xl shadow-[0_40px_100px_rgba(0,0,0,1)] overflow-hidden flex flex-col max-h-[400px] {light ? 'bg-white border-slate-200' : 'bg-[#030303] border-white/20'}"
      transition:slide={{ duration: 300 }}
      onmouseleave={() => isOpen = false}
    >
      <!-- Search Bar & Close -->
      <div class="p-3 border-b flex items-center gap-2 {light ? 'bg-slate-50 border-slate-100' : 'bg-white/[0.03] border-white/10'}">
        <Search class="w-4 h-4 {light ? 'text-slate-500' : 'text-[#FFB7C5]'}" />
        <input 
          type="text" 
          bind:value={searchQuery}
          placeholder={step === 'province' ? 'TÌM TỈNH/THÀNH...' : 'TÌM PHƯỜNG/XÃ...'}
          class="flex-1 bg-transparent border-none outline-none text-[12px] font-black uppercase tracking-wider {light ? 'text-slate-900 placeholder:text-slate-300' : 'text-white placeholder:text-white/10'}"
          autofocus
        />
        <div class="flex items-center gap-1">
          {#if step === 'ward'}
            <button onclick={reset} class="text-[10px] font-black {light ? 'text-sky-600' : 'text-[#FFB7C5]'} uppercase px-2 py-1 bg-white/5 rounded-lg hover:opacity-80">Quay lại</button>
          {/if}
          <button onclick={() => isOpen = false} class="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-white/20 hover:text-white transition-all">
            <X class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- List Container -->
      <div class="flex-1 overflow-y-auto no-scrollbar py-2">
        {#if isLoading}
          <div class="p-8 flex flex-col items-center justify-center gap-3">
             <div class="w-6 h-6 border-2 border-[#FFB7C5]/20 border-t-[#FFB7C5] rounded-full animate-spin"></div>
             <span class="text-[10px] text-white/40 uppercase font-black tracking-widest">Đang tải dữ liệu...</span>
          </div>
        {:else}
          {#if step === 'province'}
            {#each filteredProvinces as p}
              <button 
                onclick={() => selectProvince(p)}
                class="w-full px-5 py-3.5 flex items-center justify-between text-left transition-colors group {light ? 'hover:bg-slate-50' : 'hover:bg-[#FFB7C5]/5'}"
              >
                <span class="text-[14px] font-semibold {value.province === p.name ? (light ? 'text-sky-500' : 'text-[#FFB7C5]') : (light ? 'text-slate-600 group-hover:text-slate-900' : 'text-white/70 group-hover:text-white')}">
                  {p.name}
                </span>
                {#if value.province === p.name}
                  <Check class="w-4 h-4 {light ? 'text-sky-500' : 'text-[#FFB7C5]'}" />
                {:else}
                  <ChevronRight class="w-3.5 h-3.5 {light ? 'text-slate-200' : 'text-white/10'}" />
                {/if}
              </button>
            {/each}
          {:else}
            {#each filteredWards as w}
              <button 
                onclick={() => selectWard(w)}
                class="w-full px-5 py-3.5 flex items-center justify-between text-left transition-colors group {light ? 'hover:bg-slate-50' : 'hover:bg-[#FFB7C5]/5'}"
              >
                <span class="text-[14px] font-semibold {value.ward === w ? (light ? 'text-sky-500' : 'text-[#FFB7C5]') : (light ? 'text-slate-600 group-hover:text-slate-900' : 'text-white/70 group-hover:text-white')}">
                  {w}
                </span>
                {#if value.ward === w}
                  <Check class="w-4 h-4 {light ? 'text-sky-500' : 'text-[#FFB7C5]'}" />
                {/if}
              </button>
            {:else}
              <div class="p-8 text-center">
                <span class="text-[12px] {light ? 'text-slate-400' : 'text-white/20'} italic">Không tìm thấy kết quả nào...</span>
              </div>
            {/each}
          {/if}
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .no-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .no-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
</style>
