<script lang="ts">
  import { nanobot } from "$lib/state/nanobot.svelte";
  import "./client.css";
  let { children } = $props();
</script>

<div class="client-layout min-h-screen flex flex-col">
  <main class="flex-grow">
    {@render children()}
  </main>
  
  {#if !nanobot.ui.hideFooter}
    <footer class="bg-slate-950/80 backdrop-blur-md border-t border-white/5 py-8 text-center mt-auto relative z-20">
      <div class="flex flex-col items-center gap-4">
        <a 
          href="/track" 
          class="text-[10px] font-black text-slate-500 hover:text-sky-400 transition-colors uppercase tracking-[0.4em] italic"
        >
          Tra cứu đơn hàng • Order Tracking
        </a>
        <p class="text-[8px] text-slate-700 font-bold uppercase tracking-widest">
          Copyright © 2026 Nhà Thuốc Hồng Sơn. All Rights Reserved.
        </p>
      </div>
    </footer>
  {/if}
</div>
