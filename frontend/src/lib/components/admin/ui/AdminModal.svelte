<script lang="ts">
  import { fade, fly, scale } from "svelte/transition";
  import { onMount, type Snippet, type Component } from "svelte";
  import X from "@lucide/svelte/icons/x";
  import Terminal from "@lucide/svelte/icons/terminal";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import SupremeCloseButton from "./SupremeCloseButton.svelte";

  interface Props {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    subtitle?: string;
    variant?: "emerald" | "cyan" | "amber" | "red" | "indigo";
    maxWidth?: string;
    children?: Snippet;
    footer?: Snippet;
    headerIcon?: Component;
    showCloseButton?: boolean;
    hideHeader?: boolean;
    closeOnBackdrop?: boolean;
  }

  let {
    isOpen,
    onClose,
    title,
    subtitle = "XOHI NEURAL ENGINE | ELITE V2.2",
    variant = "cyan",
    maxWidth = "max-w-4xl",
    children,
    footer,
    headerIcon = Terminal,
    showCloseButton = true,
    hideHeader = false,
    closeOnBackdrop = true
  }: Props = $props();

  let Icon = $derived(headerIcon);

  const themes = {
    emerald: {
      border: "border-emerald-500/20",
      bg: "bg-emerald-500/5",
      text: "text-emerald-400",
      glow: "shadow-[0_0_50px_rgba(16,185,129,0.1)]",
      accent: "bg-emerald-500",
      bracket: "border-emerald-500/40"
    },
    cyan: {
      border: "border-cyan-500/20",
      bg: "bg-cyan-500/5",
      text: "text-cyan-400",
      glow: "shadow-[0_0_50px_rgba(6,182,212,0.1)]",
      accent: "bg-cyan-500",
      bracket: "border-cyan-500/40"
    },
    amber: {
      border: "border-amber-500/20",
      bg: "bg-amber-500/5",
      text: "text-amber-400",
      glow: "shadow-[0_0_50px_rgba(245,158,11,0.1)]",
      accent: "bg-amber-500",
      bracket: "border-amber-500/40"
    },
    red: {
      border: "border-red-500/20",
      bg: "bg-red-500/5",
      text: "text-red-400",
      glow: "shadow-[0_0_50px_rgba(239,68,68,0.1)]",
      accent: "bg-red-500",
      bracket: "border-red-500/40"
    },
    indigo: {
      border: "border-indigo-500/20",
      bg: "bg-indigo-500/5",
      text: "text-indigo-400",
      glow: "shadow-[0_0_50px_rgba(99,102,241,0.1)]",
      accent: "bg-indigo-500",
      bracket: "border-indigo-500/40"
    }
  };

  let theme = $derived(themes[variant]);

  // Handle ESC key
  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Escape" && isOpen) {
      onClose();
    }
  }

  onMount(() => {
    window.addEventListener("keydown", handleKeydown);
    return () => window.removeEventListener("keydown", handleKeydown);
  });
</script>

{#if isOpen}
  <div 
    class="fixed inset-0 flex items-center justify-center p-4 md:p-8"
    style="z-index: {Z_INDEX_ADMIN.MODAL}"
    transition:fade={{ duration: 200 }}
  >
    <!-- Backdrop -->
    <div 
      class="absolute inset-0 bg-[#050505]/80 backdrop-blur-xl"
      onclick={() => closeOnBackdrop && onClose()}
      aria-hidden="true"
    ></div>

    <!-- Modal Container -->
    <div 
      class="relative w-full {maxWidth} max-h-full flex flex-col bg-black/40 border {theme.border} rounded-3xl overflow-hidden {theme.glow} ring-1 ring-white/5"
      transition:scale={{ start: 0.95, duration: 300, opacity: 0 }}
    >
      <!-- Scanline Effect -->
      <div class="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_2px,3px_100%] z-50 opacity-20"></div>

      <!-- HUD Brackets -->
      <div class="absolute top-0 left-0 w-8 h-8 border-t border-l {theme.bracket} rounded-tl-3xl z-10"></div>
      <div class="absolute top-0 right-0 w-8 h-8 border-t border-r {theme.bracket} rounded-tr-3xl z-10"></div>
      <div class="absolute bottom-0 left-0 w-8 h-8 border-b border-l {theme.bracket} rounded-bl-3xl z-10"></div>
      <div class="absolute bottom-0 right-0 w-8 h-8 border-b border-r {theme.bracket} rounded-br-3xl z-10"></div>

      <!-- Header -->
      {#if !hideHeader}
        <div class="flex items-center justify-between px-6 py-5 border-b {theme.border} bg-white/[0.02] shrink-0 relative z-10">
          <div class="flex items-center gap-4">
            <div class="w-10 h-10 rounded-xl {theme.bg} border {theme.border} flex items-center justify-center relative group">
              <div class="absolute inset-0 {theme.accent} opacity-20 blur-lg group-hover:opacity-40 transition-opacity"></div>
              {#if Icon}
                <Icon size={18} class="{theme.text} relative z-10" />
              {/if}
            </div>
            <div class="flex flex-col">
              <h2 class="text-xs font-black text-white uppercase tracking-[0.3em] leading-tight">
                {title}
              </h2>
              <span class="text-[8px] font-mono {theme.text} opacity-50 uppercase tracking-widest mt-1">
                {subtitle}
              </span>
            </div>
          </div>

          {#if showCloseButton}
            <SupremeCloseButton {onClose} />
          {/if}
        </div>
      {/if}

      <!-- Content -->
      <div class="flex-1 overflow-y-auto custom-scrollbar p-6 relative z-10">
        {@render children?.()}
      </div>

      <!-- Footer -->
      {#if footer}
        <div class="px-6 py-4 border-t {theme.border} bg-white/[0.01] flex justify-end items-center gap-3 shrink-0 relative z-10">
          {@render footer()}
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  @reference "tailwindcss";

  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    @apply bg-white/5 rounded-full;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    @apply bg-white/10;
  }
</style>
