<script lang="ts">
  import './MobileVideoBanner.css';
  import { resolveMediaUrl } from '$lib/state/utils';
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
    const v = (metadata.video_url as string | undefined)?.trim() ?? '';
    const hv = (metadata.hero_video_url as string | undefined)?.trim() ?? '';
    const hvr = (metadata.hero_video as string | undefined)?.trim() ?? '';
    const url = v || hv || hvr;
    // Auto-strip erroneous paths like /frontend/static/ or ./static/
    // SvelteKit serves static/ at root (no /static prefix).
    const sanitized = url.replace(/^(\.\/)?(\/)?(frontend\/)?static\//, '/');
    return resolveMediaUrl(sanitized);
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
    // Support all tiktok domains (tiktok.com, vt.tiktok.com, etc)
    if (rawUrl.includes('tiktok.com')) return 'tiktok';
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
    
    if (rawUrl.includes('tiktok.com')) {
      const ttId = getTiktokId(rawUrl);
      if (ttId) return `https://www.tiktok.com/embed/v2/${ttId}`;
      // Fallback for tiktok links where we can't extract ID immediately (like vt.tiktok.com)
      // Use the standard tiktok embed endpoint which sometimes works with full URLs
      return `https://www.tiktok.com/embed/${encodeURIComponent(rawUrl)}`;
    }
    return null;
  });

  const handle = $derived(metadata.mobile_handle as string || '@MICSMO.COM');

  const headline = $derived(metadata.hero_headline as string || '<span>ĐÁNH BAY</span> <br/> <span class="headline-shift">THÂM SẠM</span>');
  const shortDescription = $derived(product?.shortDescription || '');
  const metrics = $derived(metadata.hero_metrics || [
    { label: '[Khoa học]', value: 'LIPOSOME PHÁ GỐC THÂM', color: 'blue' },
    { label: '[Hiệu quả]', value: 'DỨT ĐIỂM HẮC SẮC TỐ', color: 'indigo' },
    { label: '[Tiêu chuẩn]', value: 'SỐ 1 DƯỢC LIỆU NHẬT', color: 'emerald' }
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
            <div class="metric-item {metric.color}">
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

