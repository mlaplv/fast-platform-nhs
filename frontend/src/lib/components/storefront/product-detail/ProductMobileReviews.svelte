<script lang="ts">
  import EliteReviewSystem from './reviews/EliteReviewSystem.svelte';
  
  interface Props {
    product: { id: string; name: string; slug: string };
    entityType?: 'PRODUCT' | 'CATEGORY' | 'NEWS';
  }
  let { product, entityType = 'PRODUCT' }: Props = $props();
</script>

<section id="reviews" class="content-section bg-white p-4">
  <div class="flex justify-between items-center mb-6">
    <h2 class="text-sm font-black text-gray-900 uppercase tracking-tight">Cảm nhận thực tế</h2>
    <a href="/{product.slug}/reviews" class="text-xs font-bold text-luxury-copper flex items-center gap-1">
      Xem tất cả
    </a>
  </div>

  <EliteReviewSystem 
    entityId={product.id} 
    {entityType} 
    mode="snippet" 
  />

  <div class="fomo-footer mt-6 p-4 bg-luxury-peach/5 rounded-2xl border border-luxury-peach/10">
    <div class="flex items-center justify-between">
      <div>
        <span class="block text-[10px] font-black text-luxury-copper uppercase tracking-tighter">Độ tin cậy 100%</span>
        <span class="text-[9px] text-gray-400 font-bold uppercase mt-0.5">Xác thực từ người mua hàng</span>
      </div>
      <a href="/{product.slug}/reviews" class="px-4 py-2 bg-luxury-copper text-white text-[10px] font-black rounded-lg uppercase">
        Khám phá
      </a>
    </div>
  </div>
</section>

<style>
  .content-section { background: white; padding: 16px; }
  .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
  .section-title { font-size: 14px; font-weight: 800; color: #222; margin: 0; text-transform: uppercase; letter-spacing: -0.01em; }
  .view-all { font-size: 12px; display: flex; align-items: center; gap: 4px; font-weight: 600; text-decoration: none; }

  .score-big { font-size: 24px; font-weight: 900; color: #333; display: flex; align-items: baseline; gap: 2px; }
  .score-big span { font-size: 14px; color: #999; font-weight: 500; }

  .viral-review-card { position: relative; }
  .user-row { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
  .avatar { width: 40px; height: 40px; background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: 900; color: #666; border: 1px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
  .user-meta { flex: 1; }
  .username { font-size: 13px; font-weight: 700; color: #222; }
  .review-date-mini { font-size: 10px; color: #bbb; font-weight: 500; }

  .review-content { margin-bottom: 12px; font-size: 14px; color: #444; line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }

  .media-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-bottom: 4px; }
  .media-item { aspect-ratio: 1; border-radius: 8px; overflow: hidden; position: relative; background: #f9f9f9; border: 1px solid #f0f0f0; }
  .media-preview { width: 100%; height: 100%; object-fit: cover; }
  .play-overlay { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.2); }
  .media-more { position: absolute; bottom: 10px; right: 10px; width: 32px; height: 32px; border-radius: 50%; background: rgba(0,0,0,0.6); color: white; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 900; }

  .btn-discover { color: white; font-size: 10px; font-weight: 900; padding: 6px 12px; border-radius: 4px; text-decoration: none; text-transform: uppercase; letter-spacing: 0.5px; box-shadow: 0 4px 10px rgba(193, 143, 126, 0.2); }

  :global(.prose-micsmo-mini p) { margin: 0 !important; }
</style>
