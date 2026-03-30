<script lang="ts">
  import { ShoppingCart, Share2, Heart, MessageCircle, Bookmark } from 'lucide-svelte';
  import { Z_INDEX } from '$lib/core/constants/zIndex';
  import type { Product } from '$lib/types';

  interface Props {
    product: Product;
    onPurchase: () => void;
  }

  let {
    product,
    onPurchase
  }: Props = $props();

  const metadata = $derived(product?.metadata || {});

  const labels = $derived({
    shop_avatar: (metadata.mobile_shop_avatar as string) || "/favicon.png",
    likes: (metadata.mobile_stats_likes as number) || 1200,
    comments: (metadata.mobile_stats_comments as number) || 128,
    saves: (metadata.mobile_stats_saves as number) || 45,
    label_share: (metadata.mobile_label_share as string) || "Chia sẻ",
    label_purchase: (metadata.mobile_label_purchase as string) || "Mở giỏ hàng",
    disk_image: (metadata.mobile_disk_image as string) || "https://ui-avatars.com/api/?name=E&background=000&color=fff",
    label_liked: (metadata.mobile_label_liked as string) || "Đã thích",
    label_saved: (metadata.mobile_label_saved as string) || "Đã lưu",
    aria_like: (metadata.mobile_aria_like as string) || "Thích sản phẩm",
    aria_unlike: (metadata.mobile_aria_unlike as string) || "Bỏ thích",
    aria_comments: (metadata.mobile_aria_comments as string) || "Xem bình luận",
    aria_save: (metadata.mobile_aria_save as string) || "Lưu sản phẩm",
    aria_unsave: (metadata.mobile_aria_unsave as string) || "Bỏ lưu",
    aria_share: (metadata.mobile_aria_share as string) || "Chia sẻ sản phẩm"
  });

  let liked = $state(false);
  let saved = $state(false);

  // Format số lượng (Ví dụ: 1200 -> 1.2k)
  const formatCount = (num: number) => {
    if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
    return num.toString();
  };
</script>

<div
  class="fixed right-2 flex flex-col items-center gap-4 pb-4 transition-all duration-300"
  style="z-index: {Z_INDEX.SURFACE}; bottom: calc(1.5rem + env(safe-area-inset-bottom))"
>
  <!-- Profile Avatar -->
  <div class="relative mb-2 group cursor-pointer">
    <div class="w-12 h-12 rounded-full border-[1.5px] border-white/80 overflow-hidden bg-gray-900 shadow-lg">
      <img src={labels.shop_avatar} alt="Avatar" class="w-full h-full object-cover" loading="lazy" />
    </div>
    <div class="absolute -bottom-2 left-1/2 -translate-x-1/2 bg-red-600 rounded-full w-5 h-5 flex items-center justify-center border-2 border-white shadow-sm">
      <span class="text-white text-[10px] font-bold leading-none">+</span>
    </div>
  </div>

  <button
    class="flex flex-col items-center group outline-none focus-visible:ring-2 focus-visible:ring-red-500 rounded-full p-1"
    onclick={() => liked = !liked}
    aria-label={liked ? labels.aria_unlike : labels.aria_like}
  >
    <Heart
      class="w-9 h-9 tiktok-shadow transition-all duration-200 active:scale-50 hover:scale-110"
      fill={liked ? '#ef4444' : 'transparent'}
      color={liked ? '#ef4444' : 'white'}
      strokeWidth={1.5}
    />
    <span class="text-white text-[11px] font-bold mt-0.5 tiktok-shadow tracking-tight">
      {liked ? formatCount(labels.likes + 1) : formatCount(labels.likes)}
    </span>
  </button>

  <button
    class="flex flex-col items-center group outline-none focus-visible:ring-2 focus-visible:ring-white rounded-full p-1 mt-1"
    aria-label={labels.aria_comments}
  >
    <MessageCircle class="w-9 h-9 text-white tiktok-shadow transition-transform hover:scale-110" fill="transparent" strokeWidth={1.5} />
    <span class="text-white text-[11px] font-bold mt-0.5 tiktok-shadow tracking-tight">
      {formatCount(labels.comments)}
    </span>
  </button>

  <button
    class="flex flex-col items-center group outline-none focus-visible:ring-2 focus-visible:ring-yellow-500 rounded-full p-1 mt-1"
    onclick={() => saved = !saved}
    aria-label={saved ? labels.aria_unsave : labels.aria_save}
  >
    <Bookmark
      class="w-9 h-9 tiktok-shadow transition-all duration-200 active:scale-50 hover:scale-110"
      fill={saved ? '#eab308' : 'transparent'}
      color={saved ? '#eab308' : 'white'}
      strokeWidth={1.5}
    />
    <span class="text-white text-[11px] font-bold mt-0.5 tiktok-shadow tracking-tight">
      {saved ? labels.label_saved : formatCount(labels.saves)}
    </span>
  </button>

  <button
    class="flex flex-col items-center group outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded-full p-1 mt-1"
    aria-label={labels.aria_share}
  >
    <Share2 class="w-9 h-9 text-white tiktok-shadow transition-transform hover:scale-110" strokeWidth={1.5} />
    <span class="text-white text-[11px] font-bold mt-0.5 tiktok-shadow tracking-tight">{labels.label_share}</span>
  </button>

  <!-- Animated Record / Purchase Button -->
  <button
    class="mt-4 relative w-12 h-12 flex items-center justify-center outline-none focus-visible:ring-2 focus-visible:ring-white rounded-full group/buy"
    onclick={onPurchase}
    aria-label={labels.label_purchase}
  >
    <!-- Freeship Tag -->
    <div class="absolute -top-6 left-1/2 -translate-x-1/2 bg-emerald-500 text-white text-[7px] font-black px-1.5 py-0.5 rounded-md shadow-lg animate-bounce whitespace-nowrap z-20">
      FREESHIP
    </div>
    
    <div class="vinyl-spin w-full h-full bg-gradient-to-tr from-gray-900 to-gray-700 rounded-full flex items-center justify-center border-2 border-white/20 shadow-xl overflow-hidden will-change-transform group-hover/buy:scale-110 transition-transform">
      <div
        class="w-full h-full animate-spin-slow bg-cover opacity-60 absolute inset-0"
        style="background-image: url('{labels.disk_image}')"
      ></div>
      <ShoppingCart class="w-5 h-5 text-white relative z-10 drop-shadow-md" />
    </div>
  </button>
</div>
