/**
 * R50 + R52: Voice-Synced Typewriter.
 *
 * Types text in sync with TTS audio output:
 * - When voice volume > threshold → advance characters
 * - When voice pauses → text pauses too
 * - Emotion-aware: extra pause at punctuation
 * - Fallback: if no voice playing, types at steady pace
 */

interface TypewriterParams {
  text: string;
  speed?: number;
  getVolume?: () => number;
  isSpeaking?: () => boolean;
  onComplete?: () => void;
}

interface Token {
  text: string;
  delay: number;
}

function emotionPause(char: string, prev: string, next: string): number {
  if (char === "." && prev === "." && next !== ".") return 350;
  if (char === "." && next === ".") return 0;
  if (char === "!") return 300;
  if (char === "?") return 280;
  if (char === "." && (next === " " || !next)) return 240;
  if (char === ",") return 130;
  if (char === ":" || char === ";") return 170;
  if (char === "\n") return 200;
  return 0;
}

export function typewriter(node: HTMLElement, params: TypewriterParams) {
  let { text, speed = 60, getVolume, isSpeaking, onComplete } = params;
  let frameId: number | null = null;
  let tokenIdx: number = 0;
  let lastTime: number = 0;
  let pauseUntil: number = 0; 
  let isDormant: boolean = false; 
  let currentHTML: string = "";

  node.style.willChange = "contents";

  const segmenter: Intl.Segmenter | null = (typeof Intl !== 'undefined' && "Segmenter" in Intl) 
    ? new Intl.Segmenter("vi", { granularity: "grapheme" }) 
    : null;

  function tokenize(input: string): Token[] {
    const normalized = (input || "").normalize('NFC');
    const parts = normalized.split(/(<[^>]+>)/g);
    const result: Token[] = [];
    
    for (const part of parts) {
      if (part.startsWith("<")) {
        result.push({ text: part, delay: 0 });
      } else {
        if (segmenter) {
          const segments = segmenter.segment(part);
          for (const { segment } of segments) {
            result.push({ text: segment, delay: speed });
          }
        } else {
          for (const char of part) {
            result.push({ text: char, delay: speed });
          }
        }
      }
    }
    return result;
  }

  let tokens: Token[] = tokenize(text);

  if (speed <= 0) {
    node.innerHTML = text;
    isDormant = true;
    onComplete?.();
  } else {
    node.innerHTML = "";
  }

  function tick(ts: number) {
    if (isDormant) return;
    if (!lastTime) lastTime = ts;

    if (ts < pauseUntil) {
      frameId = requestAnimationFrame(tick);
      return;
    }

    if (tokenIdx >= tokens.length) {
      node.innerHTML = text;
      node.style.willChange = "auto";
      onComplete?.();
      return;
    }

    const speaking = isSpeaking?.() ?? false;
    const vol = getVolume?.() ?? 0;

    let shouldAdvance = false;
    const currentDelay = tokens[tokenIdx].delay;

    if (speaking) {
      if (vol > 0.02) {
        const volSpeed = Math.max(20, 80 - vol * 100);
        if (ts - lastTime >= volSpeed) shouldAdvance = true;
      } else {
        if (ts - lastTime >= 150) shouldAdvance = true;
      }
    } else {
      if (ts - lastTime >= currentDelay) {
        shouldAdvance = true;
      }
    }

    if (shouldAdvance) {
      const token = tokens[tokenIdx];
      currentHTML += token.text;
      tokenIdx++;
      
      node.innerHTML = currentHTML;
      lastTime = ts;

      if (token.delay > 0) {
        const c = token.text;
        const prev = tokenIdx > 1 ? tokens[tokenIdx - 2].text : "";
        const next = tokenIdx < tokens.length ? tokens[tokenIdx].text : "";
        const extra = emotionPause(c, prev, next);
        if (extra > 0) {
          pauseUntil = ts + extra;
        }
      } else {
        tick(ts);
        return;
      }
    }

    frameId = requestAnimationFrame(tick);
  }

  if (!isDormant) {
    frameId = requestAnimationFrame(tick);
  }

  return {
    update(p: TypewriterParams) {
      const wasSpeaking = isSpeaking?.() ?? false;
      const isStillSpeaking = p.isSpeaking?.() ?? false;

      if ((p.speed ?? 60) <= 0 || (p.text === text && wasSpeaking && !isStillSpeaking)) {
        isDormant = true;
        node.innerHTML = p.text;
        text = p.text;
        node.style.willChange = "auto";
        if (frameId) cancelAnimationFrame(frameId);
        return;
      }

      if (p.text !== text) {
        const isExtension = p.text.startsWith(text) && p.text.length > text.length;
        text = p.text;
        speed = p.speed ?? 60;
        getVolume = p.getVolume;
        isSpeaking = p.isSpeaking;
        onComplete = p.onComplete;
        
        const newTokens = tokenize(p.text);
        if (isExtension) {
            tokens = newTokens;
        } else {
            tokens = newTokens;
            tokenIdx = 0;
            currentHTML = "";
            lastTime = 0;
            pauseUntil = 0;
            isDormant = false;
            node.innerHTML = "";
        }

        node.style.willChange = "contents";
        if (frameId) cancelAnimationFrame(frameId);
        frameId = requestAnimationFrame(tick);
      }
    },
    destroy() {
      if (frameId) cancelAnimationFrame(frameId);
      node.style.willChange = "auto";
    },
  };
}
