import { Plugin, PluginKey } from '@tiptap/pm/state';
import type { EditorState, Transaction } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';
import type { EditorView } from '@tiptap/pm/view';
import { Extension } from '@tiptap/core';
import { ReplaceStep } from '@tiptap/pm/transform';
import type { EditorAnnotation } from '$lib/types';
import type { Node as ProseMirrorNode } from '@tiptap/pm/model';

export const AnnotationPluginKey = new PluginKey('xohi-annotation-plugin');

export interface AnnotationPluginState {
  annotations: EditorAnnotation[];
  decorations: DecorationSet;
}

/**
 * Cerberus 2026: Position-Safe Highlighting Plugin
 * Uses Decorations instead of Marks to ensure document integrity and support overlapping highlights.
 */
export const AnnotationPlugin = () => {
  return new Plugin<AnnotationPluginState>({
    key: AnnotationPluginKey,
    state: {
      init(_: unknown, { doc }: { doc: ProseMirrorNode }): AnnotationPluginState {
        return {
          annotations: [],
          decorations: DecorationSet.empty,
        };
      },
      apply(tr: Transaction, value: AnnotationPluginState, oldState: EditorState, newState: EditorState): AnnotationPluginState {
        const meta = tr.getMeta(AnnotationPluginKey);
        if (meta && meta.type === 'SET_ANNOTATIONS') {
          return {
            annotations: meta.annotations,
            decorations: createDecorations(newState.doc as ProseMirrorNode, meta.annotations),
          };
        }
        // Map positions for typing/selection. setContent triggers SET_ANNOTATIONS from content sync.
        return {
          ...value,
          decorations: value.decorations.map(tr.mapping, tr.doc),
        };
      },
    },
    props: {
      decorations(state: EditorState) {
        return AnnotationPluginKey.getState(state)?.decorations;
      },
      handleDOMEvents: {
        mousemove(view: EditorView, event: MouseEvent) {
          // Rule R82.47: Tooltip Capture — Centralized event handling
          const target = event.target as Node;
          const targetEl = target.nodeType === 3 ? (target.parentElement as HTMLElement) : (target as HTMLElement);
          
          if (!targetEl) return false;
          const decoEl = targetEl.closest('.xohi-annotation') as HTMLElement;

          if (decoEl) {
            const id = decoEl.getAttribute('data-annotation-id');
            const type = decoEl.getAttribute('data-annotation-type');
            const message = decoEl.getAttribute('data-annotation-message');
            const source = decoEl.getAttribute('data-annotation-source');
            const severity = decoEl.getAttribute('data-annotation-severity');
            
            // Recover positions from attributes to be 100% safe
            const from = parseInt(decoEl.getAttribute('data-from') || '0');
            const to = parseInt(decoEl.getAttribute('data-to') || '0');
            
            // Get snippet text
            let text = "";
            try {
              text = view.state.doc.textBetween(from, to);
            } catch (err: unknown) {
              console.warn("[Neural Annotation] Position capture mismatch:", err);
            }

            const customEvent = new CustomEvent('annotation-hover', {
              detail: {
                x: event.clientX,
                y: event.clientY,
                id,
                type,
                message,
                source,
                severity,
                text,
                from,
                to
              },
              bubbles: true,
              cancelable: true,
              composed: true
            });
            view.dom.dispatchEvent(customEvent);
          } else if (targetEl && (targetEl.classList.contains('tiptap-content') || targetEl.closest('.tiptap-content'))) {
            view.dom.dispatchEvent(new CustomEvent('annotation-leave', { bubbles: true, composed: true }));
          }
          return false;
        },
        mouseleave(view: EditorView) {
          view.dom.dispatchEvent(new CustomEvent('annotation-leave', { bubbles: true, composed: true }));
          return false;
        }
      }
    },
  });
};

/**
 * Tiptap Extension wrapper for the Annotation Plugin.
 */
export const AnnotationExtension = Extension.create({
  name: 'annotationPlugin',

  addProseMirrorPlugins() {
    return [AnnotationPlugin()];
  },
});

/**
 * Creates DecorationSet by scanning the document for all annotation occurrences.
 * CNS V93: Ultra-stable 1:1 Position Mapping & Overlap Merging.
 */
