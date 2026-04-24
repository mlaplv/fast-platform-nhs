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
        const meta = tr.getMeta(AnnotationPluginKey);
        if (meta && meta.type === 'SET_ANNOTATIONS') {
          return {
            annotations: meta.annotations,
            decorations: createDecorations(newState.doc as ProseMirrorNode, meta.annotations),
          };
        }

        // CNS V87.5: Rely on SET_ANNOTATIONS for full re-scans 
        // and tr.mapping for incremental typing updates. 
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
  // CNS V87.1: Ultra-robust matching — Normalize to NFD and strip marks to avoid Vietnamese accent mismatches
  const isAlphaNum = (c: string) => /\p{L}|\p{N}/u.test(c);
  const isMark = (c: string) => /\p{M}/u.test(c);
  
  const robustNormalize = (text: string) => {
    return text.normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '') // Strip all combining marks
      .toLowerCase()
      .replace(/[^\p{L}\p{N}]/gu, ''); // Keep only letters and numbers
  };

  // 1. Build a searchable normalized buffer of the doc
  let searchBuffer = '';
  const posMap: number[] = [];

  // 1. Build the alphanumeric buffer & position map
  doc.descendants((node: ProseMirrorNode, pos: number) => {
    if (node.isText && node.text) {
      const text = node.text;
      for (let i = 0; i < text.length; i++) {
        const char = text[i];
        if (isAlphaNum(char) || isMark(char)) {
          const cleanChar = char.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
          if (cleanChar) {
            searchBuffer += cleanChar;
            posMap.push(pos + i);
          }
        }
      }
    }
  });

  // 2. Scan for each annotation
  for (const ann of annotations) {
    if (!ann.text || ann.text.length < 3) continue;

    // CNS V88.5: AI Prefix Stripping (Handles "Các mục: ", "Đoạn văn: ", etc.)
    let plainPattern = ann.text.replace(/<[^>]+>/g, '');
    const aiPrefixes = [
      /^các mục:\s*/i, /^đoạn văn:\s*/i, /^nội dung:\s*/i, /^phần:\s*/i,
      /^vấn đề:\s*/i, /^câu:\s*/i, /^dòng:\s*/i, /^từ:\s*/i
    ];
    for (const prefix of aiPrefixes) {
      plainPattern = plainPattern.replace(prefix, '');
    }

    const normalizedPattern = robustNormalize(plainPattern);

    if (normalizedPattern.length < 4) {
       console.warn(`[Neural Annotation] Pattern too short after normalization: "${ann.text.slice(0, 20)}..." -> "${normalizedPattern}"`);
       continue;
    }

    const pushBlockSafeDecorations = (startIdx: number, endIdx: number, baseAttrs: Record<string, string | number | boolean | undefined>) => {
      if (startIdx > endIdx || startIdx >= posMap.length) return;
      const totalFrom = posMap[startIdx];
      const totalTo = posMap[Math.min(posMap.length - 1, endIdx)] + 1;
      
      // Elite V2.2: Use nodesBetween to correctly span across blocks without dropping
      doc.nodesBetween(totalFrom, totalTo, (node, pos) => {
        if (node.isText) {
          const start = Math.max(totalFrom, pos);
          const end = Math.min(totalTo, pos + node.nodeSize);
          if (start < end) {
            // Each segment needs the FULL match range for the "Fix" feature to work
            const attrs = {
              ...baseAttrs,
              'data-from': totalFrom,
              'data-to': totalTo
            };
            decorations.push(Decoration.inline(start, end, attrs));
          }
        }
      });
    };

    const getAttrs = (type: string, severity: string, suffix: string = ''): Record<string, string | number | boolean | undefined> => {
      let inlineStyle = '';
      if (severity === 'high') inlineStyle = 'background-color: rgba(239, 68, 68, 0.45) !important; border-bottom: 3px solid #ef4444 !important; color: #fff !important;';
      else if (severity === 'medium') inlineStyle = 'background-color: rgba(245, 158, 11, 0.35) !important; border-bottom: 3px solid #f59e0b !important; color: #fff !important;';
      else inlineStyle = 'background-color: rgba(16, 185, 129, 0.25) !important; border-bottom: 2px solid #10b981 !important;';

      const startPos = posMap[startIdx] || 0; // fallback just for ID
      return {
        class: `xohi-annotation type-${type} severity-${severity}`,
        'data-annotation-id': `deco-${type}-${startPos}-${matchCount}${suffix}`,
        'data-annotation-type': type,
        'data-annotation-message': ann.message,
        'data-annotation-source': ann.source || '',
        'data-annotation-severity': severity,
        style: inlineStyle
      };
    };

    // Find ALL occurrences (Exact Match)
    let startIdx = 0;
    let matchCount = 0;
    while ((startIdx = searchBuffer.indexOf(normalizedPattern, startIdx)) !== -1) {
      const endIdx = startIdx + normalizedPattern.length - 1;
      const severity = (ann.severity || 'medium').toLowerCase();
      const type = (ann.type || 'unknown').toLowerCase();
      
      pushBlockSafeDecorations(startIdx, endIdx, getAttrs(type, severity));
      matchCount++;
      startIdx += 1; 
    }

    // CNS V87.6: Anchor-based Recovery Fallback + Smart Endpoint Detection
    if (matchCount === 0 && normalizedPattern.length > 20) {
      // Attempt matching with smaller chunks of the pattern (Sliding Anchor)
      const anchorSize = Math.min(60, Math.floor(normalizedPattern.length * 0.7));
      const anchors = [
        normalizedPattern.slice(0, anchorSize),
        normalizedPattern.slice(-anchorSize),
        normalizedPattern.slice(Math.floor(normalizedPattern.length/2) - 20, Math.floor(normalizedPattern.length/2) + 20)
      ].filter(a => a.length >= 10);

      for (const anchor of anchors) {
        if (matchCount > 0) break;
        let anchorIdx = 0;
        while ((anchorIdx = searchBuffer.indexOf(anchor, anchorIdx)) !== -1) {
          // Smart Endpoint: match character by character until mismatch
          let matchLen = 0;
          while (anchorIdx + matchLen < searchBuffer.length && matchLen < normalizedPattern.length) {
            if (searchBuffer[anchorIdx + matchLen] === normalizedPattern[matchLen]) matchLen++;
            else break;
          }
          
          if (matchLen < anchor.length) { anchorIdx += 1; continue; }

          const endIdx = anchorIdx + matchLen - 1;
          const severity = (ann.severity || 'medium').toLowerCase();
          const type = (ann.type || 'unknown').toLowerCase();
          
          startIdx = anchorIdx; 
          pushBlockSafeDecorations(anchorIdx, endIdx, getAttrs(type, severity, '-fuzzy'));
          matchCount++;
          anchorIdx += 1;
        }
      }
    }
  }

  // 3. Rule R82.46: Canonical Sorting
  decorations.sort((a, b) => {
    if (a.from !== b.from) return a.from - b.from;
    return a.to - b.to;
  });

  return DecorationSet.create(doc, decorations);
}
