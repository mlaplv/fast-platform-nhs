/**
 * AnnotationManager.svelte.ts (Elite V2.7)
 * Logic for handling AI annotations, tooltips, and fixes.
 */
import type { Editor } from '@tiptap/core';

export function createAnnotationManager(options: {
  getOnFix: () => (((snippet: string, type: string, message: string) => Promise<string | null>) | null);
  getEditor: () => Editor | null;
}) {
  const state = $state({
    tooltipVisible: false,
    tooltipText: '',
    tooltipSnippet: '',
    tooltipType: '',
    tooltipId: '',
    tooltipFrom: 0,
    tooltipTo: 0,
    tooltipX: 0,
    tooltipY: 0,
    isFixing: false,
    isHoveringTooltip: false
  });

  let tooltipHideTimeout: ReturnType<typeof setTimeout> | null = null;

  function handleAnnotationHover(e: Event) {
    if (state.isFixing) return;
    if (tooltipHideTimeout) {
      clearTimeout(tooltipHideTimeout);
      tooltipHideTimeout = null;
    }
    const customEvent = e as CustomEvent;
    const data = customEvent.detail;
    if (!data || !data.id) return;

    state.tooltipX = data.x;
    state.tooltipY = data.y - 10;
    state.tooltipText = data.message;
    state.tooltipType = data.type;
    state.tooltipId = data.id;
    state.tooltipSnippet = data.text;
    state.tooltipFrom = data.from;
    state.tooltipTo = data.to;
    state.tooltipVisible = true;
  }

  function handleAnnotationLeave() {
    if (state.isFixing || state.isHoveringTooltip) return;
    
    if (tooltipHideTimeout) clearTimeout(tooltipHideTimeout);
    tooltipHideTimeout = setTimeout(() => {
      if (!state.isHoveringTooltip && !state.isFixing) {
        state.tooltipVisible = false;
      }
    }, 600);
  }

  function handleTooltipEnter() {
    state.isHoveringTooltip = true;
    if (tooltipHideTimeout) {
      clearTimeout(tooltipHideTimeout);
      tooltipHideTimeout = null;
    }
  }

  function handleTooltipLeave() {
    state.isHoveringTooltip = false;
    handleAnnotationLeave();
  }

  async function handleFix() {
    const editor = options.getEditor();
    const onfix = options.getOnFix();
    if (!onfix || state.isFixing || !state.tooltipSnippet || !editor) return;
    state.isFixing = true;
    try {
      const newText = await onfix(state.tooltipSnippet, state.tooltipType, state.tooltipText);
      if (newText) {
        const { state: editorState, view } = editor;
        const tr = editorState.tr.insertText(newText, state.tooltipFrom, state.tooltipTo);
        view.dispatch(tr);
        state.tooltipType = 'fixed';
      }
    } finally {
      state.isFixing = false;
      setTimeout(() => { if (!state.isFixing) state.tooltipVisible = false; }, 1500);
    }
  }

  return {
    state,
    handleAnnotationHover,
    handleAnnotationLeave,
    handleTooltipEnter,
    handleTooltipLeave,
    handleFix
  };
}
