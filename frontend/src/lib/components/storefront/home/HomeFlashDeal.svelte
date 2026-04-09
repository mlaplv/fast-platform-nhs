<script lang="ts">
  import { goto } from '$app/navigation';
  import { slugify } from '$lib/utils/format';

  const realImages = [
    '/-MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-CREAM-60g-Kem-Duong-Nhau-Thai-Lam-Sang-amp-Cap-Am-Diu-Nhe_33.1.png',
    '/Hurry-Harry-Medicated-Beauty-Wrinkle-Serum-Rich-jpeg.jpg',
    '/MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-ESSENCE-180ml-TINH-CHAT-CAP-AM-LAM-DIU-DA_. (14.1).png',
    '/-MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-PACK-130g-Mat-na-u-duong-trang-sang-da-tu-nhau-thai_23.png'
  ];

  const deals = Array.from({ length: 6 }).map((_, i) => ({
    id: i,
    name: `Siêu phẩm Flash Sale ${i + 1}`,
    price: 99000 + i * 20000,
    discount: 50 - i * 5,
    image: `/uploads/img/micsmo${realImages[i % realImages.length]}`
  }));
</script>

<div class="bg-white rounded-sm shadow-[0_1px_1px_0_rgba(0,0,0,0.05)] overflow-hidden">
  <div class="flex flex-row items-center justify-between px-5 py-4 border-b border-gray-100">
    <div class="flex items-center gap-3">
      <!-- Flash Sale Header Image / Text representation -->
      <div class="flex items-center">
        <h2 class="text-xl md:text-2xl font-black text-[#ee4d2d] italic tracking-tighter uppercase mr-2">F l a s h</h2>
        <h2 class="text-xl md:text-2xl font-black text-[#ee4d2d] italic tracking-tighter uppercase">S a l e</h2>
      </div>
      <div class="flex gap-1 ml-2">
        {#each ['00', '59', '59'] as time}
          <span class="bg-black text-white px-1.5 py-0.5 rounded-sm font-mono text-sm font-bold flex items-center justify-center min-w-[24px]">{time}</span>
        {/each}
      </div>
    </div>
    <a href="/deals" class="text-[#ee4d2d] font-normal text-sm hover:text-red-700 transition-colors flex items-center gap-1 group">
      Xem tất cả
      <span class="text-xs group-hover:translate-x-1 transition-transform">›</span>
    </a>
  </div>

  <div class="grid grid-cols-2 md:grid-cols-6 border-t border-l border-gray-100">
    {#each deals as deal}
      <button
        onclick={() => goto(`/${slugify(deal.name)}`)}
        class="border-r border-b border-gray-100 p-3 hover:shadow-[0_0_10px_rgba(0,0,0,0.05)] hover:z-10 bg-white relative transition-all group flex flex-col items-center"
      >
        <div class="w-full aspect-square relative mb-2 overflow-hidden">
            <!-- Micsmo Discount Badge (Top Right) -->
            <div class="absolute top-0 right-0 bg-[#ffd839] text-[#ee4d2d] text-[10px] sm:text-xs font-bold px-1.5 py-0.5 z-10 block text-center rounded-sm">
              <div>{deal.discount}%</div>
              <div class="text-[9px] uppercase font-medium text-white bg-[#ee4d2d] px-1 -mx-0.5 mt-0.5 rounded-sm">GIẢM</div>
            </div>
            <img src={deal.image} alt={deal.name} class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 origin-center" />
            <!-- Overlay overlay -->
            <div class="absolute inset-0 bg-black/0 group-hover:bg-black/[0.02] transition-colors pointer-events-none"></div>
        </div>
        <p class="text-[#ee4d2d] font-medium text-lg leading-none mt-1 text-center w-full truncate"><span class="text-xs mr-0.5 underline">đ</span>{deal.price.toLocaleString('vi-VN')}</p>
        
        <!-- Progress Bar -->
        <div class="w-[85%] h-3.5 bg-[#ffbda6] rounded-full mt-2 relative overflow-hidden flex items-center justify-center">
          <div class="absolute left-0 top-0 h-full bg-[#ee4d2d] rounded-full" style="width: 75%"></div>
          <span class="relative z-10 text-[9px] font-bold text-white tracking-widest uppercase line-clamp-1 truncate px-1">Đã bán {20 + deal.id * 5}</span>
        </div>
      </button>
    {/each}
  </div>
</div>
