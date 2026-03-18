<script lang="ts">
  import { nanobot } from "$lib/state/nanobot.svelte";
  import XohiLogo from "./XohiLogo.svelte";
  import { scale } from "svelte/transition";

  // Luxury Design Tokens 2026
  const statusConfig = {
    THINKING: {
      border: "border-neon-cyan/60",
      bg: "bg-neon-cyan/5",
      glow: "shadow-[0_0_15px_rgba(0,255,255,0.4)]",
      text: "text-neon-cyan",
      point: "bg-neon-cyan",
    },
    PROCESSING: {
      border: "border-hacker-green/60",
      bg: "bg-hacker-green/5",
      glow: "shadow-[0_0_15px_rgba(16,185,129,0.4)]",
      text: "text-hacker-green",
      point: "bg-hacker-green",
    },
    ERROR: {
      border: "border-alert-red/60",
      bg: "bg-alert-red/5",
      glow: "shadow-[0_0_15px_rgba(239,68,68,0.4)]",
      text: "text-alert-red",
      point: "bg-alert-red",
    },
    VOICE: {
      border: "border-neon-magenta/60",
      bg: "bg-neon-magenta/5",
      glow: "shadow-[0_0_15px_rgba(236,72,153,0.4)]",
      text: "text-neon-magenta",
      point: "bg-neon-magenta",
    },
    SUCCESS: {
      border: "border-neon-yellow/60",
      bg: "bg-neon-yellow/5",
      glow: "shadow-[0_0_15px_rgba(234,179,8,0.4)]",
      text: "text-neon-yellow",
      point: "bg-neon-yellow",
    },
    IDLE: {
      border: "border-white/10",
      bg: "bg-transparent",
      glow: "",
      text: "text-gray-500",
      point: "bg-gray-500",
    },
  };

  // God Mode: Use derived status directly from nanobot store to prevent frame delay (CNS V76)
  let localStatus = $derived(nanobot?.nanoBotStatus || "IDLE");

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
  class="relative w-8 h-8 flex items-center justify-center group active:scale-90 transition-transform cursor-pointer overflow-visible bg-[#050505] rounded-xl border border-white/5 shadow-2xl"
>
  <!-- Outer Diamond Ring -->
  <div
    class="absolute inset-0 border rounded-lg transition-all duration-700 transform rotate-45 {borderClass} {isGlow
      ? 'opacity-80 ' + glowClass
      : 'opacity-20'}"
  ></div>

  <!-- Inner Rotating Core (Hamster Edition) -->
  <div
    class="w-6 h-6 rounded-full overflow-hidden border-2 transition-all duration-500 animate-[spin_6s_linear_infinite] {borderClass} {bgClass} {localStatus === 'THINKING' ? 'animate-pulse scale-110' : ''} {isGlow ? 'shadow-inner' : 'grayscale opacity-50'}"
  >
    <XohiLogo variant="simple" size={24} />
  </div>

  <!-- Status Label (Admin Context) -->
  {#if localStatus !== "IDLE"}
    <div
      in:scale={{ duration: 200 }}
      class="absolute -top-7 left-1/2 -translate-x-1/2 text-[7px] font-black tracking-widest uppercase whitespace-nowrap px-2 py-0.5 rounded-full bg-black/80 border border-white/10 {textClass} shadow-glow-sm"
    >
      {localStatus}
    </div>
  {/if}
</button>

<style>
  @keyframes spin {
    from {
      transform: rotate(45deg);
    }
    to {
      transform: rotate(405deg);
    }
  }
</style>
