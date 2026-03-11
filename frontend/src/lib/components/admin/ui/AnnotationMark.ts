import { Mark, mergeAttributes } from '@tiptap/core';

export interface AnnotationOptions {
  HTMLAttributes: Record<string, unknown>;
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    annotation: {
      setAnnotation: (attrs: { id?: string; type: string; message: string; source?: string; severity: string }) => ReturnType;
      unsetAnnotation: () => ReturnType;
      clearAllAnnotations: () => ReturnType;
    };
  }
}

/**
 * AnnotationMark — Custom Tiptap Mark for inline Copyright & SEO highlighting.
 * 
 * Renders text passages as colored underlines with a hover tooltip.
 * Does NOT interfere with editing — marks are just visual overlays.
 * 
 * Types:
 *  - copyright (severity: low/medium/high)  → yellow/orange/red underline
 *  - seo-error                              → red wavy underline
 *  - seo-warning                            → orange wavy underline
 *  - seo-info                               → blue underline
 */
export const AnnotationMark = Mark.create<AnnotationOptions>({
  name: 'annotation',

  addOptions() {
    return {
      HTMLAttributes: {},
    };
  },

  addAttributes() {
    return {
      id: {
        default: null,
        parseHTML: (el) => el.getAttribute('data-annotation-id'),
        renderHTML: (attrs) => attrs.id ? { 'data-annotation-id': attrs.id } : {},
      },
      type: {
        default: 'seo-info',
        parseHTML: (el) => el.getAttribute('data-annotation-type'),
        renderHTML: (attrs) => ({ 'data-annotation-type': attrs.type }),
      },
      severity: {
        default: 'info',
        parseHTML: (el) => el.getAttribute('data-annotation-severity'),
        renderHTML: (attrs) => ({ 'data-annotation-severity': attrs.severity }),
      },
      message: {
        default: '',
        parseHTML: (el) => el.getAttribute('data-annotation-message'),
        renderHTML: (attrs) => ({ 'data-annotation-message': attrs.message }),
      },
      source: {
        default: '',
        parseHTML: (el) => el.getAttribute('data-annotation-source'),
        renderHTML: (attrs) => attrs.source ? { 'data-annotation-source': attrs.source } : {},
      },
    };
  },

  parseHTML() {
    return [{ tag: 'mark[data-annotation-type]' }];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'mark',
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        class: 'xohi-annotation',
      }),
      0,
    ];
  },

  addCommands() {
    return {
      setAnnotation:
        (attrs) =>
        ({ commands }) => {
          return commands.setMark(this.name, attrs);
        },
      unsetAnnotation:
        () =>
        ({ commands }) => {
          return commands.unsetMark(this.name);
        },
      clearAllAnnotations:
        () =>
        ({ tr, dispatch }) => {
          const { doc } = tr;
          const annotationMarkType = this.type;
          const changes: Array<{ from: number; to: number }> = [];
          
          doc.descendants((node, pos) => {
            if (node.isText && node.marks.some(m => m.type === annotationMarkType)) {
              changes.push({ from: pos, to: pos + node.nodeSize });
            }
          });

          // Apply removals in reverse order to not mess up positions
          if (dispatch) {
            let newTr = tr;
            for (const { from, to } of changes.reverse()) {
              newTr = newTr.removeMark(from, to, annotationMarkType);
            }
            dispatch(newTr);
          }
          return true;
        },
    };
  },
});

// ─── CSS injected globally (once) ───────────────────────────────────────────

