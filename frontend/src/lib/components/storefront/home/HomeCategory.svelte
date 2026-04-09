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
        <!-- Modern Squircle Icon Container -->
        <div class="w-[50px] h-[50px] md:w-[56px] md:h-[56px] bg-white rounded-[18px] md:rounded-[22px] flex items-center justify-center border border-gray-100/80 shadow-[0_4px_12px_rgba(0,0,0,0.03),0_1px_2px_rgba(0,0,0,0.06)] transition-all duration-400 group-hover:-translate-y-2 group-hover:shadow-[0_12px_200px_rgba(0,0,0,0.08)] group-hover:border-[#ee4d2d]/10 shrink-0 overflow-hidden">
          {#if category.image}
            <img src={category.image} alt={category.name} class="w-3/4 h-3/4 md:w-full md:h-full object-contain transition-transform duration-500 group-hover:scale-110" />
          {:else}
            <div class="text-2xl md:text-3xl transition-transform duration-500 group-hover:scale-110 select-none">
              {category.icon || '📦'}
            </div>
          {/if}
        </div>
        
        <!-- Refined Typography -->
        <span class="mt-3 text-[11px] md:text-[13px] font-medium text-gray-700 text-center leading-snug transition-colors duration-300 group-hover:text-[#ee4d2d] w-full line-clamp-2 px-1">
          {category.name}
        </span>
      </button>
    {/each}
  </div>
</div>
