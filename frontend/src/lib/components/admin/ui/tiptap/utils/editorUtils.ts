/**
 * Neural Editor Utilities (Elite V3.0)
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
 * [CNS V91.0] Neural Clean (NASP-inspired): Strips toxic styles and redundant structure.
 */
export const neuralCleanPastedHTML = (htmlStr: string): string => {
  if (!htmlStr || typeof document === 'undefined') return htmlStr;
  
  const parser = new DOMParser();
  const doc = parser.parseFromString(htmlStr, 'text/html');
  
  // 1. Deterministic Artifact Stripping
  const junk = doc.querySelectorAll('script, style, meta, link, noscript, iframe, embed, object');
  junk.forEach(el => el.remove());

  // 2. NASP: Structural Tree Pruning
  let changed = true;
  let passes = 0;
  while (changed && passes < 10) {
    changed = false;
    passes++;
    const elements = Array.from(doc.querySelectorAll('*')).reverse();
    
    elements.forEach(el => {
      if (!(el instanceof HTMLElement)) return;
      
      const tag = el.tagName.toLowerCase();

      // 2.1 Absolute Attribute Stripping
      const whitelist = ['href', 'src', 'alt', 'title', 'target', 'rel', 'style'];
      Array.from(el.attributes).forEach(attr => {
        if (!whitelist.includes(attr.name.toLowerCase())) {
          el.removeAttribute(attr.name);
          changed = true;
        }
      });

      // 2.2 Strip Toxic Styles
      const style = el.getAttribute('style');
      if (style) {
        const toxicProps = ['font-family', 'text-align', 'color', 'background', 'line-height', 'font-size', 'margin', 'padding', 'width', 'height'];
        const styles = style.split(';').map(s => s.trim()).filter(Boolean);
        const cleanStyles = styles.filter(s => {
          const prop = s.split(':')[0].toLowerCase().trim();
          return !toxicProps.some(toxic => prop.startsWith(toxic));
        });
        
        const newStyle = cleanStyles.join('; ');
        if (newStyle !== style) {
          if (newStyle) {
            el.setAttribute('style', newStyle);
          } else {
            el.removeAttribute('style');
          }
          changed = true;
        }
      }

      // 2.3 Prune Redundant Tags
      if ((tag === 'span' || tag === 'div') && !el.attributes.length) {
        while (el.firstChild) {
          el.parentNode?.insertBefore(el.firstChild, el);
        }
        el.remove();
        changed = true;
        return;
      }

      // 2.4 Flatten ListItem Paragraphs
      if (tag === 'li' && el.children.length === 1 && el.children[0].tagName.toLowerCase() === 'p') {
        const p = el.children[0] as HTMLElement;
        while (p.firstChild) {
          el.insertBefore(p.firstChild, p);
        }
        p.remove();
        changed = true;
        return;
      }

      // 2.5 Prune Empty Nodes
      const containers = ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'strong', 'b', 'em', 'i', 'span', 'u', 's', 'del', 'a'];
      const whitelisted = ['img', 'br', 'hr'];
      
      if (containers.includes(tag)) {
        const hasRealText = el.textContent?.replace(/\u00A0|\u200B|\uFEFF/g, '').trim().length > 0;
        const hasMeaningfulChild = Array.from(el.children).some(child => 
          whitelisted.includes(child.tagName.toLowerCase()) || 
          containers.includes(child.tagName.toLowerCase())
        );
        
        if (!hasRealText && !hasMeaningfulChild) {
          el.remove();
          changed = true;
        }
      }
    });
  }

  return doc.body.innerHTML;
};

/**
 * Strips <mark> tags and performs Neural Structural Cleaning.
 */
export const stripMarks = (html: string): string => {
  if (!html) return '';
  const noMarks = html.replace(/<mark[^>]*>|<\/mark>/g, '');
  return neuralCleanPastedHTML(noMarks);
};

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
 * Recursive Neural Formatter (Elite V3.0)
 * Uses context-aware DOM traversal for perfect indentation and zero vertical noise.
 */
export const beautifyHTML = (html: string): string => {
  if (!html || typeof document === 'undefined') return html;
  
  const parser = new DOMParser();
  const doc = parser.parseFromString(html.replace(/>\s+</g, '><').trim(), 'text/html');
  const body = doc.body;
  
  let result = '';
  const tab = '  ';
  const blockTags = ['p', 'div', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'section', 'article', 'figure', 'figcaption'];
  
  const walk = (node: Node, level: number) => {
    if (node.nodeType === 3) {
      // Text node
      const text = node.textContent?.trim();
      if (text) result += text;
      return;
    }
    
    if (node.nodeType === 1) {
      const el = node as HTMLElement;
      const tag = el.tagName.toLowerCase();
      const isBlock = blockTags.includes(tag);
      
      const attrs = Array.from(el.attributes)
        .map(a => ` ${a.name}="${a.value}"`)
        .join('');
      
      const openTag = `<${tag}${attrs}>`;
      const closeTag = `</${tag}>`;
      
      if (isBlock) {
        if (result && !result.endsWith('\n')) result += '\n';
        result += tab.repeat(level) + openTag;
        
        // Process children
        Array.from(el.childNodes).forEach(child => walk(child, level + 1));
        
        // Closing block tag
        const hasBlockChild = Array.from(el.children).some(c => blockTags.includes(c.tagName.toLowerCase()));
        if (hasBlockChild) {
          if (!result.endsWith('\n')) result += '\n';
          result += tab.repeat(level) + closeTag + '\n';
        } else {
          result += closeTag + '\n';
        }
      } else {
        // Inline tag
        result += openTag;
        Array.from(el.childNodes).forEach(child => walk(child, level));
        result += closeTag;
      }
    }
  };
  
  Array.from(body.childNodes).forEach(child => walk(child, 0));
  return result.trim();
};
