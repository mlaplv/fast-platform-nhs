<script lang="ts">
    import Search from "@lucide/svelte/icons/search";
  import ChevronLeft from "@lucide/svelte/icons/chevron-left";
  import ShoppingCart from "@lucide/svelte/icons/shopping-cart";
  import Share2 from "@lucide/svelte/icons/share-2";
  import MoreHorizontal from "@lucide/svelte/icons/more-horizontal";

  let { variant = 'grid' } = $props<{
    variant?: 'grid' | 'home' | 'detail';
  }>();
</script>

<div class="fixed inset-0 bg-white z-[9999] flex flex-col font-sans overflow-hidden">
  
  {#if variant === 'home'}
     <!-- TikTok Home Loading -->
     <div class="flex-grow flex flex-col">
       <!-- Fake Header Nav -->
       <div class="px-4 h-12 flex items-center justify-between border-b border-gray-50">
          <div class="h-6 w-24 bg-gray-50 rounded animate-pulse"></div>
          <div class="flex items-center gap-4">
             <div class="w-8 h-8 bg-gray-50 rounded-full animate-pulse"></div>
             <div class="w-8 h-8 bg-gray-50 rounded-full animate-pulse"></div>
          </div>
       </div>
       
       <!-- Banner Placeholder -->
       <div class="w-full aspect-[21/9] bg-gray-50 relative overflow-hidden">
          <div class="shimmer-effect absolute inset-0"></div>
       </div>

       <!-- Category Circle Row -->
       <div class="px-4 py-6 flex gap-6 overflow-hidden">
          {#each Array(5) as _}
             <div class="flex flex-col items-center gap-2 flex-shrink-0">
                <div class="w-14 h-14 bg-gray-50 rounded-full animate-pulse relative overflow-hidden">
                   <div class="shimmer-effect absolute inset-0"></div>
                </div>
                <div class="h-3 w-10 bg-gray-50 rounded animate-pulse"></div>
             </div>
          {/each}
       </div>

       <!-- Video Banner Placeholder -->
       <div class="px-4 mb-6">
          <div class="w-full aspect-video bg-gray-50 rounded-2xl relative overflow-hidden shadow-sm">
             <div class="shimmer-effect absolute inset-0"></div>
          </div>
       </div>

       <!-- List Placeholder -->
       <div class="px-4 flex flex-col gap-4">
          <div class="h-5 w-32 bg-gray-50 rounded animate-pulse mb-2"></div>
          <div class="grid grid-cols-2 gap-4">
             {#each Array(2) as _}
                <div class="aspect-square bg-gray-50 rounded-xl animate-pulse relative overflow-hidden">
                   <div class="shimmer-effect absolute inset-0"></div>
                </div>
             {/each}
          </div>
       </div>
     </div>

  {:else if variant === 'detail'}
     <!-- TikTok Product Detail Loading -->
     <div class="flex-grow flex flex-col">
       <!-- Floating Actions -->
       <div class="absolute top-0 left-0 right-0 z-10 p-4 flex items-center justify-between pointer-events-none">
          <div class="w-8 h-8 bg-black/5 rounded-full backdrop-blur-md"></div>
          <div class="flex gap-2">
             <div class="w-8 h-8 bg-black/5 rounded-full backdrop-blur-md"></div>
             <div class="w-8 h-8 bg-black/5 rounded-full backdrop-blur-md"></div>
          </div>
       </div>

       <!-- Hero Image Overlay -->
       <div class="w-full aspect-square bg-gray-50 relative overflow-hidden shadow-sm">
          <div class="shimmer-effect absolute inset-0"></div>
       </div>

       <!-- Pricing & Specs -->
       <div class="p-4 flex flex-col gap-4 bg-white -mt-4 rounded-t-3xl relative z-10 shadow-[0_-10px_30px_rgba(0,0,0,0.03)] focus-within:z-auto">
          <div class="flex items-end gap-3 px-1">
             <div class="h-8 w-32 bg-gray-50 rounded animate-pulse"></div>
             <div class="h-4 w-20 bg-gray-50 rounded animate-pulse"></div>
          </div>
          <div class="h-5 w-full bg-gray-50 rounded animate-pulse"></div>
          <div class="h-5 w-3/4 bg-gray-50 rounded animate-pulse"></div>
          
          <div class="h-[1px] w-full bg-gray-100 my-2"></div>
          
          <div class="flex flex-col gap-3">
             <div class="h-4 w-24 bg-gray-50 rounded animate-pulse"></div>
             <div class="flex gap-2">
                {#each Array(3) as _}
                   <div class="h-10 w-24 bg-gray-50 rounded-lg animate-pulse"></div>
                {/each}
             </div>
          </div>
       </div>

       <!-- Bottom CTA Placeholder -->
       <div class="fixed bottom-0 left-0 right-0 h-20 bg-white border-t border-gray-50 flex items-center px-4 gap-3">
          <div class="w-12 h-12 bg-gray-50 rounded-xl animate-pulse"></div>
          <div class="w-12 h-12 bg-gray-50 rounded-xl animate-pulse"></div>
          <div class="flex-1 h-12 bg-[var(--color-brand-primary)]/10 rounded-xl animate-pulse"></div>
          <div class="flex-1 h-12 bg-[var(--color-brand-primary)]/20 rounded-xl animate-pulse"></div>
       </div>
     </div>

  {:else}
    <!-- Grid Loading (Default for Results/Categories) -->
    <!-- Fake Header -->
    <div class="px-2 py-1 flex items-center gap-2 h-12 border-b border-gray-50">
      <div class="p-2 text-gray-200">
        <ChevronLeft size={24} />
      </div>
      <div class="flex-1 h-10 bg-gray-50 rounded-xl flex items-center px-4 gap-2 border border-gray-50">
        <Search size={18} class="text-gray-100" />
        <div class="h-4 w-32 bg-gray-100 rounded animate-pulse"></div>
      </div>
    </div>

    <!-- Fake Tabs -->
    <div class="flex items-center px-4 py-2 gap-4 border-b border-gray-50 overflow-hidden">
      {#each Array(4) as _}
        <div class="h-8 w-20 bg-gray-50 rounded-full animate-pulse flex-shrink-0"></div>
      {/each}
    </div>

    <!-- Grid Loading -->
    <div class="p-3 flex-grow overflow-hidden">
      <div class="grid grid-cols-2 gap-3">
        {#each Array(6) as _}
          <div class="bg-white rounded-2xl border border-gray-50 overflow-hidden shadow-sm">
            <!-- Image Shimmer -->
            <div class="aspect-square bg-gray-50 relative overflow-hidden">
              <div class="shimmer-effect absolute inset-0"></div>
            </div>
            
            <div class="p-3 flex flex-col gap-2">
              <!-- Title Lines -->
              <div class="h-3.5 w-full bg-gray-50 rounded animate-pulse relative overflow-hidden">
                 <div class="shimmer-effect absolute inset-0"></div>
              </div>
              <div class="h-3.5 w-2/3 bg-gray-50 rounded animate-pulse relative overflow-hidden">
                 <div class="shimmer-effect absolute inset-0"></div>
              </div>
              
              <!-- Price Line -->
              <div class="mt-2 h-5 w-1/2 bg-gray-50 rounded animate-pulse relative overflow-hidden">
                <div class="shimmer-effect absolute inset-0"></div>
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

</div>

<style>
  .shimmer-effect {
    background: linear-gradient(
      90deg,
      rgba(255, 255, 255, 0) 0%,
      rgba(255, 255, 255, 0.6) 50%,
      rgba(255, 255, 255, 0) 100%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
  }

  @keyframes shimmer {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }

  /* Custom pulse for softer transition */
  .animate-pulse {
    animation: pulse-soft 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }

  @keyframes pulse-soft {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: .4;
    }
  }
</style>
