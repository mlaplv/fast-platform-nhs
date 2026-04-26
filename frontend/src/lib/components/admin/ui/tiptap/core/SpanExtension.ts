import { Mark, mergeAttributes } from '@tiptap/core';

export const Span = Mark.create({
  name: 'span',

  addAttributes() {
    return {
      class: {
        default: null,
        parseHTML: element => element.getAttribute('class'),
        renderHTML: attributes => {
          if (!attributes.class) return {};
          return { class: attributes.class };
        },
      }
    };
  },

  parseHTML() {
    return [
      { 
        tag: 'span',
        getAttrs: (node) => {
          const el = node as HTMLElement;
          // [CNS V92.0] Only match if it actually does something (has attributes)
          return el.attributes.length > 0 ? {} : false;
        }
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return ['span', mergeAttributes(HTMLAttributes), 0];
  },
});
