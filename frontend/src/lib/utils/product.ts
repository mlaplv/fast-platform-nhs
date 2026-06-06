/**
 * Elite V2.2: Viral Intelligence - Automatic Ingredient Icon Recognition
 * Maps ingredient names to relevant viral emojis for enhanced UI/UX.
 */
export function getIngredientIcon(name: string): string {
  if (!name) return '🧬';
  
  const n = name.toLowerCase();
  
  if (n.includes('dipotassium') || n.includes('glycyrrhizate') || n.includes('cam thảo') || n.includes('rễ cây')) return '🪵';
  if (n.includes('collagen') || n.includes('atelocollagen') || n.includes('đàn hồi')) return '🧬';
  if (n.includes('ha') || n.includes('hyaluronic') || n.includes('cấp ẩm') || n.includes('moisture') || n.includes('nước')) return '💧';
  if (n.includes('vitamin c') || n.includes('lemon')) return '🍋';
  if (n.includes('niacinamide') || n.includes('b3') || n.includes('bảo vệ') || n.includes('vách ngăn')) return '🛡️';
  if (n.includes('retinol') || n.includes('chống lão hóa') || n.includes('aging') || n.includes('tái tạo')) return '🌙';
  if (n.includes('trà xanh') || n.includes('tràm trà') || n.includes('thảo mộc') || n.includes('tea') || n.includes('lá')) return '🌿';
  if (n.includes('ceramide') || n.includes('phục hồi') || n.includes('repair') || n.includes('củng cố')) return '🧬';
  if (n.includes('sáng da') || n.includes('white') || n.includes('glow') || n.includes('mờ thâm')) return '✨';
  if (n.includes('chống nắng') || n.includes('sun') || n.includes('uv') || n.includes('spf')) return '☀️';
  if (n.includes('acid') || n.includes('aha') || n.includes('bha') || n.includes('salicylic') || n.includes('peel')) return '🧪';
  if (n.includes('collagen') || n.includes('tế bào gốc') || n.includes('nâng cơ')) return '🧬';
  if (n.includes('rau má') || n.includes('centella') || n.includes('cica')) return '🌱';
  if (n.includes('lựu') || n.includes('pomegranate') || n.includes('đỏ')) return '🍎';
  if (n.includes('hoa hồng') || n.includes('rose') || n.includes('hoa')) return '🌹';
  if (n.includes('mật ong') || n.includes('honey') || n.includes('propolis')) return '🍯';
  if (n.includes('dầu') || n.includes('oil') || n.includes('olive') || n.includes('argan')) return '🫗';
  if (n.includes('than hoạt tính') || n.includes('charcoal') || n.includes('đất sét')) return '🌑';
  
  return '🧬'; // Standard science icon for unknown but technical ingredients
}

export interface CommitmentsData {
  title: string;
  subtitle: string;
  items: string[];
  fomo: string;
}

import { resolveOptimizedImageUrl } from "$lib/state/utils";

export function optimizeHtmlImages(html: string): string {
  if (!html) return '';
  return html.replace(/<img([^>]*)\s+src=["']([^"']+)["']([^>]*)>/gi, (match, before, src, after) => {
    if (src.includes('/api/v1/media/') || src.includes('/uploads/')) {
      const src412 = resolveOptimizedImageUrl(src, 412);
      const src600 = resolveOptimizedImageUrl(src, 600);
      const src800 = resolveOptimizedImageUrl(src, 800);
      
      // Clean up existing attributes to prevent duplicates
      const cleanBefore = before.replace(/\s+(loading|decoding|fetchpriority|srcset|src|sizes)=["'][^"']*["']/gi, '');
      const cleanAfter = after.replace(/\s+(loading|decoding|fetchpriority|srcset|src|sizes)=["'][^"']*["']/gi, '');
      
      return `<img${cleanBefore} src="${src600}" srcset="${src412} 412w, ${src600} 600w, ${src800} 800w" sizes="(max-width: 600px) 100vw, 600px" loading="lazy" decoding="async"${cleanAfter}>`;
    }
    return match;
  });
}

/**
 * Robust HTML Commitments Parser for Elite Storefront conversion
 */
export function parseDescriptionAndCommitments(description: string): {
  cleanDescription: string;
  commitments: CommitmentsData | null;
} {
  if (!description) {
    return { cleanDescription: '', commitments: null };
  }

  // Look for the "Cam kết" section header
  const commitRegex = /(?:<h2[^>]*>\s*Cam\s*kết\s*<\/h2>|<strong[^>]*>\s*Cam\s*kết\s*<\/strong>|<h3>\s*Cam\s*kết\s*<\/h3>)/i;
  const match = description.match(commitRegex);

  if (!match) {
    // Check if there is an implicit commitments section containing "3 Không" or "Lành tính & An toàn"
    const fallbackRegex = /(?:<p[^>]*>|<strong>)\s*(?:Cam\s*kết\s*["“]3\s*Không["”]|Lành\s*tính\s*&\s*An\s*toàn)/i;
    const fallbackMatch = description.match(fallbackRegex);
    if (!fallbackMatch) {
      return { cleanDescription: optimizeHtmlImages(description), commitments: null };
    }

    const index = fallbackMatch.index!;
    // Search backward to find nearby H2 or strong tags to split cleanly
    const searchPart = description.slice(0, index);
    const headerIndex = searchPart.lastIndexOf('<h2');
    const splitIndex = headerIndex !== -1 ? headerIndex : index;

    const cleanDescription = description.slice(0, splitIndex).trim() || description.slice(0, index).trim();
    return {
      cleanDescription: optimizeHtmlImages(cleanDescription),
      commitments: null
    };
  }

  const index = match.index!;
  const cleanDescription = description.slice(0, index).trim();

  return {
    cleanDescription: optimizeHtmlImages(cleanDescription),
    commitments: null
  };
}

export function unescapeHtml(str: string): string {
  if (!str) return '';
  return str
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, ' ');
}
