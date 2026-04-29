<script lang="ts">
  import EliteReviewSystem from '../product-detail/reviews/EliteReviewSystem.svelte';
  
  interface Props {
    articleId: string;
    title?: string;
  }
  let { articleId, title = 'Phản hồi từ độc giả' }: Props = $props();
</script>

<div class="news-reviews-wrapper bg-gray-50/30 border-t border-gray-100 py-16 px-4">
  <div class="max-w-4xl mx-auto">
    <EliteReviewSystem 
      entityId={articleId} 
      entityType="NEWS" 
      {title} 
    />
  </div>
</div>
