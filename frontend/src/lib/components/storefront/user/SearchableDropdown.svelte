<script lang="ts">
  import { ChevronDown, Search, Check } from 'lucide-svelte';
  import { fade, fly } from 'svelte/transition';
  import { onMount } from 'svelte';

  let { 
    value = $bindable(), 
    options = [], 
    placeholder = "Chọn...", 
    disabled = false,
    onChange = () => {},
    getBadge
  } = $props<{
    value: string;
    options: string[];
    placeholder?: string;
    disabled?: boolean;
    onChange?: () => void;
    getBadge?: (opt: string) => { text: string, type: 'success' | 'warning' | 'info' | 'error' | 'default' } | null;
  }>();

  let open = $state(false);
  let search = $state('');
  let dropdownRef = $state<HTMLDivElement>();

  const filteredOptions = $derived(
    options.filter(opt => opt && opt.toLowerCase().includes(search.toLowerCase()))
  );

  function handleClickOutside(event: MouseEvent) {
    if (dropdownRef && !dropdownRef.contains(event.target as Node)) {
      open = false;
    }
  }

  onMount(() => {
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  });

  function selectOption(opt: string) {
    value = opt;
    open = false;
    search = '';
    onChange();
  }
</script>

<div class="relative" bind:this={dropdownRef}>
  <!-- Dropdown Trigger -->
  <button
    type="button"
    class="w-full h-11 border-b border-stone-200 bg-transparent outline-none flex items-center justify-between text-left transition-colors {disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-luxury-copper'} {value ? 'text-stone-800' : 'text-stone-400'}"
    {disabled}
    onclick={() => !disabled && (open = !open)}
  >
    <span class="truncate">{value || placeholder}</span>
    <ChevronDown class="w-4 h-4 text-stone-400 transition-transform duration-300 {open ? 'rotate-180' : ''}" />
  </button>

  <!-- Dropdown Menu -->
  {#if open}
    <div 
      class="absolute left-0 top-[calc(100%+4px)] w-full bg-white border border-stone-200 shadow-xl z-50 rounded-sm overflow-hidden"
      in:fly={{ y: -5, duration: 200 }}
      out:fade={{ duration: 150 }}
    >
      <!-- Search Box -->
      <div class="p-2 border-b border-stone-100 flex items-center bg-stone-50">
        <Search class="w-3.5 h-3.5 text-stone-400 mr-2 shrink-0" />
        <input 
          type="text" 
          bind:value={search} 
          placeholder="Tìm kiếm..." 
          class="w-full bg-transparent outline-none text-[13px] text-stone-800 placeholder:text-stone-400"
          autofocus
        />
      </div>

      <!-- Options -->
      <div class="max-h-60 overflow-y-auto overscroll-contain">
        {#if filteredOptions.length === 0}
          <div class="p-4 text-center text-[12px] text-stone-400 italic">Không tìm thấy kết quả.</div>
        {:else}
          {#each filteredOptions as opt}
            <button
              type="button"
              class="w-full px-4 py-2.5 text-left text-[13px] hover:bg-stone-50 transition-colors flex items-center justify-between group {value === opt ? 'bg-stone-50/80 text-luxury-copper font-bold' : 'text-stone-700'}"
              onclick={() => selectOption(opt)}
            >
              <div class="flex items-center gap-2 flex-1 min-w-0">
                <span class="truncate">{opt}</span>
                {#if getBadge && getBadge(opt)}
                  {@const badge = getBadge(opt)}
                  <span class="px-1.5 py-0.5 text-[8px] font-black uppercase tracking-tighter rounded-sm {badge.type === 'success' ? 'bg-emerald-50 text-emerald-600 border border-emerald-100' : 'bg-stone-100 text-stone-400 border border-stone-200'}">
                    {badge.text}
                  </span>
                {/if}
              </div>
              {#if value === opt}
                <Check class="w-3.5 h-3.5 text-luxury-copper" />
              {/if}
            </button>
          {/each}
        {/if}
      </div>
    </div>
  {/if}
</div>
