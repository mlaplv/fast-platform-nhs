<script lang="ts">
  import './MobileVideoBanner.css';
  import { resolveMediaUrl } from '$lib/state/utils';
  import type { Product } from '$lib/types';
  import EditableWrapper from '../../admin/EditableWrapper.svelte';
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';

  interface MobileVideoBannerProps {
    product: Product | null;
  }

  let { product }: MobileVideoBannerProps = $props();
  const isEditMode = $derived(liveEditStore.isEditMode);
  // Elite V2.2: Reactive sync with editor state
  const metadata = $derived(isEditMode ? liveEditStore.dirtyMetadata : (product?.metadata ?? {}));


  // Admin form saves to `video_url`; desktop hero uses `hero_video_url` as fallback.
  // Read both to stay compatible with whichever key is set.
  // Also auto-correct /static/ prefix: SvelteKit serves static/ at root (no /static prefix).
  const rawUrl = $derived.by((): string => {
    const v = (metadata.video_url as string | undefined)?.trim() ?? '';
    const hv = (metadata.hero_video_url as string | undefined)?.trim() ?? '';
    const hvr = (metadata.hero_video as string | undefined)?.trim() ?? '';
    let url = v || hv || hvr;
    if (!url) return '';
    
    // Elite V2.2: Intelligent Path Sanitization
    // If it's already a full URL or starts with / (already resolved), keep it.
    if (url.startsWith('http') || url.startsWith('//') || url.startsWith('blob:')) return url;
    
    // Auto-strip erroneous paths like /frontend/static/ or ./static/
    const sanitized = url.replace(/^(\.\/)?(\/)?(frontend\/)?static\//, '/');
    
    // If it now starts with / (was static), don't pass it to resolveMediaUrl (which aliases to /uploads/)
    if (sanitized.startsWith('/')) return sanitized;
    
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
    
    // Elite V2.2: Local-First Robust Fallback
    // If it's not a known stream provider and has content, attempt native playback
    return 'local';
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
  const metrics = $derived.by(() => {
    const raw = metadata.hero_metrics || [];
    const fallbacks = [
      { label: '[Khoa học]', value: 'LIPOSOME PHÁ GỐC THÂM', color: 'blue' },
      { label: '[Hiệu quả]', value: 'DỨT ĐIỂM HẮC SẮC TỐ', color: 'indigo' },
      { label: '[Tiêu chuẩn]', value: 'SỐ 1 DƯỢC LIỆU NHẬT', color: 'emerald' }
    ];

    return fallbacks.map((fb, i) => {
      const custom = raw[i];
      if (!custom) return fb;
      return {
        label: custom.label || fb.label,
        value: custom.value || fb.value,
        color: custom.color || fb.color
      };
    });
  });

</script>

<div class="video-banner-root">
    {#if videoMode}
      <EditableWrapper path="metadata.video_url" type="video" label="SỬA VIDEO BANNER" class="w-full h-full z-0">
        {#if videoMode === 'local'}
          <!-- Native <video> for local/relative MP4 (e.g. /static/video/HN_TikTok.mp4) -->
          <video
            class="video-element video-local absolute inset-0"
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
          <div class="video-element video-iframe-wrapper absolute inset-0">
            <iframe
              src={iframeEmbedUrl}
              title="Product Video"
              allow="autoplay; fullscreen; picture-in-picture"
              allowfullscreen
              frameborder="0"
            ></iframe>
          </div>
        {/if}
      </EditableWrapper>
    {/if}

    <!-- Cinematic gradient overlays -->
    <div class="gradient-top"></div>
    <div class="gradient-bottom"></div>

    <!-- Bottom-left: Content Summary -->
    <div class="meta-overlay">
      <div class="content-summary">
        <EditableWrapper path="metadata.hero_headline" type="html" label="SỬA TIÊU ĐỀ">
          <h1 class="headline tiktok-shadow">{@html headline}</h1>
        </EditableWrapper>
        
        {#if shortDescription}
          <EditableWrapper path="shortDescription" type="html" label="SỬA MÔ TẢ">
            <p class="description tiktok-shadow">{@html shortDescription}</p>
          </EditableWrapper>
        {/if}
        
        <div class="metrics-grid">
          {#each metrics as metric, i}
            <div class="metric-item {metric.color}">
              <div class="metric-dot"></div>
              <EditableWrapper path="metadata.hero_metrics.{i}.label" value={metric.label} label="SỬA NHÃN {i+1}">
                <span class="metric-label">{metric.label}</span>
              </EditableWrapper>
              <EditableWrapper path="metadata.hero_metrics.{i}.value" value={metric.value} label="SỬA GIÁ TRỊ {i+1}">
                <span class="metric-value">{metric.value}</span>
              </EditableWrapper>
            </div>
          {/each}
        </div>
      </div>

      <div class="handle-row">
        <EditableWrapper path="metadata.mobile_handle" label="SỬA HANDLE">
          <p class="handle tiktok-shadow">{handle}</p>
        </EditableWrapper>
      </div>
    </div>
  </div>
