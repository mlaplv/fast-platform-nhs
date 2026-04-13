<script lang="ts">
  import UserLayout from '$lib/components/storefront/user/UserLayout.svelte';
</script>

<UserLayout>
  <div class="space-y-6 min-h-[400px]">
    <!-- Header -->
    <div class="border-b border-gray-100 pb-5">
      <h1 class="text-[18px] font-semibold text-gray-900">Đơn Mua</h1>
      <div class="flex items-center gap-10 mt-6 border-b border-gray-50 -mb-[21px]">
        {#each ['Tất cả', 'Chờ thanh toán', 'Vận chuyển', 'Chờ giao hàng', 'Hoàn thành', 'Đã hủy'] as tab, i}
          <button class="pb-4 text-[14px] transition-colors relative {i === 0 ? 'text-[#ee4d2d]' : 'text-gray-700'}">
            {tab}
            {#if i === 0}
              <div class="absolute bottom-0 left-0 w-full h-0.5 bg-[#ee4d2d]"></div>
            {/if}
          </button>
        {/each}
      </div>
    </div>

    <!-- Empty State Placeholder -->
    <div class="flex flex-col items-center justify-center py-20 gap-4">
      <div class="w-24 h-24 bg-gray-50 rounded-full flex items-center justify-center">
         <svg class="w-12 h-12 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" /></svg>
      </div>
      <p class="text-[14px] text-gray-500">Chưa có đơn hàng nào</p>
    </div>
  </div>
</UserLayout>
