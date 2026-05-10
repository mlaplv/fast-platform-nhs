import { getClientUi } from '$lib/state/commerce/ui.svelte';

/**
 * Elite V2.2: Centralized Viral Utils
 */

export function formatViralCount(count: number): string {
  if (count >= 1000) return (count / 1000).toFixed(1).replace('.0', '') + 'k';
  return count.toString();
}

export async function shareToPlatform(platform: string, url: string, title: string, onComplete?: () => void) {
  if (typeof window === 'undefined') return;
  
  const encodedUrl = encodeURIComponent(url);
  const platforms: Record<string, string> = {
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`,
    zalo: `https://sp.zalo.me/plugins/share?url=${encodedUrl}`,
    twitter: `https://twitter.com/intent/tweet?url=${encodedUrl}&text=${encodeURIComponent(title)}`,
    linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl}`
  };

  const shareUrl = platforms[platform];
  
  if (shareUrl) {
    window.open(shareUrl, '_blank', 'width=600,height=400');
    onComplete?.();
  } else if (platform === 'copy') {
    await copyViralLink(url);
    onComplete?.();
  }
}

export async function copyViralLink(url: string) {
  if (typeof navigator === 'undefined' || !navigator.clipboard) return;
  await navigator.clipboard.writeText(url);
  const ui = getClientUi();
  ui.showToast('Đã sao chép đường dẫn', 'success');
}

export function createHeartConfetti(clientX: number, clientY: number) {
  if (typeof document === 'undefined') return;
  
  const container = document.createElement('div');
  container.className = 'vsb-heart-burst';
  container.style.left = `${clientX}px`;
  container.style.top = `${clientY}px`;
  document.body.appendChild(container);
  
  const emojis = ['❤️', '💖', '✨', '🌸', '🔥'];
  for (let i = 0; i < 12; i++) {
    const p = document.createElement('div');
    p.className = 'vsb-heart-particle';
    p.style.setProperty('--i', i.toString());
    p.style.setProperty('--delay', (Math.random() * 0.2).toString() + 's');
    p.innerHTML = emojis[Math.floor(Math.random() * emojis.length)];
    container.appendChild(p);
  }
  
  setTimeout(() => {
    if (container.parentNode) {
      container.remove();
    }
  }, 1000);
}