function createDecorations(doc: ProseMirrorNode, annotations: EditorAnnotation[]): DecorationSet {
  const decorations: Decoration[] = [];
  if (!annotations.length) return DecorationSet.empty;

  // Simple normalization that preserves character length (essential for 1:1 map)
  const normalizeForSearch = (text: string) => {
    return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  };

  console.log(`[AnnotationPlugin] createDecorations called with ${annotations.length} annotations.`);

  let searchBuffer = '';
  const posMap: number[] = [];

  // 1. Build Search Buffer & Position Map (Ignoring Whitespace for Robust Matching)
  // [CNS V95] Map only non-whitespace characters to ignore formatting differences.
  doc.descendants((node: ProseMirrorNode, pos: number) => {
    if (node.isText && node.text) {
      const text = node.text;
      const normalizedText = normalizeForSearch(text);
      for (let i = 0; i < text.length; i++) {
        // Only index non-whitespace characters
        if (!/^\s*$/.test(normalizedText[i])) {
          searchBuffer += normalizedText[i];
          posMap.push(pos + i);
        }
      }
    } else if (node.isBlock || node.type.name === 'hardBreak') {
      // Use a special boundary character that won't match any normal word
      searchBuffer += ' '; 
      // Push the pos so posMap stays aligned with searchBuffer length
      posMap.push(pos);
    }
  });

  for (const ann of annotations) {
    if (!ann.text || ann.text.length < 3) continue;

    let plainPattern = ann.text.replace(/<[^>]+>/g, '');
    const aiPrefixes = [
      /^các mục:\s*/i, /^đoạn văn:\s*/i, /^nội dung:\s*/i, /^phần:\s*/i,
      /^vấn đề:\s*/i, /^câu:\s*/i, /^dòng:\s*/i, /^từ:\s*/i
    ];
    for (const prefix of aiPrefixes) {
      plainPattern = plainPattern.replace(prefix, '');
    }

    // Strip whitespace from pattern to match the stripped buffer
    const normalizedPattern = normalizeForSearch(plainPattern).replace(/\s/g, '');
    if (normalizedPattern.length < 4) continue;

    let matchCount = 0;
    let startIdx = 0;

    // Exact Match Scan using 1:1 buffer
    while ((startIdx = searchBuffer.indexOf(normalizedPattern, startIdx)) !== -1) {
      const endIdx = startIdx + normalizedPattern.length - 1;
      const totalFrom = posMap[startIdx];
      const totalTo = posMap[Math.min(posMap.length - 1, endIdx)] + 1;
      
      const severity = (ann.severity || 'medium').toLowerCase();
      const type = (ann.type || 'unknown').toLowerCase();

      const baseAttrs = {
        class: `xohi-annotation type-${type} severity-${severity}`,
        'data-annotation-id': `deco-${type}-${totalFrom}-${matchCount}`,
        'data-annotation-type': type,
        'data-annotation-message': ann.message,
        'data-annotation-source': ann.source || '',
        'data-annotation-severity': severity,
        'data-from': totalFrom,
        'data-to': totalTo
      };

      doc.nodesBetween(totalFrom, totalTo, (node, pos) => {
        if (node.isText) {
          const start = Math.max(totalFrom, pos);
          const end = Math.min(totalTo, pos + node.nodeSize);
          if (start < end) {
            decorations.push(Decoration.inline(start, end, baseAttrs));
          }
        }
      });

      matchCount++;
      startIdx += 1;
    }
  }

  // 2. Canonical Sort & Filter (CRITICAL: ProseMirror fails on invalid overlaps)
  decorations.sort((a, b) => {
    if (a.from !== b.from) return a.from - b.from;
    return a.to - b.to;
  });

  // Filter out exact duplicates to prevent rendering errors
  const finalDecorations = decorations.filter((deco, idx, self) => {
    if (idx === 0) return true;
    const prev = self[idx - 1];
    return !(deco.from === prev.from && deco.to === prev.to && (deco.spec as any).class === (prev.spec as any).class);
  });

  console.log(`[Neural Annotation] Applied ${finalDecorations.length} total highlights.`);
  return DecorationSet.create(doc, finalDecorations);
}

