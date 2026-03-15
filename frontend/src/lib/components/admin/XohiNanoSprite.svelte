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

  // God Mode: Shadow state to avoid race conditions during hydration
  let localStatus = $state("IDLE");
  
  $effect(() => {
    if (nanobot?.nanoBotStatus) {
      localStatus = nanobot.nanoBotStatus;
    }
  });

  let currentConfig = $derived(
    statusConfig[localStatus as keyof typeof statusConfig] || statusConfig.IDLE
  );

  let borderClass = $derived(currentConfig?.border || "");
  let bgClass = $derived(currentConfig?.bg || "");
  let glowClass = $derived(currentConfig?.glow || "");
  let textClass = $derived(currentConfig?.text || "");
  let pointClass = $derived(currentConfig?.point || "");
  
  let isGlow = $derived(localStatus !== "IDLE");
</script>

<button
  onclick={() => {
    if (localStatus === "IDLE") {
      nanobot?.startRecording();
    } else {
      nanobot?.setVuiActive(true);
    }
  }}
  class="relative w-8 h-8 flex items-center justify-center group active:scale-90 transition-transform cursor-pointer overflow-visible"
>
  <!-- Outer Ring -->
  <div
    class="absolute inset-0 border-2 rounded-lg transition-all duration-500 transform rotate-45 {borderClass} {isGlow
      ? 'opacity-80 ' + glowClass
      : 'opacity-30'}"
  ></div>

  <!-- Inner Rotating Core -->
  <div
    class="w-4 h-4 border transition-all duration-500 animate-[spin_4s_linear_infinite] {borderClass} {bgClass} {localStatus === 'THINKING' ? 'animate-pulse' : ''}"
  ></div>

  <!-- Micro Glow Points -->
  <div
    class="absolute -top-1 -right-1 w-1.5 h-1.5 rounded-full transition-all duration-500 {pointClass} {isGlow
      ? 'opacity-100 animate-ping'
      : 'opacity-0'}"
  ></div>
  <div
    class="absolute -bottom-1 -left-1 w-1 h-1 rounded-full transition-all duration-500 {pointClass} {isGlow
      ? 'opacity-50 animate-pulse'
      : 'opacity-0'}"
  ></div>

  <!-- Status Label (Hidden by default, shows on admin context) -->
  {#if localStatus !== "IDLE"}
    <div
      in:scale={{ duration: 200 }}
      class="absolute -top-6 left-1/2 -translate-x-1/2 text-[8px] font-mono tracking-tighter uppercase whitespace-nowrap {textClass}"
    >
      {localStatus}
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
