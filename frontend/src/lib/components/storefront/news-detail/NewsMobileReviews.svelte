<script lang="ts">
  import EliteReviewSystem from '../product-detail/reviews/EliteReviewSystem.svelte';
  
  interface Props {
    articleId: string;
    slug: string;
  }
  let { articleId, slug }: Props = $props();
</script>

<div class="news-reviews-mobile bg-white px-6 py-10 border-t border-gray-100">
  <div class="flex justify-between items-center mb-8">
    <h2 class="text-xs font-black text-[#0f172a] uppercase tracking-[0.2em] italic">Phản hồi độc giả</h2>
    <a href="/{slug}/reviews" class="text-[10px] font-black text-luxury-copper uppercase tracking-widest">
      Xem tất cả
    </a>
  </div>

  <EliteReviewSystem 
    entityId={articleId} 
    entityType="NEWS" 
    mode="snippet" 
  />

  <div class="mt-8 p-5 bg-luxury-peach/5 border border-luxury-peach/10 rounded-xl">
    <div class="flex items-center justify-between">
      <div class="space-y-1">
        <span class="block text-[10px] font-black text-luxury-copper uppercase italic">Cộng đồng tin cậy</span>
        <span class="block text-[9px] text-gray-400 font-bold uppercase">Xác thực bởi Micsmo Elite</span>
      </div>
      <a href="/{slug}/reviews" class="px-5 py-2.5 bg-luxury-copper text-white text-[9px] font-black uppercase rounded-lg">
        GIA NHẬP
      </a>
    </div>
  </div>
</div>
