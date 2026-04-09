<script lang="ts">
  import HomeProductGrid from '../../lib/components/storefront/home/HomeProductGrid.svelte';
  interface Props {
    products: Array<{ id: string; name: string; price: number; image: string }>;
  }
  let { products }: Props = $props();
</script>

<div class="max-w-7xl mx-auto p-6">
  <h1 class="text-3xl font-bold mb-8 text-slate-800">Tất cả sản phẩm mỹ phẩm</h1>
  <HomeProductGrid {products} />
</div>