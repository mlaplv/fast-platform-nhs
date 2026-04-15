<script lang="ts">
  import type { Snippet } from 'svelte';
  import UserSidebar from './UserSidebar.svelte';

  let { children }: { children: Snippet } = $props();
</script>

<div class="bg-[#F9F8F6] min-h-screen">
  <div class="max-w-[1200px] mx-auto px-4 xl:px-0 py-8 md:py-12 flex flex-col md:flex-row gap-8 lg:gap-10">
    <UserSidebar />
    <main class="flex-grow bg-white rounded-[4px] p-10 border border-stone-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] min-h-[700px]">
      {@render children()}
    </main>
  </div>
</div>
