import { Node, mergeAttributes } from '@tiptap/core';

export const Caption = Node.create({
  name: 'caption',
  group: 'block',
  content: 'inline*',
  defining: true,

  parseHTML() {
    return [{ tag: 'caption' }];
  },

  renderHTML({ HTMLAttributes }) {
    return ['caption', mergeAttributes(HTMLAttributes), 0];
  },
});
