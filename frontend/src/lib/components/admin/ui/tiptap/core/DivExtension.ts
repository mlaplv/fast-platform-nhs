import { Node, mergeAttributes } from '@tiptap/core';

export const Div = Node.create({
  name: 'div',
  group: 'block',
  content: 'block+',
  
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
        tag: 'div',
        getAttrs: (node) => {
          const el = node as HTMLElement;
          // [CNS V92.0] Only match if it has attributes, otherwise it's just a redundant block
          return el.attributes.length > 0 ? {} : false;
        }
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return ['div', mergeAttributes(HTMLAttributes), 0];
  },
});
