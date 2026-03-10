/**
 * R50-compliant Sci-Fi SFX — Zero-Byte Audio using Web Audio API.
 * No MP3, no external files. Pure OscillatorNode synthesis.
 */

let _sfxCtx: AudioContext | null = null;

function getSfxCtx(): AudioContext {
  if (!_sfxCtx || _sfxCtx.state === "closed") {
    const Ctor = window.AudioContext || (window as any).webkitAudioContext;
    _sfxCtx = new Ctor();
  }
  // R85.2: Autoplay safety — only attempt resume if suspended, and silent catch
  if (_sfxCtx.state === "suspended") {
    _sfxCtx.resume().catch(() => {
      /* Silently ignore autoplay restrictions */
    });
  }
  return _sfxCtx;
}

/**
 * Sci-Fi system wake-up beep — 150ms dual-tone chirp.
 */
export function playSciFiBeep(): void {
  try {
    const ctx = getSfxCtx();
    const now = ctx.currentTime;

    const osc1 = ctx.createOscillator();
    osc1.type = "sine";
    osc1.frequency.setValueAtTime(1200, now);
    osc1.frequency.exponentialRampToValueAtTime(1800, now + 0.08);
    osc1.frequency.exponentialRampToValueAtTime(2000, now + 0.15);

    const osc2 = ctx.createOscillator();
    osc2.type = "square";
    osc2.frequency.setValueAtTime(600, now);
    osc2.frequency.exponentialRampToValueAtTime(900, now + 0.15);

    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(0.15, now + 0.01);
    gain.gain.setValueAtTime(0.15, now + 0.06);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);

    const gain2 = ctx.createGain();
    gain2.gain.setValueAtTime(0.03, now);
    gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.15);

    osc1.connect(gain).connect(ctx.destination);
    osc2.connect(gain2).connect(ctx.destination);

    osc1.start(now);
    osc2.start(now);
    osc1.stop(now + 0.16);
    osc2.stop(now + 0.16);
  } catch {}
}

/**
 * Short confirmation "tick" — 50ms click for button feedback.
 */
export function playTick(): void {
  try {
    const ctx = getSfxCtx();
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    osc.type = "sine";
    osc.frequency.setValueAtTime(2400, now);
    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0.08, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
    osc.connect(gain).connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.06);
  } catch {}
}

/**
 * Siri-style "ding-ding" — two-note ascending chime for mic activation.
 * Note 1: E6 (1318Hz) → Note 2: G6 (1568Hz), 100ms gap.
 */
export function playSiriDing(): void {
  try {
    const ctx = getSfxCtx();
    const now = ctx.currentTime;

    // Note 1: E6
    const o1 = ctx.createOscillator();
    o1.type = "sine";
    o1.frequency.setValueAtTime(1318, now);
    const g1 = ctx.createGain();
    g1.gain.setValueAtTime(0, now);
    g1.gain.linearRampToValueAtTime(0.18, now + 0.008);
    g1.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
    o1.connect(g1).connect(ctx.destination);
    o1.start(now);
    o1.stop(now + 0.13);

    // Note 2: G6 (higher, after gap)
    const o2 = ctx.createOscillator();
    o2.type = "sine";
    o2.frequency.setValueAtTime(1568, now + 0.1);
    const g2 = ctx.createGain();
    g2.gain.setValueAtTime(0, now + 0.1);
    g2.gain.linearRampToValueAtTime(0.2, now + 0.108);
    g2.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
    o2.connect(g2).connect(ctx.destination);
    o2.start(now + 0.1);
    o2.stop(now + 0.23);
  } catch {}
}
