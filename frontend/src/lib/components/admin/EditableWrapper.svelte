<script lang="ts">
  import { liveEditStore } from "$lib/state/commerce/liveEdit.svelte";
  import { fade } from "svelte/transition";
  import { Edit, Image as ImageIcon, Settings2, Check } from "lucide-svelte";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/zIndex";
  import { portal } from "$lib/core/actions/portal";

  interface Props {
    path: string;
    type?: 'text' | 'html' | 'image' | 'video' | 'quiz' | 'metrics';
    label?: string;
    children?: import('svelte').Snippet;
  }

  let { path, type = 'text', label = 'SỬA NỘI DUNG', children }: Props = $props();

  const isEditMode = $derived(liveEditStore.isEditMode);
  const isAdmin = $derived(liveEditStore.isAdmin);

  let isHovered = $state(false);
  let isInlineEditing = $state(false);
  let inlineValue = $state("");
  let wrapperRef = $state<HTMLElement | null>(null);

  let showSuccessFlash = $state(false);
  let isCancelling = false;

  const activePath = $derived(liveEditStore.activePath);
  const isTargetOfFocus = $derived(activePath === path);
  const shouldHideHUD = $derived(activePath !== null && !isTargetOfFocus);

  const getValue = (p: string, fallback = "") => {
    if (!liveEditStore.dirtyProduct) return fallback;
    const keys = p.split(".");
    let current: any = liveEditStore.dirtyProduct;
    for (const key of keys) {
        if (!current || typeof current !== 'object') return fallback;
        current = current[key];
    }
    return current || fallback;
  };

  function handleEditClick(e: MouseEvent) {
    if (!isEditMode) return;
    e.preventDefault();
    e.stopPropagation();
    
      // For text/html, use inline editing
    if (type === 'text' || type === 'html') {
      liveEditStore.activePath = path;
      // Elite V2.2: Capture current screen text as fallback if store is empty
      const container = wrapperRef?.querySelector('.content-container');
      const currentHTML = container?.innerHTML || "";
      let rawValue = getValue(path, currentHTML.trim());
      
      // Elite V2.2: Clean up 'overload' (Svelte internal classes and noise)
      if (type === 'html' || type === 'text') {
          // Remove Svelte scoped classes (s-XXXXX)
          rawValue = rawValue.replace(/\s+s-[a-zA-Z0-9_-]+/g, "");
          // Remove empty class attributes
          rawValue = rawValue.replace(/class=""/g, "");
          // For 'html' type we preserve structure but convert BRs to newlines
          if (type === 'html') {
              rawValue = rawValue.replace(/<br\s*\/?>/gi, '\n');
              // If it's a simple paragraph wrap, strip it for cleaner editing
              if (rawValue.startsWith('<p') && rawValue.endsWith('</p>') && (rawValue.match(/<p/g) || []).length === 1) {
                  rawValue = rawValue.replace(/^<p[^>]*>/, '').replace(/<\/p>$/, '');
              }
          } else {
              // For 'text' type we strip ALL tags
              rawValue = rawValue.replace(/<\/?[^>]+(>|$)/g, "");
          }
      }
      
      inlineValue = rawValue;
      isInlineEditing = true;
      isCancelling = false;
      return;
    }

    // Dispatch custom event for the parent to handle specific types of editing
    const event = new CustomEvent('open-editor', {
      detail: { path, type, label },
      bubbles: true,
      composed: true
    });
    window.dispatchEvent(event);
  }

  function saveInline() {
    if (isCancelling) return;
    
    let finalValue = inlineValue;
    if (type === 'html') {
        // Convert newlines back to BR tags for correct HTML rendering
        const lines = inlineValue.split('\n');
        if (lines.length > 1) {
            // Apply pink color to the second line automatically if it's the banner headline
            if (path.includes('hero_headline')) {
                finalValue = `${lines[0]}<br/><span class="text-sakura-pink">${lines.slice(1).join(' ')}</span>`;
            } else {
                finalValue = lines.join('<br/>');
            }
        }
    }
    
    liveEditStore.updateField(path, finalValue);
    isInlineEditing = false;
    liveEditStore.activePath = null;
    
    // Show success feedback
    showSuccessFlash = true;
    setTimeout(() => { showSuccessFlash = false; }, 1000);
  }

  function cancelInline() {
    isCancelling = true;
    isInlineEditing = false;
    liveEditStore.activePath = null;
  }

  function autoResize(node: HTMLTextAreaElement) {
    node.style.height = 'auto';
    node.style.height = node.scrollHeight + 'px';
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
        cancelInline();
    }
    if (e.key === 'Enter' && !e.shiftKey && type === 'text') {
        e.preventDefault();
        saveInline();
    }
  }

  $effect(() => {
    if (isInlineEditing) {
        const ta = document.querySelector('.inline-edit-ta') as HTMLTextAreaElement;
        if (ta) autoResize(ta);
    }
  });
</script>

