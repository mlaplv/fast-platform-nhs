/**
 * V45.0: Passive Telemetry State
 * Reactive latency measured from real API traffic (zero extra requests).
 * Separate .svelte.ts file because $state runes require Svelte-aware compilation.
 */

const latency = $state({ ms: null as number | null });

export const globalLatency = {
  get ms() {
    return latency.ms;
  },
  set(val: number) {
    latency.ms = val;
  },
};
