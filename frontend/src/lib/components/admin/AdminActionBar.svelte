<script lang="ts">
  import { onMount } from "svelte";
  import { liveEditStore } from "$lib/state/commerce/liveEdit.svelte";
  import { permissionState } from "$lib/state/permissions.svelte";
  import { fade, fly } from "svelte/transition";
  import { 
    Edit3, 
    Save, 
    X, 
    ShieldCheck, 
    RefreshCcw,
    MousePointer2,
    GripVertical
  } from "lucide-svelte";

  const isEditMode = $derived(liveEditStore.isEditMode);
  
  $effect(() => {
    if (isEditMode) {
      document.body.classList.add('is-editing-mode');
    } else {
      document.body.classList.remove('is-editing-mode');
    }
  });

  // Viral 2026: Administrative HUD logic
  const isAdmin = $derived(liveEditStore.isAdmin);

  // Drag Interaction (Elite V2.2)
  let dragOffset = $state({ x: 0, y: 0 });
  let isDragging = $state(false);
  let startPos = { x: 0, y: 0 };

  onMount(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      dragOffset.x = e.clientX - startPos.x;
      dragOffset.y = e.clientY - startPos.y;
    };
    
    const onMouseUp = () => {
      isDragging = false;
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    
    // Quantum Mobile: Touch listeners
    const onTouchMove = (e: TouchEvent) => {
      if (!isDragging || e.touches.length === 0) return;
      const touch = e.touches[0];
      dragOffset.x = touch.clientX - startPos.x;
      dragOffset.y = touch.clientY - startPos.y;
    };
    const onTouchEnd = () => { isDragging = false; };

    window.addEventListener('touchmove', onTouchMove, { passive: false });
    window.addEventListener('touchend', onTouchEnd);

    return () => {
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
        window.removeEventListener('touchmove', onTouchMove);
        window.removeEventListener('touchend', onTouchEnd);
    };
  });

  function handleDragStart(e: MouseEvent | TouchEvent) {
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    
    isDragging = true;
    startPos = {
      x: clientX - dragOffset.x,
      y: clientY - dragOffset.y
    };
  }

  function triggerHaptic() {
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      navigator.vibrate(10); // Standard Elite short buzz
    }
  }

  function toggleEditMode() {
    triggerHaptic();
    liveEditStore.toggleEditMode();
  }
</script>