<div 
  bind:this={wrapperRef}
  class="editable-wrapper relative group/editable {isEditMode ? 'cursor-pointer' : ''} {showSuccessFlash ? 'success-flash' : ''}"
  onmouseenter={() => isHovered = true}
  onmouseleave={() => isHovered = false}
  onclick={handleEditClick}
  role="presentation"
>
  {#if isAdmin && isEditMode}
    {#if isInlineEditing}
        <!-- Elite V2.2: PORTAL HUD (ARCHITECTURAL ESCAPE) -->
        <div use:portal>
            <!-- Fixed Backdrop -->
            <div 
                class="fixed inset-0 bg-slate-950/80 backdrop-blur-md" 
                style:z-index={Z_INDEX_ADMIN.BACKDROP}
                transition:fade={{ duration: 250 }} 
                onclick={saveInline} 
                role="presentation"
            ></div>
            
            <!-- Fixed Editor Overlay (Centered) -->
            <div 
                class="fixed inset-0 flex items-center justify-center p-6 pointer-events-none" 
                style:z-index={Z_INDEX_ADMIN.EDITOR}
                transition:fade={{ duration: 200 }}
            >
                <div class="relative w-full max-w-3xl pointer-events-auto animate-editor-reveal">
                    <textarea
                        bind:value={inlineValue}
                        autofocus
                        onblur={() => setTimeout(saveInline, 100)}
                        onkeydown={handleKeydown}
                        oninput={(e) => autoResize(e.currentTarget)}
                        class="inline-edit-ta w-full bg-[#0d1117] text-white border-2 border-blue-500/50 rounded-3xl p-10 outline-none shadow-[0_40px_120px_rgba(0,0,0,0.9),0_0_60px_rgba(59,130,246,0.2)] font-sans resize-none overflow-hidden transition-all focus:border-blue-500"
                        style="font-size: 1.25rem; line-height: 1.6; font-weight: 500; text-align: left; min-height: 160px;"
                    ></textarea>
                    
                    <!-- Elite Toolbar -->
                    <div class="absolute -bottom-4 right-8 flex gap-3">
                        <button class="bg-blue-600 text-white text-[11px] font-black px-8 py-4 rounded-2xl shadow-2xl hover:bg-blue-500 transition-all active:scale-95 flex items-center gap-3 uppercase tracking-[0.2em]" onclick={saveInline}>
                            <Check size={16} strokeWidth={3} />
                            LƯU THAY ĐỔI
                        </button>
                        <button class="bg-slate-800 text-white/40 text-[11px] font-black px-8 py-4 rounded-2xl hover:bg-slate-700 hover:text-white/70 transition-all active:scale-95 uppercase tracking-[0.2em]" onclick={cancelInline}>HỦY (ESC)</button>
                    </div>
                </div>
            </div>
        </div>
    {:else if !shouldHideHUD}
        <!-- Elite V2.2: Precision Focus Frame -->
        <div 
            class="absolute -inset-2 border border-blue-500/0 group-hover/editable:border-blue-500/40 rounded-xl transition-all duration-300 pointer-events-none overflow-visible"
            style:z-index={Z_INDEX_ADMIN.HUD}
        >
          <!-- Glow Corner Tags -->
          <div class="absolute -top-1 -left-1 w-2 h-2 bg-blue-500 rounded-full opacity-0 group-hover/editable:opacity-100 shadow-[0_0_10px_#3b82f6]"></div>
          
          <!-- Label HUD -->
          <div class="absolute bottom-full left-0 mb-2 opacity-0 group-hover/editable:opacity-100 transition-opacity flex items-center gap-2 bg-blue-600 px-3 py-1 rounded-full whitespace-nowrap shadow-xl">
            {#if type === 'image' || type === 'video'}
                <ImageIcon size={10} class="text-white" />
            {:else if type === 'quiz'}
                <Settings2 size={10} class="text-white" />
            {:else}
                <Edit size={10} class="text-white" />
            {/if}
            <span class="text-[8px] font-black text-white uppercase tracking-widest">{label}</span>
          </div>
        </div>
        
        <!-- Pulse Overlay -->
        <div class="absolute inset-0 bg-blue-500/5 opacity-0 group-hover/editable:opacity-100 transition-opacity rounded-lg pointer-events-none"></div>
    {/if}
  {/if}

  <div class="content-container {isInlineEditing ? 'opacity-20 blur-sm pointer-events-none' : ''} transition-all duration-300" style="display: contents;">
    {@render children?.()}
  </div>
</div>

<style lang="postcss">
  .editable-wrapper {
     transition: all 0.3s ease;
  }
  
  .success-flash {
    animation: success-pulse 1s ease;
  }

  @keyframes success-pulse {
    0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
    30% { transform: scale(1.02); box-shadow: 0 0 30px 10px rgba(34, 197, 94, 0.4); }
    100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
  }

  .animate-editor-reveal {
    animation: editor-reveal 0.4s cubic-bezier(0.23, 1, 0.32, 1) forwards;
  }

  @keyframes editor-reveal {
    from { opacity: 0; transform: scale(0.95) translateY(10px); }
    to { opacity: 1; transform: scale(1) translateY(0); }
  }
</style>
