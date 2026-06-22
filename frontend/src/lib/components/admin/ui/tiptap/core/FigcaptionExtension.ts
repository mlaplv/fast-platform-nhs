import { Node, mergeAttributes } from '@tiptap/core';

export const Figcaption = Node.create({
  name: 'figcaption',
  group: 'block',
  content: 'inline*',
  defining: true,

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
    return [{ tag: 'figcaption' }];
  },

  renderHTML({ HTMLAttributes }) {
    return ['figcaption', mergeAttributes(HTMLAttributes), 0];
  },
});
