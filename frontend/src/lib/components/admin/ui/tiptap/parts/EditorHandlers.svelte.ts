/**
 * EditorHandlers.svelte.ts (Elite V2.7)
 * Event handlers and interaction logic for TiptapEditor.
 */
import type { Editor } from '@tiptap/core';

export function createEditorHandlers(state: {
  editor: Editor | null;
  showMediaVault: boolean;
  imageMenuVisible: boolean;
  imageMenuX: number;
  imageMenuY: number;
  onblur: () => void;
}) {
  function handleFocusOut(e: FocusEvent) {
    if (!state.onblur) return;
    const ct = e.currentTarget;
    const rt = e.relatedTarget;
    if (!rt || !(ct instanceof Node) || !ct.contains(rt as Node)) {
      state.onblur();
    }
  }

  function handleImageClick(e: MouseEvent | KeyboardEvent) {
    const target = e.target as HTMLElement;
    let img = target.closest('.tiptap-content img') as HTMLImageElement | null;
    
    if (!img && target.closest('figcaption')) {
      img = target.closest('figure')?.querySelector('img') as HTMLImageElement | null;
    }
    
    if (img && state.editor) {
      state.editor.commands.focus();
      const pos = state.editor.view.posAtDOM(img, 0);
      if (pos >= 0) {
        const rect = img.getBoundingClientRect();
        state.imageMenuX = rect.left + rect.width / 2;
        state.imageMenuY = rect.top;
        state.imageMenuVisible = true;
      }
    } else {
      state.imageMenuVisible = false;
    }
  }

  function handleDoubleClick(e: MouseEvent) {
    const target = e.target as HTMLElement;
    const img = target.closest('.tiptap-content img') as HTMLImageElement | null;
    if (img && state.editor) {
      state.showMediaVault = true;
      state.imageMenuVisible = false;
    }
  }

  return {
    handleFocusOut,
    handleImageClick,
    handleDoubleClick
  };
}
