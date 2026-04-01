<script lang="ts">
  import { Music } from 'lucide-svelte';
  import type { Product } from '$lib/types';

  interface MobileVideoBannerProps {
    product: Product | null;
  }

  let { product }: MobileVideoBannerProps = $props();
  const metadata = $derived(product?.metadata ?? {});


  // Admin form saves to `video_url`; desktop hero uses `hero_video_url` as fallback.
  // Read both to stay compatible with whichever key is set.
  // Also auto-correct /static/ prefix: SvelteKit serves static/ at root (no /static prefix).
  const rawUrl = $derived.by((): string => {
    const v = (metadata.video_url as string | undefined) ?? '';
    const hv = (metadata.hero_video_url as string | undefined) ?? '';
    const url = v || hv;
    // Auto-strip erroneous /static/ prefix so /static/video/x.mp4 → /video/x.mp4
    return url.replace(/^\/static\//, '/');
  });

  type VideoMode = 'youtube' | 'tiktok' | 'local' | null;

  // Utility: extract YouTube video ID
  function getYoutubeId(url: string): string | null {
    const match = url.match(
      /(?:youtube\.com\/(?:watch\?v=|shorts\/)|youtu\.be\/)([A-Za-z0-9_-]{11})/
    );
    return match ? match[1] : null;
  }

  // Utility: extract TikTok video ID
  function getTiktokId(url: string): string | null {
    const match = url.match(/tiktok\.com\/@[\w.-]+\/video\/(\d+)/);
    return match ? match[1] : null;
  }

  // Detect video mode: youtube | tiktok | local | null
  const videoMode = $derived.by((): VideoMode => {
    if (!rawUrl) return null;
    if (getYoutubeId(rawUrl)) return 'youtube';
    if (getTiktokId(rawUrl)) return 'tiktok';
    // Local: has a video file extension OR is a relative/absolute path with video extension
    if (/\.(mp4|webm|ogg|mov)(\?.*)?$/i.test(rawUrl)) return 'local';
    return null;
  });

  // Iframe embed URL for YouTube / TikTok
  const iframeEmbedUrl = $derived.by((): string | null => {
    if (!rawUrl) return null;
    const ytId = getYoutubeId(rawUrl);
    if (ytId) {
      return `https://www.youtube.com/embed/${ytId}?autoplay=1&mute=1&loop=1&playlist=${ytId}&controls=0&playsinline=1&rel=0&modestbranding=1`;
    }
    const ttId = getTiktokId(rawUrl);
    if (ttId) {
      return `https://www.tiktok.com/embed/v2/${ttId}`;
    }
    return null;
  });

  const handle = $derived(metadata.mobile_handle as string || '@nhathuochongson.com');
  const musicLabel = $derived(metadata.mobile_music_label as string || 'Nhạc nền gốc – Elite Storefront');

  const headline = $derived(metadata.hero_headline as string || '<span>CHẤM DỨT</span> <br/> <span class="headline-shift">MÙI CƠ THỂ.</span>');
  const shortDescription = $derived(product?.shortDescription || '');
  const metrics = $derived(metadata.hero_metrics || [
    { label: '[Tốc độ]', value: 'THẨM THẤU TÀNG HÌNH 3S', color: 'blue' },
    { label: '[Hiệu quả]', value: 'PHONG TỎA MÙI 48H', color: 'indigo' },
    { label: '[Thành phần]', value: 'TINH CHẤT DƯỢC LIỆU SẠCH', color: 'emerald' }
  ]);

</script>

{#if videoMode}
  <div class="video-banner-root">
    {#if videoMode === 'local'}
      <!-- Native <video> for local/relative MP4 (e.g. /static/video/HN_TikTok.mp4) -->
      <video
        class="video-iframe"
        src={rawUrl}
        autoplay
        muted
        loop
        playsinline
        disablepictureinpicture
      >
        <track kind="captions" />
      </video>
    {:else}
      <!-- Iframe embed for YouTube / TikTok -->
      <iframe
        class="video-iframe"
        src={iframeEmbedUrl}
        title="Product Video"
        allow="autoplay; fullscreen; picture-in-picture"
        allowfullscreen
        frameborder="0"
      ></iframe>
    {/if}

    <!-- Cinematic gradient overlays -->
    <div class="gradient-top"></div>
    <div class="gradient-bottom"></div>

    <!-- Bottom-left: Content Summary -->
    <div class="meta-overlay">
      <div class="content-summary">
        <h1 class="headline tiktok-shadow">{@html headline}</h1>
        {#if shortDescription}
          <p class="description tiktok-shadow">{@html shortDescription}</p>
        {/if}
        
        <div class="metrics-grid">
          {#each metrics as metric}
            <div class="metric-item" style:--metric-color="var(--{metric.color}-400, {metric.color === 'blue' ? '#60a5fa' : metric.color === 'indigo' ? '#818cf8' : '#34d399'})">
              <div class="metric-dot"></div>
              <span class="metric-label">{metric.label}</span>
              <span class="metric-value">{metric.value}</span>
            </div>
          {/each}
        </div>
      </div>

      <div class="handle-row">
        <p class="handle tiktok-shadow">{handle}</p>
      </div>
    </div>
  </div>
{/if}

<style lang="postcss">
  .video-banner-root {
    position: relative;
    width: 100%;
    height: 100dvh;
    background: #000;
    overflow: hidden;
  }

  .video-iframe {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    border: none;
    object-fit: cover;
    pointer-events: none; /* allow swipe-to-next-section to pass through */
  }

  /* Top gradient for safe-area / notch */
  .gradient-top {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 120px;
    background: linear-gradient(to bottom, rgba(0,0,0,0.55) 0%, transparent 100%);
    pointer-events: none;
    z-index: 2;
  }

  /* Bottom gradient for meta overlay readability */
  .gradient-bottom {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 320px; /* Taller gradient for better text backdrop */
    background: linear-gradient(to top, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.6) 40%, transparent 100%);
    pointer-events: none;
    z-index: 2;
  }

  /* ── Bottom-left metadata ── */
  .meta-overlay {
    position: absolute;
    bottom: calc(var(--mobile-bottom-space) + env(safe-area-inset-bottom, 0px));
    left: 1.25rem;
    right: 5rem;
    z-index: 3;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .content-summary {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .headline {
    font-size: 1.75rem;
    font-weight: 900;
    line-height: 1.1;
    color: #fff;
    text-transform: uppercase;
    text-shadow: 0 2px 10px rgba(0,0,0,0.5);
  }

  :global(.headline-shift) {
    color: var(--blue-400, #60a5fa);
  }

  .description {
    font-size: 0.9375rem; /* Increased slightly */
    line-height: 1.5;
    color: rgba(255,255,255,1); /* Pure white for max contrast */
    font-weight: 500; /* Medium weight */
    max-width: 95%;
    display: -webkit-box;
    -webkit-line-clamp: 3; /* Show more if needed */
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-shadow: 0 1px 12px rgba(0,0,0,0.8); /* Stronger shadow */
  }

  .metrics-grid {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-top: 0.25rem;
  }

  .metric-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .metric-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--metric-color);
    box-shadow: 0 0 8px var(--metric-color);
  }

  .metric-label {
    font-size: 0.625rem;
    font-weight: 800;
    color: var(--metric-color);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    min-width: 70px;
  }

  .metric-value {
    font-size: 0.75rem;
    font-weight: 700;
    color: #fff;
  }

  .handle-row {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .handle {
    font-size: 0.9375rem;
    font-weight: 700;
    color: #fff;
  }

  .music-row {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    color: rgba(255,255,255,0.85);
  }

  :global(.music-icon) {
    width: 1rem;
    height: 1rem;
    animation: pulse 2s ease-in-out infinite;
    flex-shrink: 0;
  }

  .music-ticker-wrap {
    overflow: hidden;
    white-space: nowrap;
    max-width: 200px;
  }

  .music-ticker {
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 500;
    animation: ticker 12s linear infinite;
  }

  /* ── Keyframes ── */
  @keyframes ticker {
    0% { transform: translateX(0); }
    30% { transform: translateX(0); }
    70% { transform: translateX(-60%); }
    100% { transform: translateX(0); }
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
</style>
