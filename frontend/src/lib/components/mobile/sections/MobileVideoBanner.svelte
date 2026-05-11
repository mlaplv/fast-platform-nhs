<script lang="ts">
  import { untrack } from 'svelte';
  import './MobileVideoBanner.css';
  import { resolveMediaUrl } from '$lib/state/utils';
  import type { Product } from '$lib/types';
  import EditableWrapper from '../../admin/EditableWrapper.svelte';
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';

  let { product: propProduct } = $props<{ product: Product | null }>();
  const shopStore = getShopStore();
  const product = $derived(liveEditStore.isEditMode && liveEditStore.dirtyProduct ? liveEditStore.dirtyProduct : (propProduct || shopStore.product));
  const metadata = $derived(product?.metadata || {});

  const stripTags = (h: string) => h ? h.replace(/<[^>]*>?/gm, '').trim() : '';
  const legacyParts = $derived(metadata.hero_headline?.split('<br/>') || []);
  const h1 = $derived(metadata.hero_headline_1 || stripTags(legacyParts[0]) || 'ĐÁNH BAY');
  const h2 = $derived(metadata.hero_headline_2 || stripTags(legacyParts[1]) || 'THÂM SẠM');

  const rawUrl = $derived.by((): string => {
    const v = (metadata.video_url as string | undefined)?.trim() ?? '';
    const hv = (metadata.hero_video_url as string | undefined)?.trim() ?? '';
    const hvr = (metadata.hero_video as string | undefined)?.trim() ?? '';
    let url = v || hv || hvr;
    if (!url) return '';
    if (url.startsWith('http') || url.startsWith('//') || url.startsWith('blob:')) return url;
    const sanitized = url.replace(/^(\.\/)?(\/)?(frontend\/)?static\//, '/');
    if (sanitized.startsWith('/')) return sanitized;
    return resolveMediaUrl(sanitized);
  });

  const videoUrl = $derived(rawUrl);
  type VideoMode = 'youtube' | 'tiktok' | 'local' | null;

  function getYoutubeId(url: string): string | null {
    const match = url.match(/(?:youtube\.com\/(?:watch\?v=|shorts\/)|youtu\.be\/)([A-Za-z0-9_-]{11})/);
    return match ? match[1] : null;
  }

  function getTiktokId(url: string): string | null {
    const match = url.match(/tiktok\.com\/@[\w.-]+\/video\/(\d+)/);
    return match ? match[1] : null;
  }

  const videoMode = $derived.by((): VideoMode => {
    if (!videoUrl) return null;
    if (getYoutubeId(videoUrl)) return 'youtube';
    if (videoUrl.includes('tiktok.com')) return 'tiktok';
    return 'local';
  });

  const videoStartTime = $derived(Number(metadata.video_start_time) || 0);
  const videoEndTime = $derived(Number(metadata.video_end_time) || 0);

  let videoEl = $state<HTMLVideoElement | null>(null);
  let hasSeekedInitial = $state(false);

  function handleTimeUpdate() {
    if (!videoEl) return;
    const currentStart = videoStartTime;
    const currentEnd = videoEndTime;

    // Initial Seek Protection (Untracked)
    if (!untrack(() => hasSeekedInitial) && currentStart > 0) {
      if (videoEl.currentTime < currentStart - 0.5) {
        videoEl.currentTime = currentStart;
        hasSeekedInitial = true;
      }
    }

    if (currentEnd > 0 && videoEl.currentTime >= currentEnd) {
      videoEl.currentTime = currentStart;
      videoEl.play().catch(() => {});
    }
  }

  $effect(() => {
    // Track dependencies to trigger reset
    videoUrl; videoStartTime; videoEndTime;
    
    untrack(() => {
      hasSeekedInitial = false;
    });

    if (videoEl && videoMode === 'local') {
      const onSeek = () => {
        if (videoEl && !untrack(() => hasSeekedInitial)) {
          videoEl.currentTime = videoStartTime;
          hasSeekedInitial = true;
          videoEl.play().catch(() => {});
        }
      };
      
      videoEl.addEventListener('loadedmetadata', onSeek, { once: true });
      videoEl.addEventListener('canplay', onSeek, { once: true });
      if (videoEl.readyState >= 1) onSeek();

      return () => {
        videoEl?.removeEventListener('loadedmetadata', onSeek);
        videoEl?.removeEventListener('canplay', onSeek);
      };
    }
  });

  const iframeEmbedUrl = $derived.by((): string | null => {
    if (!videoUrl) return null;
    const ytId = getYoutubeId(videoUrl);
    if (ytId) {
      let url = `https://www.youtube.com/embed/${ytId}?autoplay=1&mute=1&loop=1&playlist=${ytId}&controls=0&playsinline=1&rel=0&modestbranding=1`;
      if (videoStartTime) url += `&start=${videoStartTime}`;
      if (videoEndTime) url += `&end=${videoEndTime}`;
      return url;
    }
    if (videoUrl.includes('tiktok.com')) {
      const ttId = getTiktokId(videoUrl);
      if (ttId) return `https://www.tiktok.com/embed/v2/${ttId}`;
      return `https://www.tiktok.com/embed/${encodeURIComponent(videoUrl)}`;
    }
    return null;
  });

  const handle = $derived(metadata.mobile_handle as string || '@osmo');
  const metrics = $derived.by(() => {
    const raw = metadata.hero_metrics || [];
    const fallbacks = [
      { label: '[Khoa học]', value: 'LIPOSOME PHÁ GỐC THÂM', color: 'sakura' },
      { label: '[Hiệu quả]', value: 'DỨT ĐIỂM HẮC SẾT TỐ', color: 'sakura' },
      { label: '[Tiêu chuẩn]', value: 'SỐ 1 DƯỢC LIỆU NHẬT', color: 'sakura' }
    ];
    return fallbacks.map((fb, i) => {
      const custom = raw[i];
      if (!custom) return fb;
      return { label: custom.label || fb.label, value: custom.value || fb.value, color: custom.color || fb.color };
    });
  });
</script>

<div class="video-banner-root">
    {#if videoMode}
      <EditableWrapper path="metadata.video_url" type="video" label="SỬA VIDEO BANNER" class="w-full h-full z-0">
        {#if videoMode === 'local'}
          <video
            bind:this={videoEl}
            ontimeupdate={handleTimeUpdate}
            class="video-element video-local absolute inset-0"
            src={videoUrl}
            autoplay
            muted
            loop
            playsinline
            disablepictureinpicture
          >
            <track kind="captions" />
          </video>
        {:else}
          {#key iframeEmbedUrl}
            <div class="video-element video-iframe-wrapper absolute inset-0">
              <iframe
                src={iframeEmbedUrl}
                title="Product Video"
                allow="autoplay; fullscreen; picture-in-picture"
                allowfullscreen
                frameborder="0"
              ></iframe>
            </div>
          {/key}
        {/if}
      </EditableWrapper>
    {/if}

    <div class="gradient-top"></div>
    <div class="gradient-bottom"></div>

    <div class="meta-overlay">
      <div class="content-overlay">
      <h2 class="headline">
        <EditableWrapper path="metadata.hero_headline_1" type="text" label="SỬA TIÊU ĐỀ 1" class="inline" as="span">
          {h1}
        </EditableWrapper>
        <br/>
        <span class="headline-shift">
          <EditableWrapper path="metadata.hero_headline_2" type="text" label="SỬA TIÊU ĐỀ 2" class="inline" as="span">
            {h2}
          </EditableWrapper>
        </span>
      </h2>
        
        {#if product?.shortDescription}
          <p class="description tiktok-shadow">
            <EditableWrapper path="shortDescription" label="SỬA MÔ TẢ" as="span">
              {product.shortDescription}
            </EditableWrapper>
          </p>
        {/if}
        
        <div class="metrics-grid">
          {#each metrics as metric, i}
            <div class="metric-item">
              <div class="metric-dot"></div>
              <span class="metric-label whitespace-nowrap text-sakura-pink">{metric.label}</span>
              <span class="metric-value whitespace-nowrap">{metric.value}</span>
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
