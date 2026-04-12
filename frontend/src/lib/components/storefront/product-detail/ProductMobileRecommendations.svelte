<script lang="ts">
  import type { Product } from '$lib/types';

  interface Props {
    relatedProducts: Product[];
  }

  let { relatedProducts }: Props = $props();
  const formatPrice = (p: number) => p.toLocaleString('vi-VN');
</script>

<section id="recommendations" class="content-section">
  <h2 class="section-title">Có thể bạn cũng thích</h2>
  <div class="recommendations-grid">
    {#each relatedProducts as p}
      <a data-sveltekit-reload href="/{p.slug}" class="related-card">
        <div class="img-wrap">
          <img src={p.images?.[0] || 'https://via.placeholder.com/150'} alt={p.name} />
        </div>
        <div class="info-wrap">
          <h3 class="related-name">{p.name}</h3>
          <div class="related-price">{formatPrice(p.discountPrice || p.discount_price || p.price)}đ</div>
        </div>
      </a>
    {/each}
  </div>
</section>

<style>
  .content-section { background: white; padding: 16px; }
  .section-title { font-size: 14px; font-weight: 700; color: #333; margin-bottom: 12px; }
  .recommendations-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
  .related-card { display: flex; flex-direction: column; background: white; border-radius: 8px; overflow: hidden; border: 1px solid #f0f0f0; text-decoration: none; color: inherit; }
  .img-wrap { aspect-ratio: 1/1; }
  .img-wrap img { width: 100%; height: 100%; object-fit: cover; }
  .info-wrap { padding: 8px; }
  .related-name { font-size: 12px; font-weight: 500; color: #333; line-height: 1.3; height: 2.6em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin: 0 0 4px 0; }
  .related-price { font-size: 14px; font-weight: 700; color: #ff2556; }
</style>