const ANNOTATION_STYLES = `
  /* AnnotationMark — XoHi Content Studio 2026 — Dark Background Edition */

  /* Base: MUST override browser <mark> defaults (yellow bg, black text) */
  .xohi-annotation {
    background: transparent;
    color: inherit;
    position: relative;
    cursor: pointer;
    border-radius: 2px;
    transition: background 0.2s ease, text-shadow 0.2s ease;
  }

  /* ══ COPYRIGHT —— Việt Nam scale: vàng → cam → đỏ ══ */

  /* LOW: vàng, text #fef08a (yellow-200) rõ trên nền #111827 */
  .xohi-annotation[data-annotation-type="copyright" i][data-annotation-severity="low" i] {
    color: #fef08a !important;
    background: rgba(234, 179, 8, 0.18);
    text-decoration: underline wavy rgba(234, 179, 8, 1);
    text-decoration-thickness: 2px;
    text-shadow: 0 0 12px rgba(234, 179, 8, 0.4);
  }
  /* MEDIUM: cam, text #fed7aa (orange-200) */
  .xohi-annotation[data-annotation-type="copyright" i][data-annotation-severity="medium" i] {
    color: #fed7aa !important;
    background: rgba(249, 115, 22, 0.20);
    text-decoration: underline wavy rgba(249, 115, 22, 1);
    text-decoration-thickness: 2px;
    text-shadow: 0 0 14px rgba(249, 115, 22, 0.45);
  }
  /* HIGH: đỏ nổi, text #fca5a5 (red-300) */
  .xohi-annotation[data-annotation-type="copyright" i][data-annotation-severity="high" i] {
    color: #fca5a5 !important;
    background: rgba(239, 68, 68, 0.22);
    text-decoration: underline wavy rgba(239, 68, 68, 1);
    text-decoration-thickness: 2.5px;
    text-shadow: 0 0 18px rgba(239, 68, 68, 0.55);
  }

  /* ══ SEO ERROR — đỏ crisp ══ */
  .xohi-annotation[data-annotation-type="seo-error" i],
  .xohi-annotation[data-annotation-type="missing_h1" i],
  .xohi-annotation[data-annotation-type="keyword_stuffing" i] {
    color: #fca5a5 !important;    /* red-300 — rõ trên nền tối */
    background: rgba(239, 68, 68, 0.18);
    text-decoration: underline wavy rgba(239, 68, 68, 1);
    text-decoration-thickness: 2px;
    text-shadow: 0 0 14px rgba(239, 68, 68, 0.45);
  }

  /* ══ SEO WARNING — cam ấm ══ */
  .xohi-annotation[data-annotation-type="seo-warning" i],
  .xohi-annotation[data-annotation-type="missing_h2" i],
  .xohi-annotation[data-annotation-type="weak_intro" i],
  .xohi-annotation[data-annotation-type="thin_section" i],
  .xohi-annotation[data-annotation-type="missing_cta" i],
  .xohi-annotation[data-annotation-type="keyword_missing" i] {
    color: #fed7aa !important;    /* orange-200 — ấm, đọc được ngay */
    background: rgba(249, 115, 22, 0.16);
    text-decoration: underline wavy rgba(249, 115, 22, 1);
    text-decoration-thickness: 2px;
    text-shadow: 0 0 12px rgba(249, 115, 22, 0.4);
  }

  /* ══ SEO INFO — xanh dương nhạt ══ */
  .xohi-annotation[data-annotation-type="seo-info" i],
  .xohi-annotation[data-annotation-type="ai_stiff" i] {
    color: #bae6fd !important;    /* sky-200 — dế chịu không làm mỏi mắt */
    background: rgba(96, 165, 250, 0.12);
    text-decoration: underline dotted rgba(96, 165, 250, 1);
    text-decoration-thickness: 1.5px;
    text-shadow: 0 0 10px rgba(96, 165, 250, 0.3);
  }

  /* ══ AI READINESS / GEO — tím neon nhạt ══ */
  .xohi-annotation[data-annotation-type="geo-info" i],
  .xohi-annotation[data-annotation-type="geo_stats" i],
  .xohi-annotation[data-annotation-type="geo_quotes" i],
  .xohi-annotation[data-annotation-type="geo_fluff" i],
  .xohi-annotation[data-annotation-type="geo_snippet" i] {
    color: #f0abfc !important;    /* fuchsia-300 */
    background: rgba(192, 38, 211, 0.15); /* fuchsia-600 with opacity */
    text-decoration: underline dashed rgba(192, 38, 211, 0.8);
    text-decoration-thickness: 1.5px;
    text-shadow: 0 0 12px rgba(192, 38, 211, 0.4);
  }

  /* ══ FIXED / SUCCESS — xanh lá (Emerald) ══ */
  .xohi-annotation[data-annotation-type="fixed" i] {
    color: #6ee7b7 !important;    /* emerald-300 */
    background: rgba(16, 185, 129, 0.15);
    text-decoration: underline rgba(16, 185, 129, 1);
    text-decoration-thickness: 2px;
    text-shadow: 0 0 12px rgba(16, 185, 129, 0.45);
  }

  /* ══ HOVER — amplify glow ══ */
  .xohi-annotation[data-annotation-type="copyright" i][data-annotation-severity="high" i]:hover {
    background: rgba(239, 68, 68, 0.35);
    text-shadow: 0 0 22px rgba(239, 68, 68, 0.75);
  }
  .xohi-annotation[data-annotation-type="copyright" i][data-annotation-severity="medium" i]:hover {
    background: rgba(249, 115, 22, 0.32);
    text-shadow: 0 0 18px rgba(249, 115, 22, 0.65);
  }
  .xohi-annotation[data-annotation-type="copyright" i][data-annotation-severity="low" i]:hover {
    background: rgba(234, 179, 8, 0.28);
    text-shadow: 0 0 14px rgba(234, 179, 8, 0.55);
  }
  .xohi-annotation[data-annotation-type="seo-error" i]:hover,
  .xohi-annotation[data-annotation-type="missing_h1" i]:hover,
  .xohi-annotation[data-annotation-type="keyword_stuffing" i]:hover {
    background: rgba(239, 68, 68, 0.30);
    text-shadow: 0 0 20px rgba(239, 68, 68, 0.65);
  }
  .xohi-annotation[data-annotation-type="seo-warning" i]:hover,
  .xohi-annotation[data-annotation-type="missing_h2" i]:hover,
  .xohi-annotation[data-annotation-type="missing_cta" i]:hover,
  .xohi-annotation[data-annotation-type="keyword_missing" i]:hover {
    background: rgba(249, 115, 22, 0.28);
    text-shadow: 0 0 16px rgba(249, 115, 22, 0.6);
  }
  .xohi-annotation[data-annotation-type="seo-info" i]:hover,
  .xohi-annotation[data-annotation-type="ai_stiff" i]:hover {
    background: rgba(96, 165, 250, 0.22);
    text-shadow: 0 0 14px rgba(96, 165, 250, 0.45);
  }
  .xohi-annotation[data-annotation-type="geo-info" i]:hover,
  .xohi-annotation[data-annotation-type="geo_stats" i]:hover,
  .xohi-annotation[data-annotation-type="geo_quotes" i]:hover,
  .xohi-annotation[data-annotation-type="geo_fluff" i]:hover,
  .xohi-annotation[data-annotation-type="geo_snippet" i]:hover {
    background: rgba(192, 38, 211, 0.25);
    text-shadow: 0 0 16px rgba(192, 38, 211, 0.55);
  }
`;

let stylesInjected = false;
export function injectAnnotationStyles() {
  if (stylesInjected || typeof document === 'undefined') return;
  const style = document.createElement('style');
  style.id = 'xohi-annotation-styles';
  style.textContent = ANNOTATION_STYLES;
  document.head.appendChild(style);
  stylesInjected = true;
}
