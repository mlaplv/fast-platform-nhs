<script lang="ts">
  import { onMount } from "svelte";
  import { fade, fly } from "svelte/transition";
  import { liveEditStore } from "$lib/state/commerce/liveEdit.svelte";
  import { X, Save, RefreshCcw } from "lucide-svelte";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/zIndex";
  
  // Dynamic Editors
  import TextEditor from "./editors/TextEditor.svelte";
  import MediaPickerEditor from "./editors/MediaPickerEditor.svelte";
  import QuizEditor from "./editors/QuizEditor.svelte";

  let activeEditor = $state<{
    path: string;
    type: 'text' | 'html' | 'image' | 'video' | 'quiz' | 'metrics';
    label: string;
  } | null>(null);

  // Drag State (Elite V2.2)
  let dragOffset = $state({ x: 0, y: 0 });
  let isDragging = $state(false);
  let startPos = { x: 0, y: 0 };

  onMount(() => {
    const handleOpen = (e: any) => {
      activeEditor = e.detail;
      // Reset drag position on open
      dragOffset = { x: 0, y: 0 };
    };
    window.addEventListener('open-editor', handleOpen);
    
    // Global mouse listeners for smoother dragging
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

    return () => {
        window.removeEventListener('open-editor', handleOpen);
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
    };
  });

  function handleDragStart(e: MouseEvent) {
    // Only allow drag for non-fullscreen editors
    if (activeEditor?.type === 'image' || activeEditor?.type === 'video') return;
    
    isDragging = true;
    startPos = {
      x: e.clientX - dragOffset.x,
      y: e.clientY - dragOffset.y
    };
  }

  function close() {
    activeEditor = null;
    dragOffset = { x: 0, y: 0 };
  }

  function handleSave(value: any) {
    if (!activeEditor) return;
    liveEditStore.updateField(activeEditor.path, value);
    close();
  }
</script>

{#if activeEditor}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div 
    class="fixed inset-0 flex items-center justify-center p-0 md:p-4 bg-slate-950/40 backdrop-blur-md"
    style:z-index={Z_INDEX_ADMIN.PICKER}
    transition:fade
    onclick={close}
  >
    <div 
      class="editor-box bg-[#0a0c10] border-white/10 shadow-[0_50px_100px_rgba(0,0,0,0.9)] overflow-hidden flex flex-col transition-all duration-500
      {activeEditor.type === 'image' || activeEditor.type === 'video' ? 'fixed inset-0 w-full h-full rounded-none' : 'fixed inset-0 w-full h-full md:relative md:w-full md:max-w-2xl md:max-h-[90dvh] md:rounded-[2.5rem] md:border'}
      {isDragging ? 'is-dragging select-none' : ''}"
      style:z-index={Z_INDEX_ADMIN.PICKER_BOX}
      style:transform="translate({dragOffset.x}px, {dragOffset.y}px)"
      transition:fly={{ y: 20, duration: 600 }}
      onclick={(e) => e.stopPropagation()}
    >
      <!-- Header (Hidden for Pure Media Picker) -->
      {#if activeEditor.type !== 'image' && activeEditor.type !== 'video'}
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div 
            class="px-8 py-6 border-b border-white/5 bg-white/[0.02] flex items-center justify-between cursor-grab active:cursor-grabbing select-none"
            onmousedown={handleDragStart}
        >
          <div class="flex items-center gap-4 pointer-events-none">
            <div class="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <RefreshCcw size={20} />
            </div>
            <div>
              <h3 class="text-lg font-black text-white uppercase tracking-widest leading-none">{activeEditor.label}</h3>
              <p class="text-[8px] text-white/20 font-mono mt-1.5 tracking-widest">{activeEditor.path.toUpperCase()}</p>
            </div>
          </div>
          <button 
            onclick={close}
            class="p-3 bg-white/5 hover:bg-white/10 rounded-xl transition-all"
          >
            <X size={20} class="text-white/40" />
          </button>
        </div>
      {/if}

      <!-- Editor Content -->
      <div class="flex-1 custom-scrollbar min-h-0 {activeEditor.type === 'image' || activeEditor.type === 'video' ? 'p-0 overflow-hidden' : 'p-8 overflow-y-auto'}">
        {#if activeEditor.type === 'text' || activeEditor.type === 'html'}
          <TextEditor 
            path={activeEditor.path} 
            type={activeEditor.type} 
            onSave={handleSave} 
          />
        {:else if activeEditor.type === 'image' || activeEditor.type === 'video'}
          <MediaPickerEditor 
            path={activeEditor.path} 
            type={activeEditor.type} 
            onSave={handleSave} 
            onClose={close}
          />
        {:else if activeEditor.type === 'quiz'}
          <QuizEditor
            path={activeEditor.path}
            onSave={handleSave}
          />
        {/if}
      </div>

      <!-- Footer HUD (Hidden for Pure Media Picker) -->
      {#if activeEditor.type !== 'image' && activeEditor.type !== 'video'}
        <div class="px-8 py-4 bg-black/40 border-t border-white/5 flex items-center justify-between text-[7px] font-mono text-white/10 uppercase tracking-[0.3em]">
          <span>ELITE_CORE_EDITOR // V2.2</span>
          <span>PRESS ESC TO DISCARD. CLICK_OUTSIDE TO CANCEL.</span>
        </div>
      {/if}
    </div>
  </div>
{/if}

<style lang="postcss">
  .editor-box {
    animation: box-entry 0.6s cubic-bezier(0.22, 1, 0.36, 1);
  }

  .editor-box.is-dragging {
    transition: none !important;
  }

  @keyframes box-entry {
    from { transform: scale(0.95) translateY(20px); opacity: 0; }
    to { transform: scale(1) translateY(0); opacity: 1; }
  }
</style>
