/**
 * Purify Utility (V2026)
 * Surgical artifact stripping and content cleaning for AI-generated drafts and outlines.
 * Rules: Zero-dependency, Full Type Safety, No 'any'.
 */

export interface PurificationOptions {
  stripBackticks?: boolean;
  stripCodeBlocks?: boolean;
  trim?: boolean;
}

/**
 * Strips markdown code block artifacts (e.g., ```html ... ```) from a string.
 */
export function stripMarkdownArtifacts(content: string): string {
  if (!content) return "";
  
  return content
    .replace(/```[a-z]*\n?|```/gi, '') 
    .replace(/^\s*[\r\n]+|[\r\n]+\s*$/g, '')
    .trim();
}

/**
 * Master purification function for AI content.
 */
export function purifyAIContent(content: string | null | undefined, options: PurificationOptions = {}): string {
  const { stripBackticks = true, trim = true } = options;
  
  let result = content || "";
  
  if (stripBackticks) {
    result = stripMarkdownArtifacts(result);
  }
  
  if (trim) {
    result = result.trim();
  }
  
  return result;
}
