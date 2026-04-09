<script lang="ts">
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { goto } from '$app/navigation';

  const cartStore = getCartStore();

  interface Props {
    product: { id?: string; name: string; price: number; description: string; image: string };
  }
  let { product }: Props = $props();

  function addToCart() {
    cartStore.addItem(product as any);
  }

  function buyNow() {
    cartStore.addItem(product as any);
    cartStore.closeCart();
    goto('/checkout');
  }
</script>

<div class="h-screen w-screen relative bg-black text-white overflow-y-scroll">
  <!-- Immersive Image -->
  <img src={product.image} alt={product.name} class="absolute inset-0 w-full h-full object-cover z-0" />
  <div class="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent/60 z-0"></div>

  <!-- Info Overlay -->
  <div class="absolute bottom-0 left-0 w-full p-8 pb-24 z-10 bg-gradient-to-t from-black via-black/90 to-transparent">
    <span class="bg-red-600 text-white px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest mb-4 inline-block">Product</span>
    <h1 class="text-3xl font-black mb-2 tracking-tighter leading-tight">{product.name}</h1>
    <p class="text-red-400 font-black text-3xl mb-6 tracking-tighter italic">{product.price.toLocaleString('vi-VN')} ₫</p>
    <p class="text-slate-200 text-sm leading-relaxed font-medium line-clamp-3 mb-8">{product.description}</p>

    <div class="flex gap-4">
      <button onclick={addToCart} class="flex-grow bg-white text-black font-black py-4 rounded-2xl shadow-xl hover:bg-red-500 hover:text-white transition uppercase tracking-widest text-sm">
        Thêm giỏ
      </button>
      <button onclick={buyNow} class="flex-grow bg-red-600 text-white font-black py-4 rounded-2xl shadow-xl hover:bg-red-700 transition uppercase tracking-widest text-sm">
        Mua ngay
      </button>
    </div>
  </div>
</div>
