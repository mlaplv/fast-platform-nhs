<script lang="ts">
  import { Star, ShieldCheck } from 'lucide-svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  
  let { product } = $props();
  const metadata = $derived(product?.metadata || {});
  const reviews = $derived(metadata?.reviews || []);
  
  const labels = $derived({
    headline: metadata.reviews_headline || 'KHÁCH HÀNG NÓI GÌ?',
    trust_score: metadata.reviews_trust_score || '4.9/5',
    count_text: metadata.reviews_count_text || '2,140+ LƯỢT MUA',
    label_verified: metadata.reviews_label_verified || 'VERIFIED',
    label_store_verified: metadata.reviews_label_store_verified || 'Store_Verified'
  });
</script>

<div class="h-full flex flex-col justify-center px-6 py-20 bg-[#020617]" id="reviews">
  <div class="mb-10">
    <div class="flex items-center gap-2 mb-4">
      <div class="flex items-center gap-0.5">
        {#each Array(5) as _, i}
          <Star class="w-2.5 h-2.5 {i < 5 ? 'text-amber-400 fill-amber-400' : 'text-white/10'}" />
        {/each}
      </div>
      <span class="text-[9px] text-white/40 font-black uppercase tracking-widest">{labels.trust_score}</span>
      <span class="mx-1 text-white/10">|</span>
      <span class="text-[9px] text-white/40 font-black uppercase tracking-widest">{labels.count_text}</span>
    </div>
    
    <h2 class="text-3xl font-black text-white leading-tight uppercase tracking-tighter italic">
      {@html labels.headline}
    </h2>
  </div>

  <div class="space-y-6">
    {#each reviews.slice(0, 3) as review}
      <div class="p-6 bg-white/5 border border-white/10 rounded-[32px] backdrop-blur-xl relative overflow-hidden group">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-4">
            <div class="w-10 h-10 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold text-sm">
              {review.initial || review.name[0]}
            </div>
            <div>
              <h4 class="text-white font-bold text-sm">{review.name}</h4>
              <div class="flex items-center gap-1.5">
                <ShieldCheck class="w-3 h-3 text-emerald-400" />
                <span class="text-[9px] text-emerald-400 font-bold uppercase tracking-widest">{labels.label_verified}</span>
              </div>
            </div>
          </div>
          <div class="flex gap-0.5">
            {#each Array(review.rating || 5) as _}
              <Star class="w-2.5 h-2.5 text-emerald-400 fill-emerald-400" />
            {/each}
          </div>
        </div>
        <p class="text-white/80 text-sm leading-relaxed italic">
          "{typeof review.content === 'string' ? review.content : 'Sản phẩm tuyệt vời, rất đáng để trải nghiệm.'}"
        </p>
        
        <div class="absolute -top-10 -right-10 w-32 h-32 bg-emerald-500/5 rounded-full blur-3xl group-hover:bg-emerald-500/10 transition-colors"></div>
      </div>
    {/each}
  </div>

  <div class="mt-12 text-center">
    <button class="text-white/40 text-[10px] uppercase font-black tracking-[0.4em] hover:text-white transition-colors underline underline-offset-8">
      Xem tất cả đánh giá thực tế
    </button>
  </div>
</div>
