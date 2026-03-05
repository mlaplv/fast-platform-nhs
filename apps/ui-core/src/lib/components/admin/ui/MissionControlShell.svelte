<script lang="ts">
  import { fade, fly } from "svelte/transition";
  import X from "lucide-svelte/icons/x";
  import Activity from "lucide-svelte/icons/activity";
  import Cpu from "lucide-svelte/icons/cpu";
  import Terminal from "lucide-svelte/icons/terminal";

  interface Props {
    title: string;
    node?: string;
    protocol?: string;
    variant?: "cyan" | "red";
    isOpen: boolean;
    onClose: () => void;
    showFooter?: boolean;
    maxWidth?: string;
    height?: string;
    children?: any;
    headerIcon?: any;
    zIndex?: string;
    backdropClass?: string;
  }

  let {
    title,
    node = "TRINITY_PRIMARY",
    protocol = "GHOST_v8",
    variant = "cyan",
    isOpen,
    onClose,
    showFooter = true,
    maxWidth = "max-w-6xl",
    height = "h-[85vh]",
    children,
    headerIcon = Terminal,
    zIndex = "z-[100]",
    backdropClass = "bg-[#050505]/95 md:bg-black/85 md:backdrop-blur-2xl",
  }: Props = $props();

  const theme = $derived({
    color: variant === "cyan" ? "#00f3ff" : "#ff0000",
    textClass: variant === "cyan" ? "text-neon-cyan" : "text-alert-red",
    borderClass:
      variant === "cyan" ? "border-neon-cyan/20" : "border-alert-red/30",
    bgClass: variant === "cyan" ? "bg-neon-cyan/5" : "bg-alert-red/10",
    shadowClass:
      variant === "cyan"
        ? "shadow-[0_0_100px_rgba(0,243,255,0.15)]"
        : "shadow-[0_0_150px_rgba(255,0,0,0.15)]",
    glowClass: variant === "cyan" ? "bg-neon-cyan/20" : "bg-alert-red/20",
    bracketClass:
      variant === "cyan" ? "border-neon-cyan/60" : "border-alert-red/80",
    sparkClass:
      variant === "cyan"
        ? "bg-neon-cyan shadow-[0_0_15px_#00f3ff]"
        : "bg-alert-red shadow-[0_0_15px_#ff0000]",
    flowClass: variant === "cyan" ? "via-neon-cyan/40" : "via-alert-red/40",
  });

  let currentTime = $state(new Date().toLocaleTimeString());
  $effect(() => {
    const timer = setInterval(() => {
      currentTime = new Date().toLocaleTimeString();
    }, 1000);
    return () => clearInterval(timer);
  });
</script>

