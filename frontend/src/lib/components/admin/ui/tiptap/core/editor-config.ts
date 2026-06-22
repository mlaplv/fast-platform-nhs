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
import { BulletList, ListItem, OrderedList } from '@tiptap/extension-list';
import { AnnotationExtension } from './AnnotationPlugin';
import { Div } from './DivExtension';
import { Span } from './SpanExtension';
import { Figure } from './FigureExtension';
import { Figcaption } from './FigcaptionExtension';
import { Cite } from './CiteExtension';
import { Caption } from './CaptionExtension';
import { Table } from '@tiptap/extension-table';
import { TableRow } from '@tiptap/extension-table-row';
import { TableCell } from '@tiptap/extension-table-cell';
import { TableHeader } from '@tiptap/extension-table-header';
import { neuralCleanPastedHTML } from '../utils/editorUtils';
import { mergeAttributes } from '@tiptap/core';

/**
 * [CNS V92.0] Neural ListItem: Allows inline content to prevent redundant <p> wrapping.
 * This directly addresses the "li > p" noise issue.
 */
const NeuralListItem = ListItem.extend({
  content: 'paragraph block*',
});

// CNS V95.0 Custom table node to support caption preservation
const CustomTable = Table.extend({
  content: 'caption? tableRow+',
  renderHTML({ HTMLAttributes }) {
    return ['table', mergeAttributes(this.options.HTMLAttributes, HTMLAttributes), 0];
  },
}).configure({
  resizable: false,
});

export const getEditorExtensions = (placeholderText: string = 'Start writing...') => [
  StarterKit.configure({
    bold: {},
    italic: {},
    strike: {},
    code: {},
    history: {},
    heading: {
      levels: [1, 2, 3, 4]
    },
    link: false,
    underline: false,
    listItem: false,    // Disable default → dùng NeuralListItem
    bulletList: false,  // Disable default → import riêng từ @tiptap/extension-list (Tiptap v3)
    orderedList: false, // Disable default → import riêng từ @tiptap/extension-list (Tiptap v3)
  }).extend({
    addKeyboardShortcuts() {
      return {
        'Mod-\\': () => this.editor.commands.unsetAllMarks(),
        'Mod-Shift-Backspace': () => this.editor.commands.clearNodes(),
      }
    }
  }),
  NeuralListItem,
  BulletList,
  OrderedList,
  Typography,
  Underline,
  Link.extend({
    addAttributes() {
      return {
        ...this.parent?.(),
        title: {
          default: null,
          parseHTML: element => element.getAttribute('title'),
          renderHTML: attributes => {
            if (!attributes.title) return {};
            return { title: attributes.title };
          },
        },
      }
    },
    addKeyboardShortcuts() {
      return {
        'Mod-Shift-k': () => this.editor.commands.unsetLink(),
      }
    },
    addCommands() {
      return {
        ...this.parent?.(),
        unsetAllLinks: () => ({ tr, dispatch }) => {
          if (dispatch) {
            const { from, to } = tr.selection;
            const hasSelection = from !== to;
            const start = hasSelection ? from : 0;
            const end = hasSelection ? to : tr.doc.content.size;
            
            const linkType = tr.doc.type.schema.marks.link;
            if (linkType) {
              tr.removeMark(start, end, linkType);
            }
          }
          return true;
        },
      }
    },
  }).configure({
    autolink: false,
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
        { 
          tag: 'figure', 
          getAttrs: (node: HTMLElement) => {
            const img = node.querySelector('img');
            if (!img) return false;
            const caption = node.querySelector('figcaption')?.textContent || null;
            return { 
              src: img.getAttribute('src'),
              alt: img.getAttribute('alt'),
              class: img.getAttribute('class') || node.getAttribute('class'),
              title: caption,
            };
          }
        },
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
  Div,
  Span,
  CustomTable,
  TableRow,
  TableHeader,
  TableCell,
  Figure,
  Figcaption,
  Cite,
  Caption,
];

export const editorProps = {
  attributes: {
    class: 'focus:outline-none w-full',
  },
  transformPastedHTML(html: string) {
    return neuralCleanPastedHTML(html);
  }
};
