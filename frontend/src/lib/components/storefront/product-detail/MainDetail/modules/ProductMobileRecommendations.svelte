<script lang="ts">
  import { formatCurrency, trimProductName } from '$lib/utils/format';
  import { resolveOptimizedImageUrl } from '$lib/state/utils';
  interface Props {
    relatedProducts: Product[];
  }

  let { relatedProducts }: Props = $props();
</script>

<section id="recommendations" class="content-section">
  <h2 class="section-title">Có thể bạn cũng thích</h2>
  <div class="recommendations-grid">
    {#each relatedProducts as p}
      <a data-sveltekit-reload href="/{p.slug}" class="related-card">
        <div class="img-wrap">
          <img 
            src={resolveOptimizedImageUrl(p.images?.[0] || '', 300)} 
            srcset="{resolveOptimizedImageUrl(p.images?.[0] || '', 200)} 200w, {resolveOptimizedImageUrl(p.images?.[0] || '', 330)} 330w, {resolveOptimizedImageUrl(p.images?.[0] || '', 400)} 400w, {resolveOptimizedImageUrl(p.images?.[0] || '', 600)} 600w"
            sizes="(max-width: 767px) 50vw, 300px"
            alt={p.name} 
            loading="lazy" 
            decoding="async" 
            width="300"
            height="300"
          />
        </div>
        <div class="info-wrap">
          <h3 class="related-name">{trimProductName(p.name)}</h3>
          <div class="related-price">{formatCurrency(p.discountPrice || p.discount_price || p.price)}</div>
        </div>
      </a>
    {/each}
  </div>
</section>

<style>
  .content-section { background: white; padding: 8px 10px 8px 10px; }
  .section-title { font-size: 14px; font-weight: 800; color: #222; margin-bottom: 6px; letter-spacing: -0.01em; }
  .recommendations-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
  .related-card { display: flex; flex-direction: column; background: white; border-radius: 12px; overflow: hidden; border: 1px solid #f5f5f5; text-decoration: none; color: inherit; transition: all 0.3s ease; }
  .related-card:active { transform: scale(0.98); background: #fafafa; }
  .img-wrap { aspect-ratio: 1/1; }
  .img-wrap img { width: 100%; height: 100%; object-fit: cover; }
  .info-wrap { padding: 10px; }
  .related-name { font-size: 12px; font-weight: 600; color: #333; line-height: 1.4; height: 2.8em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin: 0 0 6px 0; }
  .related-price { font-size: 15px; font-weight: 900; color: #d32f2f; letter-spacing: -0.02em; }
</style>
