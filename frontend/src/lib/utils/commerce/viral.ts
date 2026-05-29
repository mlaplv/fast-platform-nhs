import { env } from '$env/dynamic/public';
import { getClientUi } from '$lib/state/commerce/ui.svelte';
import type { Product } from '$lib/types';

/**
 * Elite V2.2: Centralized Viral Utils
 */

export function getProductLikeCount(product: Product | null | undefined, isLiked: boolean): number {
  const baseCount = parseInt(env.PUBLIC_G_BY_COUNT || '569', 10);
  const seed = product?.id ? product.id.split('').reduce((acc: number, char: string) => acc + char.charCodeAt(0), 0) : 0;
  const stableRand = (seed % 41) + 10;
  const realLikes = Number(
    product?.metadata?.viral_suite?.likes_count ?? 
    product?.metadata?.likes ?? 
    0
  );
  const userInteraction = isLiked ? 1 : 0;
  return baseCount + stableRand + realLikes + userInteraction;
}

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

export function getProductShareCount(product: Product | null | undefined): number {
  const viralSuite = product?.metadata?.viral_suite ?? null;
  return Number(
    viralSuite?.share_count ?? 
    product?.metadata?.share_count ?? 
    0
  );
}

export function getProductShareTarget(product: Product | null | undefined): number {
  const viralSuite = product?.metadata?.viral_suite ?? null;
  return Number(
    viralSuite?.share_target ?? 
    product?.metadata?.share_target ?? 
    0
  );
}

export function getProductShareProgress(product: Product | null | undefined): number {
  const shareCount = getProductShareCount(product);
  const shareTarget = getProductShareTarget(product);
  return shareTarget > 0 
    ? Math.max(80, Math.min((shareCount / shareTarget) * 100, 100)) 
    : 80;
}
