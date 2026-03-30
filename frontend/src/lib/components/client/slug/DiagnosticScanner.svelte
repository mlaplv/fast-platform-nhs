<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import "./QuantumScan.css";

  let { status = "Đang phân tích tập dữ liệu lâm sàng..." } = $props<{ status?: string }>();

  let binaryData = $state("");
  let interval: any;

  onMount(() => {
    interval = setInterval(() => {
      binaryData = Array.from({ length: 20 }, () => Math.round(Math.random())).join(" ");
    }, 100);
  });

  onDestroy(() => {
    if (interval) clearInterval(interval);
  });
</script>

<div class="quantum-scanner" in:fade={{ duration: 1000 }}>
  <!-- Sci-fi Background Layers! -->
  <div class="scanner-grid"></div>
  <div class="scanner-vignette"></div>
  <div class="biometric-pulse"></div>
  <div class="biometric-pulse" style:animation-delay="1s"></div>
  
  <!-- The Scanning Laser! -->
  <div class="laser-line"></div>

  <!-- Central Analysis HUD! -->
  <div class="hud-center relative px-6 text-center" style:z-index="20">
    <div class="analysis-text text-3xl md:text-6xl font-black mb-6 tracking-[0.2em]">
      ĐANG PHÂN TÍCH...
    </div>
    
    <div class="analysis-status animate-pulse uppercase tracking-[0.15em] font-bold text-center mt-4 text-blue-400/80 text-xs md:text-sm max-w-md mx-auto">
      {status}
    </div>
  </div>

  <!-- Binary Data Flow Overlay! -->
  <div class="data-stream absolute bottom-12 left-12 opacity-40 text-sm">
    <div class="mb-2">SYSTEM_PULSE: OK</div>
    <div class="mb-2">NEURAL_SYNC: {binaryData}</div>
    <div class="mb-2">AGENTIC_REASONING: ACTIVE</div>
  </div>

  <div class="absolute inset-0 bg-blue-500/5 pointer-events-none"></div>
</div>

<style>
  .hud-center {
    filter: drop-shadow(0 0 15px rgba(59, 130, 246, 0.5));
  }
</style>
