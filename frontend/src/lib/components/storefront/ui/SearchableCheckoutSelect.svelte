<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { onMount, tick } from 'svelte';

  let { 
    value = $bindable(), 
    options = [], 
    placeholder = "Chọn...", 
    disabled = false,
    onChange = () => {},
    getBadge = undefined,
    id = undefined
  } = $props<{
    value: string;
    options: string[];
    placeholder?: string;
    disabled?: boolean;
    onChange?: () => void;
    getBadge?: (opt: string) => { text: string, type: 'success' | 'warning' | 'info' | 'error' | 'default' } | null;
    id?: string;
  }>();

  let open = $state(false);
  let search = $state('');
  let containerRef = $state<HTMLDivElement>();
  let inputRef = $state<HTMLInputElement>();

  const filteredOptions = $derived.by(() => {
    const q = search.toLowerCase().trim();
    if (!q) return options;
    
    // Split search query into individual keywords
    const queryWords = q.split(/\s+/).filter(Boolean);
    const queryNormalizedWords = queryWords.map(w => removeAccents(w));
    
    if (queryWords.length === 0) return options;
    
    const results = options.filter(opt => {
      if (!opt) return false;
      const lowerOpt = opt.toLowerCase();
      const normalizedOpt = removeAccents(lowerOpt);
      
      // All query keywords must match the option text or their abbreviation mappings
      return queryWords.every((qw, idx) => {
        const nqw = queryNormalizedWords[idx];
        
        // 1. Advanced abbreviation mappings for rapid search
        if (qw === 'hcm' || qw === 'tphcm') {
          if (normalizedOpt.includes('ho chi minh') || normalizedOpt.includes('hcm')) return true;
        }
        if (qw === 'hn' || qw === 'tphn') {
          if (normalizedOpt.includes('ha noi') || normalizedOpt.includes('hn')) return true;
        }
        if (qw === 'tp') {
          if (normalizedOpt.includes('thanh pho') || normalizedOpt.includes('tp')) return true;
        }
        if (qw === 'q' || qw === 'q.') {
          if (normalizedOpt.includes('quan') || normalizedOpt.includes('q')) return true;
        }
        if (qw === 'h' || qw === 'h.') {
          if (normalizedOpt.includes('huyen') || normalizedOpt.includes('h')) return true;
        }
        if (qw === 'p' || qw === 'p.') {
          if (normalizedOpt.includes('phuong') || normalizedOpt.includes('p')) return true;
        }
        if (qw === 'x' || qw === 'x.') {
          if (normalizedOpt.includes('xa') || normalizedOpt.includes('x')) return true;
        }
        
        // 2. Fallback to exact or accent-insensitive substring matching
        return lowerOpt.includes(qw) || normalizedOpt.includes(nqw);
      });
    });
    
    return results.slice(0, 50); // [ELITE V2.2] Performance Guard: Limit DOM nodes to 50
  });

  function removeAccents(str: string) {
    if (!str) return '';
    return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D');
  }

  function handleClickOutside(e: MouseEvent) {
    if (containerRef && !containerRef.contains(e.target as Node)) {
      open = false;
    }
  }

  onMount(() => {
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  });

  async function toggle() {
    if (disabled) return;
    open = !open;
    if (open) {
      search = '';
      await tick();
      inputRef?.focus();
    }
  }

  function selectOption(opt: string) {
    value = opt;
    open = false;
    search = '';
    onChange();
  }

  function clearSelection(e: MouseEvent) {
    e.stopPropagation();
    value = '';
    search = '';
    onChange();
  }

  // Effect to close if disabled changes
  $effect(() => {
    if (disabled && open) open = false;
  });
</script>

<div class="relative w-full font-sans" bind:this={containerRef}>
  <!-- Main Display Box -->
  <div class="relative group">
    <button
      {id}
      type="button"
      onclick={toggle}
      class="w-full bg-gray-50 border {open ? 'border-[#ee4d2d] shadow-[0_0_0_1px_#ee4d2d]' : 'border-gray-100'} pl-4 pr-8 py-3 text-sm outline-none font-bold flex items-center justify-between transition-all duration-200 {disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-gray-200'} {value ? 'text-gray-900' : 'text-gray-400'}"
      {disabled}
    >
      <span class="truncate">{value || placeholder}</span>
      <svg 
        class="w-4 h-4 text-gray-400 absolute right-2.5 top-1/2 -translate-y-1/2 transition-transform duration-300 {open ? 'rotate-180 text-[#ee4d2d]' : ''}" 
        fill="none" 
        viewBox="0 0 24 24" 
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    {#if value && !disabled}
      <button
        type="button"
        onclick={clearSelection}
        class="absolute right-7 top-1/2 -translate-y-1/2 p-1 text-gray-300 hover:text-[#ee4d2d] bg-gray-50 transition-colors"
        aria-label="Xóa chọn"
      >
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    {/if}
  </div>

  <!-- Dropdown Menu -->
  {#if open}
    <div 
      class="absolute left-0 right-0 top-[110%] bg-white border border-gray-100 shadow-2xl z-[100] max-h-[320px] flex flex-col overflow-hidden rounded-md"
      in:fly={{ y: 5, duration: 200 }}
      out:fade={{ duration: 150 }}
    >
      <!-- Integrated Search Box -->
      <div class="p-3 border-b border-gray-50 bg-gray-50/50 flex items-center gap-2">
        <svg class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input 
          bind:this={inputRef}
          type="text" 
          bind:value={search} 
          placeholder="Tìm tên tỉnh, huyện, xã..." 
          aria-label="Tìm kiếm tỉnh, quận, huyện hoặc xã"
          class="w-full bg-transparent outline-none text-sm font-bold text-gray-900 placeholder:text-gray-300 placeholder:font-normal"
        />
      </div>

      <!-- Options List -->
      <div class="overflow-y-auto flex-1 custom-scrollbar">
        {#if filteredOptions.length === 0}
          <div class="p-6 text-center text-xs text-gray-400 italic">Không tìm thấy kết quả nào...</div>
        {:else}
          {#each filteredOptions as opt}
            <button
              type="button"
              class="w-full px-4 py-3 text-left text-sm font-bold transition-all flex items-center justify-between group {value === opt ? 'bg-[#fff4f1] text-[#ee4d2d]' : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'}"
              onclick={() => selectOption(opt)}
            >
              <div class="flex items-center gap-2 flex-1 min-w-0">
                <span class="truncate">{opt}</span>
                {#if getBadge && getBadge(opt)}
                  {@const badge = getBadge(opt)}
                  <span class="px-1.5 py-0.5 text-[8px] font-black tracking-tighter rounded-sm {badge.type === 'success' ? 'bg-emerald-50 text-emerald-600 border border-emerald-100' : 'bg-gray-50 text-gray-400 border border-gray-100'}">
                    {badge.text}
                  </span>
                {/if}
              </div>
              {#if value === opt}
                <svg class="w-4 h-4 text-[#ee4d2d]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              {/if}
            </button>
          {/each}
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar { width: 4px; }
  .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
  .custom-scrollbar::-webkit-scrollbar-thumb { background: #eee; border-radius: 10px; }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #ddd; }
</style>
