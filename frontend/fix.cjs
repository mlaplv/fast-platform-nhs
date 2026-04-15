const fs = require('fs');
const file = 'src/lib/components/client/HeroBanner.svelte';
let content = fs.readFileSync(file, 'utf8');

// Fix 1: remove opacity:0.2 & add pointer-events wrapper correctly
content = content.replace(
  'style="z-index: var(--z-bg); opacity: 0.2;"',
  'style="z-index: var(--z-bg);"'
);

// Fix 2: EditableWrapper wrapping video
content = content.replace(
  '<EditableWrapper path="metadata.video_url" type="video" label="SỬA VIDEO NỀN">\n        {#if videoMode === \'local\'}',
  '<div class="absolute inset-0 overflow-hidden pointer-events-none" style="z-index: 0;">\n    <EditableWrapper path="metadata.video_url" type="video" label="SỬA VIDEO NỀN" class="absolute inset-0 w-full h-full pointer-events-auto flex z-10 block">\n        {#if videoMode === \'local\'}'
);

content = content.replace(
  '        {/if}\n    </EditableWrapper>\n  </div>\n\n  <div class="container mx-auto px-6 max-w-7xl',
  '        {/if}\n        <!-- CSS overlays -->\n        <div class="video-dim-overlay pointer-events-none"></div>\n        <div class="video-vignette-top pointer-events-none"></div>\n        <div class="video-vignette-bottom pointer-events-none"></div>\n        <div class="video-vignette-radial pointer-events-none"></div>\n    </EditableWrapper>\n    </div>\n  </div>\n\n  <div class="container mx-auto px-6 max-w-7xl'
);


// Fix 3: videoMode check & trim logic
content = content.replace(
  "  const videoMode = $derived.by((): VideoMode => {\n    if (!videoUrl) return null;\n    if (getYoutubeId(videoUrl)) return 'youtube';\n    if (videoUrl.includes('tiktok.com')) return 'tiktok';\n    if (/\\.(mp4|webm|ogg|mov)(\\?.*)?$/i.test(videoUrl)) return 'local';\n    return 'local'; // Default to local for anything else if we want to try rendering it\n  });",
  "  const videoMode = $derived.by((): VideoMode => {\n    if (!videoUrl) return null;\n    if (getYoutubeId(videoUrl)) return 'youtube';\n    if (videoUrl.includes('tiktok.com')) return 'tiktok';\n    return 'local';\n  });\n\n  const videoStartTime = $derived(\n    typeof metadata.video_start_time === 'number' ? metadata.video_start_time :\n    (metadata.video_start_time != null ? Number(metadata.video_start_time) : 0)\n  );\n  const videoEndTime = $derived.by((): number | null => {\n    if (metadata.video_end_time == null) return null;\n    const n = Number(metadata.video_end_time);\n    return isNaN(n) ? null : n;\n  });\n\n  let videoEl: HTMLVideoElement | null = $state(null);\n  \n  function handleTimeUpdate() {\n    if (!videoEl) return;\n    if (videoEndTime !== null && videoEl.currentTime >= videoEndTime) {\n      videoEl.currentTime = videoStartTime;\n      videoEl.play().catch(() => {});\n    }\n  }\n\n  function handleVideoEnded() {\n    if (!videoEl) return;\n    videoEl.currentTime = videoStartTime;\n    videoEl.play().catch(() => {});\n  }\n\n  $effect(() => {\n    const el = videoEl;\n    const currentUrl = videoUrl;\n    const start = videoStartTime;\n    const mode = videoMode;\n\n    if (el && mode === 'local' && currentUrl) {\n      if (el.readyState >= 1) {\n        el.currentTime = start;\n        el.play().catch(() => {});\n      } else {\n        el.load();\n        const onMeta = () => {\n          el.currentTime = start;\n          el.play().catch(() => {});\n        };\n        el.addEventListener('loadedmetadata', onMeta, { once: true });\n        return () => el.removeEventListener('loadedmetadata', onMeta);\n      }\n    }\n  });"
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
