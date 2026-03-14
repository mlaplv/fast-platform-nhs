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

const ANNOTATION_STYLES = `
  .xohi-annotation {
    background: transparent;
    color: inherit;
    position: relative;
    cursor: pointer;
    border-radius: 0;
    transition: background 0.2s ease, text-shadow 0.2s ease;
    pointer-events: auto !important;
  }
  .xohi-annotation[data-annotation-type="copyright" i][data-annotation-severity="low" i] {
    color: #fef08a !important;
    background: rgba(234, 179, 8, 0.18);
    text-decoration: underline wavy rgba(234, 179, 8, 1);
    text-decoration-thickness: 2px;
    text-shadow: 0 0 12px rgba(234, 179, 8, 0.4);
  }
  .xohi-annotation[data-annotation-type="copyright" i][data-annotation-severity="medium" i] {
    color: #fed7aa !important;
    background: rgba(249, 115, 22, 0.20);
    text-decoration: underline wavy rgba(249, 115, 22, 1);
    text-decoration-thickness: 2px;
    text-shadow: 0 0 14px rgba(249, 115, 22, 0.45);
  }
  .xohi-annotation[data-annotation-type="copyright" i][data-annotation-severity="high" i] {
    color: #fca5a5 !important;
    background: rgba(239, 68, 68, 0.22);
    text-decoration: underline wavy rgba(239, 68, 68, 1);
    text-decoration-thickness: 2.5px;
    text-shadow: 0 0 18px rgba(239, 68, 68, 0.55);
  }
  .xohi-annotation[data-annotation-type="seo-error" i],
  .xohi-annotation[data-annotation-type="missing_h1" i],
  .xohi-annotation[data-annotation-type="keyword_stuffing" i] {
    color: #fca5a5 !important;
    background: rgba(239, 68, 68, 0.18);
    text-decoration: underline wavy rgba(239, 68, 68, 1);
    text-decoration-thickness: 2px;
    text-shadow: 0 0 14px rgba(239, 68, 68, 0.45);
  }
  .xohi-annotation[data-annotation-type="seo-warning" i],
  .xohi-annotation[data-annotation-type="missing_h2" i],
  .xohi-annotation[data-annotation-type="weak_intro" i],
  .xohi-annotation[data-annotation-type="thin_section" i],
  .xohi-annotation[data-annotation-type="missing_cta" i],
  .xohi-annotation[data-annotation-type="keyword_missing" i] {
    color: #fed7aa !important;
    background: rgba(249, 115, 22, 0.16);
    text-decoration: underline wavy rgba(249, 115, 22, 1);
    text-decoration-thickness: 2px;
    text-shadow: 0 0 12px rgba(249, 115, 22, 0.4);
  }
  .xohi-annotation[data-annotation-type="seo-info" i],
  .xohi-annotation[data-annotation-type="ai_stiff" i] {
    color: #bae6fd !important;
    background: rgba(96, 165, 250, 0.12);
    text-decoration: underline dotted rgba(96, 165, 250, 1);
    text-decoration-thickness: 1.5px;
    text-shadow: 0 0 10px rgba(96, 165, 250, 0.3);
  }
  .xohi-annotation[data-annotation-type="internal-dedup" i] {
    color: #e879f9 !important;
    background: rgba(217, 70, 239, 0.12);
    text-decoration: underline dashed rgba(217, 70, 239, 1);
    text-decoration-thickness: 1.5px;
    text-shadow: 0 0 12px rgba(217, 70, 239, 0.4);
  }
  .xohi-annotation[data-annotation-type="internal-dedup" i]:hover {
    background: rgba(217, 70, 239, 0.25);
    text-shadow: 0 0 18px rgba(217, 70, 239, 0.6);
  }
  .xohi-annotation[data-annotation-type="geo-info" i],
  .xohi-annotation[data-annotation-type="geo_stats" i],
  .xohi-annotation[data-annotation-type="geo_quotes" i],
  .xohi-annotation[data-annotation-type="geo_fluff" i],
  .xohi-annotation[data-annotation-type="geo_snippet" i] {
    color: #f0abfc !important;
    background: rgba(192, 38, 211, 0.15);
    text-decoration: underline dashed rgba(192, 38, 211, 0.8);
    text-decoration-thickness: 1.5px;
    text-shadow: 0 0 12px rgba(192, 38, 211, 0.4);
  }
  .xohi-annotation[data-annotation-type="fixed" i] {
    color: #6ee7b7 !important;
    background: rgba(16, 185, 129, 0.15);
    text-decoration: underline rgba(16, 185, 129, 1);
    text-decoration-thickness: 2px;
    text-shadow: 0 0 12px rgba(16, 185, 129, 0.45);
  }
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
  .xohi-annotation[data-annotation-type="seo-error" i]:hover {
    background: rgba(239, 68, 68, 0.30);
    text-shadow: 0 0 20px rgba(239, 68, 68, 0.65);
  }
  .xohi-annotation[data-annotation-type="seo-warning" i]:hover {
    background: rgba(249, 115, 22, 0.28);
    text-shadow: 0 0 16px rgba(249, 115, 22, 0.6);
  }
  .xohi-annotation[data-annotation-type="seo-info" i]:hover {
    background: rgba(96, 165, 250, 0.22);
    text-shadow: 0 0 14px rgba(96, 165, 250, 0.45);
  }
  .xohi-annotation[data-annotation-type="geo-info" i]:hover {
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
