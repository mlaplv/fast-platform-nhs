/**
 * Neural Editor Utilities (Elite V2.7)
 * Strictly typed, no any, high-performance logic.
 */

export const tokenize = (text: string): Set<string> => {
  const normalized = text.toLowerCase().normalize('NFC');
  return new Set(normalized
    .replace(/\d+/g, '')
    .replace(/[^\w\s\u00C0-\u024F\u1E00-\u1EFF]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length >= 2));
};

export const jaccard = (a: Set<string>, b: Set<string>): number => {
  if (a.size === 0 && b.size === 0) return 1;
  if (a.size === 0 || b.size === 0) return 0;
  let intersect = 0;
  a.forEach(w => { if (b.has(w)) intersect++; });
  return intersect / (a.size + b.size - intersect);
};

export const normalizeHTML = (html: string, stripMarksFn: (h: string) => string) => {
  if (typeof document === 'undefined') return html.trim();
  const div = document.createElement('div');
  
  // CNS V2.2: Strip temporary marks for comparison to prevent sync loops
  const clean = stripMarksFn(html)
      .replace(/&nbsp;/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
      
  div.innerHTML = clean;

  const prune = (node: Node) => {
      for (let i = node.childNodes.length - 1; i >= 0; i--) {
          const child = node.childNodes[i];
          if (child.nodeType === 1) {
              prune(child);
              const el = child as HTMLElement;
              const isContainer = ['P', 'DIV', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'STRONG', 'B', 'EM', 'I', 'SPAN'].includes(el.tagName);
              const isEmpty = el.innerHTML.replace(/&nbsp;/g, '').replace(/\s+/g, '').trim() === '' || el.innerHTML === '<br>';
              if (isContainer && isEmpty) el.remove();
          }
      }
  };
  prune(div);
  return div.innerHTML.replace(/>\s+</g, '><');
};

/**
 * Strips <mark> tags from HTML content.
 */
export const stripMarks = (html: string): string => html.replace(/<mark[^>]*>|<\/mark>/g, '');

/**
 * Generates a stable ID for an annotation based on text and message.
 */
export const generateStableId = (text: string, message: string): string => {
  let hash = 5381;
  const str = text + message;
  for (let i = 0; i < str.length; i++) {
    hash = (hash * 33) ^ str.charCodeAt(i);
  }
  return (hash >>> 0).toString(36);
};
/**
 * Beautifies HTML for source view (Elite V2.7 - Robust Edition)
 */
export const beautifyHTML = (html: string): string => {
  if (!html) return '';
  
  let result = '';
  let indent = '';
  const tab = '  ';
  
  // Robust split by tags, preserving tags and content
  const tokens = html.replace(/>\s*</g, '><').split(/(<[^>]+>)/g).filter(v => v.trim() !== '');

  tokens.forEach(token => {
    if (token.startsWith('</')) {
      // Closing tag: decrement indent and append
      indent = indent.slice(tab.length);
      result += indent + token + '\n';
    } else if (token.startsWith('<') && !token.endsWith('/>') && !token.match(/^<(br|hr|img|input|link|meta)/i)) {
      // Opening tag (not self-closing): append and increment indent
      result += indent + token + '\n';
      indent += tab;
    } else {
      // Self-closing tag or text content
      result += indent + token + '\n';
    }
  });

  return result.trim();
};
