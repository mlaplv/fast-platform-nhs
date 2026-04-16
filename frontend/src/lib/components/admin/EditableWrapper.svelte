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
    value?: string; // Elite V2.2: Explicit initial value to prevent DOM-scraping doubling
    class?: string;
    children?: import('svelte').Snippet;
  }

  let { path, type = 'text', label = 'SỬA NỘI DUNG', value: explicitValue, children, ...props }: Props = $props();

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

  const getValue = (p: string, fallback = ""): string => {
    if (!liveEditStore.dirtyProduct) return fallback;
    try {
        const keys = p.split(".");
        let current: any = liveEditStore.dirtyProduct as Product;
        for (const key of keys) {
            if (current === null || current === undefined || typeof current !== 'object') return fallback;
            current = (current as any)[key];
        }
        return (current as string) ?? fallback;
    } catch {
        return fallback;
    }
  };

  function triggerHaptic(strength = 10) {
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      navigator.vibrate(strength);
    }
  }

  function handleEditClick(e: MouseEvent | TouchEvent) {
    if (!isEditMode) return;
    if (e.cancelable) e.preventDefault();
    e.stopPropagation();
    
      // For text/html, use inline editing
    if (type === 'text' || type === 'html') {
      triggerHaptic(15);
      liveEditStore.activePath = path;
      // Elite V2.2: Intelligent Value Resolution
      // 1. Priority: Explicit prop (Best for complex structures)
      // 2. Fallback: Store value (Database source)
      // 3. Last Resort: DOM Scraper (Guess from screen)
      const storeValue = getValue(path, null as any);
      let rawValue = explicitValue ?? storeValue;
      
      if (rawValue === null || rawValue === undefined) {
         const container = wrapperRef?.querySelector('.content-container');
         rawValue = container?.innerHTML?.trim() || "";
         
         // Elite V2.2: Anti-Doubling Guard
         // If we are scraping but found structural HTML (div, span, h3) and the type is text, 
         // it means we are accidentally capturing the whole wrapper. Discard it.
         if (type === 'text' && rawValue.includes('<') && (rawValue.includes('<div') || rawValue.includes('<span') || rawValue.includes('<h3'))) {
            rawValue = "";
         }
      }
      
      rawValue = String(rawValue);
      
      // Elite V2.2: Clean up 'overload' (Svelte internal classes and noise)
      if (type === 'html' || type === 'text') {
          // Remove Svelte scoped classes (s-XXXXX)
          rawValue = rawValue.replace(/\s+s-[a-zA-Z0-9_-]+/g, "");
          // Remove empty class attributes
          rawValue = rawValue.replace(/class=""/g, "");
          // Elite V2.2: Strip Sakura Pink spans and any other stylistic spans to ensure clean editing experience
          // This prevents the "nested span" nightmare reported by the Boss
          rawValue = rawValue.replace(/<span[^>]*class=["']text-sakura-pink["'][^>]*>/gi, "")
                             .replace(/<span[^>]*>/gi, "") // Neutralize all spans
                             .replace(/<\/span>/gi, "");
          
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
    
    try {
        let finalValue = inlineValue;
        if (type === 'html') {
            // Convert newlines back to BR tags for correct HTML rendering
            const lines = inlineValue.split('\n');
            if (lines.length > 1) {
                // Apply pink color to the second line automatically if it's the banner headline
                if (path.includes('hero_headline')) {
                    // Clean lines to ensure no residual tags before wrapping
                    const line1 = lines[0].replace(/<\/?[^>]+(>|$)/g, "").trim();
                    const line2 = lines.slice(1).join(' ').replace(/<\/?[^>]+(>|$)/g, "").trim();
                    finalValue = `${line1}<br/><span class="text-sakura-pink">${line2}</span>`;
                } else {
                    finalValue = lines.join('<br/>');
                }
            }
        }
        
        liveEditStore.updateField(path, finalValue);
        
        // Show success feedback
        showSuccessFlash = true;
        setTimeout(() => { showSuccessFlash = false; }, 1000);
    } catch (e) {
        console.error("EditableWrapper: Save failed:", e);
    } finally {
        isInlineEditing = false;
        liveEditStore.activePath = null;
    }
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
  class="editable-wrapper relative group/editable {isEditMode ? 'cursor-pointer' : ''} {showSuccessFlash ? 'success-flash' : ''} {props.class || ''}"
  onmouseenter={() => isHovered = true}
  onmouseleave={() => isHovered = false}
  onclick={handleEditClick}
  ontouchend={handleEditClick}
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
            
            <!-- Fixed Editor Overlay (Responsive HUD) -->
            <div 
                class="fixed inset-0 flex items-end md:items-center justify-center md:pb-6 pointer-events-none" 
                style:z-index={Z_INDEX_ADMIN.EDITOR}
                transition:fade={{ duration: 250 }}
            >
                <!-- Mobile BottomSheet (Native App Feel) / Desktop Box (Elite Glass) -->
                <div class="relative w-full md:max-w-3xl h-[85dvh] md:h-auto bg-black md:bg-[#0d1117] rounded-t-[40px] md:rounded-[40px] shadow-[0_-15px_60px_rgba(0,0,0,0.9)] md:shadow-[0_40px_120px_rgba(0,0,0,0.9)] overflow-hidden flex flex-col pointer-events-auto animate-editor-reveal">
                    
                    <!-- Elite Mobile Drag Handle -->
                    <div class="md:hidden w-full flex justify-center pt-5 pb-3">
                        <div class="w-10 h-1 bg-white/20 rounded-full"></div>
                    </div>

                    <!-- Lean Header Toolbar (Top-Right Action) -->
                    <div class="flex items-center justify-between px-8 py-4 md:border-b border-white/5 bg-transparent md:bg-slate-900/50 backdrop-blur-sm">
                        <span class="text-[10px] font-black text-white/30 uppercase tracking-[0.3em] italic">{label}</span>
                        <div class="flex items-center gap-4">
                            <button class="text-white/40 text-[10px] font-black uppercase tracking-widest hover:text-white transition-colors" onclick={() => { triggerHaptic(5); cancelInline(); }}>HỦY</button>
                            <button class="bg-blue-600 text-white text-[10px] font-black px-8 py-3 rounded-full shadow-[0_0_20px_rgba(59,130,246,0.5)] active:scale-95 flex items-center gap-2 uppercase tracking-widest" onclick={() => { triggerHaptic(20); saveInline(); }}>
                                <Check size={14} strokeWidth={4} />
                                XONG
                            </button>
                        </div>
                    </div>

                    <div class="flex-1 p-8 md:p-14 overflow-y-auto">
                        <textarea
                            bind:value={inlineValue}
                            autofocus
                            onblur={() => setTimeout(saveInline, 100)}
                            onkeydown={handleKeydown}
                            oninput={(e) => autoResize(e.currentTarget)}
                            class="inline-edit-ta w-full h-full bg-transparent text-white outline-none font-sans resize-none transition-all placeholder:text-white/5"
                            style="font-size: 1.25rem; line-height: 1.5; font-weight: 500; text-align: left;"
                            placeholder="Chạm để bắt đầu nhập..."
                        ></textarea>
                    </div>

                    <!-- Bottom Safety Pad for Mobile -->
                    <div class="h-10 md:hidden bg-transparent"></div>
                </div>
            </div>
        </div>
    {:else if !shouldHideHUD}
        <!-- Elite V2.2: Precision Focus Frame -->
        <div 
            class="absolute -inset-2 border md:border-blue-500/0 border-blue-500/40 md:group-hover/editable:border-blue-500/40 rounded-xl transition-all duration-300 pointer-events-none overflow-visible"
            style:z-index={Z_INDEX_ADMIN.HUD}
        >
          <!-- Glow Corner Tags -->
          <div class="absolute -top-1 -left-1 w-2 h-2 bg-blue-500 rounded-full opacity-100 md:opacity-0 md:group-hover/editable:opacity-100 shadow-[0_0_10px_#3b82f6]"></div>
          
          <!-- Label HUD (Elite Adaptive Design) -->
          <div class="absolute bottom-full left-0 mb-2 opacity-100 md:opacity-0 md:group-hover/editable:opacity-100 transition-opacity flex items-center gap-2 bg-blue-600 md:px-3 md:py-1 p-1.5 rounded-full whitespace-nowrap shadow-xl">
            {#if type === 'image' || type === 'video'}
                <ImageIcon size={12} class="text-white" />
            {:else if type === 'quiz'}
                <Settings2 size={12} class="text-white" />
            {:else}
                <Edit size={12} class="text-white" />
            {/if}
            <span class="text-[8px] font-black text-white uppercase tracking-widest hidden md:inline">{label}</span>
          </div>
        </div>
        
        <!-- Pulse Overlay -->
        <div class="absolute inset-0 bg-blue-500/5 opacity-100 md:opacity-0 md:group-hover/editable:opacity-100 transition-opacity rounded-lg pointer-events-none"></div>
    {/if}
  {/if}

  <div class="content-container w-full h-full {isInlineEditing ? 'opacity-20 blur-sm pointer-events-none' : ''} transition-all duration-300 relative" style:display={isEditMode ? 'contents' : 'block'}>
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
    animation: editor-reveal 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }

  @keyframes editor-reveal {
    from { opacity: 0; transform: translateY(100%); }
    to { opacity: 1; transform: translateY(0); }
  }
</style>
