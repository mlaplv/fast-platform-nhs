<script lang="ts">
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import X from "@lucide/svelte/icons/x";
  import { portal } from '$lib/core/actions/portal';
  import { fade, fly } from 'svelte/transition';
  import type { Snippet } from 'svelte';

  interface Props {
    active: boolean;
    title: string;
    children: Snippet;
    fullWidth?: boolean;
    extraStyle?: string;
    tight?: boolean;
    onClose?: () => void;
  }

  let { active = $bindable(), title, children, fullWidth = false, extraStyle = "", tight = false, onClose }: Props = $props();

  // Drag-to-Close Logic
  let dragY = $state(0);
  let isDragging = $state(false);
  let startY = 0;

  function onPointerDown(e: PointerEvent) {
    isDragging = true;
    startY = e.clientY;
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }

  function onPointerMove(e: PointerEvent) {
    if (!isDragging) return;
    const delta = e.clientY - startY;
    if (delta > 0) dragY = delta;
    else dragY = delta * 0.2;
  }

  function onPointerUp() {
    if (!isDragging) return;
    isDragging = false;
    if (dragY > 120) {
      close();
    }
    dragY = 0;
  }

  function close() {
    active = false;
    if (onClose) onClose();
  }
</script>

<div use:portal class="mobile-bottom-sheet-root" style:--z-index={Z_INDEX_CLIENT.MOBILE_BOTTOM_SHEET}>
  {#if active}
    <button
      type="button"
      class="mobile-overlay border-none outline-none"
      class:active
      onclick={close}
      aria-label="Đóng"
      transition:fade={{ duration: 300 }}
      style:z-index={Z_INDEX_CLIENT.MOBILE_BOTTOM_SHEET_OVERLAY}
    ></button>

    <div
      class="mobile-modal-base"
      class:active
      class:dragging={isDragging}
      style:--drag-y={dragY + 'px'}
      style:z-index={Z_INDEX_CLIENT.MOBILE_BOTTOM_SHEET}
      role="dialog"
      aria-modal="true"
      transition:fly={{ y: '100%', duration: 400 }}
    >
      <div
        class="w-full flex justify-center pt-4 pb-2 relative touch-none cursor-grab active:cursor-grabbing"
        onpointerdown={onPointerDown}
        onpointermove={onPointerMove}
        onpointerup={onPointerUp}
        onpointercancel={onPointerUp}
      >
        <div class="w-12 h-1 bg-white/20 rounded-full"></div>
      </div>

      <button onclick={close} aria-label="Đóng" class="absolute right-0 top-0 w-12 h-12 flex items-center justify-center text-white/40 hover:text-white transition-all active:scale-90" style:z-index={Z_INDEX_CLIENT.HEADER}>
        <X class="w-5 h-5" strokeWidth={2} />
      </button>

      <div class="relative flex items-center justify-center px-6 pt-2 pb-4 border-b border-white/5">
        <h2 class="text-[11px] font-black tracking-[0.25em] text-white/60">
          {title}
        </h2>
      </div>

      <div 
        id="elite-bottom-sheet-content"
        class="px-1 pt-4 overflow-y-auto custom-scrollbar flex flex-col h-auto max-h-[75dvh] flex-initial"
        class:pb-4={!tight}
        class:pb-1={tight}
        style={extraStyle}
      >
        {@render children()}
      </div>
    </div>
  {/if}
</div>

<style>
  .mobile-bottom-sheet-root {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: var(--z-index);
    pointer-events: none;
  }
  .mobile-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.6);
    pointer-events: auto;
  }
  .mobile-modal-base {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background: #0a0a0a;
    color: white;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 5px 5px 0 0;
    pointer-events: auto;
    transform: translateY(var(--drag-y, 0));
  }
</style>
