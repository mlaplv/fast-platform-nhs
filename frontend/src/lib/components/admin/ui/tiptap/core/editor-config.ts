import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import Link from '@tiptap/extension-link';
import Image from '@tiptap/extension-image';
import Underline from '@tiptap/extension-underline';
import TextAlign from '@tiptap/extension-text-align';
import { TextStyle } from '@tiptap/extension-text-style';
import Color from '@tiptap/extension-color';
import FontFamily from '@tiptap/extension-font-family';
import CharacterCount from '@tiptap/extension-character-count';
import Typography from '@tiptap/extension-typography';
import { AnnotationExtension } from './AnnotationPlugin';

export const getEditorExtensions = (placeholderText: string = 'Start writing...') => [
  StarterKit.configure({
    bold: {},
    italic: {},
    strike: {},
    code: {},
    history: {},
    link: false,
    underline: false
  }),
  Typography,
  Underline,
  Link.configure({
    openOnClick: false,
    HTMLAttributes: { class: 'text-blue-400 underline hover:text-blue-300 transition-colors cursor-pointer' },
  }),
  Image.extend({
    addAttributes() {
      return {
        ...this.parent?.(),
        src: {
          default: null,
          parseHTML: element => element.getAttribute('src'),
          renderHTML: attributes => {
            if (!attributes.src) return {};
            return { src: attributes.src };
          },
        },
        alt: {
          default: null,
          parseHTML: element => element.getAttribute('alt'),
          renderHTML: attributes => {
            if (!attributes.alt) return {};
            return { alt: attributes.alt };
          },
        },
        class: {
          default: 'max-w-full mx-auto my-4 shadow-lg flex',
          parseHTML: element => element.getAttribute('class'),
          renderHTML: attributes => {
            if (!attributes.class) return {};
            return { class: attributes.class };
          },
        },
        title: {
          default: null,
          parseHTML: element => element.getAttribute('title') || element.closest('figure')?.querySelector('figcaption')?.textContent || null,
          renderHTML: attributes => {
            if (!attributes.title) return {};
            return { title: attributes.title };
          },
        },
      }
    },
    renderHTML({ HTMLAttributes }) {
      const { title, ...imgAttrs } = HTMLAttributes;
      if (title) {
        return ['figure', { class: 'image-figure' }, 
          ['img', imgAttrs],
          ['figcaption', {}, title]
        ];
      }
      return ['img', HTMLAttributes];
    },
    parseHTML() {
      return [
        { tag: 'figure.image-figure', getAttrs: (node: HTMLElement) => {
          const img = node.querySelector('img');
          if (!img) return false;
          const caption = node.querySelector('figcaption')?.textContent || null;
          return { 
            src: img.getAttribute('src'),
            alt: img.getAttribute('alt'),
            class: img.getAttribute('class'),
            title: caption,
          };
        }},
        { tag: 'img[src]' },
      ];
    },
  }).configure({
    inline: false,
    HTMLAttributes: { class: 'max-w-full mx-auto my-4 shadow-lg flex' },
  }),
  TextAlign.configure({ types: ['heading', 'paragraph'] }),
  TextStyle,
  Color,
  FontFamily.configure({ types: ['textStyle'] }),
  CharacterCount,
  Placeholder.configure({
    placeholder: placeholderText,
    emptyEditorClass: 'is-editor-empty',
  }),
  AnnotationExtension,
];

export const editorProps = {
  attributes: {
    class: 'focus:outline-none w-full',
  },
};
