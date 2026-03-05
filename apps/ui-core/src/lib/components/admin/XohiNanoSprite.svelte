<script lang="ts">
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { scale } from "svelte/transition";

  // Design Tokens mapping
  const statusConfig = {
    THINKING: {
      border: "border-neon-cyan",
      bg: "bg-neon-cyan/15",
      glow: "shadow-glow-cyan",
      text: "text-neon-cyan",
      point: "bg-neon-cyan",
    },
    PROCESSING: {
      border: "border-hacker-green",
      bg: "bg-hacker-green/15",
      glow: "shadow-glow-green",
      text: "text-hacker-green",
      point: "bg-hacker-green",
    },
    ERROR: {
      border: "border-alert-red",
      bg: "bg-alert-red/15",
      glow: "shadow-glow-red",
      text: "text-alert-red",
      point: "bg-alert-red",
    },
    VOICE: {
      border: "border-neon-magenta",
      bg: "bg-neon-magenta/15",
      glow: "shadow-glow-magenta",
      text: "text-neon-magenta",
      point: "bg-neon-magenta",
    },
    SUCCESS: {
      border: "border-neon-yellow",
      bg: "bg-neon-yellow/15",
      glow: "shadow-glow-yellow",
      text: "text-neon-yellow",
      point: "bg-neon-yellow",
    },
    IDLE: {
      border: "border-idle-gray",
      bg: "bg-idle-gray/15",
      glow: "",
      text: "text-idle-gray",
      point: "bg-idle-gray",
    },
  };

  let currentConfig = $derived(
    statusConfig[nanobot.nanoBotStatus] || statusConfig.IDLE,
  );
  let isGlow = $derived(nanobot.nanoBotStatus !== "IDLE");
</script>

<button
  onclick={() => nanobot.setVuiActive(true)}
  class="relative w-8 h-8 flex items-center justify-center group active:scale-90 transition-transform cursor-pointer"
>
  <!-- Outer Ring -->
  <div
    class="absolute inset-0 border-2 rounded-lg transition-all duration-500 transform rotate-45 {currentConfig.border} {isGlow
      ? 'opacity-80 ' + currentConfig.glow
      : 'opacity-30'}"
  ></div>

  <!-- Inner Rotating Core -->
  <div
    class="w-4 h-4 border transition-all duration-500 animate-[spin_4s_linear_infinite] {currentConfig.border} {currentConfig.bg} {nanobot.nanoBotStatus ===
    'THINKING'
      ? 'animate-pulse'
      : ''}"
  ></div>

  <!-- Micro Glow Points -->
  <div
    class="absolute -top-1 -right-1 w-1.5 h-1.5 rounded-full transition-all duration-500 {currentConfig.point} {isGlow
      ? 'opacity-100 animate-ping'
      : 'opacity-0'}"
  ></div>
  <div
    class="absolute -bottom-1 -left-1 w-1 h-1 rounded-full transition-all duration-500 {currentConfig.point} {isGlow
      ? 'opacity-50 animate-pulse'
      : 'opacity-0'}"
  ></div>

  <!-- Status Label (Hidden by default, shows on admin context) -->
  {#if nanobot.nanoBotStatus !== "IDLE"}
    <div
      in:scale={{ duration: 200 }}
      class="absolute -top-6 left-1/2 -translate-x-1/2 text-[8px] font-mono tracking-tighter uppercase whitespace-nowrap {currentConfig.text}"
    >
      {nanobot.nanoBotStatus}
    </div>
  {/if}
</button>

<style>
  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
</style>
