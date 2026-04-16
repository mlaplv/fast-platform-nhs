<script lang="ts">
  import { Search, ChevronLeft } from 'lucide-svelte';
</script>

<div class="fixed inset-0 bg-white z-[9999] flex flex-col font-sans overflow-hidden">
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
