<script lang="ts">
  import { goto } from '$app/navigation';
  import { slugify } from '$lib/utils/format';

  interface Props {
    categories: Array<{ id: string; name: string; slug: string; image?: string; icon?: string }>;
  }
  let { categories }: Props = $props();
</script>

<div class="w-full pt-[15px] pb-6 overflow-hidden">
  <div class="flex flex-wrap justify-start items-start gap-x-8 md:gap-x-12 gap-y-8 px-2 md:px-0">
    {#each categories as category (category.id)}
      <button
        onclick={() => goto(`/${category.slug || slugify(category.name)}/`)}
        class="flex flex-col items-center justify-start w-[85px] md:w-[100px] cursor-pointer group outline-none"
      >
        <!-- Elite Squircle Icon Container (Viral 2026) -->
        <div class="w-[50px] h-[50px] md:w-[60px] md:h-[60px] bg-white rounded-[20px] md:rounded-[24px] flex items-center justify-center border border-gray-100 shadow-[0_4px_20px_rgba(0,0,0,0.04)] transition-all duration-500 group-hover:-translate-y-2 group-hover:shadow-[0_12px_30px_rgba(193,143,126,0.15)] group-hover:border-[#C18F7E]/20 shrink-0 overflow-hidden relative">
          {#if category.image}
            <img 
              src={category.image} 
              alt={category.name} 
              class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" 
            />
          {:else}
            <div class="text-2xl md:text-3xl transition-transform duration-700 group-hover:scale-110 select-none opacity-80 group-hover:opacity-100">
              {category.icon || '✨'}
            </div>
          {/if}
          
          <!-- Liquid Glow Overlay -->
          <div class="absolute inset-0 bg-gradient-to-tr from-[#C18F7E]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
        </div>
        
        <!-- Premium Typography -->
        <span class="mt-4 text-[11px] md:text-[13px] font-bold text-gray-600 text-center leading-snug transition-colors duration-300 group-hover:text-[#C18F7E] w-full line-clamp-2 px-1 tracking-tight">
          {category.name}
        </span>
      </button>
    {/each}
  </div>
</div>
