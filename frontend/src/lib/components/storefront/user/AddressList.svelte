<script lang="ts">
    import Edit3 from "@lucide/svelte/icons/edit-3";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import MapPin from "@lucide/svelte/icons/map-pin";
  import Phone from "@lucide/svelte/icons/phone";
  import UserIcon from "@lucide/svelte/icons/user";
  import Check from "@lucide/svelte/icons/check";
  import { fade, fly } from 'svelte/transition';
  import type { UserAddress } from '$lib/state/authStore.svelte';

  interface Props {
    addresses: UserAddress[];
    onEdit: (addr: UserAddress) => void;
    onDelete: (id: string) => void;
    onSetDefault: (id: string) => void;
  }

  let { addresses, onEdit, onDelete, onSetDefault }: Props = $props();
</script>

<div class="space-y-6">
  {#if addresses.length === 0}
    <div class="py-16 text-center border-2 border-dashed border-stone-50 rounded-xl" in:fade>
      <div class="w-16 h-16 bg-stone-50 rounded-full flex items-center justify-center mx-auto mb-4">
        <MapPin class="w-8 h-8 text-stone-200" />
      </div>
      <p class="text-stone-400 font-serif italic">Quý khách chưa lưu địa chỉ nhận hàng nào.</p>
    </div>
  {:else}
    {#each addresses as addr, i (addr.id)}
      <div
        class="group relative bg-white p-6 border border-stone-100 transition-all duration-500 hover:shadow-[0_15px_30px_rgba(0,0,0,0.03)] {addr.isDefault ? 'ring-1 ring-luxury-copper/20' : ''}"
        in:fly={{ y: 20, delay: i * 100 }}
      >
        {#if addr.isDefault}
          <div class="absolute top-0 right-0 px-3 py-1 bg-luxury-copper text-white text-[8px] font-black tracking-[2px]">
            Mặc định
          </div>
        {/if}

        <div class="flex justify-between items-start mb-6">
          <div class="flex items-center gap-3">
             <div class="w-8 h-8 rounded-full bg-stone-50 flex items-center justify-center">
                <UserIcon class="w-3.5 h-3.5 text-stone-400" />
             </div>
             <div>
               <h3 class="text-[13px] font-bold text-stone-800 tracking-wider">{addr.name}</h3>
               <div class="flex items-center gap-1.5 mt-0.5">
                  <Phone class="w-3 h-3 text-luxury-copper" />
                  <span class="text-[12px] text-stone-500 font-medium">{addr.phone}</span>
               </div>
             </div>
          </div>

          <div class="flex gap-2">
            <button
              onclick={() => onEdit(addr)}
              class="w-10 h-10 flex items-center justify-center rounded-full bg-stone-50 text-stone-400 hover:bg-luxury-copper/10 hover:text-luxury-copper transition-all"
              title="Chỉnh sửa"
            >
              <Edit3 class="w-4 h-4" />
            </button>
            {#if !addr.isDefault}
              <button
                onclick={() => onDelete(addr.id)}
                class="w-10 h-10 flex items-center justify-center rounded-full bg-stone-50 text-stone-400 hover:bg-red-50 hover:text-red-500 transition-all"
                title="Xóa"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            {/if}
          </div>
        </div>

        <div class="flex gap-3 items-start pl-1">
          <MapPin class="w-4 h-4 text-luxury-copper shrink-0 mt-0.5" />
          <div class="space-y-1">
            <p class="text-[13px] text-stone-600 leading-relaxed font-medium">{addr.address}</p>
            <p class="text-[12px] text-stone-400 font-bold tracking-widest">{addr.ward}, {addr.city}</p>
          </div>
        </div>

        {#if !addr.isDefault}
          <div class="mt-6 pt-5 border-t border-stone-50 flex justify-end">
            <button
              onclick={() => onSetDefault(addr.id)}
              class="text-[10px] font-black tracking-[2px] text-stone-400 hover:text-luxury-copper flex items-center gap-2 group/btn py-2"
            >
              <div class="w-5 h-5 rounded-full border border-stone-200 flex items-center justify-center group-hover/btn:border-luxury-copper transition-colors">
                 <Check class="w-3 h-3 opacity-0 group-hover/btn:opacity-100 transition-opacity" />
              </div>
              Thiết lập mặc định
            </button>
          </div>
        {/if}
      </div>
    {/each}
  {/if}
</div>
