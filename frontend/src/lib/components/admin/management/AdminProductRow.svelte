<script lang="ts">
    import type { ProductResponse } from '$lib/types/commerce';

    let { product } = $props<{ product: ProductResponse }>();

    let isScanning = $state(false);
    let marketData = $state(product.marketData || {});

    // Check if sync happened today
    let lastSync = $derived(product.lastMarketSync ? new Date(product.lastMarketSync) : null);
    let today = new Date();
    let isSyncDisabled = $derived(
        isScanning ||
        (lastSync && lastSync.toDateString() === today.toDateString())
    );

    async function syncPrice() {
        isScanning = true;
        try {
            const res = await fetch(`/api/v1/products/${product.id}/sync-price`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const json = await res.json();
            if (json.data) {
                marketData = json.data;
            }
        } catch (e) {
            console.error("Sync failed", e);
        } finally {
            isScanning = false;
        }
    }
</script>

<tr class="border-b hover:bg-gray-50">
    <td class="p-2">{product.name}</td>
    <td class="p-2">{product.price.toLocaleString()}</td>

    <!-- Intel Giá (AI) -->
    <td class="p-2">
        {#if Object.keys(marketData).length > 0}
            <div class="text-sm">
                <p class="text-gray-500 line-through text-xs">{marketData.original_price?.toLocaleString() || 'N/A'}</p>
                <p class="text-red-600 font-bold">{marketData.final_price?.toLocaleString() || 'N/A'}</p>
                <p class="text-xs text-blue-600">{marketData.platform}: {marketData.analysis}</p>
            </div>
        {:else}
            <span class="text-gray-400 text-xs">Chưa quét</span>
        {/if}
    </td>

    <td class="p-2">
        <button
            onclick={syncPrice}
            disabled={isSyncDisabled}
            class="px-3 py-1 bg-blue-600 text-white rounded text-sm disabled:bg-gray-400 transition-colors"
        >
            {isScanning ? 'Đang quét...' : 'Quét giá AI'}
        </button>
    </td>
</tr>
