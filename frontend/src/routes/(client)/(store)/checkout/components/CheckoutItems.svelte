<script lang="ts">
  import { slide } from 'svelte/transition';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { formatCurrency } from '$lib/utils/format';
  import type { CustomItem } from '$lib/types/commerce/checkout';

  let { 
    customItems = $bindable(), 
    showCustomItemForm = $bindable(), 
    newCustomItem = $bindable(),
    addCustomItem,
    removeCustomItem
  } = $props<{
    customItems: CustomItem[];
    showCustomItemForm: boolean;
    newCustomItem: CustomItem; // Strict typing enforced
    addCustomItem: () => void;
    removeCustomItem: (idx: number) => void;
  }>();

  const cartStore = getCartStore();
  const clientUi = getClientUi();
</script>

<div class="lg:col-span-12">
  <div class="bg-white p-6 shadow-sm border border-gray-100">
    <h2 class="text-lg font-black uppercase text-gray-900 mb-6 pb-4 border-b border-gray-100 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <svg class="w-5 h-5 text-[#ee4d2d]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>
        <span class="italic">GIỎ HÀNG</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-[10px] bg-gray-50 px-2 py-1 text-gray-400 font-bold uppercase tracking-widest">{cartStore.selectedItemsCount} SẢN PHẨM</span>
        <button 
          onclick={async () => { 
            const confirmed = await clientUi.openConfirm({
              title: 'DỌN DẸP GIỎ HÀNG',
              message: 'Bạn có chắc chắn muốn xóa giỏ hàng không? Hành động này không thể hoàn tác.',
              confirmLabel: 'XÓA GIỎ HÀNG',
              cancelLabel: 'ĐỂ LẠI'
            });
            if (confirmed) cartStore.clearCart(); 
          }} 
          class="p-1.5 hover:bg-red-50 text-gray-300 hover:text-red-500 transition-colors group/clear"
          title="Xóa tận gốc giỏ hàng"
        >
          <svg class="w-3.5 h-3.5 group-hover/clear:rotate-12 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
        </button>
      </div>
    </h2>

    <!-- Items -->
    <div class="space-y-4 max-h-[350px] overflow-y-auto pr-2 custom-scrollbar mb-6">
      {#each cartStore.items.filter(i => i.selected) as item}
        <div class="flex gap-4 group bg-gray-50/50 p-2 border border-transparent hover:border-gray-100 transition-all">
          <div class="w-16 h-16 bg-white border border-gray-100 overflow-hidden shrink-0 relative">
            <img 
              src={item.product.image || item.product.images?.[0] || '/uploads/img/micsmo/sp1.png'} 
              alt={item.product.name} 
              class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" 
            />
            <div class="absolute bottom-0 right-0 bg-gray-900/80 text-white text-[8px] px-1 font-black">x{item.quantity}</div>
          </div>
          <div class="flex-1 min-w-0 flex flex-col justify-between py-0.5">
            <div class="space-y-0.5">
              <h4 class="text-[10px] font-bold text-gray-800 leading-tight uppercase italic line-clamp-2 antialiased">{item.product.name}</h4>
              {#if item.variant}
                <div class="flex items-center gap-1.5 mt-1">
                  <span class="text-[7px] font-black text-white bg-gray-400 px-1.5 py-0.5 uppercase tracking-tighter">PHÂN LOẠI</span>
                  <span class="text-[8px] font-bold text-gray-500 uppercase">{item.variant.sku}</span>
                </div>
              {/if}
            </div>
            <div class="flex items-center justify-between mt-1">
              <div class="flex items-center gap-1">
                 <button type="button" onclick={() => cartStore.updateQuantity(item.id, item.quantity - 1)} class="w-5 h-5 flex items-center justify-center bg-white border border-gray-100 text-gray-400 hover:text-[#ee4d2d] text-[10px] font-black">-</button>
                 <span class="text-[10px] font-black w-4 text-center">{item.quantity}</span>
                 <button type="button" onclick={() => cartStore.updateQuantity(item.id, item.quantity + 1)} class="w-5 h-5 flex items-center justify-center bg-white border border-gray-100 text-gray-400 hover:text-[#ee4d2d] text-[10px] font-black">+</button>
              </div>
              <div class="flex flex-col items-end gap-0">
                {#if (item.variant?.discountPrice || item.product.discountPrice) && (item.variant?.price || item.product.price)}
                  <span class="text-[9px] text-gray-400 line-through font-bold">
                    {formatCurrency((item.variant?.price ?? item.product.price ?? 0) * item.quantity)}
                  </span>
                {/if}
                <span class="text-sm font-black text-[#ee4d2d] italic tracking-tightest antialiased">
                  {formatCurrency((item.variant?.discountPrice ?? item.variant?.price ?? item.product.discountPrice ?? item.product.price ?? 0) * item.quantity)}
                </span>
              </div>
            </div>
          </div>
        </div>
      {/each}

      {#if customItems.length > 0}
        <div class="mt-4 pt-4 border-t border-dashed border-gray-200 space-y-3" in:slide>
          <h3 class="text-[10px] font-black text-gray-400 uppercase tracking-widest italic flex items-center gap-2">
            <svg class="w-3.5 h-3.5 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            YÊU CẦU THÊM (CHỜ BÁO GIÁ)
          </h3>
          {#each customItems as item, idx}
            <div class="flex gap-4 bg-orange-50/40 p-2 border border-orange-100 relative group animate-pulse-subtle">
              <div class="w-12 h-12 bg-white border border-orange-100 shrink-0 flex items-center justify-center overflow-hidden">
                {#if item.image && item.image.startsWith('http')}
                  <img src={item.image} alt={item.name} class="w-full h-full object-cover" />
                {:else}
                  <svg class="w-6 h-6 text-orange-200" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 00-2 2z" /></svg>
                {/if}
              </div>
              <div class="flex-1 min-w-0 flex flex-col justify-center">
                <h4 class="text-[9px] font-black text-gray-800 uppercase italic line-clamp-1">{item.name}</h4>
                <div class="text-[8px] text-gray-400 font-bold">Số lượng: {item.quantity} · <span class="text-orange-500 italic">Đang chờ xử lý</span></div>
              </div>
              <button 
                type="button"
                onclick={() => removeCustomItem(idx)}
                class="absolute -top-1.5 -right-1.5 w-5 h-5 bg-white border border-gray-200 text-gray-400 hover:text-red-500 rounded-full flex items-center justify-center shadow-sm opacity-0 group-hover:opacity-100 transition-all"
              >
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <!-- ADD CUSTOM ITEM CONTROL -->
    <div class="mt-4 pt-4 border-t border-gray-100">
      {#if !showCustomItemForm}
        <button 
          type="button"
          onclick={() => showCustomItemForm = true}
          class="w-full py-4 border-2 border-dashed border-gray-100 text-gray-400 hover:border-[#ee4d2d] hover:text-[#ee4d2d] hover:bg-[#fff4f1]/30 transition-all flex items-center justify-center gap-3 group"
        >
          <div class="w-6 h-6 rounded-full border border-current flex items-center justify-center group-hover:bg-[#ee4d2d] group-hover:text-white transition-colors">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 6v6m0 0v6m0-6h6m-6 0H6" /></svg>
          </div>
          <span class="text-[10px] font-black uppercase tracking-widest italic text-center">Yêu cầu thêm sản phẩm khác</span>
        </button>
      {:else}
        <div class="p-5 bg-gray-50 border border-gray-100 space-y-4 shadow-inner" in:slide>
          <div class="flex items-center justify-between mb-2">
            <span class="text-[10px] font-black text-gray-900 uppercase italic tracking-widest flex items-center gap-2">
              <div class="w-1.5 h-1.5 bg-[#ee4d2d] rounded-full"></div>
              Mục sản phẩm bổ sung
            </span>
            <button type="button" onclick={() => showCustomItemForm = false} class="text-gray-300 hover:text-gray-900 transition-colors"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" /></svg></button>
          </div>
          <div class="space-y-3">
            <div class="space-y-1">
              <label class="text-[8px] font-black text-gray-400 uppercase ml-1">Tên sản phẩm</label>
              <input type="text" bind:value={newCustomItem.name} placeholder="VD: Sữa rửa mặt Cerave SA 473ml..." class="w-full bg-white border border-gray-100 px-3 py-2.5 text-[10px] font-bold outline-none focus:border-[#ee4d2d] transition-colors text-gray-900" />
            </div>
            <div class="grid grid-cols-2 gap-3">
               <div class="space-y-1">
                 <label class="text-[8px] font-black text-gray-400 uppercase ml-1">Số lượng</label>
                 <input type="number" bind:value={newCustomItem.quantity} class="w-full bg-white border border-gray-100 px-3 py-2.5 text-[10px] font-bold outline-none focus:border-[#ee4d2d] text-gray-900" />
               </div>
               <div class="space-y-1">
                 <label class="text-[8px] font-black text-gray-400 uppercase ml-1">Giá dự kiến (VNĐ)</label>
                 <input type="number" bind:value={newCustomItem.price} placeholder="0" class="w-full bg-white border border-gray-100 px-3 py-2.5 text-[10px] font-bold outline-none focus:border-[#ee4d2d]" />
               </div>
            </div>
            <div class="space-y-1">
              <label class="text-[8px] font-black text-gray-400 uppercase ml-1">Hình ảnh / Mô tả</label>
              <input type="text" bind:value={newCustomItem.image} placeholder="Nhập Link ảnh hoặc yêu cầu màu sắc, kích thước..." class="w-full bg-white border border-gray-100 px-3 py-2.5 text-[10px] font-bold outline-none focus:border-[#ee4d2d]" />
            </div>
          </div>
          <button 
            type="button" 
            onclick={addCustomItem}
            class="w-full py-3 bg-gray-900 text-white text-[10px] font-black uppercase tracking-widest hover:bg-[#ee4d2d] transition-all flex items-center justify-center gap-2 shadow-lg shadow-gray-200"
          >
            XÁC NHẬN YÊU CẦU
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
          </button>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: #f9fafb;
    border-radius: 10px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: #e5e7eb;
    border-radius: 10px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: #d1d5db;
  }
</style>
