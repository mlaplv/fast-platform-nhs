import { Plugin, PluginKey } from '@tiptap/pm/state';
import type { EditorState, Transaction } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';
import type { EditorView } from '@tiptap/pm/view';
import { Extension } from '@tiptap/core';
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
        // Handle metadata updates for annotations
        const meta = tr.getMeta(AnnotationPluginKey);
        if (meta && meta.type === 'SET_ANNOTATIONS') {
          return {
            annotations: meta.annotations,
            decorations: createDecorations(newState.doc as ProseMirrorNode, meta.annotations),
          };
        }

        // Map decorations on document changes (ProseMirror magic)
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
            } catch (e) {}

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
 */
function createDecorations(doc: ProseMirrorNode, annotations: EditorAnnotation[]): DecorationSet {
  const decorations: Decoration[] = [];
  if (!annotations.length) return DecorationSet.empty;

  // Rule R82.45: Position-Safe Normalization
  const isAlphaNum = (c: string) => /\p{L}|\p{N}/u.test(c);

  // 1. Build a searchable normalized buffer of the doc
  // Cerberus 2026: Surgical Position Mapping
  let fullText = '';
  const posMap: number[] = [];

  doc.descendants((node: ProseMirrorNode, pos: number) => {
    if (node.isText && node.text) {
      const text = node.text;
      for (let i = 0; i < text.length; i++) {
        const char = text[i];
        // Rules R82/R03: Maximum Vietnamese standard (NFC) + Whitespace Normalization
        // TipTap/ProseMirror often uses \u00A0 (NBSP)
        const normalizedChar = char
          .normalize('NFC')
          .replace(/[\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000]/g, ' ')
          .toLowerCase();
        fullText += normalizedChar;
        posMap.push(pos + i);
      }
    } else if (node.isBlock) {
      fullText += '\n';
      posMap.push(pos);
    }
  });

  // 2. Scan for each annotation
  for (const ann of annotations) {
    if (!ann.text || ann.text.length < 3) continue;

    const pattern = ann.text
      .normalize('NFC')
      .replace(/[\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000]/g, ' ')
      .toLowerCase();

    // Find ALL occurrences (Fixes the "5 vs 2" reported mismatch)
    let startIdx = 0;
    while ((startIdx = fullText.indexOf(pattern, startIdx)) !== -1) {
      const startPos = posMap[startIdx];
      const endPos = posMap[startIdx + pattern.length - 1] + 1;

      if (startPos !== undefined && endPos !== undefined) {
        decorations.push(
          Decoration.inline(startPos, endPos, {
            class: `xohi-annotation type-${ann.type} severity-${ann.severity || 'medium'}`,
            'data-annotation-id': `deco-${ann.type}-${startPos}-${Math.random().toString(36).slice(2, 6)}`,
            'data-annotation-type': ann.type,
            'data-annotation-message': ann.message,
            'data-annotation-source': ann.source || '',
            'data-annotation-severity': ann.severity || 'medium',
            'data-from': startPos.toString(),
            'data-to': endPos.toString(),
          })
        );
      }
      startIdx += 1; // Overlapping matches allowed
    }
  }

  // 3. Rule R82.46: Canonical Sorting — Mandatory for DecorationSet.create
  // Restoring sorting as it's critical for ProseMirror rendering
  decorations.sort((a, b) => {
    if (a.from !== b.from) return a.from - b.from;
    return a.to - b.to;
  });

  return DecorationSet.create(doc, decorations);
}
