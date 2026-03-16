<script lang="ts">
  import { vuiState } from "$lib/vui";
  import { onMount } from "svelte";

  // VUI 2026: Neural Visualization Parameters
  const CORE_RADIUS = 40;
  const BLOB_COUNT = 4;

  // Reactive state for blobs
  let blobs = $state(
    Array.from({ length: BLOB_COUNT }, (_, i) => ({
      id: i,
      x: 0,
      y: 0,
      size: 15 + Math.random() * 15,
      angle: (i / BLOB_COUNT) * Math.PI * 2,
      speed: 0.02 + Math.random() * 0.03,
      distance: 30 + Math.random() * 20
    }))
  );

  // Derived values for animation
  let volumeFactor = $derived(vuiState.volume * 2);
  let activityFactor = $derived(vuiState.speechProb);
  let phase = $derived(vuiState.phase);

  let animationFrame: number;
  let time = 0;

  const update = () => {
    time += 0.016; // Approx 60fps

    // Smooth transition factor for different phases
    let speedMult = 1;
    let distMult = 1;

    if (phase === 'thinking') {
      speedMult = 3;
      distMult = 0.5; // Merge into center
    } else if (phase === 'speaking') {
      speedMult = 1.5;
      distMult = 1.2 + volumeFactor;
    } else if (phase === 'listening') {
      speedMult = 1 + activityFactor * 2;
      distMult = 1 + activityFactor + volumeFactor;
    } else {
      // Idle / Error
      speedMult = 0.5;
      distMult = 0.8;
    }

    blobs.forEach((blob, i) => {
      blob.angle += blob.speed * speedMult;
      const currentDist = blob.distance * distMult;

      // Add some noise/wobble
      const wobble = Math.sin(time + i) * 5 * activityFactor;

      blob.x = Math.cos(blob.angle) * (currentDist + wobble);
      blob.y = Math.sin(blob.angle) * (currentDist + wobble);
    });

    animationFrame = requestAnimationFrame(update);
  };

  onMount(() => {
    animationFrame = requestAnimationFrame(update);
    return () => cancelAnimationFrame(animationFrame);
  });

  // Dynamic colors based on phase - Svelte 5 Optimized Derived
  let orbColor = $derived(
    phase === 'thinking' ? '#6366f1' :
    phase === 'speaking' ? '#10b981' :
    phase === 'error' ? '#ef4444' :
    phase === 'listening' ? (vuiState.speechProb > 0.5 ? '#f59e0b' : '#3b82f6') :
    '#94a3b8'
  );
</script>

<div class="voice-orb-container w-64 h-64 flex items-center justify-center relative pointer-events-none">
  <!-- The SVG Metaball Filter -->
  <svg width="0" height="0" class="absolute">
    <defs>
      <filter id="metaball">
        <feGaussianBlur in="SourceGraphic" stdDeviation="10" result="blur" />
        <feColorMatrix
          in="blur"
          mode="matrix"
          values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 20 -10"
          result="goo"
        />
        <feComposite in="SourceGraphic" in2="goo" operator="atop" />
      </filter>
    </defs>
  </svg>

  <!-- The Actual Orb -->
  <svg viewBox="-150 -150 300 300" class="w-full h-full drop-shadow-2xl">
    <g filter="url(#metaball)">
      <!-- Core -->
      <circle
        cx="0" cy="0"
        r={CORE_RADIUS + (volumeFactor * 10)}
        fill={orbColor}
        class="transition-colors duration-500"
      />

      <!-- Blobs -->
      {#each blobs as blob}
        <circle
          cx={blob.x}
          cy={blob.y}
          r={blob.size * (1 + (volumeFactor * 0.5))}
          fill={orbColor}
          class="transition-colors duration-500"
        />
      {/each}
    </g>

    <!-- Neural Ring (Thinking Phase) -->
    {#if phase === 'thinking'}
      <circle
        cx="0" cy="0"
        r={CORE_RADIUS + 20}
        fill="none"
        stroke={orbColor}
        stroke-width="2"
        stroke-dasharray="10 20"
        class="animate-spin-slow opacity-50"
      />
    {/if}
  </svg>

  <!-- Inner Pulse for feedback -->
  {#if phase === 'listening' && vuiState.speechProb > 0.1}
    <div
      class="absolute w-12 h-12 rounded-full bg-white/20 animate-ping"
      style="animation-duration: {1000 / (1 + volumeFactor)}ms"
    ></div>
  {/if}
</div>

<style>
  .voice-orb-container {
    filter: drop-shadow(0 0 20px rgba(0,0,0,0.5));
  }

  @keyframes spin-slow {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .animate-spin-slow {
    animation: spin-slow 8s cubic-bezier(0.4, 0, 0.2, 1) infinite;
    transform-origin: center;
  }

</style>
