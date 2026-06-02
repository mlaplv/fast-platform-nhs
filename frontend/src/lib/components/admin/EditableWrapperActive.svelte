<script lang="ts">
  import { liveEditStore } from "$lib/state/commerce/liveEdit.svelte";
  import Edit from "@lucide/svelte/icons/edit";
  import ImageIcon from "@lucide/svelte/icons/image";
  import Settings2 from "@lucide/svelte/icons/settings-2";
  import Check from "@lucide/svelte/icons/check";
  import Eye from "@lucide/svelte/icons/eye";
  import EyeOff from "@lucide/svelte/icons/eye-off";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/zIndex";

  interface Props {
    path: string;
    type?: 'text' | 'html' | 'image' | 'video' | 'quiz' | 'metrics';
    label?: string;
    value?: string; 
    class?: string;
    as?: 'div' | 'span';
    children?: import('svelte').Snippet;
  }

  let { path, type = 'text', label = 'SỬA NỘI DUNG', value: explicitValue, as = 'div', children, ...props }: Props = $props();

  const isEditMode = $derived(liveEditStore.isEditMode);

  let isInlineEditing = $state(false);
  let inlineValue = $state("");
  let wrapperRef = $state<HTMLElement | null>(null);
  let taRef = $state<HTMLTextAreaElement | null>(null);

  let showSuccessFlash = $state(false);
  let isCancelling = false;
  let isCooldown = false;

  const activePath = $derived(liveEditStore.activePath);
  const isTargetOfFocus = $derived(activePath === path);
  const shouldHideHUD = $derived(activePath !== null && !isTargetOfFocus);

  // Auto-close if another wrapper is focused
  $effect(() => {
    if (isInlineEditing && activePath !== path) {
        isInlineEditing = false;
    }
  });

  const currentValue = $derived(getValue(path, explicitValue || ""));
  const isDisabled = $derived(String(currentValue).startsWith('[OFF]'));

  function getValue(p: string, fallback = ""): string {
    const product = liveEditStore.dirtyProduct;
    if (!product) return fallback;
    
    try {
        const normalizedPath = p.replace(/\[(\d+)\]/g, '.$1');
        const keys = normalizedPath.split(".");
        let current: unknown = product;
        for (const key of keys) {
            if (current === null || current === undefined || typeof current !== 'object') return fallback;
            current = (current as Record<string, unknown>)[key];
        }
        return (current as string) ?? fallback;
    } catch (err) {
        console.warn(`[EditableWrapperActive] Lỗi khi lấy giá trị đường dẫn ${p}:`, err);
        return fallback;
    }
  }

  function triggerHaptic(strength = 10) {
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      navigator.vibrate(strength);
    }
  }

  function handleEditClick(e: MouseEvent | TouchEvent) {
    if (!isEditMode) return;
    if (isInlineEditing || isCooldown || (typeof window !== 'undefined' && (window as any)._agEditLock)) {
        e.stopPropagation();
        return;
    }
    if (e.cancelable) e.preventDefault();
    e.stopPropagation();
    
    if (type === 'text' || type === 'html') {
      triggerHaptic(15);
      liveEditStore.activePath = path;
      const storeValue = getValue(path, "");
      let rawValue = explicitValue ?? storeValue;
      
      if (!rawValue) {
         const container = wrapperRef?.querySelector('.content-container');
         rawValue = container?.innerHTML?.trim() || "";
      }
      
      rawValue = String(rawValue);
      if (type === 'html' || type === 'text') {
          rawValue = rawValue.replace(/\s+s-[a-zA-Z0-9_-]+/g, "");
          rawValue = rawValue.replace(/class=""/g, "");
          rawValue = rawValue.replace(/<span[^>]*class=["']text-sakura-pink["'][^>]*>/gi, "")
                             .replace(/<span[^>]*>/gi, "")
                             .replace(/<\/span>/gi, "");
          
          if (type === 'html') {
              rawValue = rawValue.replace(/<br\s*\/?>/gi, '\n');
              if (rawValue.startsWith('<p') && rawValue.endsWith('</p>') && (rawValue.match(/<p/g) || []).length === 1) {
                  rawValue = rawValue.replace(/^<p[^>]*>/, '').replace(/<\/p>$/, '');
              }
          } else {
              rawValue = rawValue.replace(/<\/?[^>]+(>|$)/g, "");
          }
      }
      
      inlineValue = rawValue;
      isInlineEditing = true;
      isCancelling = false;
      return;
    }

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
        let finalValue = taRef ? taRef.value : inlineValue;
        if (type === 'html') {
            const lines = finalValue.split('\n');
            if (lines.length > 1) {
                if (path.includes('hero_headline')) {
                    const line1 = lines[0].replace(/<\/?[^>]+(>|$)/g, "").trim();
                    const line2 = lines.slice(1).join(' ').replace(/<\/?[^>]+(>|$)/g, "").trim();
                    finalValue = `${line1}<br/><span class="text-sakura-pink">${line2}</span>`;
                } else {
                    finalValue = lines.join('<br/>');
                }
            }
        }
        liveEditStore.updateField(path, finalValue);
        showSuccessFlash = true;
        setTimeout(() => { showSuccessFlash = false; }, 1000);
    } catch (e) {
        console.error("EditableWrapperActive: Save failed:", e);
    } finally {
        isInlineEditing = false;
        liveEditStore.activePath = null;
        if (typeof window !== 'undefined') {
            (window as any)._agEditLock = true;
            setTimeout(() => { (window as any)._agEditLock = false; }, 400);
        }
        isCooldown = true;
        setTimeout(() => { isCooldown = false; }, 300);
    }
  }

  function cancelInline() {
    isCancelling = true;
    isInlineEditing = false;
    liveEditStore.activePath = null;
    if (typeof window !== 'undefined') {
        (window as any)._agEditLock = true;
        setTimeout(() => { (window as any)._agEditLock = false; }, 400);
    }
    isCooldown = true;
    setTimeout(() => { isCooldown = false; }, 300);
  }

  let isResizing = false;
  function autoResize(node: HTMLTextAreaElement) {
    if (isResizing) return;
    isResizing = true;
    requestAnimationFrame(() => {
        node.style.height = 'auto';
        node.style.height = node.scrollHeight + 'px';
        isResizing = false;
    });
  }

  function toggleDisabled(e: MouseEvent | TouchEvent) {
    e.stopPropagation();
    e.preventDefault();
    triggerHaptic(25);
    
    let val = String(currentValue);
    if (val.startsWith('[OFF]')) {
        val = val.substring(5);
    } else {
        val = '[OFF]' + val;
    }
    
    liveEditStore.updateField(path, val);
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

  function initResize(node: HTMLTextAreaElement) {
    node.value = inlineValue;
    setTimeout(() => autoResize(node), 10);
  }
</script>

<svelte:element
  this={as}
  bind:this={wrapperRef}
  class="editable-wrapper group/editable cursor-pointer {isDisabled ? 'is-disabled' : ''} {showSuccessFlash ? 'success-flash' : ''} {as === 'span' ? 'inline' : 'block'} {props.class || ''}"
  style="position: relative; z-index: {isInlineEditing ? 999999 : 'auto'};"
  onclick={handleEditClick}
  ontouchend={handleEditClick}
  role="presentation"
>
  {#if isInlineEditing}
      <div class="relative w-full h-full pointer-events-auto flex flex-col" style="z-index: 999999;" onclick={(e) => e.stopPropagation()} ontouchend={(e) => e.stopPropagation()} onpointerdown={(e) => e.stopPropagation()} role="presentation">
          <textarea bind:this={taRef} use:initResize autofocus onkeydown={handleKeydown} oninput={(e) => autoResize(e.currentTarget as HTMLTextAreaElement)} class="w-full bg-transparent text-white outline-none font-sans resize-none placeholder:text-white/20 p-0 m-0 border-none transition-colors relative z-[999999]" style="font-size: inherit; line-height: inherit; font-weight: inherit; text-align: inherit; min-height: 1.5em; overflow: hidden;" placeholder="Nhập văn bản..."></textarea>
          
          <div class="mt-2 ml-auto flex items-center gap-1 p-1 bg-slate-900/95 backdrop-blur-md border border-white/10 rounded-lg shadow-xl animate-fade-in w-max relative z-[999999]">
              <button class="text-white/60 hover:text-white text-[10px] font-bold px-3 py-1.5 transition-colors" onclick={(e) => { e.stopPropagation(); cancelInline(); }} ontouchend={(e) => e.stopPropagation()} onpointerdown={(e) => e.stopPropagation()}>HỦY</button>
              <button class="bg-blue-600 text-white text-[10px] font-bold px-3 py-1.5 rounded-md flex items-center gap-1 active:scale-95 transition-transform" onclick={(e) => { e.stopPropagation(); saveInline(); }} ontouchend={(e) => e.stopPropagation()} onpointerdown={(e) => e.stopPropagation()}><Check size={12} strokeWidth={4} /> XONG</button>
          </div>
      </div>
  {:else if !shouldHideHUD}
      <div class="absolute -inset-2 border md:border-blue-500/0 border-blue-500/40 md:group-hover/editable:border-blue-500/40 rounded-xl transition-all duration-300 pointer-events-none overflow-visible" style:z-index={Z_INDEX_ADMIN.HUD}>
        <div class="absolute -top-1 -left-1 w-2 h-2 bg-blue-500 rounded-full opacity-100 md:opacity-0 md:group-hover/editable:opacity-100 shadow-[0_0_10px_#3b82f6]"></div>
        <div class="absolute bottom-full left-0 mb-2 opacity-100 md:opacity-0 md:group-hover/editable:opacity-100 transition-opacity flex items-center gap-2 bg-blue-600 md:px-3 md:py-1 p-1.5 rounded-full whitespace-nowrap shadow-xl pointer-events-auto hud-label-bridge">
          {#if type === 'image' || type === 'video'}
              <ImageIcon size={12} class="text-white" />
          {:else if type === 'quiz'}
              <Settings2 size={12} class="text-white" />
          {:else}
              <Edit size={12} class="text-white" />
          {/if}
          <span class="text-[8px] font-black text-white tracking-widest px-1 min-w-[50px] inline-block">{label}</span>
          
          {#if type === 'text' || type === 'html'}
              <button class="ml-2 pl-2 border-l border-white/20 text-white/60 hover:text-white transition-colors flex items-center gap-1 active:scale-90" onclick={(e) => { e.stopPropagation(); e.preventDefault(); triggerHaptic(15); window.dispatchEvent(new CustomEvent('open-editor', { detail: { path, type, label }, bubbles: true, composed: true })); }} ontouchend={(e) => { e.stopPropagation(); e.preventDefault(); triggerHaptic(15); window.dispatchEvent(new CustomEvent('open-editor', { detail: { path, type, label }, bubbles: true, composed: true })); }} title="Mở trình soạn thảo">
                  <Settings2 size={12} strokeWidth={3} />
              </button>
          {/if}

          <button class="ml-2 pl-2 border-l border-white/20 text-white/60 hover:text-white transition-colors flex items-center gap-1 active:scale-90" onclick={toggleDisabled} ontouchend={toggleDisabled} title={isDisabled ? "Hiện nội dung" : "Ẩn nội dung"}>
              {#if isDisabled}
                  <EyeOff size={12} strokeWidth={3} />
                  <span class="text-[8px] font-bold hidden md:inline">ĐÃ ẨN</span>
              {:else}
                  <Eye size={12} strokeWidth={3} />
                  <span class="text-[8px] font-bold hidden md:inline">ẨN</span>
              {/if}
          </button>
        </div>
      </div>
      <div class="absolute inset-0 bg-blue-500/5 opacity-100 md:opacity-0 md:group-hover/editable:opacity-100 transition-opacity rounded-lg pointer-events-none"></div>
  {/if}

  <svelte:element this={as} class="content-container w-full h-full transition-all duration-300 relative" style:display={isInlineEditing ? 'none' : (as === 'span' ? 'contents' : 'block')}>
    {@render children?.()}
  </svelte:element>
</svelte:element>

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

  :global(.hud-label-bridge)::before {
    content: '';
    position: absolute;
    top: 100%;
    left: 0;
    width: 100%;
    height: 15px;
    background: transparent;
  }

  .animate-fade-in {
    animation: fade-in 0.25s ease-out forwards;
  }

  @keyframes fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
  }
</style>
