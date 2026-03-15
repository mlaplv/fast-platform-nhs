import { SIGNAL_THROTTLE_MS } from "./utils";
import { permissionState } from "../permissions.svelte";

interface AudioThrottleDeps {
  state: {
    signalQueue: string[];
    audioUnlocked: boolean;
  };
}

export function createAudioThrottle(state: AudioThrottleDeps["state"]) {
  let lastSpeakTime = 0;
  let signalThrottleTimer: ReturnType<typeof setTimeout> | null = null;

  const flushSignalQueue = async () => {
    if (signalThrottleTimer) {
      clearTimeout(signalThrottleTimer);
      signalThrottleTimer = null;
    }
    if (state.signalQueue.length === 0 || !state.audioUnlocked) return;

    const now = Date.now();
    const waitTime = Math.max(0, SIGNAL_THROTTLE_MS - (now - lastSpeakTime));

    if (waitTime > 0) {
      signalThrottleTimer = setTimeout(flushSignalQueue, waitTime);
      return;
    }

    // Determine what to speak
    const queue = [...state.signalQueue];
    state.signalQueue = [];

    let toSpeak = "";
    if (queue.length === 1) {
      toSpeak = queue[0];
    } else {
      // Rule R81.68: Auto-Summarization
      const userName = (permissionState as { userName?: string }).userName || 'Admin';
      toSpeak = `Hệ thống có ${queue.length} cập nhật mới cho ${userName}.`;
    }

    if (toSpeak) {
      lastSpeakTime = Date.now();
      const { vuiController } = await import("$lib/vui");
      vuiController.speak(toSpeak);
    }
  };

  return {
    get lastSpeakTime() { return lastSpeakTime; },
    setLastSpeakTime: (val: number) => (lastSpeakTime = val),
    flushSignalQueue,
    get isThrottling() { return !!signalThrottleTimer; },
    scheduleFlush: () => {
      if (!signalThrottleTimer && state.audioUnlocked) {
        signalThrottleTimer = setTimeout(flushSignalQueue, SIGNAL_THROTTLE_MS);
      }
    }
  };
}
