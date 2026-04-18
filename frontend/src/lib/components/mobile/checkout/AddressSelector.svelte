<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, slide, fly } from 'svelte/transition';
  import { MapPin, Search, ChevronRight, Check, X } from 'lucide-svelte';

  interface Ward {
    name: string;
  }

  interface Province {
    id: string;
    name: string;
    code: string;
    wards: string[];
  }

  let { onSelect, value = { province: '', ward: '' } } = $props<{
    onSelect: (data: { province: string, ward: string }) => void;
    value?: { province: string, ward: string };
  }>();

  // State Management (Runes)
  let provinces = $state<Province[]>([]);
  let isLoading = $state(true);
  let step = $state<'province' | 'ward'>('province');
  let searchQuery = $state('');
  let isOpen = $state(false);

  // Derived Values
  const selectedProvince = $derived(provinces.find(p => p.name === value.province));
  
  const filteredProvinces = $derived.by(() => {
    if (!searchQuery) return provinces;
    const query = searchQuery.toLowerCase();
    return provinces.filter(p => p.name.toLowerCase().includes(query));
  });

  const filteredWards = $derived.by(() => {
    if (!selectedProvince) return [];
    if (!searchQuery) return selectedProvince.wards;
    const query = searchQuery.toLowerCase();
    return selectedProvince.wards.filter(w => w.toLowerCase().includes(query));
  });

  onMount(async () => {
    try {
      // Lazy Load Address Data - Corrected path
      const response = await fetch('/resources/vn_divisions.json');
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      // Bỏ qua object hướng dẫn đầu tiên
      provinces = data.slice(1);
      console.log('Elite Address Data Loaded:', provinces.length);
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
        if (value.province) step = 'ward';
    }
  }
</script>

<div class="relative w-full">
  <!-- Trigger Button -->
  <button 
    onclick={toggle}
    class="w-full h-[52px] bg-white/[0.03] border border-white/10 rounded-2xl px-5 flex items-center justify-between transition-all {isOpen ? 'border-[#FFB7C5]/50 ring-2 ring-[#FFB7C5]/10' : ''}"
  >
    <div class="flex items-center gap-3 overflow-hidden">
      <MapPin class="w-4 h-4 {value.province ? 'text-[#FFB7C5]' : 'text-white/20'}" />
      <div class="flex flex-col items-start leading-tight">
        {#if value.province}
          <span class="text-[8px] text-white/40 font-black uppercase tracking-[0.15em]">Khu vực</span>
          <span class="text-white text-[13px] font-bold truncate tracking-tight">
            {value.province}{value.ward ? `, ${value.ward}` : ''}
          </span>
        {:else}
          <span class="text-white/40 text-[13px] font-bold uppercase tracking-wider italic">Chọn Khu Vực *</span>
        {/if}
      </div>
    </div>
    <ChevronRight class="w-4 h-4 text-white/20 transition-transform {isOpen ? 'rotate-90' : ''}" />
  </button>

  <!-- Dropdown Modal (Elite Glass) -->
  {#if isOpen}
    <div 
      class="absolute top-[calc(100%+8px)] left-0 w-full z-[2000] bg-[#121212] border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[400px]"
      transition:slide={{ duration: 300 }}
    >
      <!-- Search Bar -->
      <div class="p-3 border-b border-white/10 flex items-center gap-2 bg-white/[0.02]">
        <Search class="w-4 h-4 text-white/40" />
        <input 
          type="text" 
          bind:value={searchQuery}
          placeholder={step === 'province' ? 'Tìm Tỉnh/Thành phố...' : 'Tìm Phường/Xã...'}
          class="flex-1 bg-transparent border-none outline-none text-white text-[14px] placeholder:text-white/20"
          autofocus
        />
        {#if step === 'ward'}
          <button onclick={reset} class="text-[10px] font-black text-[#FFB7C5] uppercase px-2 hover:opacity-80">Quay lại</button>
        {/if}
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
                class="w-full px-5 py-3.5 flex items-center justify-between text-left hover:bg-[#FFB7C5]/5 transition-colors group"
              >
                <span class="text-[14px] font-semibold {value.province === p.name ? 'text-[#FFB7C5]' : 'text-white/70 group-hover:text-white'}">
                  {p.name}
                </span>
                {#if value.province === p.name}
                  <Check class="w-4 h-4 text-[#FFB7C5]" />
                {:else}
                  <ChevronRight class="w-3.5 h-3.5 text-white/10" />
                {/if}
              </button>
            {/each}
          {:else}
            {#each filteredWards as w}
              <button 
                onclick={() => selectWard(w)}
                class="w-full px-5 py-3.5 flex items-center justify-between text-left hover:bg-[#FFB7C5]/5 transition-colors group"
              >
                <span class="text-[14px] font-semibold {value.ward === w ? 'text-[#FFB7C5]' : 'text-white/70 group-hover:text-white'}">
                  {w}
                </span>
                {#if value.ward === w}
                  <Check class="w-4 h-4 text-[#FFB7C5]" />
                {/if}
              </button>
            {:else}
              <div class="p-8 text-center">
                <span class="text-[12px] text-white/20 italic">Không tìm thấy kết quả nào...</span>
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
