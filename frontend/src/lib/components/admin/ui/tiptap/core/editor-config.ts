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
    typography: false,
    bold: true,
    italic: true,
    strike: true,
    code: true,
    history: true,
    link: false,
    underline: false
  }),
  Typography,
  Underline,
  Link.configure({
    openOnClick: false,
    HTMLAttributes: { class: 'text-blue-400 underline hover:text-blue-300 transition-colors cursor-pointer' },
  }),
  Image.configure({
    inline: false,
    HTMLAttributes: { class: 'max-w-full mx-auto my-4 shadow-lg' },
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
