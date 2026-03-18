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
  getVolume?: () => number;      // Function that returns current audio volume 0-1
  isSpeaking?: () => boolean;    // Function that returns if TTS is active
  onComplete?: () => void;
}

// Emotion: extra pause AFTER typing this character
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
  let idx = 0;
  let lastTime = 0;
  let pauseUntil = 0; // emotion pause timestamp
  let isDormant = false; // Elite 2026: Visual Continuity Shield

  node.style.willChange = "contents";

  // Elite 2026: Instant Mode
  if (speed <= 0) {
    node.textContent = text;
    isDormant = true;
    onComplete?.();
  } else {
    node.textContent = "";
  }

  function tick(ts: number) {
    if (isDormant) return;
    if (!lastTime) lastTime = ts;

    // Emotion pause: wait it out
    if (ts < pauseUntil) {
      frameId = requestAnimationFrame(tick);
      return;
    }

    const speaking = isSpeaking?.() ?? false;
    const vol = getVolume?.() ?? 0;

    if (idx >= text.length) {
      node.textContent = text;
      node.style.willChange = "auto";
      onComplete?.();
      return;
    }

    let shouldAdvance = false;

    if (speaking) {
      // ═══ VOICE-SYNC MODE ═══
      if (vol > 0.02) {
        const volSpeed = Math.max(20, 80 - vol * 100);
        if (ts - lastTime >= volSpeed) {
          shouldAdvance = true;
        }
      } else {
        if (ts - lastTime >= 150) {
          shouldAdvance = true;
        }
      }
    } else {
      // ═══ FALLBACK MODE ═══
      if (ts - lastTime >= speed) {
        shouldAdvance = true;
      }
    }

    if (shouldAdvance) {
      idx++;
      node.textContent = text.slice(0, idx);
      lastTime = ts;

      const c = text[idx - 1];
      const p = idx > 1 ? text[idx - 2] : "";
      const n = idx < text.length ? text[idx] : "";
      const extra = emotionPause(c, p, n);
      if (extra > 0) {
        pauseUntil = ts + extra;
      }
    }

    frameId = requestAnimationFrame(tick);
  }

  if (!isDormant) {
    frameId = requestAnimationFrame(tick);
  }

  return {
    update(p: TypewriterParams) {
      const isExtension = p.text.startsWith(text) && p.text.length > text.length;
      const wasSpeaking = isSpeaking?.() ?? false;
      const isStillSpeaking = p.isSpeaking?.() ?? false;

      // Elite 2026: Visual Continuity Shield
      // If speed becomes 0 OR if we stop speaking and text is same, freeze it.
      if ((p.speed ?? 60) <= 0 || (p.text === text && wasSpeaking && !isStillSpeaking)) {
        isDormant = true;
        node.textContent = p.text;
        text = p.text;
        node.style.willChange = "auto";
        if (frameId) cancelAnimationFrame(frameId);
        return;
      }

      if (p.text !== text) {
        text = p.text;
        speed = p.speed ?? 60;
        getVolume = p.getVolume;
        isSpeaking = p.isSpeaking;
        onComplete = p.onComplete;

        if (!isExtension) {
          idx = 0;
          lastTime = 0;
          pauseUntil = 0;
          isDormant = false;
          node.textContent = "";
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