{#if isOpen}
  <div
    class="absolute inset-0 {zIndex} flex items-center justify-center p-6 pointer-events-none"
    transition:fade={{ duration: 400 }}
  >
    <!-- Master Backdrop -->
    <div
      class="absolute inset-0 {backdropClass} pointer-events-auto"
      onclick={(e) => { e.stopPropagation(); onClose(); }}
      onkeydown={(e) => e.key === "Escape" && onClose()}
      role="presentation"
    >
      <!-- Scanning Line Effect -->
      <div
        class="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(0,255,255,0.06),rgba(0,0,0,0.02),rgba(0,255,0,0.02))] z-0 pointer-events-none bg-[length:100%_2px,3px_100%]"
      ></div>
      <div
        class="absolute inset-0 overflow-hidden pointer-events-none opacity-20"
      >
        <div class="universal-scanline"></div>
      </div>
    </div>

    <!-- THE MASTER FRAME -->
    <div
      class="relative w-full {maxWidth} {height} bg-[#0a0a0a]/95 border {theme.borderClass} flex flex-col pointer-events-auto {theme.shadowClass} overflow-hidden"
      transition:fly={{ y: 50, duration: 600, opacity: 0 }}
    >
      <!-- ELECTRONIC BORDER EFFECT -->
      <div
        class="absolute inset-0 z-0 pointer-events-none overflow-hidden opacity-50"
      >
        <div
          class="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent {theme.flowClass} to-transparent animate-border-flow-x"
        ></div>
        <div
          class="absolute bottom-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent {theme.flowClass} to-transparent animate-border-flow-x-reverse"
        ></div>
        <div
          class="absolute top-0 left-0 w-[1px] h-full bg-gradient-to-b from-transparent {theme.flowClass} to-transparent animate-border-flow-y"
        ></div>
        <div
          class="absolute top-0 right-0 w-[1px] h-full bg-gradient-to-b from-transparent {theme.flowClass} to-transparent animate-border-flow-y-reverse"
        ></div>

        <div
          class="absolute top-0 left-0 w-16 h-[1px] {theme.sparkClass} animate-spark-top"
        ></div>
        <div
          class="absolute bottom-0 right-0 w-16 h-[1px] {theme.sparkClass} animate-spark-bottom"
        ></div>
        <div
          class="absolute top-0 right-0 w-[1px] h-16 {theme.sparkClass} animate-spark-right"
        ></div>
        <div
          class="absolute bottom-0 left-0 w-[1px] h-16 {theme.sparkClass} animate-spark-left"
        ></div>
      </div>

      <!-- HUD Brackets -->
      <div
        class="absolute top-0 left-0 w-12 h-12 border-t-2 border-l-2 {theme.bracketClass} animate-hud-flicker bracket-tl"
      ></div>
      <div
        class="absolute top-0 right-0 w-12 h-12 border-t-2 border-r-2 {theme.bracketClass} animate-hud-flicker bracket-tr"
      ></div>
      <div
        class="absolute bottom-0 left-0 w-12 h-12 border-b-2 border-l-2 {theme.bracketClass} animate-hud-flicker bracket-bl"
      ></div>
      <div
        class="absolute bottom-0 right-0 w-12 h-12 border-b-2 border-r-2 {theme.bracketClass} animate-hud-flicker bracket-br"
      ></div>

      <!-- Header HUD -->
      <div
        class="flex items-center justify-between px-8 py-5 border-b {theme.borderClass} bg-white/[0.02] relative z-10"
      >
        <div class="flex items-center gap-6">
          <div
            class="p-3 {theme.bgClass} border {theme.borderClass} rounded-xl relative group"
          >
            <div
              class="absolute inset-0 {theme.glowClass} blur-lg animate-pulse"
            ></div>
            {#if typeof headerIcon === "string"}
              <span class="text-xl relative z-10">{headerIcon}</span>
            {:else}
              {@const IconComponent = headerIcon}
              <IconComponent
                size={22}
                class="{theme.textClass} relative z-10"
              />
            {/if}
          </div>
          <div class="flex flex-col">
            <div class="flex items-center gap-3 mb-1">
              <Activity size={14} class="{theme.textClass} animate-pulse" />
              <h2
                class="text-xl font-bold text-white tracking-[0.4em] uppercase"
              >
                {title}
              </h2>
            </div>
            <div
              class="flex items-center gap-4 text-[8px] font-mono text-white/20 uppercase tracking-[0.3em]"
            >
              <span>Node: {node}</span>
              <span class="w-1 h-1 rounded-full bg-white/10"></span>
              <span>Protocol: {protocol}</span>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-4">
          <div class="flex flex-col items-end mr-6 opacity-40">
            <span
              class="text-[8px] font-mono text-white uppercase tracking-[0.5em]"
              >System Display</span
            >
            <span
              class="text-[10px] font-mono {theme.textClass} uppercase tracking-widest tabular-nums"
              >{currentTime}</span
            >
          </div>
          <button
            onclick={onClose}
            class="w-12 h-12 flex items-center justify-center border {theme.borderClass} {theme.bgClass} {theme.textClass} hover:bg-white/10 transition-all group"
          >
            <X
              size={22}
              class="group-hover:rotate-90 transition-transform duration-500"
            />
          </button>
        </div>
      </div>

      <!-- Main Content Area -->
      <div
        class="flex-1 overflow-y-auto relative scrollbar-mission z-10"
      >
        <div
          class="absolute inset-0 opacity-[0.04] pointer-events-none"
          style="background-image: url(&quot;data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.7' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E&quot;)"
        ></div>
        {@render children?.()}
      </div>

      <!-- Footer HUD -->
      {#if showFooter}
        <div
          class="px-8 py-3 bg-white/[0.02] border-t {theme.borderClass} flex justify-between items-center relative overflow-hidden z-10"
        >
          <div class="flex flex-col">
            <span
              class="text-[7px] font-mono text-white/20 uppercase tracking-[0.5em]"
              >System Status: Operational</span
            >
            <div class="flex gap-1 mt-1">
              {#each Array(6) as _, i}
                <div
                  class="w-1.5 h-1.5 {variant === 'cyan'
                    ? 'bg-neon-cyan'
                    : 'bg-alert-red'} {i < 5 ? 'opacity-40' : 'opacity-5'}"
                ></div>
              {/each}
            </div>
          </div>

          <div class="flex items-center gap-4">
            <Cpu size={14} class="text-white/20" />
            <div
              class="text-[9px] text-white/20 uppercase tracking-[0.8em] font-mono"
            >
              Mission Control Interface Active
            </div>
          </div>
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .scrollbar-mission::-webkit-scrollbar {
    width: 4px;
  }
  .scrollbar-mission::-webkit-scrollbar-track {
    background: transparent;
  }
  .scrollbar-mission::-webkit-scrollbar-thumb {
    background: rgba(0, 243, 255, 0.15);
  }

  .universal-scanline {
    width: 100%;
    height: 150px;
    z-index: 10;
    background: linear-gradient(
      0deg,
      rgba(0, 0, 0, 0) 0%,
      rgba(0, 243, 255, 0.08) 50%,
      rgba(0, 0, 0, 0) 100%
    );
    position: absolute;
    bottom: 100%;
    animation: scanline 12s linear infinite;
  }

  @keyframes scanline {
    0% {
      bottom: 100%;
    }
    100% {
      bottom: -150px;
    }
  }

  @keyframes border-flow-x {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }
  @keyframes border-flow-y {
    0% {
      transform: translateY(-100%);
    }
    100% {
      transform: translateY(100%);
    }
  }
  @keyframes spark-top {
    0% {
      left: -10%;
      opacity: 0;
    }
    10%,
    90% {
      opacity: 1;
    }
    100% {
      left: 110%;
      opacity: 0;
    }
  }
  @keyframes spark-bottom {
    0% {
      right: -10%;
      opacity: 0;
    }
    10%,
    90% {
      opacity: 1;
    }
    100% {
      right: 110%;
      opacity: 0;
    }
  }
  @keyframes spark-right {
    0% {
      top: -10%;
      opacity: 0;
    }
    10%,
    90% {
      opacity: 1;
    }
    100% {
      top: 110%;
      opacity: 0;
    }
  }
  @keyframes spark-left {
    0% {
      bottom: -10%;
      opacity: 0;
    }
    10%,
    90% {
      opacity: 1;
    }
    100% {
      bottom: 110%;
      opacity: 0;
    }
  }

  @keyframes hud-flicker {
    0%,
    100% {
      opacity: 0.6;
    }
    50% {
      opacity: 0.3;
    }
    52% {
      opacity: 0.8;
    }
    54% {
      opacity: 0.4;
    }
  }
  .animate-hud-flicker {
    animation: hud-flicker 4s linear infinite;
  }

  /* Bracket Animation Offsets */
  .bracket-tr {
    animation-delay: 0.5s;
  }
  .bracket-bl {
    animation-delay: 1.2s;
  }
  .bracket-br {
    animation-delay: 0.8s;
  }
</style>
