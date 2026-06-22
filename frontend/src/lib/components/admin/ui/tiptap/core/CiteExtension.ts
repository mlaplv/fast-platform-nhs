import { Mark, mergeAttributes } from '@tiptap/core';

export const Cite = Mark.create({
  name: 'cite',

  addAttributes() {
    return {
      class: {
        default: 'xohi-cite',
        parseHTML: element => element.getAttribute('class'),
        renderHTML: attributes => {
          if (!attributes.class) return {};
          return { class: attributes.class };
        },
      }
    };
  },

  parseHTML() {
    return [{ tag: 'cite' }];
  },

  renderHTML({ HTMLAttributes }) {
    return ['cite', mergeAttributes(HTMLAttributes), 0];
  },
});
