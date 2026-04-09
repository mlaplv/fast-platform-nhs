<script lang="ts">
  import { goto } from '$app/navigation';
  import { slugify } from '$lib/utils/format';

  interface Props {
    products: Array<{ id: string; name: string; price: number; image: string }>;
  }
  let { products }: Props = $props();
</script>

<div class="h-[calc(100vh-env(safe-area-inset-bottom)-60px)] w-screen overflow-y-scroll snap-y snap-mandatory bg-black">
  {#each products as product (product.id)}
    <div class="snap-start h-full w-full relative flex items-center justify-center bg-black">
      <!-- Immersive Image -->
      <img src={product.image} alt={product.name} class="absolute inset-0 w-full h-full object-cover z-0" />
      <div class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent z-0"></div>

      <!-- Product Info Overlay -->
      <div class="absolute bottom-6 left-4 z-10 text-white p-4 w-[75%]">
        <span class="bg-red-600 text-white px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-widest mb-2 inline-block">Product</span>
        <h3 class="text-xl font-black mb-1 tracking-tighter leading-tight">{product.name}</h3>
        <p class="text-2xl font-black text-red-400 tracking-tighter italic">{product.price.toLocaleString('vi-VN')} ₫</p>
      </div>

      <!-- Action Overlay (TikTok Style) -->
      <div class="absolute right-4 bottom-24 z-10 flex flex-col items-center gap-6">
        <button class="flex flex-col items-center text-white group">
          <span class="text-3xl drop-shadow-lg group-hover:scale-110 transition-transform">❤️</span>
          <p class="text-[10px] font-bold mt-1">Like</p>
        </button>
        <button
          onclick={() => goto(`/${slugify(product.name)}`)}
          class="flex flex-col items-center text-white group cursor-pointer"
        >
          <span class="text-3xl drop-shadow-lg group-hover:scale-110 transition-transform">🛒</span>
          <p class="text-[10px] font-bold mt-1 text-red-400 uppercase tracking-widest">Xem</p>
        </button>
      </div>
    </div>
  {/each}
</div>