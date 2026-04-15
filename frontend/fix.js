const fs = require('fs');
const file = 'src/lib/components/client/HeroBanner.svelte';
let content = fs.readFileSync(file, 'utf8');

// Fix 1: opacity: 0.2 removal
content = content.replace('style="z-index: var(--z-bg); opacity: 0.2;"', 'style="z-index: var(--z-bg);"');

// Fix 2: EditableWrapper wrapping video
content = content.replace(
  '<EditableWrapper path="metadata.video_url" type="video" label="SỬA VIDEO NỀN">\n        {#if videoMode === \'local\'}',
  '<div class="absolute inset-0 overflow-hidden pointer-events-none" style="z-index: 0;">\n    <EditableWrapper path="metadata.video_url" type="video" label="SỬA VIDEO NỀN" class="absolute inset-0 w-full h-full pointer-events-auto flex z-10 block">\n        {#if videoMode === \'local\'}'
);

content = content.replace(
  '        {/if}\n    </EditableWrapper>\n  </div>\n\n  <div class="container mx-auto px-6 max-w-7xl',
  '        {/if}\n        <div class="video-dim-overlay pointer-events-none"></div>\n        <div class="video-vignette-top pointer-events-none"></div>\n        <div class="video-vignette-bottom pointer-events-none"></div>\n        <div class="video-vignette-radial pointer-events-none"></div>\n    </EditableWrapper>\n    </div>\n  </div>\n\n  <div class="container mx-auto px-6 max-w-7xl'
);

// Fix 3: videoMode check for local readyState
content = content.replace(
  `  const videoMode = $derived.by(() => {
    if (!videoUrl) return null;
    if (getYoutubeId(videoUrl)) return 'youtube';
    if (videoUrl.includes('tiktok.com')) return 'tiktok';
    if (/\\.(mp4|webm|ogg|mov)(\\?.*)?$/i.test(videoUrl)) return 'local';
    return 'local'; // Default to local for anything else if we want to try rendering it
  });`,
  `  const videoMode = $derived.by(() => {
    if (!videoUrl) return null;
    if (getYoutubeId(videoUrl)) return 'youtube';
    if (videoUrl.includes('tiktok.com')) return 'tiktok';
    return 'local';
  });

  const videoStartTime = $derived(
    typeof metadata.video_start_time === 'number' ? metadata.video_start_time :
    (metadata.video_start_time != null ? Number(metadata.video_start_time) : 0)
  );
  const videoEndTime = $derived.by(() => {
    if (metadata.video_end_time == null) return null;
    const n = Number(metadata.video_end_time);
    return isNaN(n) ? null : n;
  });

  let videoEl = $state(null);
  
  function handleTimeUpdate() {
    if (!videoEl) return;
    if (videoEndTime !== null && videoEl.currentTime >= videoEndTime) {
      videoEl.currentTime = videoStartTime;
      videoEl.play().catch(() => {});
    }
  }

  function handleVideoEnded() {
    if (!videoEl) return;
    videoEl.currentTime = videoStartTime;
    videoEl.play().catch(() => {});
  }

  $effect(() => {
    const el = videoEl;
    const currentUrl = videoUrl;
    const start = videoStartTime;
    const mode = videoMode;

    if (el && mode === 'local' && currentUrl) {
      if (el.readyState >= 1) {
        el.currentTime = start;
        el.play().catch(() => {});
      } else {
        el.load();
        const onMeta = () => {
          el.currentTime = start;
          el.play().catch(() => {});
        };
        el.addEventListener('loadedmetadata', onMeta, { once: true });
        return () => el.removeEventListener('loadedmetadata', onMeta);
      }
    }
  });`
);

// Update local video tag to bind 
content = content.replace(
  '<video autoplay muted loop playsinline class="elite-video-bg">',
  '<video bind:this={videoEl} ontimeupdate={handleTimeUpdate} onended={handleVideoEnded} autoplay muted playsinline class="elite-video-bg w-full h-full object-cover pointer-events-none">'
);

content = content.replace(
  '<iframe\n            class="elite-video-bg pointer-events-none"',
  '<iframe\n            class="elite-video-bg w-full h-full object-cover absolute inset-0 pointer-events-none"'
);

fs.writeFileSync(file, content);
