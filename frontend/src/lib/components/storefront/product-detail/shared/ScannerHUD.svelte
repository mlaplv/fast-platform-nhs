<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, fly, scale } from 'svelte/transition';
  import Scan from "@lucide/svelte/icons/scan";
  import Camera from "@lucide/svelte/icons/camera";
  import type { BarcodeVerificationResponse } from '$lib/types';

  let { barcode = '4968123159022', oncomplete }: { 
    barcode?: string, 
    oncomplete?: (data: {barcode: string, verificationData?: BarcodeVerificationResponse}) => void 
  } = $props();

  let progress = $state(0);
  let isFound = $state(false);
  let isVerifying = $state(false);

  onMount(() => {
    // Simulate scanning process with real data fetch at the end
    const interval = setInterval(async () => {
      progress += 5;
      if (progress >= 80 && !isFound) {
        isFound = true;
      }
      if (progress >= 100) {
        clearInterval(interval);
        isVerifying = true;
        
        console.log(`🧬 [ScannerHUD] Starting verification for: ${barcode}`);
        try {
          const response = await fetch(`/api/v1/client/barcode/verify?barcode=${barcode}`);
          if (response.ok) {
            const data = await response.json();
            console.log(`🧬 [ScannerHUD] Data received:`, data);
            oncomplete?.({ barcode, verificationData: data });
          } else {
            console.error(`🧬 [ScannerHUD] API Error: ${response.status}`);
            oncomplete?.({ barcode }); // Fallback to mock
          }
        } catch (e) {
          console.error("Verification API failed:", e);
          oncomplete?.({ barcode });
        }
      }
    }, 100);

    return () => clearInterval(interval);
  });
</script>

<div class="scanner-hud fixed inset-0 z-[10000] flex items-center justify-center bg-black/90 backdrop-blur-md" transition:fade>
  <!-- SCANNER FRAME -->
  <div class="relative w-72 h-72 border-2 border-white/20 rounded-3xl overflow-hidden" in:scale={{ duration: 600 }}>
    <!-- Corner Accents -->
    <div class="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-luxury-gold rounded-tl-xl"></div>
    <div class="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-luxury-gold rounded-tr-xl"></div>
    <div class="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-luxury-gold rounded-bl-xl"></div>
    <div class="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-luxury-gold rounded-br-xl"></div>

    <!-- Scan Line Animation -->
    <div class="scan-line" style:top="{progress}%"></div>

    <!-- Simulation Overlay -->
    <div class="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-gradient-to-b from-transparent via-white/5 to-transparent">
      {#if isVerifying}
        <div class="barcode-preview" in:fade>
          <span class="text-luxury-gold font-mono text-xl font-black tracking-[0.2em]">{barcode}</span>
          <p class="text-luxury-gold text-[10px] font-black uppercase mt-2 animate-pulse">VERIFYING WITH AI...</p>
        </div>
      {:else if isFound}
        <div class="barcode-preview" in:fly={{ y: 20 }}>
          <span class="text-luxury-gold font-mono text-xl font-black tracking-[0.2em]">{barcode}</span>
          <p class="text-green-400 text-[10px] font-black uppercase mt-2">MATCH FOUND 100%</p>
        </div>
      {:else}
        <Scan size={48} class="text-white/20 animate-pulse" />
        <p class="text-white/40 text-[10px] font-bold uppercase tracking-widest">Đang tìm mã vạch...</p>
      {/if}
    </div>
  </div>

  <!-- STATUS TEXT -->
  <div class="absolute bottom-16 left-0 w-full text-center px-10">
    <div class="glass-morphism-bar max-w-md mx-auto p-6 rounded-[32px] border border-white/10 backdrop-blur-2xl bg-black/20">
      <div class="w-full h-1.5 bg-white/10 rounded-full overflow-hidden mb-4">
        <div class="h-full bg-gradient-to-r from-luxury-gold to-white transition-all duration-300" style:width="{progress}%"></div>
      </div>
      <h2 class="text-white font-black text-xl mb-1 tracking-tight uppercase italic">Truy xuất nguồn gốc</h2>
      <p class="text-white/40 text-[10px] font-bold uppercase tracking-widest italic">Hệ thống thẩm định AI đang bắt mã vạch...</p>
    </div>
  </div>
</div>

<style>
  .scanner-hud {
    user-select: none;
    font-family: var(--font-sans, sans-serif);
  }

  .scan-line {
    position: absolute;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(to bottom, transparent, #E8D5B0, transparent);
    box-shadow: 0 0 25px rgba(232, 213, 176, 0.8);
    z-index: 10;
    transition: top 0.1s linear;
  }

  .barcode-preview {
    text-align: center;
    background: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(20px);
    padding: 16px 32px;
    border-radius: 24px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
  }
</style>