{#if isAdmin && liveEditStore.isEditMode}
  <!-- Quantum Mobile: Top-Edge Active Edit Indicator -->
  <div
    class="md:hidden fixed top-0 left-0 right-0 h-[3px] bg-blue-600 shadow-[0_0_15px_rgba(59,130,246,0.8)] animate-pulse z-[var(--z-admin-action-bar-progress)]"
    transition:fade
  ></div>
{/if}

{#if isAdmin}
  <div
    class="admin-action-bar fixed bottom-6 md:bottom-10 left-1/2 z-[var(--z-admin-action-bar)] flex items-center gap-1 md:gap-2 p-1.5 md:p-2 bg-slate-950/80 backdrop-blur-3xl border border-white/10 rounded-full shadow-[0_30px_100px_rgba(0,0,0,0.8)] {isDragging ? 'is-dragging select-none' : ''}"
    style:transform="translate(calc(-50% + {dragOffset.x}px), {dragOffset.y}px)"
    in:fly={{ y: 50, duration: 800 }}
  >
    <!-- Drag Handle (Elite V2.2) -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div 
      class="pl-3 md:pl-4 pr-1 py-2 flex items-center gap-2 cursor-grab active:cursor-grabbing hover:text-blue-400 transition-colors group"
      onmousedown={handleDragStart}
      ontouchstart={handleDragStart}
    >
      <GripVertical size={14} class="text-white/20 group-hover:text-blue-500/50 transition-colors" />
      
      <!-- Operator Status -->
      <div class="flex items-center gap-3 border-r border-white/10 pr-4 pointer-events-none">
        <div class="relative">
          <ShieldCheck size={18} class="text-blue-400" />
          <div class="absolute inset-0 bg-blue-400 blur-md opacity-20"></div>
        </div>
        <div class="flex flex-col hidden md:flex">
          <span class="text-[8px] font-black text-white/30 uppercase tracking-[0.2em] leading-none mb-0.5">AUTH_LEVEL</span>
          <div class="flex items-center gap-2">
            <span class="text-[10px] font-black text-blue-400 uppercase tracking-widest leading-none">
              {permissionState.userName || 'UNAUTHORIZED'}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Toggle -->
    <button 
      onclick={toggleEditMode}
      class="flex items-center gap-2 md:gap-3 px-4 md:px-6 py-2.5 md:py-3 rounded-full transition-all duration-500 {liveEditStore.isEditMode ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-[0_0_30px_rgba(245,158,11,0.1)]' : 'hover:bg-white/5 text-white/60 hover:text-white'}"
    >
      <Edit3 size={15} />
      <span class="text-[11px] font-black uppercase tracking-[0.2em] hidden md:inline">{liveEditStore.isEditMode ? 'DANG CHỈNH SỬA' : 'CHẾ ĐỘ CHỈNH SỬA'}</span>
    </button>

    {#if liveEditStore.isEditMode}
      <div class="w-px h-6 bg-white/10"></div>
      
      <!-- Save Button -->
      <button 
        onclick={() => liveEditStore.save()}
        disabled={liveEditStore.isSaving}
        class="flex items-center gap-2 md:gap-3 px-5 md:px-8 py-2.5 md:py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-full transition-all duration-300 shadow-[0_10px_40px_rgba(37,99,235,0.3)] active:scale-95 disabled:opacity-50"
      >
        {#if liveEditStore.isSaving}
          <RefreshCcw size={15} class="animate-spin" />
        {:else}
          <Save size={15} />
        {/if}
        <span class="text-[11px] font-black uppercase tracking-[0.2em] hidden md:inline">{liveEditStore.isSaving ? 'DANG LƯU...' : 'LƯU THAY ĐỔI'}</span>
      </button>

      <!-- Discard Button -->
      <button 
        onclick={() => liveEditStore.discardChanges()}
        disabled={liveEditStore.isSaving}
        class="p-3 text-white/40 hover:text-red-400 hover:bg-red-400/10 rounded-full transition-all"
        title="Hủy bỏ"
      >
        <X size={18} />
      </button>
    {/if}

    <!-- Visual Hint -->
    {#if !liveEditStore.isEditMode}
      <div class="absolute -top-10 left-1/2 -translate-x-1/2 px-4 py-2 bg-blue-500/10 backdrop-blur-xl border border-blue-500/20 rounded-lg pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
        <span class="text-[9px] font-bold text-blue-400 tracking-widest uppercase">ENABLE LIVE_EDITOR_V2.2 TO SYNC ASSETS</span>
      </div>
    {/if}
  </div>
{/if}

<style lang="postcss">
  :global(body.is-editing-mode) {
    cursor: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z'></path></svg>") 0 20, auto !important;
  }

  :global(body.is-editing-mode .editable-wrapper:hover) {
    cursor: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 24 24' fill='none' stroke='%233b82f6' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><path d='M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z'></path></svg>") 0 20, pointer !important;
  }

  .admin-action-bar {
    animation: bar-glow 4s infinite alternate;
    transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
  }

  .admin-action-bar.is-dragging {
    transition: none !important;
  }

  @keyframes bar-glow {
    from { box-shadow: 0 30px 100px rgba(0,0,0,0.8), 0 0 20px rgba(59,130,246,0.05); }
    to { box-shadow: 0 30px 100px rgba(0,0,0,0.8), 0 0 40px rgba(59,130,246,0.1); }
  }
</style>
