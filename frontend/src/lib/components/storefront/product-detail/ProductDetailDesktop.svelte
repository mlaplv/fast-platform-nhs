<script lang="ts">
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { goto } from '$app/navigation';

  const cartStore = getCartStore();

  interface Props {
    product: { id?: string; name: string; price: number; description: string; images: string[] };
  }
  let { product }: Props = $props();

  function addToCart() {
    // Ép kiểu (as any) tạm thời để tương thích với mock data chưa chuẩn hóa toàn bộ trường Product
    cartStore.addItem(product as any);
  }

  function buyNow() {
    cartStore.addItem(product as any);
    cartStore.closeCart();
    goto('/checkout');
  }
</script>

<div class="max-w-7xl mx-auto p-6 md:p-12 grid grid-cols-1 md:grid-cols-2 gap-12 bg-white rounded-3xl shadow-sm border border-slate-100 my-8">
  <!-- Left: Images -->
  <div class="space-y-4">
    <div class="aspect-square w-full bg-slate-50 rounded-3xl overflow-hidden shadow-inner">
      <img src={product.images[0]} alt={product.name} class="w-full h-full object-cover transition-transform duration-700 hover:scale-105" />
    </div>
    <div class="grid grid-cols-4 gap-3">
      {#each product.images as img}
        <div class="aspect-square bg-slate-50 rounded-2xl overflow-hidden border border-slate-100 cursor-pointer hover:border-red-300 transition-colors">
          <img src={img} alt="Thumbnail" class="w-full h-full object-cover" />
        </div>
      {/each}
    </div>
  </div>

  <!-- Right: Info -->
  <div class="flex flex-col">
    <h1 class="text-4xl font-black text-slate-900 mb-6 tracking-tighter leading-tight">{product.name}</h1>

    <div class="bg-red-50 p-8 rounded-3xl mb-8 border border-red-100">
      <p class="text-5xl font-black text-red-600 tracking-tighter italic">{product.price.toLocaleString('vi-VN')} ₫</p>
    </div>

    <p class="text-slate-600 mb-8 leading-relaxed font-medium text-lg">{product.description}</p>

    <div class="mt-auto flex gap-4">
      <button onclick={addToCart} class="bg-slate-900 text-white font-black py-5 px-10 rounded-2xl hover:bg-red-600 transition-all active:scale-95 shadow-xl shadow-red-500/20 uppercase tracking-widest text-sm">
        Thêm vào giỏ hàng
      </button>
      <button onclick={buyNow} class="bg-white border-2 border-slate-900 text-slate-900 font-black py-5 px-10 rounded-2xl hover:bg-slate-50 transition-all active:scale-95 uppercase tracking-widest text-sm">
        Mua ngay
      </button>
    </div>
  </div>
</div>
